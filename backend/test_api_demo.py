#!/usr/bin/env python3
"""
理想的な対話APIの簡単なテスト

APIが正常に動作することを確認します。
"""

import requests
import json
import time

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 理想的な対話API テスト")
    print("=" * 50)
    
    # 1. セッション開始
    print("1. セッション開始...")
    start_response = requests.post(
        f"{base_url}/api/ideal-dialogue/start",
        json={
            "abstract_instruction": "もっと顧客との関係を深めて売上を伸ばしてほしい",
            "user_context": {
                "name": "田中",
                "role": "新人営業担当",
                "experience": "6ヶ月"
            }
        }
    )
    
    if start_response.status_code == 200:
        start_data = start_response.json()
        session_id = start_data["session_id"]
        print(f"✅ セッション開始成功: {session_id}")
        print(f"🤖 挨拶: {start_data['message'][:100]}...")
    else:
        print(f"❌ セッション開始失敗: {start_response.status_code}")
        return
    
    # 2. 対話テスト
    test_responses = [
        "今月も目標の85%でした。新規開拓8割、既存フォロー2割くらいです。正直、関係を深めるという指示が抽象的で困っています。",
        "A社の佐藤部長とは良い関係です。月1回訪問して、先月は追加注文もいただけました。仕事以外の話もするようになったのが良かったと思います。",
        "大口で関係薄いB社・C社を優先的にアプローチしたいです。A社と同じように定期訪問と信頼関係構築を考えています。",
        "来月までにB社・C社に各2回ずつ訪問し、担当者の関心事を3つずつ把握したいです。3ヶ月後には各社10%の売上アップを目指します。",
        "時間確保が一番の課題です。新規開拓時間の一部を既存フォローに振り分けて、週次で進捗確認したいと思います。"
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n{i}. 部下の回答を送信...")
        print(f"👤 {response[:50]}...")
        
        dialogue_response = requests.post(
            f"{base_url}/api/ideal-dialogue/respond",
            json={
                "session_id": session_id,
                "user_response": response
            }
        )
        
        if dialogue_response.status_code == 200:
            dialogue_data = dialogue_response.json()
            print(f"✅ 回答処理成功")
            
            if dialogue_data["type"] == "question":
                print(f"🤖 次の質問: {dialogue_data['message'][:100]}...")
                if dialogue_data.get("progress"):
                    print(f"📊 進捗: {dialogue_data['progress']['percentage']}%")
            elif dialogue_data["type"] == "summary":
                print(f"🎉 アクションプラン完成！")
                print(f"🤖 最終メッセージ: {dialogue_data['message'][:100]}...")
                
                # アクションプランの概要を表示
                if dialogue_data.get("action_plan"):
                    action_plan = dialogue_data["action_plan"]
                    if "short_term_goals" in action_plan:
                        print(f"📋 短期目標数: {len(action_plan['short_term_goals'])}")
                break
        else:
            print(f"❌ 回答処理失敗: {dialogue_response.status_code}")
            break
        
        time.sleep(1)  # API負荷軽減
    
    # 3. セッション情報取得
    print(f"\n3. セッション情報取得...")
    progress_response = requests.get(f"{base_url}/api/ideal-dialogue/session/{session_id}/progress")
    
    if progress_response.status_code == 200:
        progress_data = progress_response.json()
        print(f"✅ 進捗取得成功")
        print(f"📊 対話回数: {progress_data['dialogue_count']}")
        print(f"📋 現在の状態: {progress_data['current_state']}")
    else:
        print(f"❌ 進捗取得失敗: {progress_response.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ APIテスト完了！")
    print("\n💡 次のステップ:")
    print("- python ideal_interactive_demo.py (インタラクティブ体験)")
    print("- python demo_ideal_scenario.py (自動実演)")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません。")
        print("以下のコマンドでサーバーを起動してください：")
        print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")