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
    ):
        """
        Initialize the Optimization Service.

        Args:
            recommendation_repository: Repository for recommendation operations
            metrics_repository: Repository for metrics operations
            api_repository: Repository for API operations
        """
        self.recommendation_repo = recommendation_repository
        self.metrics_repo = metrics_repository
        self.api_repo = api_repository

    def generate_recommendations_for_api(
        self,
        api_id: UUID,
        focus_areas: Optional[List[RecommendationType]] = None,
        min_impact: float = 10.0,
    ) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations for a specific API.

        Args:
            api_id: API UUID
            focus_areas: Specific optimization types to focus on
            min_impact: Minimum expected improvement percentage

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
        recommendations = []

        # Check for caching opportunities
        if not focus_areas or RecommendationType.CACHING in focus_areas:
            caching_rec = self._analyze_caching_opportunity(api_id, metrics)
            if caching_rec and caching_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(caching_rec)

        # Check for query optimization opportunities
        if not focus_areas or RecommendationType.QUERY_OPTIMIZATION in focus_areas:
            query_rec = self._analyze_query_optimization(api_id, metrics)
            if query_rec and query_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(query_rec)

        # Check for resource allocation opportunities
        if not focus_areas or RecommendationType.RESOURCE_ALLOCATION in focus_areas:
            resource_rec = self._analyze_resource_allocation(api_id, metrics)
            if resource_rec and resource_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(resource_rec)

        # Check for compression opportunities
        if not focus_areas or RecommendationType.COMPRESSION in focus_areas:
            compression_rec = self._analyze_compression_opportunity(api_id, metrics)
            if compression_rec and compression_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(compression_rec)

        # Check for connection pooling opportunities
        if not focus_areas or RecommendationType.CONNECTION_POOLING in focus_areas:
            pooling_rec = self._analyze_connection_pooling(api_id, metrics)
            if pooling_rec and pooling_rec.estimated_impact.improvement_percentage >= min_impact:
                recommendations.append(pooling_rec)

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

        # Calculate cost savings
        cost_savings = (avg_p95 - expected_p95) * self.COST_PER_MS_IMPROVEMENT

        return OptimizationRecommendation(
            id=uuid4(),
            api_id=api_id,
            recommendation_type=RecommendationType.CACHING,
            title="Implement Response Caching",
            description=(
                f"Current P95 response time is {avg_p95:.0f}ms. Implementing a caching "
                f"layer (Redis/Memcached) can reduce response times by approximately "
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
            implementation_effort=ImplementationEffort.MEDIUM,
            implementation_steps=[
                "Set up Redis/Memcached cluster",
                "Implement caching middleware in API layer",
                "Define cache invalidation strategy",
                "Add cache key generation logic",
                "Monitor cache hit rates and adjust TTL",
            ],
            cost_savings=cost_savings,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    def _analyze_query_optimization(
        self, api_id: UUID, metrics: List[Metric]
    ) -> Optional[OptimizationRecommendation]:
        """Analyze if query optimization would benefit this API."""
        if not metrics:
            return None

        # Calculate average response times
        avg_p99 = statistics.mean([m.response_time_p99 for m in metrics])

        # Check if P99 is significantly higher than P95 (indicates slow queries)
        avg_p95 = statistics.mean([m.response_time_p95 for m in metrics])
        p99_p95_ratio = avg_p99 / avg_p95 if avg_p95 > 0 else 1.0

        if p99_p95_ratio < 2.0:  # P99 should be at least 2x P95 for query issues
            return None

        # Estimate improvement (query optimization typically reduces P99 by 30-50%)
        improvement_percentage = 40.0
        expected_p99 = avg_p99 * (1 - improvement_percentage / 100)

        return OptimizationRecommendation(
            id=uuid4(),
            api_id=api_id,
            recommendation_type=RecommendationType.QUERY_OPTIMIZATION,
            title="Optimize Database Queries",
            description=(
                f"P99 response time ({avg_p99:.0f}ms) is {p99_p95_ratio:.1f}x higher than "
                f"P95 ({avg_p95:.0f}ms), indicating slow database queries. Optimizing queries "
                f"and adding indexes can reduce P99 by approximately {improvement_percentage:.0f}%."
            ),
            priority=RecommendationPriority.HIGH,
            estimated_impact=EstimatedImpact(
                metric="response_time_p99",
                current_value=avg_p99,
                expected_value=expected_p99,
                improvement_percentage=improvement_percentage,
                confidence=0.80,
            ),
            implementation_effort=ImplementationEffort.MEDIUM,
            implementation_steps=[
                "Identify slow queries using query profiling",
                "Add database indexes for frequently queried fields",
                "Optimize N+1 query patterns",
                "Implement query result pagination",
                "Add query performance monitoring",
            ],
            cost_savings=(avg_p99 - expected_p99) * self.COST_PER_MS_IMPROVEMENT,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    def _analyze_resource_allocation(
        self, api_id: UUID, metrics: List[Metric]
    ) -> Optional[OptimizationRecommendation]:
        """Analyze if resource allocation changes would benefit this API."""
        if not metrics:
            return None

        # Calculate average throughput and error rate
        avg_throughput = statistics.mean([m.throughput for m in metrics])
        avg_error_rate = statistics.mean([m.error_rate for m in metrics])

        # Check if low throughput with high error rate (resource constraint)
        if avg_throughput > self.LOW_THROUGHPUT or avg_error_rate < self.HIGH_ERROR_RATE:
            return None

        # Estimate improvement
        improvement_percentage = 30.0
        expected_error_rate = avg_error_rate * (1 - improvement_percentage / 100)

        return OptimizationRecommendation(
            id=uuid4(),
            api_id=api_id,
            recommendation_type=RecommendationType.RESOURCE_ALLOCATION,
            title="Increase Resource Allocation",
            description=(
                f"Low throughput ({avg_throughput:.1f} req/s) combined with high error rate "
                f"({avg_error_rate*100:.1f}%) suggests resource constraints. Increasing CPU/memory "
                f"allocation can reduce errors by approximately {improvement_percentage:.0f}%."
            ),
            priority=RecommendationPriority.CRITICAL if avg_error_rate > 0.10 else RecommendationPriority.HIGH,
            estimated_impact=EstimatedImpact(
                metric="error_rate",
                current_value=avg_error_rate,
                expected_value=expected_error_rate,
                improvement_percentage=improvement_percentage,
                confidence=0.75,
            ),
            implementation_effort=ImplementationEffort.LOW,
            implementation_steps=[
                "Analyze current resource utilization metrics",
                "Increase CPU allocation by 50%",
                "Increase memory allocation by 50%",
                "Monitor performance improvements",
                "Adjust auto-scaling thresholds",
            ],
            cost_savings=(avg_error_rate - expected_error_rate) * 100 * self.COST_PER_PERCENT_ERROR_REDUCTION,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

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
            cost_savings=(avg_p50 - expected_p50) * self.COST_PER_MS_IMPROVEMENT * 0.5,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    def _analyze_connection_pooling(
        self, api_id: UUID, metrics: List[Metric]
    ) -> Optional[OptimizationRecommendation]:
        """Analyze if connection pooling would benefit this API."""
        if not metrics:
            return None

        # Calculate average response times and throughput
        avg_p95 = statistics.mean([m.response_time_p95 for m in metrics])
        avg_throughput = statistics.mean([m.throughput for m in metrics])

        # Connection pooling helps with high throughput and moderate response times
        if avg_throughput < 50 or avg_p95 < 200:
            return None

        # Estimate improvement (connection pooling typically reduces response time by 15-25%)
        improvement_percentage = 20.0
        expected_p95 = avg_p95 * (1 - improvement_percentage / 100)

        return OptimizationRecommendation(
            id=uuid4(),
            api_id=api_id,
            recommendation_type=RecommendationType.CONNECTION_POOLING,
            title="Implement Connection Pooling",
            description=(
                f"High throughput ({avg_throughput:.0f} req/s) with P95 of {avg_p95:.0f}ms "
                f"suggests connection overhead. Implementing connection pooling can reduce "
                f"response times by approximately {improvement_percentage:.0f}%."
            ),
            priority=RecommendationPriority.MEDIUM,
            estimated_impact=EstimatedImpact(
                metric="response_time_p95",
                current_value=avg_p95,
                expected_value=expected_p95,
                improvement_percentage=improvement_percentage,
                confidence=0.85,
            ),
            implementation_effort=ImplementationEffort.MEDIUM,
            implementation_steps=[
                "Configure database connection pool (size: 10-50)",
                "Set connection timeout and idle timeout",
                "Implement connection health checks",
                "Add connection pool monitoring",
                "Tune pool size based on load patterns",
            ],
            cost_savings=(avg_p95 - expected_p95) * self.COST_PER_MS_IMPROVEMENT,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )


# Made with Bob