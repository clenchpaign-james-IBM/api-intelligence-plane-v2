"""
Migration 010: WebMethods Transactional Logs Index Template

Creates the transactional logs index template for storing raw transactional
events collected from gateway adapters. Indices are created daily and retain
90 days of data to support drill-down from aggregated metrics.
"""

from opensearchpy import OpenSearch


INDEX_TEMPLATE_NAME = "transactional-logs-template"
INDEX_PATTERN = "transactional-logs-*"


def create_transactional_logs_index_template(client: OpenSearch) -> None:
    """Create the transactional logs index template with daily index pattern."""

    template_body = {
        "index_patterns": [INDEX_PATTERN],
        "template": {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "refresh_interval": "30s",
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "gateway_id": {"type": "keyword"},
                    "api_id": {"type": "keyword"},
                    "application_id": {"type": "keyword"},
                    "event_type": {"type": "keyword"},
                    "event_status": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "request_method": {"type": "keyword"},
                    "request_path": {"type": "keyword"},
                    "request_uri": {"type": "keyword"},
                    "consumer_id": {"type": "keyword"},
                    "consumer_name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                    },
                    "client_ip": {"type": "ip"},
                    "http_status_code": {"type": "integer"},
                    "total_duration_ms": {"type": "float"},
                    "gateway_duration_ms": {"type": "float"},
                    "backend_duration_ms": {"type": "float"},
                    "cache_status": {"type": "keyword"},
                    "cache_hit": {"type": "boolean"},
                    "cache_key": {"type": "keyword"},
                    "request_size_bytes": {"type": "long"},
                    "response_size_bytes": {"type": "long"},
                    "error_origin": {"type": "keyword"},
                    "error_message": {"type": "text"},
                    "error_code": {"type": "keyword"},
                    "backend_service_name": {"type": "keyword"},
                    "backend_url": {"type": "keyword"},
                    "region": {"type": "keyword"},
                    "environment": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "external_calls": {
                        "type": "nested",
                        "properties": {
                            "service_name": {"type": "keyword"},
                            "call_type": {"type": "keyword"},
                            "duration_ms": {"type": "float"},
                            "status_code": {"type": "integer"},
                            "target": {"type": "keyword"},
                            "success": {"type": "boolean"},
                        },
                    },
                    "vendor_metadata": {"type": "object", "enabled": True},
                    "created_at": {"type": "date"},
                }
            },
        },
        "_meta": {
            "description": "Daily raw transactional log events for WebMethods analytics",
            "retention": "90d",
        },
    }

    client.indices.put_index_template(name=INDEX_TEMPLATE_NAME, body=template_body)


# Made with Bob