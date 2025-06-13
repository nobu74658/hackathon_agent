#!/usr/bin/env python3
"""
理想的な対話シナリオ - クイック体験デモ

IDEAL_DIALOGUE_SCENARIO.mdの内容を簡潔に体験できます。
"""

import requests
import json

def main():
    base_url = "http://localhost:8000"
    
    print("🎯 理想的な対話シナリオ - クイック体験")
    print("=" * 60)
    print()
    
    # セッション開始
    print("🚀 セッション開始...")
    start_response = requests.post(
        f"{base_url}/api/ideal-dialogue/start",
        json={
            "abstract_instruction": "もっと顧客との関係を深めて売上を伸ばしてほしい",
            "user_context": {
                "name": "田中",
                "role": "新人営業担当", 
                "experience": "入社6ヶ月"
            }
        }
    )
    
    start_data = start_response.json()
    session_id = start_data["session_id"]
    
    print(f"🤖 AIコーチ:\n{start_data['message']}\n")
    print("-" * 60)
    
    # シナリオに基づく対話
    scenario_steps = [
        {
            "phase": "現状把握",
            "user_input": "今月も目標の85%でした...先月も同じくらいで、なかなか目標に届かないんです。新規開拓が8割、既存顧客フォローが2割くらいです。正直、「関係を深める」という指示が抽象的でよく分からないんです。",
            "description": "売上状況と現状の困惑を表現"
        },
        {
            "phase": "課題分析", 
            "user_input": "A社の佐藤部長とは良い関係だと思います。月1回は必ず訪問して、仕事以外の話もするようになりました。先月は追加注文をいただけて、他部署の課長も紹介してもらえました。",
            "description": "成功事例と具体的な成果を共有"
        },
        {
            "phase": "ソリューション探索",
            "user_input": "大口で関係が良いのがA社、大口だけど関係が薄いのがB社とC社、小口だけど関係が良いのがD社、E社という感じです。「大口だけど関係が薄い」B社、C社から始めるのが効率的だと思います。",
            "description": "顧客セグメンテーションと優先順位"
        },
        {
            "phase": "アクションプラン",
            "user_input": "来月までに、B社、C社それぞれに2回ずつ訪問して、担当者の趣味や関心事を3つずつ把握したいと思います。3ヶ月後にはB社、C社からそれぞれ10%の売上アップを目指したいです。",
            "description": "SMART目標の設定"
        },
        {
            "phase": "実行支援",
            "user_input": "時間の確保が一番の課題です。新規開拓の一部の時間を既存顧客フォローに振り分けることで時間を確保できそうです。週次で訪問回数と関係構築の進捗をチェックし、2週間後に中間レビューを行いたいと思います。",
            "description": "課題と解決策、進捗管理方法"
        }
    ]
    
    for step in scenario_steps:
        print(f"📋 【{step['phase']}フェーズ】{step['description']}")
        print(f"👤 田中さん: {step['user_input']}")
        print()
        
        # 対話を送信
        response = requests.post(
            f"{base_url}/api/ideal-dialogue/respond",
            json={
                "session_id": session_id,
                "user_response": step['user_input']
            }
        )
        
        data = response.json()
        
        if data["type"] == "question":
            progress = data.get("progress", {})
            print(f"📊 進捗: {progress.get('percentage', 0)}%")
            print(f"🤖 AIコーチ: {data['message']}")
            if data.get("purpose"):
                print(f"💡 質問の目的: {data['purpose']}")
            
        elif data["type"] == "summary":
            print("🎉 アクションプラン完成！")
            print(f"🤖 AIコーチ: {data['message']}")
            
            # アクションプランの表示
            if data.get("action_plan"):
                plan = data["action_plan"]
                print("\n📋 生成されたアクションプラン:")
                print("-" * 40)
                
                if "short_term_goals" in plan:
                    print("🎯 短期目標（1ヶ月）:")
                    for goal in plan["short_term_goals"]:
                        print(f"  • {goal.get('goal', '')}")
                        print(f"    期限: {goal.get('deadline', '')}")
                        print(f"    測定: {goal.get('metrics', '')}")
                
                if "challenges_and_solutions" in plan:
                    print("\n⚠️ 課題と解決策:")
                    for item in plan["challenges_and_solutions"]:
                        print(f"  • 課題: {item.get('challenge', '')}")
                        print(f"    解決策: {item.get('solution', '')}")
            break
        
        print()
        print("-" * 60)
        print()
    
    print("\n" + "=" * 60)
    print("✅ 理想的な対話シナリオの体験完了！")
    print()
    print("📚 このように上司の抽象的な指示:")
    print("「もっと顧客との関係を深めて売上を伸ばしてほしい」")
    print()
    print("↓ ソクラテス式質問法により")
    print()
    print("📝 具体的で実行可能なアクションプランに変換されました！")
    print()
    print("🚀 さらに体験したい場合:")
    print("- python ideal_interactive_demo.py (対話形式)")
    print("- ブラウザで http://localhost:8000/docs (API仕様)")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません。")
        print("以下のコマンドでサーバーを起動してください：")
        print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ エラー: {e}")