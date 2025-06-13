#!/usr/bin/env python3
"""
Slack上で理想的な対話シナリオを再現するデモスクリプト

このスクリプトは、新人営業マンとAIエージェントの理想的な対話を
Slack上でシミュレートします。ユーザーの入力を待ちながら、
段階的に対話を進めていきます。
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

# 環境変数の読み込み
from app.core.config import settings

class SlackIdealDialogueDemo:
    def __init__(self):
        """Slackデモの初期化"""
        if not settings.SLACK_BOT_TOKEN:
            raise ValueError("SLACK_BOT_TOKENが設定されていません")
        
        self.client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
        self.base_url = "http://localhost:8000"
        self.channel_id = None
        self.session = None
        self.api_session_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def setup_demo_channel(self) -> str:
        """デモ用のDMチャンネルを設定"""
        print("📱 Slackデモチャンネルの設定中...")
        
        try:
            # ボット自身の情報を取得
            auth_response = await self.client.auth_test()
            bot_user_id = auth_response["user_id"]
            
            # 自分自身のユーザーIDを取得
            users_response = await self.client.users_list()
            current_user_id = None
            
            for user in users_response["members"]:
                if not user.get("is_bot") and not user.get("deleted"):
                    # 最初の有効なユーザーを使用
                    current_user_id = user["id"]
                    break
            
            if not current_user_id:
                raise ValueError("有効なユーザーが見つかりません")
            
            # DMを開く
            dm_response = await self.client.conversations_open(users=current_user_id)
            self.channel_id = dm_response["channel"]["id"]
            
            print(f"✅ DMチャンネル設定完了: {self.channel_id}")
            return self.channel_id
            
        except SlackApiError as e:
            print(f"❌ Slack APIエラー: {e.response['error']}")
            raise
    
    async def post_message(self, text: str, as_user: bool = False) -> Dict[str, Any]:
        """Slackにメッセージを投稿"""
        try:
            if as_user:
                # ユーザーのメッセージをシミュレート（実際にはBotが投稿）
                text = f"👤 **ユーザー**: {text}"
            
            response = await self.client.chat_postMessage(
                channel=self.channel_id,
                text=text,
                mrkdwn=True
            )
            return response
            
        except SlackApiError as e:
            print(f"❌ メッセージ送信エラー: {e.response['error']}")
            raise
    
    async def wait_for_user_input(self, prompt: str = None) -> str:
        """ユーザーの入力を待つ"""
        if prompt:
            print(f"\n💭 {prompt}")
        
        print("👤 ユーザーの応答を入力してください（Enterで送信）: ")
        
        # 標準入力から読み取り
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input)
        
        return user_input.strip()
    
    async def start_api_session(self) -> Dict[str, Any]:
        """APIセッションを開始"""
        print("\n🚀 APIセッション開始中...")
        
        request_data = {
            "user_name": "山田太郎",
            "department": "営業部",
            "experience_years": 1,
            "initial_topic": "営業スキル向上",
            "specific_challenge": "新規顧客開拓と商談スキル"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/enhanced/start",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.api_session_id = result["session_id"]
                    print(f"✅ セッション開始: {self.api_session_id[:8]}...")
                    return result
                else:
                    error = await response.json()
                    print(f"❌ セッション開始失敗: {error}")
                    return None
                    
        except Exception as e:
            print(f"❌ APIエラー: {e}")
            return None
    
    async def send_to_api(self, message: str) -> Dict[str, Any]:
        """APIにメッセージを送信"""
        if not self.api_session_id:
            print("❌ APIセッションが開始されていません")
            return None
        
        request_data = {
            "session_id": self.api_session_id,
            "message": message
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/enhanced/message",
                json=request_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.json()
                    print(f"❌ API送信失敗: {error}")
                    return None
                    
        except Exception as e:
            print(f"❌ APIエラー: {e}")
            return None
    
    async def run_ideal_dialogue_scenario(self):
        """理想的な対話シナリオを実行"""
        print("\n" + "="*80)
        print("🎭 Slack上での理想的な対話シナリオ - デモ開始")
        print("="*80)
        
        # チャンネル設定
        await self.setup_demo_channel()
        
        # APIセッション開始
        session_result = await self.start_api_session()
        if not session_result:
            return
        
        # 開始メッセージ
        await self.post_message(
            "🤖 **Sales Growth AI Agent**\n\n" +
            "こんにちは、山田太郎さん！営業スキル向上のお手伝いをさせていただきます。\n\n" +
            "過去の会話履歴と社内のベストプラクティスを参考に、" +
            "山田さんに最適なサポートを提供いたします。"
        )
        
        await asyncio.sleep(1)
        
        # 知識ベースからの洞察を表示
        if session_result.get("self_resolved_insights"):
            insights_text = "💡 **過去の履歴からの洞察**\n"
            for insight in session_result["self_resolved_insights"]:
                insights_text += f"• {insight}\n"
            await self.post_message(insights_text)
            await asyncio.sleep(1)
        
        # 初期質問
        questions_text = "📝 **まず、以下の点について教えてください：**\n"
        for i, q in enumerate(session_result["questions"], 1):
            questions_text += f"{i}. {q}\n"
        await self.post_message(questions_text)
        
        # 対話ループ
        conversation_count = 0
        max_conversations = 5
        
        while conversation_count < max_conversations:
            # ユーザー入力を待つ
            user_input = await self.wait_for_user_input(
                f"質問{conversation_count + 1}への回答を入力してください"
            )
            
            if user_input.lower() in ['quit', 'exit', '終了']:
                await self.post_message("👋 対話を終了します。ありがとうございました。")
                break
            
            # ユーザーのメッセージをSlackに投稿
            await self.post_message(user_input, as_user=True)
            await asyncio.sleep(0.5)
            
            # APIに送信して応答を取得
            api_response = await self.send_to_api(user_input)
            if not api_response:
                await self.post_message("❌ エラーが発生しました。もう一度お試しください。")
                continue
            
            # 情報充足度を表示
            completeness = api_response.get("completeness_score", 0)
            await self.post_message(f"📊 **情報充足度**: {completeness}%")
            
            # 自己解決された情報があれば表示
            if api_response.get("self_resolved"):
                resolved_text = "✨ **知識ベースから自動解決された情報**\n"
                for item in api_response["self_resolved"]:
                    resolved_text += f"Q: {item['question']}\n"
                    resolved_text += f"A: {item['answer']}\n\n"
                await self.post_message(resolved_text)
                await asyncio.sleep(1)
            
            # 応答タイプに応じて処理
            if api_response["type"] == "follow_up":
                # 追加質問
                if api_response.get("questions"):
                    questions_text = "📝 **追加で確認させてください：**\n"
                    for i, q in enumerate(api_response["questions"], 1):
                        questions_text += f"{i}. {q}\n"
                    await self.post_message(questions_text)
                else:
                    await self.post_message("✅ 十分な情報が集まりました。アクションプランを作成します...")
                    await asyncio.sleep(1)
                    
                    # アクションプラン生成を促す
                    final_response = await self.send_to_api("アクションプランを作成してください")
                    if final_response and final_response["type"] == "action_plan":
                        api_response = final_response
                    else:
                        break
            
            if api_response["type"] == "action_plan":
                # アクションプラン表示
                action_plan = api_response["action_plan"]
                
                # サマリー
                await self.post_message(
                    f"🎯 **アクションプラン完成！**\n\n" +
                    f"📋 **概要**: {action_plan['summary']}"
                )
                await asyncio.sleep(1)
                
                # 提供されたテンプレート
                if action_plan.get("templates_provided"):
                    templates_text = "📑 **すぐに使えるテンプレート**\n"
                    for template in action_plan["templates_provided"][:3]:
                        templates_text += f"• {template['title']} ({template['category']})\n"
                    await self.post_message(templates_text)
                    await asyncio.sleep(1)
                
                # アクションアイテム
                actions_text = "📈 **具体的なアクション**\n\n"
                for i, item in enumerate(action_plan["action_items"][:5], 1):
                    priority_emoji = "🔴" if item.get("priority") == "high" else "🟡"
                    actions_text += f"{priority_emoji} **{i}. {item.get('title', '')}**\n"
                    actions_text += f"   {item.get('description', '')}\n"
                    if item.get('due_date'):
                        actions_text += f"   📅 期限: {item['due_date']}\n"
                    actions_text += "\n"
                
                await self.post_message(actions_text)
                await asyncio.sleep(1)
                
                # 成功のポイント
                if action_plan.get("mentor_suggestions"):
                    mentor_text = "👥 **先輩からのアドバイス**\n"
                    for suggestion in action_plan["mentor_suggestions"][:3]:
                        mentor_text += f"• {suggestion}\n"
                    await self.post_message(mentor_text)
                
                # 完了メッセージ
                await self.post_message(
                    "✅ **対話完了！**\n\n" +
                    "アクションプランに沿って実践を始めましょう。" +
                    "進捗や新しい課題があれば、いつでもご相談ください！"
                )
                break
            
            conversation_count += 1
        
        # デモ終了
        print("\n" + "="*80)
        print("🎭 デモ終了")
        print("="*80)

async def main():
    """メイン実行関数"""
    print("🤖 Sales Growth AI - Slack理想的対話デモ")
    print("=" * 60)
    
    # 環境設定チェック
    print("📋 環境設定チェック:")
    if not settings.SLACK_BOT_TOKEN:
        print("❌ SLACK_BOT_TOKENが設定されていません")
        print("   .envファイルに以下を追加してください:")
        print("   SLACK_BOT_TOKEN=xoxb-your-bot-token")
        return
    else:
        print("✅ SLACK_BOT_TOKEN: 設定済み")
    
    # APIサーバーチェック
    print("\n🔍 APIサーバー接続チェック...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    print("✅ APIサーバー: 接続成功")
                else:
                    print("❌ APIサーバー: 接続失敗")
                    print("   以下のコマンドでサーバーを起動してください:")
                    print("   cd backend && uvicorn app.main:app --reload")
                    return
    except:
        print("❌ APIサーバーに接続できません")
        print("   サーバーが起動していることを確認してください")
        return
    
    # デモ実行確認
    print("\n" + "="*60)
    print("📝 デモの内容:")
    print("1. Slack DMでAIエージェントと対話")
    print("2. 営業課題についての質問に回答")
    print("3. 知識ベースを活用した自己解決")
    print("4. 具体的なアクションプラン生成")
    print("="*60)
    
    confirm = input("\nデモを開始しますか？ (y/n): ")
    if confirm.lower() != 'y':
        print("デモをキャンセルしました")
        return
    
    # デモ実行
    try:
        async with SlackIdealDialogueDemo() as demo:
            await demo.run_ideal_dialogue_scenario()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())