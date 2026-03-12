"""
Rate Limiting Service

Handles intelligent rate limiting with adaptive policies, effectiveness tracking,
and dynamic threshold adjustments based on traffic patterns and business priorities.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import statistics

from app.db.repositories.rate_limit_repository import RateLimitPolicyRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
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
from app.models.metric import Metric

logger = logging.getLogger(__name__)


class RateLimitService:
    """Service for managing intelligent rate limiting policies."""

    # Default thresholds
    DEFAULT_REQUESTS_PER_SECOND = 100
    DEFAULT_REQUESTS_PER_MINUTE = 5000
    DEFAULT_REQUESTS_PER_HOUR = 250000
    DEFAULT_CONCURRENT_REQUESTS = 50

    # Adaptive policy parameters
    DEFAULT_LEARNING_RATE = 0.1  # 10% adjustment per cycle
    DEFAULT_ADJUSTMENT_FREQUENCY = 300  # 5 minutes in seconds
    MIN_THRESHOLD_MULTIPLIER = 0.5  # Can reduce to 50% of baseline
    MAX_THRESHOLD_MULTIPLIER = 2.0  # Can increase to 200% of baseline

    # Effectiveness thresholds
    HIGH_EFFECTIVENESS_SCORE = 0.8  # 80%+
    LOW_EFFECTIVENESS_SCORE = 0.5  # Below 50%

    # Analysis window
    ANALYSIS_WINDOW_HOURS = 24

    def __init__(
        self,
        rate_limit_repository: RateLimitPolicyRepository,
        metrics_repository: MetricsRepository,
        api_repository: APIRepository,
    ):
        """
        Initialize the Rate Limiting Service.

        Args:
            rate_limit_repository: Repository for rate limit policy operations
            metrics_repository: Repository for metrics operations
            api_repository: Repository for API operations
        """
        self.rate_limit_repo = rate_limit_repository
        self.metrics_repo = metrics_repository
        self.api_repo = api_repository

    def create_policy(
        self,
        api_id: UUID,
        policy_name: str,
        policy_type: PolicyType,
        limit_thresholds: LimitThresholds,
        enforcement_action: EnforcementAction = EnforcementAction.THROTTLE,
        priority_rules: Optional[List[PriorityRule]] = None,
        burst_allowance: Optional[int] = None,
        adaptation_parameters: Optional[AdaptationParameters] = None,
        consumer_tiers: Optional[List[ConsumerTier]] = None,
    ) -> RateLimitPolicy:
        """
        Create a new rate limit policy.

        Args:
            api_id: Target API UUID
            policy_name: Name for the policy
            policy_type: Type of rate limiting policy
            limit_thresholds: Rate limit threshold values
            enforcement_action: Action to take on limit breach
            priority_rules: Optional priority-based rules
            burst_allowance: Optional burst request allowance
            adaptation_parameters: Optional adaptive policy configuration
            consumer_tiers: Optional consumer tier definitions

        Returns:
            Created RateLimitPolicy
        """
        logger.info(f"Creating rate limit policy '{policy_name}' for API {api_id}")

        # Validate API exists
        api = self.api_repo.get(str(api_id))
        if not api:
            raise ValueError(f"API {api_id} not found")

        # Create policy
        policy = RateLimitPolicy(
            api_id=api_id,
            policy_name=policy_name,
            policy_type=policy_type,
            status=PolicyStatus.INACTIVE,
            limit_thresholds=limit_thresholds,
            enforcement_action=enforcement_action,
            priority_rules=priority_rules,
            burst_allowance=burst_allowance,
            adaptation_parameters=adaptation_parameters,
            consumer_tiers=consumer_tiers,
        )

        return self.rate_limit_repo.create_policy(policy)

    def activate_policy(self, policy_id: UUID) -> Optional[RateLimitPolicy]:
        """
        Activate a rate limit policy.

        Args:
            policy_id: Policy UUID to activate

        Returns:
            Activated policy if found, None otherwise
        """
        logger.info(f"Activating rate limit policy {policy_id}")
        return self.rate_limit_repo.activate_policy(policy_id)

    def deactivate_policy(self, policy_id: UUID) -> Optional[RateLimitPolicy]:
        """
        Deactivate a rate limit policy.

        Args:
            policy_id: Policy UUID to deactivate

        Returns:
            Deactivated policy if found, None otherwise
        """
        logger.info(f"Deactivating rate limit policy {policy_id}")

        policy = self.rate_limit_repo.get_by_id(policy_id)
        if not policy:
            return None

        policy.status = PolicyStatus.INACTIVE
        return self.rate_limit_repo.update_policy(policy)

    async def apply_policy_to_gateway(
        self, policy_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply a rate limit policy to the actual Gateway.

        This method:
        1. Retrieves the policy from the database
        2. Gets the API and Gateway information
        3. Creates a Gateway adapter
        4. Applies the policy to the Gateway via the adapter
        5. Updates the policy status and applied_at timestamp

        Args:
            policy_id: Policy UUID to apply

        Returns:
            Dictionary with application result:
                - success: bool
                - policy_id: str
                - api_id: str
                - gateway_id: str
                - message: str
                - applied_at: str (ISO format)

        Raises:
            ValueError: If policy or API not found
            RuntimeError: If Gateway connection or policy application fails
        """
        from app.db.repositories.gateway_repository import GatewayRepository
        from app.adapters.factory import create_gateway_adapter

        logger.info(f"Applying rate limit policy {policy_id} to Gateway")

        # Get policy
        policy = self.rate_limit_repo.get_by_id(policy_id)
        if not policy:
            raise ValueError(f"Rate limit policy {policy_id} not found")

        # Get API
        api = self.api_repo.get(str(policy.api_id))
        if not api:
            raise ValueError(f"API {policy.api_id} not found")

        # Get Gateway
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(api.gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {api.gateway_id} not found")

        # Create Gateway adapter
        try:
            adapter = create_gateway_adapter(gateway)
            await adapter.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Gateway {gateway.id}: {e}")
            raise RuntimeError(f"Failed to connect to Gateway: {e}")

        # Prepare policy configuration for Gateway
        policy_config = {
            "policy_id": str(policy.id),
            "policy_name": policy.policy_name,
            "policy_type": policy.policy_type.value,
            "limit_thresholds": {
                "requests_per_second": policy.limit_thresholds.requests_per_second,
                "requests_per_minute": policy.limit_thresholds.requests_per_minute,
                "requests_per_hour": policy.limit_thresholds.requests_per_hour,
                "concurrent_requests": policy.limit_thresholds.concurrent_requests,
            },
            "enforcement_action": policy.enforcement_action.value,
            "burst_allowance": policy.burst_allowance,
        }

        # Add priority rules if present
        if policy.priority_rules:
            policy_config["priority_rules"] = [
                {
                    "tier": rule.tier,
                    "multiplier": rule.multiplier,
                    "guaranteed_throughput": rule.guaranteed_throughput,
                    "burst_multiplier": rule.burst_multiplier,
                }
                for rule in policy.priority_rules
            ]

        # Add adaptation parameters if present
        if policy.adaptation_parameters:
            policy_config["adaptation_parameters"] = {
                "learning_rate": policy.adaptation_parameters.learning_rate,
                "adjustment_frequency": policy.adaptation_parameters.adjustment_frequency,
                "min_threshold": policy.adaptation_parameters.min_threshold,
                "max_threshold": policy.adaptation_parameters.max_threshold,
            }

        # Add consumer tiers if present
        if policy.consumer_tiers:
            policy_config["consumer_tiers"] = [
                {
                    "tier_name": tier.tier_name,
                    "tier_level": tier.tier_level,
                    "rate_multiplier": tier.rate_multiplier,
                    "priority_score": tier.priority_score,
                }
                for tier in policy.consumer_tiers
            ]

        # Apply policy to Gateway
        try:
            success = await adapter.apply_rate_limit_policy(
                api_id=str(api.id),
                policy=policy_config,
            )

            if not success:
                raise RuntimeError("Gateway adapter returned failure")

            # Update policy status
            policy.status = PolicyStatus.ACTIVE
            policy.applied_at = datetime.utcnow()
            self.rate_limit_repo.update_policy(policy)

            logger.info(
                f"Successfully applied rate limit policy {policy_id} to Gateway {gateway.id}"
            )

            return {
                "success": True,
                "policy_id": str(policy.id),
                "api_id": str(api.id),
                "gateway_id": str(gateway.id),
                "message": f"Rate limit policy '{policy.policy_name}' applied successfully to API '{api.name}' on Gateway '{gateway.name}'",
                "applied_at": policy.applied_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to apply rate limit policy to Gateway: {e}")
            raise RuntimeError(f"Failed to apply policy to Gateway: {e}")

        finally:
            # Disconnect from Gateway
            try:
                await adapter.disconnect()
            except Exception as e:
                logger.warning(f"Failed to disconnect from Gateway: {e}")

    def get_active_policy(self, api_id: UUID) -> Optional[RateLimitPolicy]:
        """
        Get the active rate limit policy for an API.

        Args:
            api_id: API UUID

        Returns:
            Active policy if found, None otherwise
        """
        return self.rate_limit_repo.get_active_policy(api_id)

    def list_policies(
        self,
        api_id: Optional[UUID] = None,
        status: Optional[PolicyStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[RateLimitPolicy], int]:
        """
        List rate limit policies with optional filters.

        Args:
            api_id: Optional API filter
            status: Optional status filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (policies list, total count)
        """
        return self.rate_limit_repo.list_policies(
            api_id=api_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    def suggest_policy_for_api(self, api_id: UUID) -> Dict[str, Any]:
        """
        Analyze API traffic and suggest appropriate rate limit policy.

        Args:
            api_id: API UUID

        Returns:
            Dictionary with suggested policy parameters
        """
        logger.info(f"Analyzing API {api_id} for rate limit suggestions")

        # Get API details
        api = self.api_repo.get(str(api_id))
        if not api:
            raise ValueError(f"API {api_id} not found")

        # Get historical metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.ANALYSIS_WINDOW_HOURS)

        metrics, _ = self.metrics_repo.find_by_api(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )

        if not metrics:
            # No metrics available, use defaults
            return self._default_policy_suggestion(api_id)

        # Analyze traffic patterns
        throughputs = [m.throughput for m in metrics if m.throughput]
        request_counts = [m.request_count for m in metrics if m.request_count]

        if not throughputs:
            return self._default_policy_suggestion(api_id)

        # Calculate statistics
        avg_throughput = statistics.mean(throughputs)
        max_throughput = max(throughputs)
        p95_throughput = statistics.quantiles(throughputs, n=20)[18]  # 95th percentile

        # Calculate total requests
        total_requests = sum(request_counts) if request_counts else 0
        hours_analyzed = len(metrics) / 60  # Assuming 1-minute intervals

        # Suggest thresholds based on traffic patterns
        # Use P95 + 20% buffer for normal traffic
        suggested_rps = int(p95_throughput * 1.2)
        suggested_rpm = suggested_rps * 60
        suggested_rph = suggested_rpm * 60
        suggested_concurrent = int(suggested_rps * 0.5)  # 50% of RPS

        # Determine policy type based on traffic variability
        throughput_std = statistics.stdev(throughputs) if len(throughputs) > 1 else 0
        coefficient_of_variation = throughput_std / avg_throughput if avg_throughput > 0 else 0

        if coefficient_of_variation > 0.5:
            # High variability - suggest adaptive policy
            policy_type = PolicyType.ADAPTIVE
            adaptation_params = AdaptationParameters(
                learning_rate=self.DEFAULT_LEARNING_RATE,
                adjustment_frequency=self.DEFAULT_ADJUSTMENT_FREQUENCY,
                min_threshold=int(suggested_rps * self.MIN_THRESHOLD_MULTIPLIER),
                max_threshold=int(suggested_rps * self.MAX_THRESHOLD_MULTIPLIER),
            )
        else:
            # Low variability - suggest fixed policy
            policy_type = PolicyType.FIXED
            adaptation_params = None

        return {
            "api_id": str(api_id),
            "api_name": api.name,
            "suggested_policy_type": policy_type.value,
            "suggested_thresholds": {
                "requests_per_second": suggested_rps,
                "requests_per_minute": suggested_rpm,
                "requests_per_hour": suggested_rph,
                "concurrent_requests": suggested_concurrent,
            },
            "adaptation_parameters": adaptation_params.model_dump() if adaptation_params else None,
            "burst_allowance": int(suggested_rps * 5),  # 5x RPS for bursts
            "enforcement_action": EnforcementAction.THROTTLE.value,
            "analysis_summary": {
                "avg_throughput": round(avg_throughput, 2),
                "max_throughput": round(max_throughput, 2),
                "p95_throughput": round(p95_throughput, 2),
                "total_requests_analyzed": total_requests,
                "hours_analyzed": round(hours_analyzed, 2),
                "traffic_variability": round(coefficient_of_variation, 2),
            },
        }

    def _default_policy_suggestion(self, api_id: UUID) -> Dict[str, Any]:
        """
        Provide default policy suggestion when no metrics are available.

        Args:
            api_id: API UUID

        Returns:
            Dictionary with default policy parameters
        """
        api = self.api_repo.get(str(api_id))

        return {
            "api_id": str(api_id),
            "api_name": api.name if api else "Unknown",
            "suggested_policy_type": PolicyType.FIXED.value,
            "suggested_thresholds": {
                "requests_per_second": self.DEFAULT_REQUESTS_PER_SECOND,
                "requests_per_minute": self.DEFAULT_REQUESTS_PER_MINUTE,
                "requests_per_hour": self.DEFAULT_REQUESTS_PER_HOUR,
                "concurrent_requests": self.DEFAULT_CONCURRENT_REQUESTS,
            },
            "adaptation_parameters": None,
            "burst_allowance": self.DEFAULT_REQUESTS_PER_SECOND * 5,
            "enforcement_action": EnforcementAction.THROTTLE.value,
            "analysis_summary": {
                "note": "No historical metrics available. Using default thresholds.",
            },
        }

    def adjust_adaptive_policy(self, policy_id: UUID) -> Optional[RateLimitPolicy]:
        """
        Adjust thresholds for an adaptive rate limit policy based on recent traffic.

        Args:
            policy_id: Policy UUID

        Returns:
            Updated policy if found and adjusted, None otherwise
        """
        logger.info(f"Adjusting adaptive policy {policy_id}")

        policy = self.rate_limit_repo.get_by_id(policy_id)
        if not policy:
            logger.warning(f"Policy {policy_id} not found")
            return None

        if policy.policy_type != PolicyType.ADAPTIVE:
            logger.warning(f"Policy {policy_id} is not adaptive")
            return None

        if not policy.adaptation_parameters:
            logger.warning(f"Policy {policy_id} has no adaptation parameters")
            return None

        # Get recent metrics
        lookback_seconds = policy.adaptation_parameters.adjustment_frequency * 2
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=lookback_seconds)

        metrics, _ = self.metrics_repo.find_by_api(
            api_id=policy.api_id,
            start_time=start_time,
            end_time=end_time,
        )

        if not metrics:
            logger.info(f"No recent metrics for policy {policy_id}, skipping adjustment")
            return policy

        # Calculate current traffic levels
        throughputs = [m.throughput for m in metrics if m.throughput]
        if not throughputs:
            return policy

        current_avg_throughput = statistics.mean(throughputs)
        current_max_throughput = max(throughputs)

        # Get current threshold
        current_rps = policy.limit_thresholds.requests_per_second or self.DEFAULT_REQUESTS_PER_SECOND

        # Calculate adjustment
        learning_rate = policy.adaptation_parameters.learning_rate
        target_utilization = 0.8  # Target 80% utilization

        # If current traffic is consistently high, increase threshold
        # If current traffic is consistently low, decrease threshold
        utilization = current_avg_throughput / current_rps if current_rps > 0 else 0

        if utilization > target_utilization:
            # Increase threshold
            adjustment_factor = 1 + (learning_rate * (utilization - target_utilization))
        else:
            # Decrease threshold
            adjustment_factor = 1 - (learning_rate * (target_utilization - utilization))

        new_rps = int(current_rps * adjustment_factor)

        # Apply min/max constraints
        if policy.adaptation_parameters.min_threshold:
            new_rps = max(new_rps, policy.adaptation_parameters.min_threshold)
        if policy.adaptation_parameters.max_threshold:
            new_rps = min(new_rps, policy.adaptation_parameters.max_threshold)

        # Only adjust if change is significant (>5%)
        if abs(new_rps - current_rps) / current_rps < 0.05:
            logger.info(f"Policy {policy_id} adjustment too small, skipping")
            return policy

        # Update thresholds
        new_thresholds = {
            "requests_per_second": new_rps,
            "requests_per_minute": new_rps * 60,
            "requests_per_hour": new_rps * 3600,
        }

        logger.info(
            f"Adjusting policy {policy_id} RPS from {current_rps} to {new_rps} "
            f"(utilization: {utilization:.2%})"
        )

        return self.rate_limit_repo.adjust_thresholds(policy_id, new_thresholds)

    def analyze_policy_effectiveness(
        self,
        policy_id: UUID,
        analysis_period_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Analyze the effectiveness of a rate limit policy.

        Args:
            policy_id: Policy UUID
            analysis_period_hours: Hours to analyze

        Returns:
            Dictionary with effectiveness analysis
        """
        logger.info(f"Analyzing effectiveness of policy {policy_id}")

        policy = self.rate_limit_repo.get_by_id(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")

        # Get metrics since policy was applied
        if policy.applied_at:
            start_time = policy.applied_at
        else:
            start_time = datetime.utcnow() - timedelta(hours=analysis_period_hours)

        end_time = datetime.utcnow()

        metrics, _ = self.metrics_repo.find_by_api(
            api_id=policy.api_id,
            start_time=start_time,
            end_time=end_time,
        )

        if not metrics:
            return {
                "policy_id": str(policy_id),
                "effectiveness_score": 0.0,
                "status": "insufficient_data",
                "message": "Not enough metrics data to analyze effectiveness",
            }

        # Calculate effectiveness metrics
        total_requests = sum(m.request_count for m in metrics if m.request_count)
        total_errors = sum(m.error_count for m in metrics if m.error_count)
        avg_error_rate = statistics.mean([m.error_rate for m in metrics if m.error_rate is not None])
        avg_response_time = statistics.mean([m.response_time_p95 for m in metrics if m.response_time_p95])

        # Estimate throttled/rejected requests (simplified)
        # In a real implementation, this would come from gateway logs
        threshold_rps = policy.limit_thresholds.requests_per_second or self.DEFAULT_REQUESTS_PER_SECOND
        peak_throughput = max(m.throughput for m in metrics if m.throughput)

        estimated_throttled = 0
        estimated_rejected = 0
        if peak_throughput > threshold_rps:
            # Estimate based on how much traffic exceeded threshold
            excess_ratio = (peak_throughput - threshold_rps) / peak_throughput
            if policy.enforcement_action == EnforcementAction.THROTTLE:
                estimated_throttled = int(total_requests * excess_ratio * 0.5)
            elif policy.enforcement_action == EnforcementAction.REJECT:
                estimated_rejected = int(total_requests * excess_ratio)

        # Calculate effectiveness score (0-1)
        # Based on: error rate reduction, response time stability, appropriate throttling
        error_rate_score = max(0, 1 - (avg_error_rate / 0.1))  # Lower error rate is better
        response_time_score = max(0, 1 - (avg_response_time / 1000))  # Lower response time is better
        throttling_score = 0.8 if estimated_throttled < total_requests * 0.1 else 0.5  # <10% throttled is good

        effectiveness_score = (error_rate_score * 0.4 + response_time_score * 0.3 + throttling_score * 0.3)

        # Update policy effectiveness score
        self.rate_limit_repo.update_effectiveness_score(policy_id, effectiveness_score)

        # Generate recommendations
        recommendations = []
        if effectiveness_score < self.LOW_EFFECTIVENESS_SCORE:
            recommendations.append("Consider adjusting rate limit thresholds")
            if estimated_throttled > total_requests * 0.2:
                recommendations.append("Too many requests being throttled - increase limits")
            if avg_error_rate > 0.05:
                recommendations.append("High error rate detected - may need stricter limits")

        if policy.policy_type == PolicyType.FIXED and effectiveness_score < 0.7:
            recommendations.append("Consider switching to adaptive policy for better performance")

        return {
            "policy_id": str(policy_id),
            "policy_name": policy.policy_name,
            "effectiveness_score": round(effectiveness_score, 3),
            "status": "effective" if effectiveness_score >= self.HIGH_EFFECTIVENESS_SCORE else "needs_improvement",
            "metrics": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "avg_error_rate": round(avg_error_rate, 4),
                "avg_response_time_p95": round(avg_response_time, 2),
                "estimated_throttled": estimated_throttled,
                "estimated_rejected": estimated_rejected,
                "peak_throughput": round(peak_throughput, 2),
            },
            "component_scores": {
                "error_rate_score": round(error_rate_score, 3),
                "response_time_score": round(response_time_score, 3),
                "throttling_score": round(throttling_score, 3),
            },
            "recommendations": recommendations,
            "analysis_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": round((end_time - start_time).total_seconds() / 3600, 2),
            },
        }


# Made with Bob