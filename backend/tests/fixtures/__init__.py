"""Test fixtures package."""

from .api_fixtures import (
    create_api_with_definition,
    create_api_with_performance_policies,
    create_api_with_security_policies,
    create_deprecated_api,
    create_sample_api,
    create_shadow_api,
)
from .metric_fixtures import (
    create_degrading_metric,
    create_metric_time_series,
    create_metric_with_cache,
    create_metric_with_endpoints,
    create_sample_metric,
    create_stable_metric,
)
from .optimization_fixtures import (
    create_caching_recommendation,
    create_compression_recommendation,
    create_sample_recommendation,
)
from .prediction_fixtures import (
    create_metrics_series,
    create_prediction_with_severity,
)
from .rate_limit_fixtures import (
    create_adaptive_policy,
    create_burst_allowance_policy,
    create_fixed_policy,
    create_priority_based_policy,
    create_sample_rate_limit_policy,
)
__all__ = [
    # API fixtures
    "create_sample_api",
    "create_shadow_api",
    "create_api_with_security_policies",
    "create_api_with_performance_policies",
    "create_deprecated_api",
    "create_api_with_definition",
    # Metric fixtures
    "create_sample_metric",
    "create_stable_metric",
    "create_degrading_metric",
    "create_metric_with_cache",
    "create_metric_with_endpoints",
    "create_metric_time_series",
    # Prediction fixtures
    "create_prediction_with_severity",
    "create_metrics_series",
    # Optimization fixtures
    "create_sample_recommendation",
    "create_caching_recommendation",
    "create_compression_recommendation",
    # Rate limit fixtures
    "create_sample_rate_limit_policy",
    "create_fixed_policy",
    "create_adaptive_policy",
    "create_priority_based_policy",
    "create_burst_allowance_policy",
]

# Made with Bob
