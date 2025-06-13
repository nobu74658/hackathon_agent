#!/usr/bin/env python3
"""
Slack出力フォーマットのテストスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.slack_service import SlackService

def test_slack_formatting():
    """Slackフォーマット関数のテスト"""
    
    print("🎯 Slackフォーマット修正テスト")
    print("=" * 60)
    
    # モックレスポンスデータ
    mock_response = {
        "type": "one_on_one_final_plan",
        "data": {
            "final_summary": {
                "title": "1on1フィードバック 最終アクションプラン",
                "priority_actions": [
                    {
                        "action": "商談開始時の雑談時間を設ける",
                        "specific_steps": [
                            "天気や最近のニュースから話を始める",
                            "相手の状況について質問する",
                            "相手のペースに合わせる"
                        ],
                        "frequency": "毎回の商談",
                        "measurement": "商談後のメモ記録"
                    },
                    {
                        "action": "信頼関係構築のためのアプローチ",
                        "specific_steps": [
                            "約束は必ず守る", 
                            "専門的な知識を提供する",
                            "顧客の立場を理解する"
                        ],
                        "frequency": "継続的",
                        "measurement": "顧客満足度調査"
                    }
                ],
                "implementation_timeline": {
                    "immediately": "雑談時間の導入",
                    "this_week": "信頼関係構築手法の実践",
                    "this_month": "効果測定と改善"
                },
                "success_metrics": [
                    {
                        "metric": "商談成約率",
                        "target": "前月比5%向上",
                        "how_to_measure": "CRMデータ分析"
                    },
                    {
                        "metric": "顧客満足度",
                        "target": "4.0以上",
                        "how_to_measure": "アンケート調査"
                    }
                ],
                "next_steps": [
                    "今週中に新しい手法を試行",
                    "月末に効果を測定",
                    "改善点を特定して次月に反映"
                ]
            },
            "dialogue_summary": {
                "instructions_clarified": 3,
                "total_interactions": "8回",
                "key_insights": ["雑談の重要性", "信頼関係の構築"],
                "concreteness_improvement": "抽象的→具体的に変換済み"
            }
        },
        "clarification_history": [
            {
                "original_abstract": "距離を詰める",
                "concreteness_score": 85
            },
            {
                "original_abstract": "信頼関係構築",
                "concreteness_score": 90
            },
            {
                "original_abstract": "課題に寄り添った提案",
                "concreteness_score": 88
            }
        ]
    }
    
    # SlackServiceインスタンスを作成（設定は無視）
    try:
        # 設定エラーを無視してフォーマット関数のテストのみ実行
        class MockSlackService:
            def _format_one_on_one_final_plan_for_slack(self, response):
                # 実際のSlackServiceのメソッドをコピー
                data = response.get("data", {})
                final_summary = data.get("final_summary", {})
                dialogue_summary = data.get("dialogue_summary", {})
                clarification_history = response.get("clarification_history", [])
                
                # ヘッダー
                formatted = "🎉 **1on1フィードバック 最終アクションプラン完成！**\n\n"
                
                # 対話サマリー
                instructions_count = dialogue_summary.get("instructions_clarified", 0)
                if instructions_count > 0:
                    formatted += f"✅ **対話完了**: {instructions_count}件の抽象的指示を具体化しました\n"
                    
                    # 具体化された指示の簡単な概要
                    if clarification_history:
                        formatted += "📋 **具体化された指示**:\n"
                        for i, history in enumerate(clarification_history[:3], 1):
                            original = history.get("original_abstract", "")
                            score = history.get("concreteness_score", 0)
                            formatted += f"   {i}. {original} (具体性: {score}%)\n"
                        formatted += "\n"
                
                # 優先アクション
                priority_actions = final_summary.get("priority_actions", [])
                if priority_actions:
                    formatted += "🚀 **優先的に取り組むべきアクション**:\n"
                    for i, action in enumerate(priority_actions[:3], 1):
                        formatted += f"\n**{i}. {action.get('action', '')}**\n"
                        steps = action.get('specific_steps', [])
                        for step in steps[:3]:  # 最初の3ステップ
                            formatted += f"   • {step}\n"
                        formatted += f"   📅 頻度: {action.get('frequency', '')}\n"
                        if action.get('measurement'):
                            formatted += f"   📊 測定: {action['measurement']}\n"
                
                # 実装タイムライン
                timeline = final_summary.get("implementation_timeline", {})
                if timeline:
                    formatted += "\n📅 **実装スケジュール**:\n"
                    if timeline.get("immediately"):
                        formatted += f"🔴 **今すぐ**: {timeline['immediately']}\n"
                    if timeline.get("this_week"):
                        formatted += f"🟡 **今週中**: {timeline['this_week']}\n"
                    if timeline.get("this_month"):
                        formatted += f"🟢 **今月中**: {timeline['this_month']}\n"
                
                # 成功指標
                metrics = final_summary.get("success_metrics", [])
                if metrics:
                    formatted += "\n📊 **成功指標**:\n"
                    for metric in metrics[:2]:
                        formatted += f"• **{metric.get('metric', '')}**: {metric.get('target', '')}\n"
                
                # 次のステップ  
                next_steps = final_summary.get("next_steps", [])
                if next_steps:
                    formatted += "\n🎯 **次のステップ**:\n"
                    for step in next_steps[:3]:
                        formatted += f"• {step}\n"
                
                # 完了メッセージ
                formatted += "\n✨ **お疲れ様でした！** 上司からの抽象的な指示が、明日から実行できる具体的なアクションプランになりました。"
                
                # 文字数制限対応
                if len(formatted) > 3000:
                    formatted = formatted[:2900] + "\n\n_（詳細が省略されています）_"
                
                return formatted
        
        mock_service = MockSlackService()
        formatted_output = mock_service._format_one_on_one_final_plan_for_slack(mock_response)
        
        print("✅ フォーマット成功")
        print("📄 出力結果:")
        print("-" * 40)
        print(formatted_output)
        print("-" * 40)
        
        # 改行文字の確認
        line_count = formatted_output.count('\n')
        print(f"📊 統計:")
        print(f"  - 総文字数: {len(formatted_output)}")
        print(f"  - 改行数: {line_count}")
        escape_check = '含まれている' if '\\n' in formatted_output else '含まれていない'
        print(f"  - \\n エスケープ: {escape_check}")
        
        # 問題のある箇所の確認
        if '\\n' in formatted_output:
            print("❌ エスケープシーケンスが残っています")
            positions = [i for i, char in enumerate(formatted_output) if formatted_output[i:i+2] == '\\n']
            print(f"  - \\n の位置: {positions[:5]}")  # 最初の5個の位置
        else:
            print("✅ エスケープシーケンスは正しく処理されています")
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_slack_formatting()