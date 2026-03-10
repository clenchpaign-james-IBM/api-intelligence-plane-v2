"""
Metrics API Endpoints

REST API endpoints for API metrics and performance data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.adapters.factory import GatewayAdapterFactory
from app.services.metrics_service import MetricsService
from app.models.metric import Metric

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Metrics"])


# Response Models
class MetricsResponse(BaseModel):
    """Response model for API metrics."""
    
    api_id: str
    time_series: list[dict]
    aggregated: dict
    total_data_points: int


@router.get(
    "/apis/{api_id}/metrics",
    response_model=MetricsResponse,
    summary="Get API metrics",
)
async def get_api_metrics(
    api_id: UUID,
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
    interval: str = Query("5m", description="Aggregation interval", regex="^(1m|5m|15m|1h|1d)$"),
) -> MetricsResponse:
    """
    Get metrics for a specific API.
    
    Args:
        api_id: API UUID
        start_time: Start of time range (default: 24 hours ago)
        end_time: End of time range (default: now)
        interval: Aggregation interval (1m, 5m, 15m, 1h, 1d)
        
    Returns:
        API metrics with time-series and aggregated data
        
    Raises:
        HTTPException: If API not found or metrics retrieval fails
    """
    try:
        # Verify API exists
        api_repo = APIRepository()
        api = api_repo.get(str(api_id))
        
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found",
            )
        
        # Initialize metrics service
        metrics_repo = MetricsRepository()
        gateway_repo = GatewayRepository()
        adapter_factory = GatewayAdapterFactory()
        
        metrics_service = MetricsService(
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            gateway_repository=gateway_repo,
            adapter_factory=adapter_factory,
        )
        
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Get time-series data
        time_series = metrics_service.get_time_series(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
        
        # Get aggregated metrics
        aggregated = metrics_service.get_aggregated_metrics(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )
        
        return MetricsResponse(
            api_id=str(api_id),
            time_series=time_series,
            aggregated=aggregated,
            total_data_points=len(time_series),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for API {api_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )


# Made with Bob