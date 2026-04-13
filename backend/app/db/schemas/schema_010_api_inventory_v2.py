"""
Migration 010: API Inventory V2 - Vendor-Neutral Structure

Updates the api-inventory index to support vendor-neutral architecture with:
- api_definition nested object for OpenAPI/Swagger specs
- policy_actions nested array for vendor-neutral policies
- intelligence_metadata object for AI-derived fields
- vendor_metadata object for vendor-specific extensions
- Removes current_metrics (now stored separately in time-bucketed indices)
"""

from opensearchpy import OpenSearch


def create_api_inventory_v2_index(client: OpenSearch):
    """
    Create the api-inventory-v2 index with vendor-neutral mappings.
    
    This index stores:
    - Vendor-neutral API metadata (name, version, endpoints)
    - API definitions (OpenAPI/Swagger specifications)
    - Policy actions (vendor-neutral with vendor_config extensions)
    - Intelligence metadata (health_score, risk_score, is_shadow, etc.)
    - Vendor-specific metadata (stored in vendor_metadata object)
    - Ownership, publishing, and deployment information
    
    Note: Metrics are now stored separately in time-bucketed indices
    """
    
    index_name = "api-inventory-v2"
    
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
                # ============================================================
                # Core Identification
                # ============================================================
                "id": {
                    "type": "keyword",
                },
                "gateway_id": {
                    "type": "keyword",
                },
                
                # ============================================================
                # Basic Metadata
                # ============================================================
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256,
                        }
                    },
                },
                "display_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256,
                        }
                    },
                },
                "description": {
                    "type": "text",
                },
                "icon": {
                    "type": "keyword",
                },
                
                # ============================================================
                # Versioning
                # ============================================================
                "version_info": {
                    "type": "object",
                    "properties": {
                        "current_version": {"type": "keyword"},
                        "previous_version": {"type": "keyword"},
                        "next_version": {"type": "keyword"},
                        "system_version": {"type": "integer"},
                        "version_history": {"type": "keyword"},
                    },
                },
                
                # ============================================================
                # Type and Classification
                # ============================================================
                "type": {
                    "type": "keyword",
                },
                "maturity_state": {
                    "type": "keyword",
                },
                "groups": {
                    "type": "keyword",
                },
                "tags": {
                    "type": "keyword",
                },
                
                # ============================================================
                # Base Path
                # ============================================================
                "base_path": {
                    "type": "keyword",
                },
                
                # ============================================================
                # API Definition (OpenAPI/Swagger)
                # ============================================================
                "api_definition": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "keyword"},
                        "version": {"type": "keyword"},
                        "openapi_spec": {
                            "type": "object",
                            "enabled": True,
                        },
                        "swagger_version": {"type": "keyword"},
                        "base_path": {"type": "keyword"},
                        "paths": {
                            "type": "object",
                            "enabled": True,
                        },
                        "schemas": {
                            "type": "object",
                            "enabled": True,
                        },
                        "security_schemes": {
                            "type": "object",
                            "enabled": True,
                        },
                        "vendor_extensions": {
                            "type": "object",
                            "enabled": True,
                        },
                    },
                },
                
                # ============================================================
                # Endpoints
                # ============================================================
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
                                "description": {"type": "text"},
                            },
                        },
                        "response_codes": {"type": "integer"},
                        "connection_timeout": {"type": "integer"},
                        "read_timeout": {"type": "integer"},
                    },
                },
                "methods": {
                    "type": "keyword",
                },
                
                # ============================================================
                # Authentication
                # ============================================================
                "authentication_type": {
                    "type": "keyword",
                },
                "authentication_config": {
                    "type": "object",
                    "enabled": False,  # Don't index sensitive auth data
                },
                
                # ============================================================
                # Policy Actions (Vendor-Neutral)
                # ============================================================
                "policy_actions": {
                    "type": "nested",
                    "properties": {
                        "action_type": {"type": "keyword"},
                        "enabled": {"type": "boolean"},
                        "stage": {"type": "keyword"},
                        "config": {
                            "type": "object",
                            "enabled": True,
                        },
                        "vendor_config": {
                            "type": "object",
                            "enabled": True,
                        },
                        "name": {"type": "keyword"},
                        "description": {"type": "text"},
                    },
                },
                
                # ============================================================
                # Ownership
                # ============================================================
                "ownership": {
                    "type": "object",
                    "properties": {
                        "team": {"type": "keyword"},
                        "contact": {"type": "keyword"},
                        "repository": {"type": "keyword"},
                        "organization": {"type": "keyword"},
                        "department": {"type": "keyword"},
                    },
                },
                
                # ============================================================
                # Publishing and Deployment
                # ============================================================
                "publishing": {
                    "type": "object",
                    "properties": {
                        "published_portals": {"type": "keyword"},
                        "published_to_registry": {"type": "boolean"},
                        "catalog_name": {"type": "keyword"},
                        "catalog_id": {"type": "keyword"},
                    },
                },
                "deployments": {
                    "type": "nested",
                    "properties": {
                        "environment": {"type": "keyword"},
                        "gateway_endpoints": {
                            "type": "object",
                            "enabled": True,
                        },
                        "deployed_at": {"type": "date"},
                        "deployment_status": {"type": "keyword"},
                    },
                },
                
                # ============================================================
                # Intelligence Metadata (AI-Derived Fields)
                # ============================================================
                "intelligence_metadata": {
                    "type": "object",
                    "properties": {
                        # Discovery
                        "is_shadow": {"type": "boolean"},
                        "discovery_method": {"type": "keyword"},
                        "discovered_at": {"type": "date"},
                        "last_seen_at": {"type": "date"},
                        
                        # Health and performance
                        "health_score": {"type": "float"},
                        
                        # Risk assessment
                        "risk_score": {"type": "float"},
                        "security_score": {"type": "float"},
                        
                        # Compliance
                        "compliance_status": {
                            "type": "object",
                            "enabled": True,
                        },
                        
                        # Usage patterns
                        "usage_trend": {"type": "keyword"},
                        
                        # Predictions
                        "has_active_predictions": {"type": "boolean"},
                    },
                },
                
                # ============================================================
                # Status
                # ============================================================
                "status": {
                    "type": "keyword",
                },
                "is_active": {
                    "type": "boolean",
                },
                
                # ============================================================
                # Vendor-Specific Extensions
                # ============================================================
                "vendor_metadata": {
                    "type": "object",
                    "enabled": True,  # Allow arbitrary vendor-specific fields
                },
                
                # ============================================================
                # Timestamps
                # ============================================================
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


def migrate_data_from_v1_to_v2(client: OpenSearch):
    """
    Migrate data from api-inventory (v1) to api-inventory-v2.
    
    This function:
    1. Reads all documents from api-inventory
    2. Transforms them to the new structure
    3. Writes them to api-inventory-v2
    
    Note: This is a data migration helper. The actual migration strategy
    (reindex, dual-write, etc.) should be determined based on production needs.
    """
    # TODO: Implement data migration logic
    # This would typically involve:
    # 1. Scroll through all documents in api-inventory
    # 2. Transform each document:
    #    - Move is_shadow, discovery_method, discovered_at, last_seen_at, health_score
    #      into intelligence_metadata object
    #    - Remove current_metrics (now stored separately)
    #    - Add empty policy_actions array if not present
    #    - Add empty vendor_metadata object if not present
    # 3. Bulk index into api-inventory-v2
    pass


# Made with Bob