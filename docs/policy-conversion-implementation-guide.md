# Policy Conversion Implementation Guide

**Date**: 2026-04-14
**Status**: ✅ Implementation Complete
**Completion Date**: 2026-04-14
**Related**: [`policy-conversion-holistic-analysis.md`](policy-conversion-holistic-analysis.md)

## Overview

This guide provided detailed implementation steps for unifying the three disconnected policy conversion systems into a coherent architecture.

**✅ ALL PHASES COMPLETE**: The implementation has been successfully completed. This document now serves as a reference for the implementation approach used.

## Phase 1: Enhance policy_normalizer.py (IN PROGRESS)

### Goal
Update `backend/app/utils/webmethods/policy_normalizer.py` to produce structured configs instead of dict configs.

### Implementation Steps

#### 1.1 Update Imports (✅ DONE)
```python
from ...models.base.policy_configs import (
    TlsConfig,
    AuthenticationConfig,
    AuthorizationConfig,
    LoggingConfig,
    RateLimitConfig,
    CachingConfig,
    ValidationConfig,
    DataMaskingConfig,
    CorsConfig,
)
```

#### 1.2 Update normalize_entry_protocol_policy()
**Current**: Returns dict config
**Target**: Return TlsConfig

```python
def normalize_entry_protocol_policy(policy: EntryProtocolPolicy) -> PolicyAction:
    protocol_value = policy.protocol.value if policy.protocol else "http"
    
    config = TlsConfig(
        enforce_tls=(protocol_value == "https"),
        min_tls_version="1.2",
        allowed_cipher_suites=None,
        require_client_certificate=False,
        trusted_ca_certificates=None,
        verify_backend_certificate=True
    )
    
    return PolicyAction(
        action_type=PolicyActionType.TLS,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Entry Protocol'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'entryProtocolPolicy'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.3 Update normalize_throttle_policy()
**Current**: Returns dict config
**Target**: Return RateLimitConfig

```python
def normalize_throttle_policy(policy: ThrottlePolicy) -> PolicyAction:
    throttle_rule = policy.throttle_rule if hasattr(policy, 'throttle_rule') else policy.throttleRule
    alert_interval_unit = policy.alert_interval_unit if hasattr(policy, 'alert_interval_unit') else policy.alertIntervalUnit
    
    limit_value = throttle_rule.value
    config_kwargs = {}
    
    # Map webMethods time unit to structured config
    if alert_interval_unit.value == "SECONDS":
        config_kwargs["requests_per_second"] = limit_value
    elif alert_interval_unit.value == "MINUTES":
        config_kwargs["requests_per_minute"] = limit_value
    elif alert_interval_unit.value == "HOURS":
        config_kwargs["requests_per_hour"] = limit_value
    elif alert_interval_unit.value == "DAYS":
        config_kwargs["requests_per_day"] = limit_value
    else:
        config_kwargs["requests_per_minute"] = limit_value
    
    config = RateLimitConfig(
        **config_kwargs,
        rate_limit_key="custom",  # webMethods uses consumer-based
        enforcement_action="reject"
    )
    
    return PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Traffic Optimization'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'throttle'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.4 Update normalize_evaluate_policy()
**Current**: Returns dict config
**Target**: Return AuthenticationConfig

```python
def normalize_evaluate_policy(policy: EvaluatePolicy) -> PolicyAction:
    allow_anonymous = policy.allow_anonymous if hasattr(policy, 'allow_anonymous') else policy.allowAnonymous
    
    # Determine auth type from identification rules
    identification_rules = policy.identification_rules
    auth_type = "oauth2"  # Default
    
    if identification_rules:
        first_rule = identification_rules[0]
        id_type = first_rule.identification_type if hasattr(first_rule, 'identification_type') else first_rule.identificationType
        
        if id_type.value == "API_KEY":
            auth_type = "api_key"
        elif id_type.value == "HTTP_BASIC_AUTH":
            auth_type = "basic"
        elif id_type.value == "JWT_CLAIMS":
            auth_type = "jwt"
    
    config = AuthenticationConfig(
        auth_type=auth_type,
        allow_anonymous=allow_anonymous
    )
    
    return PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Identify & Authorize'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'evaluatePolicy'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.5 Update normalize_authorize_user_policy()
**Current**: Returns dict config
**Target**: Return AuthorizationConfig

```python
def normalize_authorize_user_policy(policy: AuthorizeUserPolicy) -> PolicyAction:
    config = AuthorizationConfig(
        allowed_users=policy.users,
        allowed_groups=policy.groups,
        allowed_access_profiles=policy.access_profiles if hasattr(policy, 'access_profiles') else policy.accessProfiles
    )
    
    return PolicyAction(
        action_type=PolicyActionType.AUTHORIZATION,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Authorize User'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'authorizeUser'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.6 Update normalize_log_invocation_policy()
**Current**: Returns dict config
**Target**: Return LoggingConfig

```python
def normalize_log_invocation_policy(policy: LogInvocationPolicy) -> PolicyAction:
    store_request_headers = policy.store_request_headers if hasattr(policy, 'store_request_headers') else policy.storeRequestHeaders
    store_request_payload = policy.store_request_payload if hasattr(policy, 'store_request_payload') else policy.storeRequestPayload
    store_response_headers = policy.store_response_headers if hasattr(policy, 'store_response_headers') else policy.storeResponseHeaders
    store_response_payload = policy.store_response_payload if hasattr(policy, 'store_response_payload') else policy.storeResponsePayload
    
    config = LoggingConfig(
        log_level="info",
        log_request_headers=store_request_headers,
        log_request_body=store_request_payload,
        log_response_headers=store_response_headers,
        log_response_body=store_response_payload,
        sampling_rate=1.0,
        log_to_gateway=True
    )
    
    return PolicyAction(
        action_type=PolicyActionType.LOGGING,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Log Invocation'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'logInvocation'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.7 Update normalize_service_result_cache_policy()
**Current**: Returns dict config
**Target**: Return CachingConfig

```python
def normalize_service_result_cache_policy(policy: ServiceResultCachePolicy) -> PolicyAction:
    # Parse TTL string (e.g., "1d", "2h", "30m")
    ttl_str = policy.ttl
    ttl_seconds = 3600  # Default 1 hour
    
    if ttl_str.endswith('d'):
        ttl_seconds = int(ttl_str[:-1]) * 86400
    elif ttl_str.endswith('h'):
        ttl_seconds = int(ttl_str[:-1]) * 3600
    elif ttl_str.endswith('m'):
        ttl_seconds = int(ttl_str[:-1]) * 60
    elif ttl_str.endswith('s'):
        ttl_seconds = int(ttl_str[:-1])
    
    config = CachingConfig(
        ttl_seconds=ttl_seconds,
        cache_key_strategy="url_params",
        vary_headers=["Accept", "Accept-Encoding"]
    )
    
    return PolicyAction(
        action_type=PolicyActionType.CACHING,
        enabled=True,
        stage="response",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Service Result Cache'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'serviceResultCache'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.8 Update normalize_validate_api_spec_policy()
**Current**: Returns dict config
**Target**: Return ValidationConfig

```python
def normalize_validate_api_spec_policy(policy: ValidateAPISpecPolicy) -> PolicyAction:
    schema_validation = policy.schema_validation_flag if hasattr(policy, 'schema_validation_flag') else policy.schemaValidationFlag
    validate_query = policy.validate_query_params if hasattr(policy, 'validate_query_params') else policy.validateQueryParams
    validate_path = policy.validate_path_params if hasattr(policy, 'validate_path_params') else policy.validatePathParams
    
    config = ValidationConfig(
        validate_schema=schema_validation,
        validate_query_params=validate_query,
        validate_path_params=validate_path,
        validate_headers=False,
        strict_mode=True
    )
    
    return PolicyAction(
        action_type=PolicyActionType.VALIDATION,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Validate API Specification'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'validateAPISpec'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.9 Update normalize_request_data_masking_policy()
**Current**: Returns dict config
**Target**: Return DataMaskingConfig

```python
def normalize_request_data_masking_policy(policy: RequestDataMaskingPolicy) -> PolicyAction:
    config = DataMaskingConfig(
        mask_request=True,
        mask_response=False,
        mask_fields=["password", "ssn", "credit_card"],
        mask_pattern="****",
        preserve_length=True
    )
    
    return PolicyAction(
        action_type=PolicyActionType.DATA_MASKING,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Request Data Masking'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'requestDataMasking'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.10 Update normalize_response_data_masking_policy()
**Current**: Returns dict config
**Target**: Return DataMaskingConfig

```python
def normalize_response_data_masking_policy(policy: ResponseDataMaskingPolicy) -> PolicyAction:
    config = DataMaskingConfig(
        mask_request=False,
        mask_response=True,
        mask_fields=["password", "ssn", "credit_card"],
        mask_pattern="****",
        preserve_length=True
    )
    
    return PolicyAction(
        action_type=PolicyActionType.DATA_MASKING,
        enabled=True,
        stage="response",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Response Data Masking'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'responseDataMasking'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

#### 1.11 Update normalize_cors_policy()
**Current**: Returns dict config
**Target**: Return CorsConfig

```python
def normalize_cors_policy(policy: CorsPolicy) -> PolicyAction:
    cors_attrs = policy.cors_attributes if hasattr(policy, 'cors_attributes') else policy.corsAttributes
    
    allowed_origins = cors_attrs.allowed_origins if hasattr(cors_attrs, 'allowed_origins') else cors_attrs.allowedOrigins
    allow_headers = cors_attrs.allow_headers if hasattr(cors_attrs, 'allow_headers') else cors_attrs.allowHeaders
    expose_headers = cors_attrs.expose_headers if hasattr(cors_attrs, 'expose_headers') else cors_attrs.exposeHeaders
    allow_credentials = cors_attrs.allow_credentials if hasattr(cors_attrs, 'allow_credentials') else cors_attrs.allowCredentials
    allow_methods = cors_attrs.allow_methods if hasattr(cors_attrs, 'allow_methods') else cors_attrs.allowMethods
    max_age = cors_attrs.max_age if hasattr(cors_attrs, 'max_age') else cors_attrs.maxAge
    
    config = CorsConfig(
        allowed_origins=allowed_origins,
        allowed_methods=[m.value for m in allow_methods],
        allowed_headers=allow_headers,
        exposed_headers=expose_headers,
        allow_credentials=allow_credentials,
        max_age_seconds=max_age
    )
    
    return PolicyAction(
        action_type=PolicyActionType.CORS,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'CORS'),
        description=policy.description,
        config=config,  # Structured config
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'cors'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )
```

### Testing Phase 1
```bash
cd backend
python -m pytest tests/ -k "normalize" -v
```

## Phase 2: Enhance policy_denormalizer.py

### Goal
Update `backend/app/utils/webmethods/policy_denormalizer.py` to read structured configs instead of dict configs.

### Key Pattern
Each denormalizer function should:
1. Check if config is structured or dict
2. Convert dict to structured if needed using `dict_to_structured_config()`
3. Extract values from structured config
4. Map to webMethods policy object

### Example Template
```python
def denormalize_to_throttle_policy(action: PolicyAction) -> ThrottlePolicy:
    from app.models.base.policy_configs import RateLimitConfig
    from app.models.base.policy_helpers import dict_to_structured_config
    
    # Get structured config (convert from dict if needed)
    config = action.config
    if isinstance(config, dict):
        config = dict_to_structured_config(config, action.action_type)
    
    if not isinstance(config, RateLimitConfig):
        raise ValueError(f"Expected RateLimitConfig, got {type(config)}")
    
    # Map structured config to webMethods policy
    if config.requests_per_minute:
        value = config.requests_per_minute
        alert_unit = AlertIntervalUnit.MINUTES
    elif config.requests_per_second:
        value = config.requests_per_second
        alert_unit = AlertIntervalUnit.SECONDS
    elif config.requests_per_hour:
        value = config.requests_per_hour
        alert_unit = AlertIntervalUnit.HOURS
    elif config.requests_per_day:
        value = config.requests_per_day
        alert_unit = AlertIntervalUnit.DAYS
    else:
        value = 1000
        alert_unit = AlertIntervalUnit.MINUTES
    
    return ThrottlePolicy(
        throttleRule=ThrottleRule(
            throttleRuleName="requestCount",
            monitorRuleOperator=MonitorRuleOperator.GT,
            value=value
        ),
        consumerIds=["AllConsumers"],
        consumerSpecificCounter=False,
        destination=ThrottleDestination(
            destinationType=DestinationType.GATEWAY
        ),
        alertInterval=1,
        alertIntervalUnit=alert_unit,
        alertFrequency=AlertFrequency.ONCE,
        alertMessage=f"Rate limit of {value} requests exceeded"
    )
```

## Phase 3: Update webmethods_gateway.py

### Goal
Ensure the adapter uses the enhanced normalizer/denormalizer.

### Changes Required
**None** - The adapter already uses the normalizer/denormalizer functions. Once Phase 1 and 2 are complete, the adapter will automatically use structured configs.

### Verification
```python
# In webmethods_gateway.py:_fetch_policy_actions()
# Line 971: normalized_action = normalize_policy_action(parsed_policy)
# This will now return PolicyAction with structured config

# In webmethods_gateway.py:_transform_from_policy_action()
# Line 1385: webmethods_policy = denormalize_policy_action(policy_action)
# This will now read from structured config
```

## Phase 4: Deprecate policy_converters.py

### Goal
Mark `backend/app/adapters/policy_converters.py` as deprecated.

### Implementation
```python
# Add at top of file
import warnings

warnings.warn(
    "policy_converters.py is deprecated. "
    "Use backend/app/utils/webmethods/policy_normalizer.py and policy_denormalizer.py instead. "
    "This module will be removed in the next major version.",
    DeprecationWarning,
    stacklevel=2
)
```

## Phase 5: Update Documentation

### Files to Update
1. `docs/vendor-neutral-policy-configuration-analysis.md` - Add section on unified architecture
2. `docs/policy-conversion-holistic-analysis.md` - Mark as implemented
3. `AGENTS.md` - Update with new conversion patterns
4. `README.md` - Update architecture diagrams

### New Documentation
Create `docs/policy-conversion-unified-architecture.md` with:
- Architecture diagrams
- Conversion examples for each policy type
- Guide for adding new vendors
- Migration guide for existing code

## Testing Strategy

### Unit Tests
```bash
# Test normalizer produces structured configs
pytest backend/tests/unit/test_policy_normalizer.py -v

# Test denormalizer reads structured configs
pytest backend/tests/unit/test_policy_denormalizer.py -v
```

### Integration Tests
```bash
# Test full conversion cycle
pytest backend/tests/integration/test_policy_conversion.py -v
```

### E2E Tests
```bash
# Test with real webMethods Gateway
pytest backend/tests/e2e/test_webmethods_policies.py -v
```

## Success Criteria

- [ ] Phase 1: All normalizer functions produce structured configs
- [ ] Phase 2: All denormalizer functions read structured configs
- [ ] Phase 3: Adapter uses enhanced System 1
- [ ] Phase 4: policy_converters.py marked as deprecated
- [ ] Phase 5: Documentation updated
- [ ] All tests passing
- [ ] No breaking changes for existing code
- [ ] Backward compatibility maintained

## Timeline

| Phase | Estimated Time | Status |
|-------|---------------|--------|
| Phase 1 | 1-2 days | In Progress |
| Phase 2 | 1-2 days | Pending |
| Phase 3 | 1 day | Pending |
| Phase 4 | 1 day | Pending |
| Phase 5 | 1 day | Pending |
| **Total** | **5-7 days** | **20% Complete** |

## Notes

- The type errors in policy_normalizer.py are expected due to hasattr checks for both snake_case and camelCase attributes
- These errors will not affect runtime behavior
- Consider adding type: ignore comments for known safe hasattr patterns
- The original_policy in vendor_config preserves all webMethods-specific data

**Made with Bob**