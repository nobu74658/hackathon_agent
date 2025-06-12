from typing import Dict, Any, List, Optional, Tuple
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.schema.runnable import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from datetime import datetime
import json

from app.services.conversation_memory import ConversationMemoryService
from app.core.config import settings


class QuestionResponse(BaseModel):
    """質問生成のレスポンス構造"""
    questions: List[str] = Field(description="生成された質問のリスト")
    reasoning: str = Field(description="なぜこれらの質問が必要かの説明")
    information_needed: List[str] = Field(description="まだ必要な情報のリスト")
    completeness_score: int = Field(description="情報の充足度（0-100）")


class ActionPlanResponse(BaseModel):
    """アクションプラン生成のレスポンス構造"""
    action_items: List[Dict[str, Any]] = Field(description="アクションアイテムのリスト")
    summary: str = Field(description="全体的なサマリー")
    key_improvements: List[str] = Field(description="主要な改善ポイント")
    metrics: Dict[str, Any] = Field(description="成功指標")


class DialogueManager:
    """対話フローを管理するマネージャー"""
    
    def __init__(self):
        self.memory_service = ConversationMemoryService()
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.question_parser = PydanticOutputParser(pydantic_object=QuestionResponse)
        self.action_plan_parser = PydanticOutputParser(pydantic_object=ActionPlanResponse)
    
    async def initialize(self):
        """サービスの初期化"""
        await self.memory_service.initialize()
    
    async def start_dialogue(
        self,
        session_id: str,
        initial_context: Dict[str, Any]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """対話セッションを開始"""
        # 初期質問生成のプロンプト
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIアシスタントです。
            1on1セッションの内容から、営業スキル向上のための具体的なアクションプランを作成するために
            必要な情報を収集します。
            
            以下の情報が提供されています：
            {initial_context}
            
            効果的なアクションプランを作成するために追加で必要な情報を特定し、
            3-5個の具体的で答えやすい質問を生成してください。
            
            {format_instructions}
            """),
            ("user", "1on1セッションの内容を分析し、追加で必要な情報を収集するための質問を生成してください。")
        ])
        
        # チェーン構築
        chain = (
            {
                "initial_context": RunnablePassthrough(),
                "format_instructions": lambda _: self.question_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.question_parser
        )
        
        # 質問生成
        response = await chain.ainvoke(json.dumps(initial_context, ensure_ascii=False))
        
        # メタデータ作成
        metadata = {
            "stage": "initial",
            "reasoning": response.reasoning,
            "information_needed": response.information_needed,
            "completeness_score": response.completeness_score
        }
        
        return response.questions, metadata
    
    async def process_user_response(
        self,
        session_id: str,
        user_response: str,
        db_session: Any
    ) -> Dict[str, Any]:
        """ユーザーの回答を処理"""
        # メモリに回答を追加
        await self.memory_service.add_message(
            session_id=session_id,
            role="user",
            content=user_response,
            db=db_session
        )
        
        # 現在のコンテキストを取得
        context = await self.memory_service.get_conversation_context(
            session_id=session_id,
            include_summary=True
        )
        
        # 情報の充足度を評価
        completeness_score = await self._evaluate_completeness(context)
        
        # 対話の段階を判定
        dialogue_stage = self._determine_dialogue_stage(context, completeness_score)
        
        if dialogue_stage == "action_plan" and completeness_score >= 95:
            # 十分な情報が集まった場合、アクションプラン生成
            action_plan = await self._generate_action_plan(context)
            return {
                "type": "action_plan",
                "data": action_plan,
                "completeness_score": completeness_score,
                "stage": dialogue_stage
            }
        else:
            # まだ情報が不足している場合、段階的な質問生成
            follow_up_questions = await self._generate_stage_based_questions(context, dialogue_stage)
            return {
                "type": "follow_up",
                "questions": follow_up_questions,
                "completeness_score": completeness_score,
                "stage": dialogue_stage,
                "stage_description": self._get_stage_description(dialogue_stage)
            }
    
    def _determine_dialogue_stage(self, context: Dict[str, Any], completeness_score: int) -> str:
        """対話の段階を判定"""
        messages = context.get("messages", [])
        message_count = len([msg for msg in messages if msg.get("role") == "user"])
        
        # メッセージ数と完了度スコアによる段階判定
        if message_count <= 1:
            return "initial_understanding"  # 初期理解段階
        elif message_count <= 3 and completeness_score < 40:
            return "problem_clarification"  # 課題明確化段階  
        elif message_count <= 5 and completeness_score < 70:
            return "deep_analysis"  # 深い分析段階
        elif completeness_score < 85:
            return "solution_exploration"  # 解決策探索段階
        elif completeness_score < 95:
            return "action_preparation"  # アクション準備段階
        else:
            return "action_plan"  # アクションプラン生成段階
    
    def _get_stage_description(self, stage: str) -> str:
        """段階の説明を取得"""
        descriptions = {
            "initial_understanding": "📋 初期状況の理解",
            "problem_clarification": "🎯 課題の明確化", 
            "deep_analysis": "🔍 詳細分析",
            "solution_exploration": "💡 解決策の探索",
            "action_preparation": "📝 アクション準備",
            "action_plan": "🚀 アクションプラン生成"
        }
        return descriptions.get(stage, "🤔 分析中")
    
    async def _generate_stage_based_questions(self, context: Dict[str, Any], stage: str) -> List[str]:
        """段階に基づいた質問生成"""
        if stage == "initial_understanding":
            return await self._generate_initial_questions(context)
        elif stage == "problem_clarification":
            return await self._generate_clarification_questions(context)
        elif stage == "deep_analysis":
            return await self._generate_analysis_questions(context)
        elif stage == "solution_exploration":
            return await self._generate_solution_questions(context)
        elif stage == "action_preparation":
            return await self._generate_preparation_questions(context)
        else:
            return await self._generate_follow_up_questions(context)
    
    async def _generate_initial_questions(self, context: Dict[str, Any]) -> List[str]:
        """初期理解のための質問生成"""
        messages = context.get("messages", [])
        latest_message = messages[-1].get("content", "") if messages else ""
        
        # 1on1の内容から抽象的な指示を特定
        if "距離を詰める" in latest_message or "信頼関係" in latest_message:
            return [
                "上司から「顧客との距離を詰める」という指摘がありましたが、具体的にどのような場面でそう感じられたのでしょうか？",
                "これまでの営業活動で、顧客との関係構築において最も困難だった瞬間はどんな時でしたか？",
                "現在、新規顧客とのやり取りで特に意識していることはありますか？"
            ]
        elif "相手の課題に寄り添った提案" in latest_message:
            return [
                "「相手の課題に寄り添った提案」について、これまでどのようなアプローチを取られていましたか？",
                "顧客のヒアリング時に、どんな質問をすることが多いですか？",
                "提案内容を決める際に、最も重視している点は何ですか？"
            ]
        elif "温度感を読む" in latest_message:
            return [
                "上司から「顧客の温度感を読む」という指摘がありましたが、これまでにそういった感覚を意識したことはありますか？",
                "商談中に、顧客の興味や関心度をどのように判断していますか？",
                "顧客が積極的な時と消極的な時の違いを、何で感じ取ることが多いですか？"
            ]
        else:
            return [
                "この1on1の内容について、どの部分が最も改善したいポイントだと感じますか？",
                "上司からのアドバイスで、特に具体的な方法を知りたいと思った部分はありますか？",
                "現在の営業活動で、最も不安に感じていることは何ですか？"
            ]
    
    async def _generate_clarification_questions(self, context: Dict[str, Any]) -> List[str]:
        """課題明確化のための質問生成"""
        return [
            "その課題が発生する典型的なシチュエーションを具体的に教えてください",
            "同じような状況で、うまくいった経験はありますか？その時は何が違いましたか？",
            "この課題によって、実際にどのような損失や機会損失が発生していますか？"
        ]
    
    async def _generate_analysis_questions(self, context: Dict[str, Any]) -> List[str]:
        """深い分析のための質問生成"""
        return [
            "その課題の根本的な原因は何だと思いますか？",
            "これまでに試したことがある解決策があれば教えてください",
            "理想的な状態になったとき、どのような変化が期待できますか？"
        ]
    
    async def _generate_solution_questions(self, context: Dict[str, Any]) -> List[str]:
        """解決策探索のための質問生成"""
        return [
            "解決策を実行する上で、どのようなサポートや資源が必要ですか？",
            "この改善に取り組む際の期限や目標はありますか？",
            "成功を測る具体的な指標があれば教えてください"
        ]
    
    async def _generate_preparation_questions(self, context: Dict[str, Any]) -> List[str]:
        """アクション準備のための質問生成"""
        return [
            "実行に移す前に不安な点や懸念はありますか？",
            "取り組みを始める最適なタイミングはいつ頃でしょうか？",
            "進捗を確認する方法や頻度はどうしますか？"
        ]
    
    async def _evaluate_completeness(self, context: Dict[str, Any]) -> int:
        """情報の充足度を評価"""
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        messages = [
            {"role": "system", "content": """営業スキル向上のアクションプラン作成に必要な情報の充足度を評価してください。

段階的評価基準：
【20-30点】課題の概要は理解できるが、具体性に欠ける
【40-50点】課題は明確だが、具体的な状況や背景情報が不足
【60-70点】課題と状況は明確だが、詳細な分析が必要
【80-85点】詳細は揃っているが、解決策の方向性が未確定
【90-95点】全ての情報が揃い、アクションプラン作成準備完了
【95点以上】アクションプラン生成に十分な情報

以下の観点で厳格に評価してください：
1. 課題の具体性（抽象的な指摘→具体的な場面）
2. 根本原因の把握（症状→原因の特定）
3. 目標と期限の明確化
4. 実行可能性の検証
5. 成功指標の定義

0-100のスコアで評価してください。数字のみ回答してください。"""},
            {"role": "user", "content": f"会話履歴：\n{context_str}\n\n充足度スコア（0-100）:"}
        ]
        
        from langchain.schema import HumanMessage, SystemMessage
        langchain_messages = [
            SystemMessage(content=messages[0]["content"]),
            HumanMessage(content=messages[1]["content"])
        ]
        response = await self.llm.ainvoke(langchain_messages)
        try:
            score = int(response.content.strip())
            return min(max(score, 0), 100)  # 0-100の範囲に制限
        except:
            return 50  # デフォルト値
    
    async def _generate_follow_up_questions(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """フォローアップ質問を生成"""
        # メモリから履歴を取得
        memory = await self.memory_service.get_or_create_memory(context["session_id"])
        messages = memory.chat_memory.messages
        
        # 会話履歴を文字列に変換
        chat_history = "\n".join([
            f"{msg.type}: {msg.content}" for msg in messages[-5:]  # 最新5メッセージ
        ])
        
        prompt_messages = [
            {"role": "system", "content": """これまでの会話内容を踏まえて、アクションプラン作成に必要な追加情報を収集するための質問を生成してください。
            
            以下の点に注意してください：
            1. すでに得られた情報を踏まえて、より具体的な質問をする
            2. 実践的で測定可能なアクションにつながる情報を収集する
            3. 営業スキル向上に直接関連する質問をする
            
            質問は1行ずつ「Q: 」で始めて3-5個回答してください。"""},
            {"role": "user", "content": f"会話履歴：\n{chat_history}\n\n追加で必要な情報を収集するための質問を生成してください。"}
        ]
        
        langchain_messages = [
            SystemMessage(content=prompt_messages[0]["content"]),
            HumanMessage(content=prompt_messages[1]["content"])
        ]
        response = await self.llm.ainvoke(langchain_messages)
        
        # レスポンスから質問を抽出
        questions = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line.startswith('Q:'):
                questions.append(line[2:].strip())
            elif line.startswith('質問'):
                questions.append(line.split(':', 1)[-1].strip())
        
        # 最低1つの質問を保証
        if not questions:
            questions = ["これまでの内容について、もう少し詳しく教えていただけますか？"]
        
        return questions[:5]  # 最大5個まで
    
    async def _generate_action_plan(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """アクションプランを生成"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """会話内容を基に、新人営業マンの成長のための
            具体的で実行可能なアクションプランを作成してください。
            
            以下の要素を含めてください：
            1. 具体的なアクションアイテム（優先順位付き）
            2. 各アクションの期限と成功指標
            3. 必要なリソースやサポート
            4. 期待される成果
            
            {format_instructions}
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "これまでの会話内容を基に、成長支援のためのアクションプランを作成してください。")
        ])
        
        memory = await self.memory_service.get_or_create_memory(context["session_id"])
        messages = memory.chat_memory.messages
        
        chain = (
            {
                "chat_history": lambda _: messages,
                "format_instructions": lambda _: self.action_plan_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.action_plan_parser
        )
        
        response = await chain.ainvoke({})
        
        # レスポンスを辞書形式に変換
        return {
            "action_items": response.action_items,
            "summary": response.summary,
            "key_improvements": response.key_improvements,
            "metrics": response.metrics,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def save_dialogue_state(
        self,
        session_id: str,
        state: str,
        metadata: Dict[str, Any],
        db_session: Any
    ) -> None:
        """対話の状態を保存"""
        # Redisに状態を保存
        state_key = f"dialogue:state:{session_id}"
        state_data = {
            "state": state,
            "metadata": metadata,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if self.memory_service.redis_client:
            await self.memory_service.redis_client.setex(
                state_key,
                86400,  # 24時間
                json.dumps(state_data, ensure_ascii=False)
            )
    
    async def get_dialogue_state(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """対話の状態を取得"""
        if not self.memory_service.redis_client:
            return None
        
        state_key = f"dialogue:state:{session_id}"
        state_data = await self.memory_service.redis_client.get(state_key)
        
        if state_data:
            return json.loads(state_data)
        return None