"""
Async SQLAlchemy Engine and Session configuration.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from aitester.core.config import settings

from sqlalchemy.pool import NullPool

# Define pool arguments dynamically based on environment
pool_kwargs = {}
if getattr(settings, "ENVIRONMENT", "").lower() == "testing" or "test" in settings.DATABASE_URL:
    pool_kwargs["poolclass"] = NullPool
else:
    pool_kwargs["pool_size"] = 20
    pool_kwargs["max_overflow"] = 10

# Create the async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    **pool_kwargs
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.
    Closes the session automatically after the request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session
