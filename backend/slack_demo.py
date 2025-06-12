#!/usr/bin/env python3
"""
Slack統合デモスクリプト

このスクリプトはSlack統合機能のテストとデモを行います。
"""

import asyncio
import requests
import json
from app.core.config import settings

def test_slack_health():
    """Slack統合のヘルスチェック"""
    print("🔍 Slack統合ヘルスチェック...")
    
    try:
        response = requests.get("http://localhost:8000/api/slack/health")
        result = response.json()
        
        print(f"ステータス: {result['status']}")
        print(f"メッセージ: {result['message']}")
        
        if result['status'] == 'healthy':
            print("✅ Slack統合は正常に動作しています")
            return True
        else:
            print("❌ Slack統合に問題があります")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません。サーバーが起動していることを確認してください。")
        return False
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def test_app_health():
    """アプリ全体のヘルスチェック"""
    print("\n🔍 アプリケーション全体のヘルスチェック...")
    
    try:
        response = requests.get("http://localhost:8000/health")
        result = response.json()
        
        print(f"ステータス: {result['status']}")
        print(f"バージョン: {result['version']}")
        print("✅ アプリケーションは正常に動作しています")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません")
        return False
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def simulate_slack_event():
    """Slack イベントのシミュレーション"""
    print("\n🧪 Slack イベントシミュレーション...")
    
    # 実際のSlack Eventの構造を模擬
    mock_event = {
        "token": "verification_token",
        "team_id": "T1234567890",
        "api_app_id": "A1234567890",
        "event": {
            "type": "message",
            "user": "U1234567890",
            "text": "営業成績の向上について相談したいです",
            "ts": "1234567890.123456",
            "channel": "D1234567890",
            "event_ts": "1234567890.123456"
        },
        "type": "event_callback",
        "event_id": "Ev1234567890",
        "event_time": 1234567890
    }
    
    print("📝 模擬Slackイベント:")
    print(json.dumps(mock_event, indent=2, ensure_ascii=False))
    
    # 注意: 実際のSlack署名検証は行わない（デモ用）
    print("\n⚠️  実際のSlackからのリクエストには適切な署名検証が必要です")
    
    return mock_event

def print_integration_summary():
    """統合概要を表示"""
    print("\n" + "=" * 60)
    print("📱 Slack統合 実装概要")
    print("=" * 60)
    
    print("\n✅ 実装済み機能:")
    print("• Slack SDK (slack-bolt) の統合")
    print("• Event Subscriptions 対応")
    print("• App Mentions (/slackbot @bot-name)")
    print("• Direct Messages (DM)")
    print("• 既存AI対話システムとの連携")
    print("• ユーザーセッション管理")
    print("• エラーハンドリング")
    print("• 環境設定とヘルスチェック")
    
    print("\n🔧 設定されたエンドポイント:")
    print("• POST /api/slack/events - Slack Events API")
    print("• GET /api/slack/health - Slack統合ヘルスチェック")
    print("• POST /api/slack/install - アプリインストール用")
    print("• GET /api/slack/oauth - OAuth認証用")
    
    print("\n📋 必要な権限 (Bot Token Scopes):")
    scopes = [
        "app_mentions:read",
        "channels:history", 
        "chat:write",
        "commands",
        "im:history",
        "im:read", 
        "im:write",
        "mpim:history",
        "mpim:read",
        "mpim:write"
    ]
    
    for scope in scopes:
        print(f"• {scope}")
    
    print("\n🚀 使用方法:")
    print("1. Slack Developer Portalでアプリを作成")
    print("2. 環境変数を設定 (.env ファイル)")
    print("3. サーバーを起動")
    print("4. ngrok等で外部からアクセス可能にする")
    print("5. Slack Event SubscriptionsのRequest URLを設定")
    print("6. アプリをワークスペースにインストール")
    print("7. Slackでボットとチャット開始！")

def print_demo_commands():
    """デモ用のコマンド例を表示"""
    print("\n" + "=" * 60)
    print("💬 Slackでのテスト用メッセージ例")
    print("=" * 60)
    
    test_messages = [
        "営業成績を向上させたいです",
        "1on1ミーティングのフィードバック: 顧客アプローチが消極的でクロージングが弱い",
        "新規開拓がうまくいかない理由を分析してください",
        "アクションプランを作成してください",
        "進捗を確認したいです"
    ]
    
    print("DM（ダイレクトメッセージ）またはチャンネルでメンション:")
    for i, msg in enumerate(test_messages, 1):
        print(f"{i}. {msg}")
    
    print("\nチャンネルでの使用例:")
    print("@Sales Growth AI Agent 営業成績を向上させたいです")

async def main():
    """メイン実行関数"""
    print("🤖 Sales Growth AI - Slack統合デモ")
    print("=" * 60)
    
    # 環境設定チェック
    print("📋 環境設定チェック:")
    env_vars = [
        ("USE_MOCK_LLM", settings.USE_MOCK_LLM),
        ("SLACK_BOT_TOKEN", "設定済み" if settings.SLACK_BOT_TOKEN else "未設定"),
        ("SLACK_SIGNING_SECRET", "設定済み" if settings.SLACK_SIGNING_SECRET else "未設定")
    ]
    
    for name, value in env_vars:
        print(f"• {name}: {value}")
    
    # ヘルスチェック
    app_healthy = test_app_health()
    slack_healthy = test_slack_health()
    
    if not app_healthy:
        print("\n❌ サーバーが起動していません。以下のコマンドでサーバーを起動してください:")
        print("cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # イベントシミュレーション
    simulate_slack_event()
    
    # 概要表示
    print_integration_summary()
    print_demo_commands()
    
    print("\n" + "=" * 60)
    print("🎯 次のステップ:")
    print("1. python slack_setup_guide.py でセットアップガイドを確認")
    print("2. Slack Appの設定を完了")
    print("3. 環境変数の設定")
    print("4. Slackでのテスト")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())