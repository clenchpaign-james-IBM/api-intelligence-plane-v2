"""
Migration 014: WebMethods 1-Day Metrics Index Template

Creates an index template for api-metrics-1d-* indices.
This template stores 1-day aggregated metrics derived from 1-hour
analytics buckets for long-term reporting and trend analysis.

Retention target:
- 90 days via cleanup jobs
"""

from opensearchpy import OpenSearch


def create_wm_metrics_1d_index_template(client: OpenSearch):
    """
    Create the api-metrics-1d-* index template with mappings optimized for
    daily summaries, reporting, and longer-term trend exploration.
    """
    template_name = "api-metrics-1d-template"

    template_body = {
        "index_patterns": ["api-metrics-1d-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": "300s",
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
        "priority": 124,
    }

    client.indices.put_index_template(name=template_name, body=template_body)

# Made with Bob
