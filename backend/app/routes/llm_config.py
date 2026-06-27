"""LLM 模型配置路由 — CRUD（admin 权限保护）

端点列表：
  GET    /llm-config          列出所有模型配置
  POST   /llm-config          新增模型配置
  PUT    /llm-config/{id}     更新模型配置
  DELETE /llm-config/{id}     删除模型配置
  GET    /llm-config/models   列出可用模型（含状态）
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import RoleChecker
from app.config_multi_model import (
    ModelConfig,
    settings as multi_settings,
    parse_model_configs,
    serialize_model_configs,
)
from app.services.llm_enhanced import list_available_models

router = APIRouter()

require_admin = Depends(RoleChecker("admin"))


# ================================================================
#  Pydantic schemas
# ================================================================

class ModelConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    api_key: str = Field(..., min_length=1)
    base_url: str = ""
    model_id: str = ""
    is_default: bool = False
    is_active: bool = True
    max_tokens: int = 4096
    context_window: int = 128000
    metadata_: dict[str, Any] = Field(default={}, alias="metadata_")


class ModelConfigUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model_id: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    max_tokens: int | None = None
    context_window: int | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata_")


class ModelConfigResponse(ModelConfig):
    class Config:
        populate_by_name = True


# ================================================================
#  辅助：更新 MODEL_CONFIGS_JSON
# ================================================================

def _update_env_configs(configs: list[ModelConfig]) -> None:
    """持久化配置到环境变量（实际生产应写入数据库）"""
    json_str = serialize_model_configs(configs)
    # 注意：这里只更新内存中的 settings 对象
    # 生产环境应写入 .env 文件或配置管理服务
    import os
    os.environ["MODEL_CONFIGS_JSON"] = json_str


def _load_configs() -> list[ModelConfig]:
    return multi_settings.model_configs


def _save_configs(configs: list[ModelConfig]) -> None:
    _update_env_configs(configs)


# ================================================================
#  路由
# ================================================================

@router.get("", response_model=list[ModelConfigResponse])
async def list_configs(_user=require_admin):
    """列出所有模型配置"""
    configs = _load_configs()
    return configs


@router.post("", response_model=ModelConfigResponse, status_code=201)
async def create_config(payload: ModelConfigCreate, _user=require_admin):
    """新增模型配置"""
    configs = _load_configs()
    # 检查名称唯一性
    for c in configs:
        if c.name == payload.name:
            raise HTTPException(status_code=400, detail=f"模型名称 '{payload.name}' 已存在")
    new_cfg = ModelConfig(
        name=payload.name,
        provider=payload.provider,
        api_key=payload.api_key,
        base_url=payload.base_url,
        model_id=payload.model_id,
        is_default=payload.is_default,
        is_active=payload.is_active,
        max_tokens=payload.max_tokens,
        context_window=payload.context_window,
        metadata_=payload.metadata_,
    )
    configs.append(new_cfg)
    _save_configs(configs)
    return new_cfg


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_config(config_id: str, payload: ModelConfigUpdate, _user=require_admin):
    """更新模型配置"""
    configs = _load_configs()
    for i, c in enumerate(configs):
        if c.name == config_id or c.provider == config_id:
            update_data = payload.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                if v is not None:
                    setattr(configs[i], k, v)
            _save_configs(configs)
            return configs[i]
    raise HTTPException(status_code=404, detail=f"模型配置 '{config_id}' 不存在")


@router.delete("/{config_id}")
async def delete_config(config_id: str, _user=require_admin):
    """删除模型配置"""
    configs = _load_configs()
    new_configs = [c for c in configs if c.name != config_id and c.provider != config_id]
    if len(new_configs) == len(configs):
        raise HTTPException(status_code=404, detail=f"模型配置 '{config_id}' 不存在")
    _save_configs(new_configs)
    return {"status": "deleted", "config_id": config_id}


@router.get("/models")
async def available_models(_user=require_admin):
    """列出所有可用模型（含实时状态）"""
    models = list_available_models()
    return {"models": models, "total": len(models)}
