"""Models package for API Intelligence Plane.

This package contains all Pydantic models representing the core entities
of the API Intelligence Plane system.
"""

from backend.app.models.api import (
    API,
    APIStatus,
    AuthenticationType,
    CurrentMetrics,
    DiscoveryMethod,
    Endpoint,
    EndpointParameter,
    OwnershipInfo,
)
from backend.app.models.gateway import (
    ConnectionType,
    Gateway,
    GatewayCredentials,
    GatewayStatus,
    GatewayVendor,
)
from backend.app.models.metric import EndpointMetric, Metric
from backend.app.models.prediction import (
    ActualOutcome,
    ContributingFactor,
    Prediction,
    PredictionSeverity,
    PredictionStatus,
    PredictionType,
)
from backend.app.models.query import (
    InterpretedIntent,
    Query,
    QueryResults,
    QueryType,
    TimeRange,
    UserFeedback,
)
from backend.app.models.rate_limit import (
    AdaptationParameters,
    ConsumerTier,
    EnforcementAction,
    LimitThresholds,
    PolicyStatus,
    PolicyType,
    PriorityRule,
    RateLimitPolicy,
)
from backend.app.models.recommendation import (
    ActualImpact,
    EstimatedImpact,
    ImplementationEffort,
    OptimizationRecommendation,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
    ValidationResults,
)
from backend.app.models.vulnerability import (
    DetectionMethod,
    RemediationAction,
    RemediationType,
    VerificationStatus,
    Vulnerability,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    VulnerabilityType,
)

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
]

# Made with Bob
