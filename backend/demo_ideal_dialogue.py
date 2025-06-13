#!/usr/bin/env python3
"""
理想的な対話シナリオのAPIデモ

理想的な対話フローをAPIエンドポイント経由で体験できるデモです。
"""

import asyncio
import json
from typing import Dict, Any, List
import sys
import os

# 現在のディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.dialogue_manager import DialogueManager


class ApiIdealDialogueDemo:
    """APIベースの理想的な対話デモ"""
    
    def __init__(self):
        self.dialogue_manager = DialogueManager()
        self.session_id = "ideal_demo_session"
        
    async def run_demo(self):
        """デモの実行"""
        await self.dialogue_manager.initialize()
        
        print("🎯 理想的な対話シナリオ - APIデモ")
        print("="*60)
        
        # 上司の抽象的な指示
        abstract_instruction = "もっと顧客との関係を深めて売上を伸ばしてほしい"
        
        print(f"📋 上司の指示: 「{abstract_instruction}」")
        print("\nこの抽象的な指示を、具体的なアクションプランに変換していきます。")
        print("="*60)
        
        # 理想的な対話セッションを開始
        response = await self.dialogue_manager.start_ideal_dialogue(
            session_id=self.session_id,
            abstract_instruction=abstract_instruction,
            context={
                "role": "新人営業担当",
                "experience": "入社6ヶ月",
                "current_challenge": "月次売上目標を2ヶ月連続で下回っている"
            }
        )
        
        print(f"\n🤖 {response.get('phase_description', '')}")
        print(f"質問: {response.get('question', '')}")
        print(f"目的: {response.get('purpose', '')}")
        
        # 対話ループ（効率化により質問数を大幅削減）
        question_count = 0
        max_questions = 7  # デモ用の制限（各フェーズ1質問×5フェーズ＋調整）
        
        while question_count < max_questions:
            question_count += 1
            
            # ユーザーの回答を取得
            print(f"\n--- 質問 {question_count} ---")
            user_response = self.get_demo_response(response, question_count)
            print(f"👤 回答: {user_response}")
            
            # 対話を継続
            response = await self.dialogue_manager.continue_ideal_dialogue(
                session_id=self.session_id,
                user_response=user_response
            )
            
            # レスポンスタイプに応じた処理
            if response.get("type") == "phase_transition":
                print(f"\n✅ {response.get('message', '')}")
                print(f"📋 {response.get('phase_description', '')}")
                
                # 次の質問を取得
                response = await self.dialogue_manager.continue_ideal_dialogue(
                    session_id=self.session_id
                )
            
            if response.get("type") == "action_plan_completed":
                print("\n🎉 アクションプラン完成！")
                self.display_action_plan(response.get("action_plan", {}))
                break
            elif response.get("type") == "socratic_question":
                progress = response.get("progress", {})
                print(f"\n進捗: {progress.get('percentage', 0)}%")
                print(f"🤖 {response.get('phase_description', '')}")
                print(f"質問: {response.get('question', '')}")
                if response.get('purpose'):
                    print(f"目的: {response.get('purpose', '')}")
            elif response.get("type") == "error":
                print(f"❌ エラー: {response.get('message', '')}")
                break
        
        print("\n" + "="*60)
        print("デモ完了！")
    
    def get_demo_response(self, current_question: Dict[str, Any], question_number: int) -> str:
        """デモ用の包括的な回答を生成"""
        # フェーズと質問の内容に基づいて適切な回答を返す
        phase = current_question.get("phase", "")
        
        # 現状把握フェーズの包括的回答例
        if "current_situation" in phase:
            return ("今月の売上は目標の85%で、先月も同じくらいです。時間配分は新規開拓8割、既存フォロー2割です。"
                    "上司から「顧客との関係を深めて売上を伸ばせ」と言われましたが、正直何を具体的にすれば良いのか分からなくて。"
                    "既存顧客との関係はまちまちで、良好な関係の顧客もいればそうでない顧客もいます。")
        
        # 課題分析フェーズの包括的回答例
        elif "problem_analysis" in phase:
            return ("A社の佐藤部長とは特に良好な関係です。月1回必ず訪問し、仕事以外の話もするようになりました。"
                    "理由は、最初の商談で趣味の話で盛り上がったのがきっかけで、その後も雑談を大切にしてきたからです。"
                    "結果として、先月は追加注文をいただき、他部署の課長も紹介してもらえました。"
                    "この成功パターンは、他の顧客でも時間をかければ再現できると思います。")
        
        # ソリューション探索フェーズの包括的回答例
        elif "solution_exploration" in phase:
            return ("顧客を分類すると、大口で関係良好(A社)、大口で関係薄い(B社・C社)、小口で関係良好(D社・E社)、"
                    "小口で関係薄い(その他)という感じです。優先順位は効果の高いB社・C社から始めるべきだと思います。"
                    "具体的には、月1-2回の定期訪問、担当者の趣味や関心事の把握、業界情報の提供などで関係を深めたいです。"
                    "ただし、時間の制約があるので、まずは2社に集中して取り組みます。")
        
        # アクションプラン作成フェーズの包括的回答例
        elif "action_plan" in phase:
            return ("来月までにB社・C社それぞれに2回ずつ訪問し、担当者の趣味・関心事を3つずつ把握します。"
                    "3ヶ月後にはB社・C社からそれぞれ10%の売上アップを目指します。"
                    "測定方法は、月次の売上数値と関係構築の進捗（趣味把握数、雑談時間など）で確認します。"
                    "短期的には関係構築、中長期的には売上向上と新規紹介獲得を目標とします。")
        
        # 実行支援フェーズの包括的回答例
        elif "execution_support" in phase:
            return ("予想される課題は時間確保、話題作り、継続性の維持です。解決策として、"
                    "新規開拓時間の20%を既存フォローに振り分け、事前に業界ニュースをチェックし、"
                    "週次で訪問実績と関係構築状況をセルフチェックします。"
                    "進捗は毎週金曜に振り返り、月末に上司との面談で報告します。"
                    "モチベーション維持のため、小さな成功も記録して自信につなげます。")
        
        else:
            return "はい、理解しました。具体的に進めていきたいと思います。"
    
    def display_action_plan(self, action_plan: Dict[str, Any]):
        """アクションプランを表示"""
        print("\n📋 完成したアクションプラン:")
        print("="*50)
        
        if "summary" in action_plan:
            print(f"概要: {action_plan['summary']}")
        
        if "smart_goals" in action_plan:
            print("\n🎯 SMART目標:")
            for i, goal in enumerate(action_plan["smart_goals"], 1):
                print(f"  {i}. {goal.get('goal', '')}")
                print(f"     測定指標: {goal.get('measurable', '')}")
                print(f"     期限: {goal.get('time_bound', '')}")
        
        if "action_steps" in action_plan:
            print("\n📝 実行ステップ:")
            for i, step in enumerate(action_plan["action_steps"], 1):
                print(f"  {i}. {step.get('action', '')}")
                print(f"     期限: {step.get('deadline', '')}")
        
        if "success_metrics" in action_plan:
            metrics = action_plan["success_metrics"]
            print("\n📊 成功指標:")
            if "quantitative" in metrics:
                print(f"  定量的: {', '.join(metrics['quantitative'])}")
            if "qualitative" in metrics:
                print(f"  定性的: {', '.join(metrics['qualitative'])}")
        
        if "potential_obstacles" in action_plan:
            print("\n⚠️ 予想される課題と対策:")
            for i, obstacle in enumerate(action_plan["potential_obstacles"], 1):
                print(f"  {i}. 課題: {obstacle.get('obstacle', '')}")
                print(f"     対策: {obstacle.get('solution', '')}")
        
        if "continuous_improvement" in action_plan:
            improvement = action_plan["continuous_improvement"]
            print("\n🔄 継続的改善:")
            print(f"  週次チェック: {improvement.get('weekly_check', '')}")
            print(f"  月次レビュー: {improvement.get('monthly_review', '')}")
            print(f"  四半期目標: {improvement.get('quarterly_goal', '')}")


async def main():
    """メイン関数"""
    demo = ApiIdealDialogueDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("理想的な対話シナリオ - APIデモを開始します...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nデモを終了しました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        print("環境設定を確認してください。")