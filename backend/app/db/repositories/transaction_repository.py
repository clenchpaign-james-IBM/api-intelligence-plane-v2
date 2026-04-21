"""
Transaction Repository

Handles CRUD operations and queries for TransactionalLog entities.
Provides aggregation methods to convert transactional logs into time-bucketed metrics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from opensearchpy import OpenSearch

from app.db.repositories.base import BaseRepository
from app.models.base.transaction import TransactionalLog
from app.models.base.metric import Metric, TimeBucket


class TransactionRepository(BaseRepository[TransactionalLog]):
    """Repository for TransactionalLog entities with aggregation capabilities."""

    def __init__(self):
        """Initialize repository with OpenSearch client."""
        super().__init__("transactional-logs", TransactionalLog)

    def create_transaction(self, transaction: TransactionalLog) -> TransactionalLog:
        """
        Create a new transactional log entry.

        Args:
            transaction: TransactionalLog entity to create

        Returns:
            Created TransactionalLog with generated ID
        """
        doc = transaction.model_dump(mode="json", exclude_none=True)
        
        # Use timestamp-based index pattern for better data management
        index_name = f"{self.index_name}-{transaction.timestamp.strftime('%Y.%m')}"
        
        result = self.client.index(
            index=index_name,
            body=doc,
            id=str(transaction.id) if transaction.id else None
        )
        
        transaction.id = UUID(result["_id"])
        return transaction

    def find_by_api(
        self,
        api_id: UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[TransactionalLog]:
        """
        Find transactional logs for a specific API within a time range.

        Args:
            api_id: API identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of results

        Returns:
            List of TransactionalLog entities
        """
        query = {
            "bool": {
                "must": [
                    {"term": {"api_id": str(api_id)}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat()
                            }
                        }
                    }
                ]
            }
        }

        return self._search_transactions(query, limit)

    def find_by_gateway(
        self,
        gateway_id: UUID,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[TransactionalLog]:
        """
        Find transactional logs for a specific gateway within a time range.

        Args:
            gateway_id: Gateway identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of results

        Returns:
            List of TransactionalLog entities
        """
        query = {
            "bool": {
                "must": [
                    {"term": {"gateway_id": str(gateway_id)}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat()
                            }
                        }
                    }
                ]
            }
        }

        return self._search_transactions(query, limit)

    def find_by_application(
        self,
        application_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[TransactionalLog]:
        """
        Find transactional logs for a specific application within a time range.

        Args:
            application_id: Application/client identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of results

        Returns:
            List of TransactionalLog entities
        """
        query = {
            "bool": {
                "must": [
                    {"term": {"client_id": application_id}},
                    {
                        "range": {
                            "timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat()
                            }
                        }
                    }
                ]
            }
        }

        return self._search_transactions(query, limit)

    def aggregate_to_metrics(
        self,
        time_bucket: TimeBucket,
        start_time: datetime,
        end_time: datetime,
        api_id: Optional[UUID] = None,
        gateway_id: Optional[UUID] = None
    ) -> List[Metric]:
        """
        Aggregate transactional logs into time-bucketed metrics.

        Args:
            time_bucket: Time bucket size (1m, 5m, 1h, 1d)
            start_time: Start of aggregation period
            end_time: End of aggregation period
            api_id: Optional API filter
            gateway_id: Optional gateway filter

        Returns:
            List of aggregated Metric entities
        """
        # Build aggregation query
        must_clauses = [
            {
                "range": {
                    "timestamp": {
                        "gte": start_time.isoformat(),
                        "lte": end_time.isoformat()
                    }
                }
            }
        ]

        if api_id:
            must_clauses.append({"term": {"api_id": str(api_id)}})
        if gateway_id:
            must_clauses.append({"term": {"gateway_id": str(gateway_id)}})

        # Determine bucket interval
        interval_map = {
            TimeBucket.ONE_MINUTE: "1m",
            TimeBucket.FIVE_MINUTES: "5m",
            TimeBucket.ONE_HOUR: "1h",
            TimeBucket.ONE_DAY: "1d"
        }
        interval = interval_map[time_bucket]

        # Build comprehensive aggregation query
        agg_query = {
            "size": 0,
            "query": {"bool": {"must": must_clauses}},
            "aggs": {
                "time_buckets": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 1
                    },
                    "aggs": {
                        "by_api": {
                            "terms": {"field": "api_id", "size": 1000},
                            "aggs": {
                                "by_gateway": {
                                    "terms": {"field": "gateway_id", "size": 100},
                                    "aggs": {
                                        "by_operation": {
                                            "terms": {"field": "operation", "size": 100},
                                            "aggs": self._get_metric_aggregations()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Execute aggregation
        index_pattern = f"{self.index_name}-*"
        result = self.client.search(index=index_pattern, body=agg_query)

        # Convert aggregation results to Metric entities
        metrics = []
        for time_bucket_data in result["aggregations"]["time_buckets"]["buckets"]:
            bucket_time = datetime.fromisoformat(time_bucket_data["key_as_string"].replace("Z", "+00:00"))
            
            for api_bucket in time_bucket_data["by_api"]["buckets"]:
                api_id_str = api_bucket["key"]
                
                for gateway_bucket in api_bucket["by_gateway"]["buckets"]:
                    gateway_id_str = gateway_bucket["key"]
                    
                    for operation_bucket in gateway_bucket["by_operation"]["buckets"]:
                        operation = operation_bucket["key"]
                        
                        metric = self._build_metric_from_aggregation(
                            bucket_time=bucket_time,
                            time_bucket=time_bucket,
                            api_id=UUID(api_id_str),
                            gateway_id=UUID(gateway_id_str),
                            operation=operation,
                            agg_data=operation_bucket
                        )
                        metrics.append(metric)

        return metrics

    def _get_metric_aggregations(self) -> Dict[str, Any]:
        """Build the aggregation structure for metrics calculation."""
        return {
            "request_count": {"value_count": {"field": "transaction_id"}},
            "total_time_avg": {"avg": {"field": "total_time_ms"}},
            "gateway_time_avg": {"avg": {"field": "gateway_time_ms"}},
            "backend_time_avg": {"avg": {"field": "backend_time_ms"}},
            "response_time_percentiles": {
                "percentiles": {
                    "field": "total_time_ms",
                    "percents": [50, 95, 99]
                }
            },
            "error_count": {
                "filter": {"term": {"is_error": True}}
            },
            "status_2xx": {
                "filter": {"range": {"http_status_code": {"gte": 200, "lt": 300}}}
            },
            "status_3xx": {
                "filter": {"range": {"http_status_code": {"gte": 300, "lt": 400}}}
            },
            "status_4xx": {
                "filter": {"range": {"http_status_code": {"gte": 400, "lt": 500}}}
            },
            "status_5xx": {
                "filter": {"range": {"http_status_code": {"gte": 500, "lt": 600}}}
            },
            "cache_hits": {
                "filter": {"term": {"cache_hit": True}}
            },
            "cache_misses": {
                "filter": {"term": {"cache_hit": False}}
            },
            "request_size_avg": {"avg": {"field": "request_size_bytes"}},
            "response_size_avg": {"avg": {"field": "response_size_bytes"}}
        }

    def _build_metric_from_aggregation(
        self,
        bucket_time: datetime,
        time_bucket: TimeBucket,
        api_id: UUID,
        gateway_id: UUID,
        operation: str,
        agg_data: Dict[str, Any]
    ) -> Metric:
        """Build a Metric entity from aggregation data."""
        request_count = agg_data["request_count"]["value"]
        error_count = agg_data["error_count"]["doc_count"]
        
        # Calculate error rate
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0.0
        
        # Calculate cache metrics
        cache_hits = agg_data["cache_hits"]["doc_count"]
        cache_misses = agg_data["cache_misses"]["doc_count"]
        cache_total = cache_hits + cache_misses
        cache_hit_rate = (cache_hits / cache_total * 100) if cache_total > 0 else 0.0
        
        # Extract percentiles
        percentiles = agg_data["response_time_percentiles"]["values"]
        
        # Build metric entity
        # Calculate additional required fields
        success_count = request_count - error_count
        availability = (success_count / request_count * 100) if request_count > 0 else 100.0
        
        # Calculate throughput (requests per second based on time bucket)
        bucket_seconds = {
            TimeBucket.ONE_MINUTE: 60,
            TimeBucket.FIVE_MINUTES: 300,
            TimeBucket.ONE_HOUR: 3600,
            TimeBucket.ONE_DAY: 86400
        }
        throughput = request_count / bucket_seconds[time_bucket]
        
        # Calculate total data size
        request_size_avg = agg_data["request_size_avg"]["value"] if agg_data["request_size_avg"]["value"] else 0.0
        response_size_avg = agg_data["response_size_avg"]["value"] if agg_data["response_size_avg"]["value"] else 0.0
        total_data_size = int((request_size_avg + response_size_avg) * request_count)
        
        return Metric(
            timestamp=bucket_time,
            time_bucket=time_bucket,
            api_id=str(api_id),
            gateway_id=gateway_id,
            application_id=None,  # Not tracked at this aggregation level
            operation=operation,
            request_count=int(request_count),
            success_count=success_count,
            failure_count=error_count,
            timeout_count=0,  # Not tracked in current aggregation
            error_rate=round(error_rate, 2),
            availability=round(availability, 2),
            response_time_avg=round(agg_data["total_time_avg"]["value"], 2) if agg_data["total_time_avg"]["value"] else 0.0,
            response_time_min=0.0,  # Not tracked in current aggregation
            response_time_max=0.0,  # Not tracked in current aggregation
            response_time_p50=round(percentiles.get("50.0", 0.0), 2),
            response_time_p95=round(percentiles.get("95.0", 0.0), 2),
            response_time_p99=round(percentiles.get("99.0", 0.0), 2),
            gateway_time_avg=round(agg_data["gateway_time_avg"]["value"], 2) if agg_data["gateway_time_avg"]["value"] else 0.0,
            backend_time_avg=round(agg_data["backend_time_avg"]["value"], 2) if agg_data["backend_time_avg"]["value"] else 0.0,
            throughput=round(throughput, 2),
            total_data_size=total_data_size,
            avg_request_size=round(request_size_avg, 2),
            avg_response_size=round(response_size_avg, 2),
            cache_hit_count=cache_hits,
            cache_miss_count=cache_misses,
            cache_hit_rate=round(cache_hit_rate, 2),
            status_2xx_count=agg_data["status_2xx"]["doc_count"],
            status_3xx_count=agg_data["status_3xx"]["doc_count"],
            status_4xx_count=agg_data["status_4xx"]["doc_count"],
            status_5xx_count=agg_data["status_5xx"]["doc_count"],
            endpoint_metrics=None,
            vendor_metadata={}
        )

    def _search_transactions(
        self,
        query: Dict[str, Any],
        limit: int
    ) -> List[TransactionalLog]:
        """Execute search query and return TransactionalLog entities."""
        index_pattern = f"{self.index_name}-*"
        
        search_body = {
            "query": query,
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        result = self.client.search(index=index_pattern, body=search_body)
        
        transactions = []
        for hit in result["hits"]["hits"]:
            doc = hit["_source"]
            doc["id"] = UUID(hit["_id"])
            transactions.append(TransactionalLog(**doc))
        
        return transactions

# Made with Bob
