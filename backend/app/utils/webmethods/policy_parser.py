"""
Utility module for parsing PolicyAction format back to specific policy action models.

This module provides conversion functions to transform the generic PolicyAction
format used by the API Gateway back into specific policy action models
(EntryProtocolPolicy, EvaluatePolicy, etc.).

This is the reverse operation of policy_converter.py.

IBM Confidential - Copyright 2024 IBM Corp.
"""

from typing import Any, Dict, List, Optional, Union

from ...models.webmethods.wm_policy import (
    PolicyAction,
    PolicyActionParameter,
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


def _get_parameter_value(
    parameters: Optional[List[PolicyActionParameter]],
    template_key: str,
    default: Any = None
) -> Any:
    """
    Extract a parameter value by template key.

    Args:
        parameters: List of PolicyActionParameter objects.
        template_key: The template key to search for.
        default: Default value if parameter not found.

    Returns:
        The parameter value or default if not found.
    """
    if not parameters:
        return default
    
    for param in parameters:
        param_key = getattr(param, 'template_key', None) or getattr(param, 'templateKey', None)
        if param_key == template_key:
            if param.values and len(param.values) > 0:
                return param.values[0]
            return default
    
    return default


def _get_parameter_values(
    parameters: Optional[List[PolicyActionParameter]],
    template_key: str,
    default: Optional[List[str]] = None
) -> List[str]:
    """
    Extract parameter values list by template key.

    Args:
        parameters: List of PolicyActionParameter objects.
        template_key: The template key to search for.
        default: Default value if parameter not found.

    Returns:
        The parameter values list or default if not found.
    """
    if not parameters:
        return default or []
    
    for param in parameters:
        param_key = getattr(param, 'template_key', None) or getattr(param, 'templateKey', None)
        if param_key == template_key:
            return param.values or []
    
    return default or []


def _get_nested_parameters(
    parameters: Optional[List[PolicyActionParameter]],
    template_key: str
) -> Optional[List[PolicyActionParameter]]:
    """
    Extract nested parameters by template key.

    Args:
        parameters: List of PolicyActionParameter objects.
        template_key: The template key to search for.

    Returns:
        The nested parameters or None if not found.
    """
    if not parameters:
        return None
    
    for param in parameters:
        param_key = getattr(param, 'template_key', None) or getattr(param, 'templateKey', None)
        if param_key == template_key:
            return param.parameters
    
    return None


def parse_entry_protocol_policy(action: PolicyAction) -> EntryProtocolPolicy:
    """
    Parse PolicyAction to EntryProtocolPolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        EntryProtocolPolicy object.

    Example:
        >>> action = PolicyAction(templateKey="entryProtocolPolicy", ...)
        >>> policy = parse_entry_protocol_policy(action)
        >>> policy.protocol
        <Protocol.HTTPS: 'https'>
    """
    protocol_value = _get_parameter_value(action.parameters, "protocol", Protocol.HTTP.value)
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return EntryProtocolPolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'entryProtocolPolicy'),
        description=description,
        protocol=Protocol(protocol_value)
    )


def parse_evaluate_policy(action: PolicyAction) -> EvaluatePolicy:
    """
    Parse PolicyAction to EvaluatePolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        EvaluatePolicy object.
    """
    logical_connector_value = _get_parameter_value(
        action.parameters, "logicalConnector", LogicalConnector.OR.value
    )
    allow_anonymous_value = _get_parameter_value(action.parameters, "allowAnonymous", "false")
    trigger_violation_value = _get_parameter_value(
        action.parameters,
        "triggerPolicyViolationOnMissingAuthorizationHeader",
        "false"
    )
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    # Extract identification rules
    identification_rules = []
    if action.parameters:
        for param in action.parameters:
            if param.template_key == "IdentificationRule" and param.parameters:
                app_lookup_value = _get_parameter_value(
                    param.parameters, "applicationLookup", ApplicationLookup.STRICT.value
                )
                id_type_value = _get_parameter_value(
                    param.parameters, "identificationType", IdentificationType.API_KEY.value
                )
                
                identification_rules.append(
                    IdentificationRule(
                        applicationLookup=ApplicationLookup(app_lookup_value),
                        identificationType=IdentificationType(id_type_value)
                    )
                )
    
    return EvaluatePolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'evaluatePolicy'),
        description=description,
        logicalConnector=LogicalConnector(logical_connector_value),
        allowAnonymous=allow_anonymous_value.lower() == "true",
        triggerPolicyViolationOnMissingAuthorizationHeader=trigger_violation_value.lower() == "true",
        IdentificationRule=identification_rules
    )


def parse_authorize_user_policy(action: PolicyAction) -> AuthorizeUserPolicy:
    """
    Parse PolicyAction to AuthorizeUserPolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        AuthorizeUserPolicy object.
    """
    users = _get_parameter_values(action.parameters, "users", ["Administrator"])
    groups = _get_parameter_values(
        action.parameters, "groups", ["Administrators", "API-Gateway-Administrators"]
    )
    access_profiles = _get_parameter_values(action.parameters, "accessProfiles", ["Administrators"])
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return AuthorizeUserPolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'authorizeUser'),
        description=description,
        users=users,
        groups=groups,
        accessProfiles=access_profiles
    )


def parse_log_invocation_policy(action: PolicyAction) -> LogInvocationPolicy:
    """
    Parse PolicyAction to LogInvocationPolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        LogInvocationPolicy object.
    """
    store_request_headers = _get_parameter_value(action.parameters, "storeRequestHeaders", "true")
    store_request_payload = _get_parameter_value(action.parameters, "storeRequestPayload", "true")
    store_response_headers = _get_parameter_value(action.parameters, "storeResponseHeaders", "true")
    store_response_payload = _get_parameter_value(action.parameters, "storeResponsePayload", "true")
    store_as_zip = _get_parameter_value(action.parameters, "storeAsZip", "true")
    log_gen_freq = _get_parameter_value(
        action.parameters, "logGenerationFrequency", LogGenerationFrequency.ALWAYS.value
    )
    
    # Extract destination
    dest_params = _get_nested_parameters(action.parameters, "destination")
    dest_type_value = _get_parameter_value(dest_params, "destinationType", DestinationType.GATEWAY.value)
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return LogInvocationPolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'logInvocation'),
        description=description,
        storeRequestHeaders=store_request_headers.lower() == "true",
        storeRequestPayload=store_request_payload.lower() == "true",
        storeResponseHeaders=store_response_headers.lower() == "true",
        storeResponsePayload=store_response_payload.lower() == "true",
        storeAsZip=store_as_zip.lower() == "true",
        logGenerationFrequency=LogGenerationFrequency(log_gen_freq),
        destination=LogDestination(destinationType=DestinationType(dest_type_value))
    )


def parse_throttle_policy(action: PolicyAction) -> ThrottlePolicy:
    """
    Parse PolicyAction to ThrottlePolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        ThrottlePolicy object.
    """
    # Extract throttle rule
    throttle_rule_params = _get_nested_parameters(action.parameters, "throttleRule")
    rule_name = _get_parameter_value(throttle_rule_params, "throttleRuleName", "requestCount")
    operator_value = _get_parameter_value(
        throttle_rule_params, "monitorRuleOperator", MonitorRuleOperator.GT.value
    )
    value = int(_get_parameter_value(throttle_rule_params, "value", "10"))
    
    consumer_ids = _get_parameter_values(action.parameters, "consumerIds", ["AllConsumers"])
    consumer_specific = _get_parameter_value(action.parameters, "consumerSpecificCounter", "false")
    
    # Extract destination
    dest_params = _get_nested_parameters(action.parameters, "destination")
    dest_type_value = _get_parameter_value(dest_params, "destinationType", DestinationType.GATEWAY.value)
    
    alert_interval = int(_get_parameter_value(action.parameters, "alertInterval", "1"))
    alert_interval_unit_value = _get_parameter_value(
        action.parameters, "alertIntervalUnit", AlertIntervalUnit.MINUTES.value
    )
    alert_frequency_value = _get_parameter_value(
        action.parameters, "alertFrequency", AlertFrequency.ONCE.value
    )
    alert_message = _get_parameter_value(action.parameters, "alertMessage", "Limit exceeded")
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return ThrottlePolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'throttle'),
        description=description,
        throttleRule=ThrottleRule(
            throttleRuleName=rule_name,
            monitorRuleOperator=MonitorRuleOperator(operator_value),
            value=value
        ),
        consumerIds=consumer_ids,
        consumerSpecificCounter=consumer_specific.lower() == "true",
        destination=ThrottleDestination(destinationType=DestinationType(dest_type_value)),
        alertInterval=alert_interval,
        alertIntervalUnit=AlertIntervalUnit(alert_interval_unit_value),
        alertFrequency=AlertFrequency(alert_frequency_value),
        alertMessage=alert_message
    )


def parse_service_result_cache_policy(action: PolicyAction) -> ServiceResultCachePolicy:
    """
    Parse PolicyAction to ServiceResultCachePolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        ServiceResultCachePolicy object.
    """
    ttl = _get_parameter_value(action.parameters, "ttl", "1d")
    max_payload_size = int(_get_parameter_value(action.parameters, "max-payload-size", "1000"))
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return ServiceResultCachePolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'serviceResultCache'),
        description=description,
        ttl=ttl,
        **{"max-payload-size": max_payload_size}
    )


def parse_validate_api_spec_policy(action: PolicyAction) -> ValidateAPISpecPolicy:
    """
    Parse PolicyAction to ValidateAPISpecPolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        ValidateAPISpecPolicy object.
    """
    schema_validation = _get_parameter_value(action.parameters, "schemaValidationFlag", "false")
    validate_query = _get_parameter_value(action.parameters, "validateQueryParams", "true")
    validate_path = _get_parameter_value(action.parameters, "validatePathParams", "false")
    validate_cookie = _get_parameter_value(action.parameters, "validateCookieParams", "false")
    validate_content = _get_parameter_value(action.parameters, "validateContentTypes", "false")
    headers_validation = _get_parameter_value(action.parameters, "headersValidationFlag", "false")
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return ValidateAPISpecPolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'validateAPISpec'),
        description=description,
        schemaValidationFlag=schema_validation.lower() == "true",
        validateQueryParams=validate_query.lower() == "true",
        validatePathParams=validate_path.lower() == "true",
        validateCookieParams=validate_cookie.lower() == "true",
        validateContentTypes=validate_content.lower() == "true",
        headersValidationFlag=headers_validation.lower() == "true"
    )


def _parse_masking_criteria(params: Optional[List[PolicyActionParameter]]) -> MaskingCriteria:
    """Helper to parse MaskingCriteria from parameters."""
    action_value = _get_parameter_value(params, "action", "SOME_STRING")
    masking_type_value = _get_parameter_value(params, "maskingType", MaskingType.MASK.value)
    mask_value = _get_parameter_value(params, "maskValue", "********")
    
    return MaskingCriteria(
        action=action_value,
        maskingType=MaskingType(masking_type_value),
        maskValue=mask_value
    )


def parse_request_data_masking_policy(action: PolicyAction) -> RequestDataMaskingPolicy:
    """
    Parse PolicyAction to RequestDataMaskingPolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        RequestDataMaskingPolicy object.
    """
    # Extract jpath masking
    jpath_params = _get_nested_parameters(action.parameters, "jpathMasking")
    jpath_criteria_params = _get_nested_parameters(jpath_params, "maskingCriteria")
    jpath_criteria = _parse_masking_criteria(jpath_criteria_params)
    
    # Extract regex masking
    regex_params = _get_nested_parameters(action.parameters, "regexMasking")
    regex_criteria_params = _get_nested_parameters(regex_params, "maskingCriteria")
    regex_criteria = _parse_masking_criteria(regex_criteria_params)
    
    same_for_logging = _get_parameter_value(action.parameters, "sameForTransactionalLogging", "true")
    apply_for_payload = _get_parameter_value(action.parameters, "applyForPayload", "true")
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return RequestDataMaskingPolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'requestDataMasking'),
        description=description,
        jpathMasking=JPathMasking(maskingCriteria=jpath_criteria),
        regexMasking=RegexMasking(maskingCriteria=regex_criteria),
        sameForTransactionalLogging=same_for_logging.lower() == "true",
        applyForPayload=apply_for_payload.lower() == "true"
    )


def parse_response_data_masking_policy(action: PolicyAction) -> ResponseDataMaskingPolicy:
    """
    Parse PolicyAction to ResponseDataMaskingPolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        ResponseDataMaskingPolicy object.
    """
    # Extract jpath masking
    jpath_params = _get_nested_parameters(action.parameters, "jpathMasking")
    jpath_criteria_params = _get_nested_parameters(jpath_params, "maskingCriteria")
    jpath_criteria = _parse_masking_criteria(jpath_criteria_params)
    
    # Extract regex masking
    regex_params = _get_nested_parameters(action.parameters, "regexMasking")
    regex_criteria_params = _get_nested_parameters(regex_params, "maskingCriteria")
    regex_criteria = _parse_masking_criteria(regex_criteria_params)
    
    same_for_logging = _get_parameter_value(action.parameters, "sameForTransactionalLogging", "true")
    apply_for_payload = _get_parameter_value(action.parameters, "applyForPayload", "true")
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return ResponseDataMaskingPolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'responseDataMasking'),
        description=description,
        jpathMasking=JPathMasking(maskingCriteria=jpath_criteria),
        regexMasking=RegexMasking(maskingCriteria=regex_criteria),
        sameForTransactionalLogging=same_for_logging.lower() == "true",
        applyForPayload=apply_for_payload.lower() == "true"
    )


def parse_cors_policy(action: PolicyAction) -> CorsPolicy:
    """
    Parse PolicyAction to CorsPolicy.

    Args:
        action: The PolicyAction object to parse.

    Returns:
        CorsPolicy object.
    """
    # Extract CORS attributes
    cors_params = _get_nested_parameters(action.parameters, "corsAttributes")
    
    allowed_origins = _get_parameter_values(cors_params, "allowedOrigins", ["*"])
    allow_headers = _get_parameter_values(cors_params, "allowHeaders", ["*"])
    expose_headers = _get_parameter_values(cors_params, "exposeHeaders", [])
    allow_credentials = _get_parameter_value(cors_params, "allowCredentials", "false")
    allow_methods_values = _get_parameter_values(
        cors_params, "allowMethods",
        [m.value for m in [HttpMethod.GET, HttpMethod.POST, HttpMethod.PUT, 
                           HttpMethod.DELETE, HttpMethod.PATCH, HttpMethod.HEAD]]
    )
    max_age = int(_get_parameter_value(cors_params, "maxAge", "10"))
    
    description = None
    if action.names and len(action.names) > 0:
        description = action.names[0].value
    
    return CorsPolicy(
        templateKey=getattr(action, 'template_key', None) or getattr(action, 'templateKey', 'cors'),
        description=description,
        corsAttributes=CorsAttributes(
            allowedOrigins=allowed_origins,
            allowHeaders=allow_headers,
            exposeHeaders=expose_headers,
            allowCredentials=allow_credentials.lower() == "true",
            allowMethods=[HttpMethod(m) for m in allow_methods_values],
            maxAge=max_age
        )
    )


# Type alias for all policy action types
PolicyActionType = Union[
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


def parse_policy_action(action: PolicyAction) -> PolicyActionType:
    """
    Parse PolicyAction to the appropriate specific policy type.

    This is a convenience function that automatically detects the policy type
    from the templateKey and calls the appropriate parsing function.

    Args:
        action: PolicyAction object to parse.

    Returns:
        Specific policy action model object.

    Raises:
        ValueError: If the policy type is not supported.

    Example:
        >>> action = PolicyAction(templateKey="entryProtocolPolicy", ...)
        >>> policy = parse_policy_action(action)
        >>> isinstance(policy, EntryProtocolPolicy)
        True
    """
    template_key = getattr(action, 'template_key', None) or getattr(action, 'templateKey', None)
    
    if not template_key:
        raise ValueError("PolicyAction must have a templateKey")
    
    if template_key == "entryProtocolPolicy":
        return parse_entry_protocol_policy(action)
    elif template_key == "evaluatePolicy":
        return parse_evaluate_policy(action)
    elif template_key == "authorizeUser":
        return parse_authorize_user_policy(action)
    elif template_key == "logInvocation":
        return parse_log_invocation_policy(action)
    elif template_key == "throttle":
        return parse_throttle_policy(action)
    elif template_key == "serviceResultCache":
        return parse_service_result_cache_policy(action)
    elif template_key == "validateAPISpec":
        return parse_validate_api_spec_policy(action)
    elif template_key == "requestDataMasking":
        return parse_request_data_masking_policy(action)
    elif template_key == "responseDataMasking":
        return parse_response_data_masking_policy(action)
    elif template_key == "cors":
        return parse_cors_policy(action)
    else:
        raise ValueError(f"Unsupported policy template key: {template_key}")

# Made with Bob