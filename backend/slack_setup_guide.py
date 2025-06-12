#!/usr/bin/env python3
"""
Slack App セットアップガイド

このスクリプトはSlack Appの設定手順を案内します。
"""

import os
from app.core.config import settings

def print_setup_guide():
    """Slack App設定ガイドを表示"""
    print("=" * 60)
    print("🚀 Sales Growth AI - Slack App セットアップガイド")
    print("=" * 60)
    
    print("\n📋 必要な手順:")
    print("1. Slack Developer Portalでアプリを作成する")
    print("2. Bot Token Scopes を設定する")
    print("3. Event Subscriptions を設定する")
    print("4. 環境変数を設定する")
    print("5. アプリをワークスペースにインストールする")
    
    print("\n" + "=" * 60)
    print("1️⃣  Slack Developer Portal でアプリを作成")
    print("=" * 60)
    print("• https://api.slack.com/apps にアクセス")
    print("• 'Create New App' をクリック")
    print("• 'From scratch' を選択")
    print("• App Name: Sales Growth AI Agent")
    print("• Workspace: あなたのワークスペースを選択")
    
    print("\n" + "=" * 60)
    print("2️⃣  Bot Token Scopes を設定")
    print("=" * 60)
    print("左メニューの 'OAuth & Permissions' → 'Scopes' → 'Bot Token Scopes':")
    print("• app_mentions:read")
    print("• channels:history")
    print("• chat:write")
    print("• commands")
    print("• im:history")
    print("• im:read")
    print("• im:write")
    print("• mpim:history")
    print("• mpim:read")
    print("• mpim:write")
    
    print("\n" + "=" * 60)
    print("3️⃣  Event Subscriptions を設定")
    print("=" * 60)
    print("左メニューの 'Event Subscriptions':")
    print("• Enable Events: ON")
    print("• Request URL: https://your-domain.com/api/slack/events")
    print("  (開発中は ngrok を使用)")
    print("• Subscribe to bot events:")
    print("  - app_mention")
    print("  - message.channels")
    print("  - message.im")
    print("  - message.mpim")
    
    print("\n" + "=" * 60)
    print("4️⃣  環境変数を設定")
    print("=" * 60)
    
    # 現在の設定状況をチェック
    env_status = []
    
    if settings.SLACK_BOT_TOKEN:
        env_status.append("✅ SLACK_BOT_TOKEN: 設定済み")
    else:
        env_status.append("❌ SLACK_BOT_TOKEN: 未設定")
        print("• OAuth & Permissions → Bot User OAuth Token をコピー")
        print("  SLACK_BOT_TOKEN=xoxb-...")
    
    if settings.SLACK_SIGNING_SECRET:
        env_status.append("✅ SLACK_SIGNING_SECRET: 設定済み")
    else:
        env_status.append("❌ SLACK_SIGNING_SECRET: 未設定")
        print("• Basic Information → Signing Secret をコピー")
        print("  SLACK_SIGNING_SECRET=...")
    
    if settings.SLACK_APP_TOKEN:
        env_status.append("✅ SLACK_APP_TOKEN: 設定済み")
    else:
        env_status.append("❌ SLACK_APP_TOKEN: 未設定 (Socket Mode用)")
        print("• Basic Information → App-Level Tokens で作成")
        print("  SLACK_APP_TOKEN=xapp-...")
    
    print("\n現在の設定状況:")
    for status in env_status:
        print(f"  {status}")
    
    print("\n" + "=" * 60)
    print("5️⃣  アプリをワークスペースにインストール")
    print("=" * 60)
    print("• OAuth & Permissions → 'Install to Workspace'")
    print("• 権限を確認して 'Allow' をクリック")
    
    print("\n" + "=" * 60)
    print("🧪 テスト方法")
    print("=" * 60)
    print("1. サーバーを起動:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n2. ngrokでトンネルを作成 (開発時):")
    print("   ngrok http 8000")
    print("\n3. Slack Event Subscriptions のRequest URLを更新:")
    print("   https://your-ngrok-url.ngrok.io/api/slack/events")
    print("\n4. Slackでテスト:")
    print("   • DMでボットにメッセージを送信")
    print("   • チャンネルでボットをメンション (@Sales Growth AI Agent)")
    
    print("\n" + "=" * 60)
    print("🔧 デバッグ用URL")
    print("=" * 60)
    print("• ヘルスチェック: http://localhost:8000/api/slack/health")
    print("• アプリ全体のヘルス: http://localhost:8000/health")
    print("• 設定確認: http://localhost:8000/config")
    
    print("\n" + "=" * 60)
    print("📚 参考リンク")
    print("=" * 60)
    print("• Slack Bolt for Python: https://slack.dev/bolt-python/")
    print("• Slack API Events: https://api.slack.com/events")
    print("• ngrok: https://ngrok.com/")


def check_environment():
    """環境設定のチェック"""
    print("\n🔍 環境設定チェック結果:")
    print("-" * 40)
    
    checks = [
        ("SLACK_BOT_TOKEN", settings.SLACK_BOT_TOKEN),
        ("SLACK_SIGNING_SECRET", settings.SLACK_SIGNING_SECRET),
        ("SLACK_APP_TOKEN", settings.SLACK_APP_TOKEN),
        ("USE_MOCK_LLM", settings.USE_MOCK_LLM),
    ]
    
    all_good = True
    for name, value in checks:
        if value:
            status = "✅"
            display_value = "設定済み" if name.startswith("SLACK") else str(value)
        else:
            status = "❌" 
            display_value = "未設定"
            if name.startswith("SLACK"):
                all_good = False
        
        print(f"{status} {name}: {display_value}")
    
    if all_good:
        print("\n🎉 Slack統合の準備が完了しています！")
    else:
        print("\n⚠️  設定が不完全です。上記の未設定項目を確認してください。")
    
    return all_good


if __name__ == "__main__":
    print_setup_guide()
    check_environment()
    
    print("\n" + "=" * 60)
    print("次のステップ:")
    print("1. 上記の手順に従ってSlack Appを設定")
    print("2. 環境変数を .env ファイルに設定")  
    print("3. サーバーを起動: uvicorn app.main:app --reload")
    print("4. Slackでテストメッセージを送信")
    print("=" * 60)