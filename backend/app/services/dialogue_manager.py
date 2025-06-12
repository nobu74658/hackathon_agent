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
from app.services.one_on_one_analyzer import OneOnOneAnalyzer
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
        self.one_on_one_analyzer = OneOnOneAnalyzer()
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.question_parser = PydanticOutputParser(pydantic_object=QuestionResponse)
        self.action_plan_parser = PydanticOutputParser(pydantic_object=ActionPlanResponse)
        
        # インメモリの1on1セッション状態管理（Redisがない場合の代替）
        self._in_memory_sessions: Dict[str, Dict[str, Any]] = {}
    
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
        
        # 1on1ミーティングの内容かどうかを判定
        is_one_on_one = self._is_one_on_one_content(user_response)
        
        if is_one_on_one:
            # 1on1の場合は対話型具体化プロセスを開始
            user_id = session_id.replace("slack_", "")
            
            try:
                # 1on1の初期分析を実行（上司の指示特定のみ）
                abstract_instructions = await self._extract_supervisor_instructions_from_one_on_one(
                    user_response, db_session
                )
                
                # 対話セッションの状態を保存
                await self._save_one_on_one_session_state(
                    session_id, 
                    user_response, 
                    abstract_instructions,
                    db_session
                )
                
                # 最初の深掘り質問を生成
                first_questions = await self._generate_initial_clarification_questions(
                    abstract_instructions[0] if abstract_instructions else None,
                    user_response
                )
                
                return {
                    "type": "one_on_one_clarification",
                    "questions": first_questions,
                    "instruction_being_clarified": abstract_instructions[0] if abstract_instructions else None,
                    "total_instructions": len(abstract_instructions),
                    "current_instruction_index": 0,
                    "stage": "instruction_clarification",
                    "stage_description": f"📋 上司の指示の具体化 (1/{len(abstract_instructions)})"
                }
                
            except Exception as e:
                return {
                    "type": "error", 
                    "message": f"1on1分析開始中にエラーが発生しました: {str(e)}"
                }
        else:
            # 1on1セッション継続中かチェック
            one_on_one_session = await self._get_one_on_one_session_state(session_id)
            
            if one_on_one_session:
                # 1on1セッション継続中 - 深掘り質問への回答を処理
                try:
                    return await self._continue_one_on_one_clarification(
                        session_id, 
                        user_response, 
                        one_on_one_session,
                        db_session
                    )
                except Exception as e:
                    return {
                        "type": "error",
                        "message": f"1on1セッション継続中にエラーが発生しました: {str(e)}"
                    }
            
            # 従来の質問ベースの対話
            context = await self.memory_service.get_conversation_context(
                session_id=session_id,
                include_summary=True
            )
            
            completeness_score = await self._evaluate_completeness(context)
            
            if completeness_score >= 80:
                action_plan = await self._generate_action_plan(context)
                return {
                    "type": "action_plan",
                    "data": action_plan,
                    "completeness_score": completeness_score
                }
            else:
                follow_up_questions = await self._generate_follow_up_questions(context)
                return {
                    "type": "follow_up",
                    "questions": follow_up_questions,
                    "completeness_score": completeness_score
                }
    
    def _is_one_on_one_content(self, content: str) -> bool:
        """1on1ミーティングの内容かどうかを判定"""
        
        # 1on1の特徴的なパターンを検出
        one_on_one_indicators = [
            # 対話形式
            "：" in content and content.count("：") >= 2,  # 複数の話者
            # 上司からの典型的なフィードバック
            "距離を詰める" in content,
            "信頼関係" in content,
            "温度感" in content,
            "課題に寄り添った" in content,
            "もう少し" in content and "といいね" in content,
            "がカギだと思う" in content,
            "を意識して" in content,
            # 営業活動への言及
            "営業活動" in content and "調子" in content,
            "新規アポ" in content,
            "成約" in content,
            # 長めのテキスト（1on1の内容は通常長い）
            len(content) > 100
        ]
        
        # 複数の指標が当てはまる場合は1on1と判定
        matching_indicators = sum(1 for indicator in one_on_one_indicators if indicator)
        return matching_indicators >= 3
    
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
    
    # === 1on1対話型具体化システム ===
    
    async def _extract_supervisor_instructions_from_one_on_one(
        self, 
        one_on_one_content: str, 
        db_session: Any
    ) -> List[Dict[str, str]]:
        """LLMを使って1on1から上司の抽象的指示を特定"""
        
        prompt_messages = [
            SystemMessage(content="""1on1ミーティングの内容から、上司が新人営業マンに対して出した抽象的な指示や改善点を特定してください。

以下の基準で「抽象的な指示」を特定してください：
- 新人営業マンが「具体的にどうすればいいのかわからない」と感じるような指示
- 「もっと〜する」「〜を意識する」「〜していけるといいね」のような表現
- 具体的な行動手順が明確でない改善提案

必ず以下のJSON形式で回答してください：
```json
{
  "abstract_instructions": [
    {
      "original_text": "上司の発言そのまま",
      "abstract_concept": "抽象的な概念（例：距離を詰める、信頼関係構築）",
      "category": "カテゴリ（customer_relationship, trust_building, communication等）",
      "urgency": "優先度（high, medium, low）"
    }
  ]
}
```"""),
            HumanMessage(content=f"以下の1on1内容から抽象的な指示を特定してください：\n\n{one_on_one_content}")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            response_text = response.content.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            parsed_response = json.loads(response_text)
            return parsed_response.get("abstract_instructions", [])
            
        except Exception as e:
            # エラーの場合は基本的な指示を返す
            return [{
                "original_text": "上司からの改善指示",
                "abstract_concept": "営業スキル向上",
                "category": "general_improvement",
                "urgency": "medium"
            }]
    
    async def _save_one_on_one_session_state(
        self, 
        session_id: str, 
        original_content: str, 
        instructions: List[Dict[str, str]],
        db_session: Any
    ) -> None:
        """1on1セッションの状態を保存"""
        
        state_data = {
            "type": "one_on_one_clarification",
            "original_content": original_content,
            "abstract_instructions": instructions,
            "current_instruction_index": 0,
            "clarified_instructions": [],  # 具体化された指示を保存
            "conversation_history": [],  # 各指示の具体化対話履歴
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Redisに保存を試行、失敗したらインメモリに保存
        if self.memory_service.redis_client:
            try:
                session_key = f"one_on_one_session:{session_id}"
                await self.memory_service.redis_client.setex(
                    session_key,
                    86400,  # 24時間
                    json.dumps(state_data, ensure_ascii=False)
                )
            except Exception:
                # Redisエラーの場合はインメモリにフォールバック
                self._in_memory_sessions[session_id] = state_data
        else:
            # Redisがない場合はインメモリに保存
            self._in_memory_sessions[session_id] = state_data
    
    async def _get_one_on_one_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """1on1セッションの状態を取得"""
        
        # まずRedisから取得を試行
        if self.memory_service.redis_client:
            try:
                session_key = f"one_on_one_session:{session_id}"
                state_data = await self.memory_service.redis_client.get(session_key)
                if state_data:
                    return json.loads(state_data)
            except Exception:
                pass  # Redisエラーの場合はインメモリから取得
        
        # Redisがない場合やエラーの場合はインメモリから取得
        return self._in_memory_sessions.get(session_id)
    
    async def _generate_initial_clarification_questions(
        self, 
        instruction: Dict[str, str], 
        original_content: str
    ) -> List[str]:
        """最初の深掘り質問を生成"""
        
        if not instruction:
            return ["1on1の内容について、どの部分を最も改善したいと感じていますか？"]
        
        abstract_concept = instruction.get("abstract_concept", "")
        original_text = instruction.get("original_text", "")
        
        prompt_messages = [
            SystemMessage(content=f"""新人営業マンが上司から「{abstract_concept}」という抽象的な指示を受けました。
この指示を具体的な行動レベルまで落とし込むために、最初の深掘り質問を3-4個生成してください。

質問の目的：
- 新人がどのような場面で困っているのかを特定
- 現在の行動パターンを把握
- 具体的な改善点を見つける

質問は以下の形式で：
1. 現状把握の質問
2. 困難な場面の特定
3. 理想的な状態の確認
4. 具体的な行動への言及

1行ずつ「Q: 」で始まる形式で回答してください。"""),
            HumanMessage(content=f"上司の指示: \"{original_text}\"\n抽象概念: {abstract_concept}\n\n深掘り質問を生成してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            
            # 質問を抽出
            questions = []
            for line in response.content.split('\n'):
                line = line.strip()
                if line.startswith('Q:'):
                    questions.append(line[2:].strip())
                elif line.startswith('質問') and ':' in line:
                    questions.append(line.split(':', 1)[-1].strip())
                elif line and not line.startswith(('1.', '2.', '3.', '4.', '-', '・')):
                    # 番号なしの質問も拾う
                    if '？' in line or '?' in line:
                        questions.append(line)
            
            return questions[:4] if questions else [
                f"「{abstract_concept}」について、どのような場面で最も困難を感じますか？",
                f"現在、{abstract_concept}のためにどのような取り組みをしていますか？",
                f"理想的には{abstract_concept}がどのような状態になれば良いと思いますか？"
            ]
            
        except Exception:
            return [
                f"「{abstract_concept}」について、どのような場面で最も困難を感じますか？",
                f"現在、{abstract_concept}のためにどのような取り組みをしていますか？"
            ]
    
    async def _continue_one_on_one_clarification(
        self, 
        session_id: str, 
        user_response: str, 
        session_state: Dict[str, Any],
        db_session: Any
    ) -> Dict[str, Any]:
        """1on1具体化プロセスの継続処理（自律的な判断）"""
        
        current_index = session_state.get("current_instruction_index", 0)
        instructions = session_state.get("abstract_instructions", [])
        conversation_history = session_state.get("conversation_history", [])
        
        if current_index >= len(instructions):
            # 全ての指示が処理済み → 最終アクションプラン生成
            return await self._generate_final_action_plan_from_session(session_id, session_state, db_session)
        
        current_instruction = instructions[current_index]
        
        # 現在の対話履歴に新人の回答を追加
        if current_index < len(conversation_history):
            conversation_history[current_index].append({
                "role": "user",
                "content": user_response,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            # 新しい指示の対話開始
            conversation_history.append([{
                "role": "user", 
                "content": user_response,
                "timestamp": datetime.utcnow().isoformat()
            }])
        
        # 具体性をチェック
        concreteness_result = await self._check_instruction_concreteness(
            current_instruction, 
            conversation_history[current_index],
            user_response
        )
        
        is_concrete = concreteness_result.get("is_concrete", False)
        concreteness_score = concreteness_result.get("score", 0)
        missing_details = concreteness_result.get("missing_details", [])
        
        if is_concrete and concreteness_score >= 80:
            # 十分具体的 → 次の指示へ移動
            session_state["clarified_instructions"].append({
                "instruction": current_instruction,
                "conversation": conversation_history[current_index],
                "final_response": user_response,
                "concreteness_score": concreteness_score,
                "clarified_at": datetime.utcnow().isoformat()
            })
            
            session_state["current_instruction_index"] = current_index + 1
            session_state["conversation_history"] = conversation_history
            
            # セッション状態を更新
            await self._update_one_on_one_session_state(session_id, session_state)
            
            # 次の指示があるかチェック
            if current_index + 1 < len(instructions):
                next_instruction = instructions[current_index + 1]
                next_questions = await self._generate_initial_clarification_questions(
                    next_instruction, 
                    session_state.get("original_content", "")
                )
                
                return {
                    "type": "one_on_one_clarification",
                    "questions": next_questions,
                    "instruction_being_clarified": next_instruction,
                    "total_instructions": len(instructions),
                    "current_instruction_index": current_index + 1,
                    "stage": "instruction_clarification",
                    "stage_description": f"📋 上司の指示の具体化 ({current_index + 2}/{len(instructions)})",
                    "previous_instruction_completed": current_instruction.get("abstract_concept", ""),
                    "concreteness_achieved": concreteness_score
                }
            else:
                # 全ての指示が具体化完了 → 最終アクションプラン生成
                return await self._generate_final_action_plan_from_session(session_id, session_state, db_session)
        
        else:
            # まだ抽象的 → より深い質問を生成
            deeper_questions = await self._generate_deeper_clarification_questions(
                current_instruction,
                conversation_history[current_index],
                missing_details,
                concreteness_score
            )
            
            # 対話履歴にAIの質問を追加
            conversation_history[current_index].append({
                "role": "assistant",
                "content": f"深掘り質問: {deeper_questions}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            session_state["conversation_history"] = conversation_history
            await self._update_one_on_one_session_state(session_id, session_state)
            
            return {
                "type": "one_on_one_clarification",
                "questions": deeper_questions,
                "instruction_being_clarified": current_instruction,
                "total_instructions": len(instructions),
                "current_instruction_index": current_index,
                "stage": "instruction_clarification",
                "stage_description": f"📋 上司の指示の具体化 ({current_index + 1}/{len(instructions)}) - 更に詳しく",
                "concreteness_feedback": f"具体性: {concreteness_score}% - より詳細な情報が必要です",
                "missing_aspects": missing_details[:3]  # 最大3つの不足要素を表示
            }
    
    async def _check_instruction_concreteness(
        self, 
        instruction: Dict[str, str], 
        conversation_history: List[Dict[str, str]],
        latest_response: str
    ) -> Dict[str, Any]:
        """指示の具体性をLLMでチェック"""
        
        abstract_concept = instruction.get("abstract_concept", "")
        
        # 会話履歴をテキスト化
        conversation_text = "\\n".join([
            f"{entry['role']}: {entry['content']}" for entry in conversation_history
        ])
        
        prompt_messages = [
            SystemMessage(content=f"""営業コーチとして、新人営業マンの回答が十分具体的かを評価してください。

評価対象の抽象的指示: "{abstract_concept}"

具体性の基準：
- 明日から実行できる具体的な行動が明確か
- 頻度、タイミング、方法が具体的に示されているか
- 新人が「何をすればいいかわからない」状態を脱却できているか
- 測定可能な要素があるか

例：
❌ 抽象的: "もっと相手の気持ちを理解する"
✅ 具体的: "商談開始時に3分間、相手の最近の業務状況を質問し、メモを取る"

以下のJSON形式で評価してください：
```json
{{
  "is_concrete": true/false,
  "score": 0-100,
  "missing_details": ["不足している具体的要素1", "不足している具体的要素2"],
  "concrete_aspects": ["具体的になっている要素1", "具体的になっている要素2"],
  "next_focus": "次に重点的に聞くべき点"
}}
```"""),
            HumanMessage(content=f"会話履歴：\\n{conversation_text}\\n\\n最新の回答: {latest_response}\\n\\n具体性を評価してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            response_text = response.content.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            return json.loads(response_text)
            
        except Exception:
            # エラーの場合はもう少し深掘りが必要と判定
            return {
                "is_concrete": False,
                "score": 40,
                "missing_details": ["具体的な手順", "実行タイミング", "測定方法"],
                "concrete_aspects": [],
                "next_focus": "より詳細な実行方法"
            }
    
    async def _update_one_on_one_session_state(self, session_id: str, state_data: Dict[str, Any]) -> None:
        """1on1セッション状態を更新"""
        # Redisに保存を試行、失敗したらインメモリに保存
        if self.memory_service.redis_client:
            try:
                session_key = f"one_on_one_session:{session_id}"
                await self.memory_service.redis_client.setex(
                    session_key,
                    86400,  # 24時間
                    json.dumps(state_data, ensure_ascii=False)
                )
            except Exception:
                # Redisエラーの場合はインメモリにフォールバック
                self._in_memory_sessions[session_id] = state_data
        else:
            # Redisがない場合はインメモリに保存
            self._in_memory_sessions[session_id] = state_data
    
    async def _generate_deeper_clarification_questions(
        self, 
        instruction: Dict[str, str], 
        conversation_history: List[Dict[str, str]],
        missing_details: List[str],
        concreteness_score: int
    ) -> List[str]:
        """より深い具体化質問を生成"""
        
        abstract_concept = instruction.get("abstract_concept", "")
        
        # 会話履歴をテキスト化
        conversation_text = "\\n".join([
            f"{entry['role']}: {entry['content']}" for entry in conversation_history
        ])
        
        prompt_messages = [
            SystemMessage(content=f"""新人営業マンの回答はまだ抽象的です（具体性: {concreteness_score}%）。
更に具体的な質問をして、明日から実行できるレベルまで落とし込んでください。

対象の抽象的指示: "{abstract_concept}"
不足している要素: {missing_details}

より深い質問の観点：
- 具体的な場面・シチュエーション
- 実行する頻度とタイミング
- 具体的な手順・ステップ
- 測定・確認方法
- 必要なツールや準備

「相手に合わせたトーンと話し方を意識する」のような抽象的な回答を避け、
「商談開始時に、相手の話すスピードに合わせて自分も話すスピードを調整し、
相手が専門用語を使う場合は同レベルの用語で、使わない場合は分かりやすい言葉で説明する」
のような具体性を引き出してください。

1行ずつ「Q: 」で始まる形式で2-3個の質問を生成してください。"""),
            HumanMessage(content=f"これまでの会話：\\n{conversation_text}\\n\\nより具体的にするための深掘り質問を生成してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            
            # 質問を抽出
            questions = []
            for line in response.content.split('\\n'):
                line = line.strip()
                if line.startswith('Q:'):
                    questions.append(line[2:].strip())
                elif '？' in line or '?' in line:
                    if not line.startswith(('例：', '※', '注：')):
                        questions.append(line)
            
            return questions[:3] if questions else [
                f"「{abstract_concept}」を実行する具体的な場面を教えてください（どんな時に、誰に対して、どのように？）",
                f"その行動をどのくらいの頻度で実行しますか？（毎日、週1回、商談毎など）",
                f"うまくできているかどうかを、どのように確認・測定しますか？"
            ]
            
        except Exception:
            return [
                f"「{abstract_concept}」を実行する具体的な場面を教えてください",
                f"その行動の具体的な手順を教えてください",
                f"成果をどのように測定しますか？"
            ]
    
    async def _generate_final_action_plan_from_session(
        self, 
        session_id: str, 
        session_state: Dict[str, Any], 
        db_session: Any
    ) -> Dict[str, Any]:
        """対話型具体化プロセスから最終アクションプランを生成"""
        
        clarified_instructions = session_state.get("clarified_instructions", [])
        original_content = session_state.get("original_content", "")
        
        if not clarified_instructions:
            return {
                "type": "error",
                "message": "具体化された指示がありません。もう一度1on1の内容から始めてください。"
            }
        
        # 具体化された全ての指示をまとめる
        all_clarifications = []
        for clarified in clarified_instructions:
            instruction = clarified["instruction"]
            conversation = clarified["conversation"]
            final_response = clarified["final_response"]
            
            all_clarifications.append({
                "original_abstract": instruction.get("abstract_concept", ""),
                "clarification_conversation": conversation,
                "concrete_outcome": final_response,
                "concreteness_score": clarified.get("concreteness_score", 0)
            })
        
        # LLMに最終アクションプラン生成を依頼
        clarifications_text = "\\n\\n".join([
            f"指示: {c['original_abstract']}\\n具体化結果: {c['concrete_outcome']}"
            for c in all_clarifications
        ])
        
        prompt_messages = [
            SystemMessage(content=f"""新人営業マンとの対話を通じて、上司の抽象的な指示が具体化されました。
これらの具体化された内容を統合して、実践的な最終アクションプランを作成してください。

以下のJSON形式で回答してください：
```json
{{
  "final_summary": {{
    "title": "1on1フィードバック 最終アクションプラン",
    "priority_actions": [
      {{
        "action": "具体的なアクション",
        "specific_steps": ["ステップ1", "ステップ2", "ステップ3"],
        "frequency": "実行頻度",
        "measurement": "成果測定方法"
      }}
    ],
    "implementation_timeline": {{
      "immediately": "今すぐ実行すること",
      "this_week": "今週中に実行すること", 
      "this_month": "今月中に実行すること"
    }},
    "success_metrics": [
      {{
        "metric": "測定指標",
        "target": "目標値",
        "how_to_measure": "測定方法"
      }}
    ],
    "next_steps": ["次のステップ1", "次のステップ2"]
  }},
  "dialogue_summary": {{
    "instructions_clarified": {len(clarified_instructions)},
    "total_interactions": "対話の総数",
    "key_insights": ["洞察1", "洞察2"],
    "concreteness_improvement": "具体性の向上度"
  }}
}}
```

重要: 全て新人営業マンが明日から実行できる具体的な内容にしてください。"""),
            HumanMessage(content=f"元の1on1内容：\\n{original_content}\\n\\n具体化された指示：\\n{clarifications_text}\\n\\n最終アクションプランを生成してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            response_text = response.content.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            action_plan_data = json.loads(response_text)
            
            # 1on1セッションを完了としてマーク（削除）
            if self.memory_service.redis_client:
                try:
                    session_key = f"one_on_one_session:{session_id}"
                    await self.memory_service.redis_client.delete(session_key)
                except Exception:
                    pass  # Redisエラーは無視
            
            # インメモリからも削除
            if session_id in self._in_memory_sessions:
                del self._in_memory_sessions[session_id]
            
            return {
                "type": "one_on_one_final_plan",
                "data": action_plan_data,
                "clarification_history": all_clarifications,
                "analysis_method": "dialogue_based_concretization"
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"最終アクションプラン生成中にエラーが発生しました: {str(e)}"
            }