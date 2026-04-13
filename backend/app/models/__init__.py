"""Models package for API Intelligence Plane.

This package contains all Pydantic models representing the core entities
of the API Intelligence Plane system.
"""

from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    EndpointParameter,
    OwnershipInfo,
)
from app.models.gateway import (
    ConnectionType,
    Gateway,
    GatewayCredentials,
    GatewayStatus,
    GatewayVendor,
)
from app.models.base.metric import EndpointMetric, Metric

# Backward compatibility alias
CurrentMetrics = Metric
from app.models.prediction import (
    ActualOutcome,
    ContributingFactor,
    Prediction,
    PredictionSeverity,
    PredictionStatus,
    PredictionType,
)
from app.models.query import (
    InterpretedIntent,
    Query,
    QueryResults,
    QueryType,
    TimeRange,
    UserFeedback,
)
from app.models.rate_limit import (
    AdaptationParameters,
    ConsumerTier,
    EnforcementAction,
    LimitThresholds,
    PolicyStatus,
    PolicyType,
    PriorityRule,
    RateLimitPolicy,
)
from app.models.recommendation import (
    ActualImpact,
    EstimatedImpact,
    ImplementationEffort,
    OptimizationRecommendation,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
    ValidationResults,
)
from app.models.vulnerability import (
    DetectionMethod,
    RemediationAction,
    RemediationType,
    VerificationStatus,
    Vulnerability,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    VulnerabilityType,
)
from app.models.base.transaction import (
    CacheStatus,
    ErrorOrigin,
    EventStatus,
    EventType,
    ExternalCall,
    ExternalCallType,
    TransactionalLog,
)
from app.models.base.metric import (
    TimeBucket,
)

# Alias for backward compatibility
Metrics = Metric

__all__ = [
    # API models
    "API",
    "APIStatus",
    "AuthenticationType",
    "CurrentMetrics",
    "DiscoveryMethod",
    "Endpoint",
    "EndpointParameter",
    "OwnershipInfo",
    # Gateway models
    "ConnectionType",
    "Gateway",
    "GatewayCredentials",
    "GatewayStatus",
    "GatewayVendor",
    # Metric models
    "EndpointMetric",
    "Metric",
    # Prediction models
    "ActualOutcome",
    "ContributingFactor",
    "Prediction",
    "PredictionSeverity",
    "PredictionStatus",
    "PredictionType",
    # Query models
    "InterpretedIntent",
    "Query",
    "QueryResults",
    "QueryType",
    "TimeRange",
    "UserFeedback",
    # Rate Limit models
    "AdaptationParameters",
    "ConsumerTier",
    "EnforcementAction",
    "LimitThresholds",
    "PolicyStatus",
    "PolicyType",
    "PriorityRule",
    "RateLimitPolicy",
    # Recommendation models
    "ActualImpact",
    "EstimatedImpact",
    "ImplementationEffort",
    "OptimizationRecommendation",
    "RecommendationPriority",
    "RecommendationStatus",
    "RecommendationType",
    "ValidationResults",
    # Vulnerability models
    "DetectionMethod",
    "RemediationAction",
    "RemediationType",
    "VerificationStatus",
    "Vulnerability",
    "VulnerabilitySeverity",
    "VulnerabilityStatus",
    "VulnerabilityType",
    # WebMethods Analytics models
    "CacheStatus",
    "ErrorOrigin",
    "EventStatus",
    "EventType",
    "ExternalCall",
    "ExternalCallType",
    "Metrics",
    "TimeBucket",
    "TransactionalLog",
]

# Made with Bob
