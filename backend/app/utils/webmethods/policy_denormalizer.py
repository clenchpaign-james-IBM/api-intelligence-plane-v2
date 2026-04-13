"""
Utility module for denormalizing vendor-neutral PolicyAction to webMethods policies.

This module provides conversion functions to transform vendor-neutral PolicyAction
format back into webMethods-specific policy action models (EntryProtocolPolicy,
EvaluatePolicy, etc.).

This is the reverse operation of policy_normalizer.py.

IBM Confidential - Copyright 2024 IBM Corp.
"""

from typing import Optional, Union

from ...models.base.api import PolicyAction, PolicyActionType
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

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        EntryProtocolPolicy object.

    Example:
        >>> action = PolicyAction(action_type=PolicyActionType.TLS, config={"protocol": "https"})
        >>> policy = denormalize_to_entry_protocol_policy(action)
        >>> policy.protocol
        <Protocol.HTTPS: 'https'>
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return EntryProtocolPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    protocol_value = config.get("protocol", "http")
    
    return EntryProtocolPolicy(
        templateKey=action.vendor_config.get("template_key", "entryProtocolPolicy") if action.vendor_config else "entryProtocolPolicy",
        description=action.description,
        protocol=Protocol(protocol_value)
    )


def denormalize_to_evaluate_policy(action: PolicyAction) -> EvaluatePolicy:
    """
    Denormalize vendor-neutral PolicyAction to EvaluatePolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        EvaluatePolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return EvaluatePolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    
    # Reconstruct identification rules
    identification_rules = []
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
        logicalConnector=LogicalConnector(config.get("logical_connector", "OR")),
        allowAnonymous=config.get("allow_anonymous", False),
        triggerPolicyViolationOnMissingAuthorizationHeader=config.get(
            "trigger_policy_violation_on_missing_authorization_header", False
        ),
        IdentificationRule=identification_rules
    )


def denormalize_to_authorize_user_policy(action: PolicyAction) -> AuthorizeUserPolicy:
    """
    Denormalize vendor-neutral PolicyAction to AuthorizeUserPolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        AuthorizeUserPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return AuthorizeUserPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    
    return AuthorizeUserPolicy(
        templateKey=action.vendor_config.get("template_key", "authorizeUser") if action.vendor_config else "authorizeUser",
        description=action.description,
        users=config.get("users", ["Administrator"]),
        groups=config.get("groups", ["Administrators", "API-Gateway-Administrators"]),
        accessProfiles=config.get("access_profiles", ["Administrators"])
    )


def denormalize_to_log_invocation_policy(action: PolicyAction) -> LogInvocationPolicy:
    """
    Denormalize vendor-neutral PolicyAction to LogInvocationPolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        LogInvocationPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return LogInvocationPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    
    return LogInvocationPolicy(
        templateKey=action.vendor_config.get("template_key", "logInvocation") if action.vendor_config else "logInvocation",
        description=action.description,
        storeRequestHeaders=config.get("store_request_headers", True),
        storeRequestPayload=config.get("store_request_payload", True),
        storeResponseHeaders=config.get("store_response_headers", True),
        storeResponsePayload=config.get("store_response_payload", True),
        storeAsZip=config.get("store_as_zip", True),
        logGenerationFrequency=LogGenerationFrequency(config.get("log_generation_frequency", "Always")),
        destination=LogDestination(
            destinationType=DestinationType(config.get("destination_type", "GATEWAY"))
        )
    )


def denormalize_to_throttle_policy(action: PolicyAction) -> ThrottlePolicy:
    """
    Denormalize vendor-neutral PolicyAction to ThrottlePolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ThrottlePolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ThrottlePolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    throttle_rule_data = config.get("throttle_rule", {})
    
    return ThrottlePolicy(
        templateKey=action.vendor_config.get("template_key", "throttle") if action.vendor_config else "throttle",
        description=action.description,
        throttleRule=ThrottleRule(
            throttleRuleName=throttle_rule_data.get("name", "requestCount"),
            monitorRuleOperator=MonitorRuleOperator(throttle_rule_data.get("operator", "GT")),
            value=throttle_rule_data.get("value", 10)
        ),
        consumerIds=config.get("consumer_ids", ["AllConsumers"]),
        consumerSpecificCounter=config.get("consumer_specific_counter", False),
        destination=ThrottleDestination(
            destinationType=DestinationType(config.get("destination_type", "GATEWAY"))
        ),
        alertInterval=config.get("alert_interval", 1),
        alertIntervalUnit=AlertIntervalUnit(config.get("alert_interval_unit", "minutes")),
        alertFrequency=AlertFrequency(config.get("alert_frequency", "once")),
        alertMessage=config.get("alert_message", "Limit exceeded")
    )


def denormalize_to_service_result_cache_policy(action: PolicyAction) -> ServiceResultCachePolicy:
    """
    Denormalize vendor-neutral PolicyAction to ServiceResultCachePolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ServiceResultCachePolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ServiceResultCachePolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    
    return ServiceResultCachePolicy(
        templateKey=action.vendor_config.get("template_key", "serviceResultCache") if action.vendor_config else "serviceResultCache",
        description=action.description,
        ttl=config.get("ttl", "1d"),
        **{"max-payload-size": config.get("max_payload_size", 1000)}
    )


def denormalize_to_validate_api_spec_policy(action: PolicyAction) -> ValidateAPISpecPolicy:
    """
    Denormalize vendor-neutral PolicyAction to ValidateAPISpecPolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ValidateAPISpecPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ValidateAPISpecPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    
    return ValidateAPISpecPolicy(
        templateKey=action.vendor_config.get("template_key", "validateAPISpec") if action.vendor_config else "validateAPISpec",
        description=action.description,
        schemaValidationFlag=config.get("schema_validation", False),
        validateQueryParams=config.get("validate_query_params", True),
        validatePathParams=config.get("validate_path_params", False),
        validateCookieParams=config.get("validate_cookie_params", False),
        validateContentTypes=config.get("validate_content_types", False),
        headersValidationFlag=config.get("validate_headers", False)
    )


def denormalize_to_request_data_masking_policy(action: PolicyAction) -> RequestDataMaskingPolicy:
    """
    Denormalize vendor-neutral PolicyAction to RequestDataMaskingPolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        RequestDataMaskingPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return RequestDataMaskingPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    jpath_data = config.get("jpath_masking", {})
    regex_data = config.get("regex_masking", {})
    
    return RequestDataMaskingPolicy(
        templateKey=action.vendor_config.get("template_key", "requestDataMasking") if action.vendor_config else "requestDataMasking",
        description=action.description,
        jpathMasking=JPathMasking(
            maskingCriteria=MaskingCriteria(
                action=jpath_data.get("action", "SOME_STRING"),
                maskingType=MaskingType(jpath_data.get("masking_type", "mask")),
                maskValue=jpath_data.get("mask_value", "********")
            )
        ),
        regexMasking=RegexMasking(
            maskingCriteria=MaskingCriteria(
                action=regex_data.get("action", "SOME_STRING"),
                maskingType=MaskingType(regex_data.get("masking_type", "mask")),
                maskValue=regex_data.get("mask_value", "********")
            )
        ),
        sameForTransactionalLogging=config.get("same_for_transactional_logging", True),
        applyForPayload=config.get("apply_for_payload", True)
    )


def denormalize_to_response_data_masking_policy(action: PolicyAction) -> ResponseDataMaskingPolicy:
    """
    Denormalize vendor-neutral PolicyAction to ResponseDataMaskingPolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        ResponseDataMaskingPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return ResponseDataMaskingPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    jpath_data = config.get("jpath_masking", {})
    regex_data = config.get("regex_masking", {})
    
    return ResponseDataMaskingPolicy(
        templateKey=action.vendor_config.get("template_key", "responseDataMasking") if action.vendor_config else "responseDataMasking",
        description=action.description,
        jpathMasking=JPathMasking(
            maskingCriteria=MaskingCriteria(
                action=jpath_data.get("action", "SOME_STRING"),
                maskingType=MaskingType(jpath_data.get("masking_type", "mask")),
                maskValue=jpath_data.get("mask_value", "********")
            )
        ),
        regexMasking=RegexMasking(
            maskingCriteria=MaskingCriteria(
                action=regex_data.get("action", "SOME_STRING"),
                maskingType=MaskingType(regex_data.get("masking_type", "mask")),
                maskValue=regex_data.get("mask_value", "********")
            )
        ),
        sameForTransactionalLogging=config.get("same_for_transactional_logging", True),
        applyForPayload=config.get("apply_for_payload", True)
    )


def denormalize_to_cors_policy(action: PolicyAction) -> CorsPolicy:
    """
    Denormalize vendor-neutral PolicyAction to CorsPolicy.

    Args:
        action: The vendor-neutral PolicyAction object.

    Returns:
        CorsPolicy object.
    """
    # Try to use original policy from vendor_config if available
    if action.vendor_config and "original_policy" in action.vendor_config:
        return CorsPolicy(**action.vendor_config["original_policy"])
    
    # Otherwise reconstruct from config
    config = action.config or {}
    
    return CorsPolicy(
        templateKey=action.vendor_config.get("template_key", "cors") if action.vendor_config else "cors",
        description=action.description,
        corsAttributes=CorsAttributes(
            allowedOrigins=config.get("allowed_origins", ["*"]),
            allowHeaders=config.get("allow_headers", ["*"]),
            exposeHeaders=config.get("expose_headers", []),
            allowCredentials=config.get("allow_credentials", False),
            allowMethods=[HttpMethod(m) for m in config.get("allow_methods", ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])],
            maxAge=config.get("max_age", 10)
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

    Args:
        action: Vendor-neutral PolicyAction object.

    Returns:
        Specific webMethods policy action model object.

    Raises:
        ValueError: If the policy type cannot be determined or is not supported.

    Example:
        >>> action = PolicyAction(action_type=PolicyActionType.TLS, config={"protocol": "https"})
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