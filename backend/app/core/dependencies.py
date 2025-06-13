"""
FastAPI Dependencies

共通の依存性注入を定義します。
"""

from typing import Generator
import logging

logger = logging.getLogger(__name__)


def get_db() -> Generator[None, None, None]:
    """
    データベースセッションの依存性注入
    
    現在はダミー実装。将来的にSQLAlchemyのセッション管理を追加予定。
    """
    # 現在はダミー実装
    db = None
    try:
        yield db
    finally:
        # 将来的にはセッションのクローズ処理
        pass


def get_current_user():
    """
    現在のユーザー情報の依存性注入
    
    将来的にJWT認証やセッション管理を追加予定。
    """
    # 現在はダミー実装
    return {"user_id": "anonymous", "role": "user"}


def get_logger() -> logging.Logger:
    """
    ロガーの依存性注入
    """
    return logging.getLogger(__name__)