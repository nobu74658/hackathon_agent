#!/usr/bin/env python3
"""
Slackメッセージ処理のテストスクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.slack_service import SlackService
from app.services.dialogue_manager import DialogueManager


async def test_message_processing():
    """メッセージ処理のテスト"""
    
    # テストメッセージ（長い1on1ログの一部）
    test_message = """
佐藤：田中くん、最近の営業活動の調子はどう？

田中：はい、今週は5件の新規アポを獲得できました。ただ、成約にはまだ至っていなくて…。

佐藤：なるほどね。悪くはないけど、もう少しお客様との距離を詰めていけるといいね。

田中：距離を詰める、ですか…。例えばどういうことを意識すればよいでしょうか？
"""
    
    print("🧪 Slackメッセージ処理テスト開始")
    print(f"📝 テストメッセージ長: {len(test_message)} 文字")
    
    try:
        # DialogueManagerを直接テスト
        dialogue_manager = DialogueManager()
        session_id = "test_session_001"
        
        print("\n1️⃣ DialogueManagerの直接テスト...")
        
        response = await dialogue_manager.process_user_response(
            session_id=session_id,
            user_response=test_message,
            db_session=None
        )
        
        print(f"✅ DialogueManager応答タイプ: {response['type']}")
        print(f"📊 完了度スコア: {response.get('completeness_score', 'N/A')}%")
        
        if response["type"] == "follow_up":
            questions = response["questions"]
            print(f"❓ 生成された質問数: {len(questions)}")
            for i, q in enumerate(questions[:3], 1):
                print(f"   {i}. {q}")
                
        elif response["type"] == "action_plan":
            action_plan = response["data"]
            print(f"📋 アクションプラン概要: {action_plan.get('summary', 'N/A')}")
            action_items = action_plan.get('action_items', [])
            print(f"📝 アクションアイテム数: {len(action_items)}")
        
        print("\n2️⃣ Slackフォーマットテスト...")
        
        # モックのsay関数
        async def mock_say(message):
            print(f"📤 Slack応答: {message[:200]}...")
        
        # SlackServiceのフォーマット機能をテスト
        if response["type"] == "follow_up":
            questions = response["questions"]
            completeness_score = response["completeness_score"]
            
            # フォーマット関数を呼び出し（SlackServiceのインスタンスが必要）
            from app.services.slack_service import SlackService
            try:
                slack_service = SlackService()
                formatted = slack_service._format_questions_for_slack(questions, completeness_score)
                print(f"✅ Slackフォーマット成功: {len(formatted)} 文字")
                
                if len(formatted) > 3000:
                    print("⚠️  フォーマット後のメッセージが3000文字を超えています")
                    
            except Exception as slack_error:
                print(f"❌ Slackサービス初期化エラー: {slack_error}")
                print("💡 環境変数SLACK_BOT_TOKENとSLACK_SIGNING_SECRETが必要です")
        
        print("\n🎉 テスト完了！")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


async def test_short_message():
    """短いメッセージでのテスト"""
    print("\n🧪 短いメッセージテスト")
    
    short_message = "新規開拓で困っています。アドバイスをお願いします。"
    
    try:
        dialogue_manager = DialogueManager()
        session_id = "test_session_002"
        
        response = await dialogue_manager.process_user_response(
            session_id=session_id,
            user_response=short_message,
            db_session=None
        )
        
        print(f"✅ 短いメッセージ処理成功: {response['type']}")
        print(f"📊 完了度スコア: {response.get('completeness_score', 'N/A')}%")
        
    except Exception as e:
        print(f"❌ 短いメッセージ処理エラー: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print(" AI営業支援エージェント - Slackメッセージ処理テスト")
    print("=" * 60)
    
    # 非同期実行
    asyncio.run(test_message_processing())
    asyncio.run(test_short_message())