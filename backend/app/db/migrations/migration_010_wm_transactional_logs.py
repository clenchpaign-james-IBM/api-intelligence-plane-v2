"""
Migration 010: WebMethods Transactional Logs Index Template

Creates an index template for transactional-logs-* daily indices.
This template stores raw transactional log events collected from supported
API gateways for drill-down analytics and troubleshooting workflows.

Retention target:
- 90 days via index lifecycle / cleanup jobs
"""

from opensearchpy import OpenSearch


def create_transactional_logs_index_template(client: OpenSearch):
    """
    Create the transactional-logs-* index template with mappings optimized
    for raw event retrieval and drill-down queries.

    This template applies to:
    - transactional-logs-2026.04.11
    - transactional-logs-2026.04.12
    - etc.
    """
    template_name = "transactional-logs-template"

    template_body = {
        "index_patterns": ["transactional-logs-*"],
        "template": {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "refresh_interval": "30s",
                "index": {
                    "max_result_window": 50000,
                    "codec": "best_compression",
                },
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "gateway_id": {"type": "keyword"},
                    "api_id": {"type": "keyword"},
                    "application_id": {"type": "keyword"},
                    "transaction_id": {"type": "keyword"},
                    "correlation_id": {"type": "keyword"},
                    "request_id": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "event_type": {"type": "keyword"},
                    "event_status": {"type": "keyword"},
                    "method": {"type": "keyword"},
                    "path": {"type": "keyword"},
                    "resource_path": {"type": "keyword"},
                    "operation_name": {"type": "keyword"},
                    "consumer_id": {"type": "keyword"},
                    "consumer_name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "status_code": {"type": "integer"},
                    "backend_status_code": {"type": "integer"},
                    "latency_ms": {"type": "float"},
                    "backend_latency_ms": {"type": "float"},
                    "total_time_ms": {"type": "float"},
                    "request_size_bytes": {"type": "long"},
                    "response_size_bytes": {"type": "long"},
                    "cache_status": {"type": "keyword"},
                    "error_origin": {"type": "keyword"},
                    "error_message": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 1024}},
                    },
                    "client_ip": {"type": "ip"},
                    "protocol": {"type": "keyword"},
                    "host": {"type": "keyword"},
                    "user_agent": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword", "ignore_above": 1024}},
                    },
                    "region": {"type": "keyword"},
                    "environment": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "external_calls": {
                        "type": "nested",
                        "properties": {
                            "call_type": {"type": "keyword"},
                            "target_service": {"type": "keyword"},
                            "target_endpoint": {"type": "keyword"},
                            "duration_ms": {"type": "float"},
                            "status_code": {"type": "integer"},
                            "success": {"type": "boolean"},
                            "error_message": {
                                "type": "text",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword",
                                        "ignore_above": 1024,
                                    }
                                },
                            },
                        },
                    },
                    "metadata": {
                        "type": "object",
                        "enabled": True,
                    },
                }
            },
        },
        "priority": 120,
    }

    client.indices.put_index_template(name=template_name, body=template_body)

# Made with Bob
