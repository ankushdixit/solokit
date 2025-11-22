"""
Unit tests for API routes
"""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.unit
class TestItemRoutes:
    """Test cases for Item API routes."""

    async def test_create_item_success(self, client: AsyncClient) -> None:
        """Test creating an item via API."""
        response = await client.post(
            "/api/v1/items",
            json={"name": "Test Item", "description": "A test item", "price": 9.99},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Item"
        assert data["price"] == 9.99
        assert "id" in data

    async def test_list_items_empty(self, client: AsyncClient) -> None:
        """Test listing items when none exist."""
        response = await client.get("/api/v1/items")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_list_items_with_data(self, client: AsyncClient) -> None:
        """Test listing items with pagination."""
        # Create test items
        for i in range(5):
            await client.post(
                "/api/v1/items",
                json={"name": f"Item {i}", "price": float(i + 1)},
            )

        # List all items
        response = await client.get("/api/v1/items")
        assert response.status_code == status.HTTP_200_OK
        items = response.json()
        assert len(items) == 5

        # Test pagination
        response = await client.get("/api/v1/items?skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        items = response.json()
        assert len(items) == 2

    async def test_get_item_success(self, client: AsyncClient) -> None:
        """Test retrieving a specific item."""
        # Create an item
        create_response = await client.post(
            "/api/v1/items",
            json={"name": "Test Item", "price": 10.0},
        )
        item_id = create_response.json()["id"]

        # Get the item
        response = await client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == "Test Item"

    async def test_get_item_not_found(self, client: AsyncClient) -> None:
        """Test retrieving a non-existent item."""
        response = await client.get("/api/v1/items/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_update_item_success(self, client: AsyncClient) -> None:
        """Test updating an item."""
        # Create an item
        create_response = await client.post(
            "/api/v1/items",
            json={"name": "Original", "price": 10.0},
        )
        item_id = create_response.json()["id"]

        # Update the item
        response = await client.patch(
            f"/api/v1/items/{item_id}",
            json={"name": "Updated", "price": 15.0},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated"
        assert data["price"] == 15.0

    async def test_update_item_not_found(self, client: AsyncClient) -> None:
        """Test updating a non-existent item."""
        response = await client.patch(
            "/api/v1/items/999",
            json={"name": "Updated"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_delete_item_success(self, client: AsyncClient) -> None:
        """Test deleting an item."""
        # Create an item
        create_response = await client.post(
            "/api/v1/items",
            json={"name": "To Delete", "price": 10.0},
        )
        item_id = create_response.json()["id"]

        # Delete the item
        response = await client.delete(f"/api/v1/items/{item_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        get_response = await client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_item_not_found(self, client: AsyncClient) -> None:
        """Test deleting a non-existent item."""
        response = await client.delete("/api/v1/items/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()


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
