#!/usr/bin/env python3
"""
理想的な対話シナリオの実演デモ

IDEAL_DIALOGUE_SCENARIO.mdのシナリオを忠実に再現します。
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime
import sys


class IdealScenarioDemo:
    """理想的な対話シナリオのデモンストレーション"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def print_separator(self, char: str = "=", length: int = 60):
        """セパレーターを表示"""
        print(f"\n{char * length}\n")
    
    def print_ai_message(self, message: str, metadata: Dict[str, Any] = None):
        """AIメッセージの表示"""
        print(f"🤖 AIコーチ: {message}")
        if metadata:
            if metadata.get("purpose"):
                print(f"   [目的: {metadata['purpose']}]")
            if metadata.get("progress"):
                progress = metadata["progress"]
                print(f"   [進捗: {progress.get('percentage', 0)}%]")
        print()
    
    def print_user_message(self, message: str):
        """ユーザーメッセージの表示"""
        print(f"👤 田中さん: {message}\n")
    
    def print_scenario_context(self, text: str):
        """シナリオ文脈の表示"""
        print(f"📋 {text}\n")
    
    async def start_session(self):
        """セッションを開始"""
        print("🎯 理想的な対話シナリオ - 実演デモ")
        self.print_separator()
        
        self.print_scenario_context(
            "新人営業担当の田中さん（入社6ヶ月）が、\n"
            "上司から「もっと顧客との関係を深めて売上を伸ばしてほしい」\n"
            "という指示を受けました。月次売上目標を2ヶ月連続で下回っている状況です。"
        )
        
        # セッションを開始
        response = await self.client.post(
            f"{self.base_url}/api/ideal-dialogue/start",
            json={
                "abstract_instruction": "もっと顧客との関係を深めて売上を伸ばしてほしい",
                "user_context": {
                    "name": "田中",
                    "role": "新人営業担当",
                    "experience": "入社6ヶ月",
                    "current_challenge": "月次売上目標を2ヶ月連続で下回っている"
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data["session_id"]
            self.print_ai_message(data["message"])
            return True
        else:
            print(f"❌ エラー: {response.status_code} - {response.text}")
            return False
    
    async def process_dialogue(self, user_response: str) -> Dict[str, Any]:
        """対話を処理"""
        response = await self.client.post(
            f"{self.base_url}/api/ideal-dialogue/respond",
            json={
                "session_id": self.session_id,
                "user_response": user_response
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ エラー: {response.status_code} - {response.text}")
            return None
    
    async def run_scenario(self):
        """理想的なシナリオを実行"""
        # セッション開始
        if not await self.start_session():
            return
        
        self.print_separator()
        
        # シナリオに基づく対話
        scenario_dialogues = [
            {
                "phase": "現状把握",
                "user_response": "今月も目標の85%でした...先月も同じくらいで、なかなか目標に届かないんです。",
                "context": "売上状況について回答"
            },
            {
                "phase": "現状把握",
                "user_response": "うーん、新規開拓が8割、既存顧客フォローが2割くらいでしょうか。",
                "context": "時間配分について回答"
            },
            {
                "phase": "課題分析",
                "user_response": "正直、具体的に何をすればいいのかよく分からないんです。関係を深めるって言っても...",
                "context": "上司の指示への理解について回答"
            },
            {
                "phase": "課題分析",
                "user_response": "A社の佐藤部長とは良い関係だと思います。月1回は必ず訪問して、仕事以外の話もするようになりました。",
                "context": "成功事例について回答"
            },
            {
                "phase": "課題分析",
                "user_response": "そういえば、先月追加注文をいただけました。それに、他部署の課長も紹介してもらえて...",
                "context": "成功事例の成果について回答"
            },
            {
                "phase": "ソリューション探索",
                "user_response": "A社と同じように、定期的に訪問して、信頼関係を築く...でも、全ての顧客に同じだけ時間をかけるのは無理ですし...",
                "context": "他の顧客への応用について考察"
            },
            {
                "phase": "ソリューション探索",
                "user_response": "大口で関係が良いのがA社、大口だけど関係が薄いのがB社とC社、小口だけど関係が良いのがD社、E社...という感じです。",
                "context": "顧客セグメンテーション"
            },
            {
                "phase": "アクションプラン",
                "user_response": "月1回の定期訪問と、担当者との個人的な会話を増やす...でしょうか？",
                "context": "具体的なアプローチ方法"
            },
            {
                "phase": "アクションプラン",
                "user_response": "来月までに、B社、C社それぞれに2回ずつ訪問して、担当者の趣味や関心事を3つずつ把握する...とか？",
                "context": "SMART目標の設定"
            },
            {
                "phase": "アクションプラン",
                "user_response": "B社、C社からそれぞれ10%の売上アップを目指したいです。",
                "context": "売上目標の設定"
            },
            {
                "phase": "実行支援",
                "user_response": "時間の確保が一番の課題です。あと、どんな話題を振ればいいか分からない時もあります。",
                "context": "想定される課題"
            },
            {
                "phase": "実行支援",
                "user_response": "それなら実行できそうです！",
                "context": "解決策への反応"
            }
        ]
        
        for dialogue in scenario_dialogues:
            self.print_scenario_context(f"【{dialogue['phase']}フェーズ】{dialogue['context']}")
            self.print_user_message(dialogue["user_response"])
            
            # 対話を処理
            result = await self.process_dialogue(dialogue["user_response"])
            if not result:
                break
            
            # 結果を表示
            if result["type"] == "question":
                self.print_ai_message(
                    result["message"],
                    {
                        "purpose": result.get("purpose"),
                        "progress": result.get("progress")
                    }
                )
            elif result["type"] == "summary":
                self.print_separator("=")
                print("🎉 アクションプラン完成！")
                self.print_separator("-")
                self.print_ai_message(result["message"])
                
                # アクションプランを表示
                if result.get("action_plan"):
                    self.display_action_plan(result["action_plan"])
                
                # 洞察を表示
                if result.get("insights"):
                    self.display_insights(result["insights"])
                break
            
            # 少し間を置く（デモ効果）
            await asyncio.sleep(1)
        
        self.print_separator()
        print("✅ 理想的な対話シナリオの実演が完了しました！")
    
    def display_action_plan(self, action_plan: Dict[str, Any]):
        """アクションプランを表示"""
        print("\n📋 アクションプラン:")
        print("-" * 40)
        
        # 短期目標
        if "short_term_goals" in action_plan:
            print("\n【短期目標（1ヶ月）】")
            for goal in action_plan["short_term_goals"]:
                print(f"• {goal.get('goal', '')}")
                if goal.get("actions"):
                    for action in goal["actions"]:
                        print(f"  - {action}")
                print(f"  期限: {goal.get('deadline', '')}")
                print(f"  測定指標: {goal.get('metrics', '')}")
        
        # 中期目標
        if "mid_term_goals" in action_plan:
            print("\n【中期目標（3ヶ月）】")
            for goal in action_plan["mid_term_goals"]:
                print(f"• {goal.get('goal', '')}")
        
        # 課題と解決策
        if "challenges_and_solutions" in action_plan:
            print("\n【想定される課題と解決策】")
            for item in action_plan["challenges_and_solutions"]:
                print(f"• 課題: {item.get('challenge', '')}")
                print(f"  解決策: {item.get('solution', '')}")
        
        # 進捗確認
        if "progress_check" in action_plan:
            print("\n【進捗確認】")
            print(f"• 週次: {action_plan['progress_check'].get('weekly', '')}")
            print(f"• 月次: {action_plan['progress_check'].get('monthly', '')}")
    
    def display_insights(self, insights: Dict[str, Any]):
        """洞察を表示"""
        print("\n💡 洞察:")
        print("-" * 40)
        
        if "strengths" in insights:
            print("\n【発見された強み】")
            for strength in insights["strengths"]:
                print(f"• {strength}")
        
        if "growth_areas" in insights:
            print("\n【成長の機会】")
            for area in insights["growth_areas"]:
                print(f"• {area}")
        
        if "confidence_level" in insights:
            print(f"\n【自信度の変化】")
            print(f"• {insights['confidence_level']}")
    
    async def cleanup(self):
        """クリーンアップ"""
        await self.client.aclose()


async def main():
    """メイン関数"""
    demo = IdealScenarioDemo()
    
    try:
        await demo.run_scenario()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    print("理想的な対話シナリオの実演デモを開始します...")
    print("FastAPIサーバーが http://localhost:8000 で実行されていることを確認してください。\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nデモを中断しました。")
    except Exception as e:
        print(f"\n❌ 実行エラー: {e}")
        print("\nサーバーが起動しているか確認してください：")
        print("cd backend && uvicorn app.main:app --reload")