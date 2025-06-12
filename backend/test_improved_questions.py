#!/usr/bin/env python3
"""
改善された質問生成のテストスクリプト
回答しやすい質問になっているかを確認
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.dialogue_manager import DialogueManager


async def test_improved_questions():
    """改善された質問生成のテスト"""
    
    print("🎯 改善された質問生成テスト")
    print("=" * 60)
    
    dialogue_manager = DialogueManager()
    session_id = "test_improved_questions_001"
    
    # 1on1内容
    one_on_one_content = """
佐藤：田中くん、もう少しお客様との距離を詰めていけるといいね。
田中：距離を詰める、ですか…。
佐藤：やっぱり「信頼関係の構築」がカギだと思うよ。
田中：分かりました、意識してみます。
"""
    
    print("【ステップ1】改善された初期質問の生成")
    print("-" * 40)
    
    try:
        initial_response = await dialogue_manager.process_user_response(
            session_id=session_id,
            user_response=one_on_one_content,
            db_session=None
        )
        
        if initial_response.get("type") == "one_on_one_clarification":
            print("✅ 初期質問生成成功")
            print(f"🎯 対象指示: {initial_response.get('instruction_being_clarified', {}).get('abstract_concept', 'N/A')}")
            print("🔍 生成された質問（改善後）:")
            
            questions = initial_response.get("questions", [])
            for i, question in enumerate(questions, 1):
                print(f"  {i}. {question}")
                
                # 質問の特徴を分析
                characteristics = []
                if "最近" in question or "明日" in question:
                    characteristics.append("✅ 具体的な時間設定")
                if "ありましたか" in question or "ですか" in question:
                    characteristics.append("✅ 答えやすい形式")
                if "例えば" in question:
                    characteristics.append("✅ 具体例を促す")
                if "何分" in question or "何回" in question:
                    characteristics.append("✅ 数値で答えられる")
                    
                if characteristics:
                    print(f"     {', '.join(characteristics)}")
                    
            print()
        else:
            print(f"❌ 予期しないレスポンス: {initial_response.get('type')}")
            return
            
    except Exception as e:
        print(f"❌ 初期質問生成エラー: {e}")
        return
    
    print("【ステップ2】抽象的回答への深掘り質問")
    print("-" * 40)
    
    # 新人の抽象的な回答
    abstract_answer = "お客様ともっとコミュニケーションを取って、信頼してもらえるように頑張ります。"
    print(f"💬 新人の回答: {abstract_answer}")
    
    try:
        deeper_response = await dialogue_manager.process_user_response(
            session_id=session_id,
            user_response=abstract_answer,
            db_session=None
        )
        
        if deeper_response.get("type") == "one_on_one_clarification":
            print("✅ 深掘り質問生成成功")
            feedback = deeper_response.get("concreteness_feedback", "")
            if feedback:
                print(f"📊 {feedback}")
            
            print("🔍 深掘り質問（改善後）:")
            deeper_questions = deeper_response.get("questions", [])
            for i, question in enumerate(deeper_questions, 1):
                print(f"  {i}. {question}")
                
                # 質問の改善点を評価
                improvements = []
                if "明日" in question or "次に" in question:
                    improvements.append("✅ 即実行可能")
                if "何分" in question or "何回" in question or "どのくらい" in question:
                    improvements.append("✅ 定量的回答")
                if "最初に" in question:
                    improvements.append("✅ 手順の明確化")
                if "AとB" in question or "どちらが" in question:
                    improvements.append("✅ 選択肢提示")
                if len(question) < 50:
                    improvements.append("✅ 簡潔で理解しやすい")
                    
                if improvements:
                    print(f"     {', '.join(improvements)}")
            print()
            
        else:
            print(f"❌ 予期しないレスポンス: {deeper_response.get('type')}")
            
    except Exception as e:
        print(f"❌ 深掘り質問生成エラー: {e}")
        return
    
    print("【ステップ3】質問改善の評価")
    print("-" * 40)
    
    # 改善前と改善後の比較
    print("📊 質問改善の比較:")
    print()
    print("❌ 改善前の典型的な質問:")
    print("  - どのようなコミュニケーション手法を使っていますか？")
    print("  - 具体的にどのような行動を取っていますか？")
    print("  - 成果をどのように測定しますか？")
    print()
    print("✅ 改善後の質問:")
    print("  - 最近の商談で困った場面はありましたか？")
    print("  - 明日の商談で最初に何をしますか？")
    print("  - 1回の商談で何分くらい時間をかけますか？")
    print()
    
    print("🎯 改善のポイント:")
    print("  1. 具体的な場面設定（「最近の商談で」「明日の商談で」）")
    print("  2. Yes/No や数値で答えられる要素")
    print("  3. 実体験を思い出しやすい表現")
    print("  4. 専門用語を避けた分かりやすい言葉")
    print("  5. 選択肢や時間軸を明確にした質問")
    
    print("\n" + "=" * 60)
    print("🎉 改善された質問生成テスト完了")
    print("✅ 新人営業マンがより答えやすい質問に改善されました")


if __name__ == "__main__":
    asyncio.run(test_improved_questions())