"""
過去の会話履歴機能のテストスクリプト
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000/enhanced"


async def print_section(title: str):
    """セクション区切りを表示"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


async def test_conversation_history_flow():
    """会話履歴機能の完全なフローをテスト"""
    
    async with aiohttp.ClientSession() as session:
        
        # ユーザーIDを設定（実際の使用では認証から取得）
        user_id = "test_user_001"
        
        # 1. 初回セッション：プレゼンの緊張について
        await print_section("1. 初回セッション開始")
        
        start_data = {
            "user_name": "山田太郎",
            "department": "営業部",
            "experience_years": 1,
            "initial_topic": "プレゼンテーション",
            "specific_challenge": "プレゼンで緊張して頭が真っ白になる"
        }
        
        async with session.post(f"{BASE_URL}/start", json=start_data) as resp:
            result = await resp.json()
            session_id_1 = result["session_id"]
            print(f"セッションID: {session_id_1}")
            print(f"初期質問: {json.dumps(result['questions'], ensure_ascii=False, indent=2)}")
            print(f"自己解決された洞察: {len(result['self_resolved_insights'])}件")
        
        # 初回セッションで会話
        messages_1 = [
            "明日重要なプレゼンがあるのですが、人前に立つと緊張して言葉が出なくなります",
            "原稿は準備していますが、緊張すると頭が真っ白になって忘れてしまいます",
            "先週も途中で言葉に詰まってしまい、上司にフォローしてもらいました"
        ]
        
        for msg in messages_1:
            await print_section(f"メッセージ送信: {msg[:30]}...")
            
            msg_data = {
                "session_id": session_id_1,
                "message": msg,
                "user_id": user_id
            }
            
            async with session.post(f"{BASE_URL}/message", json=msg_data) as resp:
                result = await resp.json()
                print(f"応答タイプ: {result['type']}")
                if result['type'] == 'follow_up':
                    print(f"フォローアップ質問: {json.dumps(result['questions'], ensure_ascii=False, indent=2)}")
                else:
                    print("アクションプラン生成完了")
        
        # セッションサマリーを作成
        await print_section("セッション1のサマリーを作成")
        async with session.post(f"{BASE_URL}/session/{session_id_1}/summary") as resp:
            summary_1 = await resp.json()
            print(json.dumps(summary_1, ensure_ascii=False, indent=2))
        
        # 2. 2週間後、2回目のセッション：新規開拓について
        await print_section("2. 2週間後、2回目のセッション開始")
        
        start_data_2 = {
            "user_name": "山田太郎",
            "department": "営業部",
            "experience_years": 1,
            "initial_topic": "新規開拓",
            "specific_challenge": "新規顧客の開拓がうまくいかない"
        }
        
        async with session.post(f"{BASE_URL}/start", json=start_data_2) as resp:
            result = await resp.json()
            session_id_2 = result["session_id"]
            print(f"セッションID: {session_id_2}")
            print(f"初期質問: {json.dumps(result['questions'], ensure_ascii=False, indent=2)}")
        
        # 3. ユーザーの会話履歴を確認
        await print_section("3. ユーザーの会話履歴を確認")
        
        async with session.get(f"{BASE_URL}/user/{user_id}/history") as resp:
            history = await resp.json()
            print(f"総セッション数: {history['total_sessions']}")
            print(f"よくある課題: {json.dumps(history['common_challenges'], ensure_ascii=False)}")
            print(f"強み: {json.dumps(history['strengths'], ensure_ascii=False)}")
            print(f"学習スタイル: {history['preferred_learning_style']}")
        
        # 4. ユーザーの洞察を確認
        await print_section("4. ユーザーの洞察を確認")
        
        async with session.get(f"{BASE_URL}/user/{user_id}/insights") as resp:
            insights = await resp.json()
            print("抽出された洞察:")
            for insight in insights['insights']:
                print(f"  - [{insight['type']}] {insight['content']} (確信度: {insight['confidence']})")
            
            print("\n行動パターン:")
            for pattern in insights['patterns']:
                print(f"  - [{pattern['type']}] {pattern['description']} (頻度: {pattern['frequency']})")
        
        # 5. 3回目のセッション：再びプレゼンについて（過去の履歴を活用）
        await print_section("5. 3回目のセッション：プレゼン（履歴活用）")
        
        start_data_3 = {
            "user_name": "山田太郎",
            "department": "営業部",
            "experience_years": 1,
            "initial_topic": "プレゼンテーション",
            "specific_challenge": "大型案件のプレゼンが控えている"
        }
        
        async with session.post(f"{BASE_URL}/start", json=start_data_3) as resp:
            result = await resp.json()
            session_id_3 = result["session_id"]
            print(f"セッションID: {session_id_3}")
            print(f"初期質問: {json.dumps(result['questions'], ensure_ascii=False, indent=2)}")
            print(f"\n注目ポイント: 過去の会話履歴を活用して、より的確な質問が生成されているはずです")
        
        # パーソナライズされた対話
        msg_data_3 = {
            "session_id": session_id_3,
            "message": "来週、役員向けの大型案件プレゼンがあります。前回教えていただいた深呼吸法は効果がありましたが、まだ不安です",
            "user_id": user_id
        }
        
        async with session.post(f"{BASE_URL}/message", json=msg_data_3) as resp:
            result = await resp.json()
            print(f"\n応答タイプ: {result['type']}")
            print(f"パーソナライズ済み: {result.get('personalized', False)}")
            
            if result['type'] == 'follow_up':
                print(f"パーソナライズされた質問:")
                for q in result['questions']:
                    print(f"  - {q}")
            
            if result.get('past_insights_used'):
                print(f"\n過去の洞察を{result['past_insights_used']}件活用しました")
        
        # 6. デモシナリオで履歴機能を確認
        await print_section("6. デモシナリオ実行（履歴機能付き）")
        
        async with session.get(f"{BASE_URL}/demo/scenario/nervous_presentation") as resp:
            demo_result = await resp.json()
            print(f"シナリオ: {demo_result['scenario']}")
            print(f"ユーザーID: {demo_result['user_id']}")
            print(f"インタラクション数: {len(demo_result['interactions'])}")


async def test_specific_features():
    """特定の機能をテスト"""
    
    async with aiohttp.ClientSession() as session:
        
        await print_section("会話履歴機能の特定機能テスト")
        
        # 1. 過去の成功パターンの活用
        print("1. 過去の成功パターンが新しいアクションプランに反映されるか")
        
        # 2. 学習スタイルに基づくカスタマイズ
        print("2. ユーザーの学習スタイル（実践的）に合わせた提案がされるか")
        
        # 3. 繰り返し出現する課題の認識
        print("3. 同じ課題が繰り返し出現した場合、それを認識して対応するか")
        
        # 4. 進捗の追跡
        print("4. 過去のセッションからの進捗を追跡し、改善を認識するか")


async def main():
    """メインテスト実行"""
    
    print("=" * 80)
    print(" 会話履歴機能テスト")
    print("=" * 80)
    print("\nこのテストは、ユーザーの過去の会話履歴を活用して")
    print("より効果的な対話を実現する機能をテストします。")
    print("\n主な確認ポイント:")
    print("- 過去の会話から洞察を抽出")
    print("- ユーザープロファイルの構築")
    print("- パーソナライズされた質問生成")
    print("- 過去の成功パターンの活用")
    
    try:
        # 完全なフローテスト
        await test_conversation_history_flow()
        
        # 特定機能のテスト
        await test_specific_features()
        
        print("\n" + "="*80)
        print(" テスト完了")
        print("="*80)
        
    except aiohttp.ClientError as e:
        print(f"\nエラー: サーバーに接続できません。")
        print(f"サーバーが起動していることを確認してください。")
        print(f"詳細: {e}")
    except Exception as e:
        print(f"\n予期しないエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())