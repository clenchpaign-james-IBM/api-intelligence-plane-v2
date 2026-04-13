"""
Migration 011: 1-Minute Metrics Index Template

Creates an index template for api-metrics-1m-* indices with monthly rotation.
High-resolution time-series metrics data for real-time monitoring and alerting.

Retention: 7 days (configurable via ILM policy)
"""

from opensearchpy import OpenSearch


def create_metrics_1m_index_template(client: OpenSearch):
    """
    Create the api-metrics-1m-* index template with appropriate mappings.
    
    This template applies to:
    - api-metrics-1m-2026.03 (March 2026)
    - api-metrics-1m-2026.04 (April 2026)
    - etc.
    
    Stores:
    - 1-minute aggregated metrics from transactional logs
    - High-resolution performance data for real-time monitoring
    - Response time percentiles (p50, p95, p99)
    - Error rates and counts
    - Throughput and availability
    - Cache metrics (hit/miss/bypass rates)
    - Status code distributions
    - Data transfer metrics
    - Timing breakdown (gateway vs backend)
    - Optional per-endpoint metrics breakdowns
    
    Retention Policy:
    - Keep for 7 days for real-time monitoring
    - Roll up to 5-minute buckets for longer retention
    """
    
    template_name = "api-metrics-1m-template"
    
    template_body = {
        "index_patterns": ["api-metrics-1m-*"],
        "template": {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "refresh_interval": "5s",  # Fast refresh for real-time data
                "index": {
                    "max_result_window": 10000,
                    "codec": "best_compression",  # Compress time-series data
                },
            },
            "mappings": {
                "properties": {
                    # ========================================================
                    # Core Identification
                    # ========================================================
                    "id": {
                        "type": "keyword",
                    },
                    "gateway_id": {
                        "type": "keyword",
                    },
                    "api_id": {
                        "type": "keyword",
                    },
                    "application_id": {
                        "type": "keyword",
                    },
                    "operation": {
                        "type": "keyword",
                    },
                    
                    # ========================================================
                    # Time Bucketing
                    # ========================================================
                    "timestamp": {
                        "type": "date",
                    },
                    "time_bucket": {
                        "type": "keyword",
                    },
                    
                    # ========================================================
                    # Request Counts
                    # ========================================================
                    "request_count": {
                        "type": "integer",
                    },
                    "success_count": {
                        "type": "integer",
                    },
                    "failure_count": {
                        "type": "integer",
                    },
                    "timeout_count": {
                        "type": "integer",
                    },
                    "error_rate": {
                        "type": "float",
                    },
                    "availability": {
                        "type": "float",
                    },
                    
                    # ========================================================
                    # Response Time Metrics (milliseconds)
                    # ========================================================
                    "response_time_avg": {
                        "type": "float",
                    },
                    "response_time_min": {
                        "type": "float",
                    },
                    "response_time_max": {
                        "type": "float",
                    },
                    "response_time_p50": {
                        "type": "float",
                    },
                    "response_time_p95": {
                        "type": "float",
                    },
                    "response_time_p99": {
                        "type": "float",
                    },
                    
                    # ========================================================
                    # Timing Breakdown
                    # ========================================================
                    "gateway_time_avg": {
                        "type": "float",
                    },
                    "backend_time_avg": {
                        "type": "float",
                    },
                    
                    # ========================================================
                    # Throughput
                    # ========================================================
                    "throughput": {
                        "type": "float",
                    },
                    
                    # ========================================================
                    # Data Transfer
                    # ========================================================
                    "total_data_size": {
                        "type": "long",
                    },
                    "avg_request_size": {
                        "type": "float",
                    },
                    "avg_response_size": {
                        "type": "float",
                    },
                    
                    # ========================================================
                    # Cache Metrics
                    # ========================================================
                    "cache_hit_count": {
                        "type": "integer",
                    },
                    "cache_miss_count": {
                        "type": "integer",
                    },
                    "cache_bypass_count": {
                        "type": "integer",
                    },
                    "cache_hit_rate": {
                        "type": "float",
                    },
                    
                    # ========================================================
                    # HTTP Status Codes
                    # ========================================================
                    "status_2xx_count": {
                        "type": "integer",
                    },
                    "status_3xx_count": {
                        "type": "integer",
                    },
                    "status_4xx_count": {
                        "type": "integer",
                    },
                    "status_5xx_count": {
                        "type": "integer",
                    },
                    "status_codes": {
                        "type": "object",
                        "enabled": True,
                    },
                    
                    # ========================================================
                    # Per-Endpoint Breakdown (optional)
                    # ========================================================
                    "endpoint_metrics": {
                        "type": "nested",
                        "properties": {
                            "endpoint": {"type": "keyword"},
                            "method": {"type": "keyword"},
                            "request_count": {"type": "integer"},
                            "success_count": {"type": "integer"},
                            "failure_count": {"type": "integer"},
                            "error_rate": {"type": "float"},
                            "response_time_avg": {"type": "float"},
                            "response_time_p50": {"type": "float"},
                            "response_time_p95": {"type": "float"},
                            "response_time_p99": {"type": "float"},
                        },
                    },
                    
                    # ========================================================
                    # Vendor-Specific Extensions
                    # ========================================================
                    "vendor_metadata": {
                        "type": "object",
                        "enabled": True,
                    },
                    
                    # ========================================================
                    # Metadata
                    # ========================================================
                    "created_at": {
                        "type": "date",
                    },
                    "updated_at": {
                        "type": "date",
                    },
                }
            },
        },
        "priority": 200,  # Higher priority than generic api-metrics-* template
    }
    
    client.indices.put_index_template(name=template_name, body=template_body)


def create_metrics_1m_ilm_policy(client: OpenSearch):
    """
    Create ILM (Index Lifecycle Management) policy for 1-minute metrics.
    
    Policy:
    - Hot phase: Keep for 2 days with fast refresh
    - Warm phase: Move to warm nodes after 2 days
    - Delete phase: Delete after 7 days
    
    Note: This is optional and depends on OpenSearch ILM support.
    For basic deployments, manual cleanup scripts can be used instead.
    """
    policy_name = "api-metrics-1m-policy"
    
    # Note: OpenSearch ILM syntax may differ from Elasticsearch
    # This is a conceptual example - adjust based on your OpenSearch version
    policy_body = {
        "policy": {
            "description": "ILM policy for 1-minute metrics indices",
            "default_state": "hot",
            "states": [
                {
                    "name": "hot",
                    "actions": [],
                    "transitions": [
                        {
                            "state_name": "warm",
                            "conditions": {
                                "min_index_age": "2d"
                            }
                        }
                    ]
                },
                {
                    "name": "warm",
                    "actions": [
                        {
                            "replica_count": {
                                "number_of_replicas": 0
                            }
                        }
                    ],
                    "transitions": [
                        {
                            "state_name": "delete",
                            "conditions": {
                                "min_index_age": "7d"
                            }
                        }
                    ]
                },
                {
                    "name": "delete",
                    "actions": [
                        {
                            "delete": {}
                        }
                    ],
                    "transitions": []
                }
            ]
        }
    }
    
    # Note: Uncomment if your OpenSearch version supports ISM (Index State Management)
    # client.transport.perform_request(
    #     "PUT",
    #     f"/_plugins/_ism/policies/{policy_name}",
    #     body=policy_body
    # )


# Made with Bob