"""
Unit tests for example service
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession  # type: ignore[import-not-found]

from src.models.example import ItemCreate, ItemUpdate  # type: ignore[import-not-found]
from src.services.example import ItemService  # type: ignore[import-not-found]


@pytest.mark.unit
class TestItemService:
    """Test cases for ItemService."""

    async def test_create_item(self, db_session: AsyncSession) -> None:
        """Test creating an item."""
        service = ItemService(db_session)
        item_data = ItemCreate(
            name="Test Item",
            description="A test item",
            price=9.99,
        )

        item = await service.create_item(item_data)

        assert item.id is not None
        assert item.name == "Test Item"
        assert item.description == "A test item"
        assert item.price == 9.99
        assert item.is_active is True

    async def test_get_item(self, db_session: AsyncSession) -> None:
        """Test retrieving an item."""
        service = ItemService(db_session)

        # Create an item first
        item_data = ItemCreate(name="Test Item", price=9.99)
        created_item = await service.create_item(item_data)
        assert created_item.id is not None

        # Retrieve the item
        retrieved_item = await service.get_item(created_item.id)

        assert retrieved_item is not None
        assert retrieved_item.id == created_item.id
        assert retrieved_item.name == created_item.name

    async def test_get_nonexistent_item(self, db_session: AsyncSession) -> None:
        """Test retrieving a non-existent item."""
        service = ItemService(db_session)
        item = await service.get_item(999)
        assert item is None

    async def test_get_items_pagination(self, db_session: AsyncSession) -> None:
        """Test listing items with pagination."""
        service = ItemService(db_session)

        # Create multiple items (starting from 1 to avoid price=0 validation error)
        for i in range(1, 6):
            item_data = ItemCreate(name=f"Item {i}", price=float(i))
            await service.create_item(item_data)

        # Test pagination
        items = await service.get_items(skip=0, limit=3)
        assert len(items) == 3

        items = await service.get_items(skip=3, limit=3)
        assert len(items) == 2

    async def test_update_item(self, db_session: AsyncSession) -> None:
        """Test updating an item."""
        service = ItemService(db_session)

        # Create an item
        item_data = ItemCreate(name="Original Name", price=10.0)
        created_item = await service.create_item(item_data)
        assert created_item.id is not None

        # Update the item
        update_data = ItemUpdate(name="Updated Name", price=15.0)
        updated_item = await service.update_item(created_item.id, update_data)

        assert updated_item is not None
        assert updated_item.name == "Updated Name"
        assert updated_item.price == 15.0

    async def test_update_nonexistent_item(self, db_session: AsyncSession) -> None:
        """Test updating a non-existent item."""
        service = ItemService(db_session)
        update_data = ItemUpdate(name="Updated Name")
        result = await service.update_item(999, update_data)
        assert result is None

    async def test_delete_item(self, db_session: AsyncSession) -> None:
        """Test deleting an item."""
        service = ItemService(db_session)

        # Create an item
        item_data = ItemCreate(name="To Delete", price=10.0)
        created_item = await service.create_item(item_data)
        assert created_item.id is not None

        # Delete the item
        success = await service.delete_item(created_item.id)
        assert success is True

        # Verify deletion
        deleted_item = await service.get_item(created_item.id)
        assert deleted_item is None

    async def test_delete_nonexistent_item(self, db_session: AsyncSession) -> None:
        """Test deleting a non-existent item."""
        service = ItemService(db_session)
        success = await service.delete_item(999)
        assert success is False
