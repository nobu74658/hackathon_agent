#!/usr/bin/env python3
"""
対話型具体化システムのテストスクリプト
1on1から抽象的指示を特定し、新人営業マンとの対話で段階的に具体化
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.dialogue_manager import DialogueManager


async def test_dialogue_based_concretization():
    """対話型具体化システムのテスト"""
    
    # 実際の1on1ログ
    one_on_one_content = """
佐藤：田中くん、最近の営業活動の調子はどう？

田中：はい、今週は5件の新規アポを獲得できました。ただ、成約にはまだ至っていなくて…。

佐藤：なるほどね。悪くはないけど、もう少しお客様との距離を詰めていけるといいね。

田中：距離を詰める、ですか…。例えばどういうことを意識すればよいでしょうか？

佐藤：うーん、やっぱり「信頼関係の構築」がカギだと思うよ。お客様が安心して話せるような雰囲気づくりとか、ね。

田中：なるほど…。雰囲気づくりというのは、雑談を増やすとかでしょうか？

佐藤：まあ、それもあるし、相手に合わせたトーンとか話し方とかもあるよね。全体的なバランスっていうのかな。

田中：（…具体的にどう改善すればいいのか分からないな）分かりました、意識してみます。

佐藤：うん。あと、もっと「相手の課題に寄り添った提案」をしていけるといいかもね。

田中：はい、ありがとうございます。それって、ヒアリングの内容をもう少し掘り下げる感じですか？

佐藤：そうだね。ただ掘り下げるだけじゃなくて、「相手の温度感を読む」ってのも大事だよ。

田中：（温度感…？どうやって読むんだろう）分かりました。意識してみます。
"""
    
    print("🎯 対話型具体化システムテスト")
    print("=" * 60)
    
    dialogue_manager = DialogueManager()
    session_id = "test_dialogue_session_001"
    
    print("【ステップ1】1on1内容の入力と初期分析")
    print("-" * 40)
    
    # ステップ1: 1on1内容を処理（初期分析と最初の質問生成）
    try:
        initial_response = await dialogue_manager.process_user_response(
            session_id=session_id,
            user_response=one_on_one_content,
            db_session=None
        )
        
        print(f"✅ 初期処理成功")
        print(f"📝 レスポンスタイプ: {initial_response.get('type')}")
        
        if initial_response.get("type") == "one_on_one_clarification":
            print(f"📋 分析された指示数: {initial_response.get('total_instructions', 0)}")
            print(f"🎯 現在の指示: {initial_response.get('instruction_being_clarified', {}).get('abstract_concept', 'N/A')}")
            print(f"📊 進捗: {initial_response.get('current_instruction_index', 0) + 1}/{initial_response.get('total_instructions', 0)}")
            print("🔍 生成された質問:")
            for i, question in enumerate(initial_response.get("questions", []), 1):
                print(f"  {i}. {question}")
        else:
            print(f"⚠️ 予期しないレスポンス: {initial_response}")
            return
            
    except Exception as e:
        print(f"❌ 初期処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ステップ2: 新人営業マンの回答をシミュレート（抽象的な回答）
    print("\n" + "=" * 60)
    print("【ステップ2】新人営業マンの最初の回答（抽象的）")
    print("-" * 40)
    
    abstract_answer = "顧客との距離を詰めるために、もっとコミュニケーションを取るようにしたいと思います。相手の話をよく聞いて、親しみやすい雰囲気を作るように心がけます。"
    
    print(f"💬 新人の回答: {abstract_answer}")
    
    try:
        second_response = await dialogue_manager.process_user_response(
            session_id=session_id,
            user_response=abstract_answer,
            db_session=None
        )
        
        print(f"✅ 回答処理成功")
        print(f"📝 レスポンスタイプ: {second_response.get('type')}")
        
        if second_response.get("type") == "one_on_one_clarification":
            feedback = second_response.get("concreteness_feedback", "")
            missing = second_response.get("missing_aspects", [])
            
            print(f"📊 {feedback}")
            if missing:
                print("🔍 不足している要素:")
                for aspect in missing:
                    print(f"  • {aspect}")
            
            print("🔍 追加の深掘り質問:")
            for i, question in enumerate(second_response.get("questions", []), 1):
                print(f"  {i}. {question}")
        else:
            print(f"⚠️ 予期しないレスポンス: {second_response}")
            
    except Exception as e:
        print(f"❌ 回答処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ステップ3: より具体的な回答をシミュレート
    print("\n" + "=" * 60)
    print("【ステップ3】新人営業マンのより具体的な回答")
    print("-" * 40)
    
    concrete_answer = """商談開始時に必ず3分間の雑談時間を設けます。具体的には：
1. 天気や最近のニュースから話を始める
2. 「最近お忙しいですか？」「業界の状況はいかがですか？」など相手の状況を聞く
3. 相手の話すスピードに合わせて自分のペースも調整する
4. 相手が専門用語を使う場合は同レベルで、使わない場合は分かりやすい言葉で説明する
これを毎回の商談で実行し、商談後に「雑談がうまくいったか」「相手がリラックスできていたか」をメモに記録します。"""
    
    print(f"💬 新人の具体的回答: {concrete_answer}")
    
    try:
        third_response = await dialogue_manager.process_user_response(
            session_id=session_id,
            user_response=concrete_answer,
            db_session=None
        )
        
        print(f"✅ 具体的回答処理成功")
        print(f"📝 レスポンスタイプ: {third_response.get('type')}")
        
        if third_response.get("type") == "one_on_one_clarification":
            # まだ次の指示がある場合
            current_index = third_response.get("current_instruction_index", 0)
            total = third_response.get("total_instructions", 0)
            
            if "previous_instruction_completed" in third_response:
                completed = third_response["previous_instruction_completed"]
                score = third_response.get("concreteness_achieved", 0)
                print(f"✅ 指示「{completed}」が具体化完了 (具体性: {score}%)")
            
            print(f"📊 進捗: {current_index + 1}/{total}")
            print(f"🎯 次の指示: {third_response.get('instruction_being_clarified', {}).get('abstract_concept', 'N/A')}")
            print("🔍 次の指示の質問:")
            for i, question in enumerate(third_response.get("questions", []), 1):
                print(f"  {i}. {question}")
        
        elif third_response.get("type") == "one_on_one_final_plan":
            # 最終アクションプラン生成
            print("🎉 全ての指示が具体化完了！最終アクションプランが生成されました")
            
            data = third_response.get("data", {})
            final_summary = data.get("final_summary", {})
            dialogue_summary = data.get("dialogue_summary", {})
            
            print(f"📊 対話サマリー:")
            print(f"  - 具体化された指示数: {dialogue_summary.get('instructions_clarified', 0)}")
            
            priority_actions = final_summary.get("priority_actions", [])
            print(f"🚀 生成されたアクション数: {len(priority_actions)}")
            
            if priority_actions:
                print("主要アクション:")
                for i, action in enumerate(priority_actions[:2], 1):
                    print(f"  {i}. {action.get('action', '')}")
        
        else:
            print(f"⚠️ 予期しないレスポンス: {third_response}")
            
    except Exception as e:
        print(f"❌ 具体的回答処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("🎉 対話型具体化システムのテスト完了")
    print("✅ 期待される動作:")
    print("  1. 1on1内容から抽象的指示を特定")
    print("  2. 各指示について段階的に深掘り質問")
    print("  3. 回答の具体性を自動判定")
    print("  4. 十分具体的になったら次の指示へ移動")
    print("  5. 全て完了したら最終アクションプラン生成")


if __name__ == "__main__":
    asyncio.run(test_dialogue_based_concretization())