"""
Unit tests for API routes
"""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.unit
class TestHealthRoutes:
    """Test cases for Health check routes."""

    async def test_health_check(self, client: AsyncClient) -> None:
        """Test basic health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    async def test_readiness_check(self, client: AsyncClient) -> None:
        """Test readiness check endpoint."""
        response = await client.get("/health/ready")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"

    async def test_liveness_check(self, client: AsyncClient) -> None:
        """Test liveness check endpoint."""
        response = await client.get("/health/live")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"

    async def test_readiness_check_database_error(self) -> None:
        """Test readiness check when database connection fails."""
        from unittest.mock import AsyncMock

        from sqlmodel.ext.asyncio.session import AsyncSession

        from src.api.routes.health import readiness_check

        # Create a mock session that raises an exception
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database connection failed")

        # Call the readiness check with the failing session
        result = await readiness_check(db=mock_session)

        assert result["status"] == "not ready"
        assert result["database"] == "disconnected"
        assert "error" in result
