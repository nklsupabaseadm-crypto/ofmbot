from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,          # set True to see SQL queries in logs
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # drops stale connections automatically
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency — yields a fresh DB session per request."""
    async with async_session_factory() as session:
        yield session
