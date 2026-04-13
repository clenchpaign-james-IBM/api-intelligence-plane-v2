"""
Utility module for normalizing webMethods policy actions to vendor-neutral format.

This module provides conversion functions to transform webMethods-specific policy action
models (EntryProtocolPolicy, EvaluatePolicy, etc.) into the vendor-neutral PolicyAction
format used by the API Intelligence Plane.

IBM Confidential - Copyright 2024 IBM Corp.
"""

from typing import Any, Dict, Optional, Union

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
)


def normalize_entry_protocol_policy(policy: EntryProtocolPolicy) -> PolicyAction:
    """
    Normalize EntryProtocolPolicy to vendor-neutral PolicyAction.

    Args:
        policy: The EntryProtocolPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.

    Example:
        >>> policy = EntryProtocolPolicy(protocol=Protocol.HTTPS)
        >>> action = normalize_entry_protocol_policy(policy)
        >>> action.action_type
        <PolicyActionType.TLS: 'tls'>
    """
    return PolicyAction(
        action_type=PolicyActionType.TLS,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Entry Protocol'),
        description=policy.description,
        config={
            "protocol": policy.protocol.value if policy.protocol else "http",
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'entryProtocolPolicy'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_evaluate_policy(policy: EvaluatePolicy) -> PolicyAction:
    """
    Normalize EvaluatePolicy to vendor-neutral PolicyAction.

    Args:
        policy: The EvaluatePolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    identification_rules = []
    for rule in policy.identification_rules:
        identification_rules.append({
            "application_lookup": rule.application_lookup.value if hasattr(rule, 'application_lookup') else rule.applicationLookup.value,
            "identification_type": rule.identification_type.value if hasattr(rule, 'identification_type') else rule.identificationType.value
        })
    
    return PolicyAction(
        action_type=PolicyActionType.AUTHENTICATION,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Identify & Authorize'),
        description=policy.description,
        config={
            "logical_connector": policy.logical_connector.value if hasattr(policy, 'logical_connector') else policy.logicalConnector.value,
            "allow_anonymous": policy.allow_anonymous if hasattr(policy, 'allow_anonymous') else policy.allowAnonymous,
            "trigger_policy_violation_on_missing_authorization_header": (
                policy.trigger_policy_violation_on_missing_authorization_header 
                if hasattr(policy, 'trigger_policy_violation_on_missing_authorization_header') 
                else policy.triggerPolicyViolationOnMissingAuthorizationHeader
            ),
            "identification_rules": identification_rules
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'evaluatePolicy'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_authorize_user_policy(policy: AuthorizeUserPolicy) -> PolicyAction:
    """
    Normalize AuthorizeUserPolicy to vendor-neutral PolicyAction.

    Args:
        policy: The AuthorizeUserPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    return PolicyAction(
        action_type=PolicyActionType.AUTHORIZATION,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Authorize User'),
        description=policy.description,
        config={
            "users": policy.users,
            "groups": policy.groups,
            "access_profiles": policy.access_profiles if hasattr(policy, 'access_profiles') else policy.accessProfiles
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'authorizeUser'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_log_invocation_policy(policy: LogInvocationPolicy) -> PolicyAction:
    """
    Normalize LogInvocationPolicy to vendor-neutral PolicyAction.

    Args:
        policy: The LogInvocationPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    store_request_headers = policy.store_request_headers if hasattr(policy, 'store_request_headers') else policy.storeRequestHeaders
    store_request_payload = policy.store_request_payload if hasattr(policy, 'store_request_payload') else policy.storeRequestPayload
    store_response_headers = policy.store_response_headers if hasattr(policy, 'store_response_headers') else policy.storeResponseHeaders
    store_response_payload = policy.store_response_payload if hasattr(policy, 'store_response_payload') else policy.storeResponsePayload
    store_as_zip = policy.store_as_zip if hasattr(policy, 'store_as_zip') else policy.storeAsZip
    log_gen_freq = policy.log_generation_frequency if hasattr(policy, 'log_generation_frequency') else policy.logGenerationFrequency
    dest_type = policy.destination.destination_type if hasattr(policy.destination, 'destination_type') else policy.destination.destinationType
    
    return PolicyAction(
        action_type=PolicyActionType.LOGGING,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Log Invocation'),
        description=policy.description,
        config={
            "store_request_headers": store_request_headers,
            "store_request_payload": store_request_payload,
            "store_response_headers": store_response_headers,
            "store_response_payload": store_response_payload,
            "store_as_zip": store_as_zip,
            "log_generation_frequency": log_gen_freq.value,
            "destination_type": dest_type.value
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'logInvocation'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_throttle_policy(policy: ThrottlePolicy) -> PolicyAction:
    """
    Normalize ThrottlePolicy to vendor-neutral PolicyAction.

    Args:
        policy: The ThrottlePolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    throttle_rule = policy.throttle_rule if hasattr(policy, 'throttle_rule') else policy.throttleRule
    rule_name = throttle_rule.throttle_rule_name if hasattr(throttle_rule, 'throttle_rule_name') else throttle_rule.throttleRuleName
    operator = throttle_rule.monitor_rule_operator if hasattr(throttle_rule, 'monitor_rule_operator') else throttle_rule.monitorRuleOperator
    
    consumer_ids = policy.consumer_ids if hasattr(policy, 'consumer_ids') else policy.consumerIds
    consumer_specific = policy.consumer_specific_counter if hasattr(policy, 'consumer_specific_counter') else policy.consumerSpecificCounter
    dest_type = policy.destination.destination_type if hasattr(policy.destination, 'destination_type') else policy.destination.destinationType
    alert_interval = policy.alert_interval if hasattr(policy, 'alert_interval') else policy.alertInterval
    alert_interval_unit = policy.alert_interval_unit if hasattr(policy, 'alert_interval_unit') else policy.alertIntervalUnit
    alert_frequency = policy.alert_frequency if hasattr(policy, 'alert_frequency') else policy.alertFrequency
    alert_message = policy.alert_message if hasattr(policy, 'alert_message') else policy.alertMessage
    
    return PolicyAction(
        action_type=PolicyActionType.RATE_LIMITING,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Traffic Optimization'),
        description=policy.description,
        config={
            "throttle_rule": {
                "name": rule_name,
                "operator": operator.value,
                "value": throttle_rule.value
            },
            "consumer_ids": consumer_ids,
            "consumer_specific_counter": consumer_specific,
            "destination_type": dest_type.value,
            "alert_interval": alert_interval,
            "alert_interval_unit": alert_interval_unit.value,
            "alert_frequency": alert_frequency.value,
            "alert_message": alert_message
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'throttle'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_service_result_cache_policy(policy: ServiceResultCachePolicy) -> PolicyAction:
    """
    Normalize ServiceResultCachePolicy to vendor-neutral PolicyAction.

    Args:
        policy: The ServiceResultCachePolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    max_payload = policy.max_payload_size if hasattr(policy, 'max_payload_size') else getattr(policy, 'max-payload-size', 1000)
    
    return PolicyAction(
        action_type=PolicyActionType.CACHING,
        enabled=True,
        stage="response",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Service Result Cache'),
        description=policy.description,
        config={
            "ttl": policy.ttl,
            "max_payload_size": max_payload
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'serviceResultCache'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_validate_api_spec_policy(policy: ValidateAPISpecPolicy) -> PolicyAction:
    """
    Normalize ValidateAPISpecPolicy to vendor-neutral PolicyAction.

    Args:
        policy: The ValidateAPISpecPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    schema_validation = policy.schema_validation_flag if hasattr(policy, 'schema_validation_flag') else policy.schemaValidationFlag
    validate_query = policy.validate_query_params if hasattr(policy, 'validate_query_params') else policy.validateQueryParams
    validate_path = policy.validate_path_params if hasattr(policy, 'validate_path_params') else policy.validatePathParams
    validate_cookie = policy.validate_cookie_params if hasattr(policy, 'validate_cookie_params') else policy.validateCookieParams
    validate_content = policy.validate_content_types if hasattr(policy, 'validate_content_types') else policy.validateContentTypes
    headers_validation = policy.headers_validation_flag if hasattr(policy, 'headers_validation_flag') else policy.headersValidationFlag
    
    return PolicyAction(
        action_type=PolicyActionType.VALIDATION,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Validate API Specification'),
        description=policy.description,
        config={
            "schema_validation": schema_validation,
            "validate_query_params": validate_query,
            "validate_path_params": validate_path,
            "validate_cookie_params": validate_cookie,
            "validate_content_types": validate_content,
            "validate_headers": headers_validation
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'validateAPISpec'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_request_data_masking_policy(policy: RequestDataMaskingPolicy) -> PolicyAction:
    """
    Normalize RequestDataMaskingPolicy to vendor-neutral PolicyAction.

    Args:
        policy: The RequestDataMaskingPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    jpath_masking = policy.jpath_masking if hasattr(policy, 'jpath_masking') else policy.jpathMasking
    regex_masking = policy.regex_masking if hasattr(policy, 'regex_masking') else policy.regexMasking
    same_for_logging = policy.same_for_transactional_logging if hasattr(policy, 'same_for_transactional_logging') else policy.sameForTransactionalLogging
    apply_for_payload = policy.apply_for_payload if hasattr(policy, 'apply_for_payload') else policy.applyForPayload
    
    jpath_criteria = jpath_masking.masking_criteria if hasattr(jpath_masking, 'masking_criteria') else jpath_masking.maskingCriteria
    regex_criteria = regex_masking.masking_criteria if hasattr(regex_masking, 'masking_criteria') else regex_masking.maskingCriteria
    
    return PolicyAction(
        action_type=PolicyActionType.DATA_MASKING,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Request Data Masking'),
        description=policy.description,
        config={
            "jpath_masking": {
                "action": jpath_criteria.action,
                "masking_type": jpath_criteria.masking_type.value if hasattr(jpath_criteria, 'masking_type') else jpath_criteria.maskingType.value,
                "mask_value": jpath_criteria.mask_value if hasattr(jpath_criteria, 'mask_value') else jpath_criteria.maskValue
            },
            "regex_masking": {
                "action": regex_criteria.action,
                "masking_type": regex_criteria.masking_type.value if hasattr(regex_criteria, 'masking_type') else regex_criteria.maskingType.value,
                "mask_value": regex_criteria.mask_value if hasattr(regex_criteria, 'mask_value') else regex_criteria.maskValue
            },
            "same_for_transactional_logging": same_for_logging,
            "apply_for_payload": apply_for_payload
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'requestDataMasking'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_response_data_masking_policy(policy: ResponseDataMaskingPolicy) -> PolicyAction:
    """
    Normalize ResponseDataMaskingPolicy to vendor-neutral PolicyAction.

    Args:
        policy: The ResponseDataMaskingPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    jpath_masking = policy.jpath_masking if hasattr(policy, 'jpath_masking') else policy.jpathMasking
    regex_masking = policy.regex_masking if hasattr(policy, 'regex_masking') else policy.regexMasking
    same_for_logging = policy.same_for_transactional_logging if hasattr(policy, 'same_for_transactional_logging') else policy.sameForTransactionalLogging
    apply_for_payload = policy.apply_for_payload if hasattr(policy, 'apply_for_payload') else policy.applyForPayload
    
    jpath_criteria = jpath_masking.masking_criteria if hasattr(jpath_masking, 'masking_criteria') else jpath_masking.maskingCriteria
    regex_criteria = regex_masking.masking_criteria if hasattr(regex_masking, 'masking_criteria') else regex_masking.maskingCriteria
    
    return PolicyAction(
        action_type=PolicyActionType.DATA_MASKING,
        enabled=True,
        stage="response",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'Response Data Masking'),
        description=policy.description,
        config={
            "jpath_masking": {
                "action": jpath_criteria.action,
                "masking_type": jpath_criteria.masking_type.value if hasattr(jpath_criteria, 'masking_type') else jpath_criteria.maskingType.value,
                "mask_value": jpath_criteria.mask_value if hasattr(jpath_criteria, 'mask_value') else jpath_criteria.maskValue
            },
            "regex_masking": {
                "action": regex_criteria.action,
                "masking_type": regex_criteria.masking_type.value if hasattr(regex_criteria, 'masking_type') else regex_criteria.maskingType.value,
                "mask_value": regex_criteria.mask_value if hasattr(regex_criteria, 'mask_value') else regex_criteria.maskValue
            },
            "same_for_transactional_logging": same_for_logging,
            "apply_for_payload": apply_for_payload
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'responseDataMasking'),
            "original_policy": policy.model_dump(by_alias=True)
        }
    )


def normalize_cors_policy(policy: CorsPolicy) -> PolicyAction:
    """
    Normalize CorsPolicy to vendor-neutral PolicyAction.

    Args:
        policy: The CorsPolicy object to normalize.

    Returns:
        Vendor-neutral PolicyAction object.
    """
    cors_attrs = policy.cors_attributes if hasattr(policy, 'cors_attributes') else policy.corsAttributes
    
    allowed_origins = cors_attrs.allowed_origins if hasattr(cors_attrs, 'allowed_origins') else cors_attrs.allowedOrigins
    allow_headers = cors_attrs.allow_headers if hasattr(cors_attrs, 'allow_headers') else cors_attrs.allowHeaders
    expose_headers = cors_attrs.expose_headers if hasattr(cors_attrs, 'expose_headers') else cors_attrs.exposeHeaders
    allow_credentials = cors_attrs.allow_credentials if hasattr(cors_attrs, 'allow_credentials') else cors_attrs.allowCredentials
    allow_methods = cors_attrs.allow_methods if hasattr(cors_attrs, 'allow_methods') else cors_attrs.allowMethods
    max_age = cors_attrs.max_age if hasattr(cors_attrs, 'max_age') else cors_attrs.maxAge
    
    return PolicyAction(
        action_type=PolicyActionType.CORS,
        enabled=True,
        stage="request",
        name=getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'CORS'),
        description=policy.description,
        config={
            "allowed_origins": allowed_origins,
            "allow_headers": allow_headers,
            "expose_headers": expose_headers,
            "allow_credentials": allow_credentials,
            "allow_methods": [m.value for m in allow_methods],
            "max_age": max_age
        },
        vendor_config={
            "vendor": "webmethods",
            "template_key": getattr(policy, 'name', None) or getattr(policy, 'templateKey', 'cors'),
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
        Vendor-neutral PolicyAction object.

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