from typing import Dict, Any, Optional
import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from app.core.config import settings
# from app.services.dialogue_manager import DialogueManager
# from app.services.conversation_memory import ConversationMemoryService
# from app.services.real_llm_service import RealLLMService
# from app.services.mock_llm_service import MockLLMService

logger = logging.getLogger(__name__)


class SlackService:
    def __init__(self):
        if not settings.SLACK_BOT_TOKEN or not settings.SLACK_SIGNING_SECRET:
            raise ValueError("Slack credentials are required")
            
        self.app = AsyncApp(
            token=settings.SLACK_BOT_TOKEN,
            signing_secret=settings.SLACK_SIGNING_SECRET,
            process_before_response=True
        )
        
        # LLMサービスの初期化（一時的にコメントアウト）
        # if settings.USE_MOCK_LLM:
        #     self.llm_service = MockLLMService()
        # else:
        #     self.llm_service = RealLLMService()
        
        # self.memory_service = ConversationMemoryService()
        # self.dialogue_manager = DialogueManager(self.llm_service, self.memory_service)
        
        # イベントハンドラーを設定
        self._setup_event_handlers()
        
        self.handler = AsyncSlackRequestHandler(self.app)
    
    def _setup_event_handlers(self):
        """Slackイベントハンドラーを設定"""
        
        @self.app.event("app_mention")
        async def handle_app_mention(event: Dict[str, Any], say):
            """アプリがメンションされた時の処理"""
            try:
                await self._handle_message(event, say, is_mention=True)
            except Exception as e:
                logger.error(f"Error handling app mention: {e}")
                await say("申し訳ございません。エラーが発生しました。")
        
        @self.app.event("message")
        async def handle_message(event: Dict[str, Any], say):
            """DMでメッセージを受信した時の処理"""
            # Bot自身のメッセージは無視
            if event.get("subtype") == "bot_message":
                return
                
            # チャンネル内のメッセージでメンションがない場合は無視
            if event.get("channel_type") == "channel" and "app_mention" not in event.get("type", ""):
                return
                
            try:
                await self._handle_message(event, say, is_mention=False)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await say("申し訳ございません。エラーが発生しました。")
    
    async def _handle_message(self, event: Dict[str, Any], say, is_mention: bool = False):
        """メッセージ処理の共通ロジック"""
        user_id = event.get("user")
        text = event.get("text", "")
        
        # メンションの場合はBot IDを除去
        if is_mention:
            # <@BOT_ID>を除去
            import re
            text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
        
        if not text:
            await say("メッセージが空です。何かご質問はありますか？")
            return
        
        # セッションIDとしてSlackユーザーIDを使用
        session_id = f"slack_{user_id}"
        
        try:
            # 一時的にエコー応答
            response = f"受信したメッセージ: {text}\n\n（AI機能は準備中です）"
            
            # Slack用にフォーマット
            formatted_response = self._format_for_slack(response)
            await say(formatted_response)
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            await say("申し訳ございません。処理中にエラーが発生しました。もう一度お試しください。")
    
    def _format_for_slack(self, response: str) -> str:
        """AI応答をSlack用にフォーマット"""
        # 基本的なマークダウン変換
        # 長すぎる場合は分割することも考慮
        if len(response) > 3000:
            # Slackのメッセージ制限を考慮して分割
            return response[:2900] + "\n\n_（続きがあります）_"
        
        return response
    
    async def get_handler(self):
        """FastAPI用のハンドラーを取得"""
        return self.handler


# シングルトンインスタンス
slack_service = None

def get_slack_service() -> SlackService:
    """SlackServiceのシングルトンインスタンスを取得"""
    global slack_service
    if slack_service is None:
        slack_service = SlackService()
    return slack_service