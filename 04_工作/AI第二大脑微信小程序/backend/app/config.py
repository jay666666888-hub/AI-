from pydantic_settings import BaseSettings
from functools import lru_cache
import os

from pydantic import ConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AI第二大脑"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/ai_brain"

    # JWT - CRITICAL: Must be set via environment variable in production!
    SECRET_KEY: str = ""  # 从环境变量加载，不允许为空
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7天

    # 微信小程序
    WX_APPID: str = ""
    WX_SECRET: str = ""

    # Telegram Mini App
    TELEGRAM_BOT_TOKEN: str = ""  # 从环境变量加载

    # CORS - Configure allowed origins for production
    #微信小程序安全域名列表
    CORS_ORIGINS: list = [
        "*",
        "http://localhost",
        "http://127.0.0.1",
        "http://198.18.0.1",
        "http://123.56.13.231",
    ]

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

def get_settings() -> Settings:
    return Settings()

settings = get_settings()