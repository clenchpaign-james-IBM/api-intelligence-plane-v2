"""Test fixtures for optimization recommendations.

Provides reusable test data for optimization integration tests.
"""

from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
    EstimatedImpact,
    ImplementationEffort,
)


def create_sample_recommendation(
    api_id: str | None = None,
    recommendation_type: RecommendationType = RecommendationType.CACHING,
    priority: RecommendationPriority = RecommendationPriority.HIGH,
    status: RecommendationStatus = RecommendationStatus.PENDING,
    **kwargs
) -> OptimizationRecommendation:
    """Create a sample optimization recommendation.
    
    Args:
        api_id: Target API ID (generates random if None)
        recommendation_type: Type of optimization
        priority: Priority level
        status: Implementation status
        **kwargs: Additional fields to override
        
    Returns:
        Sample OptimizationRecommendation instance
    """
    defaults = {
        "id": str(uuid4()),
        "api_id": api_id or str(uuid4()),
        "recommendation_type": recommendation_type,
        "priority": priority,
        "title": f"Optimize {recommendation_type.value} for improved performance",
        "description": f"Implement {recommendation_type.value} to reduce latency and improve throughput",
        "current_metrics": {
            "avg_response_time_ms": 450.0,
            "p95_response_time_ms": 850.0,
            "requests_per_minute": 120.0,
            "error_rate": 0.02,
        },
        "estimated_impact": EstimatedImpact(
            metric="response_time_p95",
            current_value=850.0,
            expected_value=510.0,
            improvement_percentage=40.0,
            confidence=0.85,
        ),
        "implementation_steps": [
            "Analyze current caching strategy",
            "Identify cacheable endpoints",
            "Implement Redis caching layer",
            "Configure cache TTL policies",
            "Monitor cache hit rates",
        ],
        "implementation_effort": ImplementationEffort.MEDIUM,
        "status": status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    defaults.update(kwargs)
    return OptimizationRecommendation(**defaults)


def create_caching_recommendation(api_id: str) -> OptimizationRecommendation:
    """Create a caching optimization recommendation."""
    return create_sample_recommendation(
        api_id=api_id,
        recommendation_type=RecommendationType.CACHING,
        priority=RecommendationPriority.HIGH,
        title="Implement Redis caching for frequently accessed data",
        description="Add caching layer to reduce database load and improve response times for read-heavy endpoints",
        current_metrics={
            "avg_response_time_ms": 520.0,
            "p95_response_time_ms": 980.0,
            "requests_per_minute": 200.0,
            "cache_hit_rate": 0.0,
        },
        estimated_impact=EstimatedImpact(
            metric="response_time_p95",
            current_value=980.0,
            expected_value=392.0,
            improvement_percentage=60.0,
            confidence=0.92,
        ),
        implementation_steps=[
            "Set up Redis cluster",
            "Identify cacheable GET endpoints",
            "Implement cache-aside pattern",
            "Configure TTL based on data volatility",
            "Add cache invalidation logic",
            "Monitor cache hit rates and memory usage",
        ],
        implementation_effort=ImplementationEffort.HIGH,
    )


def create_query_optimization_recommendation(api_id: str) -> OptimizationRecommendation:
    """Create a query optimization recommendation."""
    return create_sample_recommendation(
        api_id=api_id,
        recommendation_type=RecommendationType.QUERY_OPTIMIZATION,
        priority=RecommendationPriority.CRITICAL,
        title="Optimize database queries with missing indexes",
        description="Add database indexes and optimize N+1 query patterns causing performance bottlenecks",
        current_metrics={
            "avg_response_time_ms": 1200.0,
            "p95_response_time_ms": 2500.0,
            "requests_per_minute": 80.0,
            "slow_query_count": 45,
        },
        estimated_impact=EstimatedImpact(
            metric="response_time_p95",
            current_value=2500.0,
            expected_value=750.0,
            improvement_percentage=70.0,
            confidence=0.95,
        ),
        implementation_steps=[
            "Analyze slow query logs",
            "Identify missing indexes",
            "Create composite indexes for common queries",
            "Refactor N+1 queries to use joins",
            "Add query result pagination",
            "Monitor query execution times",
        ],
        implementation_effort=ImplementationEffort.HIGH,
    )


def create_resource_allocation_recommendation(api_id: str) -> OptimizationRecommendation:
    """Create a resource allocation recommendation."""
    return create_sample_recommendation(
        api_id=api_id,
        recommendation_type=RecommendationType.RESOURCE_ALLOCATION,
        priority=RecommendationPriority.MEDIUM,
        title="Adjust resource allocation based on usage patterns",
        description="Right-size container resources and implement auto-scaling for cost optimization",
        current_metrics={
            "avg_cpu_usage": 25.0,
            "avg_memory_usage": 40.0,
            "peak_cpu_usage": 65.0,
            "peak_memory_usage": 75.0,
        },
        estimated_impact=EstimatedImpact(
            metric="cost_per_request",
            current_value=0.05,
            expected_value=0.0325,
            improvement_percentage=35.0,
            confidence=0.88,
        ),
        implementation_steps=[
            "Analyze resource utilization patterns",
            "Right-size container CPU and memory",
            "Configure horizontal pod autoscaling",
            "Set up resource requests and limits",
            "Implement cost monitoring",
        ],
        implementation_effort=ImplementationEffort.MEDIUM,
    )


def create_compression_recommendation(api_id: str) -> OptimizationRecommendation:
    """Create a compression optimization recommendation."""
    return create_sample_recommendation(
        api_id=api_id,
        recommendation_type=RecommendationType.COMPRESSION,
        priority=RecommendationPriority.LOW,
        title="Enable response compression for large payloads",
        description="Implement gzip/brotli compression to reduce bandwidth and improve transfer speeds",
        current_metrics={
            "avg_response_size_kb": 450.0,
            "bandwidth_usage_gb": 125.0,
            "compression_enabled": False,
        },
        estimated_impact=EstimatedImpact(
            metric="bandwidth_usage",
            current_value=125.0,
            expected_value=75.0,
            improvement_percentage=40.0,
            confidence=0.90,
        ),
        implementation_steps=[
            "Enable gzip compression middleware",
            "Configure compression thresholds",
            "Test with various content types",
            "Monitor compression ratios",
            "Measure bandwidth savings",
        ],
        implementation_effort=ImplementationEffort.LOW,
    )


def create_connection_pooling_recommendation(api_id: str) -> OptimizationRecommendation:
    """Create a connection pooling recommendation."""
    return create_sample_recommendation(
        api_id=api_id,
        recommendation_type=RecommendationType.CONNECTION_POOLING,
        priority=RecommendationPriority.HIGH,
        title="Optimize database connection pooling",
        description="Configure connection pool settings to reduce connection overhead and improve concurrency",
        current_metrics={
            "avg_connection_time_ms": 85.0,
            "active_connections": 15,
            "max_connections": 20,
            "connection_errors": 12,
        },
        estimated_impact=EstimatedImpact(
            metric="connection_time_ms",
            current_value=85.0,
            expected_value=59.5,
            improvement_percentage=30.0,
            confidence=0.87,
        ),
        implementation_steps=[
            "Analyze connection pool metrics",
            "Increase pool size based on load",
            "Configure connection timeout settings",
            "Implement connection retry logic",
            "Monitor pool utilization",
        ],
        implementation_effort=ImplementationEffort.MEDIUM,
    )


def create_diverse_recommendations(api_id: str, count: int = 5) -> List[OptimizationRecommendation]:
    """Create a diverse set of optimization recommendations.
    
    Args:
        api_id: Target API ID
        count: Number of recommendations (max 5)
        
    Returns:
        List of diverse OptimizationRecommendation instances
    """
    generators = [
        create_caching_recommendation,
        create_query_optimization_recommendation,
        create_resource_allocation_recommendation,
        create_compression_recommendation,
        create_connection_pooling_recommendation,
    ]
    
    return [gen(api_id) for gen in generators[:count]]


def create_recommendations_with_statuses(api_id: str) -> List[OptimizationRecommendation]:
    """Create recommendations with various implementation statuses.
    
    Args:
        api_id: Target API ID
        
    Returns:
        List of recommendations in different states
    """
    return [
        create_sample_recommendation(
            api_id=api_id,
            recommendation_type=RecommendationType.CACHING,
            priority=RecommendationPriority.HIGH,
            status=RecommendationStatus.PENDING,
        ),
        create_sample_recommendation(
            api_id=api_id,
            recommendation_type=RecommendationType.QUERY_OPTIMIZATION,
            priority=RecommendationPriority.CRITICAL,
            status=RecommendationStatus.IN_PROGRESS,
            implemented_at=datetime.utcnow() - timedelta(days=2),
        ),
        create_sample_recommendation(
            api_id=api_id,
            recommendation_type=RecommendationType.COMPRESSION,
            priority=RecommendationPriority.LOW,
            status=RecommendationStatus.IMPLEMENTED,
            implemented_at=datetime.utcnow() - timedelta(days=3),
        ),
        create_sample_recommendation(
            api_id=api_id,
            recommendation_type=RecommendationType.RESOURCE_ALLOCATION,
            priority=RecommendationPriority.MEDIUM,
            status=RecommendationStatus.IMPLEMENTED,
            implemented_at=datetime.utcnow() - timedelta(days=7),
        ),
    ]


def create_high_impact_recommendations(api_id: str) -> List[OptimizationRecommendation]:
    """Create high-impact optimization recommendations.
    
    Args:
        api_id: Target API ID
        
    Returns:
        List of high-impact recommendations
    """
    return [
        create_sample_recommendation(
            api_id=api_id,
            recommendation_type=RecommendationType.QUERY_OPTIMIZATION,
            priority=RecommendationPriority.CRITICAL,
            estimated_impact=EstimatedImpact(
                metric="response_time_p95",
                current_value=3000.0,
                expected_value=750.0,
                improvement_percentage=75.0,
                confidence=0.95,
            ),
        ),
        create_sample_recommendation(
            api_id=api_id,
            recommendation_type=RecommendationType.CACHING,
            priority=RecommendationPriority.HIGH,
            estimated_impact=EstimatedImpact(
                metric="response_time_p95",
                current_value=1000.0,
                expected_value=350.0,
                improvement_percentage=65.0,
                confidence=0.92,
            ),
        ),
    ]

# Made with Bob
