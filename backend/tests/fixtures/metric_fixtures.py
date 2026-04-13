"""Test fixtures for vendor-neutral Metric models.

Provides reusable test data for metric-related tests with time-bucketed structure.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from app.models.base.metric import Metric, TimeBucket, EndpointMetric


def create_sample_metric(
    api_id: Optional[str] = None,
    gateway_id: Optional[UUID] = None,
    application_id: Optional[str] = None,
    operation: Optional[str] = None,
    time_bucket: TimeBucket = TimeBucket.ONE_HOUR,
    timestamp: Optional[datetime] = None,
    request_count: int = 1000,
    error_rate: float = 1.0,
    **kwargs
) -> Metric:
    """Create a sample metric fixture with time-bucketed structure.
    
    Args:
        api_id: API identifier
        gateway_id: Gateway identifier
        application_id: Application identifier (optional)
        operation: Operation/endpoint (optional)
        time_bucket: Time bucket size
        timestamp: Metric timestamp
        request_count: Total requests
        error_rate: Error rate percentage
        **kwargs: Additional fields to override
        
    Returns:
        Sample Metric instance
    """
    now = timestamp or datetime.utcnow()
    failure_count = int(request_count * (error_rate / 100))
    success_count = request_count - failure_count
    
    defaults = {
        "id": uuid4(),
        "gateway_id": gateway_id or uuid4(),
        "api_id": api_id or str(uuid4()),
        "application_id": application_id,
        "operation": operation,
        "timestamp": now,
        "time_bucket": time_bucket,
        "request_count": request_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "timeout_count": 0,
        "error_rate": error_rate,
        "availability": 100.0 - error_rate,
        "response_time_avg": 120.0,
        "response_time_min": 50.0,
        "response_time_max": 500.0,
        "response_time_p50": 100.0,
        "response_time_p95": 250.0,
        "response_time_p99": 400.0,
        "gateway_time_avg": 20.0,
        "backend_time_avg": 100.0,
        "throughput": request_count / 3600.0,  # requests per second
        "total_data_size": request_count * 2048,  # 2KB average
        "avg_request_size": 512.0,
        "avg_response_size": 1536.0,
        "cache_hit_count": 0,
        "cache_miss_count": 0,
        "cache_bypass_count": 0,
        "cache_hit_rate": 0.0,
        "status_2xx_count": success_count,
        "status_3xx_count": 0,
        "status_4xx_count": 0,
        "status_5xx_count": failure_count,
        "status_codes": {"200": success_count, "500": failure_count},
        "endpoint_metrics": None,
        "vendor_metadata": {"test": True},
        "created_at": now,
        "updated_at": now,
    }
    
    defaults.update(kwargs)
    return Metric(**defaults)


def create_stable_metric(
    api_id: Optional[str] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> Metric:
    """Create a metric with stable/healthy performance."""
    return create_sample_metric(
        api_id=api_id,
        gateway_id=gateway_id,
        request_count=1000,
        error_rate=1.0,
        response_time_avg=80.0,
        response_time_p50=80.0,
        response_time_p95=150.0,
        response_time_p99=200.0,
        availability=99.9,
        **kwargs
    )


def create_degrading_metric(
    api_id: Optional[str] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> Metric:
    """Create a metric showing performance degradation."""
    return create_sample_metric(
        api_id=api_id,
        gateway_id=gateway_id,
        request_count=1000,
        error_rate=15.0,
        response_time_avg=400.0,
        response_time_p50=200.0,
        response_time_p95=600.0,
        response_time_p99=800.0,
        availability=85.0,
        **kwargs
    )


def create_metric_with_cache(
    api_id: Optional[str] = None,
    gateway_id: Optional[UUID] = None,
    cache_hit_rate: float = 60.0,
    **kwargs
) -> Metric:
    """Create a metric with cache statistics."""
    request_count = kwargs.get("request_count", 1000)
    cache_hit_count = int(request_count * (cache_hit_rate / 100))
    cache_miss_count = request_count - cache_hit_count
    
    return create_sample_metric(
        api_id=api_id,
        gateway_id=gateway_id,
        cache_hit_count=cache_hit_count,
        cache_miss_count=cache_miss_count,
        cache_bypass_count=0,
        cache_hit_rate=cache_hit_rate,
        **kwargs
    )


def create_metric_with_endpoints(
    api_id: Optional[str] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> Metric:
    """Create a metric with per-endpoint breakdown."""
    endpoint_metrics = [
        EndpointMetric(
            endpoint="/users",
            method="GET",
            request_count=600,
            success_count=594,
            failure_count=6,
            error_rate=1.0,
            response_time_avg=80.0,
            response_time_p50=75.0,
            response_time_p95=120.0,
            response_time_p99=150.0,
        ),
        EndpointMetric(
            endpoint="/orders",
            method="POST",
            request_count=400,
            success_count=396,
            failure_count=4,
            error_rate=1.0,
            response_time_avg=150.0,
            response_time_p50=140.0,
            response_time_p95=250.0,
            response_time_p99=300.0,
        ),
    ]
    
    return create_sample_metric(
        api_id=api_id,
        gateway_id=gateway_id,
        endpoint_metrics=endpoint_metrics,
        **kwargs
    )


def create_metric_time_series(
    api_id: str,
    gateway_id: UUID,
    start_time: datetime,
    duration_hours: int = 24,
    time_bucket: TimeBucket = TimeBucket.ONE_HOUR,
    degrading: bool = False,
) -> list[Metric]:
    """Create a time series of metrics.
    
    Args:
        api_id: API identifier
        gateway_id: Gateway identifier
        start_time: Start timestamp
        duration_hours: Duration in hours
        time_bucket: Time bucket size
        degrading: Whether metrics should show degradation over time
        
    Returns:
        List of Metric instances representing a time series
    """
    metrics = []
    bucket_minutes = {
        TimeBucket.ONE_MINUTE: 1,
        TimeBucket.FIVE_MINUTES: 5,
        TimeBucket.ONE_HOUR: 60,
        TimeBucket.ONE_DAY: 1440,
    }
    
    interval_minutes = bucket_minutes[time_bucket]
    num_buckets = (duration_hours * 60) // interval_minutes
    
    for i in range(num_buckets):
        timestamp = start_time + timedelta(minutes=i * interval_minutes)
        
        if degrading:
            # Gradually increase error rate and response time
            error_rate = 1.0 + (i / num_buckets) * 14.0  # 1% to 15%
            response_time_avg = 100.0 + (i / num_buckets) * 300.0  # 100ms to 400ms
        else:
            error_rate = 1.0
            response_time_avg = 100.0
        
        metric = create_sample_metric(
            api_id=api_id,
            gateway_id=gateway_id,
            timestamp=timestamp,
            time_bucket=time_bucket,
            error_rate=error_rate,
            response_time_avg=response_time_avg,
            response_time_p50=response_time_avg * 0.8,
            response_time_p95=response_time_avg * 2.0,
            response_time_p99=response_time_avg * 3.0,
        )
        metrics.append(metric)
    
    return metrics


# Made with Bob