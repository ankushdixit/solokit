"""
Integration test fixtures
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient  # type: ignore[import-not-found]
from sqlalchemy.ext.asyncio import (  # type: ignore[import-not-found]
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel  # type: ignore[import-not-found]
from sqlmodel.ext.asyncio.session import AsyncSession  # type: ignore[import-not-found]

from src.api.dependencies import get_db  # type: ignore[import-not-found]
from src.main import app  # type: ignore[import-not-found]

# Use a separate test database for integration tests
INTEGRATION_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"


@pytest.fixture()
async def integration_db_engine() -> AsyncGenerator[Any, None]:
    """Create a test database engine for integration tests."""
    engine = create_async_engine(
        INTEGRATION_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture()
async def integration_db_session(
    integration_db_engine: Any,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session for integration tests."""
    session_maker = async_sessionmaker(
        integration_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        yield session


@pytest.fixture()
async def integration_client(
    integration_db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for integration tests.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield integration_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver", timeout=30.0
    ) as ac:  # nosec B113 - Test client timeout is set to 30 seconds
        yield ac

    app.dependency_overrides.clear()
