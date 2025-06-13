"""
1on1ミーティング分析エンジン
LLMを使って上司の指示を読み取り、analyze.mdの方法論で具体的なアクションプランを生成
"""

from typing import Dict, Any, List, Optional
import json
import re
from datetime import datetime

from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.conversation_history_service import ConversationHistoryService
from app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage


class OneOnOneAnalyzer:
    """1on1ミーティングの内容をLLMで分析し、具体的なアクションプランを生成"""
    
    def __init__(self):
        self.knowledge_service = KnowledgeBaseService()
        self.history_service = ConversationHistoryService()
        
        # LLMの初期化（Mock LLMかどうかに関わらず設定）
        if settings.USE_MOCK_LLM:
            # Mock環境では分析をスキップ
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.3,  # 分析では一貫性を重視
                api_key=settings.OPENAI_API_KEY
            )
    
    async def analyze_and_generate_summary(
        self, 
        one_on_one_content: str, 
        user_id: str,
        db_session = None
    ) -> Dict[str, Any]:
        """
        LLMを使って1on1の内容を分析し、具体的なサマリーを生成
        
        Args:
            one_on_one_content: 1on1ミーティングの内容
            user_id: ユーザーID
            db_session: データベースセッション
            
        Returns:
            具体的なアクションサマリー
        """
        
        # Mock環境では簡易版を返す
        if self.llm is None:
            return self._generate_mock_analysis(one_on_one_content)
        
        # ナレッジベース情報を収集
        relevant_knowledge = await self._search_knowledge_for_analysis(one_on_one_content)
        
        # 過去の対話ログを収集
        past_insights = await self._search_past_insights_for_analysis(user_id, db_session)
        
        # LLMに分析を実行させる
        analysis_result = await self._llm_analyze_one_on_one(
            one_on_one_content, 
            relevant_knowledge, 
            past_insights
        )
        
        return {
            "original_content": one_on_one_content,
            "analysis_result": analysis_result,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "knowledge_used": len(relevant_knowledge) > 0,
            "insights_used": len(past_insights) > 0,
            # 最終サマリーとして分析結果を展開
            "supervisor_instructions": analysis_result.get("supervisor_instructions", []),
            "final_summary": analysis_result.get("final_summary", {})
        }
    
    def _generate_mock_analysis(self, content: str) -> Dict[str, Any]:
        """Mock環境用の簡易分析"""
        return {
            "supervisor_instructions": [
                {"abstract_concept": "顧客との関係構築", "analysis": "Mock分析結果"}
            ],
            "final_summary": {
                "title": "Mock 1on1分析結果",
                "priority_actions": [
                    {"action": "Mock アクション1", "specific_steps": ["ステップ1"], "frequency": "毎日"}
                ],
                "implementation_timeline": {
                    "immediately": "Mock: 即座に実行すること",
                    "this_week": "Mock: 今週中に実行すること"
                },
                "success_metrics": [
                    {"metric": "Mock指標", "target": "Mock目標"}
                ],
                "next_steps": ["Mock: 次のステップ"]
            }
        }
    
    async def _search_knowledge_for_analysis(self, content: str) -> List[Dict[str, Any]]:
        """分析用のナレッジベース検索"""
        try:
            # 営業関連のキーワードを抽出
            keywords = ["営業", "顧客", "信頼", "関係", "提案", "ヒアリング", "商談"]
            all_results = []
            
            for keyword in keywords:
                results = await self.knowledge_service.search_knowledge(keyword)
                all_results.extend(results)
            
            # 重複除去
            unique_results = []
            seen_titles = set()
            for result in all_results:
                title = result.get('title', '')
                if title not in seen_titles:
                    unique_results.append(result)
                    seen_titles.add(title)
            
            return unique_results[:5]  # 最大5件
        except Exception:
            return []
    
    async def _search_past_insights_for_analysis(self, user_id: str, db_session) -> List[Dict[str, Any]]:
        """分析用の過去洞察検索"""
        if not db_session:
            return []
        
        try:
            insights = await self.history_service.get_user_insights(user_id, db_session)
            return insights[:3]  # 最大3件
        except Exception:
            return []
    
    async def _llm_analyze_one_on_one(
        self, 
        content: str, 
        knowledge: List[Dict[str, Any]], 
        insights: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """LLMを使ってanalyze.mdの方法論で1on1を分析"""
        
        # ナレッジベース情報をテキスト化
        knowledge_text = ""
        if knowledge:
            knowledge_text = "\\n\\n【参考ナレッジ】\\n"
            for k in knowledge:
                knowledge_text += f"- {k.get('title', '')}: {k.get('content', '')[:100]}...\\n"
        
        # 過去の洞察をテキスト化
        insights_text = ""
        if insights:
            insights_text = "\\n\\n【過去の洞察】\\n"
            for i in insights:
                insights_text += f"- {i.get('content', '')[:100]}...\\n"
        
        # analyze.mdの方法論を含むシステムプロンプト
        system_prompt = f"""あなたは営業コーチングの専門家です。1on1ミーティングの内容を分析し、上司の抽象的な指示を具体的な行動計画に変換してください。

以下の5ステップで分析を実行してください：

**ステップ1: 課題の再定義（なぜ必要か）**
- 上司の指示の真の目的を明確化
- それを達成することで得られる成果を具体化

**ステップ2: 構成要素の洗い出し**  
- 抽象的な概念を構成する具体的要素に分解
- 各要素の重要度を評価

**ステップ3: 行動レベルに落とし込む**
- 明日から実行できる具体的なアクションに変換
- 頻度、タイミング、方法を明確に指定

**ステップ4: KPI・指標化**
- 各アクションの成果を測定する方法
- 具体的な目標値を設定

**ステップ5: 習慣化・振り返り方法**
- 継続実行のための仕組み
- 定期的な効果検証方法

必ず以下のJSON形式で回答してください：
```json
{{
  "supervisor_instructions": [
    {{
      "original_text": "上司の発言そのまま",
      "abstract_concept": "抽象的な概念",
      "redefined_purpose": "再定義された目的と理由"
    }}
  ],
  "final_summary": {{
    "title": "1on1フィードバック分析結果",
    "priority_actions": [
      {{
        "action": "具体的なアクション",
        "specific_steps": ["ステップ1", "ステップ2"],
        "frequency": "実行頻度"
      }}
    ],
    "implementation_timeline": {{
      "immediately": "今すぐ実行すること",
      "this_week": "今週中に実行すること", 
      "this_month": "今月中に実行すること"
    }},
    "success_metrics": [
      {{
        "metric": "測定指標",
        "target": "目標値",
        "how_to_measure": "測定方法"
      }}
    ],
    "next_steps": ["次のステップ1", "次のステップ2"]
  }}
}}
```

**重要**: 抽象的な表現は一切使わず、全て具体的で実行可能な内容にしてください。{knowledge_text}{insights_text}"""
        
        # LLMに分析を実行させる
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"以下の1on1内容を分析してください：\\n\\n{content}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # JSONを抽出してパース
            response_text = response.content.strip()
            
            # ```json で囲まれている場合は抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            return json.loads(response_text)
            
        except Exception as e:
            # エラーの場合は基本的な分析結果を返す
            return {
                "supervisor_instructions": [
                    {"abstract_concept": "分析エラー", "original_text": str(e)}
                ],
                "final_summary": {
                    "title": "分析エラー",
                    "priority_actions": [
                        {"action": "エラーが発生しました", "specific_steps": [], "frequency": ""}
                    ],
                    "implementation_timeline": {},
                    "success_metrics": [],
                    "next_steps": []
                }
            }