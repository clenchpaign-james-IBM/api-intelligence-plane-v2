"""RateLimitPolicy model for API Intelligence Plane.

Represents a rate limiting configuration with target API, limit thresholds,
priority rules, and adaptation parameters.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PolicyType(str, Enum):
    """Type of rate limit policy strategy.
    
    Defines the rate limiting approach and behavior for controlling API traffic.
    
    Attributes:
        FIXED: Static rate limits that remain constant regardless of traffic patterns
              or system load. Simple and predictable.
        ADAPTIVE: Dynamic rate limits that adjust automatically based on system load,
                 performance metrics, and traffic patterns. Optimizes resource utilization.
        PRIORITY_BASED: Rate limits vary by consumer tier or priority level. Premium
                       users get higher limits than standard users.
        BURST_ALLOWANCE: Allows temporary traffic bursts above the base rate limit,
                        useful for handling legitimate traffic spikes.
    """

    FIXED = "fixed"
    ADAPTIVE = "adaptive"
    PRIORITY_BASED = "priority_based"
    BURST_ALLOWANCE = "burst_allowance"


class PolicyStatus(str, Enum):
    """Rate limit policy activation status.
    
    Indicates whether the policy is currently being enforced on the gateway.
    
    Attributes:
        ACTIVE: Policy is actively enforced. Traffic exceeding limits will be throttled
               or rejected according to the enforcement action.
        INACTIVE: Policy exists but is not enforced. Useful for maintaining policy
                 definitions without active enforcement.
        TESTING: Policy is in testing mode. May log violations without enforcing limits,
                allowing validation before full activation.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"


class EnforcementAction(str, Enum):
    """Action taken when rate limit is exceeded.
    
    Defines how the gateway responds to requests that exceed the rate limit.
    
    Attributes:
        THROTTLE: Slow down request processing by adding delays. Requests are still
                 processed but with increased latency. Provides graceful degradation.
        REJECT: Immediately reject excess requests with HTTP 429 (Too Many Requests).
               Protects backend services but may impact user experience.
        QUEUE: Place excess requests in a queue for later processing. Requests are
              delayed but eventually processed. Requires queue management infrastructure.
    """

    THROTTLE = "throttle"
    REJECT = "reject"
    QUEUE = "queue"


class LimitThresholds(BaseModel):
    """Rate limit threshold values.
    
    Defines the maximum allowed request rates across different time windows.
    At least one threshold must be specified.
    
    Attributes:
        requests_per_second: Maximum requests allowed per second. Useful for protecting
                           against rapid bursts and ensuring consistent performance.
        requests_per_minute: Maximum requests allowed per minute. Common for API quotas
                           and medium-term rate limiting.
        requests_per_hour: Maximum requests allowed per hour. Useful for daily quota
                         management and long-term capacity planning.
        concurrent_requests: Maximum number of simultaneous in-flight requests. Protects
                           against connection exhaustion and resource contention.
    """

    requests_per_second: Optional[int] = Field(
        None, ge=0, description="Requests per second limit"
    )
    requests_per_minute: Optional[int] = Field(
        None, ge=0, description="Requests per minute limit"
    )
    requests_per_hour: Optional[int] = Field(
        None, ge=0, description="Requests per hour limit"
    )
    concurrent_requests: Optional[int] = Field(
        None, ge=0, description="Concurrent requests limit"
    )

    @field_validator("requests_per_second", "requests_per_minute", "requests_per_hour", "concurrent_requests")
    @classmethod
    def validate_at_least_one_threshold(cls, v, info) -> Optional[int]:
        """Validate at least one threshold is defined."""
        # This will be checked at the model level
        return v


class PriorityRule(BaseModel):
    """Priority-based rate limiting rule for consumer tiers.
    
    Defines rate limit adjustments for different consumer priority levels,
    enabling differentiated service levels.
    
    Attributes:
        tier: Name of the consumer tier (e.g., 'premium', 'standard', 'free').
             Must be unique within a policy.
        multiplier: Rate limit multiplier applied to base thresholds. For example,
                   2.0 means this tier gets 2x the base rate limit.
        guaranteed_throughput: Minimum guaranteed requests per second for this tier,
                             regardless of system load. Ensures SLA compliance.
        burst_multiplier: Additional multiplier for burst allowance. For example,
                        1.5 means this tier can burst to 1.5x their normal limit.
    """

    tier: str = Field(
        ...,
        description="Name of the consumer tier (e.g., 'premium', 'standard', 'free'). Must be unique within a policy."
    )
    multiplier: float = Field(
        ...,
        gt=0,
        description="Rate limit multiplier applied to base thresholds. For example, 2.0 means this tier gets 2x the base rate limit."
    )
    guaranteed_throughput: int = Field(
        ...,
        ge=0,
        description="Minimum guaranteed requests per second for this tier, regardless of system load. Ensures SLA compliance."
    )
    burst_multiplier: float = Field(
        ...,
        gt=0,
        description="Additional multiplier for burst allowance. For example, 1.5 means this tier can burst to 1.5x their normal limit."
    )


class AdaptationParameters(BaseModel):
    """Adaptive rate limit policy configuration.
    
    Controls how adaptive policies automatically adjust rate limits based on
    system performance and traffic patterns.
    
    Attributes:
        learning_rate: Speed of adaptation (0.0 to 1.0). Higher values mean faster
                      response to changes but more volatility. Lower values provide
                      stability but slower adaptation. Typical: 0.1-0.3.
        adjustment_frequency: How often (in seconds) to recalculate and adjust rate limits.
                            Lower values provide faster response but higher overhead.
                            Typical: 60-300 seconds.
        min_threshold: Minimum rate limit floor. Prevents adaptive algorithm from
                      setting limits too low during low-traffic periods.
        max_threshold: Maximum rate limit ceiling. Prevents adaptive algorithm from
                      setting limits too high, protecting backend capacity.
    """

    learning_rate: float = Field(
        ...,
        gt=0,
        le=1,
        description="Speed of adaptation (0.0 to 1.0). Higher values mean faster response to changes but more volatility. Lower values provide stability but slower adaptation. Typical: 0.1-0.3."
    )
    adjustment_frequency: int = Field(
        ...,
        gt=0,
        description="How often (in seconds) to recalculate and adjust rate limits. Lower values provide faster response but higher overhead. Typical: 60-300 seconds."
    )
    min_threshold: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum rate limit floor. Prevents adaptive algorithm from setting limits too low during low-traffic periods."
    )
    max_threshold: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum rate limit ceiling. Prevents adaptive algorithm from setting limits too high, protecting backend capacity."
    )


class ConsumerTier(BaseModel):
    """Consumer tier definition for differentiated service levels.
    
    Defines a consumer tier with associated rate limit adjustments and priority.
    
    Attributes:
        tier_name: Human-readable name of the tier (e.g., 'Enterprise', 'Professional', 'Free').
        tier_level: Numeric tier level where 1 is the highest priority tier. Used for
                   ordering and priority resolution. Lower numbers = higher priority.
        rate_multiplier: Multiplier applied to base rate limits for this tier. For example,
                        3.0 means this tier gets 3x the base rate limit.
        priority_score: Numeric priority score used for request prioritization when
                       system is under load. Higher scores get preferential treatment.
    """

    tier_name: str = Field(
        ...,
        description="Human-readable name of the tier (e.g., 'Enterprise', 'Professional', 'Free')."
    )
    tier_level: int = Field(
        ...,
        ge=1,
        description="Numeric tier level where 1 is the highest priority tier. Used for ordering and priority resolution. Lower numbers = higher priority."
    )
    rate_multiplier: float = Field(
        ...,
        gt=0,
        description="Multiplier applied to base rate limits for this tier. For example, 3.0 means this tier gets 3x the base rate limit."
    )
    priority_score: int = Field(
        ...,
        ge=0,
        description="Numeric priority score used for request prioritization when system is under load. Higher scores get preferential treatment."
    )


class RateLimitPolicy(BaseModel):
    """RateLimitPolicy entity representing a rate limiting configuration.

    Attributes:
        id: Unique identifier (UUID v4)
        api_id: Target API
        policy_name: Policy name (1-255 characters)
        policy_type: Type of policy
        status: Policy status
        limit_thresholds: Rate limit values
        priority_rules: Priority-based rules
        burst_allowance: Burst request allowance
        adaptation_parameters: Adaptive policy config
        consumer_tiers: Consumer tier definitions
        enforcement_action: Action on limit breach
        applied_at: When policy activated
        last_adjusted_at: Last adaptation
        effectiveness_score: Policy effectiveness (0-1)
        metadata: Additional data
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    api_id: UUID = Field(..., description="Target API")
    policy_name: str = Field(..., min_length=1, max_length=255, description="Policy name")
    policy_type: PolicyType = Field(..., description="Type of policy")
    status: PolicyStatus = Field(
        default=PolicyStatus.INACTIVE, description="Policy status"
    )
    limit_thresholds: LimitThresholds = Field(..., description="Rate limit values")
    priority_rules: Optional[list[PriorityRule]] = Field(
        None, description="Priority-based rules"
    )
    burst_allowance: Optional[int] = Field(
        None, ge=0, description="Burst request allowance"
    )
    adaptation_parameters: Optional[AdaptationParameters] = Field(
        None, description="Adaptive policy config"
    )
    consumer_tiers: Optional[list[ConsumerTier]] = Field(
        None, description="Consumer tier definitions"
    )
    enforcement_action: EnforcementAction = Field(..., description="Action on limit breach")
    applied_at: Optional[datetime] = Field(None, description="When policy activated")
    last_adjusted_at: Optional[datetime] = Field(None, description="Last adaptation")
    effectiveness_score: Optional[float] = Field(
        None, ge=0, le=1, description="Policy effectiveness (0-1)"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional data")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @field_validator("limit_thresholds")
    @classmethod
    def validate_limit_thresholds(cls, v: LimitThresholds) -> LimitThresholds:
        """Validate at least one threshold is defined."""
        if not any(
            [
                v.requests_per_second,
                v.requests_per_minute,
                v.requests_per_hour,
                v.concurrent_requests,
            ]
        ):
            raise ValueError("At least one threshold must be defined in limit_thresholds")
        return v

    @field_validator("burst_allowance")
    @classmethod
    def validate_burst_allowance(cls, v: Optional[int], info) -> Optional[int]:
        """Validate burst_allowance <= requests_per_second * 10."""
        if v is not None and "limit_thresholds" in info.data:
            thresholds = info.data["limit_thresholds"]
            if thresholds.requests_per_second:
                max_burst = thresholds.requests_per_second * 10
                if v > max_burst:
                    raise ValueError(
                        f"burst_allowance ({v}) must be <= requests_per_second * 10 ({max_burst})"
                    )
        return v

    @field_validator("priority_rules")
    @classmethod
    def validate_priority_rules(
        cls, v: Optional[list[PriorityRule]]
    ) -> Optional[list[PriorityRule]]:
        """Validate priority_rules tier names are unique."""
        if v:
            tier_names = [rule.tier for rule in v]
            if len(tier_names) != len(set(tier_names)):
                raise ValueError("priority_rules tier names must be unique")
        return v

    @field_validator("adaptation_parameters")
    @classmethod
    def validate_adaptation_parameters(
        cls, v: Optional[AdaptationParameters], info
    ) -> Optional[AdaptationParameters]:
        """Validate if policy_type is adaptive, adaptation_parameters must be set."""
        if "policy_type" in info.data:
            policy_type = info.data["policy_type"]
            if policy_type == PolicyType.ADAPTIVE and v is None:
                raise ValueError(
                    "adaptation_parameters must be set when policy_type is adaptive"
                )
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440006",
                "api_id": "550e8400-e29b-41d4-a716-446655440001",
                "policy_name": "User API Rate Limit",
                "policy_type": "priority_based",
                "status": "active",
                "limit_thresholds": {
                    "requests_per_second": 100,
                    "requests_per_minute": 5000,
                    "requests_per_hour": 250000,
                    "concurrent_requests": 50,
                },
                "priority_rules": [
                    {
                        "tier": "premium",
                        "multiplier": 2.0,
                        "guaranteed_throughput": 200,
                        "burst_multiplier": 1.5,
                    },
                    {
                        "tier": "standard",
                        "multiplier": 1.0,
                        "guaranteed_throughput": 100,
                        "burst_multiplier": 1.2,
                    },
                ],
                "burst_allowance": 500,
                "enforcement_action": "throttle",
                "applied_at": "2026-03-09T10:00:00Z",
                "effectiveness_score": 0.92,
            }
        }

# Made with Bob
