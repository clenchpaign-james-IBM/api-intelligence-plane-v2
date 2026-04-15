"""
Schema: Gateway Registry Index

Creates the gateway-registry index for storing connected API Gateway configurations,
connection details, and capabilities.
"""

from opensearchpy import OpenSearch


def create_gateway_registry_index(client: OpenSearch):
    """
    Create the gateway-registry index with appropriate mappings.
    
    This index stores:
    - Connected API Gateway configurations
    - Vendor information and versions
    - Connection details and credentials (encrypted)
    - Gateway capabilities and features
    - Connection status and health
    """
    
    index_name = "gateway-registry"
    
    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": "10s",
        },
        "mappings": {
            "properties": {
                "id": {
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
                "vendor": {
                    "type": "keyword",
                },
                "version": {
                    "type": "keyword",
                },
                "connection_url": {
                    "type": "keyword",
                },
                "connection_type": {
                    "type": "keyword",
                },
                "credentials": {
                    "type": "object",
                    "enabled": False,  # Don't index sensitive credentials
                },
                "capabilities": {
                    "type": "keyword",
                },
                "status": {
                    "type": "keyword",
                },
                "last_connected_at": {
                    "type": "date",
                },
                "last_error": {
                    "type": "text",
                },
                "api_count": {
                    "type": "integer",
                },
                "metrics_enabled": {
                    "type": "boolean",
                },
                "security_scanning_enabled": {
                    "type": "boolean",
                },
                "rate_limiting_enabled": {
                    "type": "boolean",
                },
                "configuration": {
                    "type": "object",
                    "enabled": True,
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
