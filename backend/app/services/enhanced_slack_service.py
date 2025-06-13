"""
Enhanced Slack Service with conversation history and knowledge base integration
"""

from typing import Dict, Any, Optional, List, Set
import logging
import time
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.enhanced_dialogue_manager import EnhancedDialogueManager
from app.services.conversation_memory import ConversationMemoryService
from app.services.conversation_history_service import ConversationHistoryService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.real_llm_service import RealLLMService
from app.services.mock_llm import MockLLMProvider
from app.db.session import get_db

logger = logging.getLogger(__name__)


class EnhancedSlackService:
    """対話履歴とナレッジベースを統合したSlackサービス"""
    
    def __init__(self):
        if not settings.SLACK_BOT_TOKEN or not settings.SLACK_SIGNING_SECRET:
            raise ValueError("Slack credentials are required")
            
        self.app = AsyncApp(
            token=settings.SLACK_BOT_TOKEN,
            signing_secret=settings.SLACK_SIGNING_SECRET,
            process_before_response=True
        )
        
        # 重複イベント防止
        self.processed_events: Set[str] = set()
        self.event_cleanup_time = time.time()
        
        # サービスの初期化
        self.llm_service = RealLLMService() if not settings.USE_MOCK_LLM else MockLLMProvider()
        self.memory_service = ConversationMemoryService()
        self.history_service = ConversationHistoryService()
        self.knowledge_service = KnowledgeBaseService()
        
        # EnhancedDialogueManagerを使用
        self.dialogue_manager = EnhancedDialogueManager()
        
        # イベントハンドラーを設定
        self._setup_event_handlers()
        
        self.handler = AsyncSlackRequestHandler(self.app)
    
    def _setup_event_handlers(self):
        """Slackイベントハンドラーを設定"""
        
        @self.app.event("app_mention")
        async def handle_app_mention(event: Dict[str, Any], say):
            """アプリメンション時の処理"""
            await self._handle_message(event, say, is_mention=True)
        
        @self.app.event("message")
        async def handle_message(event: Dict[str, Any], say):
            """DM受信時の処理"""
            # DMのみを処理（チャンネルメッセージは無視）
            if event.get("channel_type") == "im":
                await self._handle_message(event, say, is_mention=False)
        
        @self.app.command("/ai_help")
        async def handle_help_command(ack, say, command):
            """ヘルプコマンド"""
            await ack()
            help_text = self._get_help_text()
            await say(help_text)
        
        @self.app.command("/ai_knowledge")
        async def handle_knowledge_search(ack, say, command):
            """ナレッジベース検索コマンド"""
            await ack()
            query = command.get("text", "")
            if not query:
                await say("検索キーワードを入力してください。例: `/ai_knowledge 営業クロージング`")
                return
            
            # ナレッジベースを検索
            results = await self.knowledge_service.search(query, limit=3)
            formatted_results = self._format_knowledge_results(results)
            await say(formatted_results)
        
        @self.app.command("/ai_history")
        async def handle_history_command(ack, say, command):
            """会話履歴サマリーコマンド"""
            await ack()
            user_id = command["user_id"]
            
            # データベースセッションを取得
            async for db in get_db():
                insights = await self.history_service.get_user_insights(f"slack_{user_id}", db)
                profile = await self.history_service.get_or_create_user_profile(f"slack_{user_id}", db)
                
                summary = self._format_user_history(profile, insights)
                await say(summary)
                break
    
    def _is_bot_message(self, event: Dict[str, Any]) -> bool:
        """ボット自身のメッセージかどうかをチェック"""
        if event.get("subtype") == "bot_message":
            return True
        if event.get("bot_id"):
            return True
        return False
    
    def _is_duplicate_event(self, event: Dict[str, Any]) -> bool:
        """重複イベントかどうかをチェック"""
        event_key = f"{event.get('ts', '')}_{event.get('user', '')}_{event.get('channel', '')}"
        
        # 古いイベントIDをクリーンアップ
        current_time = time.time()
        if current_time - self.event_cleanup_time > 300:  # 5分
            self.processed_events.clear()
            self.event_cleanup_time = current_time
        
        if event_key in self.processed_events:
            return True
        
        self.processed_events.add(event_key)
        return False
    
    async def _handle_message(self, event: Dict[str, Any], say, is_mention: bool = False):
        """メッセージ処理の共通ロジック（強化版）"""
        if self._is_duplicate_event(event):
            return
        
        if self._is_bot_message(event):
            return
        
        text = event.get("text", "")
        user_id = event.get("user", "")
        
        if is_mention:
            text = text.split(">", 1)[1].strip() if ">" in text else text
        
        if not text:
            return
        
        session_id = f"slack_{user_id}"
        
        try:
            # 一時的な応答メッセージ
            thinking_msg = await say("🤔 考えています...")
            
            # データベースセッションを使用して処理
            async for db in get_db():
                # ユーザーの過去の洞察を取得
                insights = await self.history_service.get_user_insights(session_id, db)
                
                # ナレッジベースで関連情報を検索
                knowledge_results = await self.knowledge_service.search(text, limit=2)
                
                # コンテキストにナレッジ情報を追加
                context = {
                    "user_insights": insights,
                    "knowledge_base": knowledge_results,
                    "source": "slack"
                }
                
                # EnhancedDialogueManagerで処理
                response = await self.dialogue_manager.process_user_response(
                    session_id, text, db, additional_context=context
                )
                
                # 応答をフォーマット
                if response["type"] == "action_plan":
                    formatted_response = self._format_enhanced_action_plan(
                        response["data"], 
                        response["completeness_score"],
                        response.get("personalization_info")
                    )
                else:
                    formatted_response = self._format_enhanced_questions(
                        response["questions"], 
                        response["completeness_score"],
                        response.get("used_knowledge", False),
                        response.get("personalization_info")
                    )
                
                # 一時メッセージを更新
                await self.app.client.chat_update(
                    channel=event["channel"],
                    ts=thinking_msg["ts"],
                    text=formatted_response
                )
                break
                
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            await say("申し訳ございません。処理中にエラーが発生しました。もう一度お試しください。")
    
    def _format_enhanced_questions(
        self, 
        questions: List[str], 
        completeness_score: int,
        used_knowledge: bool,
        personalization_info: Optional[Dict] = None
    ) -> str:
        """強化された質問フォーマット"""
        formatted = f"📊 情報収集進捗: {completeness_score}%\n"
        
        # パーソナライゼーション情報を表示
        if personalization_info:
            if personalization_info.get("returning_user"):
                formatted += f"👤 お帰りなさい！前回から{personalization_info.get('days_since_last', 0)}日ぶりですね。\n"
            if personalization_info.get("common_challenges"):
                formatted += f"💡 過去の課題を考慮して質問を調整しました。\n"
        
        if used_knowledge:
            formatted += "📚 社内ナレッジを参考にしています。\n"
        
        formatted += "\n以下の点について詳しく教えてください：\n"
        
        for i, question in enumerate(questions, 1):
            formatted += f"{i}. {question}\n"
        
        # ヘルプ情報
        formatted += "\n💡 `/ai_knowledge キーワード` で社内ナレッジを検索できます。"
        
        return formatted[:3000]
    
    def _format_enhanced_action_plan(
        self, 
        action_plan: Dict, 
        completeness_score: int,
        personalization_info: Optional[Dict] = None
    ) -> str:
        """強化されたアクションプランフォーマット"""
        formatted = f"🎯 **営業成長アクションプラン** (完了度: {completeness_score}%)\n"
        
        # パーソナライゼーション情報
        if personalization_info and personalization_info.get("success_rate"):
            formatted += f"📈 あなたの過去の成功率: {personalization_info['success_rate']}%\n"
        
        formatted += f"\n📝 **概要**\n{action_plan.get('summary', '')}\n\n"
        
        # テンプレート提案
        if action_plan.get('suggested_templates'):
            formatted += "📋 **推奨テンプレート**\n"
            for template in action_plan['suggested_templates'][:2]:
                formatted += f"• {template['title']} (成功率: {template.get('success_rate', 'N/A')}%)\n"
            formatted += "\n"
        
        # アクションアイテム
        action_items = action_plan.get('action_items', [])
        if action_items:
            formatted += "📋 **具体的アクション**\n"
            for item in action_items[:5]:  # 最大5件
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.get('priority'), "⚪")
                formatted += f"{priority_emoji} **{item.get('title', '')}**\n"
                formatted += f"   └ {item.get('description', '')}\n"
                if item.get('due_date'):
                    formatted += f"   📅 期限: {item.get('due_date')}\n"
                formatted += "\n"
        
        # 履歴サマリーを見るための案内
        formatted += "\n💬 `/ai_history` で過去の会話履歴と洞察を確認できます。"
        
        return formatted[:3000]
    
    def _format_knowledge_results(self, results: List[Dict]) -> str:
        """ナレッジ検索結果のフォーマット"""
        if not results:
            return "該当するナレッジが見つかりませんでした。"
        
        formatted = "📚 **ナレッジベース検索結果**\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **{result.get('title', '無題')}**\n"
            formatted += f"   カテゴリ: {result.get('category', '未分類')}\n"
            formatted += f"   関連度: {result.get('relevance_score', 0):.0%}\n"
            formatted += f"   {result.get('summary', '')[:100]}...\n\n"
        
        return formatted
    
    def _format_user_history(self, profile: Dict, insights: List[Dict]) -> str:
        """ユーザー履歴のフォーマット"""
        formatted = "📊 **あなたの成長履歴**\n\n"
        
        # プロファイル情報
        formatted += f"セッション数: {profile.get('total_sessions', 0)}回\n"
        formatted += f"完了アクション: {profile.get('completed_actions', 0)}件\n"
        formatted += f"成功率: {profile.get('success_rate', 0)}%\n\n"
        
        # よくある課題
        if profile.get('common_challenges'):
            formatted += "**💪 取り組んでいる課題**\n"
            for challenge in profile['common_challenges'][:3]:
                formatted += f"• {challenge}\n"
            formatted += "\n"
        
        # 強み
        if profile.get('strengths'):
            formatted += "**✨ あなたの強み**\n"
            for strength in profile['strengths'][:3]:
                formatted += f"• {strength}\n"
            formatted += "\n"
        
        # 最近の洞察
        if insights:
            formatted += "**🔍 最近の洞察**\n"
            for insight in insights[:3]:
                formatted += f"• [{insight['insight_type']}] {insight['content']}\n"
        
        return formatted
    
    def _get_help_text(self) -> str:
        """ヘルプテキスト"""
        return """
🤖 **AI営業支援エージェント - Slackコマンド一覧**

**基本的な使い方:**
• DMで直接メッセージを送信
• チャンネルで @AI営業支援 をメンション

**コマンド:**
• `/ai_help` - このヘルプを表示
• `/ai_knowledge キーワード` - 社内ナレッジを検索
• `/ai_history` - あなたの成長履歴を表示

**特徴:**
✅ 過去の会話を記憶し、パーソナライズされた支援
✅ 社内のベストプラクティスを活用
✅ 具体的で実行可能なアクションプラン生成
"""
    
    async def get_handler(self):
        """FastAPI用のハンドラーを取得"""
        return self.handler


# シングルトンインスタンス
enhanced_slack_service = None

def get_enhanced_slack_service() -> EnhancedSlackService:
    """EnhancedSlackServiceのシングルトンインスタンスを取得"""
    global enhanced_slack_service
    if enhanced_slack_service is None:
        enhanced_slack_service = EnhancedSlackService()
    return enhanced_slack_service