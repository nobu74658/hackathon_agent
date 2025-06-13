#!/usr/bin/env python3
"""
理想的な対話シナリオ - インタラクティブデモ（新ワークフロー版）

ユーザーが実際に回答を入力しながら、理想的な対話フローを体験できます。
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime
import sys


class IdealInteractiveDemo:
    """理想的な対話のインタラクティブデモ"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def print_separator(self, char: str = "=", length: int = 70):
        """セパレーターを表示"""
        print(f"\n{char * length}\n")
    
    def print_ai_message(self, message: str, metadata: Dict[str, Any] = None):
        """AIメッセージの表示"""
        print(f"🤖 AIコーチ:\n{message}")
        if metadata:
            print(f"\n   📊 進捗: {metadata.get('progress', {}).get('percentage', 0)}%")
            if metadata.get("purpose"):
                print(f"   🎯 目的: {metadata['purpose']}")
        print()
    
    def get_user_input(self, prompt: str = "あなたの回答") -> str:
        """ユーザー入力を取得"""
        while True:
            try:
                user_input = input(f"👤 {prompt}: ").strip()
                if user_input:
                    return user_input
                print("回答を入力してください。")
            except KeyboardInterrupt:
                print("\n\nデモを終了します。")
                sys.exit(0)
    
    def print_intro(self):
        """イントロダクション"""
        self.print_separator()
        print("🎯 理想的な対話シナリオ - インタラクティブデモ")
        self.print_separator()
        
        print("このデモでは、新人営業担当として上司の抽象的な指示を")
        print("具体的なアクションプランに変換する対話を体験できます。\n")
        
        print("📋 シナリオ設定:")
        print("- あなたの役割: 新人営業担当（入社6ヶ月）")
        print("- 上司の指示: 「もっと顧客との関係を深めて売上を伸ばしてほしい」")
        print("- 現状: 月次売上目標を2ヶ月連続で下回っている\n")
        
        print("💡 ヒント:")
        print("- 正直に現状を話してください")
        print("- 成功体験を思い出してみてください")
        print("- 具体的な数字や例を挙げると良いでしょう")
        
        self.print_separator()
        input("準備ができたらEnterキーを押してください...")
    
    async def start_session(self, name: str):
        """セッションを開始"""
        response = await self.client.post(
            f"{self.base_url}/api/ideal-dialogue/start",
            json={
                "abstract_instruction": "もっと顧客との関係を深めて売上を伸ばしてほしい",
                "user_context": {
                    "name": name,
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
    
    def show_progress_bar(self, percentage: int):
        """進捗バーを表示"""
        bar_length = 40
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n進捗: [{bar}] {percentage}%")
    
    def display_phase_info(self, state: str):
        """フェーズ情報を表示"""
        phase_info = {
            "current_situation": "🔍 現状把握 - あなたの状況を理解します",
            "problem_analysis": "💡 課題分析 - 成功パターンを発見します",
            "solution_exploration": "🎯 解決策探索 - 戦略的アプローチを設計します",
            "action_plan": "📝 アクションプラン - 具体的な目標を設定します",
            "execution_support": "🚀 実行支援 - 成功のための仕組みを作ります"
        }
        
        if state in phase_info:
            print(f"\n現在のフェーズ: {phase_info[state]}")
    
    async def run_interactive_session(self):
        """インタラクティブセッションを実行"""
        self.print_intro()
        
        # 名前を取得
        name = self.get_user_input("お名前を教えてください")
        
        # セッション開始
        self.print_separator()
        if not await self.start_session(name):
            return
        
        # 対話ループ
        while True:
            # ユーザーの回答を取得
            user_response = self.get_user_input(f"{name}さんの回答")
            
            # 対話を処理
            result = await self.process_dialogue(user_response)
            if not result:
                break
            
            # 進捗を表示
            if result.get("progress"):
                self.show_progress_bar(result["progress"]["percentage"])
            
            # フェーズ情報を表示
            if result.get("state"):
                self.display_phase_info(result["state"])
            
            # 結果に応じた処理
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
                print("🎉 素晴らしい！アクションプランが完成しました！")
                self.print_separator("-")
                
                self.print_ai_message(result["message"])
                
                # アクションプランを表示
                if result.get("action_plan"):
                    self.display_action_plan(result["action_plan"])
                
                # 洞察を表示
                if result.get("insights"):
                    self.display_insights(result["insights"])
                
                self.print_separator()
                print("✅ 対話セッションが完了しました！")
                print("\nこのアクションプランを実行することで、")
                print("上司の抽象的な指示を具体的な成果につなげることができます。")
                print("\n頑張ってください！応援しています！🎯")
                break
    
    def display_action_plan(self, action_plan: Dict[str, Any]):
        """アクションプランを表示"""
        print("\n📋 あなたのアクションプラン:")
        print("=" * 50)
        
        # 短期目標
        if "short_term_goals" in action_plan:
            print("\n🎯 短期目標（1ヶ月）:")
            for i, goal in enumerate(action_plan["short_term_goals"], 1):
                print(f"\n{i}. {goal.get('goal', '')}")
                if goal.get("actions"):
                    print("   実行項目:")
                    for action in goal["actions"]:
                        print(f"   • {action}")
                print(f"   📅 期限: {goal.get('deadline', '')}")
                print(f"   📊 測定指標: {goal.get('metrics', '')}")
        
        # 中期目標
        if "mid_term_goals" in action_plan:
            print("\n🎯 中期目標（3ヶ月）:")
            for i, goal in enumerate(action_plan["mid_term_goals"], 1):
                print(f"{i}. {goal.get('goal', '')}")
        
        # 成功パターン
        if "success_patterns" in action_plan:
            print("\n✨ 活用すべき成功パターン:")
            for pattern in action_plan["success_patterns"]:
                print(f"• {pattern}")
        
        # 課題と解決策
        if "challenges_and_solutions" in action_plan:
            print("\n⚠️ 想定される課題と解決策:")
            for item in action_plan["challenges_and_solutions"]:
                print(f"\n課題: {item.get('challenge', '')}")
                print(f"→ 解決策: {item.get('solution', '')}")
        
        # 進捗確認
        if "progress_check" in action_plan:
            print("\n📅 進捗確認方法:")
            print(f"• 週次: {action_plan['progress_check'].get('weekly', '')}")
            print(f"• 月次: {action_plan['progress_check'].get('monthly', '')}")
    
    def display_insights(self, insights: Dict[str, Any]):
        """洞察を表示"""
        print("\n💡 発見されたあなたの特徴:")
        print("=" * 50)
        
        if "strengths" in insights:
            print("\n✨ 強み:")
            for strength in insights["strengths"]:
                print(f"• {strength}")
        
        if "growth_areas" in insights:
            print("\n📈 成長の機会:")
            for area in insights["growth_areas"]:
                print(f"• {area}")
        
        if "confidence_level" in insights:
            print(f"\n🎯 自信度の変化:")
            print(f"{insights['confidence_level']}")
    
    async def cleanup(self):
        """クリーンアップ"""
        await self.client.aclose()


async def main():
    """メイン関数"""
    demo = IdealInteractiveDemo()
    
    try:
        await demo.run_interactive_session()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    print("理想的な対話シナリオ - インタラクティブデモ")
    print("\nFastAPIサーバーが http://localhost:8000 で実行されていることを確認してください。")
    print("サーバー起動コマンド: cd backend && uvicorn app.main:app --reload\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nデモを終了しました。")
    except Exception as e:
        print(f"\n❌ 実行エラー: {e}")
        print("\nサーバーが起動しているか確認してください。")