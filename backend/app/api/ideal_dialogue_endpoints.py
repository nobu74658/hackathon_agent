"""
理想的な対話シナリオのAPIエンドポイント

ソクラテス式質問法による部下の成長支援を提供します。
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from app.services.ideal_dialogue_workflow import (
    IdealDialogueWorkflow,
    DialogueState
)
from app.core.dependencies import get_db


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ideal-dialogue", tags=["ideal_dialogue"])

# グローバルインスタンス（本番環境では適切な依存性注入を使用）
dialogue_workflow = IdealDialogueWorkflow()


class StartSessionRequest(BaseModel):
    """セッション開始リクエスト"""
    abstract_instruction: str = Field(
        ...,
        description="上司からの抽象的な指示",
        example="もっと顧客との関係を深めて売上を伸ばしてほしい"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="部下の情報（役職、経験年数など）",
        example={"role": "新人営業担当", "experience": "6ヶ月", "name": "田中"}
    )


class ProcessResponseRequest(BaseModel):
    """回答処理リクエスト"""
    session_id: str = Field(..., description="セッションID")
    user_response: str = Field(
        ...,
        description="部下の回答",
        example="今月も目標の85%でした。新規開拓が8割、既存顧客フォローが2割くらいです。"
    )


class DialogueResponse(BaseModel):
    """対話レスポンス"""
    type: str = Field(..., description="レスポンスタイプ（greeting, question, summary）")
    message: str = Field(..., description="AIコーチからのメッセージ")
    session_id: Optional[str] = Field(None, description="セッションID")
    state: Optional[str] = Field(None, description="現在の対話状態")
    purpose: Optional[str] = Field(None, description="質問の目的")
    expected_outcome: Optional[str] = Field(None, description="期待される成果")
    progress: Optional[Dict[str, Any]] = Field(None, description="進捗情報")
    action_plan: Optional[Dict[str, Any]] = Field(None, description="アクションプラン")
    insights: Optional[Dict[str, Any]] = Field(None, description="洞察")


@router.post("/start", response_model=DialogueResponse)
async def start_dialogue_session(
    request: StartSessionRequest,
    db=Depends(get_db)
) -> DialogueResponse:
    """理想的な対話セッションを開始"""
    try:
        # セッションIDを生成（実際の実装では適切なID生成を使用）
        import uuid
        session_id = f"ideal_{uuid.uuid4().hex[:8]}"
        
        result = await dialogue_workflow.start_session(
            session_id=session_id,
            abstract_instruction=request.abstract_instruction,
            user_context=request.user_context
        )
        
        return DialogueResponse(
            type=result["type"],
            message=result["message"],
            session_id=result["session_id"],
            state=result.get("next_state")
        )
        
    except Exception as e:
        logger.error(f"Failed to start dialogue session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/respond", response_model=DialogueResponse)
async def process_user_response(
    request: ProcessResponseRequest,
    db=Depends(get_db)
) -> DialogueResponse:
    """部下の回答を処理して次の質問を生成"""
    try:
        result = await dialogue_workflow.process_response(
            session_id=request.session_id,
            user_response=request.user_response
        )
        
        return DialogueResponse(
            type=result["type"],
            message=result["message"],
            session_id=request.session_id,
            state=result.get("state"),
            purpose=result.get("purpose"),
            expected_outcome=result.get("expected_outcome"),
            progress=result.get("progress"),
            action_plan=result.get("action_plan"),
            insights=result.get("insights")
        )
        
    except Exception as e:
        logger.error(f"Failed to process response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/progress")
async def get_session_progress(
    session_id: str,
    db=Depends(get_db)
) -> Dict[str, Any]:
    """セッションの進捗を取得"""
    try:
        session = dialogue_workflow.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        progress = dialogue_workflow._calculate_progress(session)
        
        return {
            "session_id": session_id,
            "abstract_instruction": session["abstract_instruction"],
            "current_state": session["state"].value,
            "progress": progress,
            "dialogue_count": len(session["dialogue_history"]),
            "discovered_patterns": session.get("discovered_patterns", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_dialogue_history(
    session_id: str,
    db=Depends(get_db)
) -> Dict[str, Any]:
    """対話履歴を取得"""
    try:
        session = dialogue_workflow.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "abstract_instruction": session["abstract_instruction"],
            "user_context": session.get("user_context"),
            "dialogue_history": session["dialogue_history"],
            "created_at": session.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dialogue history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def end_session(
    session_id: str,
    db=Depends(get_db)
) -> Dict[str, str]:
    """セッションを終了"""
    try:
        if session_id in dialogue_workflow.sessions:
            del dialogue_workflow.sessions[session_id]
            return {"message": "Session ended successfully", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "service": "ideal_dialogue",
        "active_sessions": len(dialogue_workflow.sessions)
    }