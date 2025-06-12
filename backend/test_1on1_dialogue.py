#!/usr/bin/env python3
"""
1on1対話フローのテストスクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.dialogue_manager import DialogueManager


async def test_1on1_dialogue_flow():
    """1on1対話フローの段階的テスト"""
    
    # 実際の1on1ログ
    initial_message = """
佐藤：田中くん、最近の営業活動の調子はどう？

田中：はい、今週は5件の新規アポを獲得できました。ただ、成約にはまだ至っていなくて…。

佐藤：なるほどね。悪くはないけど、もう少しお客様との距離を詰めていけるといいね。

田中：距離を詰める、ですか…。例えばどういうことを意識すればよいでしょうか？

佐藤：うーん、やっぱり「信頼関係の構築」がカギだと思うよ。お客様が安心して話せるような雰囲気づくりとか、ね。

田中：なるほど…。雰囲気づくりというのは、雑談を増やすとかでしょうか？

佐藤：まあ、それもあるし、相手に合わせたトーンとか話し方とかもあるよね。全体的なバランスっていうのかな。

田中：（…具体的にどう改善すればいいのか分からないな）分かりました、意識してみます。
"""
    
    print("🎭 1on1対話フローテスト開始")
    print("=" * 60)
    
    dialogue_manager = DialogueManager()
    session_id = "test_1on1_session"
    
    # 第1段階：初期入力
    print("【第1段階】初期1on1ログの入力")
    print("-" * 40)
    
    response1 = await dialogue_manager.process_user_response(
        session_id=session_id,
        user_response=initial_message,
        db_session=None
    )
    
    print(f"応答タイプ: {response1['type']}")
    print(f"段階: {response1.get('stage', 'N/A')}")
    print(f"段階説明: {response1.get('stage_description', 'N/A')}")
    print(f"完了度: {response1.get('completeness_score', 'N/A')}%")
    print("\n生成された質問:")
    for i, q in enumerate(response1.get('questions', []), 1):
        print(f"  {i}. {q}")
    
    # 第2段階：ユーザーの回答をシミュレート
    print("\n" + "=" * 60)
    print("【第2段階】ユーザーの回答（具体的な事例）")
    print("-" * 40)
    
    user_response_2 = """
先週、大手企業の担当者との商談がありました。資料の説明は一通りできたのですが、相手の方がとても静かで、「検討させていただきます」と言われて終わりました。

何か質問はないか聞いたのですが、「特にありません」と言われて...。
その時は相手が忙しそうだったので、あまり深く聞けませんでした。

他の案件でも似たようなことがあって、相手が本当に興味があるのか分からない時があります。
"""
    
    response2 = await dialogue_manager.process_user_response(
        session_id=session_id,
        user_response=user_response_2,
        db_session=None
    )
    
    print(f"応答タイプ: {response2['type']}")
    print(f"段階: {response2.get('stage', 'N/A')}")
    print(f"段階説明: {response2.get('stage_description', 'N/A')}")
    print(f"完了度: {response2.get('completeness_score', 'N/A')}%")
    print("\n生成された質問:")
    for i, q in enumerate(response2.get('questions', []), 1):
        print(f"  {i}. {q}")
    
    # 第3段階：さらに深い分析
    print("\n" + "=" * 60)
    print("【第3段階】ユーザーの回答（課題の深掘り）")
    print("-" * 40)
    
    user_response_3 = """
そういえば、成功した案件では、最初に相手の現在の課題について詳しく聞いていました。
その時は相手も積極的に話してくれて、「実はこんなことで困っている」と具体的に教えてくれました。

でも、うまくいかない商談では、ヒアリングが浅くて、相手の本当の課題が分からないまま提案してしまっているかもしれません。

どうやって相手の本音を引き出せばいいのか、具体的な質問の仕方を知りたいです。
"""
    
    response3 = await dialogue_manager.process_user_response(
        session_id=session_id,
        user_response=user_response_3,
        db_session=None
    )
    
    print(f"応答タイプ: {response3['type']}")
    print(f"段階: {response3.get('stage', 'N/A')}")
    print(f"段階説明: {response3.get('stage_description', 'N/A')}")
    print(f"完了度: {response3.get('completeness_score', 'N/A')}%")
    print("\n生成された質問:")
    for i, q in enumerate(response3.get('questions', []), 1):
        print(f"  {i}. {q}")
    
    print("\n" + "=" * 60)
    print("🎉 段階的対話フローテスト完了")
    print("📈 完了度の推移:", end=" ")
    print(f"{response1.get('completeness_score', 0)}% → {response2.get('completeness_score', 0)}% → {response3.get('completeness_score', 0)}%")
    print("🎯 段階の推移:", end=" ")
    print(f"{response1.get('stage', '')} → {response2.get('stage', '')} → {response3.get('stage', '')}")


if __name__ == "__main__":
    asyncio.run(test_1on1_dialogue_flow())