"""
Metrics Repository

Provides CRUD operations and time-series queries for Metric entities.
Handles monthly index rotation (api-metrics-{YYYY.MM}).
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.db.repositories.base import BaseRepository
from app.models.base.metric import Metric, TimeBucket

logger = logging.getLogger(__name__)


class MetricsRepository(BaseRepository[Metric]):
    """Repository for Metric entity operations with time-series support."""
    
    def __init__(self):
        """
        Initialize the Metrics repository.
        
        Note: Supports time-bucketed indices:
        - api-metrics-1m-{YYYY.MM} (1-minute buckets, 24h retention)
        - api-metrics-5m-{YYYY.MM} (5-minute buckets, 7d retention)
        - api-metrics-1h-{YYYY.MM} (1-hour buckets, 30d retention)
        - api-metrics-1d-{YYYY.MM} (1-day buckets, 90d retention)
        """
        # Base index pattern - actual index determined by timestamp and time bucket
        super().__init__(index_name="api-metrics-*", model_class=Metric)
    
    def _get_index_name(self, timestamp: datetime, time_bucket: Optional[TimeBucket] = None) -> str:
        """
        Get the index name for a specific timestamp and time bucket.
        
        Args:
            timestamp: Timestamp to get index for
            time_bucket: Time bucket size (1m, 5m, 1h, 1d)
            
        Returns:
            Index name in format api-metrics-{bucket}-{YYYY.MM}
        """
        bucket_suffix = f"-{time_bucket.value}" if time_bucket else ""
        return f"api-metrics{bucket_suffix}-{timestamp.strftime('%Y.%m')}"
    
    def _get_index_pattern(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_bucket: Optional[TimeBucket] = None,
    ) -> str:
        """
        Get index pattern for a time range and time bucket.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            time_bucket: Time bucket size (1m, 5m, 1h, 1d)
            
        Returns:
            Index pattern (single index, list, or wildcard)
        """
        # When no time_bucket specified, use wildcard to match all bucket types
        bucket_suffix = f"-{time_bucket.value}" if time_bucket else "-*"
        
        if not start_time and not end_time:
            return f"api-metrics{bucket_suffix}-*"
        
        if start_time and end_time:
            # Generate list of indices for the range
            indices = []
            current = start_time.replace(day=1)
            end = end_time.replace(day=1)
            
            while current <= end:
                indices.append(f"api-metrics{bucket_suffix}-{current.strftime('%Y.%m')}")
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            
            return ",".join(indices)
        
        # Single timestamp
        timestamp = start_time or end_time or datetime.utcnow()
        return self._get_index_name(timestamp, time_bucket)
    
    def create(self, document: Metric, doc_id: Optional[str] = None) -> Metric:
        """
        Create a new metric document in the appropriate monthly index.
        
        Args:
            document: Metric model instance to create
            doc_id: Optional document ID
            
        Returns:
            The created metric with ID
        """
        # Override index name based on timestamp and time bucket
        original_index = self.index_name
        self.index_name = self._get_index_name(document.timestamp, document.time_bucket)
        
        try:
            result = super().create(document, doc_id)
            return result
        finally:
            self.index_name = original_index
    
    def find_by_api(
        self,
        api_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        size: int = 1000,
        from_: int = 0,
    ) -> tuple[List[Metric], int]:
        """
        Find all metrics for a specific API within a time range.
        
        Args:
            api_id: API UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of metrics, total count)
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        query = {
            "bool": {
                "must": [
                    {"term": {"api_id": str(api_id)}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat(),
                            }
                        }
                    },
                ]
            }
        }
        
        # Use appropriate index pattern
        original_index = self.index_name
        self.index_name = self._get_index_pattern(start_time, end_time)
        
        try:
            sort = [{"timestamp": {"order": "desc"}}]
            return self.search(query, size=size, from_=from_, sort=sort)
        finally:
            self.index_name = original_index
    
    def find_by_gateway(
        self,
        gateway_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        size: int = 1000,
        from_: int = 0,
    ) -> tuple[List[Metric], int]:
        """
        Find all metrics for a specific gateway within a time range.
        
        Args:
            gateway_id: Gateway UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of metrics, total count)
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        query = {
            "bool": {
                "must": [
                    {"term": {"gateway_id": str(gateway_id)}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat(),
                            }
                        }
                    },
                ]
            }
        }
        
        # Use appropriate index pattern
        original_index = self.index_name
        self.index_name = self._get_index_pattern(start_time, end_time)
        
        try:
            sort = [{"timestamp": {"order": "desc"}}]
            return self.search(query, size=size, from_=from_, sort=sort)
        finally:
            self.index_name = original_index
    
    def get_latest_metric(self, api_id: UUID) -> Optional[Metric]:
        """
        Get the most recent metric for an API.
        
        Args:
            api_id: API UUID
            
        Returns:
            Latest metric if found, None otherwise
        """
        query = {
            "term": {"api_id": str(api_id)}
        }
        
        sort = [{"timestamp": {"order": "desc"}}]
        
        # Search recent indices
        original_index = self.index_name
        self.index_name = "api-metrics-*"
        
        try:
            results, _ = self.search(query, size=1, sort=sort)
            return results[0] if results else None
        finally:
            self.index_name = original_index
    
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
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"api_id": str(api_id)}},
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat(),
                                }
                            }
                        },
                    ]
                }
            }
            
            aggs = {
                "metrics_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0,
                    },
                    "aggs": {
                        "avg_response_time_p50": {"avg": {"field": "response_time_p50"}},
                        "avg_response_time_p95": {"avg": {"field": "response_time_p95"}},
                        "avg_response_time_p99": {"avg": {"field": "response_time_p99"}},
                        "avg_error_rate": {"avg": {"field": "error_rate"}},
                        "sum_request_count": {"sum": {"field": "request_count"}},
                        "sum_error_count": {"sum": {"field": "error_count"}},
                        "avg_throughput": {"avg": {"field": "throughput"}},
                        "avg_availability": {"avg": {"field": "availability"}},
                    },
                }
            }
            
            # Use appropriate index pattern
            original_index = self.index_name
            self.index_name = self._get_index_pattern(start_time, end_time)
            
            try:
                response = self.client.search(
                    index=self.index_name,
                    body={
                        "size": 0,
                        "query": query,
                        "aggs": aggs,
                    },
                )
                
                buckets = response["aggregations"]["metrics_over_time"]["buckets"]
                
                return [
                    {
                        "timestamp": bucket["key_as_string"],
                        "doc_count": bucket["doc_count"],
                        "avg_response_time_p50": bucket["avg_response_time_p50"]["value"],
                        "avg_response_time_p95": bucket["avg_response_time_p95"]["value"],
                        "avg_response_time_p99": bucket["avg_response_time_p99"]["value"],
                        "avg_error_rate": bucket["avg_error_rate"]["value"],
                        "sum_request_count": bucket["sum_request_count"]["value"],
                        "sum_error_count": bucket["sum_error_count"]["value"],
                        "avg_throughput": bucket["avg_throughput"]["value"],
                        "avg_availability": bucket["avg_availability"]["value"],
                    }
                    for bucket in buckets
                ]
            finally:
                self.index_name = original_index
                
        except Exception as e:
            logger.error(f"Failed to get time series for API {api_id}: {e}")
            raise
    
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
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"api_id": str(api_id)}},
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat(),
                                }
                            }
                        },
                    ]
                }
            }
            
            aggs = {
                "avg_response_time_p50": {"avg": {"field": "response_time_p50"}},
                "avg_response_time_p95": {"avg": {"field": "response_time_p95"}},
                "avg_response_time_p99": {"avg": {"field": "response_time_p99"}},
                "max_response_time_p99": {"max": {"field": "response_time_p99"}},
                "avg_error_rate": {"avg": {"field": "error_rate"}},
                "max_error_rate": {"max": {"field": "error_rate"}},
                "total_requests": {"sum": {"field": "request_count"}},
                "total_errors": {"sum": {"field": "error_count"}},
                "avg_throughput": {"avg": {"field": "throughput"}},
                "avg_availability": {"avg": {"field": "availability"}},
                "min_availability": {"min": {"field": "availability"}},
            }
            
            # Use appropriate index pattern
            original_index = self.index_name
            self.index_name = self._get_index_pattern(start_time, end_time)
            
            try:
                response = self.client.search(
                    index=self.index_name,
                    body={
                        "size": 0,
                        "query": query,
                        "aggs": aggs,
                    },
                )
                
                agg_results = response["aggregations"]
                
                return {
                    "avg_response_time_p50": agg_results["avg_response_time_p50"]["value"],
                    "avg_response_time_p95": agg_results["avg_response_time_p95"]["value"],
                    "avg_response_time_p99": agg_results["avg_response_time_p99"]["value"],
                    "max_response_time_p99": agg_results["max_response_time_p99"]["value"],
                    "avg_error_rate": agg_results["avg_error_rate"]["value"],
                    "max_error_rate": agg_results["max_error_rate"]["value"],
                    "total_requests": agg_results["total_requests"]["value"],
                    "total_errors": agg_results["total_errors"]["value"],
                    "avg_throughput": agg_results["avg_throughput"]["value"],
                    "avg_availability": agg_results["avg_availability"]["value"],
                    "min_availability": agg_results["min_availability"]["value"],
                }
            finally:
                self.index_name = original_index
                
        except Exception as e:
            logger.error(f"Failed to get aggregated metrics for API {api_id}: {e}")
            raise

    def get_raw_logs_for_metric(
        self,
        metric_id: str,
        transactional_log_repository: Any,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Any], int]:
        """
        Resolve a metric document into the raw transactional logs that contributed to it.

        Args:
            metric_id: Metric document identifier
            transactional_log_repository: Repository exposing find_logs(...)
            limit: Number of logs to return
            offset: Pagination offset

        Returns:
            Matching transactional logs and total count
        """
        metric = self.get(metric_id)
        if metric is None:
            return [], 0

        bucket_durations = {
            TimeBucket.ONE_MINUTE: timedelta(minutes=1),
            TimeBucket.FIVE_MINUTES: timedelta(minutes=5),
            TimeBucket.ONE_HOUR: timedelta(hours=1),
            TimeBucket.ONE_DAY: timedelta(days=1),
        }
        bucket_window = bucket_durations.get(metric.time_bucket, timedelta(hours=1))
        start_time = metric.timestamp
        end_time = metric.timestamp + bucket_window

        return transactional_log_repository.find_logs(
            gateway_id=str(metric.gateway_id),
            api_id=metric.api_id,
            application_id=metric.application_id,
            start_time=start_time,
            end_time=end_time,
            size=limit,
            from_=offset,
        )

    def bulk_create_metrics(self, metrics: List[Metric]) -> int:
        """
        Bulk create multiple metrics with duplicate prevention (handles multiple indices).
        
        Uses composite document IDs to prevent duplicates for the same:
        (api_id, gateway_id, timestamp, time_bucket)
        
        Args:
            metrics: List of Metric instances
            
        Returns:
            Number of successfully created metrics
        """
        try:
            from opensearchpy import helpers
            
            actions = []
            for metric in metrics:
                doc_dict = metric.model_dump(mode="json", exclude_none=True)
                
                # Generate composite ID for duplicate prevention
                # Format: {api_id}_{gateway_id}_{timestamp_iso}_{bucket}
                timestamp_str = metric.timestamp.strftime('%Y%m%d%H%M%S')
                composite_id = f"{metric.api_id}_{metric.gateway_id}_{timestamp_str}_{metric.time_bucket.value}"
                
                action = {
                    "_index": self._get_index_name(metric.timestamp, metric.time_bucket),
                    "_id": composite_id,  # Use composite ID for upsert behavior
                    "_source": doc_dict,
                    "_op_type": "index",  # Use index (upsert) instead of create
                }
                
                actions.append(action)
            
            # Bulk operation with error tracking
            success_count = 0
            error_count = 0
            errors = []
            
            for ok, result in helpers.streaming_bulk(
                self.client,
                actions,
                refresh=True,
                raise_on_error=False,  # Don't fail entire batch on single error
                raise_on_exception=False,
            ):
                if ok:
                    success_count += 1
                else:
                    error_count += 1
                    # Log first 10 errors for debugging
                    if len(errors) < 10:
                        errors.append(result)
            
            if errors:
                logger.warning(
                    f"Bulk create metrics completed with errors: "
                    f"{success_count} succeeded, {error_count} failed. "
                    f"First errors: {errors[:3]}"
                )
            else:
                logger.info(
                    f"Bulk created {success_count} metrics successfully"
                )
            
            return success_count
            
        except Exception as e:
            logger.error(f"Bulk create metrics failed: {e}", exc_info=True)
            raise


# Made with Bob
    
    def find_by_time_bucket(
        self,
        api_id: UUID,
        time_bucket: TimeBucket,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        size: int = 1000,
        from_: int = 0,
    ) -> tuple[List[Metric], int]:
        """
        Find metrics for a specific API and time bucket within a time range.
        
        Args:
            api_id: API UUID
            time_bucket: Time bucket size (1m, 5m, 1h, 1d)
            start_time: Start of time range (default: based on bucket retention)
            end_time: End of time range (default: now)
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of metrics, total count)
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            # Default time range based on bucket retention
            retention_hours = {
                TimeBucket.ONE_MINUTE: 24,
                TimeBucket.FIVE_MINUTES: 168,  # 7 days
                TimeBucket.ONE_HOUR: 720,  # 30 days
                TimeBucket.ONE_DAY: 2160,  # 90 days
            }
            start_time = end_time - timedelta(hours=retention_hours.get(time_bucket, 24))
        
        query = {
            "bool": {
                "must": [
                    {"term": {"api_id": str(api_id)}},
                    {"term": {"time_bucket": time_bucket.value}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat(),
                            }
                        }
                    },
                ]
            }
        }
        
        # Use appropriate index pattern for this time bucket
        original_index = self.index_name
        self.index_name = self._get_index_pattern(start_time, end_time, time_bucket)
        
        try:
            sort = [{"timestamp": {"order": "desc"}}]
            return self.search(query, size=size, from_=from_, sort=sort)
        finally:
            self.index_name = original_index
    
    def get_optimal_time_bucket(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> TimeBucket:
        """
        Determine the optimal time bucket for a given time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Optimal TimeBucket for the range
        """
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600
        
        if hours <= 2:
            return TimeBucket.ONE_MINUTE
        elif hours <= 24:
            return TimeBucket.FIVE_MINUTES
        elif hours <= 168:  # 7 days
            return TimeBucket.ONE_HOUR
        else:
            return TimeBucket.ONE_DAY
    
    def find_by_api_with_bucket(
        self,
        api_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_bucket: Optional[TimeBucket] = None,
        size: int = 1000,
        from_: int = 0,
    ) -> tuple[List[Metric], int]:
        """
        Find metrics for an API with automatic or specified time bucket selection.
        
        Args:
            api_id: API UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            time_bucket: Time bucket size (auto-selected if None)
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of metrics, total count)
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Auto-select optimal time bucket if not specified
        if not time_bucket:
            time_bucket = self.get_optimal_time_bucket(start_time, end_time)
            logger.info(f"Auto-selected time bucket {time_bucket.value} for range {start_time} to {end_time}")
        
    
    def find_by_api_and_gateway(
        self,
        api_id: UUID,
        gateway_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_bucket: Optional[TimeBucket] = None,
        size: int = 1000,
        from_: int = 0,
    ) -> tuple[List[Metric], int]:
        """
        Find metrics for an API scoped to a specific gateway with automatic or specified time bucket selection.
        
        Args:
            api_id: API UUID
            gateway_id: Gateway UUID to scope the query
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            time_bucket: Time bucket size (auto-selected if None)
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of metrics, total count)
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Auto-select optimal time bucket if not specified
        if not time_bucket:
            time_bucket = self.get_optimal_time_bucket(start_time, end_time)
            logger.info(f"Auto-selected time bucket {time_bucket.value} for range {start_time} to {end_time}")
        
        # Build query with both api_id and gateway_id filters
        query = {
            "bool": {
                "must": [
                    {"term": {"api_id": str(api_id)}},
                    {"term": {"gateway_id": str(gateway_id)}},
                    {"term": {"time_bucket": time_bucket.value}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat(),
                            }
                        }
                    },
                ]
            }
        }
        
        # Use appropriate index pattern for this time bucket
        original_index = self.index_name
        self.index_name = self._get_index_pattern(start_time, end_time, time_bucket)
        
        try:
            sort = [{"timestamp": {"order": "desc"}}]
            return self.search(query, size=size, from_=from_, sort=sort)
        finally:
            self.index_name = original_index