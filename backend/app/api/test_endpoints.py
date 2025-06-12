"""
API key不要のテスト用エンドポイント
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uuid
from datetime import datetime

from app.services.mock_llm import MockDialogueManager
from app.core.config import settings

router = APIRouter(prefix="/test", tags=["test"])

# グローバルなモック対話マネージャー
mock_dialogue_manager = MockDialogueManager()


class StartDialogueRequest(BaseModel):
    user_id: str
    initial_context: Dict[str, Any] = {}


class StartDialogueResponse(BaseModel):
    session_id: str
    questions: List[str]
    metadata: Dict[str, Any]


class ProcessResponseRequest(BaseModel):
    session_id: str
    user_response: str


class ProcessResponseResponse(BaseModel):
    type: str  # "follow_up" or "action_plan"
    data: Dict[str, Any]
    completeness_score: int


@router.post("/dialogue/start", response_model=StartDialogueResponse)
async def start_test_dialogue(request: StartDialogueRequest):
    """テスト用対話セッション開始"""
    try:
        await mock_dialogue_manager.initialize()
        
        session_id = str(uuid.uuid4())
        questions, metadata = await mock_dialogue_manager.start_dialogue(
            session_id=session_id,
            initial_context=request.initial_context
        )
        
        return StartDialogueResponse(
            session_id=session_id,
            questions=questions,
            metadata=metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dialogue/respond", response_model=ProcessResponseResponse)
async def process_test_response(request: ProcessResponseRequest):
    """テスト用ユーザー回答処理"""
    try:
        result = await mock_dialogue_manager.process_user_response(
            session_id=request.session_id,
            user_response=request.user_response
        )
        
        return ProcessResponseResponse(
            type=result["type"],
            data=result.get("data", result.get("questions", [])),
            completeness_score=result["completeness_score"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dialogue/{session_id}/info")
async def get_test_session_info(session_id: str):
    """テスト用セッション情報取得"""
    session_info = mock_dialogue_manager.get_session_info(session_id)
    
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "message_count": len(session_info["messages"]),
        "stage": session_info["stage"],
        "created_at": session_info["created_at"],
        "last_messages": session_info["messages"][-3:]  # 最新3件のメッセージ
    }


@router.get("/dialogue/sessions")
async def list_test_sessions():
    """テスト用セッション一覧"""
    sessions = []
    for session_id, session_info in mock_dialogue_manager.sessions.items():
        sessions.append({
            "session_id": session_id,
            "stage": session_info["stage"],
            "message_count": len(session_info["messages"]),
            "created_at": session_info["created_at"]
        })
    
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


@router.delete("/dialogue/{session_id}")
async def clear_test_session(session_id: str):
    """テスト用セッション削除"""
    if session_id in mock_dialogue_manager.sessions:
        del mock_dialogue_manager.sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/config")
async def get_test_config():
    """テスト用設定情報"""
    return {
        "use_mock_llm": settings.USE_MOCK_LLM,
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "has_anthropic_key": bool(settings.ANTHROPIC_API_KEY),
        "environment": "development" if settings.DEBUG else "production"
    }