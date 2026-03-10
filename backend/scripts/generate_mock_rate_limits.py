#!/usr/bin/env python3
"""
Generate mock rate limit policies for testing and demonstration.

This script creates sample rate limit policies of different types
to populate the system for UI testing and validation.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from uuid import uuid4
from app.db.client import get_client
from app.db.repositories.rate_limit_repository import RateLimitPolicyRepository
from app.models.rate_limit import (
    RateLimitPolicy,
    PolicyType,
    PolicyStatus,
    EnforcementAction,
    LimitThresholds,
    AdaptationParameters,
    PriorityRule,
)


def generate_fixed_policy() -> RateLimitPolicy:
    """Generate a fixed rate limit policy."""
    return RateLimitPolicy(
        id=uuid4(),
        api_id=uuid4(),
        policy_name="API Gateway Standard Limit",
        policy_type=PolicyType.FIXED,
        status=PolicyStatus.ACTIVE,
        limit_thresholds=LimitThresholds(
            requests_per_second=100,
            requests_per_minute=5000,
            requests_per_hour=250000,
            concurrent_requests=None,
        ),
        priority_rules=None,
        burst_allowance=200,
        adaptation_parameters=None,
        consumer_tiers=None,
        enforcement_action=EnforcementAction.THROTTLE,
        applied_at=datetime.utcnow() - timedelta(days=30),
        last_adjusted_at=None,
        effectiveness_score=0.92,
        metadata={"description": "Standard fixed rate limit for public API endpoints"},
        created_at=datetime.utcnow() - timedelta(days=30),
        updated_at=datetime.utcnow() - timedelta(days=1),
    )


def generate_adaptive_policy() -> RateLimitPolicy:
    """Generate an adaptive rate limit policy."""
    return RateLimitPolicy(
        id=uuid4(),
        api_id=uuid4(),
        policy_name="Payment API Adaptive Limit",
        policy_type=PolicyType.ADAPTIVE,
        status=PolicyStatus.ACTIVE,
        limit_thresholds=LimitThresholds(
            requests_per_second=50,
            requests_per_minute=2500,
            requests_per_hour=100000,
            concurrent_requests=None,
        ),
        priority_rules=None,
        burst_allowance=100,
        adaptation_parameters=AdaptationParameters(
            learning_rate=0.1,
            adjustment_frequency=300,
            min_threshold=25,
            max_threshold=100,
        ),
        consumer_tiers=None,
        enforcement_action=EnforcementAction.THROTTLE,
        applied_at=datetime.utcnow() - timedelta(days=15),
        last_adjusted_at=datetime.utcnow() - timedelta(hours=2),
        effectiveness_score=0.88,
        metadata={"description": "Adaptive rate limiting for payment processing API based on system load"},
        created_at=datetime.utcnow() - timedelta(days=15),
        updated_at=datetime.utcnow() - timedelta(hours=2),
    )


def generate_priority_policy() -> RateLimitPolicy:
    """Generate a priority-based rate limit policy."""
    return RateLimitPolicy(
        id=uuid4(),
        api_id=uuid4(),
        policy_name="User API Priority Tiers",
        policy_type=PolicyType.PRIORITY_BASED,
        status=PolicyStatus.ACTIVE,
        limit_thresholds=LimitThresholds(
            requests_per_second=75,
            requests_per_minute=4000,
            requests_per_hour=200000,
            concurrent_requests=None,
        ),
        burst_allowance=150,
        priority_rules=[
            PriorityRule(
                tier="premium",
                multiplier=2.0,
                guaranteed_throughput=50,
                burst_multiplier=1.5,
            ),
            PriorityRule(
                tier="standard",
                multiplier=1.0,
                guaranteed_throughput=25,
                burst_multiplier=1.2,
            ),
            PriorityRule(
                tier="free",
                multiplier=0.5,
                guaranteed_throughput=10,
                burst_multiplier=1.0,
            ),
        ],
        adaptation_parameters=None,
        consumer_tiers=None,
        enforcement_action=EnforcementAction.QUEUE,
        applied_at=datetime.utcnow() - timedelta(days=20),
        last_adjusted_at=None,
        effectiveness_score=0.95,
        metadata={"description": "Priority-based rate limiting with different tiers for user API"},
        created_at=datetime.utcnow() - timedelta(days=20),
        updated_at=datetime.utcnow() - timedelta(days=3),
    )


def generate_burst_policy() -> RateLimitPolicy:
    """Generate a burst allowance rate limit policy."""
    return RateLimitPolicy(
        id=uuid4(),
        api_id=uuid4(),
        policy_name="Analytics API Burst Allowance",
        policy_type=PolicyType.BURST_ALLOWANCE,
        status=PolicyStatus.TESTING,
        limit_thresholds=LimitThresholds(
            requests_per_second=30,
            requests_per_minute=1500,
            requests_per_hour=75000,
            concurrent_requests=None,
        ),
        priority_rules=None,
        burst_allowance=300,
        adaptation_parameters=None,
        consumer_tiers=None,
        enforcement_action=EnforcementAction.THROTTLE,
        applied_at=datetime.utcnow() - timedelta(days=3),
        last_adjusted_at=None,
        effectiveness_score=0.78,
        metadata={"description": "Burst allowance for analytics API to handle periodic spikes"},
        created_at=datetime.utcnow() - timedelta(days=5),
        updated_at=datetime.utcnow() - timedelta(hours=6),
    )


def generate_inactive_policy() -> RateLimitPolicy:
    """Generate an inactive rate limit policy."""
    return RateLimitPolicy(
        id=uuid4(),
        api_id=uuid4(),
        policy_name="Legacy API Rate Limit (Inactive)",
        policy_type=PolicyType.FIXED,
        status=PolicyStatus.INACTIVE,
        limit_thresholds=LimitThresholds(
            requests_per_second=20,
            requests_per_minute=1000,
            requests_per_hour=50000,
            concurrent_requests=None,
        ),
        priority_rules=None,
        burst_allowance=50,
        adaptation_parameters=None,
        consumer_tiers=None,
        enforcement_action=EnforcementAction.REJECT,
        applied_at=None,
        last_adjusted_at=None,
        effectiveness_score=None,
        metadata={"description": "Rate limit for legacy API - currently inactive pending migration"},
        created_at=datetime.utcnow() - timedelta(days=60),
        updated_at=datetime.utcnow() - timedelta(days=10),
    )


async def main():
    """Generate and store mock rate limit policies."""
    print("Generating mock rate limit policies...")
    
    # Initialize repository
    client = get_client()
    repo = RateLimitPolicyRepository()
    
    # Generate policies
    policies = [
        generate_fixed_policy(),
        generate_adaptive_policy(),
        generate_priority_policy(),
        generate_burst_policy(),
        generate_inactive_policy(),
    ]
    
    # Store policies
    created_count = 0
    for policy in policies:
        try:
            created = repo.create_policy(policy)
            print(f"✓ Created policy: {created.policy_name} ({created.policy_type.value})")
            created_count += 1
        except Exception as e:
            print(f"✗ Failed to create policy {policy.policy_name}: {e}")
    
    print(f"\nSuccessfully created {created_count}/{len(policies)} rate limit policies")
    
    # List all policies
    print("\nCurrent rate limit policies:")
    all_policies, total = repo.list_all()
    for p in all_policies:
        status_icon = "🟢" if p.status == PolicyStatus.ACTIVE else "🟡" if p.status == PolicyStatus.TESTING else "⚪"
        print(f"  {status_icon} {p.policy_name} - {p.policy_type.value} ({p.status.value})")


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
