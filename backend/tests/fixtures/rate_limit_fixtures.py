"""Test fixtures for rate limiting.

Provides reusable test data for rate limiting integration tests.
"""

from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from app.models.rate_limit import (
    RateLimitPolicy,
    PolicyType,
    PolicyStatus,
    EnforcementAction,
    LimitThresholds,
    AdaptationParameters,
    PriorityRule,
    ConsumerTier,
)


def create_sample_rate_limit_policy(
    api_id: str | None = None,
    policy_type: PolicyType = PolicyType.FIXED,
    status: PolicyStatus = PolicyStatus.INACTIVE,
    **kwargs
) -> RateLimitPolicy:
    """Create a sample rate limit policy.
    
    Args:
        api_id: Target API ID (generates random if None)
        policy_type: Type of rate limit policy
        status: Policy status
        **kwargs: Additional fields to override
        
    Returns:
        Sample RateLimitPolicy instance
    """
    defaults = {
        "id": uuid4(),
        "api_id": uuid4() if api_id is None else uuid4(api_id),
        "policy_name": f"Test {policy_type.value.title()} Policy",
        "policy_type": policy_type,
        "status": status,
        "limit_thresholds": LimitThresholds(
            requests_per_second=100,
            requests_per_minute=5000,
            requests_per_hour=250000,
            concurrent_requests=50,
        ),
        "enforcement_action": EnforcementAction.THROTTLE,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    # Add adaptive parameters for adaptive policies
    if policy_type == PolicyType.ADAPTIVE:
        defaults["adaptation_parameters"] = AdaptationParameters(
            learning_rate=0.1,
            adjustment_frequency=300,
            min_threshold=50,
            max_threshold=200,
        )
    
    # Add priority rules for priority-based policies
    if policy_type == PolicyType.PRIORITY_BASED:
        defaults["priority_rules"] = [
            PriorityRule(
                tier="premium",
                multiplier=2.0,
                guaranteed_throughput=200,
                burst_multiplier=1.5,
            ),
            PriorityRule(
                tier="standard",
                multiplier=1.0,
                guaranteed_throughput=100,
                burst_multiplier=1.2,
            ),
        ]
        defaults["consumer_tiers"] = [
            ConsumerTier(
                tier_name="premium",
                tier_level=1,
                rate_multiplier=2.0,
                priority_score=100,
            ),
            ConsumerTier(
                tier_name="standard",
                tier_level=2,
                rate_multiplier=1.0,
                priority_score=50,
            ),
        ]
    
    # Add burst allowance for burst allowance policies
    if policy_type == PolicyType.BURST_ALLOWANCE:
        defaults["burst_allowance"] = 500
    
    # Override with provided kwargs
    defaults.update(kwargs)
    
    return RateLimitPolicy(**defaults)


def create_fixed_policy(api_id: str | None = None, **kwargs) -> RateLimitPolicy:
    """Create a fixed rate limit policy.
    
    Args:
        api_id: Target API ID
        **kwargs: Additional fields to override
        
    Returns:
        Fixed rate limit policy
    """
    return create_sample_rate_limit_policy(
        api_id=api_id,
        policy_type=PolicyType.FIXED,
        **kwargs
    )


def create_adaptive_policy(api_id: str | None = None, **kwargs) -> RateLimitPolicy:
    """Create an adaptive rate limit policy.
    
    Args:
        api_id: Target API ID
        **kwargs: Additional fields to override
        
    Returns:
        Adaptive rate limit policy
    """
    return create_sample_rate_limit_policy(
        api_id=api_id,
        policy_type=PolicyType.ADAPTIVE,
        **kwargs
    )


def create_priority_based_policy(api_id: str | None = None, **kwargs) -> RateLimitPolicy:
    """Create a priority-based rate limit policy.
    
    Args:
        api_id: Target API ID
        **kwargs: Additional fields to override
        
    Returns:
        Priority-based rate limit policy
    """
    return create_sample_rate_limit_policy(
        api_id=api_id,
        policy_type=PolicyType.PRIORITY_BASED,
        **kwargs
    )


def create_burst_allowance_policy(api_id: str | None = None, **kwargs) -> RateLimitPolicy:
    """Create a burst allowance rate limit policy.
    
    Args:
        api_id: Target API ID
        **kwargs: Additional fields to override
        
    Returns:
        Burst allowance rate limit policy
    """
    return create_sample_rate_limit_policy(
        api_id=api_id,
        policy_type=PolicyType.BURST_ALLOWANCE,
        **kwargs
    )


def create_active_policy(api_id: str | None = None, **kwargs) -> RateLimitPolicy:
    """Create an active rate limit policy.
    
    Args:
        api_id: Target API ID
        **kwargs: Additional fields to override
        
    Returns:
        Active rate limit policy
    """
    return create_sample_rate_limit_policy(
        api_id=api_id,
        status=PolicyStatus.ACTIVE,
        applied_at=datetime.utcnow(),
        **kwargs
    )


def create_policy_with_effectiveness(
    api_id: str | None = None,
    effectiveness_score: float = 0.85,
    **kwargs
) -> RateLimitPolicy:
    """Create a rate limit policy with effectiveness tracking.
    
    Args:
        api_id: Target API ID
        effectiveness_score: Effectiveness score (0-1)
        **kwargs: Additional fields to override
        
    Returns:
        Rate limit policy with effectiveness score
    """
    return create_sample_rate_limit_policy(
        api_id=api_id,
        status=PolicyStatus.ACTIVE,
        applied_at=datetime.utcnow() - timedelta(hours=24),
        last_adjusted_at=datetime.utcnow() - timedelta(hours=1),
        effectiveness_score=effectiveness_score,
        **kwargs
    )


def create_multiple_policies(
    api_id: str | None = None,
    count: int = 3,
    policy_types: List[PolicyType] | None = None,
) -> List[RateLimitPolicy]:
    """Create multiple rate limit policies.
    
    Args:
        api_id: Target API ID (same for all policies)
        count: Number of policies to create
        policy_types: List of policy types (cycles through if provided)
        
    Returns:
        List of rate limit policies
    """
    if policy_types is None:
        policy_types = [PolicyType.FIXED, PolicyType.ADAPTIVE, PolicyType.PRIORITY_BASED]
    
    policies = []
    for i in range(count):
        policy_type = policy_types[i % len(policy_types)]
        policy = create_sample_rate_limit_policy(
            api_id=api_id,
            policy_type=policy_type,
            policy_name=f"Test Policy {i + 1}",
        )
        policies.append(policy)
    
    return policies


def create_policy_lifecycle_sequence(api_id: str | None = None) -> List[RateLimitPolicy]:
    """Create a sequence of policies showing lifecycle progression.
    
    Args:
        api_id: Target API ID
        
    Returns:
        List of policies in different lifecycle stages
    """
    base_time = datetime.utcnow() - timedelta(days=7)
    
    return [
        # Newly created, inactive
        create_sample_rate_limit_policy(
            api_id=api_id,
            policy_name="New Policy",
            status=PolicyStatus.INACTIVE,
            created_at=base_time,
            updated_at=base_time,
        ),
        # Testing phase
        create_sample_rate_limit_policy(
            api_id=api_id,
            policy_name="Testing Policy",
            status=PolicyStatus.TESTING,
            created_at=base_time + timedelta(days=1),
            updated_at=base_time + timedelta(days=1),
            applied_at=base_time + timedelta(days=1),
        ),
        # Active with good effectiveness
        create_policy_with_effectiveness(
            api_id=api_id,
            policy_name="Active Policy",
            effectiveness_score=0.92,
        ),
        # Active but needs adjustment
        create_policy_with_effectiveness(
            api_id=api_id,
            policy_name="Needs Adjustment Policy",
            effectiveness_score=0.65,
        ),
    ]


def create_traffic_simulation_data(
    hours: int = 24,
    base_throughput: float = 100.0,
    variation: float = 0.3,
) -> List[dict]:
    """Create simulated traffic data for testing.
    
    Args:
        hours: Number of hours of data to generate
        base_throughput: Base throughput in requests/second
        variation: Variation factor (0-1)
        
    Returns:
        List of traffic data points
    """
    now = datetime.utcnow()
    data = []
    
    for i in range(hours):
        timestamp = now - timedelta(hours=hours - 1 - i)
        hour = timestamp.hour
        
        # Business hours pattern
        if 9 <= hour <= 17:
            throughput = base_throughput * (1.5 + variation * (i % 3) / 3)
        else:
            throughput = base_throughput * (0.5 + variation * (i % 3) / 3)
        
        data.append({
            "timestamp": timestamp,
            "throughput": throughput,
            "error_rate": 0.01 + (i % 3) * 0.005,
            "response_time": 100.0 + (i % 5) * 20,
        })
    
    return data


# Made with Bob