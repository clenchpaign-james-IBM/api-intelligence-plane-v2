"""
Policy Denormalizer for webMethods Gateway

Converts vendor-neutral PolicyAction back to webMethods-specific policy actions.
This is the reverse operation of policy_normalizer.py.

Enhanced to support both dict configs (backward compatibility) and structured configs.

IBM Confidential - Copyright 2024 IBM Corp.
"""

from typing import Optional, Union

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
    Protocol,
    IdentificationRule,
    LogDestination,
    ThrottleRule,
    ThrottleDestination,
    MaskingCriteria,
    JPathMasking,
    RegexMasking,
    CorsAttributes,
    HttpMethod,
    LogicalConnector,
    ApplicationLookup,
    IdentificationType,
    LogGenerationFrequency,
    DestinationType,
    MonitorRuleOperator,
    AlertIntervalUnit,
    AlertFrequency,
    MaskingType,
)


def denormalize_to_entry_protocol_policy(action: PolicyAction) -> EntryProtocolPolicy:
    """
    Denormalize vendor-neutral PolicyAction to EntryProtocolPolicy.
    
    Supports both dict configs (backward compatibility) and structured TlsConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        EntryProtocolPolicy object.

    Example:
        >>> action = PolicyAction(action_type=PolicyActionType.TLS, config=TlsConfig(enforce_tls=True))
        >>> policy = denormalize_to_entry_protocol_policy(action)
        >>> policy.protocol
        <Protocol.HTTPS: 'https'>
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return EntryProtocolPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    protocol_value = "http"
    
    if isinstance(config, TlsConfig):
        # Structured config
        protocol_value = "https" if config.enforce_tls else "http"
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        protocol_value = config.get("protocol", "http")
    
    return EntryProtocolPolicy(
        templateKey=action.vendor_config.get("template_key", "entryProtocolPolicy") if action.vendor_config else "entryProtocolPolicy",
        description=action.description,
        protocol=Protocol(protocol_value)
    )


def denormalize_to_evaluate_policy(action: PolicyAction) -> EvaluatePolicy:
    """
    Denormalize vendor-neutral PolicyAction to EvaluatePolicy.
    
    Supports both dict configs (backward compatibility) and structured AuthenticationConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        EvaluatePolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return EvaluatePolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    allow_anonymous = False
    identification_rules = []
    
    if isinstance(config, AuthenticationConfig):
        # Structured config
        allow_anonymous = config.allow_anonymous
        
        # Map auth_type back to identification type
        id_type_map = {
            "api_key": IdentificationType.API_KEY,
            "basic": IdentificationType.HTTP_BASIC_AUTH,
            "jwt": IdentificationType.JWT_CLAIMS,
            "oauth2": IdentificationType.OAUTH2_TOKEN,
        }
        id_type = id_type_map.get(config.auth_type, IdentificationType.OAUTH2_TOKEN)
        
        identification_rules.append(
            IdentificationRule(
                applicationLookup=ApplicationLookup.STRICT,
                identificationType=id_type
            )
        )
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        allow_anonymous = config.get("allow_anonymous", False)
        
        for rule_data in config.get("identification_rules", []):
            identification_rules.append(
                IdentificationRule(
                    applicationLookup=ApplicationLookup(rule_data["application_lookup"]),
                    identificationType=IdentificationType(rule_data["identification_type"])
                )
            )
    
    return EvaluatePolicy(
        templateKey=action.vendor_config.get("template_key", "evaluatePolicy") if action.vendor_config else "evaluatePolicy",
        description=action.description,
        logicalConnector=LogicalConnector.OR,
        allowAnonymous=allow_anonymous,
        triggerPolicyViolationOnMissingAuthorizationHeader=False,
        IdentificationRule=identification_rules
    )


def denormalize_to_authorize_user_policy(action: PolicyAction) -> AuthorizeUserPolicy:
    """
    Denormalize vendor-neutral PolicyAction to AuthorizeUserPolicy.
    
    Supports both dict configs (backward compatibility) and structured AuthorizationConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        AuthorizeUserPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return AuthorizeUserPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    users = ["Administrator"]
    groups = ["Administrators", "API-Gateway-Administrators"]
    access_profiles = ["Administrators"]
    
    if isinstance(config, AuthorizationConfig):
        # Structured config
        users = config.allowed_users or users
        groups = config.allowed_groups or groups
        access_profiles = config.allowed_access_profiles or access_profiles
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        users = config.get("users", users)
        groups = config.get("groups", groups)
        access_profiles = config.get("access_profiles", access_profiles)
    
    return AuthorizeUserPolicy(
        templateKey=action.vendor_config.get("template_key", "authorizeUser") if action.vendor_config else "authorizeUser",
        description=action.description,
        users=users,
        groups=groups,
        accessProfiles=access_profiles
    )


def denormalize_to_log_invocation_policy(action: PolicyAction) -> LogInvocationPolicy:
    """
    Denormalize vendor-neutral PolicyAction to LogInvocationPolicy.
    
    Supports both dict configs (backward compatibility) and structured LoggingConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        LogInvocationPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return LogInvocationPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    store_request_headers = True
    store_request_payload = True
    store_response_headers = True
    store_response_payload = True
    store_as_zip = True
    
    if isinstance(config, LoggingConfig):
        # Structured config
        store_request_headers = config.log_request_headers
        store_request_payload = config.log_request_body
        store_response_headers = config.log_response_headers
        store_response_payload = config.log_response_body
        store_as_zip = config.compress_logs
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        store_request_headers = config.get("store_request_headers", True)
        store_request_payload = config.get("store_request_payload", True)
        store_response_headers = config.get("store_response_headers", True)
        store_response_payload = config.get("store_response_payload", True)
        store_as_zip = config.get("store_as_zip", True)
    
    return LogInvocationPolicy(
        templateKey=action.vendor_config.get("template_key", "logInvocation") if action.vendor_config else "logInvocation",
        description=action.description,
        storeRequestHeaders=store_request_headers,
        storeRequestPayload=store_request_payload,
        storeResponseHeaders=store_response_headers,
        storeResponsePayload=store_response_payload,
        storeAsZip=store_as_zip,
        logGenerationFrequency=LogGenerationFrequency.ALWAYS,
        destination=LogDestination(destinationType=DestinationType.GATEWAY)
    )


def denormalize_to_throttle_policy(action: PolicyAction) -> ThrottlePolicy:
    """
    Denormalize vendor-neutral PolicyAction to ThrottlePolicy.
    
    Supports both dict configs (backward compatibility) and structured RateLimitConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ThrottlePolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ThrottlePolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    limit_value = 10
    alert_interval = 1
    alert_interval_unit = AlertIntervalUnit.MINUTES
    
    if isinstance(config, RateLimitConfig):
        # Structured config - determine which time unit is set
        if config.requests_per_second:
            limit_value = config.requests_per_second
            alert_interval_unit = AlertIntervalUnit.SECONDS
        elif config.requests_per_minute:
            limit_value = config.requests_per_minute
            alert_interval_unit = AlertIntervalUnit.MINUTES
        elif config.requests_per_hour:
            limit_value = config.requests_per_hour
            alert_interval_unit = AlertIntervalUnit.HOURS
        elif config.requests_per_day:
            limit_value = config.requests_per_day
            alert_interval_unit = AlertIntervalUnit.DAYS
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        throttle_rule_data = config.get("throttle_rule", {})
        limit_value = throttle_rule_data.get("value", 10)
        alert_interval = config.get("alert_interval", 1)
        alert_interval_unit = AlertIntervalUnit(config.get("alert_interval_unit", "minutes"))
    
    return ThrottlePolicy(
        templateKey=action.vendor_config.get("template_key", "throttle") if action.vendor_config else "throttle",
        description=action.description,
        throttleRule=ThrottleRule(
            throttleRuleName="requestCount",
            monitorRuleOperator=MonitorRuleOperator.GT,
            value=limit_value
        ),
        consumerIds=["AllConsumers"],
        consumerSpecificCounter=False,
        destination=ThrottleDestination(destinationType=DestinationType.GATEWAY),
        alertInterval=alert_interval,
        alertIntervalUnit=alert_interval_unit,
        alertFrequency=AlertFrequency.ONCE,
        alertMessage="Limit exceeded"
    )


def denormalize_to_service_result_cache_policy(action: PolicyAction) -> ServiceResultCachePolicy:
    """
    Denormalize vendor-neutral PolicyAction to ServiceResultCachePolicy.
    
    Supports both dict configs (backward compatibility) and structured CachingConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ServiceResultCachePolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ServiceResultCachePolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    ttl = "1d"
    max_payload_size = 1000
    
    if isinstance(config, CachingConfig):
        # Structured config - convert seconds back to string format
        ttl_seconds = config.ttl_seconds
        if ttl_seconds >= 86400 and ttl_seconds % 86400 == 0:
            ttl = f"{ttl_seconds // 86400}d"
        elif ttl_seconds >= 3600 and ttl_seconds % 3600 == 0:
            ttl = f"{ttl_seconds // 3600}h"
        elif ttl_seconds >= 60 and ttl_seconds % 60 == 0:
            ttl = f"{ttl_seconds // 60}m"
        else:
            ttl = f"{ttl_seconds}s"
        
        max_payload_size = config.max_payload_size_bytes or 1000
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        ttl = config.get("ttl", "1d")
        max_payload_size = config.get("max_payload_size", 1000)
    
    return ServiceResultCachePolicy(
        templateKey=action.vendor_config.get("template_key", "serviceResultCache") if action.vendor_config else "serviceResultCache",
        description=action.description,
        ttl=ttl,
        **{"max-payload-size": max_payload_size}
    )


def denormalize_to_validate_api_spec_policy(action: PolicyAction) -> ValidateAPISpecPolicy:
    """
    Denormalize vendor-neutral PolicyAction to ValidateAPISpecPolicy.
    
    Supports both dict configs (backward compatibility) and structured ValidationConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ValidateAPISpecPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ValidateAPISpecPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    schema_validation = False
    validate_query_params = True
    validate_path_params = False
    validate_cookie_params = False
    validate_content_types = False
    headers_validation = False
    
    if isinstance(config, ValidationConfig):
        # Structured config
        schema_validation = config.validate_request_schema
        validate_query_params = config.validate_query_params
        validate_path_params = config.validate_path_params
        headers_validation = config.validate_headers
        validate_content_types = config.validate_content_type
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        schema_validation = config.get("schema_validation", False)
        validate_query_params = config.get("validate_query_params", True)
        validate_path_params = config.get("validate_path_params", False)
        validate_cookie_params = config.get("validate_cookie_params", False)
        validate_content_types = config.get("validate_content_types", False)
        headers_validation = config.get("validate_headers", False)
    
    return ValidateAPISpecPolicy(
        templateKey=action.vendor_config.get("template_key", "validateAPISpec") if action.vendor_config else "validateAPISpec",
        description=action.description,
        schemaValidationFlag=schema_validation,
        validateQueryParams=validate_query_params,
        validatePathParams=validate_path_params,
        validateCookieParams=validate_cookie_params,
        validateContentTypes=validate_content_types,
        headersValidationFlag=headers_validation
    )


def denormalize_to_request_data_masking_policy(action: PolicyAction) -> RequestDataMaskingPolicy:
    """
    Denormalize vendor-neutral PolicyAction to RequestDataMaskingPolicy.
    
    Supports both dict configs (backward compatibility) and structured DataMaskingConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        RequestDataMaskingPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return RequestDataMaskingPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    jpath_action = "SOME_STRING"
    jpath_masking_type = MaskingType.MASK
    jpath_mask_value = "********"
    regex_action = "SOME_STRING"
    regex_masking_type = MaskingType.MASK
    regex_mask_value = "********"
    same_for_logging = True
    
    if isinstance(config, DataMaskingConfig):
        # Structured config
        if config.masking_rules:
            # Use first rule for jpath, second for regex (if available)
            first_rule = config.masking_rules[0]
            jpath_action = first_rule.field_path
            jpath_masking_type = MaskingType.MASK if first_rule.mask_type == "full" else MaskingType.REMOVE
            jpath_mask_value = first_rule.mask_character
            
            if len(config.masking_rules) > 1:
                second_rule = config.masking_rules[1]
                regex_action = second_rule.field_path
                regex_masking_type = MaskingType.MASK if second_rule.mask_type == "full" else MaskingType.REMOVE
                regex_mask_value = second_rule.mask_character
        
        same_for_logging = config.mask_logs
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        jpath_data = config.get("jpath_masking", {})
        regex_data = config.get("regex_masking", {})
        
        jpath_action = jpath_data.get("action", "SOME_STRING")
        jpath_masking_type = MaskingType(jpath_data.get("masking_type", "mask"))
        jpath_mask_value = jpath_data.get("mask_value", "********")
        
        regex_action = regex_data.get("action", "SOME_STRING")
        regex_masking_type = MaskingType(regex_data.get("masking_type", "mask"))
        regex_mask_value = regex_data.get("mask_value", "********")
        
        same_for_logging = config.get("same_for_transactional_logging", True)
    
    return RequestDataMaskingPolicy(
        templateKey=action.vendor_config.get("template_key", "requestDataMasking") if action.vendor_config else "requestDataMasking",
        description=action.description,
        jpathMasking=JPathMasking(
            maskingCriteria=MaskingCriteria(
                action=jpath_action,
                maskingType=jpath_masking_type,
                maskValue=jpath_mask_value
            )
        ),
        regexMasking=RegexMasking(
            maskingCriteria=MaskingCriteria(
                action=regex_action,
                maskingType=regex_masking_type,
                maskValue=regex_mask_value
            )
        ),
        sameForTransactionalLogging=same_for_logging,
        applyForPayload=True
    )


def denormalize_to_response_data_masking_policy(action: PolicyAction) -> ResponseDataMaskingPolicy:
    """
    Denormalize vendor-neutral PolicyAction to ResponseDataMaskingPolicy.
    
    Supports both dict configs (backward compatibility) and structured DataMaskingConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ResponseDataMaskingPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ResponseDataMaskingPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    jpath_action = "SOME_STRING"
    jpath_masking_type = MaskingType.MASK
    jpath_mask_value = "********"
    regex_action = "SOME_STRING"
    regex_masking_type = MaskingType.MASK
    regex_mask_value = "********"
    same_for_logging = True
    
    if isinstance(config, DataMaskingConfig):
        # Structured config
        if config.masking_rules:
            # Use first rule for jpath, second for regex (if available)
            first_rule = config.masking_rules[0]
            jpath_action = first_rule.field_path
            jpath_masking_type = MaskingType.MASK if first_rule.mask_type == "full" else MaskingType.REMOVE
            jpath_mask_value = first_rule.mask_character
            
            if len(config.masking_rules) > 1:
                second_rule = config.masking_rules[1]
                regex_action = second_rule.field_path
                regex_masking_type = MaskingType.MASK if second_rule.mask_type == "full" else MaskingType.REMOVE
                regex_mask_value = second_rule.mask_character
        
        same_for_logging = config.mask_logs
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        jpath_data = config.get("jpath_masking", {})
        regex_data = config.get("regex_masking", {})
        
        jpath_action = jpath_data.get("action", "SOME_STRING")
        jpath_masking_type = MaskingType(jpath_data.get("masking_type", "mask"))
        jpath_mask_value = jpath_data.get("mask_value", "********")
        
        regex_action = regex_data.get("action", "SOME_STRING")
        regex_masking_type = MaskingType(regex_data.get("masking_type", "mask"))
        regex_mask_value = regex_data.get("mask_value", "********")
        
        same_for_logging = config.get("same_for_transactional_logging", True)
    
    return ResponseDataMaskingPolicy(
        templateKey=action.vendor_config.get("template_key", "responseDataMasking") if action.vendor_config else "responseDataMasking",
        description=action.description,
        jpathMasking=JPathMasking(
            maskingCriteria=MaskingCriteria(
                action=jpath_action,
                maskingType=jpath_masking_type,
                maskValue=jpath_mask_value
            )
        ),
        regexMasking=RegexMasking(
            maskingCriteria=MaskingCriteria(
                action=regex_action,
                maskingType=regex_masking_type,
                maskValue=regex_mask_value
            )
        ),
        sameForTransactionalLogging=same_for_logging,
        applyForPayload=True
    )


def denormalize_to_cors_policy(action: PolicyAction) -> CorsPolicy:
    """
    Denormalize vendor-neutral PolicyAction to CorsPolicy.
    
    Supports both dict configs (backward compatibility) and structured CorsConfig.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        CorsPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return CorsPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config (support both dict and structured)
    config = action.config
    allowed_origins = ["*"]
    allow_headers = ["*"]
    expose_headers = []
    allow_credentials = False
    allow_methods = [HttpMethod.GET, HttpMethod.POST, HttpMethod.PUT, HttpMethod.DELETE, HttpMethod.PATCH, HttpMethod.HEAD]
    max_age = 10
    
    if isinstance(config, CorsConfig):
        # Structured config
        allowed_origins = config.allowed_origins
        allow_headers = config.allowed_headers
        expose_headers = config.exposed_headers or []
        allow_credentials = config.allow_credentials
        allow_methods = [HttpMethod(m) for m in config.allowed_methods]
        max_age = config.max_age_seconds or 10
    elif isinstance(config, dict):
        # Dict config (backward compatibility)
        allowed_origins = config.get("allowed_origins", ["*"])
        allow_headers = config.get("allow_headers", ["*"])
        expose_headers = config.get("expose_headers", [])
        allow_credentials = config.get("allow_credentials", False)
        allow_methods = [HttpMethod(m) for m in config.get("allow_methods", ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])]
        max_age = config.get("max_age", 10)
    
    return CorsPolicy(
        templateKey=action.vendor_config.get("template_key", "cors") if action.vendor_config else "cors",
        description=action.description,
        corsAttributes=CorsAttributes(
            allowedOrigins=allowed_origins,
            allowHeaders=allow_headers,
            exposeHeaders=expose_headers,
            allowCredentials=allow_credentials,
            allowMethods=allow_methods,
            maxAge=max_age
        )
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


def denormalize_policy_action(action: PolicyAction) -> WebMethodsPolicyType:
    """
    Denormalize vendor-neutral PolicyAction to appropriate webMethods policy.

    This function automatically detects the policy type from the action_type
    or vendor_config and calls the appropriate denormalization function.
    
    Supports both dict configs (backward compatibility) and structured configs.

    Args:
        action: Vendor-neutral PolicyAction object.

    Returns:
        Specific webMethods policy action model object.

    Raises:
        ValueError: If the policy type cannot be determined or is not supported.

    Example:
        >>> action = PolicyAction(action_type=PolicyActionType.TLS, config=TlsConfig(enforce_tls=True))
        >>> policy = denormalize_policy_action(action)
        >>> isinstance(policy, EntryProtocolPolicy)
        True
    """
    # First try to determine from vendor_config template_key
    if action.vendor_config and "template_key" in action.vendor_config:
        template_key = action.vendor_config["template_key"]
        
        if template_key == "entryProtocolPolicy":
            return denormalize_to_entry_protocol_policy(action)
        elif template_key == "evaluatePolicy":
            return denormalize_to_evaluate_policy(action)
        elif template_key == "authorizeUser":
            return denormalize_to_authorize_user_policy(action)
        elif template_key == "logInvocation":
            return denormalize_to_log_invocation_policy(action)
        elif template_key == "throttle":
            return denormalize_to_throttle_policy(action)
        elif template_key == "serviceResultCache":
            return denormalize_to_service_result_cache_policy(action)
        elif template_key == "validateAPISpec":
            return denormalize_to_validate_api_spec_policy(action)
        elif template_key == "requestDataMasking":
            return denormalize_to_request_data_masking_policy(action)
        elif template_key == "responseDataMasking":
            return denormalize_to_response_data_masking_policy(action)
        elif template_key == "cors":
            return denormalize_to_cors_policy(action)
    
    # Fall back to action_type mapping
    action_type_map = {
        PolicyActionType.TLS: denormalize_to_entry_protocol_policy,
        PolicyActionType.AUTHENTICATION: denormalize_to_evaluate_policy,
        PolicyActionType.AUTHORIZATION: denormalize_to_authorize_user_policy,
        PolicyActionType.LOGGING: denormalize_to_log_invocation_policy,
        PolicyActionType.RATE_LIMITING: denormalize_to_throttle_policy,
        PolicyActionType.CACHING: denormalize_to_service_result_cache_policy,
        PolicyActionType.VALIDATION: denormalize_to_validate_api_spec_policy,
        PolicyActionType.CORS: denormalize_to_cors_policy,
    }
    
    # Special handling for DATA_MASKING based on stage
    if action.action_type == PolicyActionType.DATA_MASKING:
        if action.stage == "response":
            return denormalize_to_response_data_masking_policy(action)
        else:
            return denormalize_to_request_data_masking_policy(action)
    
    denormalizer = action_type_map.get(action.action_type)
    if denormalizer:
        return denormalizer(action)
    
    raise ValueError(f"Unsupported policy action type: {action.action_type}")

# Made with Bob