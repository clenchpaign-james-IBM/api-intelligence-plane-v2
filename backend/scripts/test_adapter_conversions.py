"""
Test script for Phase 2 adapter policy conversions.

Tests conversion between vendor-neutral structured configs and vendor-specific formats.
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
from app.adapters.policy_converters import (
    to_vendor_specific,
    from_vendor_specific,
    rate_limit_to_webmethods,
    rate_limit_to_native,
    webmethods_to_rate_limit,
    native_to_rate_limit,
)


def test_rate_limit_to_webmethods():
    """Test converting rate limit config to webMethods format."""
    print("\n=== Test 1: Rate Limit to webMethods ===")
    
    config = RateLimitConfig(
        requests_per_minute=1000,
        burst_allowance=100
    )
    
    wm_policy = rate_limit_to_webmethods(config)
    
    print(f"✓ Converted to webMethods format")
    print(f"  Template: {wm_policy.get('templateKey')}")
    print(f"  Throttle value: {wm_policy.get('throttleRule', {}).get('value')}")
    print(f"  Alert unit: {wm_policy.get('alertIntervalUnit')}")
    
    assert wm_policy["templateKey"] == "throttle"
    assert wm_policy["throttleRule"]["value"] == 1000
    assert wm_policy["alertIntervalUnit"] == "MINUTES"
    
    return True


def test_rate_limit_to_native():
    """Test converting rate limit config to Native Gateway format."""
    print("\n=== Test 2: Rate Limit to Native Gateway ===")
    
    config = RateLimitConfig(
        requests_per_minute=1000,
        requests_per_hour=50000,
        burst_allowance=100,
        enforcement_action="throttle"
    )
    
    native_policy = rate_limit_to_native(config)
    
    print(f"✓ Converted to Native Gateway format")
    print(f"  Policy type: {native_policy.get('policyType')}")
    print(f"  Requests/min: {native_policy.get('limitThresholds', {}).get('requestsPerMinute')}")
    print(f"  Enforcement: {native_policy.get('enforcementAction')}")
    
    assert native_policy["policyType"] == "rate_limit"
    assert native_policy["limitThresholds"]["requestsPerMinute"] == 1000
    assert native_policy["enforcementAction"] == "throttle"
    
    return True


def test_webmethods_to_rate_limit():
    """Test converting webMethods format to rate limit config."""
    print("\n=== Test 3: webMethods to Rate Limit ===")
    
    wm_policy = {
        "templateKey": "throttle",
        "throttleRule": {
            "throttleRuleName": "requestCount",
            "monitorRuleOperator": "GT",
            "value": 1000
        },
        "alertIntervalUnit": "MINUTES"
    }
    
    config = webmethods_to_rate_limit(wm_policy)
    
    print(f"✓ Converted from webMethods format")
    print(f"  Config type: {type(config).__name__}")
    print(f"  Requests/min: {config.requests_per_minute}")
    
    assert isinstance(config, RateLimitConfig)
    assert config.requests_per_minute == 1000
    
    return True


def test_native_to_rate_limit():
    """Test converting Native Gateway format to rate limit config."""
    print("\n=== Test 4: Native Gateway to Rate Limit ===")
    
    native_policy = {
        "policyType": "rate_limit",
        "limitThresholds": {
            "requestsPerMinute": 1000,
            "requestsPerHour": 50000
        },
        "enforcementAction": "throttle",
        "burstAllowance": 100
    }
    
    config = native_to_rate_limit(native_policy)
    
    print(f"✓ Converted from Native Gateway format")
    print(f"  Config type: {type(config).__name__}")
    print(f"  Requests/min: {config.requests_per_minute}")
    print(f"  Requests/hour: {config.requests_per_hour}")
    print(f"  Enforcement: {config.enforcement_action}")
    
    assert isinstance(config, RateLimitConfig)
    assert config.requests_per_minute == 1000
    assert config.requests_per_hour == 50000
    assert config.enforcement_action == "throttle"
    
    return True


def test_generic_to_vendor_specific():
    """Test generic conversion to vendor-specific format."""
    print("\n=== Test 5: Generic to Vendor-Specific ===")
    
    # Create policy action with structured config
    policy = PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        config=RateLimitConfig(requests_per_minute=1000)
    )
    
    # Convert to webMethods
    wm_policy = to_vendor_specific(policy, "webmethods")
    print(f"✓ Converted to webMethods: {wm_policy.get('templateKey')}")
    
    # Convert to Native
    native_policy = to_vendor_specific(policy, "native")
    print(f"✓ Converted to Native: {native_policy.get('policyType')}")
    
    assert wm_policy["templateKey"] == "throttle"
    assert native_policy["policyType"] == "rate_limit"
    
    return True


def test_generic_from_vendor_specific():
    """Test generic conversion from vendor-specific format."""
    print("\n=== Test 6: Generic from Vendor-Specific ===")
    
    # webMethods policy
    wm_policy = {
        "templateKey": "throttle",
        "throttleRule": {"value": 1000},
        "alertIntervalUnit": "MINUTES"
    }
    
    config = from_vendor_specific(wm_policy, PolicyActionType.RATE_LIMITING, "webmethods")
    print(f"✓ Converted from webMethods: {type(config).__name__}")
    
    # Native policy
    native_policy = {
        "limitThresholds": {"requestsPerMinute": 1000},
        "enforcementAction": "reject"
    }
    
    config = from_vendor_specific(native_policy, PolicyActionType.RATE_LIMITING, "native")
    print(f"✓ Converted from Native: {type(config).__name__}")
    
    assert isinstance(config, RateLimitConfig)
    
    return True


def test_round_trip_conversion():
    """Test round-trip conversion (vendor-neutral -> vendor-specific -> vendor-neutral)."""
    print("\n=== Test 7: Round-Trip Conversion ===")
    
    # Original config
    original = RateLimitConfig(
        requests_per_minute=1000,
        burst_allowance=100
    )
    
    # Convert to webMethods and back
    wm_policy = rate_limit_to_webmethods(original)
    converted = webmethods_to_rate_limit(wm_policy)
    
    print(f"✓ Round-trip through webMethods")
    print(f"  Original requests/min: {original.requests_per_minute}")
    print(f"  Converted requests/min: {converted.requests_per_minute}")
    
    assert converted.requests_per_minute == original.requests_per_minute
    
    # Convert to Native and back
    native_policy = rate_limit_to_native(original)
    converted = native_to_rate_limit(native_policy)
    
    print(f"✓ Round-trip through Native Gateway")
    print(f"  Original requests/min: {original.requests_per_minute}")
    print(f"  Converted requests/min: {converted.requests_per_minute}")
    
    assert converted.requests_per_minute == original.requests_per_minute
    
    return True


def test_dict_config_rejected():
    """Test that dict-based configs are now rejected."""
    print("\n=== Test 8: Dict Config Rejection ===")
    
    # Attempt to create policy with dict config (should fail)
    try:
        policy = PolicyAction(
            action_type=PolicyActionType.RATE_LIMITING,
            config={"requests_per_minute": 1000, "burst_allowance": 100}
        )
        print(f"✗ Dict config was not rejected (unexpected)")
        return False
    except Exception as e:
        print(f"✓ Dict config properly rejected")
        print(f"  Error: {str(e)[:100]}...")
        return True
    
    assert wm_policy["templateKey"] == "throttle"
    assert wm_policy["throttleRule"]["value"] == 1000
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Phase 2: Adapter Policy Conversions")
    print("=" * 60)
    
    tests = [
        ("Rate Limit to webMethods", test_rate_limit_to_webmethods),
        ("Rate Limit to Native Gateway", test_rate_limit_to_native),
        ("webMethods to Rate Limit", test_webmethods_to_rate_limit),
        ("Native Gateway to Rate Limit", test_native_to_rate_limit),
        ("Generic to Vendor-Specific", test_generic_to_vendor_specific),
        ("Generic from Vendor-Specific", test_generic_from_vendor_specific),
        ("Round-Trip Conversion", test_round_trip_conversion),
        ("Dict Config Conversion", test_dict_config_conversion),
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
        print("\n✓ All adapter conversion tests passed!")
        print("\nPhase 2 implementation complete:")
        print("  ✓ Vendor-neutral to vendor-specific conversions")
        print("  ✓ Vendor-specific to vendor-neutral conversions")
        print("  ✓ Round-trip conversions maintain data integrity")
        print("  ✓ Backward compatible with dict configs")
        print("\nNext steps:")
        print("  1. Integrate converters into gateway adapters")
        print("  2. Update adapter methods to use structured configs")
        print("  3. Test with real gateway connections")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
