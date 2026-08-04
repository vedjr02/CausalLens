"""Neon Postgres connection.

Persistence is optional: if DATABASE_URL is unset the app runs fine and only
the "save/share a run" feature is unavailable. Statistical endpoints never
depend on the database.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def _normalise_url(url: str) -> str:
    """Point SQLAlchemy at the psycopg3 async driver.

    Neon hands out plain ``postgresql://`` URLs; SQLAlchemy needs an explicit
    driver to pick the async implementation.
    """
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine | None:
    """Lazily build the engine. Returns None when no database is configured."""
    global _engine, _sessionmaker

    settings = get_settings()
    if not settings.database_url:
        return None

    if _engine is None:
        _engine = create_async_engine(
            _normalise_url(settings.database_url),
            pool_pre_ping=True,
            # Neon's free tier suspends idle compute; keep the pool small and
            # recycle connections before Neon drops them underneath us.
            pool_size=5,
            max_overflow=5,
            pool_recycle=300,
        )
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    return _engine


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a database session."""
    if get_engine() is None:
        raise RuntimeError("DATABASE_URL is not configured")
    assert _sessionmaker is not None
    async with _sessionmaker() as session:
        yield session


async def dispose_engine() -> None:
    """Close pooled connections on shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
