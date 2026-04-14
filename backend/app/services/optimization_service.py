"""
Optimization Service

Handles generation and management of performance optimization recommendations,
including analysis of metrics patterns, impact estimation, and validation tracking.
"""

import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import statistics

from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
    ImplementationEffort,
    EstimatedImpact,
    ActualImpact,
    ValidationResults,
)
from app.models.base.metric import Metric, TimeBucket

if TYPE_CHECKING:
    from app.agents.optimization_agent import OptimizationAgent
    from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class OptimizationService:
    """Service for generating and managing optimization recommendations."""

    # Thresholds for optimization triggers
    HIGH_RESPONSE_TIME_P95 = 500  # 500ms
    HIGH_RESPONSE_TIME_P99 = 1000  # 1000ms
    HIGH_ERROR_RATE = 0.05  # 5% error rate
    LOW_THROUGHPUT = 10  # 10 requests/second

    # Analysis window
    ANALYSIS_WINDOW_HOURS = 24

    # Minimum improvement thresholds
    MIN_IMPROVEMENT_PERCENTAGE = 10.0  # 10% improvement

    # Cost estimation (USD per month)
    COST_PER_MS_IMPROVEMENT = 0.50  # $0.50 per ms improvement per month
    COST_PER_PERCENT_ERROR_REDUCTION = 100.0  # $100 per 1% error reduction

    def __init__(
        self,
        recommendation_repository: RecommendationRepository,
        metrics_repository: MetricsRepository,
        api_repository: APIRepository,
        llm_service: "LLMService",
        rate_limit_service: Any | None = None,
    ):
        """
        Initialize the Optimization Service.

        Args:
            recommendation_repository: Repository for recommendation operations
            metrics_repository: Repository for metrics operations
            api_repository: Repository for API operations
            llm_service: LLM service for AI-driven recommendations
            rate_limit_service: Optional rate limiting service for integrated analysis
        """
        self.recommendation_repo = recommendation_repository
        self.metrics_repo = metrics_repository
        self.api_repo = api_repository
        self.llm_service = llm_service
        self.rate_limit_service = rate_limit_service

        from app.agents.optimization_agent import OptimizationAgent

        self._optimization_agent: OptimizationAgent = OptimizationAgent(
            llm_service=self.llm_service,
            optimization_service=self,
        )

    def _generate_rule_based_recommendations(
        self,
        gateway_id: UUID,
        api_id: UUID,
        metrics: List[Metric],
        focus_areas: Optional[List[RecommendationType]] = None,
        min_impact: float = 10.0,
    ) -> List[OptimizationRecommendation]:
        """
        Generate rule-based optimization recommendations for a specific API.

        Args:
            gateway_id: Gateway UUID
            api_id: API UUID
            metrics: Historical metrics already fetched for analysis
            focus_areas: Specific optimization types to focus on
            min_impact: Minimum expected improvement percentage

        Returns:
            List of generated recommendations
        """
        recommendations = []

        if not focus_areas or RecommendationType.CACHING in focus_areas:
            caching_rec = self._analyze_caching_opportunity(gateway_id, api_id, metrics)
            if caching_rec and caching_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(caching_rec)

        if not focus_areas or RecommendationType.COMPRESSION in focus_areas:
            compression_rec = self._analyze_compression_opportunity(gateway_id, api_id, metrics)
            if (
                compression_rec
                and compression_rec.estimated_impact.improvement_percentage >= min_impact
            ):
                recommendations.append(compression_rec)

        if not focus_areas or RecommendationType.RATE_LIMITING in focus_areas:
            rate_limit_rec = self._analyze_rate_limiting_opportunity(gateway_id, api_id, metrics)
            if (
                rate_limit_rec
                and rate_limit_rec.estimated_impact.improvement_percentage >= min_impact
            ):
                recommendations.append(rate_limit_rec)

        for recommendation in recommendations:
            try:
                self.recommendation_repo.create_recommendation(recommendation)
                logger.info(
                    f"Created {recommendation.recommendation_type.value} recommendation "
                    f"for API {api_id} with {recommendation.estimated_impact.improvement_percentage:.1f}% "
                    f"expected improvement"
                )
            except Exception as e:
                logger.error(f"Failed to store recommendation: {e}")

        return recommendations

    async def generate_recommendations_for_api(
        self,
        gateway_id: UUID,
        api_id: UUID,
        focus_areas: Optional[List[RecommendationType]] = None,
        min_impact: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Generate hybrid optimization recommendations for a specific API within a gateway context.

        Args:
            gateway_id: Gateway UUID (primary scope dimension)
            api_id: API UUID (secondary scope dimension)
            focus_areas: Specific optimization types to focus on
            min_impact: Minimum expected improvement percentage

        Returns:
            Dict with tightly integrated AI-driven recommendations
        """
        logger.info(f"Generating hybrid optimization recommendations for API {api_id} in gateway {gateway_id}")

        api = self.api_repo.get(str(api_id))
        if not api:
            logger.warning(f"API {api_id} not found")
            return {
                "error": "API not found",
                "recommendations": [],
            }
        
        # Verify API belongs to gateway
        if api.gateway_id != gateway_id:
            logger.warning(f"API {api_id} does not belong to gateway {gateway_id}")
            return {
                "error": "API does not belong to specified gateway",
                "recommendations": [],
            }

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.ANALYSIS_WINDOW_HOURS)

        metrics, _ = self.metrics_repo.find_by_api_with_bucket(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            time_bucket=TimeBucket.ONE_HOUR,
        )

        if len(metrics) < 10:
            logger.info(f"Insufficient metrics data for API {api_id} (only {len(metrics)} points)")
            return {
                "error": "Insufficient metrics data",
                "recommendations": [],
            }

        return await self._optimization_agent.generate_hybrid_recommendations(
            gateway_id=gateway_id,
            api_id=api_id,
            api_name=api.name,
            metrics=metrics,
            focus_areas=focus_areas,
            min_impact=min_impact,
        )

    async def generate_recommendations_for_gateway(
        self, gateway_id: UUID, min_impact: float = 10.0
    ) -> Dict[str, Any]:
        """
        Generate recommendations for all APIs within a specific gateway.

        Args:
            gateway_id: Gateway UUID (primary scope dimension)
            min_impact: Minimum expected improvement percentage

        Returns:
            Dict with generation results
        """
        logger.info(f"Generating optimization recommendations for all APIs in gateway {gateway_id}")

        # Get all APIs for this gateway
        apis, total = self.api_repo.find_by_gateway(gateway_id, size=1000)

        results = {
            "gateway_id": str(gateway_id),
            "total_apis": len(apis),
            "apis_analyzed": 0,
            "recommendations_generated": 0,
            "errors": [],
        }

        for api in apis:
            try:
                recommendations = await self.generate_recommendations_for_api(
                    gateway_id=gateway_id,
                    api_id=api.id,
                    min_impact=min_impact,
                )
                results["apis_analyzed"] += 1
                results["recommendations_generated"] += len(
                    recommendations.get("recommendations", [])
                )
            except Exception as e:
                logger.error(f"Failed to generate recommendations for API {api.id}: {e}")
                results["errors"].append(
                    {
                        "api_id": str(api.id),
                        "api_name": api.name,
                        "error": str(e),
                    }
                )

        logger.info(
            f"Generated {results['recommendations_generated']} recommendations "
            f"for {results['apis_analyzed']}/{results['total_apis']} APIs"
        )

        return results

    def validate_recommendation(
        self,
        recommendation_id: UUID,
        actual_metrics: Dict[str, float],
    ) -> Optional[OptimizationRecommendation]:
        """
        Validate a recommendation after implementation.

        Args:
            recommendation_id: Recommendation UUID
            actual_metrics: Actual measured metrics after implementation

        Returns:
            Updated recommendation with validation results
        """
        recommendation = self.recommendation_repo.get_recommendation(str(recommendation_id))
        if not recommendation:
            logger.warning(f"Recommendation {recommendation_id} not found")
            return None

        # Calculate actual impact
        estimated = recommendation.estimated_impact
        metric_name = estimated.metric

        before_value = estimated.current_value
        after_value = actual_metrics.get(metric_name, before_value)

        # Calculate actual improvement
        if before_value > 0:
            actual_improvement = ((before_value - after_value) / before_value) * 100
        else:
            actual_improvement = 0.0

        # Create validation results
        actual_impact = ActualImpact(
            metric=metric_name,
            before_value=before_value,
            after_value=after_value,
            actual_improvement=actual_improvement,
        )

        # Determine success (actual improvement >= 80% of expected)
        success = actual_improvement >= (estimated.improvement_percentage * 0.8)

        validation_results = ValidationResults(
            actual_impact=actual_impact,
            success=success,
            measured_at=datetime.utcnow(),
        )

        # Update recommendation
        updated = self.recommendation_repo.add_validation_results(
            recommendation_id=str(recommendation_id),
            validation_results=validation_results.model_dump(),
        )

        logger.info(
            f"Validated recommendation {recommendation_id}: "
            f"{'SUCCESS' if success else 'FAILED'} - "
            f"Expected {estimated.improvement_percentage:.1f}%, "
            f"Actual {actual_improvement:.1f}%"
        )

        return updated

    def _analyze_caching_opportunity(
        self, gateway_id: UUID, api_id: UUID, metrics: List[Metric]
    ) -> Optional[OptimizationRecommendation]:
        """Analyze if caching would benefit this API."""
        if not metrics:
            return None

        # Calculate average response times
        avg_p95 = statistics.mean([m.response_time_p95 for m in metrics])
        avg_p99 = statistics.mean([m.response_time_p99 for m in metrics])

        # Check if response times are high enough to benefit from caching
        if avg_p95 < self.HIGH_RESPONSE_TIME_P95:
            return None

        # Estimate improvement (caching typically reduces response time by 40-60%)
        improvement_percentage = 50.0
        expected_p95 = avg_p95 * (1 - improvement_percentage / 100)

        return OptimizationRecommendation(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api_id,
            recommendation_type=RecommendationType.CACHING,
            title="Enable Response Caching Policy",
            description=(
                f"Current P95 response time is {avg_p95:.0f}ms. Enabling a gateway-level "
                f"caching policy can reduce response times by approximately "
                f"{improvement_percentage:.0f}%, bringing P95 down to {expected_p95:.0f}ms."
            ),
            priority=RecommendationPriority.HIGH
            if avg_p95 > 1000
            else RecommendationPriority.MEDIUM,
            estimated_impact=EstimatedImpact(
                metric="response_time_p95",
                current_value=avg_p95,
                expected_value=expected_p95,
                improvement_percentage=improvement_percentage,
                confidence=0.85,
            ),
            implementation_effort=ImplementationEffort.LOW,
            implementation_steps=[
                "Configure gateway caching policy for this API",
                "Set cache TTL based on data freshness requirements (e.g., 5-60 minutes)",
                "Define cache key strategy (URL, headers, query parameters)",
                "Configure cache invalidation rules",
                "Monitor cache hit rates and adjust policy as needed",
            ],
            implemented_at=None,
            validation_results=None,
            cost_savings=None,
            metadata=None,
            vendor_metadata=None,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    # Removed: _analyze_query_optimization, _analyze_resource_allocation, _analyze_connection_pooling
    # These methods generated recommendations that cannot be validated with gateway-observable metrics

    def _analyze_compression_opportunity(
        self, gateway_id: UUID, api_id: UUID, metrics: List[Metric]
    ) -> Optional[OptimizationRecommendation]:
        """Analyze if response compression would benefit this API."""
        if not metrics:
            return None

        # Calculate average response times
        avg_p50 = statistics.mean([m.response_time_p50 for m in metrics])

        # Compression helps most with moderate response times (100-500ms)
        if avg_p50 < 100 or avg_p50 > 500:
            return None

        # Estimate improvement (compression typically reduces response time by 20-30%)
        improvement_percentage = 25.0
        expected_p50 = avg_p50 * (1 - improvement_percentage / 100)

        return OptimizationRecommendation(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api_id,
            recommendation_type=RecommendationType.COMPRESSION,
            title="Enable Response Compression",
            description=(
                f"Current P50 response time is {avg_p50:.0f}ms. Enabling gzip/brotli compression "
                f"can reduce response times by approximately {improvement_percentage:.0f}% and "
                f"decrease bandwidth costs."
            ),
            priority=RecommendationPriority.MEDIUM,
            estimated_impact=EstimatedImpact(
                metric="response_time_p50",
                current_value=avg_p50,
                expected_value=expected_p50,
                improvement_percentage=improvement_percentage,
                confidence=0.90,
            ),
            implementation_effort=ImplementationEffort.LOW,
            implementation_steps=[
                "Enable gzip/brotli compression in web server",
                "Configure compression level (6-9 recommended)",
                "Set minimum response size threshold (1KB)",
                "Add compression headers to responses",
                "Monitor compression ratios and performance",
            ],
            implemented_at=None,
            validation_results=None,
            cost_savings=None,
            metadata=None,
            vendor_metadata=None,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    def _analyze_rate_limiting_opportunity(
        self, gateway_id: UUID, api_id: UUID, metrics: List[Metric]
    ) -> Optional[OptimizationRecommendation]:
        """
        AI-Enhanced rate limiting analysis with intelligent pattern recognition.

        Analyzes traffic patterns, error correlations, and business context to recommend
        optimal rate limiting strategies. Uses statistical analysis combined with
        pattern recognition for intelligent threshold determination.
        """
        if not metrics:
            return None

        # Calculate comprehensive traffic statistics
        throughputs = [m.throughput for m in metrics if m.throughput]
        error_rates = [m.error_rate for m in metrics if m.error_rate is not None]
        response_times = [m.response_time_p95 for m in metrics if m.response_time_p95]

        if not throughputs or len(throughputs) < 10:
            return None

        # Advanced statistical analysis
        avg_throughput = statistics.mean(throughputs)
        max_throughput = max(throughputs)
        min_throughput = min(throughputs)
        median_throughput = statistics.median(throughputs)

        # Calculate percentiles for better threshold determination
        sorted_throughputs = sorted(throughputs)
        p50 = sorted_throughputs[len(sorted_throughputs) // 2]
        p75 = sorted_throughputs[int(len(sorted_throughputs) * 0.75)]
        p90 = sorted_throughputs[int(len(sorted_throughputs) * 0.90)]
        p95 = sorted_throughputs[int(len(sorted_throughputs) * 0.95)]
        p99 = (
            sorted_throughputs[int(len(sorted_throughputs) * 0.99)]
            if len(sorted_throughputs) > 100
            else max_throughput
        )

        # Traffic pattern analysis
        throughput_std = statistics.stdev(throughputs) if len(throughputs) > 1 else 0
        coefficient_of_variation = throughput_std / avg_throughput if avg_throughput > 0 else 0

        # Analyze error rate patterns
        avg_error_rate = statistics.mean(error_rates) if error_rates else 0.0
        max_error_rate = max(error_rates) if error_rates else 0.0

        # Correlate errors with traffic spikes
        error_spike_correlation = self._calculate_error_traffic_correlation(
            throughputs, error_rates
        )

        # Analyze response time degradation
        avg_response_time = statistics.mean(response_times) if response_times else 0
        response_time_degradation = self._analyze_response_time_degradation(
            throughputs, response_times
        )

        # AI-Enhanced Decision Logic
        # Score different factors to determine if rate limiting is needed
        variability_score = min(coefficient_of_variation / 0.5, 1.0)  # 0-1 scale
        error_score = min(avg_error_rate / 0.05, 1.0)  # 0-1 scale (5% = 1.0)
        spike_score = (
            min((max_throughput - avg_throughput) / avg_throughput / 2.0, 1.0)
            if avg_throughput > 0
            else 0
        )
        correlation_score = error_spike_correlation
        degradation_score = response_time_degradation

        # Weighted composite score
        composite_score = (
            variability_score * 0.25
            + error_score * 0.30
            + spike_score * 0.20
            + correlation_score * 0.15
            + degradation_score * 0.10
        )

        # Only recommend if composite score indicates benefit
        if composite_score < 0.35:
            return None

        # Intelligent threshold calculation based on traffic patterns
        # Use different strategies based on traffic characteristics
        if coefficient_of_variation > 0.8:
            # High variability: Use P75 with larger buffer
            suggested_rps = int(p75 * 1.5)
            burst_multiplier = 3.0
            strategy = "adaptive"
        elif coefficient_of_variation > 0.5:
            # Moderate variability: Use P90 with moderate buffer
            suggested_rps = int(p90 * 1.3)
            burst_multiplier = 2.5
            strategy = "balanced"
        else:
            # Low variability: Use P95 with small buffer
            suggested_rps = int(p95 * 1.2)
            burst_multiplier = 2.0
            strategy = "conservative"

        # Ensure minimum threshold
        suggested_rps = max(suggested_rps, int(avg_throughput * 1.1))

        # Calculate expected improvement based on pattern analysis
        if error_spike_correlation > 0.7:
            # Strong correlation: High confidence in improvement
            improvement_percentage = 50.0
            confidence = 0.90
        elif error_spike_correlation > 0.4:
            # Moderate correlation: Good confidence
            improvement_percentage = 40.0
            confidence = 0.80
        else:
            # Weak correlation: Conservative estimate
            improvement_percentage = 30.0
            confidence = 0.70

        expected_error_rate = avg_error_rate * (1 - improvement_percentage / 100)

        # Determine priority based on severity
        if avg_error_rate > 0.10 or max_error_rate > 0.20:
            priority = RecommendationPriority.CRITICAL
        elif avg_error_rate > 0.05 or composite_score > 0.7:
            priority = RecommendationPriority.HIGH
        elif composite_score > 0.5:
            priority = RecommendationPriority.MEDIUM
        else:
            priority = RecommendationPriority.LOW

        # Generate intelligent description with pattern insights
        description = self._generate_rate_limit_description(
            coefficient_of_variation=coefficient_of_variation,
            avg_error_rate=avg_error_rate,
            max_error_rate=max_error_rate,
            error_spike_correlation=error_spike_correlation,
            suggested_rps=suggested_rps,
            improvement_percentage=improvement_percentage,
            strategy=strategy,
            p50=p50,
            p95=p95,
            p99=p99,
        )

        # Generate context-aware implementation steps
        implementation_steps = self._generate_rate_limit_steps(
            suggested_rps=suggested_rps,
            burst_multiplier=burst_multiplier,
            strategy=strategy,
            has_high_errors=avg_error_rate > 0.05,
            has_spikes=coefficient_of_variation > 0.5,
        )

        # Store analysis metadata for future reference
        metadata = {
            "analysis_version": "2.0_ai_enhanced",
            "traffic_pattern": {
                "avg_rps": round(avg_throughput, 2),
                "p50_rps": p50,
                "p95_rps": p95,
                "p99_rps": p99,
                "max_rps": max_throughput,
                "coefficient_of_variation": round(coefficient_of_variation, 3),
            },
            "error_analysis": {
                "avg_error_rate": round(avg_error_rate, 4),
                "max_error_rate": round(max_error_rate, 4),
                "error_spike_correlation": round(error_spike_correlation, 3),
            },
            "recommendation_factors": {
                "variability_score": round(variability_score, 3),
                "error_score": round(error_score, 3),
                "spike_score": round(spike_score, 3),
                "correlation_score": round(correlation_score, 3),
                "degradation_score": round(degradation_score, 3),
                "composite_score": round(composite_score, 3),
            },
            "strategy": strategy,
            "burst_multiplier": burst_multiplier,
        }

        return OptimizationRecommendation(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api_id,
            recommendation_type=RecommendationType.RATE_LIMITING,
            title=f"Implement {strategy.capitalize()} Rate Limiting Strategy",
            description=description,
            priority=priority,
            estimated_impact=EstimatedImpact(
                metric="error_rate",
                current_value=avg_error_rate,
                expected_value=expected_error_rate,
                improvement_percentage=improvement_percentage,
                confidence=confidence,
            ),
            implementation_effort=ImplementationEffort.MEDIUM,
            implementation_steps=implementation_steps,
            implemented_at=None,
            validation_results=None,
            cost_savings=None,
            metadata=metadata,
            vendor_metadata=None,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    def _calculate_error_traffic_correlation(
        self, throughputs: List[float], error_rates: List[float]
    ) -> float:
        """
        Calculate correlation between traffic spikes and error rates.

        Returns:
            Correlation coefficient (0-1), where 1 indicates strong positive correlation
        """
        if not throughputs or not error_rates or len(throughputs) != len(error_rates):
            return 0.0

        try:
            # Calculate Pearson correlation coefficient
            n = len(throughputs)
            if n < 2:
                return 0.0

            mean_throughput = statistics.mean(throughputs)
            mean_error = statistics.mean(error_rates)

            numerator = sum(
                (t - mean_throughput) * (e - mean_error) for t, e in zip(throughputs, error_rates)
            )

            denominator_t = sum((t - mean_throughput) ** 2 for t in throughputs)
            denominator_e = sum((e - mean_error) ** 2 for e in error_rates)

            if denominator_t == 0 or denominator_e == 0:
                return 0.0

            correlation = numerator / (denominator_t * denominator_e) ** 0.5

            # Return absolute value normalized to 0-1
            return abs(correlation)

        except Exception as e:
            logger.warning(f"Failed to calculate correlation: {e}")
            return 0.0

    def _analyze_response_time_degradation(
        self, throughputs: List[float], response_times: List[float]
    ) -> float:
        """
        Analyze if response times degrade with increased traffic.

        Returns:
            Degradation score (0-1), where 1 indicates severe degradation
        """
        if not throughputs or not response_times or len(throughputs) != len(response_times):
            return 0.0

        try:
            # Sort by throughput and analyze response time trend
            paired = sorted(zip(throughputs, response_times))

            # Compare bottom 25% vs top 25% throughput periods
            n = len(paired)
            bottom_quarter = paired[: n // 4]
            top_quarter = paired[-n // 4 :]

            if not bottom_quarter or not top_quarter:
                return 0.0

            avg_rt_low_traffic = statistics.mean([rt for _, rt in bottom_quarter])
            avg_rt_high_traffic = statistics.mean([rt for _, rt in top_quarter])

            if avg_rt_low_traffic == 0:
                return 0.0

            # Calculate degradation percentage
            degradation_pct = (avg_rt_high_traffic - avg_rt_low_traffic) / avg_rt_low_traffic

            # Normalize to 0-1 scale (50% degradation = 1.0)
            return min(degradation_pct / 0.5, 1.0)

        except Exception as e:
            logger.warning(f"Failed to analyze response time degradation: {e}")
            return 0.0

    def _generate_rate_limit_description(
        self,
        coefficient_of_variation: float,
        avg_error_rate: float,
        max_error_rate: float,
        error_spike_correlation: float,
        suggested_rps: int,
        improvement_percentage: float,
        strategy: str,
        p50: float,
        p95: float,
        p99: float,
    ) -> str:
        """Generate intelligent, context-aware description for rate limiting recommendation."""

        # Traffic pattern description
        if coefficient_of_variation > 0.8:
            traffic_desc = f"highly variable traffic (CV: {coefficient_of_variation:.2f}) with significant spikes"
        elif coefficient_of_variation > 0.5:
            traffic_desc = f"moderate traffic variability (CV: {coefficient_of_variation:.2f})"
        else:
            traffic_desc = f"relatively stable traffic (CV: {coefficient_of_variation:.2f})"

        # Error pattern description
        if error_spike_correlation > 0.7:
            error_desc = f"strong correlation ({error_spike_correlation:.2f}) between traffic spikes and errors"
        elif error_spike_correlation > 0.4:
            error_desc = (
                f"moderate correlation ({error_spike_correlation:.2f}) between traffic and errors"
            )
        else:
            error_desc = "errors occurring independently of traffic patterns"

        # Build comprehensive description
        description = (
            f"Analysis reveals {traffic_desc} with average error rate of {avg_error_rate:.2%} "
            f"(peak: {max_error_rate:.2%}). Pattern analysis shows {error_desc}. "
            f"\n\nTraffic Distribution:\n"
            f"• Median (P50): {p50} req/s\n"
            f"• P95: {p95} req/s\n"
            f"• P99: {p99} req/s\n"
            f"\nRecommended {strategy} rate limiting strategy at {suggested_rps} requests/second "
            f"is expected to reduce errors by approximately {improvement_percentage:.0f}%, "
            f"improving system stability and user experience."
        )

        return description

    def _generate_rate_limit_steps(
        self,
        suggested_rps: int,
        burst_multiplier: float,
        strategy: str,
        has_high_errors: bool,
        has_spikes: bool,
    ) -> List[str]:
        """Generate context-aware implementation steps."""

        burst_allowance = int(suggested_rps * burst_multiplier)

        steps = [
            f"Configure base rate limit at {suggested_rps} requests/second",
            f"Set burst allowance to {burst_allowance} req/s ({burst_multiplier}x base rate)",
        ]

        if strategy == "adaptive":
            steps.append("Implement adaptive rate limiting with dynamic threshold adjustment")
            steps.append("Configure sliding window algorithm for spike detection")
        elif strategy == "balanced":
            steps.append("Use token bucket algorithm for balanced traffic shaping")
            steps.append("Configure gradual throttling (429 responses with Retry-After headers)")
        else:
            steps.append("Implement fixed window rate limiting for predictable behavior")
            steps.append("Configure immediate rejection for excess requests")

        if has_high_errors:
            steps.append("Enable circuit breaker pattern for cascading failure prevention")
            steps.append("Implement health check-based rate limit adjustment")

        if has_spikes:
            steps.append("Configure consumer-based rate limiting for fair resource allocation")
            steps.append("Implement queue-based request buffering for spike absorption")

        steps.extend(
            [
                "Set up monitoring for rate limit hits and effectiveness metrics",
                "Configure alerts for rate limit threshold breaches",
                "Plan gradual rollout with A/B testing (50% traffic initially)",
                "Schedule review after 7 days to optimize thresholds based on actual data",
            ]
        )

        return steps

    def list_recommendations(
        self,
        api_id: Optional[str] = None,
        priority: Optional[RecommendationPriority] = None,
        status: Optional[RecommendationStatus] = None,
        recommendation_type: Optional[RecommendationType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List optimization recommendations with optional filters and API name enrichment.

        Args:
            api_id: Filter by API ID
            priority: Filter by priority level
            status: Filter by recommendation status
            recommendation_type: Filter by recommendation type
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with recommendations list, total count, and pagination info
        """
        # Get recommendations with filters
        result = self.recommendation_repo.list_recommendations(
            api_id=api_id,
            priority=priority,
            status=status,
            recommendation_type=recommendation_type,
            page=page,
            page_size=page_size,
        )

        # Enrich with API names
        recommendations_with_names = []
        for rec in result["recommendations"]:
            api_name = None
            try:
                api = self.api_repo.get(str(rec.api_id))
                api_name = api.name if api else None
            except Exception:
                pass

            recommendations_with_names.append(
                {
                    "recommendation": rec,
                    "api_name": api_name,
                }
            )

        return {
            "recommendations": recommendations_with_names,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        }

    def get_recommendation_stats(
        self,
        api_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get statistics about optimization recommendations.

        Args:
            api_id: Optional API ID filter
            days: Number of days to look back

        Returns:
            Recommendation statistics
        """
        return self.recommendation_repo.get_implementation_stats(
            api_id=api_id,
            days=days,
        )

    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get optimization summary metrics for dashboard.

        Returns:
            Dictionary with recommendation counts by priority
        """
        # Get all recommendations
        result = self.recommendation_repo.list_recommendations(
            page=1,
            page_size=10000,
        )

        recommendations = result["recommendations"]

        # Count by priority
        high = sum(1 for r in recommendations if r.priority == RecommendationPriority.HIGH)
        medium = sum(1 for r in recommendations if r.priority == RecommendationPriority.MEDIUM)
        low = sum(1 for r in recommendations if r.priority == RecommendationPriority.LOW)

        return {
            "total_recommendations": len(recommendations),
            "high_priority_recommendations": high,
            "medium_priority_recommendations": medium,
            "low_priority_recommendations": low,
        }

    def get_recommendation_details(
        self, recommendation_id: str
    ) -> Optional[OptimizationRecommendation]:
        """
        Get detailed information about a specific recommendation.

        Args:
            recommendation_id: Recommendation UUID

        Returns:
            Recommendation details or None if not found
        """
        return self.recommendation_repo.get_recommendation(recommendation_id)

    async def get_recommendation_insights(
        self,
        recommendation_id: str,
    ) -> Dict[str, Any]:
        """
        Get AI-generated insights for a specific recommendation.

        Args:
            recommendation_id: Recommendation UUID

        Returns:
            AI-generated insights or fallback data
        """
        # Get recommendation
        recommendation = self.recommendation_repo.get_recommendation(recommendation_id)

        if not recommendation:
            return {
                "status": "error",
                "message": "Recommendation not found",
            }

        # Try to generate AI insights
        try:
            insights = await self.llm_service.generate_optimization_recommendation(
                {
                    "response_time_p95": recommendation.estimated_impact.current_value,
                    "response_time_p99": recommendation.estimated_impact.current_value * 1.5,
                    "error_rate": 0.01,
                    "throughput": 100,
                    "availability": 99.5,
                }
            )

            return {
                "status": "success",
                "recommendation_id": recommendation_id,
                "insights": insights,
            }

        except Exception as e:
            logger.warning(f"LLM insights unavailable: {e}")
            return {
                "status": "fallback",
                "recommendation_id": recommendation_id,
                "insights": {
                    "title": recommendation.title,
                    "description": recommendation.description,
                    "priority": recommendation.priority.value,
                    "estimated_impact": f"{recommendation.estimated_impact.improvement_percentage:.1f}%",
                },
            }

    async def apply_recommendation_to_gateway(
        self,
        recommendation_id: str,
    ) -> Dict[str, Any]:
        """
        Apply a recommendation's policy to the actual Gateway.

        Args:
            recommendation_id: Recommendation UUID to apply

        Returns:
            Dictionary with application result

        Raises:
            ValueError: If recommendation not found or not applicable
            RuntimeError: If gateway connection or policy application fails
        """
        # Get recommendation
        recommendation = self.recommendation_repo.get_recommendation(recommendation_id)

        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        # Get API
        api = self.api_repo.get(str(recommendation.api_id))
        if not api:
            raise ValueError(f"API {recommendation.api_id} not found")

        # Get Gateway
        from app.db.repositories.gateway_repository import GatewayRepository

        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(api.gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {api.gateway_id} not found")

        # Create Gateway adapter
        from app.adapters.factory import create_gateway_adapter
        from app.models.base.api import PolicyAction, PolicyActionType
        from app.models.base.policy_configs import (
            CachingConfig,
            CompressionConfig,
            RateLimitConfig,
        )
        from datetime import datetime

        adapter = create_gateway_adapter(gateway)

        try:
            await adapter.connect()

            policy_type = recommendation.recommendation_type.value
            success = False
            vendor_policy_id = None

            # Apply policy based on recommendation type
            if policy_type == "caching":
                policy = PolicyAction(
                    action_type=PolicyActionType.CACHING,
                    enabled=True,
                    stage="response",
                    config=CachingConfig(
                        ttl_seconds=300,
                        max_ttl_seconds=None,
                        cache_key_strategy="url_headers",
                        vary_headers=["Accept", "Accept-Encoding"],
                        vary_query_params=None,
                        respect_cache_control_headers=True,
                        cache_methods=["GET", "HEAD"],
                        cache_status_codes=[200, 203, 204, 206, 300, 301],
                        max_payload_size_bytes=None,
                        invalidate_on_methods=["POST", "PUT", "PATCH", "DELETE"],
                    ),
                    vendor_config={},
                    name=f"Cache Policy for {api.name}",
                    description=f"Caching policy applied from recommendation {recommendation.id}",
                )
                result = await adapter.apply_caching_policy(str(api.id), policy)
                success = result if isinstance(result, bool) else result.get("success", False)
                vendor_policy_id = result.get("policy_id") if isinstance(result, dict) else None

            elif policy_type == "compression":
                policy = PolicyAction(
                    action_type=PolicyActionType.COMPRESSION,
                    enabled=True,
                    stage="response",
                    config=CompressionConfig(
                        enabled=True,
                        algorithms=["gzip"],
                        compression_level=6,
                        min_size_bytes=1024,
                        content_types=["application/json", "text/html", "text/plain"],
                    ),
                    vendor_config={},
                    name=f"Compression Policy for {api.name}",
                    description=f"Compression policy applied from recommendation {recommendation.id}",
                )
                result = await adapter.apply_compression_policy(str(api.id), policy)
                success = result if isinstance(result, bool) else result.get("success", False)
                vendor_policy_id = result.get("policy_id") if isinstance(result, dict) else None

            elif policy_type == "rate_limiting":
                policy = PolicyAction(
                    action_type=PolicyActionType.RATE_LIMITING,
                    enabled=True,
                    stage="request",
                    config=RateLimitConfig(
                        requests_per_second=100,
                        requests_per_minute=5000,
                        requests_per_hour=250000,
                        requests_per_day=None,
                        concurrent_requests=50,
                        burst_allowance=None,
                        rate_limit_key="ip",
                        custom_key_header=None,
                        enforcement_action="throttle",
                        include_rate_limit_headers=True,
                        consumer_tiers=None,
                    ),
                    vendor_config={},
                    name=f"Rate Limit Policy for {api.name}",
                    description=f"Rate limiting policy applied from recommendation {recommendation.id}",
                )
                result = await adapter.apply_rate_limit_policy(str(api.id), policy)
                success = result if isinstance(result, bool) else result.get("success", False)
                vendor_policy_id = result.get("policy_id") if isinstance(result, dict) else None

            else:
                raise ValueError(f"Unsupported recommendation type: {policy_type}")

            if not success:
                raise RuntimeError("Gateway adapter returned failure")

            # Update recommendation status
            implemented_at = datetime.utcnow()

            vendor_metadata = {
                "gateway_id": str(gateway.id),
                "gateway_vendor": gateway.vendor,
                "policy_type": policy_type,
                "applied_at": implemented_at.isoformat(),
            }
            if vendor_policy_id:
                vendor_metadata["policy_id"] = vendor_policy_id

            self.recommendation_repo.update(
                recommendation_id,
                {
                    "status": RecommendationStatus.IMPLEMENTED.value,
                    "implemented_at": implemented_at.isoformat(),
                    "vendor_metadata": vendor_metadata,
                },
            )

            logger.info(
                f"Successfully applied {policy_type} policy for recommendation {recommendation_id} "
                f"to Gateway {gateway.id}"
            )

            return {
                "success": True,
                "recommendation_id": str(recommendation.id),
                "api_id": str(api.id),
                "gateway_id": str(gateway.id),
                "policy_type": policy_type,
                "message": f"{policy_type.capitalize()} policy applied successfully to API '{api.name}' on Gateway '{gateway.name}'",
                "applied_at": implemented_at.isoformat(),
            }

        finally:
            try:
                await adapter.disconnect()
            except Exception as e:
                logger.warning(f"Failed to disconnect from Gateway: {e}")

    async def remove_recommendation_policy(
        self,
        recommendation_id: str,
    ) -> Dict[str, Any]:
        """
        Remove a previously applied optimization policy from the Gateway.

        Args:
            recommendation_id: Recommendation UUID to remove policy for

        Returns:
            Dictionary with removal result

        Raises:
            ValueError: If recommendation not found or not implemented
            RuntimeError: If gateway connection or policy removal fails
        """
        # Get recommendation
        recommendation = self.recommendation_repo.get_recommendation(recommendation_id)

        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        if recommendation.status != RecommendationStatus.IMPLEMENTED:
            raise ValueError(
                f"Recommendation {recommendation_id} is not implemented (status: {recommendation.status.value})"
            )

        # Get API
        api = self.api_repo.get(str(recommendation.api_id))
        if not api:
            raise ValueError(f"API {recommendation.api_id} not found")

        # Get Gateway
        from app.db.repositories.gateway_repository import GatewayRepository

        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(api.gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {api.gateway_id} not found")

        # Create Gateway adapter
        from app.adapters.factory import create_gateway_adapter
        from datetime import datetime

        adapter = create_gateway_adapter(gateway)

        try:
            await adapter.connect()

            policy_type = recommendation.recommendation_type.value
            success = False

            # Remove policy based on recommendation type
            if policy_type == "caching":
                success = await adapter.remove_caching_policy(str(api.id))
            elif policy_type == "compression":
                success = await adapter.remove_compression_policy(str(api.id))
            elif policy_type == "rate_limiting":
                success = await adapter.remove_rate_limit_policy(str(api.id))
            else:
                raise ValueError(f"Unsupported recommendation type: {policy_type}")

            if not success:
                raise RuntimeError("Gateway adapter returned failure")

            # Update recommendation status
            removed_at = datetime.utcnow()

            self.recommendation_repo.update(
                recommendation_id,
                {
                    "status": RecommendationStatus.PENDING.value,
                    "implemented_at": None,
                    "vendor_metadata": {
                        "removed_at": removed_at.isoformat(),
                        "previous_application": recommendation.vendor_metadata,
                    }
                    if recommendation.vendor_metadata
                    else None,
                },
            )

            logger.info(
                f"Successfully removed {policy_type} policy for recommendation {recommendation_id} "
                f"from Gateway {gateway.id}"
            )

            return {
                "success": True,
                "recommendation_id": str(recommendation.id),
                "api_id": str(api.id),
                "gateway_id": str(gateway.id),
                "policy_type": policy_type,
                "message": f"{policy_type.capitalize()} policy removed successfully from API '{api.name}' on Gateway '{gateway.name}'",
                "removed_at": removed_at.isoformat(),
            }

        finally:
            try:
                await adapter.disconnect()
            except Exception as e:
                logger.warning(f"Failed to disconnect from Gateway: {e}")


# Made with Bob
