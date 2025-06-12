from typing import List, Dict, Any, Optional
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.memory.chat_memory import BaseChatMemory
from langchain_openai import ChatOpenAI
import json
from datetime import datetime
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.dialogue import DialogueSession, DialogueMessage, DialogueContext


class ConversationMemoryService:
    """LangChainを使用した会話履歴管理サービス"""
    
    def __init__(self):
        self.redis_client = None
        
        # モック環境かどうかによってLLMを初期化
        if settings.USE_MOCK_LLM or not settings.OPENAI_API_KEY:
            # モック環境では簡単なダミーLLMを使用
            self.llm = None  # モック時はNoneに設定
        else:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.3,
                api_key=settings.OPENAI_API_KEY
            )
    
    async def initialize(self):
        """Redis接続の初期化"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def get_or_create_memory(
        self, 
        session_id: str,
        max_token_limit: int = 2000
    ) -> ConversationSummaryBufferMemory:
        """セッション用のメモリインスタンスを取得または作成"""
        # Redis履歴ストレージ
        message_history = RedisChatMessageHistory(
            session_id=f"session:{session_id}",
            url=settings.REDIS_URL,
            key_prefix="dialogue:",
            ttl=86400  # 24時間
        )
        
        # 要約付きバッファメモリ
        memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            chat_memory=message_history,
            max_token_limit=max_token_limit,
            return_messages=True,
            memory_key="chat_history"
        )
        
        return memory
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        db: AsyncSession = None
    ):
        """メッセージを追加し、DBとRedisに保存"""
        # LangChainメモリに追加
        memory = await self.get_or_create_memory(session_id)
        
        if role == "user":
            memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            memory.chat_memory.add_ai_message(content)
        
        # DB操作はオプショナル（dbがNoneの場合はスキップ）
        if db is not None:
            try:
                session = await db.get(DialogueSession, session_id)
                if not session:
                    # セッションを作成
                    new_session = DialogueSession(
                        id=session_id,
                        user_id=session_id.replace("slack_", ""),
                        status="active"
                    )
                    db.add(new_session)
                    await db.commit()
                
                # メッセージを保存
                db_message = DialogueMessage(
                    session_id=session_id,
                    role=role,
                    content=content
                )
                db.add(db_message)
                await db.commit()
                await db.refresh(db_message)
                return db_message
            except Exception:
                # DB操作に失敗した場合は無視
                pass
        
        # 簡単なメッセージオブジェクトを返す
        class SimpleMessage:
            def __init__(self, session_id, role, content):
                self.session_id = session_id
                self.role = role
                self.content = content
                from datetime import datetime
                self.timestamp = datetime.utcnow()
        
        return SimpleMessage(session_id, role, content)
    
    async def get_conversation_context(
        self,
        session_id: str,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """現在の会話コンテキストを取得"""
        memory = await self.get_or_create_memory(session_id)
        
        # メッセージ履歴
        messages = memory.chat_memory.messages
        
        # コンテキスト構築
        context = {
            "session_id": session_id,
            "message_count": len(messages),
            "messages": [
                {
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content
                }
                for msg in messages
            ]
        }
        
        # 要約を含める場合
        if include_summary and len(messages) > 10:
            context["summary"] = await self._generate_summary(memory)
        
        return context
    
    async def _generate_summary(self, memory: ConversationSummaryBufferMemory) -> str:
        """会話の要約を生成"""
        # LangChainの要約機能を使用
        summary = memory.moving_summary_buffer
        if not summary:
            # 要約がない場合は生成
            messages = memory.chat_memory.messages
            if messages:
                summary = memory.predict_new_summary(
                    messages=messages,
                    existing_summary=""
                )
        return summary
    
    async def save_context_snapshot(
        self,
        session_id: str,
        db: AsyncSession,
        extracted_info: Dict[str, Any],
        completeness_score: int
    ) -> DialogueContext:
        """コンテキストのスナップショットを保存"""
        # 現在のコンテキストを取得
        context = await self.get_conversation_context(session_id)
        
        # 主要トピックを抽出
        key_topics = await self._extract_key_topics(context["messages"])
        
        # DBに保存
        snapshot = DialogueContext(
            session_id=session_id,
            extracted_info=extracted_info,
            completeness_score=completeness_score,
            key_topics=key_topics,
            message_count=context["message_count"]
        )
        
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        
        return snapshot
    
    async def _extract_key_topics(self, messages: List[Dict[str, str]]) -> List[str]:
        """会話から主要トピックを抽出"""
        if not messages:
            return []
        
        # 最近のメッセージから抽出
        recent_messages = messages[-10:]  # 最新10件
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in recent_messages
        ])
        
        prompt = f"""
        以下の会話から主要なトピックを3-5個抽出してください。
        JSONフォーマットで返してください。
        
        会話:
        {conversation_text}
        
        フォーマット例:
        ["トピック1", "トピック2", "トピック3"]
        """
        
        # モック環境またはLLMが無い場合
        if self.llm is None:
            # 簡単なキーワードベースの抽出
            keywords = ["営業", "顧客", "提案", "課題", "改善", "目標"]
            found_keywords = [kw for kw in keywords if kw in conversation_text]
            return found_keywords[:3]
        
        try:
            response = await self.llm.ainvoke(prompt)
            topics = json.loads(response.content)
            return topics[:5]  # 最大5個
        except Exception as e:
            # エラーの場合は空のリストを返す
            return []
    
    async def clear_session(self, session_id: str):
        """セッションの会話履歴をクリア"""
        memory = await self.get_or_create_memory(session_id)
        memory.clear()
        
        # Redisからも削除
        if self.redis_client:
            pattern = f"dialogue:session:{session_id}:*"
            async for key in self.redis_client.scan_iter(match=pattern):
                await self.redis_client.delete(key)
    
    async def get_similar_conversations(
        self,
        session_id: str,
        user_id: str,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """類似の過去の会話を取得"""
        # 現在のセッションのコンテキスト取得
        current_context = await db.execute(
            select(DialogueContext)
            .where(DialogueContext.session_id == session_id)
            .order_by(DialogueContext.created_at.desc())
            .limit(1)
        )
        current = current_context.scalar_one_or_none()
        
        if not current or not current.key_topics:
            return []
        
        # 類似トピックを持つセッションを検索
        similar_sessions = await db.execute(
            select(DialogueContext, DialogueSession)
            .join(DialogueSession)
            .where(
                DialogueSession.user_id == user_id,
                DialogueSession.id != session_id,
                DialogueContext.key_topics.op('@>')(current.key_topics[0])  # PostgreSQL JSONB演算子
            )
            .order_by(DialogueContext.completeness_score.desc())
            .limit(limit)
        )
        
        results = []
        for ctx, session in similar_sessions:
            results.append({
                "session_id": str(session.id),
                "started_at": session.started_at.isoformat(),
                "key_topics": ctx.key_topics,
                "completeness_score": ctx.completeness_score,
                "message_count": ctx.message_count
            })
        
        return results