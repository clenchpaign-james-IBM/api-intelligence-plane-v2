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
from app.models.base.metric import Metric, TimeBucket

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Metrics"])


# Response Models
class MetricsResponse(BaseModel):
    """Response model for API metrics."""
    
    api_id: str
    time_bucket: str
    time_series: list[dict]
    aggregated: dict
    cache_metrics: dict
    timing_breakdown: dict
    status_breakdown: dict
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
    time_bucket: str = Query("5m", description="Time bucket granularity", regex="^(1m|5m|1h|1d)$"),
) -> MetricsResponse:
    """
    Get time-bucketed metrics for a specific API.
    
    Args:
        api_id: API UUID
        start_time: Start of time range (default: 24 hours ago)
        end_time: End of time range (default: now)
        time_bucket: Time bucket granularity (1m, 5m, 1h, 1d)
        
    Returns:
        API metrics with time-series, cache metrics, timing breakdown, and status breakdown
        
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
        
        # Convert time_bucket string to TimeBucket enum
        bucket_enum = TimeBucket(time_bucket)
        
        # Query metrics from the time-bucketed index
        metrics, total = metrics_repo.find_by_time_bucket(
            api_id=api_id,
            time_bucket=bucket_enum,
            start_time=start_time,
            end_time=end_time,
            size=1000,  # Get up to 1000 data points
        )
        
        # Convert metrics to time-series format
        time_series = [
            {
                "timestamp": m.timestamp.isoformat(),
                "request_count": m.request_count,
                "success_count": m.success_count,
                "failure_count": m.failure_count,
                "response_time_avg": m.response_time_avg,
                "response_time_p50": m.response_time_p50,
                "response_time_p95": m.response_time_p95,
                "response_time_p99": m.response_time_p99,
                "cache_hit_rate": m.cache_hit_rate,
                "gateway_time_avg": m.gateway_time_avg,
                "backend_time_avg": m.backend_time_avg,
            }
            for m in metrics
        ]
        
        # Calculate aggregated metrics
        if metrics:
            total_requests = sum(m.request_count for m in metrics)
            total_success = sum(m.success_count for m in metrics)
            total_failures = sum(m.failure_count for m in metrics)
            
            aggregated = {
                "total_requests": total_requests,
                "success_rate": (total_success / total_requests * 100) if total_requests > 0 else 0,
                "failure_rate": (total_failures / total_requests * 100) if total_requests > 0 else 0,
                "avg_response_time": sum(m.response_time_avg * m.request_count for m in metrics) / total_requests if total_requests > 0 else 0,
                "p95_response_time": max(m.response_time_p95 for m in metrics) if metrics else 0,
                "p99_response_time": max(m.response_time_p99 for m in metrics) if metrics else 0,
            }
            
            # Cache metrics aggregation
            cache_metrics = {
                "avg_hit_rate": sum(m.cache_hit_rate for m in metrics) / len(metrics) if metrics else 0,
                "total_hits": sum(m.cache_hit_count for m in metrics),
                "total_misses": sum(m.cache_miss_count for m in metrics),
                "total_bypasses": sum(m.cache_bypass_count for m in metrics),
            }
            
            # Timing breakdown aggregation
            timing_breakdown = {
                "avg_gateway_time": sum(m.gateway_time_avg * m.request_count for m in metrics) / total_requests if total_requests > 0 else 0,
                "avg_backend_time": sum(m.backend_time_avg * m.request_count for m in metrics) / total_requests if total_requests > 0 else 0,
                "gateway_overhead_pct": 0,  # Will calculate below
            }
            if timing_breakdown["avg_gateway_time"] + timing_breakdown["avg_backend_time"] > 0:
                timing_breakdown["gateway_overhead_pct"] = (
                    timing_breakdown["avg_gateway_time"] /
                    (timing_breakdown["avg_gateway_time"] + timing_breakdown["avg_backend_time"]) * 100
                )
            
            # HTTP status breakdown aggregation
            status_breakdown = {
                "2xx": sum(m.status_2xx_count for m in metrics),
                "3xx": sum(m.status_3xx_count for m in metrics),
                "4xx": sum(m.status_4xx_count for m in metrics),
                "5xx": sum(m.status_5xx_count for m in metrics),
            }
        else:
            aggregated = {
                "total_requests": 0,
                "success_rate": 0,
                "failure_rate": 0,
                "avg_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0,
            }
            cache_metrics = {
                "avg_hit_rate": 0,
                "total_hits": 0,
                "total_misses": 0,
                "total_bypasses": 0,
            }
            timing_breakdown = {
                "avg_gateway_time": 0,
                "avg_backend_time": 0,
                "gateway_overhead_pct": 0,
            }
            status_breakdown = {
                "2xx": 0,
                "3xx": 0,
                "4xx": 0,
                "5xx": 0,
            }
        
        return MetricsResponse(
            api_id=str(api_id),
            time_bucket=time_bucket,
            time_series=time_series,
            aggregated=aggregated,
            cache_metrics=cache_metrics,
            timing_breakdown=timing_breakdown,
            status_breakdown=status_breakdown,
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


@router.get(
    "/metrics/{metric_id}/logs",
    summary="Drill down to transactional logs",
)
async def drill_down_to_logs(
    metric_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
):
    """
    Drill down from a metric to its source transactional logs.
    
    This endpoint allows you to trace a specific metric back to the individual
    transactional logs that were aggregated to create it. Useful for debugging
    performance issues or investigating specific time periods.
    
    Args:
        metric_id: ID of the metric to drill down from
        limit: Maximum number of logs to return (1-1000)
        
    Returns:
        Metric context and associated transactional logs
        
    Raises:
        HTTPException: If metric not found or drill-down fails
    """
    try:
        # Initialize metrics service
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        adapter_factory = GatewayAdapterFactory()
        
        metrics_service = MetricsService(
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            gateway_repository=gateway_repo,
            adapter_factory=adapter_factory,
        )
        
        # Perform drill-down
        result = await metrics_service.drill_down_to_logs(
            metric_id=metric_id,
            limit=limit,
        )
        
        # Check if metric was found
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        
        # Convert logs to dict format for JSON response
        logs_data = [
            {
                "id": str(log.id),
                "timestamp": datetime.utcfromtimestamp(log.timestamp / 1000).isoformat(),
                "api_id": str(log.api_id),
                "gateway_id": str(log.gateway_id),
                "application_id": str(log.application_id) if log.application_id else None,
                "operation": log.operation,
                "method": log.method,
                "path": log.path,
                "status_code": log.status_code,
                "total_time_ms": log.total_time_ms,
                "gateway_time_ms": log.gateway_time_ms,
                "backend_time_ms": log.backend_time_ms,
                "request_size": log.request_size,
                "response_size": log.response_size,
                "client_ip": log.client_ip,
                "user_agent": log.user_agent,
                "error_message": log.error_message,
            }
            for log in result["logs"]
        ]
        
        return {
            "metric_summary": result["metric_summary"],
            "time_range": {
                "start": result["time_range"]["start"].isoformat(),
                "end": result["time_range"]["end"].isoformat(),
            },
            "logs": logs_data,
            "total_logs": result["total_logs"],
            "returned_logs": result["returned_logs"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to drill down for metric {metric_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drill down to logs: {str(e)}",
        )


# Made with Bob