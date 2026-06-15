"""应用配置"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 环境
    ENV: str = "development"

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://admin:secret@postgres:5432/competitive_intel"
    DATABASE_URL_SYNC: str = "postgresql://admin:secret@postgres:5432/competitive_intel"

    # Redis
    REDIS_URL: str = "redis://:redispass@redis:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "amqp://admin:admin@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "redis://:redispass@redis:6379/1"

    # 安全
    SECRET_KEY: str = "change-me-in-production"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    # API 密钥
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
