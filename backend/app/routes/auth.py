"""认证路由：注册 / 登录 / 刷新令牌 / 当前用户"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
    RoleChecker,
)
from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查用户名 / 邮箱是否已存在
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name or body.username,
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录，返回 access_token + refresh_token"""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id), user.role)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """使用 refresh_token 换取新的 access_token"""
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的刷新令牌")

    user_id = payload.get("sub")
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="无效的令牌标识")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    new_access = create_access_token(str(user.id), user.role)
    new_refresh = create_refresh_token(str(user.id), user.role)

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户信息"""
    return current_user


@router.put("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.hashed_password = hash_password(new_password)
    await db.flush()
    return {"message": "密码修改成功"}
