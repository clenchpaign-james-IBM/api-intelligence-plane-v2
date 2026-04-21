"""Debug API Search"""

import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.client import get_client
from app.db.repositories.api_repository import APIRepository
from app.models.base.api import (
    API,
    APIType,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    IntelligenceMetadata,
    VersionInfo,
)

# Create test API
repo = APIRepository()
gateway_id = uuid4()
api_id = uuid4()

api = API(
    id=api_id,
    gateway_id=gateway_id,
    name="Debug Test API",
    base_path="/debug",
    endpoints=[Endpoint(path="/debug", method="GET", description="Test")],
    methods=["GET"],
    authentication_type=AuthenticationType.NONE,
    version_info=VersionInfo(current_version="1.0.0"),
    intelligence_metadata=IntelligenceMetadata(
        is_shadow=False,
        discovery_method=DiscoveryMethod.GATEWAY_SYNC,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        health_score=100.0,
    ),
)

print(f"Creating API with gateway_id={gateway_id}, api_id={api_id}")
created = repo.create(api, doc_id=str(api_id))
print(f"Created: {created.id}")

# Get the raw document from OpenSearch
client = get_client()
doc = client.get(index="api-inventory", id=str(api_id))
print(f"\nRaw document from OpenSearch:")
print(f"  _id: {doc['_id']}")
print(f"  _source.id: {doc['_source'].get('id')}")
print(f"  _source.gateway_id: {doc['_source'].get('gateway_id')}")

# Try to search
print(f"\nSearching with gateway_id={gateway_id}, api_id={api_id}")
found = repo.find_by_gateway_and_api_id(gateway_id, api_id)
if found:
    print(f"✓ Found: {found.name}")
else:
    print("✗ Not found")
    
    # Try manual search
    print("\nTrying manual search...")
    query = {
        "bool": {
            "must": [
                {"term": {"gateway_id": str(gateway_id)}},
                {"term": {"id": str(api_id)}}
            ]
        }
    }
    result = client.search(index="api-inventory", body={"query": query})
    print(f"Manual search hits: {result['hits']['total']['value']}")
    if result['hits']['hits']:
        for hit in result['hits']['hits']:
            print(f"  Hit _id: {hit['_id']}")
            print(f"  Hit _source.id: {hit['_source'].get('id')}")
            print(f"  Hit _source.gateway_id: {hit['_source'].get('gateway_id')}")

# Cleanup
repo.delete(str(api_id))
print("\n✓ Cleanup complete")

# Made with Bob
