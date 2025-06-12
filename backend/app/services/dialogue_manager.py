from typing import Dict, Any, List, Optional, Tuple
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
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
        
        if completeness_score >= 80:
            # 十分な情報が集まった場合、アクションプラン生成
            action_plan = await self._generate_action_plan(context)
            return {
                "type": "action_plan",
                "data": action_plan,
                "completeness_score": completeness_score
            }
        else:
            # まだ情報が不足している場合、追加質問生成
            follow_up_questions = await self._generate_follow_up_questions(context)
            return {
                "type": "follow_up",
                "questions": follow_up_questions,
                "completeness_score": completeness_score
            }
    
    async def _evaluate_completeness(self, context: Dict[str, Any]) -> int:
        """情報の充足度を評価"""
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        messages = [
            {"role": "system", "content": """営業スキル向上のアクションプラン作成に必要な情報の充足度を評価してください。
            
            以下の観点で評価してください：
            1. 現在の課題や悩みが明確か
            2. 具体的な状況や事例があるか
            3. 目標や期待される成果が明確か
            4. 現在のスキルレベルが把握できるか
            5. 利用可能なリソースや制約が明確か
            
            0-100のスコアで評価してください。数字のみ回答してください。"""},
            {"role": "user", "content": f"会話履歴：\n{context_str}\n\n充足度スコア（0-100）:"}
        ]
        
        response = await self.llm.ainvoke(messages)
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
        
        response = await self.llm.ainvoke(prompt_messages)
        
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