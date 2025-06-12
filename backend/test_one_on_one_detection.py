#!/usr/bin/env python3
"""
1on1判定のテストスクリプト
提案資料の例で1on1判定が正しく動作するかを確認
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.dialogue_manager import DialogueManager


def test_one_on_one_detection():
    """1on1判定のテスト"""
    
    print("🎯 1on1判定テスト - 提案資料の例")
    print("=" * 60)
    
    dialogue_manager = DialogueManager()
    
    # 提案資料の1on1内容
    one_on_one_content = """
**佐藤**：
田中くん、先週出してくれた提案資料、確認したよ。
**田中**：
はい、ありがとうございます。何か気になる点はありましたでしょうか？
**佐藤**：
うーん、全体的には悪くないんだけど、もう少し"伝わる資料"にしていけるといいかな。
**田中**：
伝わる…というのは、内容が分かりにくかったということでしょうか？
**佐藤**：
そういうわけでもないんだけど、なんていうか"もう一歩"なんだよね。お客さんが「なるほど、これなら任せたい」と思えるような仕上がりっていうのかな。
**田中**：
（うーん…曖昧だな）
たとえば、どこをどう変えると良くなると思いますか？
**佐藤**：
そうだなあ、例えば構成とか、デザインとか、言葉の選び方とか…全体的にもっと洗練されると良いよね。
**田中**：
はい…。それは、スライドの見せ方を変える、ということですか？
**佐藤**：
うーん、見せ方もそうだけど、やっぱり"ストーリー性"が大事なんだよね。お客様の課題から始まって、そこにどう貢献できるのかって流れが自然だと、響くんだよ。
**田中**：
なるほど、ストーリー性ですね。たとえば何か参考になる資料とかありますか？
**佐藤**：
特にこれってのはないけど、他のメンバーの資料とか見てみるといいかもね。空気感がつかめると思うから。
**田中**：
（空気感…って何だろう）
分かりました。確認してみます。
**佐藤**：
うんうん。あと、資料って"センス"もあるからさ、数こなして感覚を磨いていこう。
**田中**：
（…結局何を直せばよかったんだ…）
ありがとうございます。頑張ります。
"""
    
    print("【1on1判定の詳細分析】")
    print("-" * 40)
    
    # 1on1判定を実行
    is_one_on_one = dialogue_manager._is_one_on_one_content(one_on_one_content)
    print(f"🎯 1on1判定結果: {is_one_on_one}")
    
    # 判定指標の詳細確認
    print("\n【判定指標の詳細】")
    indicators = [
        ("対話形式（：が2個以上）", "：" in one_on_one_content and one_on_one_content.count("：") >= 2),
        ("距離を詰める", "距離を詰める" in one_on_one_content),
        ("信頼関係", "信頼関係" in one_on_one_content), 
        ("温度感", "温度感" in one_on_one_content),
        ("課題に寄り添った", "課題に寄り添った" in one_on_one_content),
        ("もう少し〜といいね", "もう少し" in one_on_one_content and "といいね" in one_on_one_content),
        ("がカギだと思う", "がカギだと思う" in one_on_one_content),
        ("を意識して", "を意識して" in one_on_one_content),
        ("営業活動", "営業活動" in one_on_one_content and "調子" in one_on_one_content),
        ("新規アポ", "新規アポ" in one_on_one_content),
        ("成約", "成約" in one_on_one_content),
        ("長文（100文字以上）", len(one_on_one_content) > 100)
    ]
    
    matching_count = 0
    for name, result in indicators:
        status = "✅" if result else "❌"
        print(f"  {status} {name}: {result}")
        if result:
            matching_count += 1
    
    print(f"\n📊 合致指標数: {matching_count}/12")
    print(f"📊 判定閾値: 3以上で1on1と判定")
    print(f"📊 結果: {'1on1と判定' if matching_count >= 3 else '1on1ではないと判定'}")
    
    # 提案資料特有の要素を確認
    print("\n【提案資料関連の要素】")
    proposal_indicators = [
        ("提案資料", "提案資料" in one_on_one_content),
        ("伝わる資料", "伝わる資料" in one_on_one_content),
        ("ストーリー性", "ストーリー性" in one_on_one_content),
        ("空気感", "空気感" in one_on_one_content),
        ("センス", "センス" in one_on_one_content),
        ("洗練", "洗練" in one_on_one_content),
        ("構成", "構成" in one_on_one_content),
        ("デザイン", "デザイン" in one_on_one_content)
    ]
    
    proposal_matching = 0
    for name, result in proposal_indicators:
        status = "✅" if result else "❌"
        print(f"  {status} {name}: {result}")
        if result:
            proposal_matching += 1
    
    print(f"\n📊 提案資料関連要素: {proposal_matching}/8")
    
    # 改善提案
    print("\n【1on1判定の改善提案】")
    if not is_one_on_one:
        print("❌ 現在の判定ロジックでは1on1と認識されていません")
        print("💡 改善案:")
        print("  1. 提案資料関連のキーワードを判定指標に追加")
        print("  2. 上司・部下の対話パターンを追加")
        print("  3. フィードバック関連のキーワードを追加")
        
        # 提案する新しい判定指標
        additional_indicators = [
            "提案資料" in one_on_one_content,
            "フィードバック" in one_on_one_content or "確認したよ" in one_on_one_content,
            "もう少し" in one_on_one_content,
            "といいかな" in one_on_one_content or "といいね" in one_on_one_content,
            "ストーリー性" in one_on_one_content,
            "センス" in one_on_one_content,
            "感覚" in one_on_one_content,
            "数こなして" in one_on_one_content
        ]
        
        additional_matching = sum(1 for indicator in additional_indicators if indicator)
        total_matching = matching_count + additional_matching
        
        print(f"  📊 追加指標を含めた場合: {total_matching}/20")
        print(f"  📊 1on1判定: {'可能' if total_matching >= 3 else '不可能'}")
    else:
        print("✅ 正しく1on1と判定されています")

if __name__ == "__main__":
    test_one_on_one_detection()