 """多模型配置管理"""
 from __future__ import annotations

 import json
 from typing import Any

 from pydantic_settings import BaseSettings


 class ModelConfig(BaseSettings):
     """单个 LLM 模型实例配置"""
     name: str
     provider: str
     api_key: str
     base_url: str = ""
     model_id: str = ""
     is_default: bool = False
     is_active: bool = True
     max_tokens: int = 4096
     context_window: int = 128000
     metadata_: dict[str, Any] = {}

     class Config:
         populate_by_name = True


 class Settings(BaseSettings):
     ENV: str = "development"
     DATABASE_URL: str = "postgresql+asyncpg://admin:secret@postgres:5432/competitive_intel"
     DATABASE_URL_SYNC: str = "postgresql://admin:secret@postgres:5432/competitive_intel"
     REDIS_URL: str = "redis://:redispass@redis:6379/0"
     CELERY_BROKER_URL: str = "amqp://admin:admin@rabbitmq:5672//"
     CELERY_RESULT_BACKEND: str = "redis://:redispass@redis:6379/1"
     SECRET_KEY: str = "change-me-in-production"
     JWT_SECRET_KEY: str = "jwt-secret-change-me-in-production"
     JWT_ALGORITHM: str = "HS256"
     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
     REFRESH_TOKEN_EXPIRE_DAYS: int = 7
     CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8080", "http://localhost:3000"]
     OPENAI_API_KEY: str = ""
     OPENAI_API_BASE: str = ""
     OPENAI_MODEL: str = "gpt-4o-mini"
     GOOGLE_API_KEY: str = ""
     MODEL_CONFIGS_JSON: str = ""

     @property
     def model_configs(self) -> list[ModelConfig]:
         if not self.MODEL_CONFIGS_JSON:
             return []
         try:
             raw = json.loads(self.MODEL_CONFIGS_JSON)
             if isinstance(raw, list):
                 return [ModelConfig(**item) for item in raw]
             return []
         except (json.JSONDecodeError, TypeError):
             return []

     @property
     def default_model(self) -> ModelConfig | None:
         for mc in self.model_configs:
             if mc.is_default and mc.is_active:
                 return mc
         for mc in self.model_configs:
             if mc.is_active:
                 return mc
         return None

     @property
     def active_model_names(self) -> list[str]:
         return [mc.name for mc in self.model_configs if mc.is_active]

     class Config:
         env_file = ".env"


 settings = Settings()


 def parse_model_configs(json_str: str) -> list[ModelConfig]:
     if not json_str:
         return []
     try:
         raw = json.loads(json_str)
         if isinstance(raw, list):
             return [ModelConfig(**item) for item in raw]
     except (json.JSONDecodeError, TypeError):
         pass
     return []


 def serialize_model_configs(configs: list[ModelConfig]) -> str:
     data = []
     for c in configs:
         d = c.model_dump(by_alias=True, exclude_unset=True)
         data.append(d)
     return json.dumps(data, ensure_ascii=False)
