"""
Utility module for converting policy action models to PolicyAction format.

This module provides conversion functions to transform specific policy action
models (EntryProtocolPolicy, EvaluatePolicy, etc.) into the generic PolicyAction
format used by the API Gateway.

IBM Confidential - Copyright 2024 IBM Corp.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ...models.webmethods.wm_policy import (
    InternationalizedString,
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
)


def _create_parameter(
    template_key: str,
    values: Optional[List[str]] = None,
    parameters: Optional[List[PolicyActionParameter]] = None
) -> PolicyActionParameter:
    """
    Create a PolicyActionParameter object.

    Args:
        template_key: The template key for the parameter.
        values: Optional list of string values.
        parameters: Optional list of nested parameters.

    Returns:
        PolicyActionParameter object.
    """
    return PolicyActionParameter(
        templateKey=template_key,
        values=values,
        parameters=parameters,
        extendedProperties=None
    )


def convert_entry_protocol_policy(
    policy: EntryProtocolPolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert EntryProtocolPolicy to PolicyAction.

    Args:
        policy: The EntryProtocolPolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.

    Example:
        >>> policy = EntryProtocolPolicy(protocol=Protocol.HTTPS)
        >>> action = convert_entry_protocol_policy(policy)
        >>> action.template_key
        'entryProtocolPolicy'
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Enable HTTP / HTTPS",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "entryProtocolPolicy",
        parameters=[
            _create_parameter(
                template_key="protocol",
                values=[policy.protocol.value if policy.protocol else Protocol.HTTP.value]
            )
        ],
        stageKey=None
    )


def convert_evaluate_policy(
    policy: EvaluatePolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert EvaluatePolicy to PolicyAction.

    Args:
        policy: The EvaluatePolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    parameters = [
        _create_parameter(
            template_key="logicalConnector",
            values=[policy.logical_connector.value]
        ),
        _create_parameter(
            template_key="allowAnonymous",
            values=[str(policy.allow_anonymous).lower()]
        ),
        _create_parameter(
            template_key="triggerPolicyViolationOnMissingAuthorizationHeader",
            values=[str(policy.trigger_policy_violation_on_missing_authorization_header).lower()]
        ),
    ]

    # Add identification rules
    for rule in policy.identification_rules:
        parameters.append(
            _create_parameter(
                template_key="IdentificationRule",
                parameters=[
                    _create_parameter(
                        template_key="applicationLookup",
                        values=[rule.application_lookup.value]
                    ),
                    _create_parameter(
                        template_key="identificationType",
                        values=[rule.identification_type.value]
                    )
                ]
            )
        )

    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Identify & Authorize",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "evaluatePolicy",
        parameters=parameters,
        stageKey=None
    )


def convert_authorize_user_policy(
    policy: AuthorizeUserPolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert AuthorizeUserPolicy to PolicyAction.

    Args:
        policy: The AuthorizeUserPolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Authorize User",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "authorizeUser",
        parameters=[
            _create_parameter(template_key="users", values=policy.users),
            _create_parameter(template_key="groups", values=policy.groups),
            _create_parameter(template_key="accessProfiles", values=policy.access_profiles),
        ],
        stageKey=None
    )


def convert_log_invocation_policy(
    policy: LogInvocationPolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert LogInvocationPolicy to PolicyAction.

    Args:
        policy: The LogInvocationPolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Log Invocation",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "logInvocation",
        parameters=[
            _create_parameter(
                template_key="storeRequestHeaders",
                values=[str(policy.store_request_headers).lower()]
            ),
            _create_parameter(
                template_key="storeRequestPayload",
                values=[str(policy.store_request_payload).lower()]
            ),
            _create_parameter(
                template_key="storeResponseHeaders",
                values=[str(policy.store_response_headers).lower()]
            ),
            _create_parameter(
                template_key="storeResponsePayload",
                values=[str(policy.store_response_payload).lower()]
            ),
            _create_parameter(
                template_key="storeAsZip",
                values=[str(policy.store_as_zip).lower()]
            ),
            _create_parameter(
                template_key="logGenerationFrequency",
                values=[policy.log_generation_frequency.value]
            ),
            _create_parameter(
                template_key="destination",
                parameters=[
                    _create_parameter(
                        template_key="destinationType",
                        values=[policy.destination.destination_type.value]
                    )
                ]
            ),
        ],
        stageKey=None
    )


def convert_throttle_policy(
    policy: ThrottlePolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert ThrottlePolicy to PolicyAction.

    Args:
        policy: The ThrottlePolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Traffic Optimization",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "throttle",
        parameters=[
            _create_parameter(
                template_key="throttleRule",
                parameters=[
                    _create_parameter(
                        template_key="throttleRuleName",
                        values=[policy.throttle_rule.throttle_rule_name]
                    ),
                    _create_parameter(
                        template_key="monitorRuleOperator",
                        values=[policy.throttle_rule.monitor_rule_operator.value]
                    ),
                    _create_parameter(
                        template_key="value",
                        values=[str(policy.throttle_rule.value)]
                    ),
                ]
            ),
            _create_parameter(template_key="consumerIds", values=policy.consumer_ids),
            _create_parameter(
                template_key="consumerSpecificCounter",
                values=[str(policy.consumer_specific_counter).lower()]
            ),
            _create_parameter(
                template_key="destination",
                parameters=[
                    _create_parameter(
                        template_key="destinationType",
                        values=[policy.destination.destination_type.value]
                    )
                ]
            ),
            _create_parameter(
                template_key="alertInterval",
                values=[str(policy.alert_interval)]
            ),
            _create_parameter(
                template_key="alertIntervalUnit",
                values=[policy.alert_interval_unit.value]
            ),
            _create_parameter(
                template_key="alertFrequency",
                values=[policy.alert_frequency.value]
            ),
            _create_parameter(
                template_key="alertMessage",
                values=[policy.alert_message]
            ),
        ],
        stageKey=None
    )


def convert_service_result_cache_policy(
    policy: ServiceResultCachePolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert ServiceResultCachePolicy to PolicyAction.

    Args:
        policy: The ServiceResultCachePolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Service Result Cache",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "serviceResultCache",
        parameters=[
            _create_parameter(template_key="ttl", values=[policy.ttl]),
            _create_parameter(
                template_key="max-payload-size",
                values=[str(policy.max_payload_size)]
            ),
        ],
        stageKey=None
    )


def convert_validate_api_spec_policy(
    policy: ValidateAPISpecPolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert ValidateAPISpecPolicy to PolicyAction.

    Args:
        policy: The ValidateAPISpecPolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Validate API Specification",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "validateAPISpec",
        parameters=[
            _create_parameter(
                template_key="schemaValidationFlag",
                values=[str(policy.schema_validation_flag).lower()]
            ),
            _create_parameter(
                template_key="validateQueryParams",
                values=[str(policy.validate_query_params).lower()]
            ),
            _create_parameter(
                template_key="validatePathParams",
                values=[str(policy.validate_path_params).lower()]
            ),
            _create_parameter(
                template_key="validateCookieParams",
                values=[str(policy.validate_cookie_params).lower()]
            ),
            _create_parameter(
                template_key="validateContentTypes",
                values=[str(policy.validate_content_types).lower()]
            ),
            _create_parameter(
                template_key="headersValidationFlag",
                values=[str(policy.headers_validation_flag).lower()]
            ),
        ],
        stageKey=None
    )


def _convert_masking_criteria_params(criteria: MaskingCriteria) -> List[PolicyActionParameter]:
    """Helper to convert MaskingCriteria to parameters."""
    return [
        _create_parameter(template_key="action", values=[criteria.action]),
        _create_parameter(template_key="maskingType", values=[criteria.masking_type.value]),
        _create_parameter(template_key="maskValue", values=[criteria.mask_value]),
    ]


def convert_request_data_masking_policy(
    policy: RequestDataMaskingPolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert RequestDataMaskingPolicy to PolicyAction.

    Args:
        policy: The RequestDataMaskingPolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Data Masking",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "requestDataMasking",
        parameters=[
            _create_parameter(
                template_key="jpathMasking",
                parameters=[
                    _create_parameter(
                        template_key="maskingCriteria",
                        parameters=_convert_masking_criteria_params(
                            policy.jpath_masking.masking_criteria
                        )
                    )
                ]
            ),
            _create_parameter(
                template_key="regexMasking",
                parameters=[
                    _create_parameter(
                        template_key="maskingCriteria",
                        parameters=_convert_masking_criteria_params(
                            policy.regex_masking.masking_criteria
                        )
                    )
                ]
            ),
            _create_parameter(
                template_key="sameForTransactionalLogging",
                values=[str(policy.same_for_transactional_logging).lower()]
            ),
            _create_parameter(
                template_key="applyForPayload",
                values=[str(policy.apply_for_payload).lower()]
            ),
        ],
        stageKey=None
    )


def convert_response_data_masking_policy(
    policy: ResponseDataMaskingPolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert ResponseDataMaskingPolicy to PolicyAction.

    Args:
        policy: The ResponseDataMaskingPolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "Data Masking",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "responseDataMasking",
        parameters=[
            _create_parameter(
                template_key="jpathMasking",
                parameters=[
                    _create_parameter(
                        template_key="maskingCriteria",
                        parameters=_convert_masking_criteria_params(
                            policy.jpath_masking.masking_criteria
                        )
                    )
                ]
            ),
            _create_parameter(
                template_key="regexMasking",
                parameters=[
                    _create_parameter(
                        template_key="maskingCriteria",
                        parameters=_convert_masking_criteria_params(
                            policy.regex_masking.masking_criteria
                        )
                    )
                ]
            ),
            _create_parameter(
                template_key="sameForTransactionalLogging",
                values=[str(policy.same_for_transactional_logging).lower()]
            ),
            _create_parameter(
                template_key="applyForPayload",
                values=[str(policy.apply_for_payload).lower()]
            ),
        ],
        stageKey=None
    )


def convert_cors_policy(
    policy: CorsPolicy,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert CorsPolicy to PolicyAction.

    Args:
        policy: The CorsPolicy object to convert.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.
    """
    return PolicyAction(
        id=policy_id or str(uuid4()),
        _docType="policyActions",
        names=[InternationalizedString(
            value=policy.description or "CORS",
            locale="en"
        )],
        descriptions=None,
        templateKey=policy.name or "cors",
        parameters=[
            _create_parameter(
                template_key="corsAttributes",
                parameters=[
                    _create_parameter(
                        template_key="allowedOrigins",
                        values=policy.cors_attributes.allowed_origins
                    ),
                    _create_parameter(
                        template_key="allowHeaders",
                        values=policy.cors_attributes.allow_headers
                    ),
                    _create_parameter(
                        template_key="exposeHeaders",
                        values=policy.cors_attributes.expose_headers
                    ),
                    _create_parameter(
                        template_key="allowCredentials",
                        values=[str(policy.cors_attributes.allow_credentials).lower()]
                    ),
                    _create_parameter(
                        template_key="allowMethods",
                        values=[method.value for method in policy.cors_attributes.allow_methods]
                    ),
                    _create_parameter(
                        template_key="maxAge",
                        values=[str(policy.cors_attributes.max_age)]
                    ),
                ]
            )
        ],
        stageKey=None
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


def convert_policy_action(
    policy: PolicyActionType,
    policy_id: Optional[str] = None
) -> PolicyAction:
    """
    Convert any policy action model to PolicyAction.

    This is a convenience function that automatically detects the policy type
    and calls the appropriate conversion function.

    Args:
        policy: Any policy action model object.
        policy_id: Optional policy action ID. If not provided, generates a new UUID.

    Returns:
        PolicyAction object in the format expected by API Gateway.

    Raises:
        ValueError: If the policy type is not supported.

    Example:
        >>> policy = EntryProtocolPolicy(protocol=Protocol.HTTPS)
        >>> action = convert_policy_action(policy)
        >>> action.template_key
        'entryProtocolPolicy'
    """
    if isinstance(policy, EntryProtocolPolicy):
        return convert_entry_protocol_policy(policy, policy_id)
    elif isinstance(policy, EvaluatePolicy):
        return convert_evaluate_policy(policy, policy_id)
    elif isinstance(policy, AuthorizeUserPolicy):
        return convert_authorize_user_policy(policy, policy_id)
    elif isinstance(policy, LogInvocationPolicy):
        return convert_log_invocation_policy(policy, policy_id)
    elif isinstance(policy, ThrottlePolicy):
        return convert_throttle_policy(policy, policy_id)
    elif isinstance(policy, ServiceResultCachePolicy):
        return convert_service_result_cache_policy(policy, policy_id)
    elif isinstance(policy, ValidateAPISpecPolicy):
        return convert_validate_api_spec_policy(policy, policy_id)
    elif isinstance(policy, RequestDataMaskingPolicy):
        return convert_request_data_masking_policy(policy, policy_id)
    elif isinstance(policy, ResponseDataMaskingPolicy):
        return convert_response_data_masking_policy(policy, policy_id)
    elif isinstance(policy, CorsPolicy):
        return convert_cors_policy(policy, policy_id)
    else:
        raise ValueError(f"Unsupported policy type: {type(policy).__name__}")

# Made with Bob
