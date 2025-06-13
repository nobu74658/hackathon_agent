#!/usr/bin/env python3
"""
Slack自動対話デモスクリプト
ユーザー入力を待たずに自動的にデモを実行します
"""

import asyncio
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import time

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

class SlackAutoDemo:
    """Slack自動デモクラス"""
    
    def __init__(self):
        """初期化"""
        self.app = AsyncApp(
            token=settings.SLACK_BOT_TOKEN,
            signing_secret=settings.SLACK_SIGNING_SECRET
        )
        self.client = self.app.client
        self.dialogue_manager = DialogueManager()
        
        # デモシナリオのスクリプト
        self.demo_script = {
            "scenario_1": {
                "name": "新規顧客開拓の課題",
                "description": "テレアポが苦手な新人営業マンのケース",
                "user_info": {
                    "name": "田中太郎",
                    "department": "営業部",
                    "experience_years": 1
                },
                "initial_topic": "新規顧客開拓のスキル向上",
                "dialogue": [
                    {
                        "wait": 2,
                        "response": "正直なところ、テレアポでアポイントを取るのが本当に苦手です。電話をかけても断られることがほとんどで..."
                    },
                    {
                        "wait": 3,
                        "response": "断られる理由ですか？よく「今は必要ない」とか「忙しい」と言われます。あと、そもそも話を聞いてもらえないことも多いですね。"
                    },
                    {
                        "wait": 3,
                        "response": "目標は月10件の新規顧客獲得です。でも今月はまだ2件しか取れていません..."
                    },
                    {
                        "wait": 2,
                        "response": "既存顧客のフォローは比較的得意だと思います。関係性ができているお客様とは良好な関係を築けています。"
                    }
                ]
            },
            "scenario_2": {
                "name": "プレゼンテーションスキル向上",
                "description": "大事な商談で緊張してしまう営業マンのケース",
                "user_info": {
                    "name": "佐藤花子",
                    "department": "営業部",
                    "experience_years": 2
                },
                "initial_topic": "プレゼンテーションスキルの向上",
                "dialogue": [
                    {
                        "wait": 2,
                        "response": "大きな商談になると緊張してしまって、準備した内容が頭から飛んでしまうんです。"
                    },
                    {
                        "wait": 3,
                        "response": "資料作成は得意で、提案内容もしっかり準備するんですが、いざ本番になると早口になったり、重要なポイントを飛ばしてしまったり..."
                    },
                    {
                        "wait": 3,
                        "response": "先週も100万円規模の商談があったんですが、緊張のあまり製品の主要機能の説明を忘れてしまいました。"
                    }
                ]
            }
        }
    
    async def send_typing_indicator(self, channel: str):
        """タイピングインジケーターを送信"""
        try:
            # Slack APIにはタイピングインジケーターの直接的なAPIはないため、
            # リアクションやステータス更新で代用することもできますが、
            # ここではシンプルに待機時間で表現します
            pass
        except:
            pass
    
    async def send_message_with_typing(self, channel: str, text: str, thread_ts: Optional[str] = None, typing_time: int = 2):
        """タイピング効果付きでメッセージを送信"""
        await self.send_typing_indicator(channel)
        await asyncio.sleep(typing_time)
        
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
    
    async def run_scenario(self, channel: str, scenario_key: str):
        """シナリオを実行"""
        if scenario_key not in self.demo_script:
            print(f"❌ シナリオ {scenario_key} が見つかりません")
            return
        
        script = self.demo_script[scenario_key]
        print(f"\n🎬 シナリオ実行: {script['name']}")
        
        # 開始メッセージ
        start_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎭 自動デモ: {script['name']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*シナリオ:* {script['description']}\n\n*登場人物:*\n• {script['user_info']['name']} ({script['user_info']['department']}, 経験{script['user_info']['experience_years']}年)"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        response = await self.client.chat_postMessage(
            channel=channel,
            blocks=start_blocks,
            text=f"自動デモを開始: {script['name']}"
        )
        thread_ts = response.get("ts")
        
        # 少し待機
        await asyncio.sleep(2)
        
        try:
            # 対話セッションを開始
            print("📝 対話セッション開始...")
            result = await self.dialogue_manager.start_dialogue(
                user_name=script['user_info']['name'],
                department=script['user_info']['department'],
                experience_years=script['user_info']['experience_years'],
                initial_topic=script['initial_topic']
            )
            
            session_id = result['session_id']
            
            # AIの初期質問を送信
            await self.send_message_with_typing(
                channel,
                f"🤖 *AIコーチ:*\n{result['initial_questions'][0]}",
                thread_ts,
                typing_time=1
            )
            
            # スクリプトに従って対話を進める
            for i, dialogue_item in enumerate(script['dialogue']):
                print(f"  ステップ {i+1}/{len(script['dialogue'])}")
                
                # 待機時間
                await asyncio.sleep(dialogue_item['wait'])
                
                # ユーザーの応答を送信
                user_name = script['user_info']['name']
                await self.send_message_with_typing(
                    channel,
                    f"👤 *{user_name}:*\n{dialogue_item['response']}",
                    thread_ts,
                    typing_time=2
                )
                
                # AIの応答を処理
                ai_result = await self.dialogue_manager.process_message(
                    session_id=session_id,
                    message=dialogue_item['response']
                )
                
                # AIの応答を送信
                if ai_result['status'] == 'need_more_info' and 'next_question' in ai_result:
                    await self.send_message_with_typing(
                        channel,
                        f"🤖 *AIコーチ:*\n{ai_result['next_question']}",
                        thread_ts,
                        typing_time=1
                    )
                elif ai_result['status'] == 'ready_for_action_plan':
                    # 最後の対話の後にアクションプランを生成
                    break
            
            # アクションプランを生成
            print("📋 アクションプラン生成中...")
            await self.send_message_with_typing(
                channel,
                "💭 *AIコーチ:* 情報を分析してアクションプランを作成しています...",
                thread_ts,
                typing_time=1
            )
            
            action_plan_result = await self.dialogue_manager.generate_action_plan(session_id)
            
            # アクションプランを送信
            await self.send_action_plan(channel, thread_ts, action_plan_result['action_plan'])
            
            # 完了メッセージ
            completion_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ *デモが完了しました！*\n\nこのような形で、AIコーチが営業担当者の課題を分析し、具体的なアクションプランを提供します。"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"セッションID: `{session_id}` | 実行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
            
            await self.client.chat_postMessage(
                channel=channel,
                blocks=completion_blocks,
                text="デモ完了",
                thread_ts=thread_ts
            )
            
            print("✅ シナリオ実行完了")
            
        except Exception as e:
            print(f"❌ シナリオ実行エラー: {e}")
            import traceback
            traceback.print_exc()
            
            await self.send_message_with_typing(
                channel,
                f"❌ デモ実行中にエラーが発生しました: {str(e)}",
                thread_ts
            )
    
    async def send_action_plan(self, channel: str, thread_ts: str, action_plan: Dict[str, Any]):
        """アクションプランを整形して送信"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 パーソナライズされたアクションプラン"
                }
            }
        ]
        
        # サマリー
        if 'summary' in action_plan:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📝 *概要:*\n{action_plan['summary']}"
                }
            })
        
        # 主要な課題
        if 'main_challenges' in action_plan and action_plan['main_challenges']:
            challenges_text = '\n'.join([f"• {c}" for c in action_plan['main_challenges']])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🎯 *特定された課題:*\n{challenges_text}"
                }
            })
        
        blocks.append({"type": "divider"})
        
        # アクションアイテム
        if 'action_items' in action_plan:
            for i, item in enumerate(action_plan['action_items'][:3], 1):  # 最大3つまで表示
                # アクションタイトルと説明
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🎯 アクション{i}: {item.get('title', 'アクション')}*\n_{item.get('description', '')}_"
                    }
                })
                
                # 実施ステップ
                if 'steps' in item and item['steps']:
                    steps_text = '\n'.join([f"{j}. {step}" for j, step in enumerate(item['steps'][:5], 1)])
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"📌 *実施ステップ:*\n{steps_text}"
                        }
                    })
                
                # 期限と成功指標
                if 'timeline' in item or 'success_metrics' in item:
                    metrics_parts = []
                    if 'timeline' in item:
                        metrics_parts.append(f"⏰ *期限:* {item['timeline']}")
                    if 'success_metrics' in item and item['success_metrics']:
                        metrics_parts.append(f"📊 *成功指標:* {', '.join(item['success_metrics'][:2])}")
                    
                    blocks.append({
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": " | ".join(metrics_parts)
                            }
                        ]
                    })
                
                if i < len(action_plan['action_items'][:3]):
                    blocks.append({"type": "divider"})
        
        # フォローアップ
        if 'follow_up_schedule' in action_plan:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📅 *フォローアップ計画:*\n{action_plan['follow_up_schedule']}"
                }
            })
        
        await self.client.chat_postMessage(
            channel=channel,
            blocks=blocks,
            text="アクションプラン",
            thread_ts=thread_ts
        )
    
    async def run_all_scenarios(self, channel: str):
        """すべてのシナリオを順番に実行"""
        print("\n🎬 全シナリオ自動実行開始")
        print("=" * 60)
        
        for scenario_key in self.demo_script.keys():
            await self.run_scenario(channel, scenario_key)
            
            # シナリオ間で少し待機
            if scenario_key != list(self.demo_script.keys())[-1]:
                print("\n⏳ 次のシナリオまで10秒待機...")
                await asyncio.sleep(10)
        
        print("\n✅ 全シナリオ実行完了!")

async def main():
    """メイン関数"""
    print("🤖 Sales Growth AI - Slack自動デモ")
    print("=" * 60)
    
    # 環境設定チェック
    if not settings.SLACK_BOT_TOKEN or not settings.SLACK_SIGNING_SECRET:
        print("❌ Slack認証情報が設定されていません")
        print("📝 .envファイルに以下を設定してください:")
        print("   SLACK_BOT_TOKEN=xoxb-your-token")
        print("   SLACK_SIGNING_SECRET=your-secret")
        return
    
    # オプション選択
    print("\n実行モードを選択してください:")
    print("1. 特定のシナリオを実行")
    print("2. すべてのシナリオを自動実行")
    
    mode = input("選択 (1-2): ").strip()
    
    # チャンネルID入力
    print("\n📍 デモを実行するSlackチャンネルIDを入力してください")
    print("   (例: C1234567890)")
    channel_id = input("チャンネルID: ").strip()
    
    if not channel_id:
        print("❌ チャンネルIDが入力されていません")
        return
    
    demo = SlackAutoDemo()
    
    try:
        if mode == "1":
            # シナリオ選択
            print("\n📋 実行するシナリオを選択してください:")
            print("1. 新規顧客開拓の課題")
            print("2. プレゼンテーションスキル向上")
            
            choice = input("選択 (1-2): ").strip()
            scenario_map = {"1": "scenario_1", "2": "scenario_2"}
            
            if choice in scenario_map:
                await demo.run_scenario(channel_id, scenario_map[choice])
            else:
                print("❌ 無効な選択です")
        
        elif mode == "2":
            await demo.run_all_scenarios(channel_id)
        
        else:
            print("❌ 無効な選択です")
    
    except KeyboardInterrupt:
        print("\n⚠️  ユーザーによって中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())