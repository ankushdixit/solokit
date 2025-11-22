"""
Example CRUD endpoints demonstrating SQLModel usage
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies import get_db
from src.models.example import Item, ItemCreate, ItemRead, ItemUpdate
from src.services.example import ItemService

router = APIRouter()


@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Item:
    """
    Create a new item.

    Args:
        item: Item data
        db: Database session

    Returns:
        Item: Created item
    """
    service = ItemService(db)
    return await service.create_item(item)


@router.get("/items", response_model=list[ItemRead])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[Item]:
    """
    List all items with pagination.

    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        db: Database session

    Returns:
        List[Item]: List of items
    """
    service = ItemService(db)
    return await service.get_items(skip=skip, limit=limit)


@router.get("/items/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Item:
    """
    Get a specific item by ID.

    Args:
        item_id: Item ID
        db: Database session

    Returns:
        Item: Item data

    Raises:
        HTTPException: If item not found
    """
    service = ItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    return item


@router.patch("/items/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Item:
    """
    Update an item.

    Args:
        item_id: Item ID
        item_update: Fields to update
        db: Database session

    Returns:
        Item: Updated item

    Raises:
        HTTPException: If item not found
    """
    service = ItemService(db)
    item = await service.update_item(item_id, item_update)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> None:
    """
    Delete an item.

    Args:
        item_id: Item ID
        db: Database session

    Raises:
        HTTPException: If item not found
    """
    service = ItemService(db)
    success = await service.delete_item(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
