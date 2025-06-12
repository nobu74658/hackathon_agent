#!/usr/bin/env python3
"""
改善されたLLM APIデモスクリプト
知識ベースと自己解決機能を含む対話デモ
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any
from datetime import datetime

BASE_URL = "http://localhost:8000"

class EnhancedLLMDemo:
    def __init__(self):
        self.session = None
        self.session_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_knowledge_base(self):
        """知識ベース機能のテスト"""
        print("🧠 知識ベーステスト...")
        
        # 会社の価値観を取得
        try:
            async with self.session.get(f"{BASE_URL}/enhanced/knowledge/company-values") as response:
                values = await response.json()
                print("✅ 会社の価値観:")
                print(f"   ミッション: {values.get('mission', 'N/A')}")
                print(f"   ビジョン: {values.get('vision', 'N/A')}")
                print("   バリュー:")
                for value in values.get('values', []):
                    print(f"   - {value}")
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
        
        # 知識検索テスト
        test_queries = ["緊張", "新規開拓", "プレゼン"]
        for query in test_queries:
            print(f"\n🔍 「{query}」を検索中...")
            try:
                async with self.session.post(
                    f"{BASE_URL}/enhanced/knowledge/search",
                    json={"query": query}
                ) as response:
                    result = await response.json()
                    print(f"   検索結果: {result['count']}件")
                    if result['results']:
                        print(f"   最も関連性の高い結果: {result['results'][0]['category']}")
            except Exception as e:
                print(f"❌ 検索エラー: {str(e)}")
    
    async def test_templates(self):
        """テンプレート機能のテスト"""
        print("\n📋 テンプレート機能テスト...")
        
        try:
            async with self.session.get(f"{BASE_URL}/enhanced/templates/list") as response:
                templates = await response.json()
                print("✅ 利用可能なテンプレートカテゴリ:")
                for category, items in templates.get("templates", {}).items():
                    print(f"   - {category}: {len(items)}個のテンプレート")
                    for item in items[:2]:  # 最初の2個を表示
                        print(f"     • {item['title']}")
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
    
    async def start_enhanced_session(self, specific_challenge: str = None):
        """改善されたセッション開始"""
        print(f"\n🚀 改善されたセッション開始...")
        
        request_data = {
            "user_name": "田中太郎",
            "department": "営業部",
            "experience_years": 1,
            "initial_topic": "新規顧客開拓のスキル向上",
            "specific_challenge": specific_challenge
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/enhanced/start",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.session_id = result["session_id"]
                    
                    print(f"✅ セッション開始成功 (ID: {self.session_id[:8]}...)")
                    print(f"📊 初期情報充足度: {result['completeness_score']}%")
                    print(f"🧠 知識ベース活用: {'はい' if result['knowledge_used'] else 'いいえ'}")
                    print(f"💭 理由: {result['reasoning']}")
                    
                    if result.get("self_resolved_insights"):
                        print("\n💡 自己解決された洞察:")
                        for insight in result["self_resolved_insights"]:
                            print(f"   - {insight}")
                    
                    if result.get("suggested_resources"):
                        print("\n📚 推奨リソース:")
                        for resource in result["suggested_resources"]:
                            print(f"   - {resource}")
                    
                    print("\n📝 生成された質問:")
                    for i, question in enumerate(result["questions"], 1):
                        print(f"   {i}. {question}")
                    
                    return result
                else:
                    error = await response.json()
                    print(f"❌ セッション開始失敗: {error['detail']}")
                    return None
                    
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return None
    
    async def send_message(self, message: str):
        """メッセージ送信（改善版）"""
        if not self.session_id:
            print("❌ セッションが開始されていません")
            return None
        
        print(f"\n💬 ユーザー: {message}")
        print("🤖 AI応答生成中...")
        
        request_data = {
            "session_id": self.session_id,
            "message": message
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/enhanced/message",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"📊 情報充足度: {result['completeness_score']}%")
                    
                    if result.get("self_resolved"):
                        print("💡 自己解決された質問:")
                        for resolved in result["self_resolved"]:
                            print(f"   Q: {resolved['question']}")
                            print(f"   A: {resolved['answer']}")
                    
                    if result["type"] == "follow_up":
                        print(f"🤝 対話の確信度: {result.get('confidence', 'N/A')}")
                        if result["questions"]:
                            print("📝 追加質問（最小限）:")
                            for i, question in enumerate(result["questions"], 1):
                                print(f"   {i}. {question}")
                        else:
                            print("✅ 追加質問なし（十分な情報が収集されました）")
                    
                    elif result["type"] == "action_plan":
                        print("🎯 アクションプラン生成完了!")
                        action_plan = result["action_plan"]
                        
                        print(f"\n📋 サマリー: {action_plan['summary']}")
                        
                        if action_plan.get("templates_provided"):
                            print("\n📑 提供されたテンプレート:")
                            for template in action_plan["templates_provided"]:
                                print(f"   - {template['title']} ({template['category']})")
                        
                        print("\n📈 アクションアイテム:")
                        for i, item in enumerate(action_plan["action_items"][:5], 1):  # 最初の5個
                            print(f"   {i}. {item.get('title', 'N/A')}")
                            print(f"      説明: {item.get('description', 'N/A')}")
                            print(f"      優先度: {item.get('priority', 'N/A')}")
                            print(f"      期限: {item.get('due_date', 'N/A')}")
                        
                        if action_plan.get("knowledge_references"):
                            print("\n📚 参照した社内ナレッジ:")
                            for ref in action_plan["knowledge_references"][:3]:
                                print(f"   - {ref.get('type', 'N/A')}")
                        
                        if action_plan.get("mentor_suggestions"):
                            print("\n👥 先輩からのアドバイス:")
                            for suggestion in action_plan["mentor_suggestions"][:3]:
                                print(f"   - {suggestion}")
                    
                    return result
                else:
                    error = await response.json()
                    print(f"❌ メッセージ送信失敗: {error['detail']}")
                    return None
                    
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return None
    
    async def run_demo_scenario(self, scenario: str):
        """デモシナリオ実行"""
        print(f"\n🎬 デモシナリオ「{scenario}」を実行中...")
        
        try:
            async with self.session.get(f"{BASE_URL}/enhanced/demo/scenario/{scenario}") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ シナリオ実行完了")
                    print(f"   セッションID: {result['session_id'][:8]}...")
                    print(f"   インタラクション数: {len(result['interactions'])}")
                    
                    # 最終的なアクションプランを表示
                    last_interaction = result['interactions'][-1]
                    if last_interaction['response']['type'] == 'action_plan':
                        print("\n🎯 生成されたアクションプラン:")
                        action_plan = last_interaction['response']['action_plan']
                        print(f"   アクション数: {len(action_plan['action_items'])}")
                        print(f"   テンプレート数: {len(action_plan.get('templates_provided', []))}")
                        print(f"   知識参照数: {len(action_plan.get('knowledge_references', []))}")
                    
                    return result
                else:
                    error = await response.json()
                    print(f"❌ シナリオ実行失敗: {error['detail']}")
                    return None
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return None

async def interactive_demo():
    """インタラクティブデモ（改善版）"""
    print("=" * 60)
    print("🤖 営業スキル向上AI - 改善版デモ")
    print("   知識ベース＋自己解決機能搭載")
    print("=" * 60)
    
    async with EnhancedLLMDemo() as demo:
        # 知識ベースとテンプレートのテスト
        await demo.test_knowledge_base()
        await demo.test_templates()
        
        print("\n" + "="*60)
        print("💬 対話デモを開始しますか？")
        print("1. インタラクティブモード")
        print("2. シナリオ実行（緊張克服）")
        print("3. シナリオ実行（新規開拓）")
        print("4. 終了")
        
        choice = input("\n選択 (1-4): ").strip()
        
        if choice == "1":
            # インタラクティブモード
            specific_challenge = input("具体的な課題を入力してください（オプション）: ").strip()
            
            session_result = await demo.start_enhanced_session(
                specific_challenge if specific_challenge else None
            )
            if not session_result:
                return
            
            print("\n" + "="*60)
            print("💬 対話開始! 'quit'で終了")
            print("="*60)
            
            while True:
                user_input = input("\n🗣️  あなた: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                result = await demo.send_message(user_input)
                
                if result and result["type"] == "action_plan":
                    print("\n🎉 アクションプランが完成しました!")
                    
                    # セッションの洞察を表示
                    async with demo.session.get(
                        f"{BASE_URL}/enhanced/session/{demo.session_id}/insights"
                    ) as response:
                        if response.status == 200:
                            insights = await response.json()
                            print(f"\n📊 セッション統計:")
                            print(f"   総メッセージ数: {insights['conversation_efficiency']['total_messages']}")
                            print(f"   自己解決数: {insights['self_resolved_count']}")
                    
                    break
        
        elif choice == "2":
            # 緊張克服シナリオ
            await demo.run_demo_scenario("nervous_presentation")
        
        elif choice == "3":
            # 新規開拓シナリオ
            await demo.run_demo_scenario("new_customer_acquisition")
        
        print("\n👋 デモを終了します。お疲れさまでした!")

async def comparison_demo():
    """従来版と改善版の比較デモ"""
    print("📊 従来版と改善版の比較デモ")
    print("=" * 60)
    
    # 同じ課題で両方のシステムをテスト
    test_messages = [
        "プレゼンで緊張して頭が真っ白になってしまいます",
        "原稿を用意しても、本番では忘れてしまいます",
        "先週も重要な商談で失敗してしまいました"
    ]
    
    # 従来版
    print("\n【従来版】")
    # （従来版のAPIコール - 省略）
    
    # 改善版
    print("\n【改善版】")
    async with EnhancedLLMDemo() as demo:
        await demo.start_enhanced_session("プレゼンでの緊張")
        for msg in test_messages:
            await demo.send_message(msg)
    
    print("\n✅ 改善点:")
    print("   1. 質問数の削減（自己解決により）")
    print("   2. 具体的なテンプレート提供")
    print("   3. 先輩の成功事例の参照")

def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "compare":
            asyncio.run(comparison_demo())
        else:
            asyncio.run(interactive_demo())
    else:
        asyncio.run(interactive_demo())

if __name__ == "__main__":
    main()