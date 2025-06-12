from typing import Dict, Any, Optional, List, Set
import logging
import time
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from app.core.config import settings
from app.services.dialogue_manager import DialogueManager
from app.services.conversation_memory import ConversationMemoryService
from app.services.real_llm_service import RealLLMService
from app.services.mock_llm import MockLLMProvider

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
        
        # 重複イベント防止
        self.processed_events: Set[str] = set()
        self.event_cleanup_time = time.time()
        
        # LLMサービスの初期化
        if settings.USE_MOCK_LLM:
            self.llm_service = MockLLMProvider()
            # モック環境では簡単なメモリサービスを使用
            from app.services.mock_llm import MockDialogueManager
            self.dialogue_manager = MockDialogueManager()
        else:
            self.llm_service = RealLLMService()
            self.memory_service = ConversationMemoryService()
            self.dialogue_manager = DialogueManager()
        
        # イベントハンドラーを設定
        self._setup_event_handlers()
        
        self.handler = AsyncSlackRequestHandler(self.app)
    
    def _setup_event_handlers(self):
        """Slackイベントハンドラーを設定"""
        
        @self.app.event("app_mention")
        async def handle_app_mention(event: Dict[str, Any], say):
            """アプリがメンションされた時の処理"""
            try:
                # Bot自身のメッセージかチェック
                if self._is_bot_message(event):
                    return
                    
                await self._handle_message(event, say, is_mention=True)
            except Exception as e:
                logger.error(f"Error handling app mention: {e}")
                await say("申し訳ございません。エラーが発生しました。")
        
        @self.app.event("message")
        async def handle_message(event: Dict[str, Any], say):
            """DMでメッセージを受信した時の処理"""
            try:
                # Bot自身のメッセージは無視
                if self._is_bot_message(event):
                    return
                
                # チャンネル内のメッセージでapp_mentionイベントがある場合は無視（重複防止）
                if event.get("channel_type") == "channel":
                    return
                    
                # DMのみ処理
                if event.get("channel_type") == "im":
                    await self._handle_message(event, say, is_mention=False)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await say("申し訳ございません。エラーが発生しました。")
    
    def _is_bot_message(self, event: Dict[str, Any]) -> bool:
        """ボット自身のメッセージかどうかをチェック"""
        # subtypeがbot_messageの場合
        if event.get("subtype") == "bot_message":
            return True
        
        # bot_idが設定されている場合
        if event.get("bot_id"):
            return True
            
        # ユーザーIDがボット自身の場合（ボットのuser_idと比較）
        if event.get("user") and hasattr(self.app.client, "auth_test"):
            try:
                # ボット自身のユーザーIDと比較（簡易版）
                if event.get("user").startswith("B"):  # ボットユーザーIDは通常Bで始まる
                    return True
            except:
                pass
        
        return False
    
    def _is_duplicate_event(self, event: Dict[str, Any]) -> bool:
        """重複イベントかどうかをチェック"""
        # イベントの一意性チェック用のキーを生成
        event_key = f"{event.get('ts', '')}_{event.get('user', '')}_{event.get('channel', '')}"
        
        # 古いイベントIDをクリーンアップ（5分以上古いものは削除）
        current_time = time.time()
        if current_time - self.event_cleanup_time > 300:  # 5分
            self.processed_events.clear()
            self.event_cleanup_time = current_time
        
        # 重複チェック
        if event_key in self.processed_events:
            return True
        
        # 新しいイベントとして記録
        self.processed_events.add(event_key)
        return False
    
    async def _handle_message(self, event: Dict[str, Any], say, is_mention: bool = False):
        """メッセージ処理の共通ロジック"""
        # 重複イベントチェック
        if self._is_duplicate_event(event):
            logger.info(f"Duplicate event detected, skipping: {event.get('ts')}")
            return
        
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
            # AI対話マネージャーで処理（db_sessionはNoneで渡す）
            response = await self.dialogue_manager.process_user_response(session_id, text, None)
            
            # レスポンスタイプに応じて適切にフォーマット
            if response["type"] == "action_plan":
                action_plan = response["data"]
                formatted_response = self._format_action_plan_for_slack(action_plan, response["completeness_score"])
            else:  # follow_up
                questions = response["questions"] 
                formatted_response = self._format_questions_for_slack(questions, response["completeness_score"])
            
            await say(formatted_response)
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            await say("申し訳ございません。処理中にエラーが発生しました。もう一度お試しください。")
    
    def _format_questions_for_slack(self, questions: List[str], completeness_score: int) -> str:
        """質問をSlack用にフォーマット"""
        formatted = f"📊 情報収集進捗: {completeness_score}%\n\n"
        formatted += "以下の点について詳しく教えてください：\n"
        
        for i, question in enumerate(questions, 1):
            formatted += f"{i}. {question}\n"
        
        if len(formatted) > 3000:
            formatted = formatted[:2900] + "\n\n_（続きがあります）_"
        
        return formatted
    
    def _format_action_plan_for_slack(self, action_plan: Dict, completeness_score: int) -> str:
        """アクションプランをSlack用にフォーマット"""
        formatted = f"🎯 **営業成長アクションプラン** (完了度: {completeness_score}%)\n\n"
        formatted += f"📝 **概要**\n{action_plan.get('summary', '')}\n\n"
        
        # アクションアイテム
        action_items = action_plan.get('action_items', [])
        if action_items:
            formatted += "📋 **具体的アクション**\n"
            for item in action_items:
                priority_emoji = "🔴" if item.get('priority') == 'high' else "🟡" if item.get('priority') == 'medium' else "🟢"
                formatted += f"{priority_emoji} **{item.get('title', '')}**\n"
                formatted += f"   └ {item.get('description', '')}\n"
                if item.get('due_date'):
                    formatted += f"   📅 期限: {item.get('due_date')}\n"
                formatted += "\n"
        
        # 主要改善ポイント
        key_improvements = action_plan.get('key_improvements', [])
        if key_improvements:
            formatted += "🎯 **重点改善項目**\n"
            for improvement in key_improvements:
                formatted += f"• {improvement}\n"
        
        if len(formatted) > 3000:
            formatted = formatted[:2900] + "\n\n_（続きがあります）_"
        
        return formatted
    
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