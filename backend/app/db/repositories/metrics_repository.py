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
from app.models.metric import Metric

logger = logging.getLogger(__name__)


class MetricsRepository(BaseRepository[Metric]):
    """Repository for Metric entity operations with time-series support."""
    
    def __init__(self):
        """
        Initialize the Metrics repository.
        
        Note: Uses monthly index pattern api-metrics-{YYYY.MM}
        """
        # Base index pattern - actual index determined by timestamp
        super().__init__(index_name="api-metrics-*", model_class=Metric)
    
    def _get_index_name(self, timestamp: datetime) -> str:
        """
        Get the index name for a specific timestamp.
        
        Args:
            timestamp: Timestamp to get index for
            
        Returns:
            Index name in format api-metrics-{YYYY.MM}
        """
        return f"api-metrics-{timestamp.strftime('%Y.%m')}"
    
    def _get_index_pattern(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> str:
        """
        Get index pattern for a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Index pattern (single index, list, or wildcard)
        """
        if not start_time and not end_time:
            return "api-metrics-*"
        
        if start_time and end_time:
            # Generate list of indices for the range
            indices = []
            current = start_time.replace(day=1)
            end = end_time.replace(day=1)
            
            while current <= end:
                indices.append(f"api-metrics-{current.strftime('%Y.%m')}")
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            
            return ",".join(indices)
        
        # Single timestamp
        timestamp = start_time or end_time or datetime.utcnow()
        return self._get_index_name(timestamp)
    
    def create(self, document: Metric, doc_id: Optional[str] = None) -> Metric:
        """
        Create a new metric document in the appropriate monthly index.
        
        Args:
            document: Metric model instance to create
            doc_id: Optional document ID
            
        Returns:
            The created metric with ID
        """
        # Override index name based on timestamp
        original_index = self.index_name
        self.index_name = self._get_index_name(document.timestamp)
        
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
                    {"term": {"api_id.keyword": str(api_id)}},
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
            "term": {"api_id.keyword": str(api_id)}
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
                        {"term": {"api_id.keyword": str(api_id)}},
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
                        {"term": {"api_id.keyword": str(api_id)}},
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
    
    def bulk_create_metrics(self, metrics: List[Metric]) -> int:
        """
        Bulk create multiple metrics (handles multiple indices).
        
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
                
                action = {
                    "_index": self._get_index_name(metric.timestamp),
                    "_source": doc_dict,
                }
                
                if metric.id:
                    action["_id"] = str(metric.id)
                
                actions.append(action)
            
            success, failed = helpers.bulk(
                self.client,
                actions,
                refresh=True,
            )
            
            logger.info(
                f"Bulk created {success} metrics, {failed} failed"
            )
            return success
            
        except Exception as e:
            logger.error(f"Bulk create metrics failed: {e}")
            raise


# Made with Bob