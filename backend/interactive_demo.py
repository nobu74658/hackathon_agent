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
            "効率的な対話を通じて、この指示を具体的で実行可能なアクションプランに変えていきましょう。\n"
            "各段階で包括的な質問をしますので、詳しく教えてください。"
        )
        
        input("続行するにはEnterキーを押してください...")\n        self.print_separator()
    
    async def current_situation_phase(self):
        """現状把握フェーズ（効率化版）"""
        self.print_ai_message(
            "まず現在の状況を包括的に教えてください。\n\n"
            "以下について詳しく聞かせてください：\n"
            "1. 今月・先月の売上状況と目標達成度\n"
            "2. 現在の時間配分（新規開拓 vs 既存顧客フォロー）\n"
            "3. 既存顧客との関係の現状（良好な顧客、そうでない顧客）\n"
            "4. 上司の「顧客との関係を深める」という指示に対するあなたの理解\n\n"
            "これらをまとめて教えてください。"
        )
        
        response = self.get_user_input("現状の包括的な説明")
        self.user_responses.append({"phase": "current_situation", "question": "現状把握", "answer": response})
        
        self.print_separator()
    
    async def problem_analysis_phase(self):
        """課題分析フェーズ（効率化版）"""
        self.print_ai_message(
            "抽象的な指示を具体的に理解するため、成功体験を分析しましょう。\n\n"
            "以下について詳しく教えてください：\n"
            "1. 最も良好な関係を築けている顧客は？\n"
            "2. その顧客とうまくいっている理由は何だと思いますか？\n"
            "3. その良好な関係から生まれた具体的な成果（売上、紹介など）\n"
            "4. この成功パターンを他の顧客にも応用できるとお考えですか？\n\n"
            "成功事例を包括的に分析して教えてください。"
        )
        
        response = self.get_user_input("成功事例の包括的な分析")
        self.user_responses.append({"phase": "problem_analysis", "question": "成功体験分析", "answer": response})
        
        self.print_separator()
    
    async def solution_exploration_phase(self):
        """ソリューション探索フェーズ（効率化版）"""
        self.print_ai_message(
            "成功体験を他の顧客に効率的に応用する戦略を立てましょう。\n\n"
            "以下について戦略的に考えて教えてください：\n"
            "1. 顧客を「売上規模」と「関係の深さ」で分類するとどうなりますか？\n"
            "2. その中で最も効果的にアプローチすべき優先順位は？\n"
            "3. 優先度の高い顧客に対する具体的な関係構築方法は？\n"
            "4. 時間やリソースの制約を考慮した現実的な計画は？\n\n"
            "戦略的なアプローチ計画を包括的に教えてください。"
        )
        
        response = self.get_user_input("戦略的アプローチ計画")
        self.user_responses.append({"phase": "solution_exploration", "question": "戦略設計", "answer": response})
        
        self.print_separator()
    
    async def action_plan_phase(self):
        """アクションプラン作成フェーズ（効率化版）"""
        self.print_ai_message(
            "戦略を具体的で測定可能なアクションプランに落とし込みましょう。\n\n"
            "SMART目標として以下を設定してください：\n"
            "1. 具体的なアクション内容（何を、誰に、どのように）\n"
            "2. 実行期限（短期・中期の目標設定）\n"
            "3. 成功の測定方法（定量的・定性的指標）\n"
            "4. 期待される成果（売上向上、関係改善など）\n"
            "5. 実行可能性の確認（リソース、時間の妥当性）\n\n"
            "包括的なSMART目標を設定してください。"
        )
        
        response = self.get_user_input("SMART目標の包括的設定")
        self.user_responses.append({"phase": "action_plan", "question": "SMART目標設定", "answer": response})
        
        self.print_separator()
    
    async def execution_support_phase(self):
        """実行支援フェーズ（効率化版）"""
        self.print_ai_message(
            "計画を確実に実行し、継続するための仕組みを作りましょう。\n\n"
            "実行成功のために以下について考えて教えてください：\n"
            "1. 予想される障害や課題（時間、スキル、モチベーションなど）\n"
            "2. それぞれの課題に対する具体的な解決策\n"
            "3. 継続するための仕組み（習慣化、動機維持の方法）\n"
            "4. 進捗確認の方法（週次・月次のチェックポイント）\n"
            "5. 計画修正のタイミングとトリガー\n\n"
            "実行を成功させる包括的な支援策を教えてください。"
        )
        
        response = self.get_user_input("実行支援の包括的計画")
        self.user_responses.append({"phase": "execution_support", "question": "実行支援計画", "answer": response})
        
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
            "効率的な対話を通じて、以下を短時間で達成できました：\n"
            "✅ 現状を包括的に把握\n"
            "✅ 成功パターンを発見・分析\n"
            "✅ 戦略的なアプローチ方法を設計\n"
            "✅ SMART目標と具体的なアクションプランを設定\n"
            "✅ 実行支援の仕組みを構築\n\n"
            "わずか5つの包括的な質問で、上司の抽象的な指示が\n"
            "実行可能なアクションプランに変換されました！\n\n"
            "このプロセスにより、効率的に問題解決スキルが向上し、\n"
            "自立的な思考力が身につきます。"
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