"""
Optimization Service

Handles generation and management of performance optimization recommendations,
including analysis of metrics patterns, impact estimation, and validation tracking.
"""

import logging
from typing import List, Optional, Dict, Any
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
from app.models.metric import Metric

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
        llm_service: Optional[Any] = None,
        rate_limit_service: Optional[Any] = None,
    ):
        """
        Initialize the Optimization Service.

        Args:
            recommendation_repository: Repository for recommendation operations
            metrics_repository: Repository for metrics operations
            api_repository: Repository for API operations
            llm_service: Optional LLM service for AI-enhanced recommendations
            rate_limit_service: Optional rate limiting service for integrated analysis
        """
        self.recommendation_repo = recommendation_repository
        self.metrics_repo = metrics_repository
        self.api_repo = api_repository
        self.llm_service = llm_service
        self.rate_limit_service = rate_limit_service
        self._optimization_agent = None

    def _should_use_ai_enhancement(self, confidence: float = 0.0) -> bool:
        """
        Determine if AI enhancement should be used based on configuration and confidence.
        
        Args:
            confidence: Confidence score of rule-based analysis (0.0-1.0)
            
        Returns:
            True if AI enhancement should be used, False otherwise
        """
        from app.config import settings
        
        # Check if AI enhancement is enabled
        if not settings.OPTIMIZATION_AI_ENABLED:
            return False
        
        # Check if LLM service is available
        if not self.llm_service:
            return False
        
        # Use AI if confidence is below threshold
        return confidence < settings.OPTIMIZATION_AI_THRESHOLD

    def generate_recommendations_for_api(
        self,
        api_id: UUID,
        focus_areas: Optional[List[RecommendationType]] = None,
        min_impact: float = 10.0,
        use_ai_enhancement: bool = False,
    ) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations for a specific API.

        Args:
            api_id: API UUID
            focus_areas: Specific optimization types to focus on
            min_impact: Minimum expected improvement percentage
            use_ai_enhancement: Force AI enhancement regardless of confidence

        Returns:
            List of generated recommendations
        """
        logger.info(f"Generating optimization recommendations for API {api_id}")

        # Get API details
        api = self.api_repo.get(str(api_id))
        if not api:
            logger.warning(f"API {api_id} not found")
            return []

        # Get historical metrics for analysis
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.ANALYSIS_WINDOW_HOURS)
        
        metrics, _ = self.metrics_repo.find_by_api(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )

        if len(metrics) < 10:  # Need sufficient data points
            logger.info(
                f"Insufficient metrics data for API {api_id} (only {len(metrics)} points)"
            )
            return []

        # Analyze metrics and generate recommendations
        # Only generate recommendations that can be validated with gateway-observable metrics
        recommendations = []

        # Check for caching opportunities
        if not focus_areas or RecommendationType.CACHING in focus_areas:
            caching_rec = self._analyze_caching_opportunity(api_id, metrics)
            if caching_rec and caching_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(caching_rec)

        # Check for compression opportunities
        if not focus_areas or RecommendationType.COMPRESSION in focus_areas:
            compression_rec = self._analyze_compression_opportunity(api_id, metrics)
            if compression_rec and compression_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(compression_rec)

        # Check for rate limiting opportunities (integrated from rate_limit_service)
        if not focus_areas or RecommendationType.RATE_LIMITING in focus_areas:
            rate_limit_rec = self._analyze_rate_limiting_opportunity(api_id, metrics)
            if rate_limit_rec and rate_limit_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(rate_limit_rec)

        # Store recommendations
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
    
    async def generate_ai_enhanced_recommendations(
        self,
        api_id: UUID,
        focus_areas: Optional[List[RecommendationType]] = None,
        min_impact: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Generate AI-enhanced optimization recommendations with LLM analysis.
        
        Args:
            api_id: API UUID
            focus_areas: Specific optimization types to focus on
            min_impact: Minimum expected improvement percentage
            
        Returns:
            Dict with recommendations and AI analysis
        """
        logger.info(f"Generating AI-enhanced recommendations for API {api_id}")
        
        # Get API details
        api = self.api_repo.get(str(api_id))
        if not api:
            logger.warning(f"API {api_id} not found")
            return {
                "error": "API not found",
                "recommendations": [],
            }
        
        # Get historical metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.ANALYSIS_WINDOW_HOURS)
        
        metrics, _ = self.metrics_repo.find_by_api(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )
        
        if len(metrics) < 10:
            logger.info(f"Insufficient metrics data for API {api_id}")
            return {
                "error": "Insufficient metrics data",
                "recommendations": [],
            }
        
        # Try AI-enhanced generation if available
        if self.llm_service:
            try:
                # Lazy load optimization agent
                if self._optimization_agent is None:
                    from app.agents.optimization_agent import OptimizationAgent
                    self._optimization_agent = OptimizationAgent(
                        llm_service=self.llm_service,
                        optimization_service=self,
                    )
                
                # Generate AI-enhanced recommendations
                result = await self._optimization_agent.generate_enhanced_recommendations(
                    api_id=api_id,
                    api_name=api.name,
                    metrics=metrics,
                    focus_areas=focus_areas,
                )
                
                logger.info(f"Generated AI-enhanced recommendations for API {api_id}")
                return result
                
            except Exception as e:
                logger.error(f"AI-enhanced recommendation failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based recommendations
        recommendations = self.generate_recommendations_for_api(api_id, focus_areas, min_impact)
        
        return {
            "api_id": str(api_id),
            "api_name": api.name,
            "recommendations": [
                {
                    "id": str(r.id),
                    "type": r.recommendation_type.value,
                    "title": r.title,
                    "priority": r.priority.value,
                    "estimated_impact": r.estimated_impact.improvement_percentage,
                }
                for r in recommendations
            ],
            "fallback_mode": True,
        }

    def generate_recommendations_for_all_apis(
        self, min_impact: float = 10.0
    ) -> Dict[str, Any]:
        """
        Generate recommendations for all active APIs.

        Args:
            min_impact: Minimum expected improvement percentage

        Returns:
            Dict with generation results
        """
        logger.info("Generating optimization recommendations for all APIs")

        # Get all active APIs
        apis, total = self.api_repo.list_all(size=1000)

        results = {
            "total_apis": len(apis),
            "apis_analyzed": 0,
            "recommendations_generated": 0,
            "errors": [],
        }

        for api in apis:
            try:
                recommendations = self.generate_recommendations_for_api(
                    api_id=api.id,
                    min_impact=min_impact,
                )
                results["apis_analyzed"] += 1
                results["recommendations_generated"] += len(recommendations)
            except Exception as e:
                logger.error(f"Failed to generate recommendations for API {api.id}: {e}")
                results["errors"].append({
                    "api_id": str(api.id),
                    "api_name": api.name,
                    "error": str(e),
                })

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
        self, api_id: UUID, metrics: List[Metric]
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
            api_id=api_id,
            recommendation_type=RecommendationType.CACHING,
            title="Enable Response Caching Policy",
            description=(
                f"Current P95 response time is {avg_p95:.0f}ms. Enabling a gateway-level "
                f"caching policy can reduce response times by approximately "
                f"{improvement_percentage:.0f}%, bringing P95 down to {expected_p95:.0f}ms."
            ),
            priority=RecommendationPriority.HIGH if avg_p95 > 1000 else RecommendationPriority.MEDIUM,
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
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    # Removed: _analyze_query_optimization, _analyze_resource_allocation, _analyze_connection_pooling
    # These methods generated recommendations that cannot be validated with gateway-observable metrics

    def _analyze_compression_opportunity(
        self, api_id: UUID, metrics: List[Metric]
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
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    def _analyze_rate_limiting_opportunity(
        self, api_id: UUID, metrics: List[Metric]
    ) -> Optional[OptimizationRecommendation]:
        """
        Analyze if rate limiting would benefit this API.
        Integrated from rate_limit_service for unified optimization recommendations.
        """
        if not metrics:
            return None

        # Calculate traffic statistics
        throughputs = [m.throughput for m in metrics if m.throughput]
        error_rates = [m.error_rate for m in metrics if m.error_rate is not None]
        
        if not throughputs:
            return None

        avg_throughput = statistics.mean(throughputs)
        max_throughput = max(throughputs)
        p95_throughput = statistics.quantiles(throughputs, n=20)[18] if len(throughputs) > 1 else max_throughput
        
        # Check if error rate is high (indicating potential overload)
        avg_error_rate = statistics.mean(error_rates) if error_rates else 0.0
        
        # Rate limiting is beneficial if:
        # 1. High traffic variability (spikes)
        # 2. High error rates during peak traffic
        # 3. Throughput exceeds reasonable thresholds
        
        throughput_std = statistics.stdev(throughputs) if len(throughputs) > 1 else 0
        coefficient_of_variation = throughput_std / avg_throughput if avg_throughput > 0 else 0
        
        # Only recommend if there's high variability or high error rates
        if coefficient_of_variation < 0.3 and avg_error_rate < 0.02:
            return None

        # Estimate improvement (rate limiting typically reduces error rate by 30-50%)
        improvement_percentage = 40.0
        expected_error_rate = avg_error_rate * (1 - improvement_percentage / 100)
        
        # Suggest rate limit threshold (P95 + 20% buffer)
        suggested_rps = int(p95_throughput * 1.2)

        return OptimizationRecommendation(
            id=uuid4(),
            api_id=api_id,
            recommendation_type=RecommendationType.RATE_LIMITING,
            title="Implement Intelligent Rate Limiting",
            description=(
                f"Current traffic shows high variability (CV: {coefficient_of_variation:.2f}) "
                f"with error rate of {avg_error_rate:.2%}. Implementing rate limiting at "
                f"{suggested_rps} requests/second can reduce errors by approximately "
                f"{improvement_percentage:.0f}% and improve system stability."
            ),
            priority=RecommendationPriority.HIGH if avg_error_rate > 0.05 else RecommendationPriority.MEDIUM,
            estimated_impact=EstimatedImpact(
                metric="error_rate",
                current_value=avg_error_rate,
                expected_value=expected_error_rate,
                improvement_percentage=improvement_percentage,
                confidence=0.80,
            ),
            implementation_effort=ImplementationEffort.MEDIUM,
            implementation_steps=[
                f"Configure rate limit policy at {suggested_rps} requests/second",
                "Set burst allowance for traffic spikes (5x base rate)",
                "Configure throttling action (delay vs reject)",
                "Implement consumer tier-based limits if needed",
                "Monitor effectiveness and adjust thresholds",
            ],
            expires_at=datetime.utcnow() + timedelta(days=30),
        )



# Made with Bob