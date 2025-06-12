from pydantic_settings import BaseSettings
from typing import List, Union
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sales Growth AI Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"  # テスト用SQLite
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    
    # Redis (オプショナル)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    
    # Security
    SECRET_KEY: str = "test-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # LLM設定
    USE_MOCK_LLM: bool = True  # 開発・テスト時はモックを使用
    
    # OpenAI
    OPENAI_API_KEY: str = ""  # 実際のキーが必要な場合のみ設定
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Anthropic  
    ANTHROPIC_API_KEY: str = ""  # 実際のキーが必要な場合のみ設定
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    
    # Slack
    SLACK_BOT_TOKEN: str = ""  # Slack Bot User OAuth Token (xoxb-)
    SLACK_SIGNING_SECRET: str = ""  # Slack App Signing Secret
    SLACK_APP_TOKEN: str = ""  # Socket Mode用App-Level Token (xapp-)
    
    # CORS - 文字列またはリストを受け付ける
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8080"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_PERIOD: int = 60
    
    @property
    def cors_origins_list(self) -> List[str]:
        """CORS_ORIGINSをリスト形式で取得"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()