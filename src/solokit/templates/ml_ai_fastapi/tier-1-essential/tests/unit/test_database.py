"""
Unit tests for database and dependencies
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession  # type: ignore[import-not-found]

from src.api.dependencies import get_db  # type: ignore[import-not-found]


@pytest.mark.unit
class TestDatabase:
    """Test cases for database functions."""

    async def test_get_db_dependency(self, db_session: AsyncSession) -> None:
        """Test the get_db dependency."""
        # The db_session fixture already tests get_db indirectly
        # Just verify we can use a session
        assert isinstance(db_session, AsyncSession)

    async def test_get_db_function_directly(self) -> None:
        """Test get_db function directly."""

        # Mock the async_session_maker to avoid real DB connection
        with patch("src.api.dependencies.async_session_maker") as mock_maker:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_maker.return_value.__aenter__.return_value = mock_session
            mock_maker.return_value.__aexit__.return_value = None

            # Use the get_db generator
            gen = get_db()
            session = await gen.__anext__()
            assert session is mock_session
            await gen.aclose()

    async def test_create_db_and_tables(self) -> None:
        """Test database table creation with mock."""
        with patch("src.core.database.engine") as mock_engine:
            # Create mock connection
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            # Import and call the function
            from src.core.database import create_db_and_tables

            await create_db_and_tables()

            # Verify run_sync was called
            assert mock_conn.run_sync.called

    async def test_get_session(self) -> None:
        """Test get_session function."""
        with patch("src.core.database.async_session_maker") as mock_maker:
            # Create mock session
            mock_session = AsyncMock(spec=AsyncSession)
            mock_maker.return_value.__aenter__.return_value = mock_session

            # Import and use the function
            from src.core.database import get_session

            async for session in get_session():
                assert isinstance(session, AsyncMock)
                break
