"""
Item service - handles business logic for items
"""

from datetime import datetime, timezone

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.example import Item, ItemCreate, ItemUpdate


class ItemService:
    """Service for managing items."""

    def __init__(self, db: AsyncSession):
        """
        Initialize item service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_item(self, item_data: ItemCreate) -> Item:
        """
        Create a new item.

        Args:
            item_data: Item creation data

        Returns:
            Item: Created item
        """
        item = Item.model_validate(item_data)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_item(self, item_id: int) -> Item | None:
        """
        Get an item by ID.

        Args:
            item_id: Item ID

        Returns:
            Optional[Item]: Item if found, None otherwise
        """
        statement = select(Item).where(Item.id == item_id)
        result = await self.db.exec(statement)
        return result.one_or_none()

    async def get_items(self, skip: int = 0, limit: int = 100) -> list[Item]:
        """
        Get all items with pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            list[Item]: List of items
        """
        statement = select(Item).offset(skip).limit(limit)
        result = await self.db.exec(statement)
        return list(result.all())

    async def update_item(self, item_id: int, item_update: ItemUpdate) -> Item | None:
        """
        Update an item.

        Args:
            item_id: Item ID
            item_update: Fields to update

        Returns:
            Optional[Item]: Updated item if found, None otherwise
        """
        item = await self.get_item(item_id)
        if not item:
            return None

        # Update only provided fields
        update_data = item_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        # Update timestamp
        item.updated_at = datetime.now(timezone.utc)

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item_id: int) -> bool:
        """
        Delete an item.

        Args:
            item_id: Item ID

        Returns:
            bool: True if item was deleted, False if not found
        """
        item = await self.get_item(item_id)
        if not item:
            return False

        await self.db.delete(item)
        await self.db.commit()
        return True
