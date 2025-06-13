"""
改善された対話マネージャー
知識ベースを活用し、自己解決機能を持つ対話システム
"""

from typing import Dict, Any, List, Optional, Tuple
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from datetime import datetime
import json

from app.services.conversation_memory import ConversationMemoryService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.action_template_generator import ActionTemplateGenerator
from app.services.conversation_history_service import ConversationHistoryService
from app.core.config import settings


class EnhancedQuestionResponse(BaseModel):
    """改善された質問生成のレスポンス構造"""
    questions: List[str] = Field(description="生成された質問のリスト")
    reasoning: str = Field(description="なぜこれらの質問が必要かの説明")
    information_needed: List[str] = Field(description="まだ必要な情報のリスト")
    self_resolved_insights: List[Dict[str, Any]] = Field(description="知識ベースから自己解決した洞察")
    suggested_resources: List[str] = Field(description="参考になるリソース")
    completeness_score: int = Field(description="情報の充足度（0-100）")


class EnhancedActionPlanResponse(BaseModel):
    """改善されたアクションプラン生成のレスポンス構造"""
    action_items: List[Dict[str, Any]] = Field(description="具体的なアクションアイテム（テンプレート付き）")
    templates_provided: List[Dict[str, Any]] = Field(description="提供されたテンプレート")
    summary: str = Field(description="全体的なサマリー")
    key_improvements: List[str] = Field(description="主要な改善ポイント")
    metrics: Dict[str, Any] = Field(description="成功指標")
    knowledge_references: List[Dict[str, Any]] = Field(description="参照した社内ナレッジ")
    mentor_suggestions: List[str] = Field(description="先輩の成功事例からの提案")


class SelfResolutionResponse(BaseModel):
    """自己解決の結果"""
    resolved_questions: List[Dict[str, str]] = Field(description="解決された質問と回答")
    remaining_questions: List[str] = Field(description="まだ回答が必要な質問")
    confidence_level: str = Field(description="解決の確信度")
    sources_used: List[str] = Field(description="使用した情報源")


class EnhancedDialogueManager:
    """改善された対話フローを管理するマネージャー"""
    
    def __init__(self):
        self.memory_service = ConversationMemoryService()
        self.knowledge_service = KnowledgeBaseService()
        self.template_generator = ActionTemplateGenerator()
        self.history_service = ConversationHistoryService()
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.question_parser = PydanticOutputParser(pydantic_object=EnhancedQuestionResponse)
        self.action_plan_parser = PydanticOutputParser(pydantic_object=EnhancedActionPlanResponse)
        self.self_resolution_parser = PydanticOutputParser(pydantic_object=SelfResolutionResponse)
    
    async def initialize(self):
        """サービスの初期化"""
        await self.memory_service.initialize()
    
    async def start_dialogue(
        self,
        session_id: str,
        initial_context: Dict[str, Any],
        user_id: Optional[str] = None,
        db_session: Optional[Any] = None
    ) -> Tuple[List[str], Dict[str, Any]]:
        """対話セッションを開始（改善版 + 会話履歴活用）"""
        
        # 初期コンテキストから関連知識を検索
        topic = initial_context.get("topic", "")
        relevant_knowledge = await self.knowledge_service.search_knowledge(topic)
        
        # 会社の価値観を取得
        company_values = await self.knowledge_service.get_company_values()
        
        # ユーザーの過去の会話履歴と洞察を取得
        past_insights = []
        user_profile = None
        conversation_history = []
        
        if user_id and db_session:
            # 過去の会話履歴を取得
            conversation_history = await self.history_service.get_user_conversation_history(
                user_id=user_id,
                db=db_session,
                limit=5
            )
            
            # 過去の洞察を取得
            past_insights = await self.history_service.get_relevant_past_insights(
                user_id=user_id,
                current_topic=topic,
                db=db_session
            )
            
            # ユーザープロファイルを取得
            from sqlalchemy import select
            from app.models.dialogue import UserProfile
            profile_result = await db_session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            user_profile = profile_result.scalar_one_or_none()
        
        # パーソナライズされた質問生成のプロンプト
        prompt = ChatPromptTemplate.from_messages([
            ("system", """あなたは新人営業マンの成長を支援するAIアシスタントです。
            会社のミッション・ビジョン・バリューに基づいて、営業スキル向上のための支援を行います。
            
            会社の価値観：
            {company_values}
            
            関連する社内ナレッジ：
            {relevant_knowledge}
            
            初期コンテキスト：
            {initial_context}
            
            過去の洞察：
            {past_insights}
            
            ユーザープロファイル：
            {user_profile}
            
            以下の点を考慮して、効果的な質問を生成してください：
            1. まず社内ナレッジから回答できる部分は自己解決する
            2. 過去の会話で既に議論した内容は繰り返さない
            3. ユーザーの傾向や好みに合わせてパーソナライズする
            4. 本当に新人から聞く必要がある情報のみ質問する
            5. 質問の負荷を最小限に抑える
            6. 具体的で答えやすい質問にする
            
            {format_instructions}
            """),
            ("user", "社内ナレッジと過去の履歴を活用しながら、最適な質問を生成してください。")
        ])
        
        # チェーン構築
        chain = (
            {
                "initial_context": RunnablePassthrough(),
                "company_values": lambda _: json.dumps(company_values, ensure_ascii=False),
                "relevant_knowledge": lambda _: json.dumps(relevant_knowledge, ensure_ascii=False),
                "past_insights": lambda _: json.dumps(past_insights, ensure_ascii=False),
                "user_profile": lambda _: json.dumps({
                    "common_challenges": user_profile.common_challenges if user_profile else [],
                    "strengths": user_profile.strengths if user_profile else [],
                    "learning_style": user_profile.preferred_learning_style if user_profile else None
                }, ensure_ascii=False),
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
            "completeness_score": response.completeness_score,
            "self_resolved_insights": response.self_resolved_insights,
            "suggested_resources": response.suggested_resources,
            "knowledge_used": len(relevant_knowledge) > 0,
            "history_used": len(past_insights) > 0,
            "user_sessions_count": user_profile.total_sessions if user_profile else 0
        }
        
        return response.questions, metadata
    
    async def self_resolve_questions(
        self,
        questions: List[str],
        context: Dict[str, Any]
    ) -> SelfResolutionResponse:
        """質問の自己解決を試みる"""
        
        resolved = []
        remaining = []
        sources = []
        
        for question in questions:
            # 知識ベースから回答を検索
            knowledge_results = await self.knowledge_service.search_knowledge(question)
            
            if knowledge_results:
                # 知識が見つかった場合
                best_match = knowledge_results[0]
                resolved.append({
                    "question": question,
                    "answer": f"社内ナレッジより: {json.dumps(best_match['content'], ensure_ascii=False)}",
                    "source": best_match['category']
                })
                sources.append(best_match['category'])
            else:
                # 解決できない場合
                remaining.append(question)
        
        confidence = "high" if len(resolved) > len(remaining) else "medium" if resolved else "low"
        
        return SelfResolutionResponse(
            resolved_questions=resolved,
            remaining_questions=remaining,
            confidence_level=confidence,
            sources_used=list(set(sources))
        )
    
    async def process_user_response(
        self,
        session_id: str,
        user_response: str,
        db_session: Any,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """ユーザーの回答を処理（改善版 + 会話履歴活用）"""
        
        # メモリに回答を追加
        await self.memory_service.add_message(
            session_id=session_id,
            role="user",
            content=user_response,
            db=db_session
        )
        
        # 現在のコンテキストを取得
        context = await self.memory_service.get_conversation_context(
            session_id=session_id,
            include_summary=True
        )
        
        # ユーザーの回答から課題を抽出
        challenges = await self._extract_challenges(user_response)
        
        # 各課題に対する解決策を知識ベースから検索
        solutions = []
        for challenge in challenges:
            solution = await self.knowledge_service.get_solution_for_challenge(challenge)
            if solution:
                solutions.append(solution)
        
        # 過去の洞察を活用
        past_insights = []
        user_profile = None
        
        if user_id and db_session:
            # 現在の会話から洞察を抽出して保存
            conversation_history = [context]
            insights = await self.history_service.extract_insights_from_history(
                user_id=user_id,
                conversation_history=conversation_history
            )
            
            # 洞察を保存
            await self.history_service.save_insights(
                user_id=user_id,
                session_id=session_id,
                insights=insights,
                db=db_session
            )
            
            # ユーザープロファイルを更新
            user_profile = await self.history_service.update_user_profile(
                user_id=user_id,
                insights=insights,
                db=db_session
            )
            
            # 会話パターンを保存
            if insights.patterns:
                await self.history_service.save_conversation_patterns(
                    user_id=user_id,
                    patterns=insights.patterns,
                    db=db_session
                )
            
            # 関連する過去の洞察を取得
            topic = challenges[0] if challenges else "営業スキル"
            past_insights = await self.history_service.get_relevant_past_insights(
                user_id=user_id,
                current_topic=topic,
                db=db_session
            )
        
        # 情報の充足度を評価（過去の洞察も考慮）
        completeness_score = await self._evaluate_completeness_with_history(
            context, solutions, past_insights
        )
        
        if completeness_score >= 75:  # 閾値を下げて早めにアクションプラン生成
            # アクションプラン生成（テンプレート付き + 過去の成功事例）
            action_plan = await self._generate_enhanced_action_plan_with_history(
                context, challenges, solutions, past_insights, user_profile
            )
            return {
                "type": "action_plan",
                "data": action_plan,
                "completeness_score": completeness_score,
                "solutions_found": solutions,
                "past_insights_used": len(past_insights)
            }
        else:
            # パーソナライズされたフォローアップ質問を生成
            if user_profile and past_insights:
                follow_up_questions = await self.history_service.generate_personalized_questions(
                    user_id=user_id,
                    current_context=context,
                    user_profile=user_profile,
                    past_insights=past_insights
                )
            else:
                follow_up_questions = await self._generate_smart_follow_up_questions(context, solutions)
            
            # 自己解決を試みる
            self_resolution = await self.self_resolve_questions(follow_up_questions, context)
            
            # 本当に必要な質問のみ返す
            return {
                "type": "follow_up",
                "questions": self_resolution.remaining_questions,
                "completeness_score": completeness_score,
                "self_resolved": self_resolution.resolved_questions,
                "confidence": self_resolution.confidence_level,
                "personalized": user_profile is not None
            }
    
    async def _extract_challenges(self, user_response: str) -> List[str]:
        """ユーザーの回答から課題を抽出"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """営業担当者の発言から具体的な課題や困りごとを抽出してください。
            
            例：
            - 「緊張して頭が真っ白になる」→「プレゼン時の緊張」
            - 「新規開拓がうまくいかない」→「新規顧客開拓」
            - 「断られるのが怖い」→「拒絶への恐怖」
            
            課題を短い名詞句で、カンマ区切りで列挙してください。"""),
            ("user", f"発言: {user_response}\n\n課題:")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        challenges = [c.strip() for c in response.content.split(",")]
        return challenges
    
    async def _evaluate_completeness(
        self,
        context: Dict[str, Any],
        solutions: List[Dict[str, Any]]
    ) -> int:
        """情報の充足度を評価（改善版）"""
        base_score = 20  # 基本スコア
        
        # 会話回数によるスコア
        if "conversation_history" in context:
            message_count = len(context["conversation_history"])
            base_score += min(message_count * 15, 40)
        
        # 解決策が見つかった場合のボーナス
        if solutions:
            base_score += len(solutions) * 10
        
        # 具体的な情報が含まれているかチェック
        context_str = json.dumps(context, ensure_ascii=False)
        if any(keyword in context_str for keyword in ["目標", "現在", "課題", "困って"]):
            base_score += 15
        
        return min(base_score, 100)
    
    async def _generate_smart_follow_up_questions(
        self,
        context: Dict[str, Any],
        existing_solutions: List[Dict[str, Any]]
    ) -> List[str]:
        """スマートなフォローアップ質問を生成"""
        
        # すでに解決策がある部分は除外
        solved_challenges = [sol["challenge"] for sol in existing_solutions]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """これまでの会話と既存の解決策を踏まえて、
            本当に必要な追加情報のみを収集する質問を生成してください。
            
            すでに解決策がある課題：
            {solved_challenges}
            
            以下の原則に従ってください：
            1. すでに解決策がある部分は質問しない
            2. 具体的で答えやすい質問にする
            3. 質問数は最小限（1-3個）に抑える
            4. アクションプラン作成に直結する情報のみ聞く"""),
            ("user", "会話履歴：{context}\n\n追加で必要な質問:")
        ])
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({
            "context": json.dumps(context, ensure_ascii=False),
            "solved_challenges": json.dumps(solved_challenges, ensure_ascii=False)
        })
        
        # 質問を抽出
        questions = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # 番号や記号を除去
                clean_line = line.lstrip('1234567890.-・ ')
                if clean_line:
                    questions.append(clean_line)
        
        return questions[:3]  # 最大3個
    
    async def _generate_enhanced_action_plan(
        self,
        context: Dict[str, Any],
        challenges: List[str],
        solutions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """強化されたアクションプランを生成"""
        
        # メインの課題を特定
        main_challenge = challenges[0] if challenges else "営業スキル向上"
        
        # テンプレートジェネレーターでアクションプランを生成
        template_plan = await self.template_generator.generate_action_plan(
            challenge=main_challenge,
            context=context,
            timeline="1ヶ月"
        )
        
        # ベストプラクティスを取得
        best_practices = await self.knowledge_service.get_best_practices(main_challenge)
        
        # 先輩の成功事例を参照
        mentor_suggestions = []
        if best_practices:
            for practice in best_practices:
                if "senior_examples" in practice.get("source", ""):
                    mentor_suggestions.extend(practice.get("practices", []))
        
        # LLMでアクションプランを統合・カスタマイズ
        prompt = ChatPromptTemplate.from_messages([
            ("system", """会話内容、テンプレート、社内ナレッジを統合して、
            パーソナライズされたアクションプランを作成してください。
            
            テンプレートプラン：
            {template_plan}
            
            解決策：
            {solutions}
            
            ベストプラクティス：
            {best_practices}
            
            以下を含めてください：
            1. 具体的なアクションアイテム（テンプレート活用）
            2. 各アクションの詳細な実行方法
            3. 成功指標と期限
            4. 参考にすべき先輩の事例
            
            {format_instructions}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "統合されたアクションプランを作成してください。")
        ])
        
        memory = await self.memory_service.get_or_create_memory(context["session_id"])
        messages = memory.chat_memory.messages
        
        chain = (
            {
                "chat_history": lambda _: messages,
                "template_plan": lambda _: json.dumps(template_plan, ensure_ascii=False),
                "solutions": lambda _: json.dumps(solutions, ensure_ascii=False),
                "best_practices": lambda _: json.dumps(best_practices, ensure_ascii=False),
                "format_instructions": lambda _: self.action_plan_parser.get_format_instructions()
            }
            | prompt
            | self.llm
            | self.action_plan_parser
        )
        
        response = await chain.ainvoke({})
        
        # レスポンスを強化
        enhanced_response = {
            "action_items": response.action_items,
            "templates_provided": template_plan.get("templates_used", []),
            "summary": response.summary,
            "key_improvements": response.key_improvements,
            "metrics": response.metrics,
            "knowledge_references": [
                {
                    "type": sol["challenge"],
                    "content": sol["solution"]
                }
                for sol in solutions
            ],
            "mentor_suggestions": mentor_suggestions[:5],  # 最大5個
            "generated_at": datetime.utcnow().isoformat(),
            "template_details": template_plan
        }
        
        return enhanced_response
    
    async def _evaluate_completeness_with_history(
        self,
        context: Dict[str, Any],
        solutions: List[Dict[str, Any]],
        past_insights: List[Dict[str, Any]]
    ) -> int:
        """情報の充足度を評価（過去の洞察も含む）"""
        
        # 基本評価
        base_score = await self._evaluate_completeness(context, solutions)
        
        # 過去の洞察によるボーナス
        if past_insights:
            # 高い関連性の洞察がある場合
            high_relevance_insights = [i for i in past_insights if i.get("relevance", 0) > 0.7]
            base_score += len(high_relevance_insights) * 5
            
            # 確信度の高い洞察がある場合
            high_confidence_insights = [i for i in past_insights if i.get("confidence", 0) > 0.8]
            base_score += len(high_confidence_insights) * 3
        
        return min(base_score, 100)
    
    async def _generate_enhanced_action_plan_with_history(
        self,
        context: Dict[str, Any],
        challenges: List[str],
        solutions: List[Dict[str, Any]],
        past_insights: List[Dict[str, Any]],
        user_profile: Optional[Any]
    ) -> Dict[str, Any]:
        """過去の洞察を活用した強化されたアクションプランを生成"""
        
        # ベースのアクションプランを生成
        base_plan = await self._generate_enhanced_action_plan(context, challenges, solutions)
        
        # 過去の洞察を統合
        if past_insights:
            # 過去の成功パターンを抽出
            success_patterns = []
            for insight in past_insights:
                if insight["type"] == "strength" or insight["type"] == "success_pattern":
                    success_patterns.append(insight["content"])
            
            # アクションプランに過去の成功パターンを追加
            base_plan["past_success_patterns"] = success_patterns[:3]  # 最大3個
            base_plan["insights_integrated"] = True
            base_plan["insights_count"] = len(past_insights)
        
        # ユーザープロファイルに基づくカスタマイズ
        if user_profile:
            # 学習スタイルに合わせた調整
            if user_profile.preferred_learning_style:
                base_plan["learning_style_adjusted"] = True
                base_plan["preferred_learning_style"] = user_profile.preferred_learning_style
                
                # アクションアイテムを学習スタイルに合わせて調整
                if user_profile.preferred_learning_style == "visual":
                    for item in base_plan["action_items"]:
                        item["visual_aids"] = "図表やビジュアルツールの活用を推奨"
                elif user_profile.preferred_learning_style == "practical":
                    for item in base_plan["action_items"]:
                        item["practice_emphasis"] = "実践的な練習を重視"
            
            # 成功率データを追加
            base_plan["user_stats"] = {
                "total_sessions": user_profile.total_sessions,
                "completed_actions": user_profile.completed_actions,
                "success_rate": user_profile.success_rate
            }
        
        return base_plan