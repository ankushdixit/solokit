"""
Prometheus metrics endpoint
"""

from fastapi import APIRouter, Response

from src.core.monitoring import get_metrics

router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Response: Prometheus metrics in text format
    """
    return get_metrics()
