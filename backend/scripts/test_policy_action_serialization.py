"""
Test PolicyAction Serialization/Deserialization

Tests that APIs with PolicyActions containing structured configs can be:
1. Created in OpenSearch
2. Retrieved from OpenSearch
3. Properly reconstructed with nested Pydantic models
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
    PolicyAction,
    PolicyActionType,
)
from app.models.base.policy_configs import (
    RateLimitConfig,
    AuthenticationConfig,
    CachingConfig,
)


def test_api_with_policy_actions():
    """Test creating and retrieving API with PolicyActions containing structured configs."""
    print("\n=== Testing API with PolicyActions ===")
    
    repo = APIRepository()
    gateway_id = uuid4()
    api_id = uuid4()
    
    # Create API with multiple policy actions using structured configs
    api = API(
        id=api_id,
        gateway_id=gateway_id,
        name="Test API with Policies",
        base_path="/test-policies",
        endpoints=[
            Endpoint(
                path="/test-policies",
                method="GET",
                description="Test endpoint with policies"
            )
        ],
        methods=["GET"],
        authentication_type=AuthenticationType.OAUTH2,
        version_info=VersionInfo(current_version="1.0.0"),
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=False,
            discovery_method=DiscoveryMethod.GATEWAY_SYNC,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            health_score=100.0,
        ),
        policy_actions=[
            PolicyAction(
                action_type=PolicyActionType.RATE_LIMITING,
                enabled=True,
                stage="request",
                config=RateLimitConfig(
                    requests_per_minute=1000,
                    burst_allowance=100,
                    rate_limit_key="api_key",
                    enforcement_action="reject",
                    include_rate_limit_headers=True,
                ),
                name="Rate Limit Policy",
                description="Limit requests to 1000/min",
            ),
            PolicyAction(
                action_type=PolicyActionType.AUTHENTICATION,
                enabled=True,
                stage="request",
                config=AuthenticationConfig(
                    auth_type="oauth2",
                    oauth_provider="auth0",
                    oauth_scopes=["read:api", "write:api"],
                    token_validation_endpoint="https://auth0.example.com/validate",
                ),
                name="OAuth2 Authentication",
                description="Validate OAuth2 tokens",
            ),
            PolicyAction(
                action_type=PolicyActionType.CACHING,
                enabled=True,
                stage="response",
                config=CachingConfig(
                    ttl_seconds=300,
                    cache_key_strategy="url_query",
                    cache_methods=["GET"],
                    cache_status_codes=[200, 304],
                ),
                name="Response Caching",
                description="Cache GET responses for 5 minutes",
            ),
        ],
    )
    
    print(f"Creating API with {len(api.policy_actions)} policy actions")
    print(f"  - Rate Limiting: {api.policy_actions[0].config.requests_per_minute} req/min")
    print(f"  - Authentication: {api.policy_actions[1].config.auth_type}")
    print(f"  - Caching: {api.policy_actions[2].config.ttl_seconds}s TTL")
    
    # Create API
    try:
        created_api = repo.create(api, doc_id=str(api_id))
        print(f"✓ Created API successfully (ID: {created_api.id})")
    except Exception as e:
        print(f"✗ Failed to create API: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Retrieve API
    print(f"\nRetrieving API by ID: {api_id}")
    try:
        retrieved_api = repo.get(str(api_id))
        if not retrieved_api:
            print("✗ Failed to retrieve API")
            return False
        
        print(f"✓ Retrieved API: {retrieved_api.name}")
        
        # Verify policy actions
        if not retrieved_api.policy_actions:
            print("✗ No policy actions found in retrieved API")
            return False
        
        print(f"✓ Found {len(retrieved_api.policy_actions)} policy actions")
        
        # Verify structured configs are properly reconstructed
        for i, policy in enumerate(retrieved_api.policy_actions):
            print(f"\nPolicy {i+1}: {policy.name}")
            print(f"  - Type: {policy.action_type}")
            print(f"  - Config Type: {type(policy.config).__name__}")
            
            # Verify config is the correct type, not a dict
            if isinstance(policy.config, dict):
                print(f"  ✗ Config is a dict, should be a Pydantic model!")
                return False
            
            # Verify specific config fields
            if policy.action_type == PolicyActionType.RATE_LIMITING:
                assert isinstance(policy.config, RateLimitConfig)
                print(f"  ✓ RateLimitConfig: {policy.config.requests_per_minute} req/min")
                assert policy.config.requests_per_minute == 1000
                assert policy.config.burst_allowance == 100
                
            elif policy.action_type == PolicyActionType.AUTHENTICATION:
                assert isinstance(policy.config, AuthenticationConfig)
                print(f"  ✓ AuthenticationConfig: {policy.config.auth_type}")
                assert policy.config.auth_type == "oauth2"
                assert policy.config.oauth_provider == "auth0"
                
            elif policy.action_type == PolicyActionType.CACHING:
                assert isinstance(policy.config, CachingConfig)
                print(f"  ✓ CachingConfig: {policy.config.ttl_seconds}s TTL")
                assert policy.config.ttl_seconds == 300
                assert policy.config.cache_key_strategy == "url_query"
        
        print("\n✓ All policy actions properly reconstructed with structured configs")
        
    except Exception as e:
        print(f"✗ Failed to retrieve or validate API: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    print(f"\nCleaning up test API")
    repo.delete(str(api_id))
    print("✓ Cleanup complete")
    
    return True


def main():
    print("=" * 60)
    print("PolicyAction Serialization/Deserialization Test")
    print("=" * 60)
    
    success = test_api_with_policy_actions()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if success:
        print("✓ PolicyAction serialization test PASSED")
        print("\nThe fix successfully resolves the issue:")
        print("  - APIs with structured PolicyAction configs can be created")
        print("  - Nested Pydantic models are properly serialized to OpenSearch")
        print("  - Nested Pydantic models are properly reconstructed on retrieval")
        return 0
    else:
        print("✗ PolicyAction serialization test FAILED")
        return 1


if __name__ == "__main__":
    exit(main())

# Made with Bob
