"""数据库连接配置"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_engine = None
_async_session = None


def get_engine():
    """延迟创建引擎，避免测试环境因缺少 asyncpg 而崩溃"""
    global _engine, _async_session
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.ENV == "development",
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
        _async_session = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _engine, _async_session


class Base(DeclarativeBase):
    pass



async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取异步数据库会话"""
    _, async_sess = get_engine()
    async with async_sess() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取异步数据库会话"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
