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
        
        # メッセージが長すぎる場合の処理
        if len(text) > 3000:
            await say("メッセージが長すぎます。もう少し短くまとめていただけますか？（3000文字以下）")
            return
        
        logger.info(f"Processing message from user {user_id}, length: {len(text)} chars")
        
        # セッションIDとしてSlackユーザーIDを使用
        session_id = f"slack_{user_id}"
        
        try:
            # AI対話マネージャーで処理（db_sessionはNoneで渡す）
            response = await self.dialogue_manager.process_user_response(session_id, text, None)
            
            # レスポンスタイプに応じて適切にフォーマット
            if response["type"] == "one_on_one_analysis":
                # 新しい1on1分析結果をフォーマット
                analysis_data = response["data"]
                formatted_response = self._format_one_on_one_analysis_for_slack(analysis_data)
            elif response["type"] == "one_on_one_clarification":
                # 1on1指示の具体化質問をフォーマット
                formatted_response = self._format_one_on_one_clarification_for_slack(response)
            elif response["type"] == "one_on_one_final_plan":
                # 対話型具体化プロセス完了後の最終アクションプラン
                formatted_response = self._format_one_on_one_final_plan_for_slack(response)
            elif response["type"] == "educational_explanation":
                # 🎓 教育的概念説明
                formatted_response = self._format_educational_explanation_for_slack(response)
            elif response["type"] == "knowledge_provision":
                # 📚 社内ナレッジ提供
                formatted_response = self._format_knowledge_provision_for_slack(response)
            elif response["type"] == "request_acknowledgment":
                # 📋 要求受理確認
                formatted_response = self._format_request_acknowledgment_for_slack(response)
            elif response["type"] == "action_plan":
                action_plan = response["data"]
                formatted_response = self._format_action_plan_for_slack(action_plan, response["completeness_score"])
            elif response["type"] == "error":
                formatted_response = f"⚠️ {response['message']}\n\n簡単な質問から始めてみませんか？"
            else:  # follow_up
                questions = response["questions"] 
                stage_info = {
                    "stage": response.get("stage", "analysis"),
                    "stage_description": response.get("stage_description", "分析中")
                }
                formatted_response = self._format_questions_for_slack(
                    questions, 
                    response["completeness_score"],
                    stage_info
                )
            
            await say(formatted_response)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error processing message for user {user_id}: {e}\nTraceback: {error_details}")
            
            # 開発環境ではより詳細なエラー情報を表示
            if settings.DEBUG:
                await say(f"🚨 エラーが発生しました:\n```{str(e)}```\n詳細はログを確認してください。")
            else:
                await say("申し訳ございません。処理中にエラーが発生しました。もう一度お試しください。")
    
    def _format_questions_for_slack(
        self, 
        questions: List[str], 
        completeness_score: int, 
        stage_info: Dict[str, str] = None
    ) -> str:
        """質問をSlack用にフォーマット"""
        # 段階情報を表示
        if stage_info:
            formatted = f"{stage_info['stage_description']} (進捗: {completeness_score}%)\n\n"
        else:
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
    
    def _format_one_on_one_analysis_for_slack(self, analysis_data: Dict[str, Any]) -> str:
        """1on1分析結果をSlack用にフォーマット"""
        
        final_summary = analysis_data.get("final_summary", {})
        supervisor_instructions = analysis_data.get("supervisor_instructions", [])
        concrete_plans = analysis_data.get("concrete_plans", [])
        
        # ヘッダー
        formatted = "🎯 **1on1フィードバック分析結果**\n\n"
        
        # 特定された上司の指示
        if supervisor_instructions:
            formatted += "📋 **特定された上司からの指示:**\n"
            for i, instruction in enumerate(supervisor_instructions[:2], 1):
                formatted += f"{i}. {instruction.get('abstract_concept', '')}\n"
            formatted += "\n"
        
        # 優先アクション
        priority_actions = final_summary.get("priority_actions", [])
        if priority_actions:
            formatted += "🚀 **優先的に取り組むべきアクション:**\n"
            for i, action in enumerate(priority_actions[:3], 1):
                formatted += f"\n**{i}. {action.get('action', '')}**\n"
                steps = action.get('specific_steps', [])
                for step in steps[:2]:  # 最初の2ステップのみ表示
                    formatted += f"   • {step}\n"
                formatted += f"   📅 実行頻度: {action.get('frequency', '')}\n"
        
        # 実装タイムライン
        timeline = final_summary.get("implementation_timeline", {})
        if timeline:
            formatted += "\n📅 **実装スケジュール:**\n"
            if timeline.get("immediately"):
                formatted += f"🔴 **今すぐ**: {timeline['immediately']}\n"
            if timeline.get("this_week"):
                formatted += f"🟡 **今週中**: {timeline['this_week']}\n"
            if timeline.get("this_month"):
                formatted += f"🟢 **今月中**: {timeline['this_month']}\n"
        
        # 成功指標
        metrics = final_summary.get("success_metrics", [])
        if metrics:
            formatted += "\n📊 **成功指標:**\n"
            for metric in metrics[:2]:
                formatted += f"• **{metric.get('metric', '')}**: {metric.get('target', '')}\n"
        
        # 活用したナレッジ
        if analysis_data.get("knowledge_used"):
            formatted += "\n📚 社内ナレッジを活用して分析しました\n"
        
        # 次のステップ
        next_steps = final_summary.get("next_steps", [])
        if next_steps:
            formatted += "\n🎯 **次のステップ:**\n"
            for step in next_steps[:2]:
                formatted += f"• {step}\n"
        
        # 文字数制限対応
        if len(formatted) > 3000:
            formatted = formatted[:2900] + "\n\n_（詳細が省略されています）_"
        
        return formatted
    
    def _format_one_on_one_clarification_for_slack(self, response: Dict[str, Any]) -> str:
        """1on1指示の具体化質問をSlack用にフォーマット"""
        
        instruction = response.get("instruction_being_clarified", {})
        questions = response.get("questions", [])
        current_index = response.get("current_instruction_index", 0)
        total_instructions = response.get("total_instructions", 1)
        stage_description = response.get("stage_description", "")
        
        # ヘッダー
        formatted = f"🎯 **{stage_description}**\n\n"
        
        # 現在分析中の指示
        if instruction:
            formatted += f"📋 **上司からの指示**: \"{instruction.get('abstract_concept', '不明')}\"\n"
            if instruction.get('original_text'):
                formatted += f"💬 **元の発言**: {instruction['original_text']}\n\n"
            else:
                formatted += "\n"
        
        # 具体化のための質問
        formatted += "🔍 **具体的にするための質問**:\n"
        for i, question in enumerate(questions, 1):
            formatted += f"{i}. {question}\n"
        
        # 進捗とフィードバック（実用レベル対応）
        formatted += f"\n📊 **進捗**: {current_index + 1}/{total_instructions} の指示を具体化中\n"
        
        # 具体性フィードバック
        concreteness_feedback = response.get("concreteness_feedback", "")
        if concreteness_feedback:
            formatted += f"🎯 **{concreteness_feedback}**\n"
        
        # 質問回数表示（実用レベル）
        dialogue_progress = response.get("dialogue_progress", "")
        if dialogue_progress:
            formatted += f"⏱️ **{dialogue_progress}**\n"
        
        # 実装上の不足要素
        implementation_gaps = response.get("implementation_gaps", [])
        if implementation_gaps:
            formatted += f"\n🔧 **改善が必要な点**: {', '.join(implementation_gaps[:2])}\n"
        
        # 必要な明確化事項
        required_clarifications = response.get("required_clarifications", [])
        if required_clarifications:
            formatted += f"📝 **明確化が必要**: {', '.join(required_clarifications[:2])}\n"
        
        # 実行可能性チェック結果（新機能）
        practical_barriers = response.get("practical_barriers", [])
        if practical_barriers:
            formatted += f"⚠️ **実行上の課題**: {', '.join(practical_barriers[:2])}\n"
        
        formatted += "\n💡 **お答えください**: 実用レベル(95%)達成のため、以下の詳細さが必要です：\n"
        formatted += "• ⏰ 具体的な時間設定（「明日朝9時から」「毎回3分間」）\n"
        formatted += "• 📍 場所・道具の明確化（「商談開始時に」「A4用紙に」）\n" 
        formatted += "• 📊 測定方法の具体化（「週1回振り返る」「メモ数をカウント」）"
        
        # 文字数制限対応
        if len(formatted) > 3000:
            formatted = formatted[:2900] + "\n\n_（内容が省略されています）_"
        
        return formatted
    
    def _format_one_on_one_final_plan_for_slack(self, response: Dict[str, Any]) -> str:
        """対話型具体化プロセス完了後の最終アクションプランをSlack用にフォーマット"""
        
        data = response.get("data", {})
        final_summary = data.get("final_summary", {})
        dialogue_summary = data.get("dialogue_summary", {})
        clarification_history = response.get("clarification_history", [])
        
        # ヘッダー
        formatted = "🎉 **1on1フィードバック 最終アクションプラン完成！**\n\n"
        
        # 対話サマリー
        instructions_count = dialogue_summary.get("instructions_clarified", 0)
        if instructions_count > 0:
            formatted += f"✅ **対話完了**: {instructions_count}件の抽象的指示を具体化しました\n"
            
            # 具体化された指示の簡単な概要
            if clarification_history:
                formatted += "📋 **具体化された指示**:\n"
                for i, history in enumerate(clarification_history[:3], 1):
                    original = history.get("original_abstract", "")
                    score = history.get("concreteness_score", 0)
                    formatted += f"   {i}. {original} (具体性: {score}%)\n"
                formatted += "\n"
        
        # 優先アクション
        priority_actions = final_summary.get("priority_actions", [])
        if priority_actions:
            formatted += "🚀 **優先的に取り組むべきアクション**:\n"
            for i, action in enumerate(priority_actions[:3], 1):
                formatted += f"\n**{i}. {action.get('action', '')}**\n"
                steps = action.get('specific_steps', [])
                for step in steps[:3]:  # 最初の3ステップ
                    formatted += f"   • {step}\n"
                formatted += f"   📅 頻度: {action.get('frequency', '')}\n"
                if action.get('measurement'):
                    formatted += f"   📊 測定: {action['measurement']}\n"
        
        # 実装タイムライン
        timeline = final_summary.get("implementation_timeline", {})
        if timeline:
            formatted += "\n📅 **実装スケジュール**:\n"
            if timeline.get("immediately"):
                formatted += f"🔴 **今すぐ**: {timeline['immediately']}\n"
            if timeline.get("this_week"):
                formatted += f"🟡 **今週中**: {timeline['this_week']}\n"
            if timeline.get("this_month"):
                formatted += f"🟢 **今月中**: {timeline['this_month']}\n"
        
        # 成功指標
        metrics = final_summary.get("success_metrics", [])
        if metrics:
            formatted += "\n📊 **成功指標**:\n"
            for metric in metrics[:2]:
                formatted += f"• **{metric.get('metric', '')}**: {metric.get('target', '')}\n"
        
        # 次のステップ  
        next_steps = final_summary.get("next_steps", [])
        if next_steps:
            formatted += "\n🎯 **次のステップ**:\n"
            for step in next_steps[:3]:
                formatted += f"• {step}\n"
        
        # 完了メッセージ
        formatted += "\n✨ **お疲れ様でした！** 上司からの抽象的な指示が、明日から実行できる具体的なアクションプランになりました。"
        
        # 文字数制限対応
        if len(formatted) > 3000:
            formatted = formatted[:2900] + "\n\n_（詳細が省略されています）_"
        
        return formatted
    
    def _format_educational_explanation_for_slack(self, response: Dict[str, Any]) -> str:
        """教育的説明をSlack用にフォーマット"""
        explanation = response.get("explanation", "")
        instruction = response.get("instruction_being_clarified", {})
        abstract_concept = instruction.get("abstract_concept", "")
        follow_up = response.get("follow_up", "")
        stage_description = response.get("stage_description", "")
        
        formatted = f"🎓 **{stage_description}**\n\n"
        formatted += f"📚 **「{abstract_concept}」について説明します**\n\n"
        formatted += f"{explanation}\n\n"
        formatted += f"💡 **次のステップ**\n{follow_up}"
        
        # 文字数制限対応
        if len(formatted) > 3000:
            formatted = formatted[:2900] + "\n\n_（詳細が省略されています）_"
        
        return formatted
    
    def _format_knowledge_provision_for_slack(self, response: Dict[str, Any]) -> str:
        """社内ナレッジ提供をSlack用にフォーマット"""
        knowledge_response = response.get("knowledge_response", "")
        original_request = response.get("original_request", "")
        follow_up = response.get("follow_up", "")
        stage_description = response.get("stage_description", "")
        
        formatted = f"📚 **{stage_description}**\n\n"
        formatted += f"✨ **ご要求**: {original_request}\n\n"
        formatted += f"{knowledge_response}\n\n"
        formatted += f"💡 **次のステップ**\n{follow_up}"
        
        # 文字数制限対応
        if len(formatted) > 3000:
            formatted = formatted[:2900] + "\n\n_（詳細が省略されています）_"
        
        return formatted
    
    def _format_request_acknowledgment_for_slack(self, response: Dict[str, Any]) -> str:
        """要求受理確認をSlack用にフォーマット"""
        message = response.get("message", "")
        
        formatted = f"📋 **ご要求を承りました**\n\n"
        formatted += f"{message}\n\n"
        formatted += "💭 より良いサポートのため、対話を続けさせていただきます。"
        
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