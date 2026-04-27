"""
Policy conversion utilities for gateway adapters.

⚠️ DEPRECATION NOTICE ⚠️
This module is DEPRECATED and will be removed in a future version.

For webMethods policy conversions, use:
- backend/app/utils/webmethods/policy_normalizer.py (webMethods → vendor-neutral)
- backend/app/utils/webmethods/policy_denormalizer.py (vendor-neutral → webMethods)

These new modules provide:
- Structured, type-safe policy configurations (Pydantic models)
- Better validation and error handling
- Clearer separation of concerns
- Single source of truth for policy conversions

Migration Path:
1. Replace imports from this module with imports from policy_normalizer/denormalizer
2. Update code to use normalize_policy_action() and denormalize_policy_action()
3. Test thoroughly with your gateway integration

Provides conversion functions between vendor-neutral structured policy configs
and vendor-specific policy formats for different gateway types.

Supports:
- webMethods API Gateway
- Kong Gateway (future)
- Apigee (future)
"""

import logging
import warnings
from typing import Any, Optional, Union

# Issue deprecation warning when module is imported
warnings.warn(
    "policy_converters.py is deprecated. Use policy_normalizer.py and policy_denormalizer.py instead. "
    "See module docstring for migration path.",
    DeprecationWarning,
    stacklevel=2
)

from app.models.base.api import PolicyAction, PolicyActionType
from app.models.base.policy_configs import (
    RateLimitConfig,
    AuthenticationConfig,
    AuthorizationConfig,
    CachingConfig,
    CorsConfig,
    ValidationConfig,
    DataMaskingConfig,
    TransformationConfig,
    LoggingConfig,
    TlsConfig,
    CompressionConfig,
    PolicyConfigType,
)
from app.models.base.policy_helpers import (
    dict_to_structured_config,
    structured_to_dict_config,
)

logger = logging.getLogger(__name__)


# ============================================================================
# webMethods Conversions
# ============================================================================

def rate_limit_to_webmethods(config: RateLimitConfig) -> dict[str, Any]:
    """
    Convert vendor-neutral RateLimitConfig to webMethods ThrottlePolicy format.
    
    Args:
        config: Vendor-neutral rate limit configuration
        
    Returns:
        webMethods throttle policy dict
    """
    # Determine which time-based limit to use (prefer minute)
    limit_value = (
        config.requests_per_minute or
        config.requests_per_second or
        config.requests_per_hour or
        config.requests_per_day or
        1000
    )
    
    # Map to webMethods alert interval unit
    if config.requests_per_second:
        alert_interval = 1
        alert_unit = "SECONDS"
    elif config.requests_per_minute:
        alert_interval = 1
        alert_unit = "MINUTES"
    elif config.requests_per_hour:
        alert_interval = 1
        alert_unit = "HOURS"
    else:
        alert_interval = 1
        alert_unit = "DAYS"
    
    return {
        "templateKey": "throttle",
        "throttleRule": {
            "throttleRuleName": "requestCount",
            "monitorRuleOperator": "GT",
            "value": limit_value
        },
        "consumerIds": ["AllConsumers"],
        "consumerSpecificCounter": config.rate_limit_key != "ip",
        "destination": {
            "destinationType": "GATEWAY"
        },
        "alertInterval": alert_interval,
        "alertIntervalUnit": alert_unit,
        "alertFrequency": "ONCE",
        "alertMessage": f"Rate limit of {limit_value} requests exceeded"
    }


def authentication_to_webmethods(config: AuthenticationConfig) -> dict[str, Any]:
    """
    Convert vendor-neutral AuthenticationConfig to webMethods format.
    
    Args:
        config: Vendor-neutral authentication configuration
        
    Returns:
        webMethods authentication policy dict
    """
    # Map auth types
    auth_type_map = {
        "basic": "HTTP_BASIC_AUTH",
        "bearer": "OAUTH2_TOKEN",
        "oauth2": "OAUTH2_TOKEN",
        "api_key": "API_KEY",
        "jwt": "JWT_CLAIMS",
        "mtls": "HTTP_BASIC_AUTH"  # webMethods handles mTLS differently
    }
    
    identification_type = auth_type_map.get(config.auth_type, "OAUTH2_TOKEN")
    
    return {
        "templateKey": "evaluate",
        "logicalConnector": "OR",
        "allowAnonymous": config.allow_anonymous,
        "triggerPolicyViolationOnMissingAuthorizationHeader": not config.allow_anonymous,
        "identificationRules": [
            {
                "applicationLookup": "STRICT",
                "identificationType": identification_type
            }
        ]
    }


def authorization_to_webmethods(config: AuthorizationConfig) -> dict[str, Any]:
    """
    Convert vendor-neutral AuthorizationConfig to webMethods format.
    
    Args:
        config: Vendor-neutral authorization configuration
        
    Returns:
        webMethods authorization policy dict
    """
    return {
        "templateKey": "authorizeUser",
        "users": config.allowed_users or ["Administrator"],
        "groups": config.allowed_groups or ["Administrators"],
        "accessProfiles": config.allowed_access_profiles or ["Administrators"]
    }


def caching_to_webmethods(config: CachingConfig) -> dict[str, Any]:
    """
    Convert vendor-neutral CachingConfig to webMethods format.
    
    Args:
        config: Vendor-neutral caching configuration
        
    Returns:
        webMethods caching policy dict
    """
    return {
        "templateKey": "serviceResultCache",
        "ttl": config.ttl_seconds,
        "maxPayloadSize": config.max_payload_size_bytes or 1048576  # 1MB default
    }


# ============================================================================
# Native Gateway Conversions
# ============================================================================

def rate_limit_to_native(config: RateLimitConfig) -> dict[str, Any]:
    """
    Convert vendor-neutral RateLimitConfig to Native Gateway format.
    
    Args:
        config: Vendor-neutral rate limit configuration
        
    Returns:
        Native gateway rate limit policy dict
    """
    return {
        "policyType": "rate_limit",
        "limitThresholds": {
            "requestsPerSecond": config.requests_per_second,
            "requestsPerMinute": config.requests_per_minute,
            "requestsPerHour": config.requests_per_hour,
            "concurrentRequests": config.concurrent_requests
        },
        "enforcementAction": config.enforcement_action,
        "burstAllowance": config.burst_allowance,
        "consumerTiers": [
            {
                "tierName": tier_name,
                "rateMultiplier": 1.0,
                "tierLevel": idx
            }
            for idx, tier_name in enumerate(config.consumer_tiers.keys() if config.consumer_tiers else [])
        ]
    }


def authentication_to_native(config: AuthenticationConfig) -> dict[str, Any]:
    """
    Convert vendor-neutral AuthenticationConfig to Native Gateway format.
    
    Args:
        config: Vendor-neutral authentication configuration
        
    Returns:
        Native gateway authentication policy dict
    """
    return {
        "auth_type": config.auth_type,
        "provider": config.oauth_provider or "default",
        "scopes": ",".join(config.oauth_scopes) if config.oauth_scopes else "read,write",
        "validation_rules": {
            "jwt_issuer": config.jwt_issuer,
            "jwt_audience": config.jwt_audience,
            "cache_ttl": config.cache_ttl_seconds
        }
    }


def caching_to_native(config: CachingConfig) -> dict[str, Any]:
    """
    Convert vendor-neutral CachingConfig to Native Gateway format.
    
    Args:
        config: Vendor-neutral caching configuration
        
    Returns:
        Native gateway caching policy dict
    """
    return {
        "ttl_seconds": config.ttl_seconds,
        "cache_key_strategy": config.cache_key_strategy,
        "vary_headers": ",".join(config.vary_headers) if config.vary_headers else "Accept,Accept-Encoding",
        "invalidation_rules": {
            "invalidate_on_methods": config.invalidate_on_methods
        }
    }


# ============================================================================
# Reverse Conversions (Vendor-Specific to Vendor-Neutral)
# ============================================================================

def webmethods_to_rate_limit(wm_policy: dict[str, Any]) -> Optional[RateLimitConfig]:
    """
    Convert webMethods throttle policy to vendor-neutral RateLimitConfig.
    
    Args:
        wm_policy: webMethods throttle policy dict
        
    Returns:
        Vendor-neutral RateLimitConfig or None if conversion fails
    """
    try:
        throttle_rule = wm_policy.get("throttleRule", {})
        value = throttle_rule.get("value", 1000)
        alert_unit = wm_policy.get("alertIntervalUnit", "MINUTES")
        
        # Map alert unit to appropriate time-based limit
        if alert_unit == "SECONDS":
            return RateLimitConfig(requests_per_second=value)
        elif alert_unit == "MINUTES":
            return RateLimitConfig(requests_per_minute=value)
        elif alert_unit == "HOURS":
            return RateLimitConfig(requests_per_hour=value)
        else:
            return RateLimitConfig(requests_per_day=value)
    except Exception as e:
        logger.error(f"Failed to convert webMethods policy to RateLimitConfig: {e}")
        return None


def native_to_rate_limit(native_policy: dict[str, Any]) -> Optional[RateLimitConfig]:
    """
    Convert Native Gateway rate limit policy to vendor-neutral RateLimitConfig.
    
    Args:
        native_policy: Native gateway rate limit policy dict
        
    Returns:
        Vendor-neutral RateLimitConfig or None if conversion fails
    """
    try:
        thresholds = native_policy.get("limitThresholds", {})
        return RateLimitConfig(
            requests_per_second=thresholds.get("requestsPerSecond"),
            requests_per_minute=thresholds.get("requestsPerMinute"),
            requests_per_hour=thresholds.get("requestsPerHour"),
            concurrent_requests=thresholds.get("concurrentRequests"),
            burst_allowance=native_policy.get("burstAllowance"),
            enforcement_action=native_policy.get("enforcementAction", "reject")
        )
    except Exception as e:
        logger.error(f"Failed to convert Native policy to RateLimitConfig: {e}")
        return None


# ============================================================================
# Generic Conversion Functions
# ============================================================================

def to_vendor_specific(
    policy_action: PolicyAction,
    vendor: str
) -> dict[str, Any]:
    """
    Convert vendor-neutral PolicyAction to vendor-specific format.
    
    Args:
        policy_action: Vendor-neutral policy action
        vendor: Target vendor ("webmethods", "native", "kong", "apigee")
        
    Returns:
        Vendor-specific policy dict
        
    Raises:
        ValueError: If vendor is not supported or conversion fails
    """
    # Get structured config (convert from dict if needed)
    config = policy_action.config
    if isinstance(config, dict):
        config = dict_to_structured_config(config, policy_action.action_type)
        if config is None:
            raise ValueError(f"Failed to convert dict config to structured config")
    
    # Route to appropriate converter based on vendor and action type
    converters = {
        "webmethods": {
            PolicyActionType.RATE_LIMITING: rate_limit_to_webmethods,
            PolicyActionType.AUTHENTICATION: authentication_to_webmethods,
            PolicyActionType.AUTHORIZATION: authorization_to_webmethods,
            PolicyActionType.CACHING: caching_to_webmethods,
        },
        "native": {
            PolicyActionType.RATE_LIMITING: rate_limit_to_native,
            PolicyActionType.AUTHENTICATION: authentication_to_native,
            PolicyActionType.CACHING: caching_to_native,
        }
    }
    
    vendor_converters = converters.get(vendor.lower())
    if not vendor_converters:
        raise ValueError(f"Unsupported vendor: {vendor}")
    
    converter = vendor_converters.get(policy_action.action_type)
    if not converter:
        # Return dict config as fallback
        if isinstance(policy_action.config, dict):
            return policy_action.config
        if policy_action.config is not None:
            return structured_to_dict_config(policy_action.config)
        return {}
    
    return converter(config)


def from_vendor_specific(
    vendor_policy: dict[str, Any],
    action_type: PolicyActionType,
    vendor: str
) -> Optional[PolicyConfigType]:
    """
    Convert vendor-specific policy to vendor-neutral structured config.
    
    Args:
        vendor_policy: Vendor-specific policy dict
        action_type: Type of policy action
        vendor: Source vendor ("webmethods", "native", "kong", "apigee")
        
    Returns:
        Vendor-neutral structured config or None if conversion fails
    """
    converters = {
        "webmethods": {
            PolicyActionType.RATE_LIMITING: webmethods_to_rate_limit,
        },
        "native": {
            PolicyActionType.RATE_LIMITING: native_to_rate_limit,
        }
    }
    
    vendor_converters = converters.get(vendor.lower(), {})
    converter = vendor_converters.get(action_type)
    
    if converter:
        return converter(vendor_policy)
    
    # Fallback: try to convert dict to structured config
    return dict_to_structured_config(vendor_policy, action_type)


# Export all conversion functions
__all__ = [
    # webMethods conversions
    "rate_limit_to_webmethods",
    "authentication_to_webmethods",
    "authorization_to_webmethods",
    "caching_to_webmethods",
    # Native Gateway conversions
    "rate_limit_to_native",
    "authentication_to_native",
    "caching_to_native",
    # Reverse conversions
    "webmethods_to_rate_limit",
    "native_to_rate_limit",
    # Generic conversions
    "to_vendor_specific",
    "from_vendor_specific",
]

# Made with Bob
