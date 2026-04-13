"""
Migration 011: WebMethods Metrics 1m Index Template

Creates the 1-minute metrics index template used for ultra real-time
aggregation. Intended retention is 24 hours.
"""

from opensearchpy import OpenSearch


INDEX_TEMPLATE_NAME = "metrics-1m-template"
INDEX_PATTERN = "metrics-1m-*"


def create_metrics_1m_index_template(client: OpenSearch) -> None:
    """Create the 1-minute metrics index template."""

    template_body = {
        "index_patterns": [INDEX_PATTERN],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": "15s",
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "gateway_id": {"type": "keyword"},
                    "api_id": {"type": "keyword"},
                    "application_id": {"type": "keyword"},
                    "time_bucket": {"type": "keyword"},
                    "bucket_start": {"type": "date"},
                    "bucket_end": {"type": "date"},
                    "request_count": {"type": "long"},
                    "error_count": {"type": "long"},
                    "error_rate": {"type": "float"},
                    "throughput": {"type": "float"},
                    "availability": {"type": "float"},
                    "response_time_p50": {"type": "float"},
                    "response_time_p95": {"type": "float"},
                    "response_time_p99": {"type": "float"},
                    "gateway_time_avg": {"type": "float"},
                    "backend_time_avg": {"type": "float"},
                    "cache_hit_count": {"type": "long"},
                    "cache_miss_count": {"type": "long"},
                    "cache_bypass_count": {"type": "long"},
                    "cache_hit_rate": {"type": "float"},
                    "status_codes": {"type": "object", "enabled": True},
                    "metadata": {"type": "object", "enabled": True},
                    "created_at": {"type": "date"},
                }
            },
        },
        "_meta": {
            "description": "1-minute aggregated metrics for WebMethods analytics",
            "retention": "24h",
        },
    }

    client.indices.put_index_template(name=INDEX_TEMPLATE_NAME, body=template_body)


# Made with Bob