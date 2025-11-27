"""
Integration tests for API endpoints
"""

import pytest
from httpx import AsyncClient  # type: ignore[import-not-found]


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    async def test_health_endpoints_integration(self, integration_client: AsyncClient) -> None:
        """Test all health check endpoints."""
        # Health check
        response = await integration_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Readiness check
        response = await integration_client.get("/health/ready")
        assert response.status_code == 200

        # Liveness check
        response = await integration_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
