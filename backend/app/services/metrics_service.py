"""
Metrics Service

Handles metrics collection from Gateways, aggregation, and analysis.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.adapters.factory import GatewayAdapterFactory
from app.models.base.metric import Metric, TimeBucket
from app.models.base.transaction import TransactionalLog
from app.models.gateway import GatewayStatus

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for collecting and managing API metrics."""
    
    def __init__(
        self,
        metrics_repository: MetricsRepository,
        api_repository: APIRepository,
        gateway_repository: GatewayRepository,
        adapter_factory: GatewayAdapterFactory,
    ):
        """
        Initialize the Metrics Service.
        
        Args:
            metrics_repository: Repository for metrics operations
            api_repository: Repository for API operations
            gateway_repository: Repository for Gateway operations
            adapter_factory: Factory for creating Gateway adapters
        """
        self.metrics_repo = metrics_repository
        self.api_repo = api_repository
        self.gateway_repo = gateway_repository
        self.adapter_factory = adapter_factory
    async def collect_transactional_logs(
        self,
        gateway_id: UUID,
        start_time: datetime,
        end_time: datetime,
        time_bucket: str = "1m",
        generate_all_buckets: bool = True,
    ) -> None:
        """
        Collect transactional logs from a gateway and aggregate into metrics.
        
        This method:
        1. Fetches transactional logs from the gateway adapter for the time range
        2. Stores logs via TransactionalLogRepository (daily indices)
        3. Aggregates logs into time-bucketed metrics (all buckets if generate_all_buckets=True)
        4. Stores metrics via MetricsRepository (time-bucketed indices)
        5. Logs results (no return value)
        
        Args:
            gateway_id: UUID of the gateway to collect logs from
            start_time: Start of time range for log collection
            end_time: End of time range for log collection
            time_bucket: Primary time bucket for metrics aggregation (1m, 5m, 1h, 1d)
            generate_all_buckets: If True, generates metrics for all time buckets (default: True)
        """
        from app.db.repositories.transactional_log_repository import TransactionalLogRepository
        from app.models.base.transaction import TransactionalLog
        
        # Get gateway
        gateway = self.gateway_repo.get(str(gateway_id))
        if not gateway:
            logger.error(f"Gateway {gateway_id} not found")
            return
        
        if gateway.status != GatewayStatus.CONNECTED:
            logger.warning(f"Gateway {gateway_id} is not connected, skipping log collection")
            return
        
        try:
            # Create adapter for this gateway
            adapter = self.adapter_factory.create_adapter(gateway)
            await adapter.connect()
            
            # Fetch transactional logs from gateway
            logs = await adapter.get_transactional_logs(
                start_time=start_time,
                end_time=end_time,
            )
            
            if not logs:
                logger.info(f"No transactional logs found for gateway {gateway_id}")
                await adapter.disconnect()
                return
            
            # Store logs in repository
            log_repo = TransactionalLogRepository()
            stored_count = log_repo.bulk_create(logs)
            logger.info(f"Stored {stored_count} transactional logs for gateway {gateway_id}")
            
            # Aggregate logs into metrics for all time buckets
            if generate_all_buckets:
                # Generate metrics for all time buckets
                time_buckets = [
                    TimeBucket.ONE_MINUTE,
                    TimeBucket.FIVE_MINUTES,
                    TimeBucket.ONE_HOUR,
                    TimeBucket.ONE_DAY,
                ]
            else:
                # Generate metrics for specified bucket only
                time_buckets = [TimeBucket(time_bucket)]
            
            total_metrics_created = 0
            for bucket in time_buckets:
                metrics = self._aggregate_logs_to_metrics(
                    logs=logs,
                    gateway_id=gateway_id,
                    time_bucket=bucket,
                )
                
                # Store metrics using bulk operation for performance
                if metrics:
                    try:
                        stored_count = self.metrics_repo.bulk_create_metrics(metrics)
                        total_metrics_created += stored_count
                        logger.info(
                            f"Bulk created {stored_count}/{len(metrics)} metrics "
                            f"for gateway {gateway_id} (bucket: {bucket.value})"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to bulk create metrics for bucket {bucket.value}: {e}",
                            exc_info=True
                        )
            
            logger.info(
                f"Total: Created {total_metrics_created} metrics from {len(logs)} logs "
                f"for gateway {gateway_id} across {len(time_buckets)} time buckets"
            )
            
            await adapter.disconnect()
            
        except Exception as e:
            logger.error(
                f"Failed to collect transactional logs for gateway {gateway_id}: {e}",
                exc_info=True
            )
    
    def _aggregate_logs_to_metrics(
        self,
        logs: List[TransactionalLog],
        gateway_id: UUID,
        time_bucket: TimeBucket,
    ) -> List[Metric]:
        """
        Aggregate transactional logs into time-bucketed metrics.
        
        Groups logs by time bucket and API, then calculates:
        - Response time percentiles (p50, p95, p99)
        - Error rate
        - Throughput (requests per bucket)
        - Availability
        
        Args:
            logs: List of transactional logs to aggregate
            gateway_id: Gateway UUID
            time_bucket: Time bucket size for aggregation
            
        Returns:
            List of aggregated metrics
        """
        from collections import defaultdict
        import statistics
        
        # Group logs by time bucket and API
        buckets: Dict[tuple, List[TransactionalLog]] = defaultdict(list)
        
        for log in logs:
            # Calculate bucket timestamp
            log_time = datetime.utcfromtimestamp(log.timestamp / 1000)
            bucket_time = self._floor_to_bucket(log_time, time_bucket)
            
            # Group by (bucket_time, api_id)
            key = (bucket_time, log.api_id)
            buckets[key].append(log)
        
        # Create metrics for each bucket
        metrics = []
        for (bucket_time, api_id), bucket_logs in buckets.items():
            # Extract response times (convert to float for consistency)
            response_times = [float(log.total_time_ms) for log in bucket_logs]
            
            # Calculate percentiles
            response_times_sorted = sorted(response_times)
            p50 = self._percentile(response_times_sorted, 50)
            p95 = self._percentile(response_times_sorted, 95)
            p99 = self._percentile(response_times_sorted, 99)
            
            # Calculate error rate
            error_count = sum(1 for log in bucket_logs if log.status_code >= 400)
            error_rate = error_count / len(bucket_logs) if bucket_logs else 0.0
            
            # Calculate throughput (requests per bucket)
            throughput = len(bucket_logs)
            
            # Calculate availability (percentage of successful requests)
            success_count = len(bucket_logs) - error_count
            availability = (success_count / len(bucket_logs) * 100) if bucket_logs else 100.0
            
            # Calculate additional metrics
            response_time_avg = sum(response_times) / len(response_times) if response_times else 0.0
            response_time_min = min(response_times) if response_times else 0.0
            response_time_max = max(response_times) if response_times else 0.0
            
            # Calculate timing breakdown
            gateway_times = [log.gateway_time_ms for log in bucket_logs]
            backend_times = [log.backend_time_ms for log in bucket_logs]
            gateway_time_avg = sum(gateway_times) / len(gateway_times) if gateway_times else 0.0
            backend_time_avg = sum(backend_times) / len(backend_times) if backend_times else 0.0
            
            # Calculate data transfer
            request_sizes = [log.request_size for log in bucket_logs]
            response_sizes = [log.response_size for log in bucket_logs]
            total_data_size = sum(request_sizes) + sum(response_sizes)
            avg_request_size = sum(request_sizes) / len(request_sizes) if request_sizes else 0.0
            avg_response_size = sum(response_sizes) / len(response_sizes) if response_sizes else 0.0
            
            # Calculate status code distribution
            status_2xx = sum(1 for log in bucket_logs if 200 <= log.status_code < 300)
            status_3xx = sum(1 for log in bucket_logs if 300 <= log.status_code < 400)
            status_4xx = sum(1 for log in bucket_logs if 400 <= log.status_code < 500)
            status_5xx = sum(1 for log in bucket_logs if 500 <= log.status_code < 600)
            
            # Create metric with all required fields
            metric = Metric(
                api_id=api_id,
                gateway_id=gateway_id,
                application_id=None,  # Can be enhanced later
                operation=None,  # Can be enhanced later
                timestamp=bucket_time,
                time_bucket=time_bucket,
                # Request counts
                request_count=len(bucket_logs),
                success_count=success_count,
                failure_count=error_count,
                timeout_count=0,  # Can be enhanced later
                error_rate=error_rate * 100,  # Convert to percentage
                availability=availability,
                # Response time metrics
                response_time_avg=response_time_avg,
                response_time_min=response_time_min,
                response_time_max=response_time_max,
                response_time_p50=p50,
                response_time_p95=p95,
                response_time_p99=p99,
                # Timing breakdown
                gateway_time_avg=gateway_time_avg,
                backend_time_avg=backend_time_avg,
                # Throughput
                throughput=throughput,
                # Data transfer
                total_data_size=total_data_size,
                avg_request_size=avg_request_size,
                avg_response_size=avg_response_size,
                # Cache metrics (defaults)
                cache_hit_count=0,
                cache_miss_count=0,
                cache_bypass_count=0,
                cache_hit_rate=0.0,
                # Status codes
                status_2xx_count=status_2xx,
                status_3xx_count=status_3xx,
                status_4xx_count=status_4xx,
                status_5xx_count=status_5xx,
                status_codes={},
                # Optional fields
                endpoint_metrics=None,
                vendor_metadata=None,
            )
            metrics.append(metric)
        
        return metrics
    
    def _floor_to_bucket(self, timestamp: datetime, bucket: TimeBucket) -> datetime:
        """
        Floor a timestamp to the start of its time bucket.
        
        Args:
            timestamp: Timestamp to floor
            bucket: Time bucket size
            
        Returns:
            Start of the time bucket
        """
        if bucket == TimeBucket.ONE_MINUTE:
            return timestamp.replace(second=0, microsecond=0)
        elif bucket == TimeBucket.FIVE_MINUTES:
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif bucket == TimeBucket.ONE_HOUR:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif bucket == TimeBucket.ONE_DAY:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """
        Calculate percentile from sorted values.
        
        Args:
            sorted_values: List of values (must be sorted)
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100) * (len(sorted_values) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        weight = index - lower
        
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    async def drill_down_to_logs(
        self,
        metric_id: str,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Drill down from a metric to its source transactional logs.
        
        This method:
        1. Retrieves the metric by ID
        2. Calculates the time range for the metric's bucket
        3. Queries transactional logs for that API, gateway, and time range
        4. Returns the logs with metric context
        
        Args:
            metric_id: ID of the metric to drill down from
            limit: Maximum number of logs to return
            
        Returns:
            dict: Metric context and associated transactional logs
        """
        # Get the metric
        metric = self.metrics_repo.get(metric_id)
        if not metric:
            logger.error(f"Metric {metric_id} not found")
            return {
                "metric": None,
                "logs": [],
                "total_logs": 0,
                "error": "Metric not found"
            }
        
        # Calculate time range for the metric's bucket
        bucket_start = metric.timestamp
        bucket_end = self._get_bucket_end(bucket_start, metric.time_bucket)
        
        # Query transactional logs for this metric's context
        log_repo = TransactionalLogRepository()
        logs, total = log_repo.find_logs(
            gateway_id=str(metric.gateway_id),
            api_id=str(metric.api_id),
            start_time=bucket_start,
            end_time=bucket_end,
            size=limit,
        )
        
        logger.info(
            f"Drill-down for metric {metric_id}: found {total} logs "
            f"(returning {len(logs)}) for API {metric.api_id} "
            f"in time range {bucket_start} to {bucket_end}"
        )
        
        return {
            "metric": metric,
            "metric_summary": {
                "api_id": str(metric.api_id),
                "gateway_id": str(metric.gateway_id),
                "timestamp": metric.timestamp,
                "time_bucket": metric.time_bucket.value,
                "request_count": metric.request_count,
                "error_rate": metric.error_rate,
                "response_time_p50": metric.response_time_p50,
                "response_time_p95": metric.response_time_p95,
                "response_time_p99": metric.response_time_p99,
            },
            "time_range": {
                "start": bucket_start,
                "end": bucket_end,
            },
            "logs": logs,
            "total_logs": total,
            "returned_logs": len(logs),
        }
    
    def _get_bucket_end(self, bucket_start: datetime, time_bucket: TimeBucket) -> datetime:
        """
        Calculate the end time of a time bucket.
        
        Args:
            bucket_start: Start of the time bucket
            time_bucket: Time bucket size
            
        Returns:
            End of the time bucket
        """
        if time_bucket == TimeBucket.ONE_MINUTE:
            return bucket_start + timedelta(minutes=1)
        elif time_bucket == TimeBucket.FIVE_MINUTES:
            return bucket_start + timedelta(minutes=5)
        elif time_bucket == TimeBucket.ONE_HOUR:
            return bucket_start + timedelta(hours=1)
        elif time_bucket == TimeBucket.ONE_DAY:
            return bucket_start + timedelta(days=1)
        else:
            return bucket_start + timedelta(minutes=1)
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from all connected Gateways.
        
        Returns:
            dict: Collection results with statistics
        """
        logger.info("Starting metrics collection across all gateways")
        
        # Get all connected gateways
        gateways, total = self.gateway_repo.find_connected_gateways(size=1000)
        
        if not gateways:
            logger.warning("No connected gateways found")
            return {
                "total_gateways": 0,
                "successful_gateways": 0,
                "failed_gateways": 0,
                "total_metrics_collected": 0,
                "errors": [],
            }
        
        results = {
            "total_gateways": len(gateways),
            "successful_gateways": 0,
            "failed_gateways": 0,
            "total_metrics_collected": 0,
            "errors": [],
        }
        
        # Collect metrics from each gateway
        for gateway in gateways:
            try:
                gateway_result = await self.collect_gateway_metrics(gateway.id)
                results["successful_gateways"] += 1
                results["total_metrics_collected"] += gateway_result["metrics_collected"]
            except Exception as e:
                logger.error(f"Failed to collect metrics from gateway {gateway.id}: {e}")
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error": str(e),
                })
        
        logger.info(
            f"Metrics collection complete: {results['total_metrics_collected']} metrics "
            f"from {results['successful_gateways']}/{results['total_gateways']} gateways"
        )
        
        return results
    
    async def collect_gateway_metrics(
        self,
        gateway_id: UUID,
        time_range_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        Collect metrics from a specific Gateway.
        
        Args:
            gateway_id: Gateway UUID
            time_range_minutes: Time range for metrics collection
            
        Returns:
            dict: Collection results for this gateway
            
        Raises:
            ValueError: If gateway not found
            RuntimeError: If collection fails
        """
        logger.info(f"Collecting metrics from gateway {gateway_id}")
        
        # Get gateway configuration
        gateway = self.gateway_repo.get(str(gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {gateway_id} not found")
        
        if gateway.status != GatewayStatus.CONNECTED:
            raise RuntimeError(f"Gateway {gateway_id} is not connected")
        
        try:
            # Create adapter for this gateway
            adapter = self.adapter_factory.create_adapter(gateway)
            
            # Connect to gateway
            await adapter.connect()
            
            # Note: collect_metrics has been removed from base adapter
            # Metrics should now be derived from transactional logs
            # This functionality needs to be reimplemented
            stored_count = 0
            
            # Disconnect from gateway
            await adapter.disconnect()
            
            result = {
                "gateway_id": str(gateway_id),
                "gateway_name": gateway.name,
                "metrics_collected": stored_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(
                f"Metrics collection complete for gateway {gateway_id}: "
                f"{stored_count} metrics stored"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Metrics collection failed for gateway {gateway_id}: {e}")
            raise RuntimeError(f"Failed to collect metrics from gateway {gateway_id}: {e}")
    
    def _add_time_buckets(self, metrics: List[Metric]) -> List[Metric]:
        """
        Add time bucket information to metrics.
        
        Metrics are stored in time-bucketed indices for efficient querying:
        - 1-minute buckets: Real-time monitoring (24h retention)
        - 5-minute buckets: Recent trends (7d retention)
        - 1-hour buckets: Historical analysis (30d retention)
        - 1-day buckets: Long-term trends (90d retention)
        
        Args:
            metrics: List of metrics to process
            
        Returns:
            List of metrics with time_bucket field set
        """
        bucketed_metrics = []
        
        for metric in metrics:
            # Default to 1-minute bucket for real-time metrics
            if not hasattr(metric, 'time_bucket') or metric.time_bucket is None:
                metric.time_bucket = TimeBucket.ONE_MINUTE
            
            bucketed_metrics.append(metric)
        
        return bucketed_metrics
    
    def _calculate_time_bucket(self, timestamp: datetime, bucket_size: TimeBucket) -> datetime:
        """
        Calculate the start of a time bucket for a given timestamp.
        
        Args:
            timestamp: The timestamp to bucket
            bucket_size: The bucket size
            
        Returns:
            Start of the time bucket
        """
        if bucket_size == TimeBucket.ONE_MINUTE:
            return timestamp.replace(second=0, microsecond=0)
        elif bucket_size == TimeBucket.FIVE_MINUTES:
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif bucket_size == TimeBucket.ONE_HOUR:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif bucket_size == TimeBucket.ONE_DAY:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp
    
    async def aggregate_metrics(
        self,
        source_bucket: TimeBucket,
        target_bucket: TimeBucket,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """
        Aggregate metrics from smaller buckets into larger buckets.
        
        This implements the aggregation hierarchy:
        - 1m → 5m: Aggregate 5 one-minute buckets
        - 5m → 1h: Aggregate 12 five-minute buckets
        - 1h → 1d: Aggregate 24 one-hour buckets
        
        Args:
            source_bucket: Source time bucket size
            target_bucket: Target time bucket size
            start_time: Start of aggregation period
            end_time: End of aggregation period
            
        Returns:
            Number of aggregated metrics created
        """
        logger.info(
            f"Aggregating metrics from {source_bucket.value} to {target_bucket.value} "
            f"for period {start_time} to {end_time}"
        )
        
        # This is a placeholder for the aggregation logic
        # The actual implementation would:
        # 1. Query source bucket metrics
        # 2. Group by API and time bucket
        # 3. Calculate aggregated statistics
        # 4. Store in target bucket
        
        # TODO: Implement aggregation logic in Phase 0.6 (Repository Layer)
        logger.warning("Metric aggregation not yet implemented - requires repository updates")
        return 0
    
    def get_api_metrics(
        self,
        api_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> tuple[List[Metric], int]:
        """
        Get metrics for an API within a time range.
        
        Args:
            api_id: API UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of metrics to return
            
        Returns:
            tuple[List[Metric], int]: List of metrics and total count
        """
        return self.metrics_repo.find_by_api(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            size=limit,
        )
    
    def get_api_metrics_auto_bucket(
        self,
        api_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """
        Get time-bucketed metrics with automatic bucket selection.
        
        Automatically selects the optimal time bucket based on the time range:
        - <= 2 hours: 1m bucket (high granularity)
        - <= 24 hours: 5m bucket (medium granularity)
        - <= 7 days: 1h bucket (lower granularity)
        - > 7 days: 1d bucket (lowest granularity)
        
        Args:
            api_id: API UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of data points to return
            
        Returns:
            Dictionary containing time-series, aggregated metrics, and selected bucket info
        """
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Automatically select optimal time bucket
        time_bucket = self.metrics_repo.get_optimal_time_bucket(start_time, end_time)
        
        logger.info(
            f"Auto-selected time bucket {time_bucket.value} for range "
            f"{start_time.isoformat()} to {end_time.isoformat()}"
        )
        
        # Get metrics with the selected bucket
        result = self.get_api_metrics_with_aggregation(
            api_id=api_id,
            time_bucket=time_bucket,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        
        # Add bucket selection info to result
        result["selected_bucket"] = time_bucket.value
        result["bucket_selection_reason"] = self._get_bucket_selection_reason(start_time, end_time)
        
        return result
    
    def _get_bucket_selection_reason(self, start_time: datetime, end_time: datetime) -> str:
        """Get human-readable reason for bucket selection."""
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600
        
        if hours <= 2:
            return "High granularity (1m) for short time range (<= 2 hours)"
        elif hours <= 24:
            return "Medium granularity (5m) for daily time range (<= 24 hours)"
        elif hours <= 168:
            return "Lower granularity (1h) for weekly time range (<= 7 days)"
        else:
            return "Lowest granularity (1d) for long time range (> 7 days)"
    
    def get_api_metrics_with_aggregation(
        self,
        api_id: UUID,
        time_bucket: Optional[TimeBucket] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """
        Get time-bucketed metrics for an API with aggregated statistics.
        
        This method retrieves metrics from time-bucketed indices and calculates:
        - Time-series data points
        - Aggregated metrics (total requests, success rate, avg response time, etc.)
        - Cache metrics (hit rate, hits, misses, bypasses)
        - Timing breakdown (gateway vs backend time)
        - HTTP status code distribution
        
        Args:
            api_id: API UUID
            time_bucket: Time bucket granularity (1m, 5m, 1h, 1d). If None, auto-selects optimal bucket.
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of data points to return
            
        Returns:
            Dictionary containing time-series, aggregated metrics, and breakdowns
        """
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Auto-select time bucket if not provided
        if time_bucket is None:
            time_bucket = self.metrics_repo.get_optimal_time_bucket(start_time, end_time)
            logger.info(f"Auto-selected time bucket: {time_bucket.value}")
        
        # Query metrics from the time-bucketed index
        metrics, total = self.metrics_repo.find_by_time_bucket(
            api_id=api_id,
            time_bucket=time_bucket,
            start_time=start_time,
            end_time=end_time,
            size=limit,
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
        
        return {
            "time_series": time_series,
            "aggregated": aggregated,
            "cache_metrics": cache_metrics,
            "timing_breakdown": timing_breakdown,
            "status_breakdown": status_breakdown,
            "total_data_points": len(time_series),
        }
    
    def get_gateway_metrics(
        self,
        gateway_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> tuple[List[Metric], int]:
        """
        Get metrics for all APIs in a Gateway within a time range.
        
        Args:
            gateway_id: Gateway UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of metrics to return
            
        Returns:
            tuple[List[Metric], int]: List of metrics and total count
        """
        return self.metrics_repo.find_by_gateway(
            gateway_id=gateway_id,
            start_time=start_time,
            end_time=end_time,
            size=limit,
        )
    
    def get_latest_metric(self, api_id: UUID) -> Optional[Metric]:
        """
        Get the most recent metric for an API.
        
        Args:
            api_id: API UUID
            
        Returns:
            Latest metric if found, None otherwise
        """
        return self.metrics_repo.get_latest_metric(api_id)
    
    def get_time_series(
        self,
        api_id: UUID,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1h",
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated time-series metrics for an API.
        
        Args:
            api_id: API UUID
            start_time: Start of time range
            end_time: End of time range
            interval: Aggregation interval (e.g., "1m", "5m", "1h", "1d")
            
        Returns:
            List of aggregated metric buckets
        """
        return self.metrics_repo.get_time_series(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
    
    def get_aggregated_metrics(
        self,
        api_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for an API over a time range.
        
        Args:
            api_id: API UUID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary with aggregated metrics
        """
        return self.metrics_repo.get_aggregated_metrics(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )
    
    def analyze_trends(
        self,
        api_id: UUID,
        metric_name: str,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific metric.
        
        Args:
            api_id: API UUID
            metric_name: Name of metric to analyze (e.g., "response_time_p95", "error_rate")
            time_range_hours: Hours of historical data to analyze
            
        Returns:
            dict: Trend analysis results
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # Get time series data
        time_series = self.get_time_series(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            interval="1h",
        )
        
        if not time_series:
            return {
                "metric_name": metric_name,
                "trend": "insufficient_data",
                "direction": None,
                "change_percentage": 0.0,
                "current_value": None,
                "average_value": None,
            }
        
        # Extract metric values
        metric_key = f"avg_{metric_name}"
        values: List[float] = []
        for bucket in time_series:
            value = bucket.get(metric_key)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))
        
        if not values:
            return {
                "metric_name": metric_name,
                "trend": "no_data",
                "direction": None,
                "change_percentage": 0.0,
                "current_value": None,
                "average_value": None,
            }
        
        # Calculate trend
        current_value: float = values[-1]
        average_value: float = sum(values) / len(values)
        
        # Simple linear regression for trend direction
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = average_value
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.01 * average_value:
            trend = "stable"
            direction = "flat"
        elif slope > 0:
            trend = "increasing"
            direction = "up"
        else:
            trend = "decreasing"
            direction = "down"
        
        # Calculate change percentage
        if len(values) > 1:
            first_value = values[0]
            change_percentage = ((current_value - first_value) / first_value * 100) if first_value != 0 else 0
        else:
            change_percentage = 0.0
        
        return {
            "metric_name": metric_name,
            "trend": trend,
            "direction": direction,
            "change_percentage": round(change_percentage, 2),
            "current_value": round(current_value, 2),
            "average_value": round(average_value, 2),
            "slope": round(slope, 4),
            "data_points": len(values),
        }
    
    def calculate_health_score(self, api_id: UUID) -> float:
        """
        Calculate health score for an API based on recent metrics.
        
        Args:
            api_id: API UUID
            
        Returns:
            Health score (0-100)
        """
        # Get metrics from last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        aggregated = self.get_aggregated_metrics(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )
        
        if not aggregated:
            return 50.0  # Default score if no data
        
        # Calculate health score based on multiple factors
        # Availability (40% weight)
        availability_score = aggregated.get("avg_availability", 100.0) * 0.4
        
        # Error rate (30% weight) - inverse score
        error_rate = aggregated.get("avg_error_rate", 0.0)
        error_score = (1 - min(error_rate, 1.0)) * 30.0
        
        # Response time (30% weight) - inverse score
        # Assume good response time is < 200ms, bad is > 1000ms
        p95_response = aggregated.get("avg_response_time_p95", 200.0)
        if p95_response < 200:
            response_score = 30.0
        elif p95_response > 1000:
            response_score = 0.0
        else:
            response_score = 30.0 * (1 - (p95_response - 200) / 800)
        
        health_score = availability_score + error_score + response_score
        
        return round(min(max(health_score, 0.0), 100.0), 2)


# Made with Bob