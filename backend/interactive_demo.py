#!/usr/bin/env python3
"""
理想的な対話シナリオを再現するインタラクティブなデモ

このデモは、上司の抽象的な指示を具体的なアクションプランに変換する
理想的な対話フローを体験できるよう設計されています。
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# 現在のディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.dialogue_manager import DialogueManager


class InteractiveDemo:
    """インタラクティブなデモクラス"""
    
    def __init__(self):
        self.dialogue_manager = DialogueManager()
        self.session_id = "demo_session"
        self.stage = "intro"
        self.user_responses = []
        
    def print_separator(self):
        """セパレーターを表示"""
        print("\n" + "="*60 + "\n")
    
    def print_ai_message(self, message: str):
        """AIメッセージの表示"""
        print(f"🤖 AI Agent: {message}\n")
    
    def print_scenario_info(self, info: str):
        """シナリオ情報の表示"""
        print(f"📋 シナリオ: {info}\n")
        
    def get_user_input(self, prompt: str = "あなたの回答") -> str:
        """ユーザー入力の取得"""
        while True:
            try:
                user_input = input(f"👤 {prompt}: ").strip()
                if user_input:
                    return user_input
                print("入力が空です。何か入力してください。")
            except KeyboardInterrupt:
                print("\n\nデモを終了します。")
                sys.exit(0)
    
    async def run_demo(self):
        """デモの実行"""
        await self.dialogue_manager.initialize()
        
        self.print_separator()
        print("🎯 Sales Growth AI Agent - 理想的な対話シナリオ デモ")
        self.print_separator()
        
        # イントロダクション
        await self.intro_phase()
        
        # フェーズ1: 現状把握
        await self.current_situation_phase()
        
        # フェーズ2: 課題分析
        await self.problem_analysis_phase()
        
        # フェーズ3: ソリューション探索
        await self.solution_exploration_phase()
        
        # フェーズ4: アクションプラン作成
        await self.action_plan_phase()
        
        # フェーズ5: 実行支援
        await self.execution_support_phase()
        
        # 総括
        await self.conclusion_phase()
    
    async def intro_phase(self):
        """イントロダクション"""
        self.print_scenario_info(
            "新人営業担当の田中さん（入社6ヶ月）として参加してください。\n"
            "上司から「もっと顧客との関係を深めて売上を伸ばしてほしい」という\n"
            "抽象的な指示を受けた状況を想定しています。"
        )
        
        self.print_ai_message(
            "こんにちは田中さん。お疲れ様です。\n\n"
            "上司から「顧客との関係を深めて売上を伸ばしてほしい」という指示があったと\n"
            "お聞きしました。私は営業スキル向上をサポートするAIアシスタントです。\n\n"
            "この指示を具体的で実行可能なアクションプランに変えていきましょう。"
        )
        
        input("続行するにはEnterキーを押してください...")\n        self.print_separator()
    
    async def current_situation_phase(self):
        """現状把握フェーズ"""
        self.print_ai_message(
            "まず現在の状況を教えてください。\n"
            "今月の売上はいかがでしたか？目標は達成できていますか？"
        )
        
        response1 = self.get_user_input("今月の売上状況")
        self.user_responses.append({"phase": "current_situation", "question": "売上状況", "answer": response1})
        
        self.print_ai_message(
            "ありがとうございます。状況を理解しました。\n\n"
            "次に、現在の顧客対応について聞かせてください。\n"
            "既存顧客と新規顧客、それぞれにどのくらい時間を割いていますか？"
        )
        
        response2 = self.get_user_input("時間配分（既存:新規の比率など）")
        self.user_responses.append({"phase": "current_situation", "question": "時間配分", "answer": response2})
        
        self.print_ai_message(
            f"なるほど、{response2}という配分なのですね。\n\n"
            "では、「顧客との関係を深める」という上司の指示について、\n"
            "田中さんはどのように解釈していますか？"
        )
        
        response3 = self.get_user_input("上司の指示への理解")
        self.user_responses.append({"phase": "current_situation", "question": "指示の解釈", "answer": response3})
        
        self.print_separator()
    
    async def problem_analysis_phase(self):
        """課題分析フェーズ"""
        self.print_ai_message(
            "抽象的で分かりにくい指示ですよね。少し具体的に考えてみましょう。\n\n"
            "今の既存顧客との関係で、うまくいっている例はありますか？\n"
            "特に良い関係を築けている顧客があれば教えてください。"
        )
        
        response1 = self.get_user_input("良好な関係の顧客例")
        self.user_responses.append({"phase": "problem_analysis", "question": "成功事例", "answer": response1})
        
        self.print_ai_message(
            f"素晴らしいですね！{response1}との関係がうまくいっているのですね。\n\n"
            "その良い関係の結果、何か具体的な変化や成果はありましたか？\n"
            "売上面でも、それ以外の面でも構いません。"
        )
        
        response2 = self.get_user_input("良好な関係から生まれた成果")
        self.user_responses.append({"phase": "problem_analysis", "question": "関係の成果", "answer": response2})
        
        self.print_ai_message(
            f"それです！{response2}というような成果が生まれたのですね。\n\n"
            "これが上司の言う「関係を深めて売上を伸ばす」の具体例です。\n\n"
            "では、他の顧客でもこのような関係を築くには、\n"
            "どんな行動が必要だと思いますか？"
        )
        
        response3 = self.get_user_input("他の顧客での関係構築方法")
        self.user_responses.append({"phase": "problem_analysis", "question": "関係構築方法", "answer": response3})
        
        self.print_separator()
    
    async def solution_exploration_phase(self):
        """ソリューション探索フェーズ"""
        self.print_ai_message(
            "良い考えですね！ただ、全ての顧客に同じだけ時間をかけるのは\n"
            "現実的ではありませんよね。\n\n"
            "効率的にアプローチするために、顧客をセグメント分けしてみませんか？\n\n"
            "現在の顧客を「売上規模」と「関係の深さ」で分類すると、\n"
            "どのようなグループができそうですか？"
        )
        
        response1 = self.get_user_input("顧客のセグメント分け")
        self.user_responses.append({"phase": "solution_exploration", "question": "顧客セグメント", "answer": response1})
        
        self.print_ai_message(
            f"完璧です！{response1}という分類ですね。\n\n"
            "この中で、最も効果的にアプローチできそうなのは\n"
            "「大口だけど関係が薄い」顧客グループだと思いませんか？\n\n"
            "そのような顧客に対して、具体的にどのような行動を取れば、\n"
            "成功事例と同じような関係を築けると思いますか？"
        )
        
        response2 = self.get_user_input("具体的なアプローチ方法")
        self.user_responses.append({"phase": "solution_exploration", "question": "アプローチ方法", "answer": response2})
        
        self.print_separator()
    
    async def action_plan_phase(self):
        """アクションプラン作成フェーズ"""
        self.print_ai_message(
            "良い方向性ですね！より具体的にしてみましょう。\n\n"
            "いつまでに、どのような結果を目指しますか？\n"
            "測定可能な目標にしてみてください。\n\n"
            "例：「来月までに○○社に○回訪問し、担当者の○○を○個把握する」"
        )
        
        response1 = self.get_user_input("具体的な目標設定")
        self.user_responses.append({"phase": "action_plan", "question": "具体的目標", "answer": response1})
        
        self.print_ai_message(
            f"素晴らしい！「{response1}」は実行可能で測定可能な目標ですね。\n\n"
            "さらに、売上への影響も設定しませんか？\n"
            "3ヶ月後にはどのような売上結果を期待しますか？"
        )
        
        response2 = self.get_user_input("売上目標")
        self.user_responses.append({"phase": "action_plan", "question": "売上目標", "answer": response2})
        
        self.print_ai_message(
            f"完璧です！{response2}という売上目標も設定できました。\n\n"
            "では、この計画を実行するうえで、想定される障害や課題はありますか？\n"
            "それらをどう克服しますか？"
        )
        
        response3 = self.get_user_input("想定される課題と解決策")
        self.user_responses.append({"phase": "action_plan", "question": "課題と解決策", "answer": response3})
        
        self.print_separator()
    
    async def execution_support_phase(self):
        """実行支援フェーズ"""
        self.print_ai_message(
            "課題を事前に特定できて素晴らしいです。\n\n"
            "具体的な解決策を考えましょう。\n"
            "1週間のスケジュールを見直して、どの活動の優先度を下げれば\n"
            "顧客訪問の時間を確保できそうですか？"
        )
        
        response1 = self.get_user_input("時間確保の具体策")
        self.user_responses.append({"phase": "execution_support", "question": "時間確保", "answer": response1})
        
        self.print_ai_message(
            f"それなら実行できそうですね！{response1}という工夫が良いと思います。\n\n"
            "最後に、このアクションプランの進捗をどのように確認しますか？\n"
            "1週間後、2週間後のチェックポイントを設定しましょう。"
        )
        
        response2 = self.get_user_input("進捗確認方法")
        self.user_responses.append({"phase": "execution_support", "question": "進捗確認", "answer": response2})
        
        self.print_separator()
    
    async def conclusion_phase(self):
        """総括フェーズ"""
        self.print_ai_message(
            "素晴らしいです！上司の抽象的な指示を\n"
            "具体的で実行可能なアクションプランに変換できました。\n\n"
            "📋 今日作成したアクションプラン：\n"
        )
        
        # アクションプランの表示
        print("┌─ アクションプラン ─────────────────────┐")
        for i, response in enumerate(self.user_responses[-6:], 1):  # 最後の6つの回答を使用
            print(f"│ {i}. {response['question']}: {response['answer'][:40]}{'...' if len(response['answer']) > 40 else ''}│")
        print("└──────────────────────────────────────────┘\n")
        
        self.print_ai_message(
            "このように、段階的な質問を通じて：\n"
            "✅ 現状を正確に把握\n"
            "✅ 成功パターンを発見\n"
            "✅ 顧客をセグメント分け\n"
            "✅ 具体的で測定可能な目標を設定\n"
            "✅ 障害を予測し解決策を検討\n"
            "✅ 進捗確認方法を決定\n\n"
            "上司の抽象的な指示が、実行可能なアクションプランになりました！\n\n"
            "このプロセスを通じて、田中さんの問題解決スキルも向上していきます。"
        )
        
        self.print_separator()
        print("🎉 デモ完了！お疲れ様でした。")
        print("\nこのような対話を通じて、部下の自立的な成長を支援し、")
        print("抽象的な指示を具体的なアクションに変換するスキルを身につけることができます。")
        self.print_separator()


async def main():
    """メイン関数"""
    demo = InteractiveDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("理想的な対話シナリオ - インタラクティブデモを開始します...")
    print("途中で終了したい場合は Ctrl+C を押してください。\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nデモを終了しました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        print("環境設定を確認してください。")