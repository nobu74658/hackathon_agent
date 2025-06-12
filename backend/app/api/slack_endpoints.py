from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import logging
from app.services.slack_service import get_slack_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/slack/events")
async def slack_events(request: Request):
    """Slack Events APIのエンドポイント"""
    try:
        # Slackの認証情報が設定されているかチェック
        if not settings.SLACK_BOT_TOKEN or not settings.SLACK_SIGNING_SECRET:
            raise HTTPException(status_code=500, detail="Slack credentials not configured")
        
        slack_service = get_slack_service()
        handler = await slack_service.get_handler()
        
        # Slack Bolt のハンドラーに委譲
        return await handler.handle(request)
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/slack/install")
async def slack_install():
    """Slack App インストール用エンドポイント（将来的に使用）"""
    return {"message": "Slack App installation endpoint"}


@router.get("/slack/oauth")
async def slack_oauth():
    """Slack OAuth認証用エンドポイント（将来的に使用）"""
    return {"message": "Slack OAuth endpoint"}


@router.get("/slack/health")
async def slack_health():
    """Slack統合のヘルスチェック"""
    try:
        # 設定のチェック
        if not settings.SLACK_BOT_TOKEN:
            return {"status": "error", "message": "SLACK_BOT_TOKEN not configured"}
        
        if not settings.SLACK_SIGNING_SECRET:
            return {"status": "error", "message": "SLACK_SIGNING_SECRET not configured"}
        
        # Slack serviceの初期化チェック
        slack_service = get_slack_service()
        
        return {
            "status": "healthy",
            "message": "Slack integration is configured and ready",
            "use_mock_llm": settings.USE_MOCK_LLM
        }
        
    except Exception as e:
        logger.error(f"Slack health check failed: {e}")
        return {"status": "error", "message": f"Slack integration error: {str(e)}"}