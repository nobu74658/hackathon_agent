"""
実際のLLM APIを使用するデモエンドポイント
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import logging

from app.services.real_llm_service import RealLLMService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["llm-demo"])

# グローバルなセッション管理（実際のプロダクションではRedis等を使用）
demo_sessions: Dict[str, Dict[str, Any]] = {}


class StartDemoRequest(BaseModel):
    user_name: str
    department: str = "営業部"
    experience_years: int = 1
    initial_topic: str = "営業スキル向上"
    llm_provider: str = "openai"  # "openai" or "anthropic"


class StartDemoResponse(BaseModel):
    session_id: str
    questions: List[str]
    reasoning: str
    information_gaps: List[str]
    completeness_score: int
    llm_provider: str


class SendMessageRequest(BaseModel):
    session_id: str
    message: str


class SendMessageResponse(BaseModel):
    type: str  # "follow_up" or "action_plan"
    questions: Optional[List[str]] = None
    action_plan: Optional[Dict[str, Any]] = None
    completeness_score: int
    reasoning: Optional[str] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None


def get_llm_service(provider: str = "openai") -> RealLLMService:
    """LLMサービスのDI"""
    try:
        return RealLLMService(provider=provider)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLMサービス初期化エラー: {str(e)}")


@router.post("/start", response_model=StartDemoResponse)
async def start_demo_session(request: StartDemoRequest):
    """デモセッション開始"""
    try:
        # セッションID生成
        session_id = str(uuid.uuid4())
        
        # 初期コンテキスト作成
        initial_context = {
            "user_name": request.user_name,
            "department": request.department,
            "experience_years": request.experience_years,
            "topic": request.initial_topic,
            "session_started": datetime.utcnow().isoformat()
        }
        
        # LLMサービス初期化
        llm_service = get_llm_service(request.llm_provider)
        
        # 初期質問生成
        logger.info(f"Generating initial questions for session {session_id}")
        question_response = await llm_service.generate_initial_questions(initial_context)
        
        # セッション情報を保存
        demo_sessions[session_id] = {
            "initial_context": initial_context,
            "conversation_history": [],
            "llm_provider": request.llm_provider,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Demo session {session_id} started successfully")
        
        return StartDemoResponse(
            session_id=session_id,
            questions=question_response.questions,
            reasoning=question_response.reasoning,
            information_gaps=question_response.information_gaps,
            completeness_score=question_response.completeness_score,
            llm_provider=request.llm_provider
        )
        
    except Exception as e:
        logger.error(f"Error starting demo session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"セッション開始エラー: {str(e)}")


@router.post("/message", response_model=SendMessageResponse)
async def send_demo_message(request: SendMessageRequest):
    """デモメッセージ送信"""
    try:
        # セッション確認
        if request.session_id not in demo_sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session = demo_sessions[request.session_id]
        
        # 会話履歴に追加
        session["conversation_history"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat()
        })
        session["last_activity"] = datetime.utcnow().isoformat()
        
        # LLMサービス取得
        llm_service = get_llm_service(session["llm_provider"])
        
        # 感情分析
        logger.info(f"Analyzing sentiment for session {request.session_id}")
        sentiment_analysis = await llm_service.analyze_conversation_sentiment(request.message)
        
        # 情報充足度評価
        logger.info(f"Evaluating completeness for session {request.session_id}")
        completeness_score = await llm_service.evaluate_information_completeness(
            session["conversation_history"]
        )
        
        # 80%以上の場合はアクションプラン生成
        if completeness_score >= 80:
            logger.info(f"Generating action plan for session {request.session_id}")
            action_plan = await llm_service.generate_action_plan(
                session["conversation_history"]
            )
            
            # アクションプランをセッションに保存
            session["action_plan"] = {
                "plan": action_plan.dict(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return SendMessageResponse(
                type="action_plan",
                action_plan=action_plan.dict(),
                completeness_score=completeness_score,
                sentiment_analysis=sentiment_analysis
            )
        
        else:
            # フォローアップ質問生成
            logger.info(f"Generating follow-up questions for session {request.session_id}")
            follow_up = await llm_service.generate_follow_up_questions(
                session["conversation_history"],
                completeness_score
            )
            
            return SendMessageResponse(
                type="follow_up",
                questions=follow_up.questions,
                completeness_score=completeness_score,
                reasoning=follow_up.reasoning,
                sentiment_analysis=sentiment_analysis
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"メッセージ処理エラー: {str(e)}")


@router.get("/session/{session_id}")
async def get_demo_session(session_id: str):
    """デモセッション情報取得"""
    if session_id not in demo_sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    session = demo_sessions[session_id]
    
    return {
        "session_id": session_id,
        "initial_context": session["initial_context"],
        "message_count": len(session["conversation_history"]),
        "conversation_history": session["conversation_history"],
        "llm_provider": session["llm_provider"],
        "created_at": session["created_at"],
        "last_activity": session["last_activity"],
        "has_action_plan": "action_plan" in session
    }


@router.get("/sessions")
async def list_demo_sessions():
    """デモセッション一覧"""
    sessions = []
    for session_id, session_data in demo_sessions.items():
        sessions.append({
            "session_id": session_id,
            "user_name": session_data["initial_context"]["user_name"],
            "llm_provider": session_data["llm_provider"],
            "message_count": len(session_data["conversation_history"]),
            "created_at": session_data["created_at"],
            "has_action_plan": "action_plan" in session_data
        })
    
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


@router.delete("/session/{session_id}")
async def clear_demo_session(session_id: str):
    """デモセッション削除"""
    if session_id in demo_sessions:
        del demo_sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")


@router.get("/config")
async def get_demo_config():
    """デモ設定情報"""
    return {
        "use_mock_llm": settings.USE_MOCK_LLM,
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "has_anthropic_key": bool(settings.ANTHROPIC_API_KEY),
        "openai_model": settings.OPENAI_MODEL,
        "anthropic_model": settings.ANTHROPIC_MODEL,
        "available_providers": []
    }


@router.get("/test-connection/{provider}")
async def test_llm_connection(provider: str):
    """LLM接続テスト"""
    try:
        llm_service = get_llm_service(provider)
        
        # 簡単なテストプロンプト
        test_context = {
            "test": "connection_test",
            "message": "Hello, this is a connection test."
        }
        
        response = await llm_service.generate_initial_questions(test_context)
        
        return {
            "status": "success",
            "provider": provider,
            "model": settings.OPENAI_MODEL if provider == "openai" else settings.ANTHROPIC_MODEL,
            "test_response": {
                "questions_count": len(response.questions),
                "has_reasoning": bool(response.reasoning),
                "completeness_score": response.completeness_score
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "provider": provider,
            "error": str(e)
        }