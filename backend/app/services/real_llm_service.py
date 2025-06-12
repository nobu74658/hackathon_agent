"""
実際のLLM APIを使用するサービス
OpenAI GPT または Anthropic Claude
"""

from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.schema.runnable import RunnablePassthrough
    from langchain.output_parsers import PydanticOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from pydantic import BaseModel, Field
from app.core.config import settings


class QuestionGenerationResponse(BaseModel):
    """質問生成のレスポンス"""
    questions: List[str] = Field(description="生成された質問のリスト（3-5個）")
    reasoning: str = Field(description="なぜこれらの質問が必要かの理由")
    information_gaps: List[str] = Field(description="まだ不足している情報")
    completeness_score: int = Field(description="現在の情報充足度（0-100）", ge=0, le=100)


class ActionPlanResponse(BaseModel):
    """アクションプラン生成のレスポンス"""
    action_items: List[Dict[str, Any]] = Field(description="具体的なアクションアイテム")
    summary: str = Field(description="アクションプランの全体サマリー")
    key_focus_areas: List[str] = Field(description="重点的に取り組むべき領域")
    success_metrics: Dict[str, Any] = Field(description="成功指標と測定方法")
    timeline: str = Field(description="実施期間の目安")


class RealLLMService:
    """実際のLLM APIを使用するサービス"""
    
    def __init__(self, provider: str = "openai"):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain関連のパッケージがインストールされていません")
        
        self.provider = provider
        self.llm = self._initialize_llm(provider)
        self.question_parser = PydanticOutputParser(pydantic_object=QuestionGenerationResponse)
        self.action_plan_parser = PydanticOutputParser(pydantic_object=ActionPlanResponse)
    
    def _initialize_llm(self, provider: str):
        """LLMプロバイダーを初期化"""
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEYが設定されていません")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
                max_tokens=2000
            )
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEYが設定されていません")
            return ChatAnthropic(
                model=settings.ANTHROPIC_MODEL,
                temperature=0.7,
                api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=2000
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def generate_initial_questions(
        self, 
        initial_context: Dict[str, Any]
    ) -> QuestionGenerationResponse:
        """初期質問の生成"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援する専門のAIコーチです。
            営業スキル向上のアクションプラン作成に必要な質問を生成してください。

            以下の形式で厳密にJSON形式で回答してください：
            {{
                "questions": ["質問1", "質問2", "質問3"],
                "reasoning": "これらの質問が必要な理由",
                "information_gaps": ["不足している情報1", "不足している情報2"],
                "completeness_score": 20
            }}

            質問は3-5個、営業スキル向上に直結する具体的な内容にしてください。"""),
            ("user", """初期コンテキスト：
            {initial_context}
            
            上記を踏まえて、JSON形式で質問を生成してください。""")
        ])
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({
            "initial_context": json.dumps(initial_context, ensure_ascii=False)
        })
        
        # JSONレスポンスをパース
        try:
            result_dict = json.loads(response.content)
            return QuestionGenerationResponse(**result_dict)
        except json.JSONDecodeError:
            # JSONパースに失敗した場合のフォールバック
            return QuestionGenerationResponse(
                questions=[
                    "現在の営業活動で最も困難に感じていることは何ですか？",
                    "これまでの営業経験で成功した事例があれば教えてください",
                    "理想的な営業成果とはどのようなものですか？"
                ],
                reasoning="営業スキル向上のための基本的な情報収集が必要です",
                information_gaps=["具体的な課題", "現在のスキルレベル", "目標設定"],
                completeness_score=20
            )
    
    async def generate_follow_up_questions(
        self,
        conversation_history: List[Dict[str, str]],
        current_completeness: int
    ) -> QuestionGenerationResponse:
        """フォローアップ質問の生成"""
        
        # 会話履歴を文字列に変換
        conversation_text = ""
        for msg in conversation_history:
            role = "ユーザー" if msg["role"] == "user" else "AI"
            conversation_text += f"{role}: {msg['content']}\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """これまでの会話を分析し、追加質問をJSON形式で生成してください。

            以下の形式で回答してください：
            {{
                "questions": ["追加質問1", "追加質問2", "追加質問3"],
                "reasoning": "なぜこれらの質問が必要か",
                "information_gaps": ["不足情報1", "不足情報2"],
                "completeness_score": {completeness_score}
            }}"""),
            ("user", """これまでの会話：
            {conversation_history}
            
            追加で必要な質問をJSON形式で生成してください。""")
        ])
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({
            "conversation_history": conversation_text,
            "completeness_score": current_completeness
        })
        
        try:
            result_dict = json.loads(response.content)
            return QuestionGenerationResponse(**result_dict)
        except json.JSONDecodeError:
            return QuestionGenerationResponse(
                questions=[
                    "より具体的な状況を教えてください",
                    "これまでに試した解決策はありますか？",
                    "期待する成果の具体的な目標はありますか？"
                ],
                reasoning="より詳細な情報収集が必要です",
                information_gaps=["具体的事例", "解決策の試行錯誤", "明確な目標"],
                completeness_score=current_completeness
            )
    
    async def evaluate_information_completeness(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> int:
        """情報の充足度を評価（0-100）"""
        
        conversation_text = ""
        for msg in conversation_history:
            if msg["role"] == "user":
                conversation_text += f"ユーザー: {msg['content']}\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """営業スキル向上のアクションプラン作成に必要な情報の充足度を0-100のスコアで評価してください。

            評価基準：
            - 現在の課題が具体的に特定されている（20点）
            - 目標や期待される成果が明確（20点）
            - 現在のスキルレベルや経験が把握できる（20点）
            - 具体的な事例や状況が提供されている（20点）
            - 制約条件やリソースが明確（20点）

            数値のみを返してください（例：75）"""),
            ("user", f"会話内容：\n{conversation_text}")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        try:
            score = int(response.content.strip())
            return max(0, min(100, score))
        except ValueError:
            # パースエラーの場合は会話回数ベースで推定
            user_messages = [msg for msg in conversation_history if msg["role"] == "user"]
            return min(len(user_messages) * 15, 90)
    
    async def generate_action_plan(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> ActionPlanResponse:
        """アクションプランの生成"""
        
        conversation_text = ""
        for msg in conversation_history:
            role = "ユーザー" if msg["role"] == "user" else "AI"
            conversation_text += f"{role}: {msg['content']}\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """会話内容からアクションプランをJSON形式で作成してください。

            以下の形式で回答してください：
            {{
                "action_items": [
                    {{
                        "id": "action_1",
                        "title": "アクション名",
                        "description": "詳細説明",
                        "priority": "high/medium/low",
                        "due_date": "2024-02-15",
                        "category": "カテゴリ",
                        "metrics": ["指標1", "指標2"]
                    }}
                ],
                "summary": "アクションプランの要約",
                "key_focus_areas": ["重点領域1", "重点領域2"],
                "success_metrics": {{
                    "success_indicators": ["成功指標1", "成功指標2"],
                    "review_frequency": "monthly"
                }},
                "timeline": "実施期間"
            }}"""),
            ("user", """会話履歴：
            {conversation_history}
            
            アクションプランをJSON形式で作成してください。""")
        ])
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({
            "conversation_history": conversation_text
        })
        
        try:
            result_dict = json.loads(response.content)
            return ActionPlanResponse(**result_dict)
        except json.JSONDecodeError:
            # フォールバック
            return ActionPlanResponse(
                action_items=[
                    {
                        "id": "action_1",
                        "title": "スキル向上研修参加",
                        "description": "営業スキル向上のための研修に参加する",
                        "priority": "high",
                        "due_date": "2024-02-28",
                        "category": "skill_development",
                        "metrics": ["研修参加回数", "学習内容の実践率"]
                    }
                ],
                summary="営業スキル向上のための基本的なアクションプラン",
                key_focus_areas=["スキル開発", "実践経験", "継続学習"],
                success_metrics={
                    "success_indicators": ["スキル向上", "成果改善"],
                    "review_frequency": "monthly"
                },
                timeline="3ヶ月間"
            )
    
    async def analyze_conversation_sentiment(
        self,
        user_message: str
    ) -> Dict[str, Any]:
        """会話の感情分析と意図理解"""
        
        # シンプルなキーワードベース感情分析に変更（API呼び出しなし）
        # 本格運用時にはLLM APIを使用
        
        # ポジティブキーワード
        positive_keywords = ["成功", "良い", "できる", "学ぶ", "向上", "改善", "満足", "順調", "達成"]
        # ネガティブキーワード  
        negative_keywords = ["困る", "難しい", "失敗", "問題", "悩み", "不安", "苦手", "緊張", "頭が真っ白"]
        # 緊急性キーワード
        urgent_keywords = ["緊急", "急", "すぐに", "至急", "明日", "今日"]
        
        # 感情判定
        positive_count = sum(1 for word in positive_keywords if word in user_message)
        negative_count = sum(1 for word in negative_keywords if word in user_message)
        
        if negative_count > positive_count:
            sentiment = "negative"
            emotional_state = "frustrated" if "失敗" in user_message or "困" in user_message else "confused"
        elif positive_count > negative_count:
            sentiment = "positive"
            emotional_state = "motivated"
        else:
            sentiment = "neutral"
            emotional_state = "neutral"
        
        # 緊急性判定
        urgency = "high" if any(word in user_message for word in urgent_keywords) else "medium"
        
        # 主要トピック抽出（簡易版）
        topics = []
        topic_keywords = {
            "プレゼンテーション": ["プレゼン", "発表", "商談"],
            "営業スキル": ["営業", "売上", "顧客"],
            "コミュニケーション": ["話", "会話", "伝える"],
            "緊張・不安": ["緊張", "不安", "真っ白"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in user_message for keyword in keywords):
                topics.append(topic)
        
        if not topics:
            topics = ["一般的な相談"]
        
        return {
            "sentiment": sentiment,
            "confidence_level": "high" if abs(positive_count - negative_count) > 1 else "medium",
            "key_topics": topics,
            "urgency": urgency,
            "emotional_state": emotional_state
        }