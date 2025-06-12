"""
改善されたLLM APIエンドポイント
知識ベースと自己解決機能を持つ対話システム
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import logging

from app.services.enhanced_dialogue_manager import EnhancedDialogueManager
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.action_template_generator import ActionTemplateGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced", tags=["enhanced-llm"])

# グローバルなセッション管理
enhanced_sessions: Dict[str, Dict[str, Any]] = {}
dialogue_manager = EnhancedDialogueManager()
knowledge_service = KnowledgeBaseService()
template_generator = ActionTemplateGenerator()


class StartEnhancedSessionRequest(BaseModel):
    user_name: str
    department: str = "営業部"
    experience_years: int = 1
    initial_topic: str = "営業スキル向上"
    specific_challenge: Optional[str] = None


class StartEnhancedSessionResponse(BaseModel):
    session_id: str
    questions: List[str]
    reasoning: str
    self_resolved_insights: List[Dict[str, Any]]
    suggested_resources: List[str]
    completeness_score: int
    knowledge_used: bool


class SendEnhancedMessageRequest(BaseModel):
    session_id: str
    message: str


class SendEnhancedMessageResponse(BaseModel):
    type: str  # "follow_up" or "action_plan"
    questions: Optional[List[str]] = None
    self_resolved: Optional[List[Dict[str, str]]] = None
    action_plan: Optional[Dict[str, Any]] = None
    completeness_score: int
    confidence: Optional[str] = None
    templates_provided: Optional[List[Dict[str, Any]]] = None
    knowledge_references: Optional[List[Dict[str, Any]]] = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None


class TemplateListResponse(BaseModel):
    templates: Dict[str, List[Dict[str, str]]]


@router.post("/start", response_model=StartEnhancedSessionResponse)
async def start_enhanced_session(request: StartEnhancedSessionRequest):
    """改善された対話セッション開始"""
    try:
        # セッションID生成
        session_id = str(uuid.uuid4())
        
        # 初期コンテキスト作成
        initial_context = {
            "user_name": request.user_name,
            "department": request.department,
            "experience_years": request.experience_years,
            "topic": request.initial_topic,
            "specific_challenge": request.specific_challenge,
            "session_started": datetime.utcnow().isoformat()
        }
        
        # 対話マネージャーを初期化
        await dialogue_manager.initialize()
        
        # 初期質問生成（知識ベース活用）
        logger.info(f"Generating initial questions with knowledge base for session {session_id}")
        questions, metadata = await dialogue_manager.start_dialogue(session_id, initial_context)
        
        # セッション情報を保存
        enhanced_sessions[session_id] = {
            "initial_context": initial_context,
            "conversation_history": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "metadata": metadata
        }
        
        logger.info(f"Enhanced session {session_id} started successfully")
        
        return StartEnhancedSessionResponse(
            session_id=session_id,
            questions=questions,
            reasoning=metadata.get("reasoning", ""),
            self_resolved_insights=metadata.get("self_resolved_insights", []),
            suggested_resources=metadata.get("suggested_resources", []),
            completeness_score=metadata.get("completeness_score", 0),
            knowledge_used=metadata.get("knowledge_used", False)
        )
        
    except Exception as e:
        logger.error(f"Error starting enhanced session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"セッション開始エラー: {str(e)}")


@router.post("/message", response_model=SendEnhancedMessageResponse)
async def send_enhanced_message(request: SendEnhancedMessageRequest):
    """改善されたメッセージ処理"""
    try:
        # セッション確認
        if request.session_id not in enhanced_sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session = enhanced_sessions[request.session_id]
        
        # 会話履歴に追加
        session["conversation_history"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session["last_activity"] = datetime.utcnow().isoformat()
        
        # メッセージ処理（知識ベースと自己解決機能付き）
        logger.info(f"Processing message with enhanced features for session {request.session_id}")
        result = await dialogue_manager.process_user_response(
            session_id=request.session_id,
            user_response=request.message,
            db_session=None  # デモ用なのでDBセッションはNone
        )
        
        # 結果に基づいてレスポンスを構築
        if result["type"] == "action_plan":
            action_plan_data = result["data"]
            return SendEnhancedMessageResponse(
                type="action_plan",
                action_plan=action_plan_data,
                completeness_score=result["completeness_score"],
                templates_provided=action_plan_data.get("templates_provided", []),
                knowledge_references=action_plan_data.get("knowledge_references", [])
            )
        else:
            return SendEnhancedMessageResponse(
                type="follow_up",
                questions=result.get("questions", []),
                self_resolved=result.get("self_resolved", []),
                completeness_score=result["completeness_score"],
                confidence=result.get("confidence", "medium")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing enhanced message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"メッセージ処理エラー: {str(e)}")


@router.post("/knowledge/search")
async def search_knowledge(request: KnowledgeSearchRequest):
    """知識ベース検索"""
    try:
        results = await knowledge_service.search_knowledge(
            query=request.query,
            category=request.category
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")


@router.get("/knowledge/company-values")
async def get_company_values():
    """会社の価値観を取得"""
    try:
        values = await knowledge_service.get_company_values()
        return values
    except Exception as e:
        logger.error(f"Error getting company values: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取得エラー: {str(e)}")


@router.get("/templates/list", response_model=TemplateListResponse)
async def list_templates():
    """利用可能なテンプレート一覧"""
    try:
        templates = await template_generator.list_available_templates()
        return TemplateListResponse(templates=templates)
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"一覧取得エラー: {str(e)}")


@router.get("/templates/{category}/{template_name}")
async def get_template_details(category: str, template_name: str):
    """特定テンプレートの詳細取得"""
    try:
        template = await template_generator.get_template_details(category, template_name)
        if not template:
            raise HTTPException(status_code=404, detail="テンプレートが見つかりません")
        
        return {
            "category": category,
            "name": template_name,
            "template": template
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取得エラー: {str(e)}")


@router.get("/session/{session_id}/insights")
async def get_session_insights(session_id: str):
    """セッションの洞察を取得"""
    if session_id not in enhanced_sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    session = enhanced_sessions[session_id]
    
    # 会話から得られた洞察をまとめる
    insights = {
        "session_id": session_id,
        "user_profile": {
            "name": session["initial_context"]["user_name"],
            "department": session["initial_context"]["department"],
            "experience_years": session["initial_context"]["experience_years"]
        },
        "identified_challenges": [],
        "self_resolved_count": 0,
        "knowledge_references_used": 0,
        "conversation_efficiency": {
            "total_messages": len(session["conversation_history"]),
            "questions_asked": 0,
            "questions_self_resolved": 0
        },
        "metadata": session.get("metadata", {})
    }
    
    # 会話履歴から洞察を抽出
    for msg in session["conversation_history"]:
        if msg["role"] == "assistant" and "self_resolved" in msg.get("metadata", {}):
            insights["self_resolved_count"] += len(msg["metadata"]["self_resolved"])
    
    return insights


@router.delete("/session/{session_id}")
async def delete_enhanced_session(session_id: str):
    """セッション削除"""
    if session_id in enhanced_sessions:
        del enhanced_sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")


@router.get("/demo/scenario/{scenario}")
async def run_demo_scenario(scenario: str):
    """デモシナリオ実行"""
    scenarios = {
        "nervous_presentation": {
            "name": "田中新人",
            "challenge": "プレゼンで緊張して頭が真っ白になる",
            "messages": [
                "明日大事なプレゼンがあるんですが、緊張して頭が真っ白になりそうで不安です",
                "いつも原稿を用意しているんですが、緊張すると忘れてしまいます",
                "先週も途中で言葉に詰まってしまい、上司にフォローしてもらいました"
            ]
        },
        "new_customer_acquisition": {
            "name": "鈴木営業",
            "challenge": "新規開拓がうまくいかない",
            "messages": [
                "テレアポをしているんですが、ほとんど断られてしまいます",
                "メールも送っているんですが、返信率が2-3%程度です",
                "月の目標は新規10社ですが、今月はまだ2社しか取れていません"
            ]
        }
    }
    
    if scenario not in scenarios:
        raise HTTPException(status_code=404, detail="シナリオが見つかりません")
    
    scenario_data = scenarios[scenario]
    
    # セッション開始
    start_request = StartEnhancedSessionRequest(
        user_name=scenario_data["name"],
        department="営業部",
        experience_years=1,
        initial_topic="営業スキル向上",
        specific_challenge=scenario_data["challenge"]
    )
    
    start_response = await start_enhanced_session(start_request)
    session_id = start_response.session_id
    
    # メッセージを順番に送信
    responses = []
    for message in scenario_data["messages"]:
        msg_request = SendEnhancedMessageRequest(
            session_id=session_id,
            message=message
        )
        response = await send_enhanced_message(msg_request)
        responses.append({
            "message": message,
            "response": response.dict()
        })
    
    return {
        "scenario": scenario,
        "session_id": session_id,
        "interactions": responses
    }