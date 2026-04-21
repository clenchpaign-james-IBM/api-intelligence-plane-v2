"""
5-Minute Metrics Index Template Schema

Creates an index template for api-metrics-5m-* indices.
This template stores 5-minute aggregated metrics derived from 1-minute
analytics buckets for short-term operational trending.

Retention target:
- 7 days via cleanup jobs
"""

from opensearchpy import OpenSearch


def create_metrics_5m_index_template(client: OpenSearch):
    """
    Create the api-metrics-5m-* index template with mappings optimized for
    operational analytics and dashboard queries.
    """
    template_name = "api-metrics-5m-template"

    template_body = {
        "index_patterns": ["api-metrics-5m-*"],
        "template": {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "refresh_interval": "30s",
                "index": {
                    "max_result_window": 10000,
                    "codec": "best_compression",
                },
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
                    "timestamp": {"type": "date"},
                    "request_count": {"type": "long"},
                    "success_count": {"type": "long"},
                    "error_count": {"type": "long"},
                    "availability": {"type": "float"},
                    "error_rate": {"type": "float"},
                    "throughput": {"type": "float"},
                    "response_time_avg": {"type": "float"},
                    "response_time_p50": {"type": "float"},
                    "response_time_p95": {"type": "float"},
                    "response_time_p99": {"type": "float"},
                    "request_size_avg": {"type": "float"},
                    "response_size_avg": {"type": "float"},
                    "cache_hit_count": {"type": "long"},
                    "cache_miss_count": {"type": "long"},
                    "cache_hit_rate": {"type": "float"},
                    "status_code_distribution": {
                        "type": "object",
                        "enabled": True,
                    },
                    "source_index": {"type": "keyword"},
                    "metadata": {
                        "type": "object",
                        "enabled": True,
                    },
                }
            },
        },
        "priority": 122,
    }

    client.indices.put_index_template(name=template_name, body=template_body)

# Made with Bob
