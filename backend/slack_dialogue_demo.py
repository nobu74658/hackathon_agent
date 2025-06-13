#!/usr/bin/env python3
"""
Slack対話デモスクリプト
DEMO_GUIDE.mdのシナリオをSlack上で再現します
"""

import asyncio
import os
import sys
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Slackクライアントのインポート
try:
    from slack_bolt.async_app import AsyncApp
    from slack_sdk.web.async_client import AsyncWebClient
except ImportError:
    print("❌ slack-boltがインストールされていません。以下のコマンドでインストールしてください:")
    print("pip install slack-bolt slack-sdk")
    sys.exit(1)

# アプリケーションのインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings
from app.services.dialogue_manager import DialogueManager
from app.services.conversation_memory import ConversationMemory

class SlackDialogueDemo:
    """Slack対話デモクラス"""
    
    def __init__(self):
        """初期化"""
        self.app = AsyncApp(
            token=settings.SLACK_BOT_TOKEN,
            signing_secret=settings.SLACK_SIGNING_SECRET
        )
        self.client = self.app.client
        self.dialogue_manager = DialogueManager()
        self.memory = ConversationMemory()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # デモシナリオの定義
        self.demo_scenarios = {
            "1": {
                "name": "新規顧客開拓の課題",
                "user_info": {
                    "name": "田中太郎",
                    "department": "営業部",
                    "experience_years": 1
                },
                "initial_topic": "新規顧客開拓のスキル向上",
                "sample_responses": [
                    "テレアポでアポイントが取れません",
                    "断られることが多く、心が折れそうです",
                    "月10件の新規顧客獲得が目標です",
                    "既存顧客のフォローは得意です"
                ]
            },
            "2": {
                "name": "プレゼンテーションスキル向上",
                "user_info": {
                    "name": "佐藤花子",
                    "department": "営業部",
                    "experience_years": 2
                },
                "initial_topic": "プレゼンテーションスキルの向上",
                "sample_responses": [
                    "大きな商談でのプレゼンが苦手です",
                    "緊張して話が伝わりません",
                    "資料作成は得意ですが、話し方に課題があります"
                ]
            }
        }
        
    async def send_message(self, channel: str, text: str, thread_ts: Optional[str] = None) -> Dict[str, Any]:
        """Slackにメッセージを送信"""
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            return response
        except Exception as e:
            print(f"❌ メッセージ送信エラー: {e}")
            return {}
    
    async def send_blocks(self, channel: str, blocks: list, text: str = "", thread_ts: Optional[str] = None) -> Dict[str, Any]:
        """Slackにブロックメッセージを送信"""
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts
            )
            return response
        except Exception as e:
            print(f"❌ ブロックメッセージ送信エラー: {e}")
            return {}
    
    async def wait_for_user_input(self, prompt: str = "続行するには何かメッセージを入力してください...") -> str:
        """ユーザー入力を待つ"""
        print(f"\n💬 {prompt}")
        return input("> ")
    
    async def start_demo_session(self, channel: str, scenario_key: str) -> str:
        """デモセッションを開始"""
        scenario = self.demo_scenarios[scenario_key]
        
        # ウェルカムメッセージ
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 デモシナリオ: {scenario['name']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ユーザー情報:*\n• 名前: {scenario['user_info']['name']}\n• 部署: {scenario['user_info']['department']}\n• 経験年数: {scenario['user_info']['experience_years']}年\n• 相談内容: {scenario['initial_topic']}"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        response = await self.send_blocks(channel, blocks, "デモセッションを開始します")
        thread_ts = response.get("ts")
        
        # セッション情報を保存
        session_id = f"demo_{scenario_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.sessions[session_id] = {
            "channel": channel,
            "thread_ts": thread_ts,
            "scenario": scenario,
            "step": 0,
            "dialogue_session_id": None
        }
        
        return session_id
    
    async def run_dialogue_step(self, session_id: str, user_message: Optional[str] = None):
        """対話ステップを実行"""
        session = self.sessions.get(session_id)
        if not session:
            print(f"❌ セッション {session_id} が見つかりません")
            return
        
        channel = session["channel"]
        thread_ts = session["thread_ts"]
        scenario = session["scenario"]
        step = session["step"]
        
        try:
            # 初回の場合はセッションを開始
            if session["dialogue_session_id"] is None:
                # AIセッションを開始
                result = await self.dialogue_manager.start_dialogue(
                    user_name=scenario["user_info"]["name"],
                    department=scenario["user_info"]["department"],
                    experience_years=scenario["user_info"]["experience_years"],
                    initial_topic=scenario["initial_topic"]
                )
                
                session["dialogue_session_id"] = result["session_id"]
                
                # 初期質問を送信
                await self.send_message(
                    channel,
                    f"🤖 *AIコーチ:*\n{result['initial_questions'][0]}",
                    thread_ts
                )
                
                # ユーザーに回答を促す
                if step < len(scenario["sample_responses"]):
                    await self.send_message(
                        channel,
                        f"💡 *サンプル回答:* {scenario['sample_responses'][step]}",
                        thread_ts
                    )
            else:
                # ユーザーメッセージがある場合は処理
                if user_message:
                    # ユーザーメッセージを表示
                    await self.send_message(
                        channel,
                        f"👤 *{scenario['user_info']['name']}:*\n{user_message}",
                        thread_ts
                    )
                    
                    # AIの応答を処理
                    result = await self.dialogue_manager.process_message(
                        session_id=session["dialogue_session_id"],
                        message=user_message
                    )
                    
                    # ステータスに応じて処理
                    if result["status"] == "need_more_info":
                        # 追加質問を送信
                        await self.send_message(
                            channel,
                            f"🤖 *AIコーチ:*\n{result['next_question']}",
                            thread_ts
                        )
                        
                        # 次のサンプル回答を表示
                        session["step"] += 1
                        if session["step"] < len(scenario["sample_responses"]):
                            await self.send_message(
                                channel,
                                f"💡 *サンプル回答:* {scenario['sample_responses'][session['step']]}",
                                thread_ts
                            )
                    
                    elif result["status"] == "ready_for_action_plan":
                        # アクションプランを生成
                        action_plan_result = await self.dialogue_manager.generate_action_plan(
                            session_id=session["dialogue_session_id"]
                        )
                        
                        # アクションプランを整形して送信
                        await self.send_action_plan(
                            channel,
                            thread_ts,
                            action_plan_result["action_plan"]
                        )
                        
                        # セッション完了
                        await self.send_message(
                            channel,
                            "✅ デモセッションが完了しました！",
                            thread_ts
                        )
                        
                        return "completed"
            
            session["step"] += 1
            self.sessions[session_id] = session
            return "continue"
            
        except Exception as e:
            print(f"❌ 対話ステップエラー: {e}")
            await self.send_message(
                channel,
                f"❌ エラーが発生しました: {str(e)}",
                thread_ts
            )
            return "error"
    
    async def send_action_plan(self, channel: str, thread_ts: str, action_plan: Dict[str, Any]):
        """アクションプランを送信"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 アクションプラン"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*概要:* {action_plan.get('summary', 'N/A')}"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # 主要な課題
        if "main_challenges" in action_plan:
            challenges_text = "\n".join([f"• {c}" for c in action_plan["main_challenges"]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🎯 主要な課題:*\n{challenges_text}"
                }
            })
        
        # アクションアイテム
        if "action_items" in action_plan:
            for i, item in enumerate(action_plan["action_items"], 1):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📌 アクション {i}: {item.get('title', 'N/A')}*\n{item.get('description', '')}"
                    }
                })
                
                # ステップ
                if "steps" in item:
                    steps_text = "\n".join([f"{j}. {s}" for j, s in enumerate(item["steps"], 1)])
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*実施ステップ:*\n{steps_text}"
                        }
                    })
                
                # タイムラインと成功指標
                metrics_text = ""
                if "timeline" in item:
                    metrics_text += f"*期限:* {item['timeline']}\n"
                if "success_metrics" in item:
                    metrics_text += f"*成功指標:* {', '.join(item['success_metrics'])}"
                
                if metrics_text:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": metrics_text
                        }
                    })
                
                blocks.append({"type": "divider"})
        
        # フォローアップスケジュール
        if "follow_up_schedule" in action_plan:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📅 フォローアップ:*\n{action_plan['follow_up_schedule']}"
                }
            })
        
        await self.send_blocks(channel, blocks, "アクションプラン", thread_ts)
    
    async def run_interactive_demo(self):
        """インタラクティブデモを実行"""
        print("\n🤖 Sales Growth AI - Slack対話デモ")
        print("=" * 60)
        
        # 環境設定チェック
        if not settings.SLACK_BOT_TOKEN or not settings.SLACK_SIGNING_SECRET:
            print("❌ Slack認証情報が設定されていません")
            print("📝 .envファイルに以下を設定してください:")
            print("   SLACK_BOT_TOKEN=xoxb-your-token")
            print("   SLACK_SIGNING_SECRET=your-secret")
            return
        
        # チャンネル選択
        print("\n📍 デモを実行するSlackチャンネルIDを入力してください")
        print("   (例: C1234567890)")
        channel_id = input("チャンネルID: ").strip()
        
        if not channel_id:
            print("❌ チャンネルIDが入力されていません")
            return
        
        # シナリオ選択
        print("\n📋 デモシナリオを選択してください:")
        for key, scenario in self.demo_scenarios.items():
            print(f"{key}. {scenario['name']}")
        
        scenario_choice = input("選択 (1-2): ").strip()
        
        if scenario_choice not in self.demo_scenarios:
            print("❌ 無効な選択です")
            return
        
        try:
            # デモセッション開始
            print("\n🚀 デモセッションを開始します...")
            session_id = await self.start_demo_session(channel_id, scenario_choice)
            
            print(f"✅ セッションID: {session_id}")
            print(f"📱 Slackチャンネルを確認してください")
            
            # 対話ループ
            scenario = self.demo_scenarios[scenario_choice]
            sample_responses = scenario["sample_responses"]
            
            for i, sample_response in enumerate(sample_responses):
                print(f"\n💬 ステップ {i+1}/{len(sample_responses)}")
                
                # ユーザー入力を待つ
                user_input = await self.wait_for_user_input(
                    f"回答を入力してください (Enterでサンプル回答を使用): "
                )
                
                # 空の場合はサンプル回答を使用
                if not user_input.strip():
                    user_input = sample_response
                    print(f"📝 サンプル回答を使用: {user_input}")
                
                # 対話ステップを実行
                status = await self.run_dialogue_step(session_id, user_input)
                
                if status == "completed":
                    print("\n🎉 デモが完了しました！")
                    break
                elif status == "error":
                    print("\n❌ エラーが発生しました")
                    break
                
                # 少し待機
                await asyncio.sleep(2)
            
        except Exception as e:
            print(f"\n❌ デモ実行エラー: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """メイン関数"""
    demo = SlackDialogueDemo()
    await demo.run_interactive_demo()

if __name__ == "__main__":
    asyncio.run(main())