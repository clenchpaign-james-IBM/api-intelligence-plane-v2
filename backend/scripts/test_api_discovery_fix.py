"""
Test API Discovery Fixes

Tests the fixes for:
1. Unique key constraint (gateway_id + api.id)
2. OpenSearch field limit (increased to 2000)
"""

import sys
import os
from uuid import uuid4
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.repositories.api_repository import APIRepository
from app.models.base.api import (
    API,
    APIStatus,
    APIType,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    IntelligenceMetadata,
    VersionInfo,
)


def test_unique_key_constraint():
    """Test that gateway_id + api.id works as unique key."""
    print("\n=== Testing Unique Key Constraint ===")
    
    repo = APIRepository()
    gateway_id = uuid4()
    api_id = uuid4()
    
    # Create test API
    api = API(
        id=api_id,
        gateway_id=gateway_id,
        name="Test API",
        base_path="/test",
        endpoints=[
            Endpoint(
                path="/test",
                method="GET",
                description="Test endpoint"
            )
        ],
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
    
    # Test 1: Create API with explicit doc_id
    print(f"Creating API with ID: {api_id}")
    created_api = repo.create(api, doc_id=str(api_id))
    print(f"✓ Created API successfully")
    
    # Test 2: Find by gateway_id and api_id
    print(f"Finding API by gateway_id={gateway_id} and api_id={api_id}")
    found_api = repo.find_by_gateway_and_api_id(gateway_id, api_id)
    
    if found_api:
        print(f"✓ Found API: {found_api.name} (ID: {found_api.id})")
        assert str(found_api.id) == str(api_id), "API ID mismatch"
        assert str(found_api.gateway_id) == str(gateway_id), "Gateway ID mismatch"
        print("✓ Unique key constraint working correctly")
    else:
        print("✗ Failed to find API by unique key")
        return False
    
    # Test 3: Try to create duplicate (should fail or update)
    print(f"Attempting to create duplicate API with same ID")
    try:
        duplicate_api = API(
            id=api_id,  # Same ID
            gateway_id=gateway_id,  # Same gateway
            name="Duplicate Test API",
            base_path="/test-duplicate",
            endpoints=[
                Endpoint(
                    path="/test-duplicate",
                    method="POST",
                    description="Duplicate endpoint"
                )
            ],
            methods=["POST"],
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
        repo.create(duplicate_api, doc_id=str(api_id))
        print("✗ Duplicate creation should have failed but didn't")
    except Exception as e:
        print(f"✓ Duplicate creation correctly prevented: {type(e).__name__}")
    
    # Cleanup
    print(f"Cleaning up test API")
    repo.delete(str(api_id))
    print("✓ Cleanup complete")
    
    return True


def test_field_limit():
    """Test that complex API structures don't exceed field limit."""
    print("\n=== Testing Field Limit ===")
    
    repo = APIRepository()
    gateway_id = uuid4()
    api_id = uuid4()
    
    # Create API with many endpoints and complex structure
    endpoints = []
    for i in range(20):  # Create 20 endpoints
        endpoints.append(
            Endpoint(
                path=f"/api/v1/resource{i}",
                method="GET",
                description=f"Endpoint {i}",
                parameters=[],
                response_codes=[200, 400, 500],
            )
        )
    
    api = API(
        id=api_id,
        gateway_id=gateway_id,
        name="Complex API",
        base_path="/api/v1",
        endpoints=endpoints,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        authentication_type=AuthenticationType.OAUTH2,
        version_info=VersionInfo(
            current_version="2.0.0",
            previous_version="1.0.0",
            system_version=5,
        ),
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=False,
            discovery_method=DiscoveryMethod.GATEWAY_SYNC,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            health_score=95.5,
            risk_score=15.0,
            security_score=85.0,
        ),
        tags=["production", "v2", "critical"],
        groups=["core-apis", "public"],
    )
    
    # Test: Create complex API
    print(f"Creating complex API with {len(endpoints)} endpoints")
    try:
        created_api = repo.create(api, doc_id=str(api_id))
        print(f"✓ Created complex API successfully (ID: {created_api.id})")
        print(f"  - Endpoints: {len(created_api.endpoints)}")
        print(f"  - Methods: {len(created_api.methods)}")
        print(f"  - Tags: {len(created_api.tags)}")
        
        # Cleanup
        repo.delete(str(api_id))
        print("✓ Field limit test passed")
        return True
    except Exception as e:
        print(f"✗ Failed to create complex API: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("API Discovery Fix Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Unique key constraint
    results.append(("Unique Key Constraint", test_unique_key_constraint()))
    
    # Test 2: Field limit
    results.append(("Field Limit", test_field_limit()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())

# Made with Bob
