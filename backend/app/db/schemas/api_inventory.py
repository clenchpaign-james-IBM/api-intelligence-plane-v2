"""
API Inventory Index Schema

Creates the api-inventory index for storing discovered APIs with their metadata,
health metrics, and current status.
"""

from opensearchpy import OpenSearch


def create_api_inventory_index(client: OpenSearch):
    """
    Create the api-inventory index with appropriate mappings.
    
    This index stores:
    - Discovered APIs from all connected Gateways
    - API metadata (name, version, endpoints, authentication)
    - Current health metrics snapshot
    - Discovery information (method, timestamps)
    - Shadow API detection flags
    """
    
    index_name = "api-inventory"
    
    index_body = {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "refresh_interval": "5s",
            "index": {
                "max_result_window": 10000,
            },
        },
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword",
                },
                "gateway_id": {
                    "type": "keyword",
                },
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256,
                        }
                    },
                },
                "version": {
                    "type": "keyword",
                },
                "base_path": {
                    "type": "keyword",
                },
                "endpoints": {
                    "type": "nested",
                    "properties": {
                        "path": {"type": "keyword"},
                        "method": {"type": "keyword"},
                        "description": {"type": "text"},
                        "parameters": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "type": {"type": "keyword"},
                                "data_type": {"type": "keyword"},
                                "required": {"type": "boolean"},
                            },
                        },
                        "response_codes": {"type": "integer"},
                    },
                },
                "methods": {
                    "type": "keyword",
                },
                "authentication_type": {
                    "type": "keyword",
                },
                "authentication_config": {
                    "type": "object",
                    "enabled": False,  # Don't index sensitive auth data
                },
                "ownership": {
                    "type": "object",
                    "properties": {
                        "team": {"type": "keyword"},
                        "contact": {"type": "keyword"},
                        "repository": {"type": "keyword"},
                    },
                },
                "tags": {
                    "type": "keyword",
                },
                "is_shadow": {
                    "type": "boolean",
                },
                "discovery_method": {
                    "type": "keyword",
                },
                "discovered_at": {
                    "type": "date",
                },
                "last_seen_at": {
                    "type": "date",
                },
                "status": {
                    "type": "keyword",
                },
                "health_score": {
                    "type": "float",
                },
                "current_metrics": {
                    "type": "object",
                    "properties": {
                        "response_time_p50": {"type": "float"},
                        "response_time_p95": {"type": "float"},
                        "response_time_p99": {"type": "float"},
                        "error_rate": {"type": "float"},
                        "throughput": {"type": "float"},
                        "availability": {"type": "float"},
                        "last_error": {"type": "date"},
                        "measured_at": {"type": "date"},
                    },
                },
                "metadata": {
                    "type": "object",
                    "enabled": True,
                },
                "created_at": {
                    "type": "date",
                },
                "updated_at": {
                    "type": "date",
                },
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
