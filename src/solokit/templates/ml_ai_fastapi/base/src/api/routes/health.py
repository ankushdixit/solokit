"""
Health check endpoints for monitoring and load balancers
"""

from fastapi import APIRouter, Depends
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies import get_db
from src.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:  # noqa: B008
    """
    Readiness check - verifies database connectivity.

    Args:
        db: Database session

    Returns:
        dict: Readiness status
    """
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
    except Exception as e:
        return {
            "status": "not ready",
            "database": "disconnected",
            "error": str(e),
        }
    else:
        return {
            "status": "ready",
            "database": "connected",
        }


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness check - verifies the application is running.

    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
    }
