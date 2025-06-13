#!/usr/bin/env python3
"""
Slackでの理想的な対話機能のテスト
"""

import asyncio
import os
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

# 環境変数を設定
os.environ["USE_MOCK_LLM"] = "true"  # モックLLMを使用

from app.services.slack_service import SlackService


async def test_ideal_dialogue_detection():
    """理想的な対話モードの検出テスト"""
    slack_service = SlackService()
    
    test_cases = [
        ("ソクラテス式の対話を始めたい", True),
        ("理想的な対話でコーチングしてください", True),
        ("アクションプランを作成してください", True),
        ("今日の天気は？", False),
        ("売上について相談したい", False),  # このキーワードだけでは開始しない
    ]
    
    print("=== 理想的な対話モード検出テスト ===\n")
    
    for text, expected in test_cases:
        result = await slack_service._is_ideal_dialogue_mode("test_user", text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' → {result} (期待値: {expected})")


async def test_ideal_dialogue_flow():
    """理想的な対話フローのテスト"""
    slack_service = SlackService()
    
    print("\n\n=== 理想的な対話フローテスト ===\n")
    
    # 1. 対話を開始
    print("1. 対話開始")
    response = await slack_service._handle_ideal_dialogue("test_user", "ソクラテス式の対話で売上向上のアクションプランを作りたい")
    formatted = slack_service._format_ideal_dialogue_for_slack(response)
    print(f"タイプ: {response['type']}")
    print(f"応答:\n{formatted}\n")
    
    # セッションIDを確認
    session_id = slack_service.ideal_dialogue_sessions.get("test_user")
    print(f"セッションID: {session_id}\n")
    
    # 2. 現状について回答
    print("2. 現状について回答")
    response = await slack_service._handle_ideal_dialogue(
        "test_user", 
        "売上が目標の80%程度で、新規開拓に時間を取られて既存顧客のフォローができていません。"
    )
    formatted = slack_service._format_ideal_dialogue_for_slack(response)
    print(f"タイプ: {response['type']}")
    print(f"状態: {response.get('state', 'N/A')}")
    print(f"進捗: {response.get('progress', {}).get('percentage', 0)}%")
    print(f"応答:\n{formatted}\n")
    
    # 3. 成功体験について回答
    print("3. 成功体験について回答")
    response = await slack_service._handle_ideal_dialogue(
        "test_user",
        "A社とは定期的な訪問で関係が深まり、新しい案件をいただけました。"
    )
    formatted = slack_service._format_ideal_dialogue_for_slack(response)
    print(f"タイプ: {response['type']}")
    print(f"状態: {response.get('state', 'N/A')}")
    print(f"応答:\n{formatted}\n")
    
    # 4. セッション終了テスト
    print("4. セッション終了")
    response = await slack_service._handle_ideal_dialogue("test_user", "終了")
    formatted = slack_service._format_ideal_dialogue_for_slack(response)
    print(f"タイプ: {response['type']}")
    print(f"応答:\n{formatted}\n")
    
    # セッションが削除されているか確認
    session_exists = "test_user" in slack_service.ideal_dialogue_sessions
    print(f"セッションが削除されているか: {'❌ まだ存在' if session_exists else '✅ 削除済み'}")


async def test_format_responses():
    """レスポンスフォーマットのテスト"""
    slack_service = SlackService()
    
    print("\n\n=== レスポンスフォーマットテスト ===\n")
    
    # 1. Greeting
    print("1. Greeting フォーマット:")
    response = {
        "type": "greeting",
        "message": "こんにちは田中さん。お疲れ様です。\n\n上司から「もっと顧客との関係を深めて売上を伸ばしてほしい」という指示があったとお聞きしました。"
    }
    formatted = slack_service._format_ideal_dialogue_for_slack(response)
    print(formatted)
    print()
    
    # 2. Question
    print("2. Question フォーマット:")
    response = {
        "type": "question",
        "message": "これまでの顧客との関係で、特にうまくいっている例はありますか？",
        "purpose": "成功体験を発見し、成功パターンを抽出する",
        "state": "problem_analysis",
        "progress": {"percentage": 40}
    }
    formatted = slack_service._format_ideal_dialogue_for_slack(response)
    print(formatted)
    print()
    
    # 3. Summary
    print("3. Summary フォーマット:")
    response = {
        "type": "summary",
        "message": "素晴らしい対話でした！",
        "action_plan": {
            "short_term_goals": [
                {
                    "goal": "優先顧客との関係強化",
                    "actions": ["B社・C社への月2回訪問", "担当者の関心事3つずつ把握"],
                    "deadline": "来月末",
                    "metrics": "訪問回数、関心事把握数"
                }
            ],
            "success_patterns": ["A社との良好な関係構築パターンの活用"],
            "progress_check": {
                "weekly": "訪問実績と関係構築進捗の確認",
                "monthly": "売上数値と目標達成度の評価"
            }
        },
        "insights": {
            "strengths": ["成功体験の活用能力", "現実的な目標設定力"],
            "confidence_level": "対話を通じて自信が向上"
        }
    }
    formatted = slack_service._format_ideal_dialogue_for_slack(response)
    print(formatted)


async def main():
    """メインテスト実行"""
    try:
        await test_ideal_dialogue_detection()
        await test_ideal_dialogue_flow()
        await test_format_responses()
        
        print("\n\n✅ すべてのテストが完了しました！")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())