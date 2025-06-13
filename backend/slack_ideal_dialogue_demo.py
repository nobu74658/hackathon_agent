#!/usr/bin/env python3
"""
Slack理想的な対話機能のデモスクリプト

このスクリプトは、Slack上で理想的な対話機能をテストするための
シンプルなデモを提供します。
"""

import os
import asyncio
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


async def send_demo_messages():
    """デモメッセージを送信"""
    
    # Slack設定を確認
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        print("❌ SLACK_BOT_TOKEN が設定されていません。")
        print("💡 .env ファイルに以下を追加してください：")
        print("   SLACK_BOT_TOKEN=xoxb-your-bot-token")
        return
    
    # Slackクライアントを初期化
    client = WebClient(token=bot_token)
    
    print("🚀 Slack理想的な対話機能デモ")
    print("=" * 50)
    
    try:
        # Bot情報を取得
        auth_response = client.auth_test()
        bot_user_id = auth_response["user_id"]
        print(f"✅ Bot接続成功: {auth_response['user']} (ID: {bot_user_id})")
        
        # 使用方法を表示
        print("\n📋 使用方法:")
        print("1. SlackでBotにDMを送信するか、チャンネルでメンションしてください")
        print("2. 以下のメッセージ例を使って対話を開始できます：")
        print()
        print("--- メッセージ例 ---")
        print("🔸 ソクラテス式の対話を始めたい")
        print("🔸 理想的な対話で売上向上のアクションプランを作りたい")
        print("🔸 コーチングで営業スキルを向上させたい")
        print("🔸 具体化のサポートをお願いします")
        print()
        print("3. 対話が始まったら、質問に自然な言葉で答えてください")
        print("4. 「終了」と入力すると対話を終了できます")
        print()
        
        # 対話の流れを説明
        print("📊 対話の流れ:")
        print("1️⃣ 現状把握 → 2️⃣ 課題分析 → 3️⃣ 解決策探索")
        print("→ 4️⃣ アクションプラン作成 → 5️⃣ 実行支援")
        print()
        
        # テスト用チャンネルの確認
        print("💡 ヒント: テスト用のプライベートチャンネルを作成して、")
        print("   Botを招待してからテストすることをお勧めします。")
        print()
        
        # サーバーの起動確認
        print("⚠️  注意: FastAPIサーバーが起動していることを確認してください")
        print("   起動コマンド: cd backend && uvicorn app.main:app --reload")
        print()
        print("✨ 準備ができたら、Slackで対話を始めてください！")
        
    except SlackApiError as e:
        print(f"❌ Slack API エラー: {e.response['error']}")
        print("💡 トークンが正しいか、必要な権限があるか確認してください")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


def main():
    """メイン関数"""
    print("Slack理想的な対話機能 - セットアップガイド")
    print("=" * 50)
    print()
    
    # 環境変数のチェック
    required_vars = [
        "SLACK_BOT_TOKEN",
        "SLACK_SIGNING_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 以下の環境変数が設定されていません:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("💡 .envファイルを作成して、必要な環境変数を設定してください")
        print()
        print("例：")
        print("SLACK_BOT_TOKEN=xoxb-your-bot-token")
        print("SLACK_SIGNING_SECRET=your-signing-secret")
        return
    
    # デモを実行
    asyncio.run(send_demo_messages())


if __name__ == "__main__":
    main()