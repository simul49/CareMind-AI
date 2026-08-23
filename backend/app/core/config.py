from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    # Database
    DATABASE_URL: str = (
        "mysql+pymysql://caremind:caremind_dev@localhost:3306/caremind_ai"
    )

    # Auth
    SECRET_KEY: str = "caremind-dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # AI
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.deepseek.com/v1"
    AI_MODEL: str = "deepseek-chat"
    AI_TIMEOUT_SECONDS: float = 45.0

    # App
    APP_NAME: str = "CareMind AI"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
