try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from functools import lru_cache
import secrets

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
        # 添加更多信任的域名...
    ]

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()