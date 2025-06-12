"""
開発・テスト用のモックLLMサービス
API keyなしでも動作確認可能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import random


class MockLLMProvider:
    """API呼び出しなしのモックLLMプロバイダー"""
    
    def __init__(self, provider_name: str = "mock"):
        self.provider_name = provider_name
        self.call_count = 0
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """テキスト解析のモック"""
        self.call_count += 1
        
        # 簡単なキーワード分析
        keywords = ["営業", "コミュニケーション", "顧客", "提案", "課題", "改善"]
        found_keywords = [kw for kw in keywords if kw in text]
        
        return {
            "analysis": {
                "sentiment": "positive" if "良い" in text or "成功" in text else "neutral",
                "keywords": found_keywords,
                "length": len(text),
                "complexity": "high" if len(text) > 100 else "medium"
            },
            "suggestions": [
                "具体的な事例を追加で聞いてみましょう",
                "数値的な目標について確認が必要です",
                "現在のスキルレベルを把握しましょう"
            ],
            "confidence": 0.85,
            "provider": self.provider_name,
            "call_count": self.call_count
        }
    
    async def generate_questions(self, context: Dict[str, Any]) -> List[str]:
        """質問生成のモック"""
        self.call_count += 1
        
        # コンテキストに基づく質問テンプレート
        base_questions = [
            "どのような場面で最も困難を感じますか？",
            "現在の営業活動で最も時間を取られていることは何ですか？",
            "理想的な営業成果とはどのようなものですか？",
            "過去に成功した営業事例があれば教えてください",
            "現在利用できるリソースや制約はありますか？"
        ]
        
        # メッセージ数に応じて質問を調整
        message_count = context.get("message_count", 0)
        if message_count > 5:
            questions = [
                "これまでの内容を踏まえて、最も優先したい改善点は何ですか？",
                "具体的な期限や目標はありますか？",
                "サポートが必要な領域を教えてください"
            ]
        else:
            questions = random.sample(base_questions, min(3, len(base_questions)))
        
        return questions
    
    async def create_action_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """アクションプラン生成のモック"""
        self.call_count += 1
        
        # 収集された情報から基本的なプランを生成
        messages = data.get("messages", [])
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        
        action_items = [
            {
                "id": "action_1",
                "title": "顧客コミュニケーション改善",
                "description": "日々の顧客とのやり取りを記録し、週1回振り返りを行う",
                "priority": "high",
                "due_date": "2024-02-15",
                "category": "communication",
                "metrics": ["顧客満足度", "フォローアップ率"]
            },
            {
                "id": "action_2", 
                "title": "営業スキル研修参加",
                "description": "社内外の営業研修やセミナーに月1回参加する",
                "priority": "medium",
                "due_date": "2024-02-29",
                "category": "skill_development",
                "metrics": ["研修参加回数", "学習内容の実践率"]
            },
            {
                "id": "action_3",
                "title": "成果測定とレビュー",
                "description": "月次で営業成果を数値化し、上司とレビューを行う",
                "priority": "high",
                "due_date": "2024-01-31",
                "category": "measurement",
                "metrics": ["売上目標達成率", "新規顧客獲得数"]
            }
        ]
        
        return {
            "action_items": action_items,
            "summary": f"{len(user_messages)}回の対話から、営業スキル向上のための実践的なアクションプランを作成しました。",
            "key_improvements": [
                "顧客とのコミュニケーション質向上",
                "継続的な学習習慣の確立", 
                "成果の可視化と定期レビュー"
            ],
            "metrics": {
                "success_indicators": ["顧客満足度向上", "売上目標達成", "スキル習得"],
                "review_frequency": "monthly",
                "evaluation_criteria": ["定量評価", "定性評価", "自己評価"]
            },
            "generated_at": datetime.utcnow().isoformat(),
            "provider": self.provider_name,
            "call_count": self.call_count
        }
    
    async def evaluate_completeness(self, context: Dict[str, Any]) -> int:
        """情報充足度評価のモック"""
        self.call_count += 1
        
        messages = context.get("messages", [])
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        
        # 簡単な評価ロジック
        base_score = min(len(user_messages) * 15, 70)  # メッセージ数 x 15点、最大70点
        
        # キーワードボーナス
        all_text = " ".join([msg.get("content", "") for msg in user_messages])
        bonus_keywords = ["課題", "目標", "具体的", "例", "状況", "期限"]
        bonus = sum(5 for keyword in bonus_keywords if keyword in all_text)
        
        score = min(base_score + bonus, 100)
        return score


class MockDialogueManager:
    """API呼び出しなしのモック対話マネージャー"""
    
    def __init__(self):
        self.llm_provider = MockLLMProvider("mock_dialogue")
        self.sessions = {}  # セッション状態をメモリに保存
    
    async def initialize(self):
        """初期化（何もしない）"""
        pass
    
    async def start_dialogue(
        self,
        session_id: str,
        initial_context: Dict[str, Any]
    ) -> tuple[List[str], Dict[str, Any]]:
        """対話開始"""
        # セッション状態を初期化
        self.sessions[session_id] = {
            "messages": [],
            "context": initial_context,
            "stage": "initial",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # 初期質問を生成
        questions = await self.llm_provider.generate_questions(initial_context)
        
        metadata = {
            "stage": "initial",
            "reasoning": "1on1セッションの詳細を把握するために基本的な質問から開始します",
            "information_needed": ["具体的な課題", "現在の状況", "目標設定"],
            "completeness_score": 10
        }
        
        return questions, metadata
    
    async def process_user_response(
        self,
        session_id: str,
        user_response: str,
        db_session=None  # モックでは使用しない
    ) -> Dict[str, Any]:
        """ユーザー回答の処理"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # メッセージを追加
        session["messages"].extend([
            {"role": "user", "content": user_response, "timestamp": datetime.utcnow().isoformat()}
        ])
        
        # コンテキストを更新
        context = {
            "session_id": session_id,
            "messages": session["messages"],
            "message_count": len(session["messages"])
        }
        
        # 情報充足度を評価
        completeness_score = await self.llm_provider.evaluate_completeness(context)
        
        if completeness_score >= 80:
            # アクションプラン生成
            action_plan = await self.llm_provider.create_action_plan(context)
            session["stage"] = "completed"
            
            return {
                "type": "action_plan",
                "data": action_plan,
                "completeness_score": completeness_score
            }
        else:
            # 追加質問生成
            follow_up_questions = await self.llm_provider.generate_questions(context)
            session["stage"] = "gathering"
            
            return {
                "type": "follow_up",
                "questions": follow_up_questions,
                "completeness_score": completeness_score
            }
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッション情報を取得"""
        return self.sessions.get(session_id)