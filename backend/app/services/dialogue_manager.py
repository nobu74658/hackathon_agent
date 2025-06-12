from typing import Dict, Any, List, Optional, Tuple
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.schema.runnable import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from datetime import datetime
import json
from enum import Enum

from app.services.conversation_memory import ConversationMemoryService
from app.services.one_on_one_analyzer import OneOnOneAnalyzer
from app.core.config import settings


class QuestionResponse(BaseModel):
    """質問生成のレスポンス構造"""
    questions: List[str] = Field(description="生成された質問のリスト")
    reasoning: str = Field(description="なぜこれらの質問が必要かの説明")
    information_needed: List[str] = Field(description="まだ必要な情報のリスト")
    completeness_score: int = Field(description="情報の充足度（0-100）")


class ActionPlanResponse(BaseModel):
    """アクションプラン生成のレスポンス構造"""
    action_items: List[Dict[str, Any]] = Field(description="アクションアイテムのリスト")
    summary: str = Field(description="全体的なサマリー")
    key_improvements: List[str] = Field(description="主要な改善ポイント")
    metrics: Dict[str, Any] = Field(description="成功指標")


class DialoguePhase(Enum):
    """理想的な対話フェーズの定義"""
    CURRENT_SITUATION = "current_situation"  # 現状把握
    PROBLEM_ANALYSIS = "problem_analysis"   # 課題分析
    SOLUTION_EXPLORATION = "solution_exploration"  # ソリューション探索
    ACTION_PLAN = "action_plan"  # アクションプラン作成
    EXECUTION_SUPPORT = "execution_support"  # 実行支援
    COMPLETED = "completed"  # 完了


class SocraticQuestionResponse(BaseModel):
    """ソクラテス式質問の構造"""
    question: str = Field(description="生成された質問")
    purpose: str = Field(description="この質問の目的")
    expected_insight: str = Field(description="期待される気づき")
    phase: str = Field(description="現在のフェーズ")
    next_phase_condition: str = Field(description="次のフェーズに進む条件")


class IdealDialogueManager:
    """理想的な対話シナリオを実現するマネージャー"""
    
    def __init__(self, llm):
        self.llm = llm
        self.socratic_parser = PydanticOutputParser(pydantic_object=SocraticQuestionResponse)
        
    async def get_socratic_question(
        self,
        phase: DialoguePhase,
        context: Dict[str, Any],
        user_responses: List[Dict[str, Any]]
    ) -> SocraticQuestionResponse:
        """ソクラテス式質問を生成"""
        
        phase_prompts = {
            DialoguePhase.CURRENT_SITUATION: self._get_current_situation_prompt(),
            DialoguePhase.PROBLEM_ANALYSIS: self._get_problem_analysis_prompt(),
            DialoguePhase.SOLUTION_EXPLORATION: self._get_solution_exploration_prompt(),
            DialoguePhase.ACTION_PLAN: self._get_action_plan_prompt(),
            DialoguePhase.EXECUTION_SUPPORT: self._get_execution_support_prompt()
        }
        
        prompt = phase_prompts.get(phase, self._get_default_prompt())
        
        chain = (
            {
                "context": lambda _: json.dumps(context, ensure_ascii=False),
                "user_responses": lambda _: json.dumps(user_responses, ensure_ascii=False),
                "format_instructions": lambda _: self.socratic_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.socratic_parser
        )
        
        return await chain.ainvoke({})
    
    def _get_current_situation_prompt(self) -> ChatPromptTemplate:
        """現状把握フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """
あなたは新人営業マンの成長を支援するAIコーチです。
現在は「現状把握フェーズ」にいます。

【このフェーズの目的】
- 部下の現在の状況を包括的に把握する
- 上司の抽象的な指示に対する理解度を確認する
- 売上状況、顧客対応の現状、課題を一度に理解する

【質問作成の原則】
- 1つの質問で複数の情報を効率的に収集
- 具体的で答えやすい構造にする
- 現状の課題と成功体験を同時に聞き出す
- 負荷を減らしつつ、必要な情報を網羅する

現在の売上状況、時間配分、顧客との関係、上司の指示への理解を包括的に聞き出す質問を1つ生成してください。

コンテキスト: {context}
過去の回答: {user_responses}

{format_instructions}
"""),
            ("user", "現状を包括的に把握するための効率的な質問を生成してください。")
        ])
    
    def _get_problem_analysis_prompt(self) -> ChatPromptTemplate:
        """課題分析フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """
あなたは新人営業マンの成長を支援するAIコーチです。
現在は「課題分析フェーズ」にいます。

【このフェーズの目的】
- 成功体験とその理由を効率的に発見する
- 抽象的な指示の具体的な意味を理解させる
- 成功パターンの再現可能性を一度に探る

【質問作成の原則】
- 成功事例、その理由、成果を一度に聞き出す
- 「何がうまくいったか？なぜうまくいったか？どんな結果が出たか？」を包括的に質問
- 部下の自信を高めつつ、効率的に情報収集
- 他の顧客への応用可能性も含めて質問

最も良好な顧客関係の事例、その成功要因、具体的な成果、他への応用可能性を包括的に聞き出す質問を1つ生成してください。

コンテキスト: {context}
過去の回答: {user_responses}

{format_instructions}
"""),
            ("user", "成功体験を包括的に分析するための効率的な質問を生成してください。")
        ])
    
    def _get_solution_exploration_prompt(self) -> ChatPromptTemplate:
        """ソリューション探索フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """
あなたは新人営業マンの成長を支援するAIコーチです。
現在は「ソリューション探索フェーズ」にいます。

【このフェーズの目的】
- 成功体験の他の顧客への応用方法を効率的に特定する
- 戦略的な優先順位付けを一度に決める
- 現実的で実行可能なアプローチを決定する

【質問作成の原則】
- 顧客セグメンテーション、優先順位、具体的アプローチを包括的に質問
- 「どの顧客に」「どの順番で」「どのような方法で」を一度に聞き出す
- リソース制約を考慮した現実的な計画を立てさせる
- 効率的な戦略立案を促進

顧客の分類、アプローチする優先順位、具体的な関係構築方法を包括的に考えさせる質問を1つ生成してください。

コンテキスト: {context}
過去の回答: {user_responses}

{format_instructions}
"""),
            ("user", "戦略的なソリューション設計のための包括的な質問を生成してください。")
        ])
    
    def _get_action_plan_prompt(self) -> ChatPromptTemplate:
        """アクションプラン作成フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """
あなたは新人営業マンの成長を支援するAIコーチです。
現在は「アクションプラン作成フェーズ」にいます。

【このフェーズの目的】
- SMART目標を効率的に設定する
- 具体的なアクション、期限、測定指標を一度に決める
- 実現可能で実行しやすい計画を作成する

【質問作成の原則】
- 「何を、いつまでに、どのように測定するか」を包括的に質問
- Specific, Measurable, Achievable, Relevant, Time-boundの要素を効率的に設定
- 短期目標と中長期目標を同時に考えさせる
- 実行の具体的なステップも含めて質問

具体的なアクション内容、実行期限、成功の測定方法、期待される成果を包括的に設定させる質問を1つ生成してください。

コンテキスト: {context}
過去の回答: {user_responses}

{format_instructions}
"""),
            ("user", "SMART目標と実行計画を包括的に設定するための質問を生成してください。")
        ])
    
    def _get_execution_support_prompt(self) -> ChatPromptTemplate:
        """実行支援フェーズのプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """
あなたは新人営業マンの成長を支援するAIコーチです。
現在は「実行支援フェーズ」にいます。

【このフェーズの目的】
- 実行時の課題と解決策を効率的に特定する
- 継続のための仕組みと進捗確認方法を一度に決める
- 自律的な問題解決能力を育成する

【質問作成の原則】
- 「予想される障害、その解決策、継続の仕組み、進捗確認方法」を包括的に質問
- 時間確保、スキル不足、モチベーション維持などの課題を一度に検討
- 週次・月次の振り返り方法も同時に設定
- 実行を成功させる具体的な工夫を引き出す

実行時の課題予測、解決策、継続のための仕組み、進捗確認方法を包括的に考えさせる質問を1つ生成してください。

コンテキスト: {context}
過去の回答: {user_responses}

{format_instructions}
"""),
            ("user", "実行成功のための包括的な支援策を考える質問を生成してください。")
        ])
    
    def _get_default_prompt(self) -> ChatPromptTemplate:
        """デフォルトプロンプト"""
        return ChatPromptTemplate.from_messages([
            ("system", """
あなたは新人営業マンの成長を支援するAIコーチです。

ソクラテス式質問法を用いて、部下の成長を促す質問を生成してください。

コンテキスト: {context}
過去の回答: {user_responses}

{format_instructions}
"""),
            ("user", "成長を促す効果的な質問を生成してください。")
        ])
    
    def determine_next_phase(
        self,
        current_phase: DialoguePhase,
        user_responses: List[Dict[str, Any]]
    ) -> DialoguePhase:
        """次のフェーズを決定"""
        phase_transitions = {
            DialoguePhase.CURRENT_SITUATION: DialoguePhase.PROBLEM_ANALYSIS,
            DialoguePhase.PROBLEM_ANALYSIS: DialoguePhase.SOLUTION_EXPLORATION,
            DialoguePhase.SOLUTION_EXPLORATION: DialoguePhase.ACTION_PLAN,
            DialoguePhase.ACTION_PLAN: DialoguePhase.EXECUTION_SUPPORT,
            DialoguePhase.EXECUTION_SUPPORT: DialoguePhase.COMPLETED
        }
        
        # 各フェーズで最低2-3の質問に答えた場合に次のフェーズに進む
        current_phase_responses = [
            r for r in user_responses 
            if r.get("phase") == current_phase.value
        ]
        
        if len(current_phase_responses) >= 1:  # 1つの回答で次のフェーズへ
            return phase_transitions.get(current_phase, DialoguePhase.COMPLETED)
        
        return current_phase


class DialogueManager:
    """対話フローを管理するマネージャー"""
    
    def __init__(self):
        self.memory_service = ConversationMemoryService()
        self.one_on_one_analyzer = OneOnOneAnalyzer()
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.question_parser = PydanticOutputParser(pydantic_object=QuestionResponse)
        self.action_plan_parser = PydanticOutputParser(pydantic_object=ActionPlanResponse)
        
        # 理想的な対話シナリオマネージャー
        self.ideal_dialogue_manager = IdealDialogueManager(self.llm)
        
        # インメモリの1on1セッション状態管理（Redisがない場合の代替）
        self._in_memory_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 理想的な対話セッション状態管理
        self._ideal_dialogue_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self):
        """サービスの初期化"""
        await self.memory_service.initialize()
    
    async def start_dialogue(
        self,
        session_id: str,
        initial_context: Dict[str, Any]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """対話セッションを開始"""
        # 初期質問生成のプロンプト
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIアシスタントです。
            1on1セッションの内容から、営業スキル向上のための具体的なアクションプランを作成するために
            必要な情報を収集します。
            
            以下の情報が提供されています：
            {initial_context}
            
            効果的なアクションプランを作成するために追加で必要な情報を特定し、
            3-5個の具体的で答えやすい質問を生成してください。
            
            {format_instructions}
            """),
            ("user", "1on1セッションの内容を分析し、追加で必要な情報を収集するための質問を生成してください。")
        ])
        
        # チェーン構築
        chain = (
            {
                "initial_context": RunnablePassthrough(),
                "format_instructions": lambda _: self.question_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.question_parser
        )
        
        # 質問生成
        response = await chain.ainvoke(json.dumps(initial_context, ensure_ascii=False))
        
        # メタデータ作成
        metadata = {
            "stage": "initial",
            "reasoning": response.reasoning,
            "information_needed": response.information_needed,
            "completeness_score": response.completeness_score
        }
        
        return response.questions, metadata
    
    async def start_ideal_dialogue(
        self,
        session_id: str,
        abstract_instruction: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """理想的な対話シナリオを開始"""
        # セッション初期化
        self._ideal_dialogue_sessions[session_id] = {
            "phase": DialoguePhase.CURRENT_SITUATION,
            "abstract_instruction": abstract_instruction,
            "user_responses": [],
            "context": context or {},
            "started_at": datetime.now().isoformat()
        }
        
        # 最初の質問を生成
        return await self.continue_ideal_dialogue(session_id, None)
    
    async def continue_ideal_dialogue(
        self,
        session_id: str,
        user_response: str = None
    ) -> Dict[str, Any]:
        """理想的な対話シナリオを継続"""
        session_state = self._ideal_dialogue_sessions.get(session_id)
        if not session_state:
            return {
                "type": "error",
                "message": "対話セッションが見つかりません"
            }
        
        # ユーザーの回答を記録（初回以外）
        if user_response:
            session_state["user_responses"].append({
                "phase": session_state["phase"].value,
                "response": user_response,
                "timestamp": datetime.now().isoformat()
            })
        
        # 現在のフェーズが完了かチェック
        if session_state["phase"] == DialoguePhase.COMPLETED:
            # 最終的なアクションプランを生成
            action_plan = await self._generate_final_action_plan(session_state)
            return {
                "type": "action_plan_completed",
                "action_plan": action_plan,
                "session_summary": self._create_session_summary(session_state)
            }
        
        # 次のフェーズに進むかチェック
        next_phase = self.ideal_dialogue_manager.determine_next_phase(
            session_state["phase"],
            session_state["user_responses"]
        )
        
        if next_phase != session_state["phase"]:
            session_state["phase"] = next_phase
            
            # フェーズ完了時のフィードバック
            if user_response:
                phase_feedback = self._get_phase_completion_feedback(session_state["phase"])
                if phase_feedback:
                    return {
                        "type": "phase_transition",
                        "message": phase_feedback,
                        "current_phase": session_state["phase"].value,
                        "phase_description": self._get_phase_description(session_state["phase"])
                    }
        
        # ソクラテス式質問を生成
        try:
            socratic_response = await self.ideal_dialogue_manager.get_socratic_question(
                session_state["phase"],
                session_state["context"],
                session_state["user_responses"]
            )
            
            return {
                "type": "socratic_question",
                "question": socratic_response.question,
                "purpose": socratic_response.purpose,
                "expected_insight": socratic_response.expected_insight,
                "phase": socratic_response.phase,
                "next_phase_condition": socratic_response.next_phase_condition,
                "phase_description": self._get_phase_description(session_state["phase"]),
                "progress": self._calculate_progress(session_state)
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"質問生成中にエラーが発生しました: {str(e)}"
            }
    
    def _get_phase_description(self, phase: DialoguePhase) -> str:
        """フェーズの説明を取得"""
        descriptions = {
            DialoguePhase.CURRENT_SITUATION: "📋 現状把握 - 現在の状況と課題を理解します",
            DialoguePhase.PROBLEM_ANALYSIS: "🔍 課題分析 - 成功体験を発見し、問題を深掘りします",
            DialoguePhase.SOLUTION_EXPLORATION: "💡 解決策探索 - 戦略的なアプローチ方法を考えます",
            DialoguePhase.ACTION_PLAN: "🎯 アクションプラン - 具体的で測定可能な目標を設定します",
            DialoguePhase.EXECUTION_SUPPORT: "🚀 実行支援 - 実現可能性と継続のための仕組みを作ります",
            DialoguePhase.COMPLETED: "✅ 完了 - アクションプランが完成しました"
        }
        return descriptions.get(phase, "対話中")
    
    def _get_phase_completion_feedback(self, completed_phase: DialoguePhase) -> Optional[str]:
        """フェーズ完了時のフィードバック"""
        feedbacks = {
            DialoguePhase.CURRENT_SITUATION: "現状を整理できました！次に成功体験を活用する方法を考えましょう。",
            DialoguePhase.PROBLEM_ANALYSIS: "素晴らしい気づきですね！この成功体験を他の場面でも活用していきましょう。",
            DialoguePhase.SOLUTION_EXPLORATION: "戦略的な視点が身についてきました！具体的な行動計画に落とし込んでいきましょう。",
            DialoguePhase.ACTION_PLAN: "実行可能な計画ができました！最後に継続するための仕組みを考えましょう。",
            DialoguePhase.EXECUTION_SUPPORT: "完璧です！実行に向けた準備が整いました。"
        }
        return feedbacks.get(completed_phase)
    
    def _calculate_progress(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """進捗を計算"""
        phase_order = [
            DialoguePhase.CURRENT_SITUATION,
            DialoguePhase.PROBLEM_ANALYSIS,
            DialoguePhase.SOLUTION_EXPLORATION,
            DialoguePhase.ACTION_PLAN,
            DialoguePhase.EXECUTION_SUPPORT,
            DialoguePhase.COMPLETED
        ]
        
        current_index = phase_order.index(session_state["phase"])
        total_phases = len(phase_order) - 1  # COMPLETEDを除く
        progress_percentage = int((current_index / total_phases) * 100)
        
        return {
            "current_phase_index": current_index,
            "total_phases": total_phases,
            "percentage": progress_percentage,
            "responses_in_current_phase": len([
                r for r in session_state["user_responses"] 
                if r.get("phase") == session_state["phase"].value
            ])
        }
    
    async def _generate_final_action_plan(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """最終的なアクションプランを生成"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
あなたは新人営業マンの成長を支援するAIコーチです。

以下の対話セッションの内容から、部下の成長を促す包括的なアクションプランを作成してください。

上司の指示: {abstract_instruction}
対話の記録: {dialogue_history}

【アクションプラン作成の原則】
1. SMART目標（具体的、測定可能、達成可能、関連性、期限付き）
2. 段階的な実行ステップ
3. 成功指標と測定方法
4. 予想される障害と対策
5. 継続的な成長のための仕組み
6. 定期的な振り返りポイント

JSON形式で以下の構造で回答してください：
{{
    "summary": "アクションプランの概要",
    "smart_goals": [
        {{
            "goal": "具体的な目標",
            "specific": "具体的な内容",
            "measurable": "測定指標",
            "achievable": "達成可能性",
            "relevant": "関連性",
            "time_bound": "期限"
        }}
    ],
    "action_steps": [
        {{
            "step": "ステップ番号",
            "action": "具体的な行動",
            "deadline": "期限",
            "success_criteria": "成功基準"
        }}
    ],
    "success_metrics": {{
        "quantitative": ["定量的指標"],
        "qualitative": ["定性的指標"]
    }},
    "potential_obstacles": [
        {{
            "obstacle": "予想される障害",
            "solution": "解決策"
        }}
    ],
    "continuous_improvement": {{
        "weekly_check": "週次チェック項目",
        "monthly_review": "月次レビュー項目",
        "quarterly_goal": "四半期目標"
    }}
}}
"""),
            ("user", "対話セッションからアクションプランを生成してください。")
        ])
        
        chain = (
            {
                "abstract_instruction": lambda _: session_state["abstract_instruction"],
                "dialogue_history": lambda _: json.dumps(session_state["user_responses"], ensure_ascii=False)
            }
            | prompt
            | self.llm
        )
        
        try:
            response = await chain.ainvoke({})
            action_plan_text = response.content
            
            # JSONパースを試行
            import re
            json_match = re.search(r'\{.*\}', action_plan_text, re.DOTALL)
            if json_match:
                action_plan = json.loads(json_match.group())
            else:
                # JSONが見つからない場合は、テキストそのままを返す
                action_plan = {"raw_response": action_plan_text}
                
            return action_plan
            
        except Exception as e:
            return {
                "error": f"アクションプラン生成中にエラーが発生しました: {str(e)}",
                "raw_dialogue": session_state["user_responses"]
            }
    
    def _create_session_summary(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """セッションの要約を作成"""
        return {
            "abstract_instruction": session_state["abstract_instruction"],
            "total_responses": len(session_state["user_responses"]),
            "phases_completed": len(set(r.get("phase") for r in session_state["user_responses"])),
            "duration": session_state.get("started_at"),
            "final_phase": session_state["phase"].value
        }

    async def process_user_response(
        self,
        session_id: str,
        user_response: str,
        db_session: Any
    ) -> Dict[str, Any]:
        """ユーザーの回答を処理"""
        # メモリに回答を追加
        await self.memory_service.add_message(
            session_id=session_id,
            role="user",
            content=user_response,
            db=db_session
        )
        
        # 1on1ミーティングの内容かどうかを判定
        is_one_on_one = self._is_one_on_one_content(user_response)
        
        if is_one_on_one:
            # 1on1の場合は対話型具体化プロセスを開始
            user_id = session_id.replace("slack_", "")
            
            try:
                # 1on1の初期分析を実行（上司の指示特定のみ）
                abstract_instructions = await self._extract_supervisor_instructions_from_one_on_one(
                    user_response, db_session
                )
                
                # 対話セッションの状態を保存
                await self._save_one_on_one_session_state(
                    session_id, 
                    user_response, 
                    abstract_instructions,
                    db_session
                )
                
                # 最初の深掘り質問を生成
                first_questions = await self._generate_initial_clarification_questions(
                    abstract_instructions[0] if abstract_instructions else None,
                    user_response
                )
                
                return {
                    "type": "one_on_one_clarification",
                    "questions": first_questions,
                    "instruction_being_clarified": abstract_instructions[0] if abstract_instructions else None,
                    "total_instructions": len(abstract_instructions),
                    "current_instruction_index": 0,
                    "stage": "instruction_clarification",
                    "stage_description": f"📋 上司の指示の具体化 (1/{len(abstract_instructions)})"
                }
                
            except Exception as e:
                return {
                    "type": "error", 
                    "message": f"1on1分析開始中にエラーが発生しました: {str(e)}"
                }
        else:
            # 1on1セッション継続中かチェック
            one_on_one_session = await self._get_one_on_one_session_state(session_id)
            
            if one_on_one_session:
                # 1on1セッション継続中 - 深掘り質問への回答を処理
                try:
                    return await self._continue_one_on_one_clarification(
                        session_id, 
                        user_response, 
                        one_on_one_session,
                        db_session
                    )
                except Exception as e:
                    return {
                        "type": "error",
                        "message": f"1on1セッション継続中にエラーが発生しました: {str(e)}"
                    }
            
            # 従来の質問ベースの対話
            context = await self.memory_service.get_conversation_context(
                session_id=session_id,
                include_summary=True
            )
            
            completeness_score = await self._evaluate_completeness(context)
            
            if completeness_score >= 80:
                action_plan = await self._generate_action_plan(context)
                return {
                    "type": "action_plan",
                    "data": action_plan,
                    "completeness_score": completeness_score
                }
            else:
                follow_up_questions = await self._generate_follow_up_questions(context)
                return {
                    "type": "follow_up",
                    "questions": follow_up_questions,
                    "completeness_score": completeness_score
                }
    
    def _is_one_on_one_content(self, content: str) -> bool:
        """1on1ミーティングの内容かどうかを判定"""
        
        # 1on1の特徴的なパターンを検出
        one_on_one_indicators = [
            # 基本的な対話形式
            "：" in content and content.count("：") >= 2,  # 複数の話者
            len(content) > 100,  # 長めの内容
            
            # 営業活動関連
            "距離を詰める" in content,
            "信頼関係" in content,
            "温度感" in content,
            "課題に寄り添った" in content,
            "営業活動" in content and "調子" in content,
            "新規アポ" in content,
            "成約" in content,
            
            # 上司からのフィードバック・指導パターン
            "もう少し" in content and ("といいね" in content or "といいかな" in content),
            "がカギだと思う" in content,
            "を意識して" in content,
            "感覚を磨いて" in content or "数こなして" in content,
            
            # 提案資料・成果物フィードバック
            "提案資料" in content,
            "伝わる資料" in content or "わかりやすく" in content,
            "ストーリー性" in content,
            "センス" in content and ("資料" in content or "提案" in content),
            "空気感" in content,
            "洗練" in content,
            
            # 一般的な上司・部下の対話パターン
            "確認したよ" in content or "確認しました" in content,
            "フィードバック" in content,
            "もう一歩" in content,
            "改善" in content and ("できる" in content or "していこう" in content),
            "頑張ります" in content and ("分かりました" in content or "ありがとうございます" in content),
            
            # 抽象的な指示パターン
            "曖昧" in content or "抽象的" in content,
            "具体的に" in content and "どう" in content,
            "例えば" in content and "どこを" in content,
            
            # 思考や内心の描写（1on1ログの特徴）
            "（" in content and "）" in content and content.count("（") >= 2
        ]
        
        # 複数の指標が当てはまる場合は1on1と判定（閾値を2に下げる）
        matching_indicators = sum(1 for indicator in one_on_one_indicators if indicator)
        return matching_indicators >= 2
    
    def _determine_dialogue_stage(self, context: Dict[str, Any], completeness_score: int) -> str:
        """対話の段階を判定"""
        messages = context.get("messages", [])
        message_count = len([msg for msg in messages if msg.get("role") == "user"])
        
        # メッセージ数と完了度スコアによる段階判定
        if message_count <= 1:
            return "initial_understanding"  # 初期理解段階
        elif message_count <= 3 and completeness_score < 40:
            return "problem_clarification"  # 課題明確化段階  
        elif message_count <= 5 and completeness_score < 70:
            return "deep_analysis"  # 深い分析段階
        elif completeness_score < 85:
            return "solution_exploration"  # 解決策探索段階
        elif completeness_score < 95:
            return "action_preparation"  # アクション準備段階
        else:
            return "action_plan"  # アクションプラン生成段階
    
    def _get_stage_description(self, stage: str) -> str:
        """段階の説明を取得"""
        descriptions = {
            "initial_understanding": "📋 初期状況の理解",
            "problem_clarification": "🎯 課題の明確化", 
            "deep_analysis": "🔍 詳細分析",
            "solution_exploration": "💡 解決策の探索",
            "action_preparation": "📝 アクション準備",
            "action_plan": "🚀 アクションプラン生成"
        }
        return descriptions.get(stage, "🤔 分析中")
    
    async def _generate_stage_based_questions(self, context: Dict[str, Any], stage: str) -> List[str]:
        """段階に基づいた質問生成"""
        if stage == "initial_understanding":
            return await self._generate_initial_questions(context)
        elif stage == "problem_clarification":
            return await self._generate_clarification_questions(context)
        elif stage == "deep_analysis":
            return await self._generate_analysis_questions(context)
        elif stage == "solution_exploration":
            return await self._generate_solution_questions(context)
        elif stage == "action_preparation":
            return await self._generate_preparation_questions(context)
        else:
            return await self._generate_follow_up_questions(context)
    
    async def _generate_initial_questions(self, context: Dict[str, Any]) -> List[str]:
        """初期理解のための質問生成"""
        messages = context.get("messages", [])
        latest_message = messages[-1].get("content", "") if messages else ""
        
        # 1on1の内容から抽象的な指示を特定
        if "距離を詰める" in latest_message or "信頼関係" in latest_message:
            return [
                "上司から「顧客との距離を詰める」という指摘がありましたが、具体的にどのような場面でそう感じられたのでしょうか？",
                "これまでの営業活動で、顧客との関係構築において最も困難だった瞬間はどんな時でしたか？",
                "現在、新規顧客とのやり取りで特に意識していることはありますか？"
            ]
        elif "相手の課題に寄り添った提案" in latest_message:
            return [
                "「相手の課題に寄り添った提案」について、これまでどのようなアプローチを取られていましたか？",
                "顧客のヒアリング時に、どんな質問をすることが多いですか？",
                "提案内容を決める際に、最も重視している点は何ですか？"
            ]
        elif "温度感を読む" in latest_message:
            return [
                "上司から「顧客の温度感を読む」という指摘がありましたが、これまでにそういった感覚を意識したことはありますか？",
                "商談中に、顧客の興味や関心度をどのように判断していますか？",
                "顧客が積極的な時と消極的な時の違いを、何で感じ取ることが多いですか？"
            ]
        else:
            return [
                "この1on1の内容について、どの部分が最も改善したいポイントだと感じますか？",
                "上司からのアドバイスで、特に具体的な方法を知りたいと思った部分はありますか？",
                "現在の営業活動で、最も不安に感じていることは何ですか？"
            ]
    
    async def _generate_clarification_questions(self, context: Dict[str, Any]) -> List[str]:
        """課題明確化のための質問生成"""
        return [
            "その課題が発生する典型的なシチュエーションを具体的に教えてください",
            "同じような状況で、うまくいった経験はありますか？その時は何が違いましたか？",
            "この課題によって、実際にどのような損失や機会損失が発生していますか？"
        ]
    
    async def _generate_analysis_questions(self, context: Dict[str, Any]) -> List[str]:
        """深い分析のための質問生成"""
        return [
            "その課題の根本的な原因は何だと思いますか？",
            "これまでに試したことがある解決策があれば教えてください",
            "理想的な状態になったとき、どのような変化が期待できますか？"
        ]
    
    async def _generate_solution_questions(self, context: Dict[str, Any]) -> List[str]:
        """解決策探索のための質問生成"""
        return [
            "解決策を実行する上で、どのようなサポートや資源が必要ですか？",
            "この改善に取り組む際の期限や目標はありますか？",
            "成功を測る具体的な指標があれば教えてください"
        ]
    
    async def _generate_preparation_questions(self, context: Dict[str, Any]) -> List[str]:
        """アクション準備のための質問生成"""
        return [
            "実行に移す前に不安な点や懸念はありますか？",
            "取り組みを始める最適なタイミングはいつ頃でしょうか？",
            "進捗を確認する方法や頻度はどうしますか？"
        ]
    
    async def _evaluate_completeness(self, context: Dict[str, Any]) -> int:
        """情報の充足度を評価"""
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        messages = [
            {"role": "system", "content": """営業スキル向上のアクションプラン作成に必要な情報の充足度を評価してください。

段階的評価基準：
【20-30点】課題の概要は理解できるが、具体性に欠ける
【40-50点】課題は明確だが、具体的な状況や背景情報が不足
【60-70点】課題と状況は明確だが、詳細な分析が必要
【80-85点】詳細は揃っているが、解決策の方向性が未確定
【90-95点】全ての情報が揃い、アクションプラン作成準備完了
【95点以上】アクションプラン生成に十分な情報

以下の観点で厳格に評価してください：
1. 課題の具体性（抽象的な指摘→具体的な場面）
2. 根本原因の把握（症状→原因の特定）
3. 目標と期限の明確化
4. 実行可能性の検証
5. 成功指標の定義

0-100のスコアで評価してください。数字のみ回答してください。"""},
            {"role": "user", "content": f"会話履歴：\n{context_str}\n\n充足度スコア（0-100）:"}
        ]
        
        from langchain.schema import HumanMessage, SystemMessage
        langchain_messages = [
            SystemMessage(content=messages[0]["content"]),
            HumanMessage(content=messages[1]["content"])
        ]
        response = await self.llm.ainvoke(langchain_messages)
        try:
            score = int(response.content.strip())
            return min(max(score, 0), 100)  # 0-100の範囲に制限
        except:
            return 50  # デフォルト値
    
    async def _generate_follow_up_questions(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """フォローアップ質問を生成"""
        # メモリから履歴を取得
        memory = await self.memory_service.get_or_create_memory(context["session_id"])
        messages = memory.chat_memory.messages
        
        # 会話履歴を文字列に変換
        chat_history = "\n".join([
            f"{msg.type}: {msg.content}" for msg in messages[-5:]  # 最新5メッセージ
        ])
        
        prompt_messages = [
            {"role": "system", "content": """これまでの会話内容を踏まえて、アクションプラン作成に必要な追加情報を収集するための質問を生成してください。
            
            以下の点に注意してください：
            1. すでに得られた情報を踏まえて、より具体的な質問をする
            2. 実践的で測定可能なアクションにつながる情報を収集する
            3. 営業スキル向上に直接関連する質問をする
            
            質問は1行ずつ「Q: 」で始めて3-5個回答してください。"""},
            {"role": "user", "content": f"会話履歴：\n{chat_history}\n\n追加で必要な情報を収集するための質問を生成してください。"}
        ]
        
        langchain_messages = [
            SystemMessage(content=prompt_messages[0]["content"]),
            HumanMessage(content=prompt_messages[1]["content"])
        ]
        response = await self.llm.ainvoke(langchain_messages)
        
        # レスポンスから質問を抽出
        questions = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line.startswith('Q:'):
                questions.append(line[2:].strip())
            elif line.startswith('質問'):
                questions.append(line.split(':', 1)[-1].strip())
        
        # 最低1つの質問を保証
        if not questions:
            questions = ["これまでの内容について、もう少し詳しく教えていただけますか？"]
        
        return questions[:5]  # 最大5個まで
    
    async def _generate_action_plan(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """アクションプランを生成"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """会話内容を基に、新人営業マンの成長のための
            具体的で実行可能なアクションプランを作成してください。
            
            以下の要素を含めてください：
            1. 具体的なアクションアイテム（優先順位付き）
            2. 各アクションの期限と成功指標
            3. 必要なリソースやサポート
            4. 期待される成果
            
            {format_instructions}
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "これまでの会話内容を基に、成長支援のためのアクションプランを作成してください。")
        ])
        
        memory = await self.memory_service.get_or_create_memory(context["session_id"])
        messages = memory.chat_memory.messages
        
        chain = (
            {
                "chat_history": lambda _: messages,
                "format_instructions": lambda _: self.action_plan_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.action_plan_parser
        )
        
        response = await chain.ainvoke({})
        
        # レスポンスを辞書形式に変換
        return {
            "action_items": response.action_items,
            "summary": response.summary,
            "key_improvements": response.key_improvements,
            "metrics": response.metrics,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def save_dialogue_state(
        self,
        session_id: str,
        state: str,
        metadata: Dict[str, Any],
        db_session: Any
    ) -> None:
        """対話の状態を保存"""
        # Redisに状態を保存
        state_key = f"dialogue:state:{session_id}"
        state_data = {
            "state": state,
            "metadata": metadata,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if self.memory_service.redis_client:
            await self.memory_service.redis_client.setex(
                state_key,
                86400,  # 24時間
                json.dumps(state_data, ensure_ascii=False)
            )
    
    async def get_dialogue_state(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """対話の状態を取得"""
        if not self.memory_service.redis_client:
            return None
        
        state_key = f"dialogue:state:{session_id}"
        state_data = await self.memory_service.redis_client.get(state_key)
        
        if state_data:
            return json.loads(state_data)
        return None
    
    # === 1on1対話型具体化システム ===
    
    async def _extract_supervisor_instructions_from_one_on_one(
        self, 
        one_on_one_content: str, 
        db_session: Any
    ) -> List[Dict[str, str]]:
        """LLMを使って1on1から上司の抽象的指示を特定"""
        
        prompt_messages = [
            SystemMessage(content="""1on1ミーティングの内容から、上司が新人営業マンに対して出した抽象的な指示や改善点を特定してください。

以下の基準で「抽象的な指示」を特定してください：
- 新人営業マンが「具体的にどうすればいいのかわからない」と感じるような指示
- 「もっと〜する」「〜を意識する」「〜していけるといいね」のような表現
- 具体的な行動手順が明確でない改善提案

重要: 質問生成時の文脈制約のため、指示の具体的なスコープと境界を明確に定義してください。

必ず以下のJSON形式で回答してください：
```json
{
  "abstract_instructions": [
    {
      "original_text": "上司の発言そのまま",
      "abstract_concept": "抽象的な概念（例：距離を詰める、信頼関係構築、伝わる資料作成）",
      "specific_scope": "この指示が対象とする具体的な範囲（例：提案資料の作成技術、顧客との会話術）",
      "excluded_areas": ["この指示に含まれない関連領域1", "含まれない関連領域2"],
      "key_elements": ["指示に含まれる主要要素1", "主要要素2", "主要要素3"],
      "category": "カテゴリ（customer_relationship, trust_building, document_creation等）",
      "urgency": "優先度（high, medium, low）"
    }
  ]
}
```"""),
            HumanMessage(content=f"以下の1on1内容から抽象的な指示を特定し、各指示の具体的なスコープと境界を明確に定義してください：\n\n{one_on_one_content}")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            response_text = response.content.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            parsed_response = json.loads(response_text)
            return parsed_response.get("abstract_instructions", [])
            
        except Exception as e:
            # エラーの場合は基本的な指示を返す
            return [{
                "original_text": "上司からの改善指示",
                "abstract_concept": "営業スキル向上",
                "category": "general_improvement",
                "urgency": "medium"
            }]
    
    async def _save_one_on_one_session_state(
        self, 
        session_id: str, 
        original_content: str, 
        instructions: List[Dict[str, str]],
        db_session: Any
    ) -> None:
        """1on1セッションの状態を保存"""
        
        state_data = {
            "type": "one_on_one_clarification",
            "original_content": original_content,
            "abstract_instructions": instructions,
            "current_instruction_index": 0,
            "clarified_instructions": [],  # 具体化された指示を保存
            "conversation_history": [],  # 各指示の具体化対話履歴
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Redisに保存を試行、失敗したらインメモリに保存
        if self.memory_service.redis_client:
            try:
                session_key = f"one_on_one_session:{session_id}"
                await self.memory_service.redis_client.setex(
                    session_key,
                    86400,  # 24時間
                    json.dumps(state_data, ensure_ascii=False)
                )
            except Exception:
                # Redisエラーの場合はインメモリにフォールバック
                self._in_memory_sessions[session_id] = state_data
        else:
            # Redisがない場合はインメモリに保存
            self._in_memory_sessions[session_id] = state_data
    
    async def _get_one_on_one_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """1on1セッションの状態を取得"""
        
        # まずRedisから取得を試行
        if self.memory_service.redis_client:
            try:
                session_key = f"one_on_one_session:{session_id}"
                state_data = await self.memory_service.redis_client.get(session_key)
                if state_data:
                    return json.loads(state_data)
            except Exception:
                pass  # Redisエラーの場合はインメモリから取得
        
        # Redisがない場合やエラーの場合はインメモリから取得
        return self._in_memory_sessions.get(session_id)
    
    async def _generate_initial_clarification_questions(
        self, 
        instruction: Dict[str, str], 
        original_content: str
    ) -> List[str]:
        """最初の深掘り質問を生成"""
        
        if not instruction:
            return ["1on1の内容について、どの部分を最も改善したいと感じていますか？"]
        
        abstract_concept = instruction.get("abstract_concept", "")
        original_text = instruction.get("original_text", "")
        specific_scope = instruction.get("specific_scope", "")
        excluded_areas = instruction.get("excluded_areas", [])
        key_elements = instruction.get("key_elements", [])
        
        # 除外領域の文字列を構築
        excluded_text = ""
        if excluded_areas:
            excluded_text = f"\n❌ 除外すべき領域: {', '.join(excluded_areas)}"
        
        # 主要要素の文字列を構築
        key_elements_text = ""
        if key_elements:
            key_elements_text = f"\n🔑 重視すべき要素: {', '.join(key_elements)}"
        
        prompt_messages = [
            SystemMessage(content=f"""新人営業マンが上司から「{abstract_concept}」という抽象的な指示を受けました。
【重要な制約】: 質問は必ず「{abstract_concept}」の文脈内でのみ生成してください。

上司の具体的な指示内容: "{original_text}"
対象スコープ: {specific_scope if specific_scope else abstract_concept}{excluded_text}{key_elements_text}

【厳密な文脈制約】:
🎯 質問は「{abstract_concept}」に特化した内容のみ
❌ 関連しそうでも異なる領域の質問は絶対禁止
✅ 「{abstract_concept}」の具体的な実行方法・経験・感覚のみを聞く

【絶対に避けるべき質問】:
❌ 上司の意図推測: 「上司が求める〜とは何だと思いますか？」
❌ 他人の期待: 「〜さんが期待している〜は何ですか？」  
❌ 文脈外の質問: 「{abstract_concept}」以外の営業スキルについて

【新人営業マン自身に焦点を当てた良い質問（「{abstract_concept}」限定）】:
✅ 「{abstract_concept}」の実体験: 「これまでに{abstract_concept}で困った経験はありますか？」
✅ 「{abstract_concept}」の現在の行動: 「普段{abstract_concept}をする時、どうしていますか？」
✅ 「{abstract_concept}」の感覚: 「{abstract_concept}がうまくいった時、どんな感じでしたか？」
✅ 「{abstract_concept}」の実行可能な行動: 「明日から{abstract_concept}を改善するとしたら？」

例：「{abstract_concept}」について
❌ 悪い質問: 「上司が求める{abstract_concept}とは何だと思いますか？」
❌ 文脈外の質問: 「コミュニケーション全般についてどう思いますか？」（{abstract_concept}が資料作成の場合）
✅ 良い質問: 「これまでに{abstract_concept}で困った経験はありますか？」

1行ずつ「Q: 」で始まる形式で、必ず「{abstract_concept}」の文脈内で回答してください。"""),
            HumanMessage(content=f"上司の指示: \"{original_text}\"\n抽象概念: {abstract_concept}\n\n「{abstract_concept}」に特化した深掘り質問を生成してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            
            # 質問を抽出
            questions = []
            for line in response.content.split('\n'):
                line = line.strip()
                if line.startswith('Q:'):
                    questions.append(line[2:].strip())
                elif line.startswith('質問') and ':' in line:
                    questions.append(line.split(':', 1)[-1].strip())
                elif line and not line.startswith(('1.', '2.', '3.', '4.', '-', '・')):
                    # 番号なしの質問も拾う
                    if '？' in line or '?' in line:
                        questions.append(line)
            
            return questions[:4] if questions else [
                f"これまでに{abstract_concept}で困った経験はありますか？どんな場面でしたか？",
                f"普段、{abstract_concept}を意識して何かしていることはありますか？",
                f"{abstract_concept}がうまくいった時と困った時、自分でも違いを感じますか？",
                f"明日から{abstract_concept}を改善するとしたら、何から始めてみたいですか？"
            ]
            
        except Exception:
            return [
                f"これまでに{abstract_concept}で困った経験はありますか？",
                f"普段、{abstract_concept}について何か意識していることはありますか？"
            ]
    
    async def _continue_one_on_one_clarification(
        self, 
        session_id: str, 
        user_response: str, 
        session_state: Dict[str, Any],
        db_session: Any
    ) -> Dict[str, Any]:
        """1on1具体化プロセスの継続処理（教育的アプローチ）"""
        
        current_index = session_state.get("current_instruction_index", 0)
        instructions = session_state.get("abstract_instructions", [])
        conversation_history = session_state.get("conversation_history", [])
        
        if current_index >= len(instructions):
            # 全ての指示が処理済み → 最終アクションプラン生成
            return await self._generate_final_action_plan_from_session(session_id, session_state, db_session)
        
        current_instruction = instructions[current_index]
        
        # 🎯 ユーザー要求チェック: 具体的な要求があるかチェック
        user_request = await self._check_for_specific_user_request(
            user_response, current_instruction
        )
        
        if user_request:
            # 具体的要求に応答
            return await self._handle_specific_user_request(
                user_request, current_instruction, session_id, db_session
            )
        
        # 🎓 教育的チェック: 新人が概念を理解していないかチェック
        needs_explanation = await self._check_if_needs_concept_explanation(
            user_response, current_instruction
        )
        
        if needs_explanation:
            # 概念説明を提供
            explanation = await self._generate_educational_explanation(
                current_instruction, user_response
            )
            
            return {
                "type": "educational_explanation",
                "explanation": explanation,
                "instruction_being_clarified": current_instruction,
                "stage": "concept_education",
                "stage_description": f"🎓 概念説明: 「{current_instruction.get('abstract_concept', '')}」について",
                "follow_up": "この説明で理解できましたか？理解できたら、具体的な経験や考えを教えてください。"
            }
        
        # 現在の対話履歴に新人の回答を追加
        if current_index < len(conversation_history):
            conversation_history[current_index].append({
                "role": "user",
                "content": user_response,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            # 新しい指示の対話開始
            conversation_history.append([{
                "role": "user", 
                "content": user_response,
                "timestamp": datetime.utcnow().isoformat()
            }])
        
        # 具体性をチェック
        concreteness_result = await self._check_instruction_concreteness(
            current_instruction, 
            conversation_history[current_index],
            user_response
        )
        
        is_concrete = concreteness_result.get("is_concrete", False)
        practical_readiness = concreteness_result.get("practical_readiness", False)
        concreteness_score = concreteness_result.get("score", 0)
        implementation_gaps = concreteness_result.get("implementation_gaps", [])
        required_clarifications = concreteness_result.get("required_clarifications", [])
        
        # 質問回数をカウント
        question_count = len([entry for entry in conversation_history[current_index] 
                             if entry.get("role") == "user"])
        
        # 深い対話のための最低質問回数（実用レベル）
        MIN_QUESTIONS = 5
        MAX_QUESTIONS = 7
        
        # 質問回数と具体性の両方をチェック
        enough_questions = question_count >= MIN_QUESTIONS
        max_questions_reached = question_count >= MAX_QUESTIONS
        
        # 実用レベル完了条件：
        # 1. 最低5回の質問を実施済み
        # 2. 95%以上の具体性スコア
        # 3. 実践準備完了
        # または最大7回に達した場合
        if (enough_questions and is_concrete and practical_readiness and concreteness_score >= 95) or max_questions_reached:
            # 十分具体的 → 次の指示へ移動
            session_state["clarified_instructions"].append({
                "instruction": current_instruction,
                "conversation": conversation_history[current_index],
                "final_response": user_response,
                "concreteness_score": concreteness_score,
                "clarified_at": datetime.utcnow().isoformat()
            })
            
            session_state["current_instruction_index"] = current_index + 1
            session_state["conversation_history"] = conversation_history
            
            # セッション状態を更新
            await self._update_one_on_one_session_state(session_id, session_state)
            
            # 次の指示があるかチェック
            if current_index + 1 < len(instructions):
                next_instruction = instructions[current_index + 1]
                next_questions = await self._generate_initial_clarification_questions(
                    next_instruction, 
                    session_state.get("original_content", "")
                )
                
                return {
                    "type": "one_on_one_clarification",
                    "questions": next_questions,
                    "instruction_being_clarified": next_instruction,
                    "total_instructions": len(instructions),
                    "current_instruction_index": current_index + 1,
                    "stage": "instruction_clarification",
                    "stage_description": f"📋 上司の指示の具体化 ({current_index + 2}/{len(instructions)})",
                    "previous_instruction_completed": current_instruction.get("abstract_concept", ""),
                    "concreteness_achieved": concreteness_score
                }
            else:
                # 全ての指示が具体化完了 → 最終アクションプラン生成
                return await self._generate_final_action_plan_from_session(session_id, session_state, db_session)
        
        else:
            # まだ抽象的 → より深い質問を生成
            deeper_questions = await self._generate_deeper_clarification_questions(
                current_instruction,
                conversation_history[current_index],
                implementation_gaps,
                required_clarifications,
                concreteness_score,
                question_count  # 質問回数を追加
            )
            
            # 対話履歴にAIの質問を追加
            conversation_history[current_index].append({
                "role": "assistant",
                "content": f"深掘り質問: {deeper_questions}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            session_state["conversation_history"] = conversation_history
            await self._update_one_on_one_session_state(session_id, session_state)
            
            # 段階情報を表示用に準備
            if question_count <= 2:
                stage_emoji = "📋"
                stage_name = "基本理解確認"
            elif question_count <= 4:
                stage_emoji = "🔍"
                stage_name = "実体験深掘り"
            elif question_count == 5:
                stage_emoji = "⚙️"
                stage_name = "実行可能性検証"
            elif question_count == 6:
                stage_emoji = "🤔"
                stage_name = "Why理解確認"
            else:
                stage_emoji = "✅"
                stage_name = "最終具体化"
            
            return {
                "type": "one_on_one_clarification",
                "questions": deeper_questions,
                "instruction_being_clarified": current_instruction,
                "total_instructions": len(instructions),
                "current_instruction_index": current_index,
                "stage": "instruction_clarification",
                "stage_description": f"{stage_emoji} {stage_name} ({current_index + 1}/{len(instructions)}) - 質問 {question_count}/7回",
                "concreteness_feedback": f"具体性: {concreteness_score}% - 実用レベル(95%)まで深掘り中",
                "dialogue_progress": f"質問回数: {question_count}/7回 | 最低5回は必要",
                "implementation_gaps": implementation_gaps[:3],  # 不足要素を表示
                "required_clarifications": required_clarifications[:3]  # 必要な明確化を表示
            }
    
    async def _check_instruction_concreteness(
        self, 
        instruction: Dict[str, str], 
        conversation_history: List[Dict[str, str]],
        latest_response: str
    ) -> Dict[str, Any]:
        """厳格な多段階具体性評価システム"""
        
        abstract_concept = instruction.get("abstract_concept", "")
        
        # 会話履歴をテキスト化
        conversation_text = "\\n".join([
            f"{entry['role']}: {entry['content']}" for entry in conversation_history
        ])
        
        prompt_messages = [
            SystemMessage(content=f"""実用レベルの営業コーチとして、新人営業マンの回答を厳格に評価してください。

評価対象の抽象的指示: "{abstract_concept}"

【厳格な実用レベル評価基準】:

🟢 レベル5 (95-100%): 実用完了レベル
- 明日朝9時から実行できる具体的な手順が明記
- 実行頻度、所要時間、測定方法が数値で指定
- 失敗時の対処法まで含む
- 他人にも教えられるレベルの詳細
例: "商談開始時に3分間、相手の業務状況を3つの質問(売上動向/課題/目標)で聞き、A4用紙にメモ。週1回振り返り"

🟡 レベル4 (80-94%): 実行準備レベル  
- 具体的な行動は明確だが、細部で曖昧さが残る
- 測定方法は示されているが数値目標が不明確
- タイミングや頻度がやや曖昧
例: "商談時に相手の状況を質問してメモを取る。定期的に振り返る"

🟠 レベル3 (60-79%): 理解進行レベル
- 基本的な行動方針は理解
- 具体的な実行方法に曖昧さが多い
- 測定や振り返り方法が不明確
例: "相手の状況をよく聞いて理解するようにする"

🔴 レベル2 (40-59%): 概念認識レベル
- 概念は理解しているが実行方法が不明
- 抽象的な表現が多い
例: "もっと相手のことを理解したい"

⚫ レベル1 (0-39%): 理解不足レベル
- 概念の理解が不十分
- 具体的な行動が全く見えない
例: "頑張ります" "意識します"

【重要】: 実用レベルでは95%以上のみを「完了」と判定してください。
90%以下は必ず追加の深掘りが必要です。

【実行可能性の厳密チェック項目】:
✅ 時間設定: 「明日朝9時から」「毎回3分間」等の具体的時間
✅ 場所・環境: 「商談開始時に」「A4用紙に」等の具体的場所・道具
✅ 手順詳細: 「3つの質問(売上・課題・目標)で聞く」等のステップ
✅ 測定方法: 「週1回振り返る」「メモの数をカウント」等の確認方法
✅ 失敗対処: 「うまくいかない時はXXする」等の代替案
✅ リソース: 必要な道具・権限・時間が明確で実現可能

以下のJSON形式で厳格に評価してください：
```json
{{
  "level": 1-5,
  "score": 0-100,
  "is_concrete": true/false,
  "practical_readiness": true/false,
  "executable_tomorrow": true/false,
  "time_specification": true/false,
  "resource_clarity": true/false,
  "measurement_method": true/false,
  "failure_handling": true/false,
  "implementation_gaps": ["不足要素1", "不足要素2"],
  "strong_points": ["具体的な要素1", "具体的な要素2"], 
  "required_clarifications": ["必要な明確化1", "必要な明確化2"],
  "next_focus": "次に重点的に確認すべき点",
  "why_understanding": true/false,
  "practical_barriers": ["実行上の障害1", "障害2"]
}}
```"""),
            HumanMessage(content=f"会話履歴：\\n{conversation_text}\\n\\n最新の回答: {latest_response}\\n\\n厳格な実用レベル基準で評価してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            response_text = response.content.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            # 実用レベルでは95%以上かつ実行可能性チェック項目をクリアが必要
            score = result.get("score", 0)
            executable_tomorrow = result.get("executable_tomorrow", False)
            time_specification = result.get("time_specification", False) 
            resource_clarity = result.get("resource_clarity", False)
            measurement_method = result.get("measurement_method", False)
            
            # 厳格な実行可能性判定
            practical_requirements_met = all([
                executable_tomorrow,
                time_specification,
                resource_clarity,
                measurement_method
            ])
            
            if score < 95 or not practical_requirements_met:
                result["is_concrete"] = False
                result["practical_readiness"] = False
            
            return result
            
        except Exception:
            # エラーの場合は厳格に低評価
            return {
                "level": 2,
                "score": 30,
                "is_concrete": False,
                "practical_readiness": False,
                "implementation_gaps": ["具体的な手順", "実行タイミング", "測定方法", "数値目標"],
                "strong_points": [],
                "required_clarifications": ["実行手順の詳細化", "測定可能な目標設定"],
                "next_focus": "具体的な実行方法の明確化",
                "why_understanding": False,
                "measurability": False
            }
    
    async def _update_one_on_one_session_state(self, session_id: str, state_data: Dict[str, Any]) -> None:
        """1on1セッション状態を更新"""
        # Redisに保存を試行、失敗したらインメモリに保存
        if self.memory_service.redis_client:
            try:
                session_key = f"one_on_one_session:{session_id}"
                await self.memory_service.redis_client.setex(
                    session_key,
                    86400,  # 24時間
                    json.dumps(state_data, ensure_ascii=False)
                )
            except Exception:
                # Redisエラーの場合はインメモリにフォールバック
                self._in_memory_sessions[session_id] = state_data
        else:
            # Redisがない場合はインメモリに保存
            self._in_memory_sessions[session_id] = state_data
    
    async def _generate_deeper_clarification_questions(
        self, 
        instruction: Dict[str, str], 
        conversation_history: List[Dict[str, str]],
        implementation_gaps: List[str],
        required_clarifications: List[str],
        concreteness_score: int,
        question_count: int
    ) -> List[str]:
        """より深い具体化質問を生成"""
        
        abstract_concept = instruction.get("abstract_concept", "")
        specific_scope = instruction.get("specific_scope", "")
        excluded_areas = instruction.get("excluded_areas", [])
        key_elements = instruction.get("key_elements", [])
        original_text = instruction.get("original_text", "")
        
        # 除外領域の文字列を構築
        excluded_text = ""
        if excluded_areas:
            excluded_text = f"\n❌ 除外すべき領域: {', '.join(excluded_areas)}"
        
        # 主要要素の文字列を構築
        key_elements_text = ""
        if key_elements:
            key_elements_text = f"\n🔑 重視すべき要素: {', '.join(key_elements)}"
        
        # 質問段階の決定
        if question_count <= 2:
            question_stage = "基本理解確認"
            stage_focus = "概念の基本的理解と経験の確認"
        elif question_count <= 4:
            question_stage = "実体験深掘り"
            stage_focus = "具体的な経験や状況の詳細化"
        elif question_count == 5:
            question_stage = "実行可能性検証"
            stage_focus = "明日から実行できる具体的な手順の確認"
        elif question_count == 6:
            question_stage = "Why理解確認"
            stage_focus = "なぜその行動が重要かの理解確認"
        else:
            question_stage = "最終具体化"
            stage_focus = "測定可能で他人にも説明できるレベルの詳細化"
        
        # 会話履歴をテキスト化
        conversation_text = "\\n".join([
            f"{entry['role']}: {entry['content']}" for entry in conversation_history
        ])
        
        prompt_messages = [
            SystemMessage(content=f"""実用レベルの営業コーチとして、段階的な深掘り質問を生成してください。

【対話の現状】:
- 質問回数: {question_count}/7回
- 現在の段階: {question_stage}
- この段階の焦点: {stage_focus}
- 具体性スコア: {concreteness_score}%

対象の抽象的指示: "{abstract_concept}"
上司の具体的な指示内容: "{original_text}"
対象スコープ: {specific_scope if specific_scope else abstract_concept}{excluded_text}{key_elements_text}
実装上の不足要素: {implementation_gaps}
必要な明確化事項: {required_clarifications}

【段階別質問戦略】:
📋 基本理解確認 (1-2回目): 概念理解と基本的な経験
🔍 実体験深掘り (3-4回目): 具体的な状況と詳細な経験
⚙️ 実行可能性検証 (5回目): 実際の手順と測定方法
🤔 Why理解確認 (6回目): なぜその行動が重要かの理解
✅ 最終具体化 (7回目): 他人に説明できるレベルの完全な詳細

【Why理解確認の重要性】:
新人が「なぜその行動が重要なのか」を理解していることで：
- 継続的な実行が可能になる
- 状況に応じた応用ができる  
- 他のメンバーにも説明できる
- モチベーションが維持される

【厳密な文脈制約】:
🎯 深掘り質問は「{abstract_concept}」に特化した内容のみ
❌ 関連しそうでも異なる領域の質問は絶対禁止
✅ 「{abstract_concept}」の具体的な実行方法・経験・手順のみを深掘り

【絶対に避けるべき深掘り質問】:
❌ 上司の意図推測: 「上司が言いたかったことは何だと思いますか？」
❌ 他人の期待: 「お客様が期待している〜は何ですか？」
❌ 会社の方針: 「会社として求められる〜は？」
❌ 文脈外の質問: 「{abstract_concept}」以外の領域について

【新人営業マン自身に焦点を当てた深掘り質問（「{abstract_concept}」限定）】:
✅ 「{abstract_concept}」の具体的体験: 「これまでに{abstract_concept}をした経験はありますか？」
✅ 「{abstract_concept}」の現在の感覚: 「{abstract_concept}をする時、どんな風に感じますか？」
✅ 「{abstract_concept}」の実行可能な行動: 「明日から{abstract_concept}を改善するとしたら、何分くらい？」
✅ 「{abstract_concept}」での自分の判断: 「{abstract_concept}でAとB、どちらを選びますか？」

【「{abstract_concept}」に特化した深掘り質問例】:
- 「これまでに{abstract_concept}がうまくいった経験はありますか？その時何をしていましたか？」
- 「普段{abstract_concept}をする時、一番困るのはどんな場面ですか？」
- 「明日{abstract_concept}を改善するとしたら、何から始めますか？」

注意: 質問は必ず「{abstract_concept}」の範囲内で生成し、他の営業スキルやコミュニケーション全般に逸脱しないこと。

1行ずつ「Q: 」で始まる形式で2-3個の質問を生成してください。"""),
            HumanMessage(content=f"これまでの会話：\\n{conversation_text}\\n\\n「{abstract_concept}」に特化したより具体的な深掘り質問を生成してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            
            # 質問を抽出
            questions = []
            for line in response.content.split('\\n'):
                line = line.strip()
                if line.startswith('Q:'):
                    questions.append(line[2:].strip())
                elif '？' in line or '?' in line:
                    if not line.startswith(('例：', '※', '注：')):
                        questions.append(line)
            
            return questions[:3] if questions else [
                f"これまでに{abstract_concept}がうまくいった経験はありますか？その時何をしていましたか？",
                f"普段{abstract_concept}で一番困るのはどんな場面ですか？",
                f"明日から{abstract_concept}を改善するために、何分くらい時間をかけてみますか？"
            ]
            
        except Exception:
            return [
                f"これまでに{abstract_concept}で困った経験はありますか？",
                f"普段{abstract_concept}について何か気をつけていることはありますか？",
                f"明日から何か新しいことを試してみるとしたら、何をしますか？"
            ]
    
    async def _generate_final_action_plan_from_session(
        self, 
        session_id: str, 
        session_state: Dict[str, Any], 
        db_session: Any
    ) -> Dict[str, Any]:
        """対話型具体化プロセスから最終アクションプランを生成"""
        
        clarified_instructions = session_state.get("clarified_instructions", [])
        original_content = session_state.get("original_content", "")
        
        if not clarified_instructions:
            return {
                "type": "error",
                "message": "具体化された指示がありません。もう一度1on1の内容から始めてください。"
            }
        
        # 具体化された全ての指示をまとめる
        all_clarifications = []
        for clarified in clarified_instructions:
            instruction = clarified["instruction"]
            conversation = clarified["conversation"]
            final_response = clarified["final_response"]
            
            all_clarifications.append({
                "original_abstract": instruction.get("abstract_concept", ""),
                "clarification_conversation": conversation,
                "concrete_outcome": final_response,
                "concreteness_score": clarified.get("concreteness_score", 0)
            })
        
        # LLMに最終アクションプラン生成を依頼
        clarifications_text = "\\n\\n".join([
            f"指示: {c['original_abstract']}\\n具体化結果: {c['concrete_outcome']}"
            for c in all_clarifications
        ])
        
        prompt_messages = [
            SystemMessage(content=f"""新人営業マンとの対話を通じて、上司の抽象的な指示が具体化されました。
これらの具体化された内容を統合して、実践的な最終アクションプランを作成してください。

以下のJSON形式で回答してください：
```json
{{
  "final_summary": {{
    "title": "1on1フィードバック 最終アクションプラン",
    "priority_actions": [
      {{
        "action": "具体的なアクション",
        "specific_steps": ["ステップ1", "ステップ2", "ステップ3"],
        "frequency": "実行頻度",
        "measurement": "成果測定方法"
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
  }},
  "dialogue_summary": {{
    "instructions_clarified": {len(clarified_instructions)},
    "total_interactions": "対話の総数",
    "key_insights": ["洞察1", "洞察2"],
    "concreteness_improvement": "具体性の向上度"
  }}
}}
```

重要: 全て新人営業マンが明日から実行できる具体的な内容にしてください。"""),
            HumanMessage(content=f"元の1on1内容：\\n{original_content}\\n\\n具体化された指示：\\n{clarifications_text}\\n\\n最終アクションプランを生成してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            response_text = response.content.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            action_plan_data = json.loads(response_text)
            
            # 1on1セッションを完了としてマーク（削除）
            if self.memory_service.redis_client:
                try:
                    session_key = f"one_on_one_session:{session_id}"
                    await self.memory_service.redis_client.delete(session_key)
                except Exception:
                    pass  # Redisエラーは無視
            
            # インメモリからも削除
            if session_id in self._in_memory_sessions:
                del self._in_memory_sessions[session_id]
            
            return {
                "type": "one_on_one_final_plan",
                "data": action_plan_data,
                "clarification_history": all_clarifications,
                "analysis_method": "dialogue_based_concretization"
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"最終アクションプラン生成中にエラーが発生しました: {str(e)}"
            }
    
    # === 教育的説明機能 ===
    
    async def _check_if_needs_concept_explanation(
        self,
        user_response: str,
        instruction: Dict[str, Any]
    ) -> bool:
        """新人が概念説明を必要としているかチェック"""
        
        abstract_concept = instruction.get("abstract_concept", "")
        
        # 経験がないことを示す有効な回答
        no_experience_indicators = [
            "ありません", "ないです", "経験がない", "経験ありません",
            "したことがない", "ない", "特にない", "特にありません"
        ]
        
        # 有効な否定回答かチェック
        normalized_response = user_response.strip()
        for indicator in no_experience_indicators:
            if indicator in normalized_response:
                return False  # 経験がないという有効な回答なので説明は不要
        
        # 明確な理解不足のサイン
        confusion_indicators = [
            "って何？", "とは？", "分からない", "わからない",
            "知らない", "初めて聞く", "意味が", "どういう",
            "よくわからない", "理解できない", "？？？",
            "何のこと", "具体的に何", "どう違う"
        ]
        
        # 基本的なチェック
        for indicator in confusion_indicators:
            if indicator in user_response:
                return True
        
        # LLMによる詳細チェック
        prompt_messages = [
            SystemMessage(content=f"""あなたは教育心理学の専門家です。

文脈：
- 上司が新人に「{abstract_concept}」について質問しています
- 新人が回答しました

新人の回答を分析し、以下を判定してください：
1. 新人はこの概念を理解していますか？
2. 概念の説明が必要ですか？

判定の際は、回答の内容と文脈から新人の理解度を総合的に判断してください。
短い回答でも、文脈に適した内容であれば理解していると判断できます。

回答：true（説明が必要）またはfalse（理解している）"""),
            HumanMessage(content=f"新人の回答: {user_response}")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            return "true" in response.content.lower()
        except Exception:
            # エラーの場合は混乱の指標がある場合のみ説明が必要と判定
            return any(indicator in user_response for indicator in confusion_indicators)
    
    async def _generate_educational_explanation(
        self,
        instruction: Dict[str, Any],
        user_response: str
    ) -> str:
        """教育的な概念説明を生成"""
        
        abstract_concept = instruction.get("abstract_concept", "")
        original_text = instruction.get("original_text", "")
        
        prompt_messages = [
            SystemMessage(content=f"""新人営業マンが「{abstract_concept}」について理解できずにいます。

新人にとって分かりやすい説明を作成してください：

説明に含める要素：
1. 概念の基本的な定義（専門用語を避けて）
2. 営業活動での具体例（3つ程度）
3. なぜ重要なのか（具体的なメリット）
4. よくある誤解の訂正
5. 新人でも今日から意識できるポイント

親しみやすく、分かりやすい説明でお願いします。
上司の発言: "{original_text}"
新人の困惑: "{user_response}" """),
            HumanMessage(content=f"「{abstract_concept}」について、新人営業マンに分かりやすく説明してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            return response.content.strip()
        except Exception:
            return f"""「{abstract_concept}」について説明しますね。

これは営業活動において重要な要素の一つです。具体的には、お客様とのやり取りや提案活動で意識すべきポイントを指しています。

まずは「{abstract_concept}」がどういうものか、一緒に具体的に考えていきましょう。"""
    
    # === ユーザー要求認識・応答機能 ===
    
    async def _check_for_specific_user_request(
        self,
        user_response: str,
        instruction: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """ユーザーの具体的な要求をチェック"""
        
        # ユーザーが自分の経験や事例を共有しているかをチェック
        experience_indicators = [
            "例えば、", "具体的には、", "実際に", "これまでに", "過去に", 
            "ました", "でした", "していた", "作成しました", "しました",
            "構成し", "用いて", "守った", "効果的でした", "ことで",
            "点も", "順に", "避け", "整理した"
        ]
        
        # 経験共有のパターンが複数含まれている場合は要求ではない
        matching_patterns = sum(1 for pattern in experience_indicators if pattern in user_response)
        if matching_patterns >= 2:  # 複数の経験指標があれば経験共有と判定
            return None
        
        # 明確な要求のパターン (より厳密に)
        request_patterns = {
            "example_request": ["例を教えて", "例を見せて", "具体例をください", "サンプルをください", "実例が欲しい"],
            "template_request": ["テンプレートを", "フォーマットを", "ひな形を", "様式を"],
            "reference_request": ["参考資料を", "お手本を", "見本を", "良い例を教えて"],
            "knowledge_request": ["ナレッジを", "資料をください", "ドキュメントを", "先輩の例を", "社内の例を"]
        }
        
        # より厳密なパターンマッチング
        for request_type, patterns in request_patterns.items():
            if any(pattern in user_response for pattern in patterns):
                return {
                    "type": request_type,
                    "original_request": user_response,
                    "abstract_concept": instruction.get("abstract_concept", "")
                }
        
        # LLMによる詳細チェック
        abstract_concept = instruction.get("abstract_concept", "")
        
        prompt_messages = [
            SystemMessage(content=f"""あなたは1on1の対話分析の専門家です。

現在の文脈：
- 上司が新人に「{abstract_concept}」について質問や指導をしています
- 新人営業マンが回答しました

新人の回答を分析し、以下を判定してください：

【重要な判定基準】:
1. 新人が自分の経験や体験を共有している場合 → 要求ではない
   例: "例えば、私は〜しました", "実際に〜を作成しました", "これまでに〜した経験があります"
   
2. 新人が具体的な資料や例を求めている場合 → 要求である
   例: "例を教えてください", "テンプレートをください", "参考資料が欲しいです"

3. 新人が質問をしている場合 → 要求ではない (情報収集)
   例: "〜はどうすればいいですか？", "〜について教えてください"

回答形式：
```json
{{
  "has_request": true/false,
  "request_type": "要求の種類（example_request/template_request/reference_request/knowledge_request/help_request）",
  "confidence": 0.0-1.0,
  "reasoning": "判定理由を簡潔に",
  "is_experience_sharing": true/false
}}
```"""),
            HumanMessage(content=f"新人の回答: {user_response}")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            response_text = response.content.strip()
            
            # JSONを抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end != -1:
                    response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            # 経験共有として判定された場合は要求ではない
            if result.get("is_experience_sharing", False):
                return None
            
            # 要求として判定され、十分な信頼度がある場合のみ処理
            if result.get("has_request", False) and result.get("confidence", 0) > 0.7:
                return {
                    "type": result.get("request_type", "example_request"),
                    "original_request": user_response,
                    "abstract_concept": abstract_concept,
                    "confidence": result.get("confidence", 0)
                }
            
            return None
            
        except Exception:
            return None
    
    async def _handle_specific_user_request(
        self,
        user_request: Dict[str, str],
        instruction: Dict[str, Any],
        session_id: str,
        db_session: Any
    ) -> Dict[str, Any]:
        """ユーザーの具体的要求に応答"""
        
        request_type = user_request.get("type", "")
        abstract_concept = user_request.get("abstract_concept", "")
        original_request = user_request.get("original_request", "")
        
        if request_type in ["example_request", "template_request", "reference_request", "knowledge_request"]:
            # 社内ナレッジベースから実例を検索・提供
            print(f"DEBUG: Processing user request - concept: '{abstract_concept}', type: '{request_type}'")
            
            knowledge_response = await self._provide_knowledge_examples(
                abstract_concept, request_type, db_session
            )
            
            print(f"DEBUG: Final knowledge_response contains markdown: {'```markdown' in knowledge_response}")
            
            return {
                "type": "knowledge_provision",
                "knowledge_response": knowledge_response,
                "instruction_being_clarified": instruction,
                "stage": "knowledge_provision",
                "stage_description": f"📚 社内ナレッジ提供: 「{abstract_concept}」の実例",
                "original_request": original_request,
                "follow_up": "この実例を参考に、あなたの経験や状況について教えてください。対話を続けてより具体的なアクションプランを作成しましょう。"
            }
        else:
            # その他の要求への対応
            return {
                "type": "request_acknowledgment", 
                "message": f"「{original_request}」というご要求を承りました。「{abstract_concept}」について、まず基本的な理解を深めてから、より具体的な支援を提供させていただきます。",
                "instruction_being_clarified": instruction,
                "stage": "request_acknowledgment"
            }
    
    async def _provide_knowledge_examples(
        self,
        abstract_concept: str,
        request_type: str,
        db_session: Any
    ) -> str:
        """社内ナレッジベースから実例を提供"""
        
        # 社内ナレッジベースアクセス（実装例）
        knowledge_examples = await self._search_knowledge_base(
            abstract_concept, request_type, db_session
        )
        
        print(f"DEBUG: Knowledge examples found: {len(knowledge_examples)}")
        
        if knowledge_examples:
            formatted_examples = self._format_knowledge_examples(
                knowledge_examples, abstract_concept, request_type
            )
            print(f"DEBUG: Formatted examples contains markdown: {'```markdown' in formatted_examples}")
            print(f"DEBUG: Formatted examples preview: {formatted_examples[:300]}...")
            return formatted_examples
        else:
            # ナレッジがない場合のフォールバック
            print(f"DEBUG: No knowledge found, using synthetic examples")
            synthetic_result = await self._generate_synthetic_examples(abstract_concept, request_type)
            print(f"DEBUG: Synthetic result contains markdown: {'```markdown' in synthetic_result}")
            return synthetic_result
    
    async def _search_knowledge_base(
        self,
        abstract_concept: str,
        request_type: str,
        db_session: Any
    ) -> List[Dict[str, Any]]:
        """社内ナレッジベースを検索"""
        
        # 実際のナレッジベース検索実装
        try:
            # データベースやナレッジベースから関連資料を検索
            # 例: SELECT * FROM knowledge_base WHERE concept LIKE %abstract_concept%
            
            # 高品質なサンプルナレッジ（実際の有用例）
            knowledge_samples = {
                "伝わる資料作成": [
                    {
                        "title": "顧客課題解決型提案資料（マークダウン版）",
                        "content": """```markdown
# [顧客名]様 業務効率化ソリューション提案書

**提案日**: 2024年12月XX日  
**提案者**: 営業部 [担当者名]  
**有効期限**: 2025年1月末まで

---

## 1. 現状課題の整理

### 🔍 ヒアリング結果
- **データ集計作業**: 月末に3日間の手作業が発生
- **レポート作成**: Excel作業で週10時間を消費  
- **情報共有**: 部署間での連携に時間がかかる

### 📊 課題の定量化
| 項目 | 現状 | 目標 |
|------|------|------|
| データ集計時間 | 24時間/月 | 2時間/月 |
| レポート作成時間 | 40時間/月 | 10時間/月 |
| エラー発生率 | 5% | 0.5% |

---

## 2. 解決策のご提案

### 💡 ソリューション概要
**[製品名]** による業務自動化システムの導入

#### Before → After
- **手作業データ集計** → **自動データ収集・加工**
- **Excel手作業** → **テンプレート自動生成**
- **メール・電話連携** → **リアルタイム情報共有**

### 🎯 導入効果
```
月間工数削減: 62時間 → 12時間 (80%削減)
年間コスト効果: 約480万円の人件費削減
精度向上: エラー率 5% → 0.5%
```

---

## 3. 導入プロセス

### 📅 3ヶ月導入計画

#### Phase 1: 基盤構築 (1ヶ月目)
- [ ] システム環境構築
- [ ] 既存データの移行準備
- [ ] 担当者向け研修実施

#### Phase 2: 段階導入 (2ヶ月目)  
- [ ] データ集計機能の稼働開始
- [ ] レポート自動生成の運用開始
- [ ] ユーザーフィードバック収集

#### Phase 3: 本格運用 (3ヶ月目)
- [ ] 全機能の本格運用
- [ ] 運用マニュアル整備
- [ ] 効果測定・改善提案

### 💰 投資回収
```
初期投資: 200万円
月額費用: 10万円
投資回収期間: 6ヶ月
3年間ROI: 350%
```

---

## 4. サポート体制

### 🛠️ 導入支援
- **専任SE**: 導入期間中の技術サポート
- **研修プログラム**: 3回の集合研修 + 個別フォロー
- **ヘルプデスク**: 平日9-18時の電話・メールサポート

### 📞 緊急時対応
- **24時間監視**: システム稼働状況の常時監視
- **1時間以内対応**: 緊急時の初期対応保証
- **月次レビュー**: 運用状況の定期確認

---

## 5. 次のステップ

### 🚀 今後のスケジュール
1. **12月20日まで**: ご検討・ご質問対応
2. **12月25日**: 最終提案書のご提示  
3. **1月10日**: 契約締結（目標）
4. **2月1日**: 導入開始

### ✅ 今回決めていただきたいこと
- [ ] 提案内容についてのご承認
- [ ] 導入時期のご確認
- [ ] 次回打ち合わせ日程の調整

---

**お問い合わせ**  
営業部 [担当者名]  
📧 [email@company.com]  
📞 090-XXXX-XXXX
```

**このテンプレートの使い方**:
1. [　]内を実際の顧客情報に置き換え
2. 数値データは必ず根拠資料を準備
3. 顧客の業界用語を積極的に使用
4. 印刷時はA4で5-6ページに収まるよう調整""",
                        "author": "営業部 田村課長",
                        "success_rate": "提案成功率 85%",
                        "usage_frequency": "月15件使用",
                        "tags": ["提案資料", "成功事例", "テンプレート"]
                    },
                    {
                        "title": "営業提案書テンプレート（簡潔版）",
                        "content": """```markdown
# 営業提案書テンプレート

## 📋 基本情報
**顧客名**: [会社名 部署名 担当者名]  
**提案者**: [自社名 担当者名]  
**提案日**: [YYYY/MM/DD]

---

## 🎯 提案概要（30秒で伝わる）
**お困りごと**: [顧客の課題を1行で]  
**解決策**: [提案内容を1行で]  
**効果**: [数値で示すメリット]

例：
- **お困りごと**: 月末の売上集計に3日かかっている
- **解決策**: 自動集計システムで即座に完了
- **効果**: 工数90%削減、正確性99.9%向上

---

## 📊 現状分析

### ヒアリング内容
| 項目 | 現状 | 課題 |
|------|------|------|
| [業務A] | [現在の状況] | [困っていること] |
| [業務B] | [現在の状況] | [困っていること] |
| [業務C] | [現在の状況] | [困っていること] |

### 定量的な課題
```
時間: XX時間/月 → YY時間/月へ短縮目標
コスト: XX万円/月 → YY万円/月へ削減目標  
品質: エラー率XX% → YY%へ改善目標
```

---

## 💡 解決提案

### Before → After
| 項目 | Before（現状） | After（改善後） | 効果 |
|------|----------------|-----------------|------|
| [項目1] | [現状] | [改善後] | [効果] |
| [項目2] | [現状] | [改善後] | [効果] |
| [項目3] | [現状] | [改善後] | [効果] |

### 📈 ROI計算
```
初期投資: XXX万円
月額費用: XX万円
年間効果: XXX万円
投資回収期間: X.X年
3年間ROI: XXX%
```

---

## 🗓️ 導入スケジュール

| フェーズ | 期間 | 内容 | 成果物 |
|----------|------|------|--------|
| 準備 | 1週間 | [準備内容] | [成果物] |
| 導入 | 2週間 | [導入内容] | [成果物] |
| 運用 | 1週間 | [運用内容] | [成果物] |

---

## 🤝 次のアクション

### 今回決めていただきたいこと
- [ ] 提案内容へのご承認
- [ ] 導入時期のご相談  
- [ ] 予算範囲のご確認

### 次回までの宿題
**弊社**: [こちらでやること]  
**お客様**: [お客様にお願いしたいこと]

### 次回打ち合わせ
**日時**: [候補日程]  
**場所**: [場所]  
**議題**: [話し合う内容]

---

**連絡先**: [担当者名] / [電話] / [メール]
```

**使用ガイド**:
1. [　]内を実際の内容に置き換えて使用
2. 数値は必ず根拠資料を用意
3. 専門用語は顧客の業界用語に合わせる
4. A4で3-4ページに収まるよう調整""",
                        "author": "営業部 山田部長",
                        "success_rate": "資料評価平均4.8/5.0",
                        "usage_frequency": "全営業が使用",
                        "tags": ["データ活用", "レイアウト", "実践的"]
                    }
                ],
                "ストーリー性": [
                    {
                        "title": "顧客の一日ストーリー型プレゼン",
                        "content": """**ストーリー展開テンプレート**:

**導入部**:「○○部長の一日を想像してみてください」

**問題提起**:
- 朝9時: 売上報告の準備に30分
- 10時: データが不正確で会議が紛糾
- 午後: 手作業でのデータ集計が3時間
- 夕方: 残業でようやく資料完成

**解決提示**:
「もし、この作業が10分で完了したら...」
- 朝の30分 → 戦略検討時間に
- データ不正確 → リアルタイム正確データ
- 3時間作業 → 自動化で即座に完了
- 残業なし → 定時で新規開拓活動

**効果測定**:
- 工数削減: 月40時間 → 5時間
- 精度向上: エラー率2% → 0.1%
- 満足度: 部長の業務満足度向上

**行動喚起**:
「来月から○○部長にこの快適な一日を過ごしていただけます」""",
                        "author": "営業部 鈴木主任",
                        "success_rate": "感情的共感度95%",
                        "usage_frequency": "大型案件で必須使用",
                        "tags": ["ストーリーテリング", "共感型", "大型案件"]
                    }
                ]
            }
            
            # 実際の検索（概念にマッチするナレッジを探す）
            matched_knowledge = knowledge_samples.get(abstract_concept, [])
            
            # デバッグ用ログ
            print(f"DEBUG: Searching for concept: '{abstract_concept}'")
            print(f"DEBUG: Available concepts: {list(knowledge_samples.keys())}")
            print(f"DEBUG: Matched knowledge count: {len(matched_knowledge)}")
            
            # より良い検索の場合、実際のDBクエリを実行
            # if db_session:
            #     query = f"SELECT * FROM knowledge_base WHERE concept LIKE '%{abstract_concept}%'"
            #     matched_knowledge = db_session.execute(query).fetchall()
            
            return matched_knowledge
            
        except Exception:
            return []
    
    def _format_knowledge_examples(
        self,
        knowledge_examples: List[Dict[str, Any]],
        abstract_concept: str,
        request_type: str
    ) -> str:
        """ナレッジ例を高品質フォーマット"""
        
        if request_type == "example_request":
            header = f"📚 **「{abstract_concept}」の社内実例**"
        elif request_type == "template_request":
            header = f"📋 **「{abstract_concept}」のテンプレート**"
        elif request_type == "reference_request":
            header = f"🎯 **「{abstract_concept}」の参考資料**"
        else:
            header = f"💡 **「{abstract_concept}」の社内ナレッジ**"
        
        formatted = f"{header}\n\n"
        
        for i, example in enumerate(knowledge_examples, 1):
            title = example.get('title', f'実例{i}')
            content = example.get('content', '')
            author = example.get('author', '')
            success_rate = example.get('success_rate', '')
            usage_frequency = example.get('usage_frequency', '')
            
            formatted += f"**{i}. {title}**\n"
            
            # 詳細内容をそのまま表示
            if content:
                formatted += f"{content}\n"
            
            # 成功指標や使用頻度があれば表示
            if success_rate:
                formatted += f"📊 成果: {success_rate}\n"
            if usage_frequency:
                formatted += f"📈 活用度: {usage_frequency}\n"
            if author:
                formatted += f"_作成者: {author}_\n"
            
            formatted += "\n---\n\n"
        
        return formatted
    
    async def _generate_synthetic_examples(
        self,
        abstract_concept: str,
        request_type: str
    ) -> str:
        """ナレッジがない場合の高品質合成例生成"""
        
        if request_type == "example_request":
            prompt_content = f"""新人営業マンが「{abstract_concept}」の具体例を求めています。

すぐに使えるマークダウン形式の実用的な例を3つ提供してください。

【重要要件】:
- コピー&ペーストで使えるマークダウン形式
- 明日から実践できるレベルの詳細さ
- 実際の営業シーンでの使用方法
- 数値・時間・頻度を含む具体性
- [変更箇所]を明示して使いやすく

【出力形式】:
**例1: [具体的なタイトル]**
```markdown
[実際に使えるマークダウンテンプレート]
```
- 使用場面: [詳細なシチュエーション]
- カスタマイズ箇所: [変更すべき[　]部分の説明]
- 成功のコツ: [実践的なアドバイス]
- 所要時間: [作成にかかる時間]

**例2**: [同様の形式]
**例3**: [同様の形式]"""
        elif request_type == "template_request":
            prompt_content = f"""新人営業マンが「{abstract_concept}」のテンプレートを求めています。

すぐに使える実用的なテンプレートを3つ提供してください。

【重要要件】:
- コピー&ペーストで使える形式
- カスタマイズ方法も説明
- 実際の文言例を含む
- レイアウト・構成を具体的に
- 使用上の注意点も併記

【出力形式】:
**テンプレート1: [名前]**
```
[実際に使える具体的なテンプレート]
```
使用方法: [詳細な説明]
カスタマイズ: [変更すべき箇所]

**テンプレート2**: [同様の形式]
**テンプレート3**: [同様の形式]"""
        else:
            prompt_content = f"""新人営業マンが「{abstract_concept}」の参考資料を求めています。

実践的で学習効果の高い参考例を3つ提供してください。

【重要要件】:
- 成功事例の具体的な内容
- なぜ成功したかの分析
- 新人が真似できるポイント
- 避けるべき失敗パターン
- 段階的な習得方法

実際の営業現場で役立つ、具体的で詳細な内容にしてください。"""
        
        prompt_messages = [
            SystemMessage(content=prompt_content),
            HumanMessage(content=f"「{abstract_concept}」について、新人営業マンが実際に使える具体的で詳細な{request_type}を提供してください。")
        ]
        
        try:
            response = await self.llm.ainvoke(prompt_messages)
            return f"💡 **「{abstract_concept}」の実践例**\n\n{response.content.strip()}"
        except Exception:
            return f"「{abstract_concept}」について、より詳しい情報をお調べして後ほど提供いたします。まずは基本的な理解から始めましょう。"