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
        
        # 対話ループ
        question_count = 0
        max_questions = 15  # デモ用の制限
        
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
        """デモ用の回答を生成"""
        # フェーズと質問の内容に基づいて適切な回答を返す
        phase = current_question.get("phase", "")
        question = current_question.get("question", "").lower()
        
        # 現状把握フェーズの回答例
        if "current_situation" in phase:
            responses = [
                "今月の売上は目標の85%でした。先月も同じくらいで、目標に届かない状況が続いています。",
                "新規開拓が8割、既存顧客フォローが2割くらいの時間配分です。",
                "正直、「関係を深める」という指示が抽象的で、具体的に何をすればいいのかよく分からないんです。"
            ]
        
        # 課題分析フェーズの回答例
        elif "problem_analysis" in phase:
            responses = [
                "A社の佐藤部長とは良い関係だと思います。月1回は必ず訪問して、仕事以外の話もするようになりました。",
                "A社からは先月追加注文をいただけました。それに、他部署の課長も紹介してもらえて新しい商談が始まりそうです。",
                "A社と同じように定期的に訪問して信頼関係を築くことだと思います。でも全ての顧客に同じだけ時間をかけるのは無理ですし..."
            ]
        
        # ソリューション探索フェーズの回答例
        elif "solution_exploration" in phase:
            responses = [
                "大口で関係が良いのがA社、大口だけど関係が薄いのがB社とC社、小口だけど関係が良いのがD社、E社という感じです。",
                "「大口だけど関係が薄い」B社、C社から始めるのが効率的だと思います。",
                "月1回の定期訪問と、担当者との個人的な会話を増やすことでしょうか。"
            ]
        
        # アクションプラン作成フェーズの回答例
        elif "action_plan" in phase:
            responses = [
                "来月までに、B社、C社それぞれに2回ずつ訪問して、担当者の趣味や関心事を3つずつ把握したいと思います。",
                "B社、C社からそれぞれ10%の売上アップを3ヶ月後に目指したいです。",
                "時間の確保が一番の課題です。あと、どんな話題を振ればいいか分からない時もあります。"
            ]
        
        # 実行支援フェーズの回答例
        elif "execution_support" in phase:
            responses = [
                "新規開拓の一部の時間を既存顧客フォローに振り分けることで時間を確保できそうです。",
                "週次で訪問回数と関係構築の進捗をチェックし、2週間後に中間レビューを行いたいと思います。"
            ]
        
        else:
            responses = ["はい、理解しました。", "そうですね。", "なるほど、そういうことですね。"]
        
        # 質問番号に基づいて回答を選択
        response_index = (question_number - 1) % len(responses)
        return responses[response_index]
    
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