import openai
from typing import Dict, List, Any
import json

class AIService:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """1on1テキストから改善点を抽出"""
        
        prompt = f"""
        以下の1on1ミーティングの内容から、新人営業マンの改善点を抽出してください。
        各改善点について、抽象度（高・中・低）を判定し、具体化が必要かどうかも示してください。

        1on1の内容:
        {text}

        以下のJSON形式で回答してください:
        {{
            "positive_points": [
                {{"content": "良かった点", "category": "カテゴリ"}}
            ],
            "improvement_points": [
                {{
                    "id": "point_1",
                    "content": "改善点",
                    "category": "カテゴリ",
                    "abstraction_level": "high/medium/low",
                    "needs_clarification": true/false
                }}
            ]
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは営業教育の専門家です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_question(self, improvement_point: Dict, history: List[Dict], user_response: str = "") -> Dict[str, Any]:
        """改善点を具体化するための質問を生成"""
        
        history_text = "\n".join([
            f"{item['role']}: {item['content']}" 
            for item in history
        ])
        
        prompt = f"""
        新人営業マンの以下の改善点について、具体的な行動計画を作成するために必要な情報を収集しています。

        改善点: {improvement_point['content']}
        カテゴリ: {improvement_point['category']}
        
        これまでの対話:
        {history_text}
        
        最新の回答: {user_response}

        次の質問を生成してください。十分な情報が集まった場合は、質問ではなく完了フラグを返してください。

        以下のJSON形式で回答してください:
        {{
            "question": "次の質問（完了の場合は空文字）",
            "is_complete": true/false,
            "progress": 進捗率（0-100）
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは営業コーチングの専門家です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_action_plan(self, analysis: Dict, chat_histories: Dict) -> List[Dict]:
        """具体的なアクションプランを生成"""
        
        improvement_details = []
        for point in analysis.get('improvement_points', []):
            point_id = point['id']
            history = chat_histories.get(point_id, [])
            
            details = {
                'improvement_point': point,
                'clarifications': [
                    item['content'] for item in history 
                    if item['role'] == 'user'
                ]
            }
            improvement_details.append(details)
        
        prompt = f"""
        新人営業マンの改善点と、それに対する詳細情報から、具体的なアクションプランを作成してください。

        改善点と詳細:
        {json.dumps(improvement_details, ensure_ascii=False, indent=2)}

        以下のJSON形式で、SMART（具体的・測定可能・達成可能・関連性・期限設定）なアクションプランを作成してください:
        [
            {{
                "title": "アクションのタイトル",
                "description": "詳細な説明",
                "category": "カテゴリ",
                "priority": "high/medium/low",
                "specific_steps": ["ステップ1", "ステップ2"],
                "success_metric": "成功指標",
                "due_date": "推奨期限（例：1週間後）",
                "resources": ["必要なリソースや参考資料"]
            }}
        ]
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは営業トレーニングの専門家です。実践的で具体的なアクションプランを作成してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 配列として返すように調整
        if isinstance(result, dict) and 'actions' in result:
            return result['actions']
        elif isinstance(result, list):
            return result
        else:
            # フォーマットが期待と異なる場合の処理
            return [{
                "title": "アクションプラン",
                "description": str(result),
                "category": "general",
                "priority": "medium",
                "specific_steps": ["詳細はAIの回答を確認してください"],
                "success_metric": "改善の実感",
                "due_date": "2週間後",
                "resources": []
            }]