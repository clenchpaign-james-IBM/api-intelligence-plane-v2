"""
Schema: API Metrics Index Template

Creates an index template for api-metrics-* indices with monthly rotation.
Time-series metrics data for API performance monitoring.
"""

from opensearchpy import OpenSearch


def create_api_metrics_index_template(client: OpenSearch):
    """
    Create the api-metrics-* index template with appropriate mappings.
    
    This template applies to:
    - api-metrics-2026.03 (March 2026)
    - api-metrics-2026.04 (April 2026)
    - etc.
    
    Stores:
    - Time-series performance metrics
    - Response time percentiles (p50, p95, p99)
    - Error rates and counts
    - Throughput and availability
    - Status code distributions
    - Per-endpoint metrics breakdowns
    """
    
    template_name = "api-metrics-template"
    
    template_body = {
        "index_patterns": ["api-metrics-*"],
        "template": {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "refresh_interval": "30s",
                "index": {
                    "max_result_window": 10000,
                    "codec": "best_compression",  # Compress time-series data
                },
            },
            "mappings": {
                "properties": {
                    "id": {
                        "type": "keyword",
                    },
                    "api_id": {
                        "type": "keyword",
                    },
                    "gateway_id": {
                        "type": "keyword",
                    },
                    "timestamp": {
                        "type": "date",
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
                    "error_rate": {
                        "type": "float",
                    },
                    "error_count": {
                        "type": "integer",
                    },
                    "request_count": {
                        "type": "integer",
                    },
                    "throughput": {
                        "type": "float",
                    },
                    "availability": {
                        "type": "float",
                    },
                    "status_codes": {
                        "type": "object",
                        "enabled": True,
                    },
                    "endpoint_metrics": {
                        "type": "nested",
                        "properties": {
                            "endpoint": {"type": "keyword"},
                            "method": {"type": "keyword"},
                            "response_time_avg": {"type": "float"},
                            "error_rate": {"type": "float"},
                            "request_count": {"type": "integer"},
                        },
                    },
                    "metadata": {
                        "type": "object",
                        "enabled": True,
                    },
                }
            },
        },
        "priority": 100,
    }
    
    client.indices.put_index_template(name=template_name, body=template_body)

# Made with Bob
