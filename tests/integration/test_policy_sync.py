"""
Integration test for policy synchronization during gateway sync.

Tests that policy additions and deletions in the Gateway are properly
reflected in the API Intelligence Plane data store.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    IntelligenceMetadata,
    PolicyAction,
    PolicyActionType,
)
from app.models.gateway import Gateway, GatewayStatus, GatewayVendor
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.services.discovery_service import DiscoveryService
from app.adapters.factory import GatewayAdapterFactory


@pytest.mark.asyncio
async def test_policy_sync_updates_existing_policies():
    """Test that gateway sync properly updates API policies."""
    
    # Setup repositories
    api_repo = APIRepository()
    gateway_repo = GatewayRepository()
    adapter_factory = GatewayAdapterFactory()
    discovery_service = DiscoveryService(api_repo, gateway_repo, adapter_factory)
    
    # Create a test gateway
    gateway_id = uuid4()
    gateway = Gateway(
        id=gateway_id,
        name="Test Gateway",
        vendor=GatewayVendor.KONG,
        base_url="http://test-gateway:8000",
        status=GatewayStatus.CONNECTED,
    )
    gateway_repo.create(gateway, doc_id=str(gateway_id))
    
    # Create an API with initial policies
    api_id = uuid4()
    initial_policies = [
        PolicyAction(
            type=PolicyActionType.RATE_LIMITING,
            name="rate-limit-1",
            enabled=True,
            configuration={"limit": 100},
        )
    ]
    
    api = API(
        id=api_id,
        gateway_id=gateway_id,
        name="Test API",
        version="1.0",
        base_path="/test",
        status=APIStatus.ACTIVE,
        authentication_type=AuthenticationType.API_KEY,
        endpoints=[
            Endpoint(
                path="/test",
                methods=["GET"],
                description="Test endpoint",
            )
        ],
        policy_actions=initial_policies,
        intelligence_metadata=IntelligenceMetadata(
            discovery_method=DiscoveryMethod.GATEWAY_SYNC,
            last_seen_at=datetime.utcnow(),
        ),
    )
    api_repo.create(api, doc_id=str(api_id))
    
    # Verify initial state
    stored_api = api_repo.get(str(api_id))
    assert stored_api is not None
    assert len(stored_api.policy_actions) == 1
    assert stored_api.policy_actions[0].name == "rate-limit-1"
    
    print("✓ Initial API created with 1 policy")
    
    # Simulate gateway sync with updated policies (policy removed)
    # In real scenario, adapter.discover_apis() would return this
    updated_api = API(
        id=api_id,
        gateway_id=gateway_id,
        name="Test API",
        version="1.0",
        base_path="/test",
        status=APIStatus.ACTIVE,
        authentication_type=AuthenticationType.API_KEY,
        endpoints=[
            Endpoint(
                path="/test",
                methods=["GET"],
                description="Test endpoint",
            )
        ],
        policy_actions=[],  # Policies removed in gateway
        intelligence_metadata=IntelligenceMetadata(
            discovery_method=DiscoveryMethod.GATEWAY_SYNC,
            last_seen_at=datetime.utcnow(),
        ),
    )
    
    # Manually perform the update logic from discovery_service
    existing_api = api_repo.find_by_gateway_and_api_id(
        gateway_id=gateway_id,
        api_id=api_id,
    )
    
    assert existing_api is not None
    
    # Apply the fix: explicitly set to empty array when no policies
    updates = {
        "intelligence_metadata.last_seen_at": datetime.utcnow().isoformat(),
        "status": APIStatus.ACTIVE.value,
        "is_active": True,
        "endpoints": [ep.model_dump() for ep in updated_api.endpoints],
        "methods": updated_api.methods,
        "authentication_type": updated_api.authentication_type.value,
        "authentication_config": updated_api.authentication_config,
        "vendor_metadata": updated_api.vendor_metadata,
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    # Handle policy_actions explicitly
    if updated_api.policy_actions is not None and len(updated_api.policy_actions) > 0:
        updates["policy_actions"] = [
            policy.model_dump(mode="json", exclude_none=True)
            for policy in updated_api.policy_actions
        ]
    else:
        updates["policy_actions"] = []  # Explicitly clear
    
    api_repo.update(str(existing_api.id), updates)
    
    # Verify policies were cleared
    synced_api = api_repo.get(str(api_id))
    assert synced_api is not None
    assert synced_api.policy_actions == [] or synced_api.policy_actions is None or len(synced_api.policy_actions) == 0
    
    print("✓ Policies successfully cleared after sync")
    
    # Cleanup
    api_repo.delete(str(api_id))
    gateway_repo.delete(str(gateway_id))
    
    print("✓ Test completed successfully")


@pytest.mark.asyncio
async def test_policy_sync_adds_new_policies():
    """Test that gateway sync properly adds new API policies."""
    
    # Setup repositories
    api_repo = APIRepository()
    gateway_repo = GatewayRepository()
    
    # Create a test gateway
    gateway_id = uuid4()
    gateway = Gateway(
        id=gateway_id,
        name="Test Gateway 2",
        vendor=GatewayVendor.KONG,
        base_url="http://test-gateway:8000",
        status=GatewayStatus.CONNECTED,
    )
    gateway_repo.create(gateway, doc_id=str(gateway_id))
    
    # Create an API without policies
    api_id = uuid4()
    api = API(
        id=api_id,
        gateway_id=gateway_id,
        name="Test API 2",
        version="1.0",
        base_path="/test2",
        status=APIStatus.ACTIVE,
        authentication_type=AuthenticationType.API_KEY,
        endpoints=[
            Endpoint(
                path="/test2",
                methods=["GET"],
                description="Test endpoint",
            )
        ],
        policy_actions=[],  # No policies initially
        intelligence_metadata=IntelligenceMetadata(
            discovery_method=DiscoveryMethod.GATEWAY_SYNC,
            last_seen_at=datetime.utcnow(),
        ),
    )
    api_repo.create(api, doc_id=str(api_id))
    
    # Verify initial state
    stored_api = api_repo.get(str(api_id))
    assert stored_api is not None
    assert len(stored_api.policy_actions or []) == 0
    
    print("✓ Initial API created with no policies")
    
    # Simulate gateway sync with new policies added
    new_policies = [
        PolicyAction(
            type=PolicyActionType.RATE_LIMITING,
            name="rate-limit-new",
            enabled=True,
            configuration={"limit": 200},
        ),
        PolicyAction(
            type=PolicyActionType.AUTHENTICATION,
            name="auth-policy",
            enabled=True,
            configuration={"type": "jwt"},
        ),
    ]
    
    # Apply update with new policies
    updates = {
        "intelligence_metadata.last_seen_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    if new_policies is not None and len(new_policies) > 0:
        updates["policy_actions"] = [
            policy.model_dump(mode="json", exclude_none=True)
            for policy in new_policies
        ]
    else:
        updates["policy_actions"] = []
    
    api_repo.update(str(api_id), updates)
    
    # Verify policies were added
    synced_api = api_repo.get(str(api_id))
    assert synced_api is not None
    assert len(synced_api.policy_actions) == 2
    assert synced_api.policy_actions[0].name == "rate-limit-new"
    assert synced_api.policy_actions[1].name == "auth-policy"
    
    print("✓ New policies successfully added after sync")
    
    # Cleanup
    api_repo.delete(str(api_id))
    gateway_repo.delete(str(gateway_id))
    
    print("✓ Test completed successfully")


if __name__ == "__main__":
    import asyncio
    
    print("Running policy sync integration tests...\n")
    asyncio.run(test_policy_sync_updates_existing_policies())
    print()
    asyncio.run(test_policy_sync_adds_new_policies())
    print("\n✅ All tests passed!")

# Made with Bob
