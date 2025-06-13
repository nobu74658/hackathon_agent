"""
理想的な対話シナリオを再現するワークフロー

IDEAL_DIALOGUE_SCENARIO.mdの内容を忠実に実装し、
ソクラテス式質問法による部下の成長支援を実現します。
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json
import re
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.mock_llm import MockLLMProvider


class DialogueState(Enum):
    """対話の状態管理"""
    GREETING = "greeting"  # 挨拶・導入
    CURRENT_SITUATION = "current_situation"  # 現状把握
    PROBLEM_ANALYSIS = "problem_analysis"  # 課題分析
    SOLUTION_EXPLORATION = "solution_exploration"  # ソリューション探索
    ACTION_PLAN = "action_plan"  # アクションプラン作成
    EXECUTION_SUPPORT = "execution_support"  # 実行支援
    SUMMARY = "summary"  # まとめ


class ResponseAnalysis(BaseModel):
    """部下の回答分析結果"""
    key_points: List[str] = Field(description="回答の重要ポイント")
    emotional_state: str = Field(description="部下の感情状態（困惑、自信、不安など）")
    understanding_level: int = Field(description="理解度（1-10）")
    success_patterns: List[str] = Field(description="言及された成功パターン")
    challenges: List[str] = Field(description="言及された課題や障害")
    next_action_hint: str = Field(description="次の質問のヒント")


class SocraticQuestion(BaseModel):
    """ソクラテス式質問"""
    question: str = Field(description="生成された質問")
    purpose: str = Field(description="この質問の目的")
    expected_outcome: str = Field(description="期待される気づきや成果")
    follow_up_options: List[str] = Field(description="想定される回答に対するフォローアップ")


class ActionPlanItem(BaseModel):
    """アクションプランの項目"""
    action: str = Field(description="具体的な行動")
    timeline: str = Field(description="実行期限")
    success_criteria: str = Field(description="成功基準")
    measurement: str = Field(description="測定方法")


class IdealDialogueWorkflow:
    """理想的な対話ワークフローの実装"""
    
    def __init__(self):
        # LLMサービスの初期化（モック対応）
        if settings.USE_MOCK_LLM or not settings.OPENAI_API_KEY:
            self.llm = MockLLMProvider()
            self.use_mock = True
        else:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY
            )
            self.use_mock = False
            
        self.response_parser = PydanticOutputParser(pydantic_object=ResponseAnalysis)
        self.question_parser = PydanticOutputParser(pydantic_object=SocraticQuestion)
        self.action_plan_parser = PydanticOutputParser(pydantic_object=ActionPlanItem)
        
        # セッション状態の管理
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def start_session(
        self,
        session_id: str,
        abstract_instruction: str,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """対話セッションを開始"""
        self.sessions[session_id] = {
            "state": DialogueState.GREETING,
            "abstract_instruction": abstract_instruction,
            "user_context": user_context or {},
            "dialogue_history": [],
            "discovered_patterns": {},
            "action_items": [],
            "created_at": datetime.now().isoformat()
        }
        
        # 挨拶と導入
        greeting = await self._generate_greeting(abstract_instruction, user_context)
        
        self.sessions[session_id]["dialogue_history"].append({
            "role": "assistant",
            "content": greeting,
            "state": DialogueState.GREETING.value,
            "timestamp": datetime.now().isoformat()
        })
        
        # 状態を現状把握に移行
        self.sessions[session_id]["state"] = DialogueState.CURRENT_SITUATION
        
        return {
            "type": "greeting",
            "message": greeting,
            "next_state": DialogueState.CURRENT_SITUATION.value,
            "session_id": session_id
        }
    
    async def process_response(
        self,
        session_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """部下の回答を処理して次の質問を生成"""
        session = self.sessions.get(session_id)
        if not session:
            return {"type": "error", "message": "セッションが見つかりません"}
        
        # 回答を記録
        session["dialogue_history"].append({
            "role": "user",
            "content": user_response,
            "state": session["state"].value,
            "timestamp": datetime.now().isoformat()
        })
        
        # 回答を分析
        analysis = await self._analyze_response(
            user_response,
            session["state"],
            session["dialogue_history"]
        )
        
        # 分析結果を保存
        self._update_session_insights(session, analysis)
        
        # 次の状態を決定
        next_state = self._determine_next_state(session, analysis)
        
        # 次の質問を生成
        if next_state == DialogueState.SUMMARY:
            # 最終サマリーを生成
            summary = await self._generate_summary(session)
            return {
                "type": "summary",
                "message": summary["message"],
                "action_plan": summary["action_plan"],
                "insights": summary["insights"]
            }
        else:
            question = await self._generate_socratic_question(
                session,
                analysis,
                next_state
            )
            
            # 状態を更新
            session["state"] = next_state
            
            # 対話履歴に追加
            session["dialogue_history"].append({
                "role": "assistant",
                "content": question.question,
                "state": next_state.value,
                "purpose": question.purpose,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "type": "question",
                "message": question.question,
                "purpose": question.purpose,
                "expected_outcome": question.expected_outcome,
                "state": next_state.value,
                "progress": self._calculate_progress(session)
            }
    
    async def _generate_greeting(
        self,
        abstract_instruction: str,
        user_context: Dict[str, Any]
    ) -> str:
        """挨拶と導入メッセージを生成"""
        if self.use_mock or isinstance(self.llm, MockLLMProvider):
            name = user_context.get('name', '田中さん')
            return f"""こんにちは{name}。お疲れ様です。

上司から「{abstract_instruction}」という指示があったとお聞きしました。私は営業スキル向上をサポートするAIコーチです。

この抽象的な指示を、あなたの状況に合った具体的で実行可能なアクションプランに変えていきましょう。まずは現在の状況を教えていただけますか？

一緒に考えていきますので、安心して現状をお聞かせください。"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIコーチです。
            
上司からの抽象的な指示を受けた部下に対して、温かく共感的な挨拶をしてください。

【重要な要素】
1. 親しみやすく、プレッシャーを与えない雰囲気
2. 上司の指示を認識していることを示す
3. 一緒に具体的な計画を作ることを提案
4. 部下の現状を聞く準備があることを示す

部下の情報: {user_context}
上司の指示: {abstract_instruction}
"""),
            ("user", "部下への挨拶と導入メッセージを生成してください。")
        ])
        
        chain = (
            {
                "user_context": lambda _: json.dumps(user_context, ensure_ascii=False),
                "abstract_instruction": lambda _: abstract_instruction
            }
            | prompt
            | self.llm
        )
        
        response = await chain.ainvoke({})
        return response.content
    
    async def _analyze_response(
        self,
        response: str,
        current_state: DialogueState,
        dialogue_history: List[Dict[str, Any]]
    ) -> ResponseAnalysis:
        """部下の回答を分析"""
        if self.use_mock or isinstance(self.llm, MockLLMProvider):
            # モック用の簡単な分析
            key_points = [response[:50] + "..." if len(response) > 50 else response]
            emotional_state = "前向き" if "できる" in response or "やりたい" in response else "不安"
            understanding_level = 8 if len(response) > 50 else 5
            success_patterns = ["A社との良好な関係"] if "A社" in response else []
            challenges = ["時間の確保"] if "時間" in response else ["目標達成"]
            
            return ResponseAnalysis(
                key_points=key_points,
                emotional_state=emotional_state,
                understanding_level=understanding_level,
                success_patterns=success_patterns,
                challenges=challenges,
                next_action_hint="次のステップへ"
            )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """部下の回答を深く分析してください。

現在の対話段階: {current_state}
対話履歴: {dialogue_history}

以下の観点で分析してください：
1. 回答から読み取れる重要なポイント
2. 部下の感情状態（困惑、自信、不安、意欲など）
3. 理解度（1-10のスケール）
4. 言及された成功パターンや良い事例
5. 言及された課題や障害
6. 次の質問で深掘りすべきポイント

{format_instructions}
"""),
            ("user", "次の回答を分析してください: {response}")
        ])
        
        chain = (
            {
                "current_state": lambda _: current_state.value,
                "dialogue_history": lambda _: json.dumps(
                    dialogue_history[-5:], ensure_ascii=False
                ),  # 直近5つの対話
                "response": lambda _: response,
                "format_instructions": lambda _: self.response_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.response_parser
        )
        
        return await chain.ainvoke({})
    
    async def _generate_socratic_question(
        self,
        session: Dict[str, Any],
        analysis: ResponseAnalysis,
        next_state: DialogueState
    ) -> SocraticQuestion:
        """ソクラテス式質問を生成"""
        if self.use_mock or isinstance(self.llm, MockLLMProvider):
            # モック用の事前定義質問
            mock_questions = {
                DialogueState.CURRENT_SITUATION: {
                    "question": "今月の売上状況と、現在の顧客対応の時間配分について詳しく教えてください。また、上司の指示をどのように理解していますか？",
                    "purpose": "現状を正確に把握し、課題を明確にする",
                    "expected_outcome": "売上状況、時間配分、指示の理解度を確認"
                },
                DialogueState.PROBLEM_ANALYSIS: {
                    "question": "これまでの顧客との関係で、特にうまくいっている例はありますか？その理由や、そこから生まれた成果について教えてください。",
                    "purpose": "成功体験を発見し、成功パターンを抽出する",
                    "expected_outcome": "具体的な成功事例と、その要因を特定"
                },
                DialogueState.SOLUTION_EXPLORATION: {
                    "question": "現在の顧客を「売上規模」と「関係の深さ」で分類すると、どのようなグループに分けられますか？どこから優先的にアプローチしますか？",
                    "purpose": "戦略的な顧客セグメンテーションと優先順位付け",
                    "expected_outcome": "効率的なアプローチ計画の策定"
                },
                DialogueState.ACTION_PLAN: {
                    "question": "具体的に「いつまでに」「何を」「どのように測定するか」を含めた目標を設定してください。短期（1ヶ月）と中期（3ヶ月）で考えてみませんか？",
                    "purpose": "SMART目標の設定と測定可能な指標の決定",
                    "expected_outcome": "実行可能で測定可能なアクションプラン"
                },
                DialogueState.EXECUTION_SUPPORT: {
                    "question": "この計画を実行する上で想定される課題や障害は何ですか？それらにどう対処し、どのように進捗を確認していきますか？",
                    "purpose": "実行時の障害予測と継続の仕組み作り",
                    "expected_outcome": "持続可能な実行計画の完成"
                }
            }
            
            question_data = mock_questions.get(next_state, {
                "question": "次のステップについて教えてください。",
                "purpose": "対話の継続",
                "expected_outcome": "情報の収集"
            })
            
            return SocraticQuestion(
                question=question_data["question"],
                purpose=question_data["purpose"],
                expected_outcome=question_data["expected_outcome"],
                follow_up_options=["詳しく聞く", "別の角度から質問する"]
            )
        
        state_prompts = {
            DialogueState.CURRENT_SITUATION: self._get_current_situation_prompt(),
            DialogueState.PROBLEM_ANALYSIS: self._get_problem_analysis_prompt(),
            DialogueState.SOLUTION_EXPLORATION: self._get_solution_exploration_prompt(),
            DialogueState.ACTION_PLAN: self._get_action_plan_prompt(),
            DialogueState.EXECUTION_SUPPORT: self._get_execution_support_prompt()
        }
        
        prompt = state_prompts.get(next_state, self._get_default_prompt())
        
        chain = (
            {
                "abstract_instruction": lambda _: session["abstract_instruction"],
                "dialogue_history": lambda _: json.dumps(
                    session["dialogue_history"][-10:], ensure_ascii=False
                ),
                "analysis": lambda _: json.dumps(analysis.dict(), ensure_ascii=False),
                "discovered_patterns": lambda _: json.dumps(
                    session["discovered_patterns"], ensure_ascii=False
                ),
                "format_instructions": lambda _: self.question_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.question_parser
        )
        
        return await chain.ainvoke({})
    
    def _get_current_situation_prompt(self) -> ChatPromptTemplate:
        """現状把握フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIコーチです。
現在は「現状把握フェーズ」です。

【目的】
- 部下の現在の売上状況を理解する
- 時間配分（新規vs既存）を把握する
- 上司の指示に対する理解度を確認する

【質問の原則】
- 事実を中立的に聞き出す
- 判断や批判を避ける
- 具体的な数字を引き出す
- 部下が答えやすい雰囲気を作る

【参考にすべき理想的な流れ】
1. まず売上状況を優しく聞く
2. 目標との差があれば、その原因を探る準備
3. 時間配分について具体的に聞く
4. 上司の指示への理解度を確認

上司の指示: {abstract_instruction}
対話履歴: {dialogue_history}
分析結果: {analysis}

{format_instructions}
"""),
            ("user", "現状を把握するための効果的な質問を生成してください。")
        ])
    
    def _get_problem_analysis_prompt(self) -> ChatPromptTemplate:
        """課題分析フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIコーチです。
現在は「課題分析フェーズ」です。

【目的】
- 抽象的な指示を具体化する手がかりを見つける
- 部下の成功体験を発見する
- 成功パターンから学習させる
- 自信を高めながら気づきを促す

【質問の原則】
- 「うまくいっている例」から始める（強みベース）
- 具体的な成功事例を聞き出す
- 成功の理由を部下自身に考えさせる
- 成果（売上、紹介など）を具体的に聞く
- 他への応用可能性を探る

【重要】
部下が「分からない」と言った場合、それを共感的に受け止め、
一緒に考える姿勢を示しながら、成功事例を探してください。

上司の指示: {abstract_instruction}
対話履歴: {dialogue_history}
分析結果: {analysis}
発見されたパターン: {discovered_patterns}

{format_instructions}
"""),
            ("user", "成功体験を発見し、課題を分析する質問を生成してください。")
        ])
    
    def _get_solution_exploration_prompt(self) -> ChatPromptTemplate:
        """ソリューション探索フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIコーチです。
現在は「ソリューション探索フェーズ」です。

【目的】
- 成功パターンを他の顧客に応用する方法を考えさせる
- 効率的なアプローチを設計する
- 顧客の優先順位付けを支援する
- 現実的な計画を立てる

【質問の原則】
- リソース制約（時間）を認識させる
- 顧客セグメンテーションを促す
- 「売上規模」×「関係の深さ」で分類させる
- 最も効果的なターゲットを特定させる
- 具体的なアプローチ方法を考えさせる

【理想的な流れ】
1. 時間制約を共感的に認める
2. 顧客の分類を提案
3. 優先順位付けを支援
4. 具体的なアクションを引き出す

上司の指示: {abstract_instruction}
対話履歴: {dialogue_history}
分析結果: {analysis}
発見されたパターン: {discovered_patterns}

{format_instructions}
"""),
            ("user", "戦略的なソリューションを探索する質問を生成してください。")
        ])
    
    def _get_action_plan_prompt(self) -> ChatPromptTemplate:
        """アクションプラン作成フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIコーチです。
現在は「アクションプラン作成フェーズ」です。

【目的】
- SMART目標を設定させる
- 測定可能な指標を決める
- 実行可能な計画を作る
- 売上への影響を明確にする

【SMART目標の要素】
- Specific（具体的）: 何を、誰に
- Measurable（測定可能）: 数値化
- Achievable（達成可能）: 現実的
- Relevant（関連性）: 上司の指示と整合
- Time-bound（期限）: いつまでに

【質問の原則】
- 曖昧な表現を具体化させる
- 数値目標を設定させる
- 短期（1ヶ月）と中期（3ヶ月）の目標
- 測定方法を明確にする
- 前向きな雰囲気を保つ

上司の指示: {abstract_instruction}
対話履歴: {dialogue_history}
分析結果: {analysis}
発見されたパターン: {discovered_patterns}

{format_instructions}
"""),
            ("user", "SMART目標を設定する質問を生成してください。")
        ])
    
    def _get_execution_support_prompt(self) -> ChatPromptTemplate:
        """実行支援フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIコーチです。
現在は「実行支援フェーズ」です。

【目的】
- 実行時の障害を予測する
- 具体的な解決策を考えさせる
- 継続の仕組みを作る
- 進捗確認方法を決める

【質問の原則】
- 想定される課題を聞き出す
- 各課題への対策を一緒に考える
- 実行可能な解決策を導く
- チェックポイントを設定する
- 自信を持って実行できるよう励ます

【重要な観点】
- 時間確保の具体策
- モチベーション維持の方法
- 進捗測定のタイミング
- 上司への報告方法

上司の指示: {abstract_instruction}
対話履歴: {dialogue_history}
分析結果: {analysis}
発見されたパターン: {discovered_patterns}

{format_instructions}
"""),
            ("user", "実行を支援する質問を生成してください。")
        ])
    
    def _get_default_prompt(self) -> ChatPromptTemplate:
        """デフォルトプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIコーチです。

ソクラテス式質問法を使って、部下の成長を促してください。

上司の指示: {abstract_instruction}
対話履歴: {dialogue_history}
分析結果: {analysis}

{format_instructions}
"""),
            ("user", "適切な質問を生成してください。")
        ])
    
    def _update_session_insights(
        self,
        session: Dict[str, Any],
        analysis: ResponseAnalysis
    ):
        """セッションの洞察を更新"""
        # 成功パターンを記録
        if analysis.success_patterns:
            if "success_patterns" not in session["discovered_patterns"]:
                session["discovered_patterns"]["success_patterns"] = []
            session["discovered_patterns"]["success_patterns"].extend(
                analysis.success_patterns
            )
        
        # 課題を記録
        if analysis.challenges:
            if "challenges" not in session["discovered_patterns"]:
                session["discovered_patterns"]["challenges"] = []
            session["discovered_patterns"]["challenges"].extend(
                analysis.challenges
            )
        
        # 感情状態の推移を記録
        if "emotional_journey" not in session["discovered_patterns"]:
            session["discovered_patterns"]["emotional_journey"] = []
        session["discovered_patterns"]["emotional_journey"].append({
            "state": session["state"].value,
            "emotion": analysis.emotional_state,
            "understanding_level": analysis.understanding_level
        })
    
    def _determine_next_state(
        self,
        session: Dict[str, Any],
        analysis: ResponseAnalysis
    ) -> DialogueState:
        """次の状態を決定"""
        current_state = session["state"]
        dialogue_count = len([
            h for h in session["dialogue_history"]
            if h["role"] == "user" and h["state"] == current_state.value
        ])
        
        # 状態遷移のロジック
        transitions = {
            DialogueState.CURRENT_SITUATION: {
                "next": DialogueState.PROBLEM_ANALYSIS,
                "condition": dialogue_count >= 2 or analysis.understanding_level >= 7
            },
            DialogueState.PROBLEM_ANALYSIS: {
                "next": DialogueState.SOLUTION_EXPLORATION,
                "condition": len(analysis.success_patterns) > 0 or dialogue_count >= 2
            },
            DialogueState.SOLUTION_EXPLORATION: {
                "next": DialogueState.ACTION_PLAN,
                "condition": "顧客" in analysis.next_action_hint or dialogue_count >= 2
            },
            DialogueState.ACTION_PLAN: {
                "next": DialogueState.EXECUTION_SUPPORT,
                "condition": any(
                    keyword in " ".join(analysis.key_points)
                    for keyword in ["目標", "訪問", "測定", "%"]
                ) or dialogue_count >= 2
            },
            DialogueState.EXECUTION_SUPPORT: {
                "next": DialogueState.SUMMARY,
                "condition": dialogue_count >= 1
            }
        }
        
        transition = transitions.get(current_state)
        if transition and transition["condition"]:
            return transition["next"]
        
        return current_state
    
    def _calculate_progress(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """進捗を計算"""
        states = [
            DialogueState.GREETING,
            DialogueState.CURRENT_SITUATION,
            DialogueState.PROBLEM_ANALYSIS,
            DialogueState.SOLUTION_EXPLORATION,
            DialogueState.ACTION_PLAN,
            DialogueState.EXECUTION_SUPPORT,
            DialogueState.SUMMARY
        ]
        
        current_index = states.index(session["state"])
        total_states = len(states) - 2  # GREETING と SUMMARY を除く
        
        completed_states = len(set(
            h["state"] for h in session["dialogue_history"]
            if h["role"] == "assistant"
        )) - 1  # GREETING を除く
        
        return {
            "current_state": session["state"].value,
            "completed_states": completed_states,
            "total_states": total_states,
            "percentage": int((completed_states / total_states) * 100),
            "dialogue_count": len(session["dialogue_history"])
        }
    
    async def _generate_summary(
        self,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最終的なサマリーとアクションプランを生成"""
        if self.use_mock or isinstance(self.llm, MockLLMProvider):
            # モック用の事前定義サマリー
            return {
                "message": """素晴らしい対話でした！上司の抽象的な指示「顧客との関係を深めて売上を伸ばす」を、具体的で実行可能なアクションプランに変換できました。

あなたの成功体験（A社との良好な関係）を基に、戦略的なアプローチを設計し、測定可能な目標を設定することができました。

この計画を実行することで、必ず成果が現れます。応援しています！""",
                "interpretation": "顧客との関係強化により信頼を構築し、それを売上向上につなげること",
                "action_plan": {
                    "short_term_goals": [
                        {
                            "goal": "優先顧客との関係強化",
                            "actions": ["B社・C社への月2回訪問", "担当者の関心事3つずつ把握"],
                            "deadline": "来月末",
                            "metrics": "訪問回数、関心事把握数"
                        }
                    ],
                    "mid_term_goals": [
                        {
                            "goal": "売上10%向上",
                            "deadline": "3ヶ月後",
                            "metrics": "月次売上額"
                        }
                    ],
                    "success_patterns": ["A社との良好な関係構築パターンの活用"],
                    "challenges_and_solutions": [
                        {
                            "challenge": "時間の確保",
                            "solution": "新規開拓時間の一部を既存フォローに振り分け"
                        }
                    ],
                    "progress_check": {
                        "weekly": "訪問実績と関係構築進捗の確認",
                        "monthly": "売上数値と目標達成度の評価"
                    }
                },
                "insights": {
                    "strengths": ["成功体験の活用能力", "現実的な目標設定力"],
                    "growth_areas": ["戦略的思考", "時間管理スキル"],
                    "confidence_level": "対話を通じて自信が向上し、具体的な行動への意欲が高まった"
                }
            }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """対話セッションの内容から、包括的なサマリーとアクションプランを作成してください。

上司の指示: {abstract_instruction}
対話履歴: {dialogue_history}
発見されたパターン: {discovered_patterns}

【サマリーに含めるべき要素】
1. 上司の抽象的な指示の具体的な解釈
2. 発見された成功パターンとその活用方法
3. 設定されたSMART目標
4. 実行計画と測定方法
5. 予想される課題と対策
6. 励ましのメッセージ

【アクションプランの構造】
- 短期目標（1ヶ月）
- 中期目標（3ヶ月）
- 具体的なアクション
- 成功指標
- 進捗確認方法

JSON形式で以下の構造で回答してください：
{{
    "message": "部下への最終メッセージ（励ましと要約）",
    "interpretation": "上司の指示の具体的解釈",
    "action_plan": {{
        "short_term_goals": [
            {{
                "goal": "目標",
                "actions": ["アクション1", "アクション2"],
                "deadline": "期限",
                "metrics": "測定指標"
            }}
        ],
        "mid_term_goals": [...],
        "success_patterns": ["活用すべき成功パターン"],
        "challenges_and_solutions": [
            {{
                "challenge": "課題",
                "solution": "解決策"
            }}
        ],
        "progress_check": {{
            "weekly": "週次チェック項目",
            "monthly": "月次チェック項目"
        }}
    }},
    "insights": {{
        "strengths": ["部下の強み"],
        "growth_areas": ["成長の機会"],
        "confidence_level": "自信度の変化"
    }}
}}
"""),
            ("user", "セッションのサマリーとアクションプランを生成してください。")
        ])
        
        chain = (
            {
                "abstract_instruction": lambda _: session["abstract_instruction"],
                "dialogue_history": lambda _: json.dumps(session["dialogue_history"], ensure_ascii=False),
                "discovered_patterns": lambda _: json.dumps(session["discovered_patterns"], ensure_ascii=False)
            }
            | prompt
            | self.llm
        )
        
        response = await chain.ainvoke({})
        
        # JSONを抽出してパース
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "message": response.content,
                "action_plan": {},
                "insights": {}
            }
        
        return result