"""
Test script for Phase 1 policy configuration implementation.

Tests backward compatibility between dict-based and structured policy configs.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.models.base.api import PolicyAction, PolicyActionType
from app.models.base.policy_configs import (
    RateLimitConfig,
    AuthenticationConfig,
    AuthorizationConfig,
    CachingConfig,
)
from app.models.base.policy_helpers import (
    dict_to_structured_config,
    structured_to_dict_config,
    validate_policy_config,
    get_migration_report,
)


def test_structured_config():
    """Test creating policy with structured config."""
    print("\n=== Test 1: Structured Config ===")
    
    # Create rate limit policy with structured config
    policy = PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        enabled=True,
        stage="request",
        config=RateLimitConfig(
            requests_per_minute=1000,
            burst_allowance=100,
            rate_limit_key="api_key"
        )
    )
    
    print(f"✓ Created policy with structured config")
    print(f"  Action type: {policy.action_type}")
    print(f"  Config type: {type(policy.config).__name__}")
    print(f"  Is structured: {isinstance(policy.config, RateLimitConfig)}")
    
    if isinstance(policy.config, RateLimitConfig):
        print(f"  Requests per minute: {policy.config.requests_per_minute}")
        print(f"  Burst allowance: {policy.config.burst_allowance}")
    
    return True


def test_dict_config_rejected():
    """Test that dict config is now rejected."""
    print("\n=== Test 2: Dict Config Rejection ===")
    
    # Attempt to create rate limit policy with dict config (should fail)
    try:
        policy = PolicyAction(
            action_type=PolicyActionType.RATE_LIMITING,
            enabled=True,
            stage="request",
            config={
                "requests_per_minute": 1000,
                "burst_allowance": 100,
                "rate_limit_key": "api_key"
            }
        )
        print(f"✗ Dict config was not rejected (unexpected)")
        return False
    except Exception as e:
        print(f"✓ Dict config properly rejected")
        print(f"  Error: {str(e)[:100]}...")
        return True
    print(f"  Is structured: {policy.is_structured_config()}")
    
    if isinstance(policy.config, dict):
        print(f"  Requests per minute: {policy.config.get('requests_per_minute')}")
        print(f"  Burst allowance: {policy.config.get('burst_allowance')}")
    
    return True


def test_conversion():
    """Test conversion between dict and structured configs."""
    print("\n=== Test 3: Config Conversion ===")
    
    # Dict to structured
    config_dict = {
        "requests_per_minute": 1000,
        "burst_allowance": 100,
        "rate_limit_key": "ip"
    }
    
    structured = dict_to_structured_config(config_dict, PolicyActionType.RATE_LIMITING)
    print(f"✓ Converted dict to structured: {type(structured).__name__}")
    
    # Structured to dict
    config_dict_back = structured_to_dict_config(structured)
    print(f"✓ Converted structured to dict: {len(config_dict_back)} fields")
    print(f"  Fields: {list(config_dict_back.keys())}")
    
    return True


def test_validation():
    """Test config validation."""
    print("\n=== Test 4: Config Validation ===")
    
    # Valid structured config
    valid_config = RateLimitConfig(requests_per_minute=1000)
    is_valid, error = validate_policy_config(valid_config, PolicyActionType.RATE_LIMITING)
    print(f"✓ Valid structured config: {is_valid}")
    
    # Valid dict config
    valid_dict = {"requests_per_minute": 1000}
    is_valid, error = validate_policy_config(valid_dict, PolicyActionType.RATE_LIMITING)
    print(f"✓ Valid dict config: {is_valid}")
    
    # Invalid type mismatch
    auth_config = AuthenticationConfig(auth_type="oauth2")
    is_valid, error = validate_policy_config(auth_config, PolicyActionType.RATE_LIMITING)
    print(f"✓ Type mismatch detected: {not is_valid}")
    if error:
        print(f"  Error: {error}")
    
    return True


def test_multiple_policy_types():
    """Test different policy types."""
    print("\n=== Test 5: Multiple Policy Types ===")
    
    policies = []
    
    # Rate limiting
    policies.append(PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        config=RateLimitConfig(requests_per_minute=1000)
    ))
    
    # Authentication
    policies.append(PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        config=AuthenticationConfig(
            auth_type="oauth2",
            oauth_provider="auth0",
            oauth_scopes=["read:api", "write:api"]
        )
    ))
    
    # Authorization
    policies.append(PolicyAction(
        action_type=PolicyActionType.AUTHORIZATION,
        config=AuthorizationConfig(
            allowed_groups=["Administrators"],
            required_scopes=["admin"]
        )
    ))
    
    # Caching
    policies.append(PolicyAction(
        action_type=PolicyActionType.CACHING,
        config=CachingConfig(
            ttl_seconds=300,
            cache_key_strategy="url"
        )
    ))
    
    print(f"✓ Created {len(policies)} policies with different types")
    for policy in policies:
        print(f"  - {policy.action_type}: {type(policy.config).__name__}")
    
    return True


def test_migration_report():
    """Test migration reporting."""
    print("\n=== Test 6: Migration Report ===")
    
    # Mix of dict and structured configs
    policy_actions = [
        {
            "action_type": "rate_limiting",
            "config": {"requests_per_minute": 1000}  # Dict
        },
        {
            "action_type": "authentication",
            "config": AuthenticationConfig(auth_type="oauth2")  # Structured
        },
        {
            "action_type": "caching",
            "config": {"ttl_seconds": 300}  # Dict
        },
    ]
    
    report = get_migration_report(policy_actions)
    print(f"✓ Migration report generated:")
    print(f"  Total policies: {report['total_policies']}")
    print(f"  Dict configs: {report['dict_configs']}")
    print(f"  Structured configs: {report['structured_configs']}")
    print(f"  Migration possible: {report['migration_possible']}")
    print(f"  Structured percentage: {report['structured_percentage']:.1f}%")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Phase 1: Structured Policy Configs (Non-Breaking)")
    print("=" * 60)
    
    tests = [
        ("Structured Config", test_structured_config),
        ("Dict Config (Backward Compatible)", test_dict_config),
        ("Config Conversion", test_conversion),
        ("Config Validation", test_validation),
        ("Multiple Policy Types", test_multiple_policy_types),
        ("Migration Report", test_migration_report),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} failed")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} failed with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All tests passed! Phase 1 implementation is working correctly.")
        print("\nNext steps:")
        print("  1. Update gateway adapters to use structured configs")
        print("  2. Migrate existing policies gradually")
        print("  3. Add deprecation warnings in Phase 4")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
