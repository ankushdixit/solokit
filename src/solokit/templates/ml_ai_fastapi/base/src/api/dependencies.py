"""
FastAPI dependency injection - provides shared dependencies like database sessions
"""

from collections.abc import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        yield session
