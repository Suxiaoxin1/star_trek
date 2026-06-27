"""pytest 配置 — 测试基础设施

提供：
  - 异步测试支持 (pytest-asyncio)
  - 测试数据库会话 (覆盖 get_db)
  - 测试用 FastAPI 客户端 (httpx AsyncClient)
  - 测试用户创建工具
"""
import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.auth import hash_password, create_access_token
from app.database import get_db, Base
from app.main import app
from app.models import User


# ==================== 测试数据库 ====================
# 使用 SQLite 内存数据库进行测试，避免依赖 PostgreSQL
TEST_DB_URL = "sqlite+aiosqlite:///test.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """创建测试数据库表（session 级别，整个测试会话只执行一次）

    先删除旧 test.db 文件（可能残留上次测试数据），
    再 drop + create 确保表结构干净。
    """
    # 清理上次可能残留的数据库文件
    import os
    try:
        os.remove("test.db")
    except (FileNotFoundError, PermissionError):
        pass

    # 先 drop 再 create，确保表结构和数据都是干净的
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # 必须先释放引擎连接，才能删除 SQLite 文件（Windows 文件锁）
    await test_engine.dispose()
    # 清理测试数据库文件
    try:
        os.remove("test.db")
    except (FileNotFoundError, PermissionError):
        pass


@pytest_asyncio.fixture
async def db_session():
    """每个测试用例获取独立的数据库会话

    测试结束后统一 rollback，撤销本测试所有数据变更，确保测试之间互不干扰。
    路由中的 session.commit() 已在 client fixture 中被替换为 flush，不会真正提交。
    """
    async with TestSession() as session:
        yield session
        # 测试结束后回滚所有未提交的变更
        await session.rollback()


# ==================== FastAPI 客户端 ====================
@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """创建异步 HTTP 测试客户端，注入测试数据库会话

    关键：拦截 db_session.commit() 使其仅执行 flush（刷入事务缓冲区），
    避免路由真正提交数据到数据库。测试结束后由 db_session 统一 rollback，
    实现测试间数据隔离。
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # 保存原始 commit 方法，替换为仅 flush 的版本（测试隔离核心）
    original_commit = db_session.commit

    async def no_op_commit():
        """替换 commit：仅 flush 不真正提交，确保测试数据可回滚"""
        await db_session.flush()

    db_session.commit = no_op_commit

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 恢复原始 commit 方法
    db_session.commit = original_commit
    app.dependency_overrides.clear()


# ==================== 测试用户工具 ====================
@pytest_asyncio.fixture
async def admin_token(client: AsyncClient):
    """创建管理员用户并返回 access_token"""
    # 注册管理员
    resp = await client.post("/api/v1/auth/register", json={
        "username": "test_admin",
        "email": "admin@test.com",
        "password": "testpass123",
        "display_name": "测试管理员",
        "role": "admin",
    })
    # 登录获取 token
    resp = await client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def analyst_token(client: AsyncClient):
    """创建分析师用户并返回 access_token"""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "test_analyst",
        "email": "analyst@test.com",
        "password": "testpass123",
        "display_name": "测试分析师",
        "role": "analyst",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "test_analyst",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def viewer_token(client: AsyncClient):
    """创建观察者用户并返回 access_token"""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "test_viewer",
        "email": "viewer@test.com",
        "password": "testpass123",
        "display_name": "测试观察者",
        "role": "viewer",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "test_viewer",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    """构建 Authorization header"""
    return {"Authorization": f"Bearer {token}"}