"""
Python Pydantic models for API Gateway PolicyActions.

This module defines policy action models for API Gateway configurations,
converted from Java classes. These models represent various gateway policies
that can be applied to APIs for protocol handling, security, and traffic management.

IBM Confidential - Copyright 2024 IBM Corp.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BasePolicy(BaseModel):
    """
    Base class for all policy models.

    Provides common fields and configuration for policy objects used across
    the API Gateway system. All specific policy types should inherit from this base.

    Attributes:
        id: Optional unique identifier for the policy instance.
    """

    id: Optional[str] = Field(
        None,
        description="Unique identifier for the policy instance"
    )

    model_config = ConfigDict(populate_by_name=True)


class Protocol(str, Enum):
    """
    Enumeration of supported network protocols.

    Defines the available protocol options for API Gateway entry points,
    determining how clients can communicate with the gateway.

    Attributes:
        HTTP: Unencrypted HTTP protocol (port 80 by default).
        HTTPS: Encrypted HTTPS protocol with TLS/SSL (port 443 by default).
    """

    HTTP = "http"
    HTTPS = "https"


class EntryProtocolPolicy(BaseModel):
    """
    Policy for configuring the entry protocol of an API Gateway.

    Defines which network protocol (HTTP or HTTPS) should be used for incoming
    client connections to the API Gateway. This policy controls the initial
    connection security and protocol handling.

    Attributes:
        name: Policy template identifier, defaults to "entryProtocolPolicy".
        description: Human-readable description of the policy's purpose.
        protocol: The network protocol to use for entry connections (HTTP or HTTPS).

    Example:
        >>> policy = EntryProtocolPolicy(protocol=Protocol.HTTPS)
        >>> policy.protocol
        <Protocol.HTTPS: 'https'>
    """

    name: Optional[str] = Field(
        "entryProtocolPolicy",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Enable HTTP / HTTPS",
        description="Human-readable description of the policy"
    )
    protocol: Optional[Protocol] = Field(
        Protocol.HTTP,
        description="Network protocol for entry connections (HTTP or HTTPS)"
    )

    model_config = ConfigDict(populate_by_name=True)


class LogicalConnector(str, Enum):
    """
    Enumeration of logical operators for combining identification rules.

    Defines how multiple identification rules should be evaluated when
    determining if a request should be authenticated and authorized.

    Attributes:
        OR: At least one identification rule must succeed.
        AND: All identification rules must succeed.
    """

    OR = "OR"
    AND = "AND"


class ApplicationLookup(str, Enum):
    """
    Enumeration of application lookup strategies.

    Defines the strictness level for application identification during
    authentication and authorization processes.

    Attributes:
        STRICT: Exact match required for application identification.
        RELAX: Flexible matching with some tolerance for variations.
        OPEN: Minimal restrictions on application identification.
    """

    STRICT = "strict"
    RELAX = "relax"
    OPEN = "open"


class IdentificationType(str, Enum):
    """
    Enumeration of supported identification/authentication methods.

    Defines the various authentication mechanisms that can be used to
    identify and authenticate API clients.

    Attributes:
        API_KEY: Authentication using API key in header or query parameter.
        HTTP_BASIC_AUTH: HTTP Basic Authentication with username/password.
        JWT_CLAIMS: JSON Web Token (JWT) with claims-based authentication.
        OAUTH2_TOKEN: OAuth 2.0 token-based authentication.
    """

    API_KEY = "apiKey"
    HTTP_BASIC_AUTH = "httpBasicAuth"
    JWT_CLAIMS = "jwtClaims"
    OAUTH2_TOKEN = "oAuth2Token"


class IdentificationRule(BaseModel):
    """
    Configuration for a single identification/authentication rule.

    Defines how a specific authentication method should be applied,
    including the lookup strategy and identification type.

    Attributes:
        application_lookup: Strategy for matching applications during identification.
        identification_type: The authentication method to use for this rule.

    Example:
        >>> rule = IdentificationRule(
        ...     application_lookup=ApplicationLookup.STRICT,
        ...     identification_type=IdentificationType.API_KEY
        ... )
    """

    application_lookup: ApplicationLookup = Field(
        ...,
        alias="applicationLookup",
        description="Application lookup strategy (strict, relax, or open)"
    )
    identification_type: IdentificationType = Field(
        ...,
        alias="identificationType",
        description="Authentication method type"
    )

    model_config = ConfigDict(populate_by_name=True)


class EvaluatePolicy(BaseModel):
    """
    Policy for identifying and authorizing API requests.

    Configures authentication and authorization rules for API Gateway requests.
    Supports multiple identification methods with configurable logical operators
    to determine how rules are evaluated.

    This policy can enforce various authentication mechanisms including API keys,
    HTTP Basic Auth, JWT tokens, and OAuth 2.0 tokens, with flexible application
    lookup strategies.

    Attributes:
        name: Policy template identifier, defaults to "evaluatePolicy".
        description: Human-readable description of the policy's purpose.
        logical_connector: Logical operator (OR/AND) for combining identification rules.
        allow_anonymous: Whether to allow unauthenticated requests.
        trigger_policy_violation_on_missing_authorization_header: Whether to trigger
            a policy violation when the Authorization header is missing.
        identification_rules: List of identification rules to evaluate.

    Example:
        >>> policy = EvaluatePolicy(
        ...     logical_connector=LogicalConnector.OR,
        ...     allow_anonymous=False,
        ...     identification_rules=[
        ...         IdentificationRule(
        ...             application_lookup=ApplicationLookup.STRICT,
        ...             identification_type=IdentificationType.API_KEY
        ...         ),
        ...         IdentificationRule(
        ...             application_lookup=ApplicationLookup.RELAX,
        ...             identification_type=IdentificationType.HTTP_BASIC_AUTH
        ...         )
        ...     ]
        ... )
    """

    name: Optional[str] = Field(
        "evaluatePolicy",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Identify & Authorize",
        description="Human-readable description of the policy"
    )
    logical_connector: LogicalConnector = Field(
        LogicalConnector.OR,
        alias="logicalConnector",
        description="Logical operator for combining identification rules (OR/AND)"
    )
    allow_anonymous: bool = Field(
        False,
        alias="allowAnonymous",
        description="Whether to allow unauthenticated/anonymous requests"
    )
    trigger_policy_violation_on_missing_authorization_header: bool = Field(
        False,
        alias="triggerPolicyViolationOnMissingAuthorizationHeader",
        description="Trigger policy violation when Authorization header is missing"
    )
    identification_rules: List[IdentificationRule] = Field(
        default_factory=list,
        alias="IdentificationRule",
        description="List of identification/authentication rules to evaluate"
    )

    model_config = ConfigDict(populate_by_name=True)


class AuthorizeUserPolicy(BaseModel):
    """
    Policy for authorizing users based on users, groups, and access profiles.

    Configures user authorization rules for API Gateway requests by specifying
    which users, user groups, and access profiles are permitted to access the API.
    This policy provides fine-grained access control based on user identity and
    group membership.

    Authorization is granted if the authenticated user matches any of the specified
    users, belongs to any of the specified groups, or has any of the specified
    access profiles.

    Attributes:
        name: Policy template identifier, defaults to "authorizeUser".
        description: Human-readable description of the policy's purpose.
        users: List of individual usernames authorized to access the API.
        groups: List of user groups authorized to access the API.
        access_profiles: List of access profiles authorized to access the API.

    Example:
        >>> policy = AuthorizeUserPolicy(
        ...     users=["Administrator", "john.doe"],
        ...     groups=["Administrators", "API-Gateway-Administrators"],
        ...     access_profiles=["Administrators", "PowerUsers"]
        ... )
        >>> policy.users
        ['Administrator', 'john.doe']
    """

    name: Optional[str] = Field(
        "authorizeUser",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Authorize User",
        description="Human-readable description of the policy"
    )
    users: List[str] = Field(
        default=["Administrator"],
        description="List of authorized usernames"
    )
    groups: List[str] = Field(
        default=["Administrators", "API-Gateway-Administrators"],
        description="List of authorized user groups"
    )
    access_profiles: List[str] = Field(
        default=["Administrators"],
        alias="accessProfiles",
        description="List of authorized access profiles"
    )

    model_config = ConfigDict(populate_by_name=True)


class LogGenerationFrequency(str, Enum):
    """
    Enumeration of log generation frequency options.

    Defines when API invocation logs should be generated and stored.

    Attributes:
        ALWAYS: Generate logs for every API invocation.
        ON_ERROR: Generate logs only when errors occur.
        NEVER: Do not generate logs.
    """

    ALWAYS = "Always"
    ON_ERROR = "OnError"
    NEVER = "Never"


class DestinationType(str, Enum):
    """
    Enumeration of log destination types.

    Defines where API invocation logs should be stored.

    Attributes:
        GATEWAY: Store logs in the API Gateway's internal storage.
        EXTERNAL: Store logs in an external logging system.
        SYSLOG: Store logs using syslog protocol.
    """

    GATEWAY = "GATEWAY"
    EXTERNAL = "EXTERNAL"
    SYSLOG = "SYSLOG"


class LogDestination(BaseModel):
    """
    Configuration for log storage destination.

    Defines where and how API invocation logs should be stored.

    Attributes:
        destination_type: The type of destination for storing logs.

    Example:
        >>> destination = LogDestination(destination_type=DestinationType.GATEWAY)
    """

    destination_type: DestinationType = Field(
        DestinationType.GATEWAY,
        alias="destinationType",
        description="Type of destination for storing logs"
    )

    model_config = ConfigDict(populate_by_name=True)


class LogInvocationPolicy(BaseModel):
    """
    Policy for logging API invocations.

    Configures comprehensive logging of API requests and responses, including
    headers and payloads. This policy enables audit trails, debugging, and
    compliance monitoring by capturing detailed information about API usage.

    Logs can be stored in various formats and destinations, with options to
    compress data and control when logs are generated.

    Attributes:
        name: Policy template identifier, defaults to "logInvocation".
        description: Human-readable description of the policy's purpose.
        store_request_headers: Whether to log request headers.
        store_request_payload: Whether to log request body/payload.
        store_response_headers: Whether to log response headers.
        store_response_payload: Whether to log response body/payload.
        store_as_zip: Whether to compress logs using ZIP format.
        log_generation_frequency: When to generate logs (Always, OnError, Never).
        destination: Configuration for where logs should be stored.

    Example:
        >>> policy = LogInvocationPolicy(
        ...     store_request_headers=True,
        ...     store_request_payload=True,
        ...     store_response_headers=True,
        ...     store_response_payload=True,
        ...     store_as_zip=True,
        ...     log_generation_frequency=LogGenerationFrequency.ALWAYS,
        ...     destination=LogDestination(destination_type=DestinationType.GATEWAY)
        ... )
    """

    name: Optional[str] = Field(
        "logInvocation",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Log Invocation",
        description="Human-readable description of the policy"
    )
    store_request_headers: bool = Field(
        True,
        alias="storeRequestHeaders",
        description="Whether to log request headers"
    )
    store_request_payload: bool = Field(
        True,
        alias="storeRequestPayload",
        description="Whether to log request body/payload"
    )
    store_response_headers: bool = Field(
        True,
        alias="storeResponseHeaders",
        description="Whether to log response headers"
    )
    store_response_payload: bool = Field(
        True,
        alias="storeResponsePayload",
        description="Whether to log response body/payload"
    )
    store_as_zip: bool = Field(
        True,
        alias="storeAsZip",
        description="Whether to compress logs using ZIP format"
    )
    log_generation_frequency: LogGenerationFrequency = Field(
        LogGenerationFrequency.ALWAYS,
        alias="logGenerationFrequency",
        description="When to generate logs (Always, OnError, Never)"
    )
    destination: LogDestination = Field(
        default_factory=lambda: LogDestination(destinationType=DestinationType.GATEWAY),
        description="Configuration for log storage destination"
    )

    model_config = ConfigDict(populate_by_name=True)


class MonitorRuleOperator(str, Enum):
    """
    Enumeration of comparison operators for throttle rules.

    Defines how the monitored metric should be compared against the threshold value.

    Attributes:
        GT: Greater than - trigger when metric exceeds threshold.
        GTE: Greater than or equal to - trigger when metric meets or exceeds threshold.
        LT: Less than - trigger when metric is below threshold.
        LTE: Less than or equal to - trigger when metric is at or below threshold.
        EQ: Equal to - trigger when metric equals threshold.
    """

    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    EQ = "EQ"


class AlertIntervalUnit(str, Enum):
    """
    Enumeration of time units for alert intervals.

    Defines the time unit for measuring alert intervals in throttle policies.

    Attributes:
        SECONDS: Time interval in seconds.
        MINUTES: Time interval in minutes.
        HOURS: Time interval in hours.
        DAYS: Time interval in days.
    """

    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class AlertFrequency(str, Enum):
    """
    Enumeration of alert frequency options.

    Defines how often alerts should be triggered when throttle conditions are met.

    Attributes:
        ONCE: Trigger alert only once when condition is met.
        EVERY_TIME: Trigger alert every time condition is met.
        PERIODIC: Trigger alert periodically while condition persists.
    """

    ONCE = "once"
    EVERY_TIME = "everyTime"
    PERIODIC = "periodic"


class ThrottleRule(BaseModel):
    """
    Configuration for a single throttle monitoring rule.

    Defines the conditions under which traffic should be throttled or alerts
    should be triggered based on API usage metrics.

    Attributes:
        throttle_rule_name: Name of the metric to monitor (e.g., "requestCount").
        monitor_rule_operator: Comparison operator for the threshold check.
        value: Threshold value for the monitored metric.

    Example:
        >>> rule = ThrottleRule(
        ...     throttle_rule_name="requestCount",
        ...     monitor_rule_operator=MonitorRuleOperator.GT,
        ...     value=10
        ... )
    """

    throttle_rule_name: str = Field(
        ...,
        alias="throttleRuleName",
        description="Name of the metric to monitor (e.g., requestCount, bandwidth)"
    )
    monitor_rule_operator: MonitorRuleOperator = Field(
        ...,
        alias="monitorRuleOperator",
        description="Comparison operator for threshold check (GT, GTE, LT, LTE, EQ)"
    )
    value: int = Field(
        ...,
        description="Threshold value for the monitored metric"
    )

    model_config = ConfigDict(populate_by_name=True)


class ThrottleDestination(BaseModel):
    """
    Configuration for throttle alert destination.

    Defines where throttle alerts and logs should be sent.

    Attributes:
        destination_type: The type of destination for throttle alerts.

    Example:
        >>> destination = ThrottleDestination(destination_type=DestinationType.GATEWAY)
    """

    destination_type: DestinationType = Field(
        DestinationType.GATEWAY,
        alias="destinationType",
        description="Type of destination for throttle alerts"
    )

    model_config = ConfigDict(populate_by_name=True)


class ThrottlePolicy(BaseModel):
    """
    Policy for traffic optimization and throttling.

    Configures traffic management rules to monitor API usage and trigger alerts
    or throttling actions when specified thresholds are exceeded. This policy
    helps prevent API abuse, manage resource consumption, and ensure fair usage
    across consumers.

    Supports consumer-specific or global counters, configurable alert intervals,
    and flexible threshold rules based on various metrics like request count,
    bandwidth, or response time.

    Attributes:
        name: Policy template identifier, defaults to "throttle".
        description: Human-readable description of the policy's purpose.
        throttle_rule: The monitoring rule defining when to throttle or alert.
        consumer_ids: List of consumer identifiers to apply throttling to.
        consumer_specific_counter: Whether to maintain separate counters per consumer.
        destination: Configuration for where alerts should be sent.
        alert_interval: Time interval for alert monitoring.
        alert_interval_unit: Unit of time for the alert interval.
        alert_frequency: How often to trigger alerts when conditions are met.
        alert_message: Custom message to include in alerts.

    Example:
        >>> policy = ThrottlePolicy(
        ...     throttle_rule=ThrottleRule(
        ...         throttle_rule_name="requestCount",
        ...         monitor_rule_operator=MonitorRuleOperator.GT,
        ...         value=10
        ...     ),
        ...     consumer_ids=["AllConsumers"],
        ...     consumer_specific_counter=False,
        ...     alert_interval=1,
        ...     alert_interval_unit=AlertIntervalUnit.MINUTES,
        ...     alert_frequency=AlertFrequency.ONCE,
        ...     alert_message="Limit exceeded"
        ... )
    """

    name: Optional[str] = Field(
        "throttle",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Traffic Optimization",
        description="Human-readable description of the policy"
    )
    throttle_rule: ThrottleRule = Field(
        ...,
        alias="throttleRule",
        description="Monitoring rule defining when to throttle or alert"
    )
    consumer_ids: List[str] = Field(
        default=["AllConsumers"],
        alias="consumerIds",
        description="List of consumer identifiers to apply throttling to"
    )
    consumer_specific_counter: bool = Field(
        False,
        alias="consumerSpecificCounter",
        description="Whether to maintain separate counters per consumer"
    )
    destination: ThrottleDestination = Field(
        default_factory=lambda: ThrottleDestination(destinationType=DestinationType.GATEWAY),
        description="Configuration for where alerts should be sent"
    )
    alert_interval: int = Field(
        1,
        alias="alertInterval",
        description="Time interval for alert monitoring"
    )
    alert_interval_unit: AlertIntervalUnit = Field(
        AlertIntervalUnit.MINUTES,
        alias="alertIntervalUnit",
        description="Unit of time for the alert interval"
    )
    alert_frequency: AlertFrequency = Field(
        AlertFrequency.ONCE,
        alias="alertFrequency",
        description="How often to trigger alerts when conditions are met"
    )
    alert_message: str = Field(
        "Limit exceeded",
        alias="alertMessage",
        description="Custom message to include in alerts"
    )

    model_config = ConfigDict(populate_by_name=True)


class ServiceResultCachePolicy(BaseModel):
    """
    Policy for caching service results to improve performance.

    Configures response caching for API Gateway to reduce backend load and
    improve response times by storing and reusing service responses. This
    policy is particularly useful for APIs with frequently requested data
    that doesn't change often.

    The cache uses a time-to-live (TTL) mechanism to control how long responses
    are cached, and supports payload size limits to prevent caching of large
    responses that could consume excessive memory.

    Attributes:
        name: Policy template identifier, defaults to "serviceResultCache".
        description: Human-readable description of the policy's purpose.
        ttl: Time-to-live for cached responses (e.g., "1d", "2h", "30m", "60s").
            Supports units: d (days), h (hours), m (minutes), s (seconds).
        max_payload_size: Maximum payload size in kilobytes that can be cached.
            Responses larger than this will not be cached.

    Example:
        >>> policy = ServiceResultCachePolicy(
        ...     ttl="1d",
        ...     max_payload_size=1000
        ... )
        >>> policy.ttl
        '1d'
    """

    name: Optional[str] = Field(
        "serviceResultCache",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Service Result Cache",
        description="Human-readable description of the policy"
    )
    ttl: str = Field(
        "1d",
        description="Time-to-live for cached responses (e.g., '1d', '2h', '30m', '60s')"
    )
    max_payload_size: int = Field(
        1000,
        alias="max-payload-size",
        description="Maximum payload size in kilobytes that can be cached"
    )

    model_config = ConfigDict(populate_by_name=True)


class ValidateAPISpecPolicy(BaseModel):
    """
    Policy for validating API requests against OpenAPI/Swagger specifications.

    Configures comprehensive validation of incoming API requests to ensure they
    conform to the API specification. This policy can validate various aspects
    of requests including schema, query parameters, path parameters, cookies,
    content types, and headers.

    Validation helps ensure API contract compliance, prevents malformed requests
    from reaching backend services, and provides early error detection with
    meaningful error messages to API consumers.

    Attributes:
        name: Policy template identifier, defaults to "validateAPISpec".
        description: Human-readable description of the policy's purpose.
        schema_validation_flag: Whether to validate request/response bodies against
            JSON/XML schemas defined in the API specification.
        validate_query_params: Whether to validate query parameters against the
            API specification.
        validate_path_params: Whether to validate path parameters against the
            API specification.
        validate_cookie_params: Whether to validate cookie parameters against the
            API specification.
        validate_content_types: Whether to validate Content-Type headers against
            allowed types in the API specification.
        headers_validation_flag: Whether to validate request headers against the
            API specification.

    Example:
        >>> policy = ValidateAPISpecPolicy(
        ...     schema_validation_flag=False,
        ...     validate_query_params=True,
        ...     validate_path_params=False,
        ...     validate_cookie_params=False,
        ...     validate_content_types=False,
        ...     headers_validation_flag=False
        ... )
        >>> policy.validate_query_params
        True
    """

    name: Optional[str] = Field(
        "validateAPISpec",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Validate API Specification",
        description="Human-readable description of the policy"
    )
    schema_validation_flag: bool = Field(
        False,
        alias="schemaValidationFlag",
        description="Whether to validate request/response bodies against schemas"
    )
    validate_query_params: bool = Field(
        True,
        alias="validateQueryParams",
        description="Whether to validate query parameters"
    )
    validate_path_params: bool = Field(
        False,
        alias="validatePathParams",
        description="Whether to validate path parameters"
    )
    validate_cookie_params: bool = Field(
        False,
        alias="validateCookieParams",
        description="Whether to validate cookie parameters"
    )
    validate_content_types: bool = Field(
        False,
        alias="validateContentTypes",
        description="Whether to validate Content-Type headers"
    )
    headers_validation_flag: bool = Field(
        False,
        alias="headersValidationFlag",
        description="Whether to validate request headers"
    )

    model_config = ConfigDict(populate_by_name=True)


class MaskingType(str, Enum):
    """
    Enumeration of data masking types.

    Defines how sensitive data should be masked or transformed.

    Attributes:
        MASK: Replace data with a mask value (e.g., "********").
        FILTER: Remove/filter out the data entirely.
    """

    MASK = "mask"
    FILTER = "filter"


class MaskingCriteria(BaseModel):
    """
    Configuration for a single masking rule.

    Defines how specific data should be masked, including the action identifier,
    masking type, and the mask value to use.

    Attributes:
        action: Identifier for the data to be masked (e.g., field name or pattern).
        masking_type: The type of masking to apply.
        mask_value: The value to use when masking (e.g., "********").

    Example:
        >>> criteria = MaskingCriteria(
        ...     action="SOME_STRING",
        ...     masking_type=MaskingType.MASK,
        ...     mask_value="********"
        ... )
    """

    action: str = Field(
        ...,
        description="Identifier for the data to be masked"
    )
    masking_type: MaskingType = Field(
        ...,
        alias="maskingType",
        description="Type of masking to apply (mask, hash, remove, encrypt)"
    )
    mask_value: str = Field(
        "********",
        alias="maskValue",
        description="Value to use when masking data"
    )

    model_config = ConfigDict(populate_by_name=True)


class JPathMasking(BaseModel):
    """
    Configuration for JSONPath-based data masking.

    Defines masking rules that use JSONPath expressions to identify and mask
    specific fields in JSON payloads.

    Attributes:
        masking_criteria: The masking rule to apply for JSONPath matches.

    Example:
        >>> jpath = JPathMasking(
        ...     masking_criteria=MaskingCriteria(
        ...         action="$.user.password",
        ...         masking_type=MaskingType.MASK,
        ...         mask_value="********"
        ...     )
        ... )
    """

    masking_criteria: MaskingCriteria = Field(
        ...,
        alias="maskingCriteria",
        description="Masking rule for JSONPath matches"
    )

    model_config = ConfigDict(populate_by_name=True)


class RegexMasking(BaseModel):
    """
    Configuration for regex-based data masking.

    Defines masking rules that use regular expressions to identify and mask
    sensitive data patterns in request/response payloads.

    Attributes:
        masking_criteria: The masking rule to apply for regex matches.

    Example:
        >>> regex = RegexMasking(
        ...     masking_criteria=MaskingCriteria(
        ...         action="\\d{16}",  # Credit card pattern
        ...         masking_type=MaskingType.MASK,
        ...         mask_value="****-****-****-****"
        ...     )
        ... )
    """

    masking_criteria: MaskingCriteria = Field(
        ...,
        alias="maskingCriteria",
        description="Masking rule for regex matches"
    )

    model_config = ConfigDict(populate_by_name=True)


class RequestDataMaskingPolicy(BaseModel):
    """
    Policy for masking sensitive data in API requests and responses.

    Configures data masking rules to protect sensitive information such as
    passwords, credit card numbers, social security numbers, and other PII
    (Personally Identifiable Information). Supports both JSONPath-based and
    regex-based masking strategies.

    This policy helps ensure compliance with data protection regulations (GDPR,
    HIPAA, PCI-DSS) by preventing sensitive data from being logged or exposed
    in monitoring systems.

    Attributes:
        name: Policy template identifier, defaults to "requestDataMasking".
        description: Human-readable description of the policy's purpose.
        jpath_masking: JSONPath-based masking configuration.
        regex_masking: Regex-based masking configuration.
        same_for_transactional_logging: Whether to apply the same masking rules
            to transactional logs.
        apply_for_payload: Whether to apply masking to request/response payloads.

    Example:
        >>> policy = RequestDataMaskingPolicy(
        ...     jpath_masking=JPathMasking(
        ...         masking_criteria=MaskingCriteria(
        ...             action="$.user.password",
        ...             masking_type=MaskingType.MASK,
        ...             mask_value="********"
        ...         )
        ...     ),
        ...     regex_masking=RegexMasking(
        ...         masking_criteria=MaskingCriteria(
        ...             action="\\d{16}",
        ...             masking_type=MaskingType.MASK,
        ...             mask_value="****-****-****-****"
        ...         )
        ...     ),
        ...     same_for_transactional_logging=True,
        ...     apply_for_payload=True
        ... )
    """

    name: Optional[str] = Field(
        "requestDataMasking",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Data Masking",
        description="Human-readable description of the policy"
    )
    jpath_masking: JPathMasking = Field(
        ...,
        alias="jpathMasking",
        description="JSONPath-based masking configuration"
    )
    regex_masking: RegexMasking = Field(
        ...,
        alias="regexMasking",
        description="Regex-based masking configuration"
    )
    same_for_transactional_logging: bool = Field(
        True,
        alias="sameForTransactionalLogging",
        description="Whether to apply the same masking rules to transactional logs"
    )
    apply_for_payload: bool = Field(
        True,
        alias="applyForPayload",
        description="Whether to apply masking to request/response payloads"
    )

    model_config = ConfigDict(populate_by_name=True)


class ResponseDataMaskingPolicy(BaseModel):
    """
    Policy for masking sensitive data in API responses.

    Configures data masking rules to protect sensitive information in API
    responses before they are sent to clients. Similar to RequestDataMasking
    but specifically targets response data. Supports both JSONPath-based and
    regex-based masking strategies.

    This policy helps ensure compliance with data protection regulations (GDPR,
    HIPAA, PCI-DSS) by preventing sensitive data from being exposed to API
    consumers or logged in monitoring systems.

    Attributes:
        name: Policy template identifier, defaults to "responseDataMasking".
        description: Human-readable description of the policy's purpose.
        jpath_masking: JSONPath-based masking configuration.
        regex_masking: Regex-based masking configuration.
        same_for_transactional_logging: Whether to apply the same masking rules
            to transactional logs.
        apply_for_payload: Whether to apply masking to response payloads.

    Example:
        >>> policy = ResponseDataMaskingPolicy(
        ...     jpath_masking=JPathMasking(
        ...         masking_criteria=MaskingCriteria(
        ...             action="$.user.ssn",
        ...             masking_type=MaskingType.MASK,
        ...             mask_value="***-**-****"
        ...         )
        ...     ),
        ...     regex_masking=RegexMasking(
        ...         masking_criteria=MaskingCriteria(
        ...             action="\\d{3}-\\d{2}-\\d{4}",
        ...             masking_type=MaskingType.MASK,
        ...             mask_value="***-**-****"
        ...         )
        ...     ),
        ...     same_for_transactional_logging=True,
        ...     apply_for_payload=True
        ... )
    """

    name: Optional[str] = Field(
        "responseDataMasking",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "Data Masking",
        description="Human-readable description of the policy"
    )
    jpath_masking: JPathMasking = Field(
        ...,
        alias="jpathMasking",
        description="JSONPath-based masking configuration"
    )
    regex_masking: RegexMasking = Field(
        ...,
        alias="regexMasking",
        description="Regex-based masking configuration"
    )
    same_for_transactional_logging: bool = Field(
        True,
        alias="sameForTransactionalLogging",
        description="Whether to apply the same masking rules to transactional logs"
    )
    apply_for_payload: bool = Field(
        True,
        alias="applyForPayload",
        description="Whether to apply masking to response payloads"
    )

    model_config = ConfigDict(populate_by_name=True)


class HttpMethod(str, Enum):
    """
    Enumeration of HTTP methods for CORS configuration.

    Defines the HTTP methods that can be allowed in CORS policies.

    Attributes:
        GET: HTTP GET method.
        POST: HTTP POST method.
        PUT: HTTP PUT method.
        DELETE: HTTP DELETE method.
        PATCH: HTTP PATCH method.
        HEAD: HTTP HEAD method.
        OPTIONS: HTTP OPTIONS method.
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class CorsAttributes(BaseModel):
    """
    Configuration attributes for CORS (Cross-Origin Resource Sharing).

    Defines the CORS settings including allowed origins, headers, methods,
    credentials, and cache duration for preflight requests.

    Attributes:
        allowed_origins: List of origins allowed to access the API.
        allow_headers: List of HTTP headers allowed in requests.
        expose_headers: List of HTTP headers exposed to the client.
        allow_credentials: Whether to allow credentials (cookies, auth headers).
        allow_methods: List of HTTP methods allowed for cross-origin requests.
        max_age: Maximum age (in seconds) for caching preflight request results.

    Example:
        >>> attrs = CorsAttributes(
        ...     allowed_origins=["https://example.com"],
        ...     allow_headers=["Content-Type", "Authorization"],
        ...     expose_headers=["X-Custom-Header"],
        ...     allow_credentials=False,
        ...     allow_methods=[HttpMethod.GET, HttpMethod.POST],
        ...     max_age=3600
        ... )
    """

    allowed_origins: List[str] = Field(
        ...,
        alias="allowedOrigins",
        description="List of origins allowed to access the API"
    )
    allow_headers: List[str] = Field(
        ...,
        alias="allowHeaders",
        description="List of HTTP headers allowed in requests"
    )
    expose_headers: List[str] = Field(
        ...,
        alias="exposeHeaders",
        description="List of HTTP headers exposed to the client"
    )
    allow_credentials: bool = Field(
        False,
        alias="allowCredentials",
        description="Whether to allow credentials (cookies, authorization headers)"
    )
    allow_methods: List[HttpMethod] = Field(
        default=[
            HttpMethod.GET,
            HttpMethod.POST,
            HttpMethod.PUT,
            HttpMethod.DELETE,
            HttpMethod.PATCH,
            HttpMethod.HEAD
        ],
        alias="allowMethods",
        description="List of HTTP methods allowed for cross-origin requests"
    )
    max_age: int = Field(
        10,
        alias="maxAge",
        description="Maximum age in seconds for caching preflight request results"
    )

    model_config = ConfigDict(populate_by_name=True)


class CorsPolicy(BaseModel):
    """
    Policy for configuring Cross-Origin Resource Sharing (CORS).

    Configures CORS settings to control how web browsers handle cross-origin
    requests to the API. CORS is a security feature that restricts web pages
    from making requests to a different domain than the one serving the page.

    This policy allows you to specify which origins, headers, and methods are
    permitted, enabling secure cross-origin access to your APIs while maintaining
    security controls.

    Attributes:
        name: Policy template identifier, defaults to "cors".
        description: Human-readable description of the policy's purpose.
        cors_attributes: CORS configuration attributes.

    Example:
        >>> policy = CorsPolicy(
        ...     cors_attributes=CorsAttributes(
        ...         allowed_origins=["https://example.com", "https://app.example.com"],
        ...         allow_headers=["Content-Type", "Authorization"],
        ...         expose_headers=["X-Request-ID"],
        ...         allow_credentials=True,
        ...         allow_methods=[HttpMethod.GET, HttpMethod.POST, HttpMethod.PUT],
        ...         max_age=3600
        ...     )
        ... )
    """

    name: Optional[str] = Field(
        "cors",
        alias="templateKey",
        description="Policy template key identifier"
    )
    description: Optional[str] = Field(
        "CORS",
        description="Human-readable description of the policy"
    )
    cors_attributes: CorsAttributes = Field(
        ...,
        alias="corsAttributes",
        description="CORS configuration attributes"
    )

    model_config = ConfigDict(populate_by_name=True)