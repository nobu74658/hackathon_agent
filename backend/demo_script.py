#!/usr/bin/env python3
"""
LLM APIデモスクリプト
実際のOpenAI/Anthropic APIを使用した対話デモ
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class LLMDemo:
    def __init__(self):
        self.session = None
        self.session_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_connection(self, provider: str = "openai"):
        """LLM接続テスト"""
        print(f"🔍 {provider.upper()} 接続テスト中...")
        
        try:
            async with self.session.get(f"{BASE_URL}/demo/test-connection/{provider}") as response:
                result = await response.json()
                
                if result["status"] == "success":
                    print(f"✅ {provider.upper()} 接続成功!")
                    print(f"   モデル: {result['model']}")
                    print(f"   テスト結果: {result['test_response']}")
                    return True
                else:
                    print(f"❌ {provider.upper()} 接続失敗: {result['error']}")
                    return False
                    
        except Exception as e:
            print(f"❌ 接続エラー: {str(e)}")
            return False
    
    async def start_demo_session(self, provider: str = "openai"):
        """デモセッション開始"""
        print(f"\n🚀 {provider.upper()} デモセッション開始...")
        
        request_data = {
            "user_name": "田中太郎",
            "department": "営業部",
            "experience_years": 1,
            "initial_topic": "新規顧客開拓のスキル向上",
            "llm_provider": provider
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/demo/start",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.session_id = result["session_id"]
                    
                    print(f"✅ セッション開始成功 (ID: {self.session_id[:8]}...)")
                    print(f"📊 初期情報充足度: {result['completeness_score']}%")
                    print(f"💭 理由: {result['reasoning']}")
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
        """メッセージ送信"""
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
                f"{BASE_URL}/demo/message",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"📊 情報充足度: {result['completeness_score']}%")
                    
                    # 感情分析結果
                    if result.get("sentiment_analysis"):
                        sentiment = result["sentiment_analysis"]
                        print(f"😊 感情分析: {sentiment.get('sentiment', 'N/A')} ({sentiment.get('emotional_state', 'N/A')})")
                    
                    if result["type"] == "follow_up":
                        print("📝 追加質問:")
                        for i, question in enumerate(result["questions"], 1):
                            print(f"   {i}. {question}")
                        if result.get("reasoning"):
                            print(f"💭 理由: {result['reasoning']}")
                    
                    elif result["type"] == "action_plan":
                        print("🎯 アクションプラン生成完了!")
                        action_plan = result["action_plan"]
                        print(f"📋 サマリー: {action_plan['summary']}")
                        print("📈 アクションアイテム:")
                        for i, item in enumerate(action_plan["action_items"], 1):
                            print(f"   {i}. {item.get('title', 'N/A')}")
                            print(f"      説明: {item.get('description', 'N/A')}")
                            print(f"      優先度: {item.get('priority', 'N/A')}")
                    
                    return result
                else:
                    error = await response.json()
                    print(f"❌ メッセージ送信失敗: {error['detail']}")
                    return None
                    
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return None
    
    async def get_session_info(self):
        """セッション情報取得"""
        if not self.session_id:
            return None
        
        try:
            async with self.session.get(f"{BASE_URL}/demo/session/{self.session_id}") as response:
                if response.status == 200:
                    return await response.json()
                return None
        except:
            return None

async def interactive_demo():
    """インタラクティブデモ"""
    print("=" * 60)
    print("🤖 営業スキル向上AI - LLMデモ")
    print("=" * 60)
    
    # プロバイダー選択
    print("\nLLMプロバイダーを選択してください:")
    print("1. OpenAI GPT-3.5-turbo")
    print("2. Anthropic Claude")
    
    while True:
        choice = input("選択 (1-2): ").strip()
        if choice == "1":
            provider = "openai"
            break
        elif choice == "2":
            provider = "anthropic"
            break
        else:
            print("❌ 無効な選択です")
    
    async with LLMDemo() as demo:
        # 接続テスト
        if not await demo.test_connection(provider):
            print("\n❌ API接続に失敗しました。.envファイルのAPI keyを確認してください。")
            return
        
        # セッション開始
        session_result = await demo.start_demo_session(provider)
        if not session_result:
            return
        
        print("\n" + "="*60)
        print("💬 対話開始! 'quit'で終了")
        print("="*60)
        
        # 対話ループ
        while True:
            user_input = input("\n🗣️  あなた: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            result = await demo.send_message(user_input)
            
            if result and result["type"] == "action_plan":
                print("\n🎉 アクションプランが完成しました!")
                
                # セッション情報を表示
                session_info = await demo.get_session_info()
                if session_info:
                    print(f"📊 総メッセージ数: {session_info['message_count']}")
                
                break
        
        print("\n👋 デモを終了します。お疲れさまでした!")

async def batch_demo():
    """バッチデモ（サンプル会話）"""
    print("🤖 バッチデモ実行中...")
    
    sample_messages = [
        "新規顧客の開拓がうまくいかず、アポイントメントが取れません。",
        "電話でのアプローチを主にしていますが、断られることが多いです。",
        "目標は月に10件の新規顧客獲得ですが、現在は2-3件程度です。",
        "営業経験は1年で、主に既存顧客のフォローをしていました。",
        "上司からはもっと積極的にアプローチするよう言われています。"
    ]
    
    async with LLMDemo() as demo:
        if not await demo.test_connection("openai"):
            print("❌ API接続失敗")
            return
        
        await demo.start_demo_session("openai")
        
        for message in sample_messages:
            await demo.send_message(message)
            await asyncio.sleep(1)  # API制限対策

def main():
    """メイン関数"""
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        asyncio.run(batch_demo())
    else:
        asyncio.run(interactive_demo())

if __name__ == "__main__":
    main()