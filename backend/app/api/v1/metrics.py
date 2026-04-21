"""
Metrics API Endpoints

REST API endpoints for API metrics and performance data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status
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


class MetricsSummaryResponse(BaseModel):
    """Response model for metrics summary."""
    
    total_requests_24h: int
    avg_response_time: float
    avg_error_rate: float


class AnalyticsMetricsResponse(BaseModel):
    """Response model for analytics metrics."""
    
    items: list[dict]
    total: int
    time_bucket: str


@router.get(
    "/analytics/metrics",
    response_model=AnalyticsMetricsResponse,
    summary="Get analytics metrics across all gateways",
)
async def get_analytics_metrics(
    gateway_id: Optional[UUID] = Query(None, description="Optional gateway filter"),
    api_id: Optional[UUID] = Query(None, description="Optional API filter"),
    time_bucket: str = Query("1h", description="Time bucket granularity"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum results"),
) -> AnalyticsMetricsResponse:
    """
    Get aggregated analytics metrics across all gateways or for a specific gateway.
    
    Returns time-bucketed metrics for analytics dashboard.
    """
    try:
        # Initialize repositories
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        
        # Set default time range (last 24 hours)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        # Convert time_bucket string to TimeBucket enum
        try:
            bucket_enum = TimeBucket(time_bucket)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time_bucket: {time_bucket}. Must be one of: 1m, 5m, 1h, 1d",
            )
        
        # Build query based on filters
        items = []
        
        if api_id:
            # Get metrics for specific API
            metrics, total = metrics_repo.find_by_time_bucket(
                api_id=api_id,
                time_bucket=bucket_enum,
                start_time=start_time,
                end_time=end_time,
                size=limit,
            )
            
            # Format metrics for response
            for metric in metrics:
                items.append({
                    "id": str(metric.id),
                    "gateway_id": str(metric.gateway_id),
                    "api_id": metric.api_id,
                    "timestamp": metric.timestamp.isoformat(),
                    "time_bucket": metric.time_bucket.value,
                    "request_count": metric.request_count,
                    "success_count": metric.success_count,
                    "failure_count": metric.failure_count,
                    "error_rate": metric.error_rate,
                    "availability": metric.availability,
                    "response_time_avg": metric.response_time_avg,
                    "response_time_p50": metric.response_time_p50,
                    "response_time_p95": metric.response_time_p95,
                    "response_time_p99": metric.response_time_p99,
                    "throughput": metric.throughput,
                    "cache_hit_rate": metric.cache_hit_rate,
                })
            
            return AnalyticsMetricsResponse(
                items=items,
                total=total,
                time_bucket=time_bucket,
            )
        
        elif gateway_id:
            # Get metrics for all APIs in a specific gateway
            metrics, total = metrics_repo.find_by_gateway(
                gateway_id=gateway_id,
                start_time=start_time,
                end_time=end_time,
                size=limit,
            )
            
            # Filter by time bucket and format
            for metric in metrics:
                if metric.time_bucket == bucket_enum:
                    items.append({
                        "id": str(metric.id),
                        "gateway_id": str(metric.gateway_id),
                        "api_id": metric.api_id,
                        "timestamp": metric.timestamp.isoformat(),
                        "time_bucket": metric.time_bucket.value,
                        "request_count": metric.request_count,
                        "success_count": metric.success_count,
                        "failure_count": metric.failure_count,
                        "error_rate": metric.error_rate,
                        "availability": metric.availability,
                        "response_time_avg": metric.response_time_avg,
                        "response_time_p50": metric.response_time_p50,
                        "response_time_p95": metric.response_time_p95,
                        "response_time_p99": metric.response_time_p99,
                        "throughput": metric.throughput,
                        "cache_hit_rate": metric.cache_hit_rate,
                    })
            
            return AnalyticsMetricsResponse(
                items=items[:limit],
                total=len(items),
                time_bucket=time_bucket,
            )
        
        else:
            # Get metrics across all gateways
            gateways, _ = gateway_repo.list_all(size=1000)
            
            for gateway in gateways:
                try:
                    metrics, _ = metrics_repo.find_by_gateway(
                        gateway_id=gateway.id,
                        start_time=start_time,
                        end_time=end_time,
                        size=limit,
                    )
                    
                    # Filter by time bucket and format
                    for metric in metrics:
                        if metric.time_bucket == bucket_enum:
                            items.append({
                                "id": str(metric.id),
                                "gateway_id": str(metric.gateway_id),
                                "api_id": metric.api_id,
                                "timestamp": metric.timestamp.isoformat(),
                                "time_bucket": metric.time_bucket.value,
                                "request_count": metric.request_count,
                                "success_count": metric.success_count,
                                "failure_count": metric.failure_count,
                                "error_rate": metric.error_rate,
                                "availability": metric.availability,
                                "response_time_avg": metric.response_time_avg,
                                "response_time_p50": metric.response_time_p50,
                                "response_time_p95": metric.response_time_p95,
                                "response_time_p99": metric.response_time_p99,
                                "throughput": metric.throughput,
                                "cache_hit_rate": metric.cache_hit_rate,
                            })
                            
                            if len(items) >= limit:
                                break
                    
                    if len(items) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to get metrics for gateway {gateway.id}: {e}")
                    continue
            
            return AnalyticsMetricsResponse(
                items=items[:limit],
                total=len(items),
                time_bucket=time_bucket,
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics metrics: {str(e)}",
        )


@router.get(
    "/metrics/summary",
    response_model=MetricsSummaryResponse,
    summary="Get metrics summary across all gateways",
)
async def get_metrics_summary(
    gateway_id: Optional[UUID] = Query(None, description="Optional gateway filter"),
) -> MetricsSummaryResponse:
    """
    Get aggregated metrics summary across all gateways or for a specific gateway.
    
    Returns summary statistics for the last 24 hours.
    """
    try:
        # Initialize repositories
        metrics_repo = MetricsRepository()
        gateway_repo = GatewayRepository()
        
        # Set time range (last 24 hours)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        # Aggregate metrics
        total_requests = 0
        total_response_time_weighted = 0
        total_errors = 0
        metrics_count = 0
        
        if gateway_id:
            # Get metrics for specific gateway
            metrics, _ = metrics_repo.find_by_gateway(
                gateway_id=gateway_id,
                start_time=start_time,
                end_time=end_time,
                size=10000,
            )
        else:
            # Get metrics across all gateways
            gateways, _ = gateway_repo.list_all(size=1000)
            metrics = []
            
            for gateway in gateways:
                try:
                    gateway_metrics, _ = metrics_repo.find_by_gateway(
                        gateway_id=gateway.id,
                        start_time=start_time,
                        end_time=end_time,
                        size=10000,
                    )
                    metrics.extend(gateway_metrics)
                except Exception as e:
                    logger.warning(f"Failed to get metrics for gateway {gateway.id}: {e}")
                    continue
        
        # Aggregate the metrics
        for metric in metrics:
            total_requests += metric.request_count
            total_errors += metric.failure_count
            
            # Weighted average for response time
            if metric.request_count > 0:
                total_response_time_weighted += metric.response_time_avg * metric.request_count
                metrics_count += metric.request_count
        
        # Calculate averages
        avg_response_time = (
            total_response_time_weighted / metrics_count if metrics_count > 0 else 0.0
        )
        avg_error_rate = (
            (total_errors / total_requests * 100) if total_requests > 0 else 0.0
        )
        
        return MetricsSummaryResponse(
            total_requests_24h=total_requests,
            avg_response_time=round(avg_response_time, 2),
            avg_error_rate=round(avg_error_rate, 2),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics summary: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/apis/{api_id}/metrics",
    response_model=MetricsResponse,
    summary="Get API metrics",
)
async def get_gateway_api_metrics(
    gateway_id: UUID,
    api_id: UUID,
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
    time_bucket: str = Query("5m", description="Time bucket granularity", pattern="^(1m|5m|1h|1d)$"),
) -> MetricsResponse:
    """
    Get time-bucketed metrics for a specific API within a gateway.
    
    Args:
        gateway_id: Gateway UUID (required)
        api_id: API UUID
        start_time: Start of time range (default: 24 hours ago)
        end_time: End of time range (default: now)
        time_bucket: Time bucket granularity (1m, 5m, 1h, 1d)
        
    Returns:
        API metrics with time-series, cache metrics, timing breakdown, and status breakdown
        
    Raises:
        HTTPException: If gateway or API not found or metrics retrieval fails
    """
    try:
        # Verify gateway exists
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Verify API exists
        api_repo = APIRepository()
        api = api_repo.get(str(api_id))
        
        if not api:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found",
            )
        
        # Verify API belongs to the gateway
        if str(api.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found in gateway {gateway_id}",
            )
        
        # Initialize metrics service
        metrics_repo = MetricsRepository()
        adapter_factory = GatewayAdapterFactory()
        
        metrics_service = MetricsService(
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            gateway_repository=gateway_repo,
            adapter_factory=adapter_factory,
        )
        
        # Convert time_bucket string to TimeBucket enum
        bucket_enum = TimeBucket(time_bucket)
        
        # Get metrics with aggregation from service layer
        result = metrics_service.get_api_metrics_with_aggregation(
            api_id=api_id,
            time_bucket=bucket_enum,
            start_time=start_time,
            end_time=end_time,
            limit=1000,
        )
        
        return MetricsResponse(
            api_id=str(api_id),
            time_bucket=time_bucket,
            time_series=result["time_series"],
            aggregated=result["aggregated"],
            cache_metrics=result["cache_metrics"],
            timing_breakdown=result["timing_breakdown"],
            status_breakdown=result["status_breakdown"],
            total_data_points=result["total_data_points"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for API {api_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )


@router.get(
    "/analytics/metrics/{metric_id}/logs",
    summary="Drill down to transactional logs from analytics",
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
        # Initialize repositories
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
                status_code=http_status.HTTP_404_NOT_FOUND,
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
            "items": logs_data,
            "total": result["total_logs"],
            "metric_summary": result["metric_summary"],
            "time_range": {
                "start": result["time_range"]["start"].isoformat(),
                "end": result["time_range"]["end"].isoformat(),
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to drill down for metric {metric_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drill down to logs: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/metrics/{metric_id}/logs",
    summary="Drill down to transactional logs",
)
async def drill_down_to_gateway_logs(
    gateway_id: UUID,
    metric_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
):
    """
    Drill down from a metric to its source transactional logs within a gateway.
    
    This endpoint allows you to trace a specific metric back to the individual
    transactional logs that were aggregated to create it. Useful for debugging
    performance issues or investigating specific time periods.
    
    Args:
        gateway_id: Gateway UUID (required)
        metric_id: ID of the metric to drill down from
        limit: Maximum number of logs to return (1-1000)
        
    Returns:
        Metric context and associated transactional logs
        
    Raises:
        HTTPException: If gateway or metric not found or drill-down fails
    """
    try:
        # Verify gateway exists
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Initialize metrics service
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
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
                status_code=http_status.HTTP_404_NOT_FOUND,
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
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drill down to logs: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/metrics/summary",
    summary="Get metrics summary for gateway APIs",
)
async def get_gateway_metrics_summary(
    gateway_id: UUID,
    status: Optional[str] = Query(None, description="Filter by API status"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
) -> dict:
    """
    Get aggregated metrics summary for all APIs within a gateway.
    
    Args:
        gateway_id: Gateway UUID (required)
        status: Optional API status filter
        start_time: Start of time range (default: 24 hours ago)
        end_time: End of time range (default: now)
        
    Returns:
        Summary statistics including avg response time, error rate, throughput, etc.
        
    Raises:
        HTTPException: If gateway not found or summary retrieval fails
    """
    try:
        # Verify gateway exists
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Initialize repositories
        api_repo = APIRepository()
        metrics_repo = MetricsRepository()
        
        # Get all APIs for this gateway
        apis, _ = api_repo.find_by_gateway(gateway_id=gateway_id, size=10000)
        
        # Apply status filter if provided
        if status:
            apis = [api for api in apis if api.status == status]
        
        if not apis:
            return {
                "total_apis": 0,
                "total_requests_24h": 0,
                "avg_response_time": 0,
                "avg_error_rate": 0,
                "avg_throughput": 0,
                "avg_availability": 0,
                "avg_health_score": 0,
            }
        
        # Aggregate metrics across all APIs
        total_requests = 0
        total_response_time_weighted = 0
        total_errors = 0
        total_throughput = 0
        total_availability = 0
        total_health_score = 0
        apis_with_metrics = 0
        
        for api in apis:
            try:
                # Get metrics for this API
                metrics, _ = metrics_repo.find_by_api(
                    api_id=api.id,
                    start_time=start_time,
                    end_time=end_time,
                    size=1000,
                )
                
                if metrics:
                    apis_with_metrics += 1
                    api_total_requests = sum(m.request_count for m in metrics)
                    api_total_errors = sum(m.failure_count for m in metrics)
                    
                    total_requests += api_total_requests
                    total_errors += api_total_errors
                    
                    # Weighted average response time
                    if api_total_requests > 0:
                        total_response_time_weighted += sum(
                            m.response_time_avg * m.request_count for m in metrics
                        )
                    
                    # Average throughput
                    total_throughput += sum(m.throughput for m in metrics) / len(metrics) if metrics else 0
                    
                    # Average availability (if available)
                    availabilities = [m.availability for m in metrics if hasattr(m, 'availability') and m.availability is not None]
                    if availabilities:
                        total_availability += sum(availabilities) / len(availabilities)
                
                # Add health score from API metadata
                if api.intelligence_metadata and api.intelligence_metadata.health_score:
                    total_health_score += api.intelligence_metadata.health_score
                    
            except Exception as e:
                logger.warning(f"Failed to get metrics for API {api.id}: {e}")
                continue
        
        # Calculate averages
        avg_response_time = (
            total_response_time_weighted / total_requests if total_requests > 0 else 0
        )
        avg_error_rate = (
            (total_errors / total_requests * 100) if total_requests > 0 else 0
        )
        avg_throughput = total_throughput / apis_with_metrics if apis_with_metrics > 0 else 0
        avg_availability = total_availability / apis_with_metrics if apis_with_metrics > 0 else 0
        avg_health_score = total_health_score / len(apis) if apis else 0
        
        return {
            "total_apis": len(apis),
            "total_requests_24h": total_requests,
            "avg_response_time": round(avg_response_time, 2),
            "avg_error_rate": round(avg_error_rate, 2),
            "avg_throughput": round(avg_throughput, 2),
            "avg_availability": round(avg_availability, 2),
            "avg_health_score": round(avg_health_score, 2),
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics summary: {str(e)}",
        )


# Made with Bob