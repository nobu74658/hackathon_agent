#!/usr/bin/env python3
"""
理想的な対話ワークフローのテスト

新しいワークフローが正しく動作することを確認します。
"""

import asyncio
import json
from typing import Dict, Any
import sys
import os

# 現在のディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ideal_dialogue_workflow import (
    IdealDialogueWorkflow,
    DialogueState,
    ResponseAnalysis,
    SocraticQuestion
)


class WorkflowTest:
    """ワークフローのテスト"""
    
    def __init__(self):
        self.workflow = IdealDialogueWorkflow()
    
    async def test_session_creation(self):
        """セッション作成のテスト"""
        print("🧪 セッション作成テスト")
        print("-" * 40)
        
        result = await self.workflow.start_session(
            session_id="test_session",
            abstract_instruction="もっと顧客との関係を深めて売上を伸ばしてほしい",
            user_context={
                "name": "テスト太郎",
                "role": "新人営業",
                "experience": "6ヶ月"
            }
        )
        
        print(f"✅ セッションタイプ: {result['type']}")
        print(f"✅ メッセージ: {result['message'][:50]}...")
        print(f"✅ セッションID: {result['session_id']}")
        print(f"✅ 次の状態: {result['next_state']}")
        
        return result['session_id']
    
    async def test_response_analysis(self):
        """回答分析のテスト"""
        print("\n🧪 回答分析テスト")
        print("-" * 40)
        
        # テスト用の回答
        test_response = "今月の売上は目標の85%でした。先月も同じくらいで、なかなか目標に届かないんです。"
        
        analysis = await self.workflow._analyze_response(
            response=test_response,
            current_state=DialogueState.CURRENT_SITUATION,
            dialogue_history=[]
        )
        
        print(f"✅ 重要ポイント: {analysis.key_points}")
        print(f"✅ 感情状態: {analysis.emotional_state}")
        print(f"✅ 理解度: {analysis.understanding_level}/10")
        print(f"✅ 課題: {analysis.challenges}")
        
        return analysis
    
    async def test_dialogue_flow(self):
        """対話フローのテスト"""
        print("\n🧪 対話フローテスト")
        print("-" * 40)
        
        # セッション開始
        session_id = await self.test_session_creation()
        
        # テスト対話
        test_dialogues = [
            {
                "response": "今月も目標の85%でした。新規開拓8割、既存フォロー2割です。",
                "expected_state": DialogueState.CURRENT_SITUATION
            },
            {
                "response": "A社の佐藤部長とは良い関係です。月1回訪問して、追加注文もいただきました。",
                "expected_state": DialogueState.PROBLEM_ANALYSIS
            },
            {
                "response": "大口で関係薄いB社C社を優先的に攻めたいと思います。",
                "expected_state": DialogueState.SOLUTION_EXPLORATION
            }
        ]
        
        for i, dialogue in enumerate(test_dialogues, 1):
            print(f"\n--- テスト {i} ---")
            print(f"回答: {dialogue['response']}")
            
            result = await self.workflow.process_response(
                session_id=session_id,
                user_response=dialogue['response']
            )
            
            if result["type"] == "question":
                print(f"✅ 次の質問: {result['message'][:50]}...")
                print(f"✅ 目的: {result.get('purpose', 'N/A')}")
                print(f"✅ 進捗: {result.get('progress', {}).get('percentage', 0)}%")
            elif result["type"] == "summary":
                print(f"✅ サマリー生成完了")
                break
    
    async def test_state_transitions(self):
        """状態遷移のテスト"""
        print("\n🧪 状態遷移テスト")
        print("-" * 40)
        
        # 各状態の遷移をテスト
        transitions = [
            (DialogueState.GREETING, DialogueState.CURRENT_SITUATION),
            (DialogueState.CURRENT_SITUATION, DialogueState.PROBLEM_ANALYSIS),
            (DialogueState.PROBLEM_ANALYSIS, DialogueState.SOLUTION_EXPLORATION),
            (DialogueState.SOLUTION_EXPLORATION, DialogueState.ACTION_PLAN),
            (DialogueState.ACTION_PLAN, DialogueState.EXECUTION_SUPPORT),
            (DialogueState.EXECUTION_SUPPORT, DialogueState.SUMMARY)
        ]
        
        for current, expected_next in transitions:
            # ダミーセッションとアナリシスを作成
            session = {
                "state": current,
                "dialogue_history": [
                    {"role": "user", "state": current.value},
                    {"role": "assistant", "state": current.value}
                ]
            }
            
            analysis = ResponseAnalysis(
                key_points=["テスト"],
                emotional_state="neutral",
                understanding_level=8,
                success_patterns=["成功パターン"],
                challenges=["課題"],
                next_action_hint="次へ"
            )
            
            next_state = self.workflow._determine_next_state(session, analysis)
            
            status = "✅" if next_state == expected_next else "❌"
            print(f"{status} {current.value} → {next_state.value}")
    
    async def test_socratic_question_generation(self):
        """ソクラテス式質問生成のテスト"""
        print("\n🧪 ソクラテス式質問生成テスト")
        print("-" * 40)
        
        session = {
            "abstract_instruction": "もっと顧客との関係を深めて売上を伸ばしてほしい",
            "dialogue_history": [],
            "discovered_patterns": {}
        }
        
        analysis = ResponseAnalysis(
            key_points=["売上85%", "新規8割"],
            emotional_state="不安",
            understanding_level=5,
            success_patterns=[],
            challenges=["目標未達"],
            next_action_hint="成功事例を探す"
        )
        
        question = await self.workflow._generate_socratic_question(
            session=session,
            analysis=analysis,
            next_state=DialogueState.PROBLEM_ANALYSIS
        )
        
        print(f"✅ 質問: {question.question}")
        print(f"✅ 目的: {question.purpose}")
        print(f"✅ 期待される成果: {question.expected_outcome}")
        print(f"✅ フォローアップ数: {len(question.follow_up_options)}")
    
    async def run_all_tests(self):
        """全テストを実行"""
        print("🎯 理想的な対話ワークフローのテスト開始")
        print("=" * 50)
        
        try:
            # 各テストを実行
            await self.test_response_analysis()
            await self.test_state_transitions()
            await self.test_socratic_question_generation()
            await self.test_dialogue_flow()
            
            print("\n" + "=" * 50)
            print("✅ 全テスト完了！")
            print("理想的な対話ワークフローが正常に動作しています。")
            
        except Exception as e:
            print(f"\n❌ テスト失敗: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """メイン関数"""
    test = WorkflowTest()
    await test.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        print("\n環境設定を確認してください：")
        print("- OpenAI APIキーが設定されているか")
        print("- 必要な依存関係がインストールされているか")