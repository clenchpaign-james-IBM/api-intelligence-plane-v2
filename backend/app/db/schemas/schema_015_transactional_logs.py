"""
Index Schema 015: Transactional Logs Index Template

Creates an index template for api-transactional-logs-* indices with monthly rotation.
Raw transactional event data for drill-down analysis and debugging.

Retention: 7 days (configurable via ILM policy)
"""

from opensearchpy import OpenSearch


def create_transactional_logs_index_template(client: OpenSearch):
    """
    Create the api-transactional-logs-* index template with appropriate mappings.
    
    This template applies to:
    - api-transactional-logs-2026.03 (March 2026)
    - api-transactional-logs-2026.04 (April 2026)
    - etc.
    
    Stores:
    - Raw transactional events from API gateways
    - Complete request/response details
    - Timing breakdown (gateway, backend, total)
    - Client information and tracking IDs
    - Caching status and backend service details
    - Error information and external calls
    - Vendor-specific extensions
    
    Retention Policy:
    - Keep for 7 days for drill-down analysis
    - Aggregate to 1-minute metrics for longer retention
    - Delete raw logs after 7 days to save storage
    """
    
    template_name = "api-transactional-logs-template"
    
    template_body = {
        "index_patterns": ["api-transactional-logs-*"],
        "template": {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "refresh_interval": "5s",  # Fast refresh for real-time drill-down
                "index": {
                    "max_result_window": 10000,
                    "codec": "best_compression",  # Compress large payloads
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
                    "event_type": {
                        "type": "keyword",
                    },
                    "timestamp": {
                        "type": "date",
                        "format": "epoch_millis",
                    },
                    
                    # ========================================================
                    # API Identification
                    # ========================================================
                    "api_id": {
                        "type": "keyword",
                    },
                    "api_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256,
                            }
                        },
                    },
                    "api_version": {
                        "type": "keyword",
                    },
                    "operation": {
                        "type": "keyword",
                    },
                    
                    # ========================================================
                    # Request Details
                    # ========================================================
                    "http_method": {
                        "type": "keyword",
                    },
                    "request_path": {
                        "type": "keyword",
                    },
                    "request_headers": {
                        "type": "object",
                        "enabled": True,
                    },
                    "request_payload": {
                        "type": "text",
                        "index": False,  # Don't index large payloads
                    },
                    "request_size": {
                        "type": "integer",
                    },
                    "query_parameters": {
                        "type": "object",
                        "enabled": True,
                    },
                    
                    # ========================================================
                    # Response Details
                    # ========================================================
                    "status_code": {
                        "type": "integer",
                    },
                    "response_headers": {
                        "type": "object",
                        "enabled": True,
                    },
                    "response_payload": {
                        "type": "text",
                        "index": False,  # Don't index large payloads
                    },
                    "response_size": {
                        "type": "integer",
                    },
                    
                    # ========================================================
                    # Client Information
                    # ========================================================
                    "client_id": {
                        "type": "keyword",
                    },
                    "client_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256,
                            }
                        },
                    },
                    "client_ip": {
                        "type": "ip",
                    },
                    "user_agent": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 512,
                            }
                        },
                    },
                    
                    # ========================================================
                    # Timing Metrics (milliseconds)
                    # ========================================================
                    "total_time_ms": {
                        "type": "integer",
                    },
                    "gateway_time_ms": {
                        "type": "integer",
                    },
                    "backend_time_ms": {
                        "type": "integer",
                    },
                    
                    # ========================================================
                    # Status and Tracking
                    # ========================================================
                    "status": {
                        "type": "keyword",
                    },
                    "correlation_id": {
                        "type": "keyword",
                    },
                    "session_id": {
                        "type": "keyword",
                    },
                    "trace_id": {
                        "type": "keyword",
                    },
                    
                    # ========================================================
                    # Caching
                    # ========================================================
                    "cache_status": {
                        "type": "keyword",
                    },
                    
                    # ========================================================
                    # Backend Service Details
                    # ========================================================
                    "backend_url": {
                        "type": "keyword",
                    },
                    "backend_method": {
                        "type": "keyword",
                    },
                    "backend_request_headers": {
                        "type": "object",
                        "enabled": True,
                    },
                    "backend_response_headers": {
                        "type": "object",
                        "enabled": True,
                    },
                    
                    # ========================================================
                    # Error Information
                    # ========================================================
                    "error_origin": {
                        "type": "keyword",
                    },
                    "error_message": {
                        "type": "text",
                    },
                    "error_code": {
                        "type": "keyword",
                    },
                    
                    # ========================================================
                    # External Calls
                    # ========================================================
                    "external_calls": {
                        "type": "nested",
                        "properties": {
                            "call_type": {"type": "keyword"},
                            "url": {"type": "keyword"},
                            "method": {"type": "keyword"},
                            "start_time": {"type": "long"},
                            "end_time": {"type": "long"},
                            "duration_ms": {"type": "integer"},
                            "status_code": {"type": "integer"},
                            "success": {"type": "boolean"},
                            "request_size": {"type": "integer"},
                            "response_size": {"type": "integer"},
                            "error_message": {"type": "text"},
                        },
                    },
                    
                    # ========================================================
                    # Gateway Information
                    # ========================================================
                    "gateway_id": {
                        "type": "keyword",
                    },
                    "gateway_node": {
                        "type": "keyword",
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
                }
            },
        },
        "priority": 200,  # Higher priority than generic api-transactional-* template
    }
    
    client.indices.put_index_template(name=template_name, body=template_body)


def create_transactional_logs_ilm_policy(client: OpenSearch):
    """
    Create ILM (Index Lifecycle Management) policy for transactional logs.
    
    Policy:
    - Hot phase: Keep for 2 days with fast refresh
    - Warm phase: Move to warm nodes after 2 days
    - Delete phase: Delete after 7 days
    
    Note: This is optional and depends on OpenSearch ILM support.
    For basic deployments, manual cleanup scripts can be used instead.
    """
    policy_name = "api-transactional-logs-policy"
    
    # Note: OpenSearch ILM syntax may differ from Elasticsearch
    # This is a conceptual example - adjust based on your OpenSearch version
    policy_body = {
        "policy": {
            "description": "ILM policy for transactional logs indices",
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