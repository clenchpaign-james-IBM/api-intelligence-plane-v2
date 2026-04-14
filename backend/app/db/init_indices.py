"""
Initialize OpenSearch Indices

Creates all required indices with proper mappings on application startup.
Uses the latest schema definitions from app/db/schemas/.
"""

import logging
from opensearchpy import OpenSearch, exceptions

from app.db.schemas.schema_010_api_inventory_v2 import create_api_inventory_v2_index

logger = logging.getLogger(__name__)


def initialize_indices(client: OpenSearch) -> None:
    """
    Initialize all required OpenSearch indices.
    
    Creates indices with proper mappings if they don't exist.
    Uses the latest schema definitions.
    
    Args:
        client: OpenSearch client instance
    """
    logger.info("Initializing OpenSearch indices...")
    
    # API Inventory Index
    try:
        # Check for both possible index names
        if not client.indices.exists(index="api-inventory") and not client.indices.exists(index="api-inventory-v2"):
            logger.info("Creating api-inventory index with vendor-neutral schema...")
            create_api_inventory_v2_index(client)
            logger.info("✅ Created api-inventory index")
        else:
            logger.info("api-inventory index already exists")
    except Exception as e:
        logger.error(f"Failed to create api-inventory index: {e}")
        raise
    
    # Gateway Registry Index
    try:
        if not client.indices.exists(index="gateway-registry"):
            logger.info("Creating gateway-registry index...")
            create_gateway_registry_index(client)
            logger.info("✅ Created gateway-registry index")
        else:
            logger.info("gateway-registry index already exists")
    except Exception as e:
        logger.error(f"Failed to create gateway-registry index: {e}")
        raise
    
    logger.info("✅ All indices initialized successfully")


def create_gateway_registry_index(client: OpenSearch):
    """Create the gateway-registry index."""
    index_name = "gateway-registry"
    
    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": "5s",
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "vendor": {"type": "keyword"},
                "base_url": {"type": "keyword"},
                "transactional_logs_url": {"type": "keyword"},
                "version": {"type": "keyword"},
                "status": {"type": "keyword"},
                "capabilities": {"type": "keyword"},
                "metadata": {
                    "type": "object",
                    "enabled": True
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
