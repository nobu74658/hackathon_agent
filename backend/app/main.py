from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import logging

from app.core.config import settings
from app.api.test_endpoints import router as test_router
from app.api.llm_demo_endpoints import router as demo_router

# ロギング設定
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(test_router)
app.include_router(demo_router)


# テスト用のモデル
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ConversationTestRequest(BaseModel):
    session_id: str
    message: str
    context: Dict[str, Any] = {}


class ConversationTestResponse(BaseModel):
    session_id: str
    response: str
    metadata: Dict[str, Any] = {}


# ヘルスチェックエンドポイント
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェック"""
    from datetime import datetime
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat()
    )


# 設定確認エンドポイント
@app.get("/config")
async def get_config():
    """設定情報の確認（セキュリティ情報は除く）"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "cors_origins": settings.CORS_ORIGINS,
        "log_level": settings.LOG_LEVEL
    }


# シンプルな対話テスト用エンドポイント
@app.post("/test/conversation", response_model=ConversationTestResponse)
async def test_conversation(request: ConversationTestRequest):
    """対話システムの基本テスト"""
    try:
        # シンプルなエコーレスポンス
        response_message = f"受信したメッセージ: {request.message}"
        
        metadata = {
            "session_id": request.session_id,
            "message_length": len(request.message),
            "has_context": bool(request.context),
            "processed_at": "2024-01-01T00:00:00Z"  # ダミータイムスタンプ
        }
        
        return ConversationTestResponse(
            session_id=request.session_id,
            response=response_message,
            metadata=metadata
        )
    
    except Exception as e:
        logger.error(f"Conversation test error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# LangChain機能のテスト（API呼び出しなし）
@app.post("/test/langchain-structure")
async def test_langchain_structure():
    """LangChainサービスの構造テスト（実際のAPI呼び出しなし）"""
    try:
        # サービスクラスの import テスト
        from app.services.conversation_memory import ConversationMemoryService
        from app.services.dialogue_manager import DialogueManager
        
        # インスタンス作成テスト
        memory_service = ConversationMemoryService()
        dialogue_manager = DialogueManager()
        
        return {
            "status": "success",
            "message": "LangChainサービスクラスの作成に成功",
            "services": {
                "memory_service": type(memory_service).__name__,
                "dialogue_manager": type(dialogue_manager).__name__
            }
        }
        
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Import error: {str(e)}",
            "type": "import_error"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Unexpected error: {str(e)}",
            "type": "general_error"
        }


# 依存関係テスト
@app.get("/test/dependencies")
async def test_dependencies():
    """必要な依存関係のテスト"""
    dependencies = {}
    
    # FastAPI
    try:
        import fastapi
        dependencies["fastapi"] = fastapi.__version__
    except ImportError:
        dependencies["fastapi"] = "not installed"
    
    # Pydantic
    try:
        import pydantic
        dependencies["pydantic"] = pydantic.__version__
    except ImportError:
        dependencies["pydantic"] = "not installed"
    
    # LangChain (オプショナル)
    try:
        import langchain
        dependencies["langchain"] = langchain.__version__
    except ImportError:
        dependencies["langchain"] = "not installed"
    
    # SQLAlchemy (将来用)
    try:
        import sqlalchemy
        dependencies["sqlalchemy"] = sqlalchemy.__version__
    except ImportError:
        dependencies["sqlalchemy"] = "not installed"
    
    return {
        "status": "checked",
        "dependencies": dependencies
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG
    )