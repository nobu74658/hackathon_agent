#!/usr/bin/env python3
"""
新しい1on1分析システムのテストスクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.dialogue_manager import DialogueManager
from app.services.one_on_one_analyzer import OneOnOneAnalyzer


async def test_new_one_on_one_system():
    """新しい1on1分析システムのテスト"""
    
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
    
    print("🎯 新しい1on1分析システムテスト")
    print("=" * 60)
    
    # テスト1: 1on1判定機能
    print("【テスト1】1on1内容の判定")
    print("-" * 40)
    
    dialogue_manager = DialogueManager()
    is_one_on_one = dialogue_manager._is_one_on_one_content(one_on_one_content)
    print(f"✅ 1on1判定結果: {is_one_on_one}")
    
    # 判定指標の詳細
    indicators = [
        ("対話形式", "：" in one_on_one_content and one_on_one_content.count("：") >= 2),
        ("距離を詰める", "距離を詰める" in one_on_one_content),
        ("信頼関係", "信頼関係" in one_on_one_content), 
        ("温度感", "温度感" in one_on_one_content),
        ("課題に寄り添った", "課題に寄り添った" in one_on_one_content),
        ("長文", len(one_on_one_content) > 100)
    ]
    
    print("判定指標の詳細:")
    for name, result in indicators:
        print(f"  - {name}: {'✅' if result else '❌'}")
    
    # テスト2: アナライザー単体テスト
    print("\n" + "=" * 60)
    print("【テスト2】OneOnOneAnalyzer単体テスト")
    print("-" * 40)
    
    analyzer = OneOnOneAnalyzer()
    
    try:
        analysis_result = await analyzer.analyze_and_generate_summary(
            one_on_one_content=one_on_one_content,
            user_id="test_user_001",
            db_session=None
        )
        
        print("✅ アナライザー実行成功")
        print(f"📋 特定された指示数: {len(analysis_result.get('supervisor_instructions', []))}")
        
        # 特定された指示を表示
        for i, instruction in enumerate(analysis_result.get('supervisor_instructions', []), 1):
            print(f"  {i}. {instruction.get('abstract_concept', '')}")
        
        print(f"🎯 具体化されたプラン数: {len(analysis_result.get('concrete_plans', []))}")
        print(f"📚 ナレッジ活用: {analysis_result.get('knowledge_used', False)}")
        
        # 最終サマリーの概要
        final_summary = analysis_result.get('final_summary', {})
        priority_actions = final_summary.get('priority_actions', [])
        print(f"🚀 優先アクション数: {len(priority_actions)}")
        
        if priority_actions:
            print("主要アクション:")
            for i, action in enumerate(priority_actions[:2], 1):
                print(f"  {i}. {action.get('action', '')}")
        
    except Exception as e:
        print(f"❌ アナライザーエラー: {e}")
        import traceback
        traceback.print_exc()
    
    # テスト3: DialogueManager統合テスト
    print("\n" + "=" * 60)
    print("【テスト3】DialogueManager統合テスト")
    print("-" * 40)
    
    try:
        response = await dialogue_manager.process_user_response(
            session_id="slack_test_user_001",
            user_response=one_on_one_content,
            db_session=None
        )
        
        print(f"✅ DialogueManager応答成功")
        print(f"📝 応答タイプ: {response.get('type')}")
        print(f"🎯 分析方法: {response.get('analysis_method', 'N/A')}")
        
        if response.get('type') == 'one_on_one_analysis':
            print("🎉 新しい1on1分析が正常に実行されました！")
            
            # データ構造の確認
            data = response.get('data', {})
            final_summary = data.get('final_summary', {})
            
            print(f"📊 最終サマリー要素:")
            for key in final_summary.keys():
                print(f"  - {key}")
                
        else:
            print(f"⚠️ 予期しない応答タイプ: {response.get('type')}")
            
    except Exception as e:
        print(f"❌ DialogueManager統合エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # テスト4: 非1on1コンテンツのテスト
    print("\n" + "=" * 60)
    print("【テスト4】非1on1コンテンツのテスト")
    print("-" * 40)
    
    simple_question = "新規開拓で困っています。どうすればいいですか？"
    
    is_simple_one_on_one = dialogue_manager._is_one_on_one_content(simple_question)
    print(f"✅ 簡単な質問の1on1判定: {is_simple_one_on_one}")
    
    simple_response = await dialogue_manager.process_user_response(
        session_id="slack_test_user_002",
        user_response=simple_question,
        db_session=None
    )
    
    print(f"📝 簡単な質問の応答タイプ: {simple_response.get('type')}")
    
    print("\n" + "=" * 60)
    print("🎉 新しい1on1分析システムのテスト完了")
    
    if response.get('type') == 'one_on_one_analysis' and not is_simple_one_on_one:
        print("✅ システムが期待通りに動作しています！")
        print("  - 1on1コンテンツは適切に分析される")
        print("  - 非1on1コンテンツは従来の対話フローを使用")
    else:
        print("⚠️ システムの動作を確認してください")


if __name__ == "__main__":
    asyncio.run(test_new_one_on_one_system())