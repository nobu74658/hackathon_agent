"""
過去の会話履歴を管理し、洞察を抽出するサービス
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.models.dialogue import (
    DialogueSession, DialogueMessage, DialogueContext,
    ConversationInsight, UserProfile, ConversationPattern
)
from app.core.config import settings


class InsightExtraction(BaseModel):
    """洞察抽出の結果"""
    insights: List[Dict[str, Any]] = Field(description="抽出された洞察のリスト")
    patterns: List[Dict[str, Any]] = Field(description="識別されたパターン")
    user_characteristics: Dict[str, Any] = Field(description="ユーザーの特性")


class ConversationSummary(BaseModel):
    """会話サマリー"""
    main_topics: List[str] = Field(description="主要なトピック")
    challenges_identified: List[str] = Field(description="特定された課題")
    solutions_discussed: List[str] = Field(description="議論された解決策")
    user_sentiment: str = Field(description="ユーザーの感情状態")
    progress_made: str = Field(description="進捗状況")


class ConversationHistoryService:
    """過去の会話履歴を活用するサービス"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
        self.insight_parser = PydanticOutputParser(pydantic_object=InsightExtraction)
        self.summary_parser = PydanticOutputParser(pydantic_object=ConversationSummary)
    
    async def get_user_conversation_history(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 10,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """ユーザーの過去の会話履歴を取得"""
        
        # 指定期間内のセッションを取得
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        sessions = await db.execute(
            select(DialogueSession)
            .where(
                and_(
                    DialogueSession.user_id == user_id,
                    DialogueSession.created_at >= cutoff_date
                )
            )
            .order_by(desc(DialogueSession.created_at))
            .limit(limit)
        )
        
        history = []
        for session in sessions.scalars():
            # セッションのメッセージを取得
            messages = await db.execute(
                select(DialogueMessage)
                .where(DialogueMessage.session_id == session.id)
                .order_by(DialogueMessage.timestamp)
            )
            
            # コンテキストを取得
            context = await db.execute(
                select(DialogueContext)
                .where(DialogueContext.session_id == session.id)
            )
            context_data = context.scalar_one_or_none()
            
            history.append({
                "session_id": session.id,
                "created_at": session.created_at,
                "status": session.status,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp
                    }
                    for msg in messages.scalars()
                ],
                "context": {
                    "extracted_info": context_data.extracted_info if context_data else {},
                    "completeness_score": context_data.completeness_score if context_data else 0,
                    "key_topics": context_data.key_topics if context_data else []
                }
            })
        
        return history
    
    async def extract_insights_from_history(
        self,
        user_id: str,
        conversation_history: List[Dict[str, Any]]
    ) -> InsightExtraction:
        """会話履歴から洞察を抽出"""
        
        # 会話履歴を文字列に変換
        history_text = self._format_conversation_history(conversation_history)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは営業トレーニングの専門家です。
            ユーザーの過去の会話履歴を分析し、以下の洞察を抽出してください：
            
            1. ユーザーが繰り返し直面している課題
            2. ユーザーの強みと弱み
            3. 学習スタイルや好み
            4. 行動パターン
            5. 改善の傾向
            
            {format_instructions}"""),
            ("user", f"ユーザーID: {user_id}\n\n会話履歴:\n{history_text}")
        ])
        
        chain = prompt | self.llm | self.insight_parser
        
        result = await chain.ainvoke({
            "format_instructions": self.insight_parser.get_format_instructions()
        })
        
        return result
    
    async def save_insights(
        self,
        user_id: str,
        session_id: str,
        insights: InsightExtraction,
        db: AsyncSession
    ) -> List[ConversationInsight]:
        """抽出した洞察をデータベースに保存"""
        
        saved_insights = []
        
        for insight in insights.insights:
            db_insight = ConversationInsight(
                session_id=session_id,
                user_id=user_id,
                insight_type=insight.get("type", "general"),
                content=insight.get("content", ""),
                confidence_score=insight.get("confidence", 0.5),
                metadata={
                    "source_sessions": insight.get("source_sessions", []),
                    "frequency": insight.get("frequency", 1)
                }
            )
            db.add(db_insight)
            saved_insights.append(db_insight)
        
        await db.commit()
        return saved_insights
    
    async def update_user_profile(
        self,
        user_id: str,
        insights: InsightExtraction,
        db: AsyncSession
    ) -> UserProfile:
        """ユーザープロファイルを更新"""
        
        # 既存のプロファイルを取得または作成
        profile = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile.scalar_one_or_none()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
        
        # 洞察からプロファイルを更新
        characteristics = insights.user_characteristics
        
        # 課題の更新
        if "challenges" in characteristics:
            existing_challenges = set(profile.common_challenges or [])
            new_challenges = set(characteristics["challenges"])
            profile.common_challenges = list(existing_challenges | new_challenges)
        
        # 強みの更新
        if "strengths" in characteristics:
            existing_strengths = set(profile.strengths or [])
            new_strengths = set(characteristics["strengths"])
            profile.strengths = list(existing_strengths | new_strengths)
        
        # 改善領域の更新
        if "improvement_areas" in characteristics:
            profile.improvement_areas = characteristics["improvement_areas"]
        
        # 学習スタイルの更新
        if "learning_style" in characteristics:
            profile.preferred_learning_style = characteristics["learning_style"]
        
        # セッション数を増加
        profile.total_sessions += 1
        
        await db.commit()
        await db.refresh(profile)
        
        return profile
    
    async def save_conversation_patterns(
        self,
        user_id: str,
        patterns: List[Dict[str, Any]],
        db: AsyncSession
    ) -> List[ConversationPattern]:
        """会話パターンを保存"""
        
        saved_patterns = []
        
        for pattern in patterns:
            # 既存のパターンを確認
            existing = await db.execute(
                select(ConversationPattern)
                .where(
                    and_(
                        ConversationPattern.user_id == user_id,
                        ConversationPattern.pattern_type == pattern["type"]
                    )
                )
            )
            existing_pattern = existing.scalar_one_or_none()
            
            if existing_pattern:
                # 既存パターンを更新
                existing_pattern.frequency += 1
                existing_pattern.pattern_data = pattern.get("data", {})
                existing_pattern.last_observed = datetime.utcnow()
                saved_patterns.append(existing_pattern)
            else:
                # 新しいパターンを作成
                new_pattern = ConversationPattern(
                    user_id=user_id,
                    pattern_type=pattern["type"],
                    pattern_data=pattern.get("data", {}),
                    frequency=1
                )
                db.add(new_pattern)
                saved_patterns.append(new_pattern)
        
        await db.commit()
        return saved_patterns
    
    async def get_relevant_past_insights(
        self,
        user_id: str,
        current_topic: str,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """現在のトピックに関連する過去の洞察を取得"""
        
        # アクティブな洞察を取得
        insights = await db.execute(
            select(ConversationInsight)
            .where(
                and_(
                    ConversationInsight.user_id == user_id,
                    ConversationInsight.is_active == True
                )
            )
            .order_by(desc(ConversationInsight.confidence_score))
            .limit(limit * 2)  # 関連性でフィルタするため多めに取得
        )
        
        # トピックとの関連性を評価
        relevant_insights = []
        for insight in insights.scalars():
            relevance_score = await self._calculate_relevance(
                insight.content,
                current_topic
            )
            
            if relevance_score > 0.5:
                relevant_insights.append({
                    "type": insight.insight_type,
                    "content": insight.content,
                    "confidence": insight.confidence_score,
                    "relevance": relevance_score,
                    "created_at": insight.created_at
                })
        
        # 関連性でソートして上位を返す
        relevant_insights.sort(key=lambda x: x["relevance"], reverse=True)
        return relevant_insights[:limit]
    
    async def _calculate_relevance(
        self,
        insight_content: str,
        current_topic: str
    ) -> float:
        """洞察と現在のトピックの関連性を計算"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """以下の2つのテキストの関連性を0.0から1.0のスコアで評価してください。
            
            評価基準:
            - 1.0: 非常に関連性が高い（同じトピックや直接的な関係）
            - 0.7-0.9: 関連性が高い（関連するトピックや間接的な関係）
            - 0.4-0.6: 中程度の関連性
            - 0.1-0.3: 低い関連性
            - 0.0: 関連性なし
            
            数値のみを返してください。"""),
            ("user", f"テキスト1（洞察）: {insight_content}\n\nテキスト2（現在のトピック）: {current_topic}")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            score = float(response.content.strip())
            return max(0.0, min(1.0, score))
        except:
            return 0.0
    
    async def generate_personalized_questions(
        self,
        user_id: str,
        current_context: Dict[str, Any],
        user_profile: UserProfile,
        past_insights: List[Dict[str, Any]]
    ) -> List[str]:
        """過去の履歴に基づいてパーソナライズされた質問を生成"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは営業トレーニングの専門家です。
            ユーザーの過去の会話履歴と現在のコンテキストに基づいて、
            最も効果的な質問を生成してください。
            
            ユーザープロファイル:
            - よくある課題: {common_challenges}
            - 強み: {strengths}
            - 学習スタイル: {learning_style}
            
            過去の洞察:
            {past_insights}
            
            現在のコンテキスト:
            {current_context}
            
            以下の原則に従ってください:
            1. ユーザーの過去の経験を活用する
            2. 既に議論した内容を繰り返さない
            3. ユーザーの学習スタイルに合わせる
            4. 具体的で実践的な質問にする
            5. 質問数は3個以内に抑える"""),
            ("user", "パーソナライズされた質問を生成してください。")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(
            common_challenges=json.dumps(user_profile.common_challenges or [], ensure_ascii=False),
            strengths=json.dumps(user_profile.strengths or [], ensure_ascii=False),
            learning_style=user_profile.preferred_learning_style or "不明",
            past_insights=json.dumps(past_insights, ensure_ascii=False),
            current_context=json.dumps(current_context, ensure_ascii=False)
        ))
        
        # 質問を抽出
        questions = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                clean_line = line.lstrip('1234567890.-・ ')
                if clean_line:
                    questions.append(clean_line)
        
        return questions[:3]
    
    async def summarize_conversation(
        self,
        messages: List[Dict[str, str]]
    ) -> ConversationSummary:
        """会話をサマライズ"""
        
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """以下の会話を分析し、サマリーを作成してください。
            
            {format_instructions}"""),
            ("user", f"会話:\n{conversation_text}")
        ])
        
        chain = prompt | self.llm | self.summary_parser
        
        result = await chain.ainvoke({
            "format_instructions": self.summary_parser.get_format_instructions()
        })
        
        return result
    
    def _format_conversation_history(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """会話履歴をテキスト形式にフォーマット"""
        
        formatted = []
        for session in conversation_history:
            formatted.append(f"\n=== セッション: {session['session_id']} ({session['created_at']}) ===")
            formatted.append(f"ステータス: {session['status']}")
            formatted.append(f"キートピック: {', '.join(session['context']['key_topics'])}")
            formatted.append(f"完了度: {session['context']['completeness_score']}%")
            formatted.append("\n会話:")
            
            for msg in session['messages']:
                formatted.append(f"{msg['role']}: {msg['content']}")
            
            formatted.append("")
        
        return "\n".join(formatted)