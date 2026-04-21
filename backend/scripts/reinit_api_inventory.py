"""
Reinitialize API Inventory Index

This script deletes and recreates the api-inventory index with the optimized schema
that addresses the field limit issue.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.client import get_client
from app.db.schemas.api_inventory import create_api_inventory_index


def reinit_api_inventory():
    """Reinitialize the API inventory index."""
    client = get_client()
    
    index_name = "api-inventory"
    
    # Check if index exists
    if client.indices.exists(index=index_name):
        print(f"Deleting existing index: {index_name}")
        client.indices.delete(index=index_name)
        print(f"✓ Deleted {index_name}")
    
    # Create new index with optimized schema
    print(f"Creating index with optimized schema: {index_name}")
    create_api_inventory_index(client)
    print(f"✓ Created {index_name} with field limit: 2000")
    
    # Verify index settings
    settings = client.indices.get_settings(index=index_name)
    mapping_settings = settings[index_name]['settings']['index'].get('mapping', {})
    
    print("\nIndex Settings:")
    print(f"  - Total fields limit: {mapping_settings.get('total_fields', {}).get('limit', 'default (1000)')}")
    print(f"  - Depth limit: {mapping_settings.get('depth', {}).get('limit', 'default')}")
    print(f"  - Nested fields limit: {mapping_settings.get('nested_fields', {}).get('limit', 'default')}")
    
    print("\n✓ API Inventory index reinitialized successfully!")


if __name__ == "__main__":
    reinit_api_inventory()

# Made with Bob
