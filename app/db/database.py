from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Satu sumber DSN dari config; skema driver disesuaikan per jalur.
SYNC_URL = settings.DATABASE_DSN
# psycopg3 dipakai untuk dua jalur sekaligus, jadi tidak perlu driver kedua.
ASYNC_URL = SYNC_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_ENGINE_KWARGS = dict(
    pool_size=10,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.APP_ENV == "development",
)

# --- async ---
engine = create_async_engine(ASYNC_URL, **_ENGINE_KWARGS)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# --- sync ---
sync_engine = create_engine(SYNC_URL, **_ENGINE_KWARGS)

SyncSessionLocal = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
)

def get_sync_db() -> Generator[Session, None, None]:
    with SyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
