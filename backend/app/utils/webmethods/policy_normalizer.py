"""
Policy Normalizer for webMethods Gateway

Converts webMethods-specific policy actions to vendor-neutral structured configs.
This is the SINGLE SOURCE OF TRUTH for webMethods → vendor-neutral conversion.

Enhanced to produce structured policy configurations for type safety and validation.

IBM Confidential - Copyright 2024 IBM Corp.
"""

from typing import Any, Dict, Optional, Union

from ...models.base.api import PolicyAction, PolicyActionType
from ...models.base.policy_configs import (
    TlsConfig,
    AuthenticationConfig,
    AuthorizationConfig,
    LoggingConfig,
    RateLimitConfig,
    CachingConfig,
    ValidationConfig,
    DataMaskingConfig,
    MaskingRule,
    CorsConfig,
)
from ...models.webmethods.wm_policy_action import (
    EntryProtocolPolicy,
    EvaluatePolicy,
    AuthorizeUserPolicy,
    LogInvocationPolicy,
    ThrottlePolicy,
    ServiceResultCachePolicy,
    ValidateAPISpecPolicy,
    RequestDataMaskingPolicy,
    ResponseDataMaskingPolicy,
    CorsPolicy,
)


def normalize_entry_protocol_policy(policy: EntryProtocolPolicy) -> PolicyAction:
    """
    Normalize EntryProtocolPolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The EntryProtocolPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with TlsConfig.

    Example:
        >>> policy = EntryProtocolPolicy(protocol=Protocol.HTTPS)
        >>> action = normalize_entry_protocol_policy(policy)
        >>> action.action_type
        <PolicyActionType.TLS: 'tls'>
    """
    # Create structured TLS config
    protocol_value = policy.protocol.value if policy.protocol else "http"
    config = TlsConfig(
        enforce_tls=(protocol_value == "https"),
        min_tls_version="1.2" if protocol_value == "https" else "1.0",
        allowed_cipher_suites=None,
        require_client_certificate=False,
        trusted_ca_certificates=None,
        verify_backend_certificate=True
    )
    
    return PolicyAction(
        action_type=PolicyActionType.TLS,
        enabled=True,
        stage="request",
        name=policy.name or 'Entry Protocol',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'entryProtocolPolicy',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_evaluate_policy(policy: EvaluatePolicy) -> PolicyAction:
    """
    Normalize EvaluatePolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The EvaluatePolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with AuthenticationConfig.
    """
    # Determine auth type from identification rules
    auth_type = "oauth2"  # Default
    
    if policy.identification_rules:
        first_rule = policy.identification_rules[0]
        id_type = first_rule.identification_type
        
        if id_type.value == "apiKey":
            auth_type = "api_key"
        elif id_type.value == "httpBasicAuth":
            auth_type = "basic"
        elif id_type.value == "jwtClaims":
            auth_type = "jwt"
    
    # Create structured authentication config
    config = AuthenticationConfig(
        auth_type=auth_type,
        allow_anonymous=policy.allow_anonymous,
        oauth_provider=None,
        oauth_scopes=None,
        oauth_token_endpoint=None,
        jwt_issuer=None,
        jwt_audience=None,
        jwt_public_key_url=None,
        api_key_header=None,
        api_key_query_param=None,
        cache_credentials=True,
        cache_ttl_seconds=300
    )
    
    return PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name=policy.name or 'Identify & Authorize',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'evaluatePolicy',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_authorize_user_policy(policy: AuthorizeUserPolicy) -> PolicyAction:
    """
    Normalize AuthorizeUserPolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The AuthorizeUserPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with AuthorizationConfig.
    """
    # Create structured authorization config
    config = AuthorizationConfig(
        allowed_users=policy.users,
        allowed_groups=policy.groups,
        allowed_access_profiles=policy.access_profiles,
        denied_users=None,
        denied_groups=None,
        allowed_roles=None,
        denied_roles=None,
        required_permissions=None,
        any_permissions=None,
        required_scopes=None,
        any_scopes=None,
        required_claims=None,
        allowed_ip_ranges=None,
        denied_ip_ranges=None,
        allowed_time_windows=None,
        timezone=None,
        authorization_mode="all",
        custom_authorization_expression=None,
        unauthorized_status_code=403,
        unauthorized_message=None
    )
    
    return PolicyAction(
        action_type=PolicyActionType.AUTHORIZATION,
        enabled=True,
        stage="request",
        name=policy.name or 'Authorize User',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'authorizeUser',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_log_invocation_policy(policy: LogInvocationPolicy) -> PolicyAction:
    """
    Normalize LogInvocationPolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The LogInvocationPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with LoggingConfig.
    """
    # Create structured logging config
    config = LoggingConfig(
        log_level="info",
        log_request_headers=policy.store_request_headers,
        log_request_body=policy.store_request_payload,
        log_response_headers=policy.store_response_headers,
        log_response_body=policy.store_response_payload,
        sampling_rate=1.0,
        log_to_gateway=True,
        log_to_external=False,
        external_log_endpoint=None,
        compress_logs=policy.store_as_zip
    )
    
    return PolicyAction(
        action_type=PolicyActionType.LOGGING,
        enabled=True,
        stage="request",
        name=policy.name or 'Log Invocation',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'logInvocation',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_throttle_policy(policy: ThrottlePolicy) -> PolicyAction:
    """
    Normalize ThrottlePolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The ThrottlePolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with RateLimitConfig.
    """
    # Map webMethods alert interval unit to structured config time-based limits
    limit_value = policy.throttle_rule.value
    config_kwargs = {}
    
    if policy.alert_interval_unit.value == "SECONDS":
        config_kwargs["requests_per_second"] = limit_value
    elif policy.alert_interval_unit.value == "MINUTES":
        config_kwargs["requests_per_minute"] = limit_value
    elif policy.alert_interval_unit.value == "HOURS":
        config_kwargs["requests_per_hour"] = limit_value
    elif policy.alert_interval_unit.value == "DAYS":
        config_kwargs["requests_per_day"] = limit_value
    else:
        # Default to per minute
        config_kwargs["requests_per_minute"] = limit_value
    
    # Create structured rate limit config
    config = RateLimitConfig(
        **config_kwargs,
        rate_limit_key="custom",  # webMethods uses consumer-based limiting
        enforcement_action="reject"
    )
    
    return PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        enabled=True,
        stage="request",
        name=policy.name or 'Traffic Optimization',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'throttle',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_service_result_cache_policy(policy: ServiceResultCachePolicy) -> PolicyAction:
    """
    Normalize ServiceResultCachePolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The ServiceResultCachePolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with CachingConfig.
    """
    # Get max payload size - handle both attribute names
    max_payload = 1000  # default
    if hasattr(policy, 'max_payload_size'):
        max_payload = policy.max_payload_size
    elif hasattr(policy, 'max-payload-size'):
        max_payload = getattr(policy, 'max-payload-size')
    
    # Parse TTL string (e.g., "1d", "2h", "30m") to seconds
    ttl_str = policy.ttl
    ttl_seconds = 300  # Default 5 minutes
    
    if ttl_str:
        if ttl_str.endswith('d'):
            ttl_seconds = int(ttl_str[:-1]) * 86400
        elif ttl_str.endswith('h'):
            ttl_seconds = int(ttl_str[:-1]) * 3600
        elif ttl_str.endswith('m'):
            ttl_seconds = int(ttl_str[:-1]) * 60
        elif ttl_str.endswith('s'):
            ttl_seconds = int(ttl_str[:-1])
        else:
            try:
                ttl_seconds = int(ttl_str)
            except ValueError:
                ttl_seconds = 300
    
    # Create structured caching config
    config = CachingConfig(
        ttl_seconds=ttl_seconds,
        max_ttl_seconds=None,
        cache_key_strategy="url",
        vary_headers=None,
        vary_query_params=None,
        respect_cache_control_headers=True,
        cache_methods=["GET", "HEAD"],
        cache_status_codes=[200, 203, 204, 206, 300, 301],
        max_payload_size_bytes=max_payload,
        invalidate_on_methods=["POST", "PUT", "PATCH", "DELETE"]
    )
    
    return PolicyAction(
        action_type=PolicyActionType.CACHING,
        enabled=True,
        stage="response",
        name=policy.name or 'Service Result Cache',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'serviceResultCache',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_validate_api_spec_policy(policy: ValidateAPISpecPolicy) -> PolicyAction:
    """
    Normalize ValidateAPISpecPolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The ValidateAPISpecPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with ValidationConfig.
    """
    # Create structured validation config
    config = ValidationConfig(
        validate_request_schema=policy.schema_validation_flag,
        validate_response_schema=False,
        validate_query_params=policy.validate_query_params,
        validate_path_params=policy.validate_path_params,
        validate_headers=policy.headers_validation_flag,
        validate_content_type=policy.validate_content_types,
        allowed_content_types=None,
        strict_mode=False,
        return_validation_errors=True
    )
    
    return PolicyAction(
        action_type=PolicyActionType.VALIDATION,
        enabled=True,
        stage="request",
        name=policy.name or 'Validate API Specification',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'validateAPISpec',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_request_data_masking_policy(policy: RequestDataMaskingPolicy) -> PolicyAction:
    """
    Normalize RequestDataMaskingPolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The RequestDataMaskingPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with DataMaskingConfig.
    """
    # Map webMethods masking type to structured config
    jpath_mask_type = policy.jpath_masking.masking_criteria.masking_type.value
    regex_mask_type = policy.regex_masking.masking_criteria.masking_type.value
    
    # Create masking rules
    masking_rules = []
    
    # Add JPath masking rule
    if policy.jpath_masking.masking_criteria.action:
        masking_rules.append(MaskingRule(
            field_path=policy.jpath_masking.masking_criteria.action,
            mask_type="full" if jpath_mask_type == "mask" else "remove",
            mask_character=policy.jpath_masking.masking_criteria.mask_value or "*",
            preserve_length=True,
            partial_mask_start=None,
            partial_mask_end=None
        ))
    
    # Add regex masking rule
    if policy.regex_masking.masking_criteria.action:
        masking_rules.append(MaskingRule(
            field_path=policy.regex_masking.masking_criteria.action,
            mask_type="full" if regex_mask_type == "mask" else "remove",
            mask_character=policy.regex_masking.masking_criteria.mask_value or "*",
            preserve_length=True,
            partial_mask_start=None,
            partial_mask_end=None
        ))
    
    # Create structured data masking config
    config = DataMaskingConfig(
        mask_request=True,
        mask_response=False,
        mask_logs=policy.same_for_transactional_logging,
        masking_rules=masking_rules if masking_rules else [MaskingRule(
            field_path="*",
            mask_type="full",
            mask_character="*",
            preserve_length=True,
            partial_mask_start=None,
            partial_mask_end=None
        )]
    )
    
    return PolicyAction(
        action_type=PolicyActionType.DATA_MASKING,
        enabled=True,
        stage="request",
        name=policy.name or 'Request Data Masking',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'requestDataMasking',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_response_data_masking_policy(policy: ResponseDataMaskingPolicy) -> PolicyAction:
    """
    Normalize ResponseDataMaskingPolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The ResponseDataMaskingPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with DataMaskingConfig.
    """
    # Map webMethods masking type to structured config
    jpath_mask_type = policy.jpath_masking.masking_criteria.masking_type.value
    regex_mask_type = policy.regex_masking.masking_criteria.masking_type.value
    
    # Create masking rules
    masking_rules = []
    
    # Add JPath masking rule
    if policy.jpath_masking.masking_criteria.action:
        masking_rules.append(MaskingRule(
            field_path=policy.jpath_masking.masking_criteria.action,
            mask_type="full" if jpath_mask_type == "mask" else "remove",
            mask_character=policy.jpath_masking.masking_criteria.mask_value or "*",
            preserve_length=True,
            partial_mask_start=None,
            partial_mask_end=None
        ))
    
    # Add regex masking rule
    if policy.regex_masking.masking_criteria.action:
        masking_rules.append(MaskingRule(
            field_path=policy.regex_masking.masking_criteria.action,
            mask_type="full" if regex_mask_type == "mask" else "remove",
            mask_character=policy.regex_masking.masking_criteria.mask_value or "*",
            preserve_length=True,
            partial_mask_start=None,
            partial_mask_end=None
        ))
    
    # Create structured data masking config
    config = DataMaskingConfig(
        mask_request=False,
        mask_response=True,
        mask_logs=policy.same_for_transactional_logging,
        masking_rules=masking_rules if masking_rules else [MaskingRule(
            field_path="*",
            mask_type="full",
            mask_character="*",
            preserve_length=True,
            partial_mask_start=None,
            partial_mask_end=None
        )]
    )
    
    return PolicyAction(
        action_type=PolicyActionType.DATA_MASKING,
        enabled=True,
        stage="response",
        name=policy.name or 'Response Data Masking',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'responseDataMasking',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_cors_policy(policy: CorsPolicy) -> PolicyAction:
    """
    Normalize CorsPolicy to vendor-neutral PolicyAction with structured config.

    Args:
        policy: The CorsPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object with CorsConfig.
    """
    cors_attrs = policy.cors_attributes
    
    # Create structured CORS config
    config = CorsConfig(
        allowed_origins=cors_attrs.allowed_origins,
        allowed_methods=[m.value for m in cors_attrs.allow_methods],
        allowed_headers=cors_attrs.allow_headers,
        exposed_headers=cors_attrs.expose_headers,
        allow_credentials=cors_attrs.allow_credentials,
        max_age_seconds=cors_attrs.max_age
    )
    
    return PolicyAction(
        action_type=PolicyActionType.CORS,
        enabled=True,
        stage="request",
        name=policy.name or 'CORS',
        description=policy.description,
        config=config,
        vendor_config={
            "vendor": "webmethods",
            "template_key": policy.name or 'cors',
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


# Type alias for all webMethods policy action types
WebMethodsPolicyType = Union[
    EntryProtocolPolicy,
    EvaluatePolicy,
    AuthorizeUserPolicy,
    LogInvocationPolicy,
    ThrottlePolicy,
    ServiceResultCachePolicy,
    ValidateAPISpecPolicy,
    RequestDataMaskingPolicy,
    ResponseDataMaskingPolicy,
    CorsPolicy,
]


def normalize_policy_action(policy: WebMethodsPolicyType) -> PolicyAction:
    """
    Normalize any webMethods policy action to vendor-neutral PolicyAction.

    This is a convenience function that automatically detects the policy type
    and calls the appropriate normalization function.

    Args:
        policy: Any webMethods policy action model object.

    Returns:
        Vendor-neutral PolicyAction object with structured config.

    Raises:
        ValueError: If the policy type is not supported.

    Example:
        >>> policy = EntryProtocolPolicy(protocol=Protocol.HTTPS)
        >>> action = normalize_policy_action(policy)
        >>> action.action_type
        <PolicyActionType.TLS: 'tls'>
    """
    if isinstance(policy, EntryProtocolPolicy):
        return normalize_entry_protocol_policy(policy)
    elif isinstance(policy, EvaluatePolicy):
        return normalize_evaluate_policy(policy)
    elif isinstance(policy, AuthorizeUserPolicy):
        return normalize_authorize_user_policy(policy)
    elif isinstance(policy, LogInvocationPolicy):
        return normalize_log_invocation_policy(policy)
    elif isinstance(policy, ThrottlePolicy):
        return normalize_throttle_policy(policy)
    elif isinstance(policy, ServiceResultCachePolicy):
        return normalize_service_result_cache_policy(policy)
    elif isinstance(policy, ValidateAPISpecPolicy):
        return normalize_validate_api_spec_policy(policy)
    elif isinstance(policy, RequestDataMaskingPolicy):
        return normalize_request_data_masking_policy(policy)
    elif isinstance(policy, ResponseDataMaskingPolicy):
        return normalize_response_data_masking_policy(policy)
    elif isinstance(policy, CorsPolicy):
        return normalize_cors_policy(policy)
    else:
        raise ValueError(f"Unsupported policy type: {type(policy).__name__}")

# Made with Bob