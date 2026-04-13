"""Integration tests for optimization recommendations.

Tests the optimization service with real OpenSearch data to verify:
- Recommendation generation logic
- Impact estimation
- Priority determination
- Implementation tracking

Requires OpenSearch to be running and accessible.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.client import get_client
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.optimization_service import OptimizationService
from app.models.base.metric import Metric
from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)
from app.models.recommendation import (
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
    ImplementationEffort,
)


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def opensearch_client():
    """Get OpenSearch client."""
    return get_client()


@pytest.fixture
def recommendation_repository():
    """Create recommendation repository."""
    return RecommendationRepository()


@pytest.fixture
def metrics_repository():
    """Create metrics repository."""
    return MetricsRepository()


@pytest.fixture
def api_repository():
    """Create API repository."""
    return APIRepository()


@pytest.fixture
def optimization_service(recommendation_repository, metrics_repository, api_repository):
    """Create optimization service with real repositories."""
    return OptimizationService(
        recommendation_repository=recommendation_repository,
        metrics_repository=metrics_repository,
        api_repository=api_repository,
    )


@pytest.fixture
async def test_api(api_repository):
    """Create a test API in OpenSearch."""
    now = datetime.utcnow()
    api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="Test API for Optimization",
        version="1.0.0",
        base_path="/api/v1",
        endpoints=[
            Endpoint(
                path="/test",
                method="GET",
                description="Test endpoint",
                parameters=[],
                response_codes=[200, 500],
            )
        ],
        methods=["GET", "POST"],
        authentication_type=AuthenticationType.NONE,
        authentication_config=None,
        ownership=None,
        tags=["test"],
        is_shadow=False,
        discovery_method=DiscoveryMethod.REGISTERED,
        discovered_at=now,
        last_seen_at=now,
        status=APIStatus.ACTIVE,
        health_score=85.0,
        current_metrics=CurrentMetrics(
            response_time_p50=250.0,
            response_time_p95=500.0,
            response_time_p99=800.0,
            error_rate=0.02,
            throughput=10.0,
            availability=98.5,
            last_error=None,
            measured_at=now,
        ),
        metadata={},
    )
    
    # Store in OpenSearch
    await api_repository.create(api)
    
    yield api
    
    # Cleanup
    try:
        await api_repository.delete(api.id)
    except Exception:
        pass


@pytest.fixture
async def slow_api_metrics(test_api, metrics_repository):
    """Create metrics showing slow response times in OpenSearch."""
    now = datetime.utcnow()
    metrics = []
    
    # Generate 24 hours of metrics with slow response times
    for i in range(24):
        timestamp = now - timedelta(hours=23-i)
        
        # Consistently slow response times (300-500ms)
        response_time_p95 = 300 + (i * 8)
        
        metric = Metric(
            id=uuid4(),
            api_id=test_api.id,
            gateway_id=test_api.gateway_id,
            timestamp=timestamp,
            response_time_p50=response_time_p95 * 0.6,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p95 * 1.3,
            error_rate=0.01,
            error_count=10,
            request_count=1000,
            throughput=16.67,
            availability=99.5,
            status_codes={"200": 990, "500": 10},
            endpoint_metrics=None,
            metadata=None,
        )
        
        # Store in OpenSearch
        await metrics_repository.create(metric)
        metrics.append(metric)
    
    yield metrics
    
    # Cleanup
    for metric in metrics:
        try:
            await metrics_repository.delete(metric.id)
        except Exception:
            pass


@pytest.fixture
async def high_throughput_metrics(test_api, metrics_repository):
    """Create metrics showing high throughput in OpenSearch."""
    now = datetime.utcnow()
    metrics = []
    
    # Generate 24 hours of high throughput metrics
    for i in range(24):
        timestamp = now - timedelta(hours=23-i)
        
        metric = Metric(
            id=uuid4(),
            api_id=test_api.id,
            gateway_id=test_api.gateway_id,
            timestamp=timestamp,
            response_time_p50=150,
            response_time_p95=300,
            response_time_p99=450,
            error_rate=0.01,
            error_count=100,
            request_count=10000,  # High request count
            throughput=166.67,  # High throughput
            availability=99.5,
            status_codes={"200": 9900, "500": 100},
            endpoint_metrics=None,
            metadata=None,
        )
        
        # Store in OpenSearch
        await metrics_repository.create(metric)
        metrics.append(metric)
    
    yield metrics
    
    # Cleanup
    for metric in metrics:
        try:
            await metrics_repository.delete(metric.id)
        except Exception:
            pass


@pytest.mark.asyncio
class TestOptimizationRecommendations:
    """Test optimization recommendation generation."""
    
    async def test_generate_recommendations_for_slow_api(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test that slow response times generate optimization recommendations."""
        # Generate recommendations for the test API
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Should generate at least one recommendation
        assert len(recommendations) > 0
        
        # Should have caching or query optimization recommendations
        rec_types = [r.recommendation_type for r in recommendations]
        assert any(
            rt in [RecommendationType.CACHING, RecommendationType.QUERY_OPTIMIZATION]
            for rt in rec_types
        )
        
        # Verify recommendation properties
        for rec in recommendations:
            assert rec.api_id == test_api.id
            assert rec.estimated_impact.improvement_percentage >= 10.0
            assert rec.priority in [
                RecommendationPriority.HIGH,
                RecommendationPriority.MEDIUM,
                RecommendationPriority.LOW
            ]
            assert rec.status == RecommendationStatus.PENDING
            assert len(rec.implementation_steps) > 0
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_caching_recommendation_for_slow_api(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test caching recommendation generation for slow API."""
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Find caching recommendation
        caching_recs = [
            r for r in recommendations
            if r.recommendation_type == RecommendationType.CACHING
        ]
        
        if len(caching_recs) > 0:
            rec = caching_recs[0]
            
            # Verify impact estimation
            assert rec.estimated_impact.current_value > 0
            assert rec.estimated_impact.expected_value < rec.estimated_impact.current_value
            assert rec.estimated_impact.improvement_percentage >= 40.0  # Caching should offer 40-60%
            assert 0 < rec.estimated_impact.confidence <= 1.0
            
            # Verify implementation details
            assert rec.implementation_effort in [
                ImplementationEffort.LOW,
                ImplementationEffort.MEDIUM,
                ImplementationEffort.HIGH
            ]
            assert len(rec.implementation_steps) >= 3
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_connection_pooling_for_high_throughput(
        self, optimization_service, test_api, high_throughput_metrics
    ):
        """Test connection pooling recommendation for high throughput API."""
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Find connection pooling recommendation
        pooling_recs = [
            r for r in recommendations
            if r.recommendation_type == RecommendationType.CONNECTION_POOLING
        ]
        
        if len(pooling_recs) > 0:
            rec = pooling_recs[0]
            
            # Verify it's for high throughput scenario
            assert rec.estimated_impact.improvement_percentage >= 15.0
            assert "connection" in rec.title.lower() or "pool" in rec.title.lower()
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_recommendation_persistence(
        self, optimization_service, recommendation_repository, test_api, slow_api_metrics
    ):
        """Test that recommendations are stored in OpenSearch."""
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        assert len(recommendations) > 0
        recommendation_id = recommendations[0].id
        
        # Retrieve from repository
        stored_rec = await recommendation_repository.get_recommendation(str(recommendation_id))
        
        assert stored_rec is not None
        assert stored_rec.id == recommendation_id
        assert stored_rec.api_id == test_api.id
        
        # Cleanup
        for rec in recommendations:
            try:
                await recommendation_repository.delete(rec.id)
            except Exception:
                pass
    
    async def test_priority_determination(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test that priority is correctly determined from impact."""
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        assert len(recommendations) > 0
        
        for rec in recommendations:
            # Verify priority matches impact thresholds
            if rec.estimated_impact.improvement_percentage >= 50:
                assert rec.priority in [
                    RecommendationPriority.CRITICAL,
                    RecommendationPriority.HIGH
                ]
            elif rec.estimated_impact.improvement_percentage >= 30:
                assert rec.priority in [
                    RecommendationPriority.HIGH,
                    RecommendationPriority.MEDIUM
                ]
            else:
                assert rec.priority in [
                    RecommendationPriority.MEDIUM,
                    RecommendationPriority.LOW
                ]
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_min_impact_filter(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test that min_impact filter works correctly."""
        # Generate with high threshold
        high_threshold_recs = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=40.0
        )
        
        # Generate with low threshold
        low_threshold_recs = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Low threshold should return more or equal recommendations
        assert len(low_threshold_recs) >= len(high_threshold_recs)
        
        # All high threshold recs should have >= 40% impact
        for rec in high_threshold_recs:
            assert rec.estimated_impact.improvement_percentage >= 40.0
        
        # Cleanup
        all_recs = high_threshold_recs + low_threshold_recs
        for rec in all_recs:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass


@pytest.mark.asyncio
class TestRecommendationValidation:
    """Test recommendation validation and tracking."""
    
    async def test_validate_recommendation(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test recommendation validation after implementation."""
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Simulate implementation with 35% improvement
        actual_improvement = 35.0
        
        # Validate recommendation
        validated_rec = await optimization_service.validate_recommendation(
            recommendation_id=rec.id,
            actual_improvement=actual_improvement
        )
        
        assert validated_rec is not None
        assert validated_rec.status == RecommendationStatus.IMPLEMENTED
        assert validated_rec.implemented_at is not None
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_recommendation_statistics(
        self, optimization_service, recommendation_repository, test_api, slow_api_metrics
    ):
        """Test recommendation statistics calculation."""
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        assert len(recommendations) > 0
        
        # Get statistics
        stats = await recommendation_repository.get_implementation_stats(
            api_id=str(test_api.id),
            days=30
        )
        
        assert stats is not None
        assert stats["total_recommendations"] >= len(recommendations)
        assert "by_status" in stats
        assert "by_priority" in stats
        assert "by_type" in stats
        
        # Cleanup
        for rec in recommendations:
            try:
                await recommendation_repository.delete(rec.id)
            except Exception:
                pass


@pytest.mark.asyncio
class TestRateLimitingRecommendations:
    """Test rate limiting recommendation generation."""
    
    async def test_generate_rate_limiting_recommendation(
        self, optimization_service, test_api, high_throughput_metrics
    ):
        """Test that high throughput generates rate limiting recommendations."""
        # Generate recommendations for the test API
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Should generate at least one recommendation
        assert len(recommendations) > 0
        
        # Find rate limiting recommendation
        rate_limit_recs = [
            r for r in recommendations
            if r.recommendation_type == RecommendationType.RATE_LIMITING
        ]
        
        # Should have at least one rate limiting recommendation for high throughput
        assert len(rate_limit_recs) > 0
        
        # Verify recommendation properties
        for rec in rate_limit_recs:
            assert rec.api_id == test_api.id
            assert rec.recommendation_type == RecommendationType.RATE_LIMITING
            assert rec.estimated_impact.improvement_percentage >= 10.0
            assert rec.priority in [
                RecommendationPriority.HIGH,
                RecommendationPriority.MEDIUM,
                RecommendationPriority.LOW
            ]
            assert rec.status == RecommendationStatus.PENDING
            assert len(rec.implementation_steps) > 0
            assert "rate" in rec.title.lower() or "limit" in rec.title.lower()
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_rate_limiting_recommendation_details(
        self, optimization_service, test_api, high_throughput_metrics
    ):
        """Test rate limiting recommendation contains proper configuration details."""
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Find rate limiting recommendation
        rate_limit_recs = [
            r for r in recommendations
            if r.recommendation_type == RecommendationType.RATE_LIMITING
        ]
        
        if len(rate_limit_recs) > 0:
            rec = rate_limit_recs[0]
            
            # Verify impact estimation
            assert rec.estimated_impact.current_value > 0
            assert rec.estimated_impact.expected_value < rec.estimated_impact.current_value
            assert rec.estimated_impact.improvement_percentage >= 15.0
            assert 0 < rec.estimated_impact.confidence <= 1.0
            
            # Verify implementation details mention rate limiting concepts
            steps_text = " ".join(rec.implementation_steps).lower()
            assert any(keyword in steps_text for keyword in ["rate", "limit", "throttle", "quota"])
            
            # Verify implementation effort
            assert rec.implementation_effort in [
                ImplementationEffort.LOW,
                ImplementationEffort.MEDIUM,
                ImplementationEffort.HIGH
            ]
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass


@pytest.mark.asyncio
class TestPolicyApplication:
    """Test policy application to Gateway."""
    
    async def test_apply_caching_policy(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test applying caching policy to Gateway."""
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Find caching recommendation
        caching_recs = [
            r for r in recommendations
            if r.recommendation_type == RecommendationType.CACHING
        ]
        
        if len(caching_recs) > 0:
            rec = caching_recs[0]
            
            # Apply policy (this would call Gateway adapter in real scenario)
            # For now, just verify the recommendation can be marked as in_progress
            updated_rec = await optimization_service.update_recommendation_status(
                recommendation_id=rec.id,
                status=RecommendationStatus.IN_PROGRESS
            )
            
            assert updated_rec is not None
            assert updated_rec.status == RecommendationStatus.IN_PROGRESS
            assert updated_rec.id == rec.id
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_apply_compression_policy(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test applying compression policy to Gateway."""
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Find compression recommendation
        compression_recs = [
            r for r in recommendations
            if r.recommendation_type == RecommendationType.COMPRESSION
        ]
        
        if len(compression_recs) > 0:
            rec = compression_recs[0]
            
            # Apply policy (this would call Gateway adapter in real scenario)
            # For now, just verify the recommendation can be marked as in_progress
            updated_rec = await optimization_service.update_recommendation_status(
                recommendation_id=rec.id,
                status=RecommendationStatus.IN_PROGRESS
            )
            
            assert updated_rec is not None
            assert updated_rec.status == RecommendationStatus.IN_PROGRESS
            assert updated_rec.id == rec.id
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_apply_rate_limiting_policy(
        self, optimization_service, test_api, high_throughput_metrics
    ):
        """Test applying rate limiting policy to Gateway."""
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Find rate limiting recommendation
        rate_limit_recs = [
            r for r in recommendations
            if r.recommendation_type == RecommendationType.RATE_LIMITING
        ]
        
        if len(rate_limit_recs) > 0:
            rec = rate_limit_recs[0]
            
            # Apply policy (this would call Gateway adapter in real scenario)
            # For now, just verify the recommendation can be marked as in_progress
            updated_rec = await optimization_service.update_recommendation_status(
                recommendation_id=rec.id,
                status=RecommendationStatus.IN_PROGRESS
            )
            
            assert updated_rec is not None
            assert updated_rec.status == RecommendationStatus.IN_PROGRESS
            assert updated_rec.id == rec.id
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass
    
    async def test_policy_application_workflow(
        self, optimization_service, test_api, slow_api_metrics
    ):
        """Test complete policy application workflow."""
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations_for_api(
            api_id=test_api.id,
            min_impact=10.0
        )
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        
        # Initial status should be PENDING
        assert rec.status == RecommendationStatus.PENDING
        
        # Mark as IN_PROGRESS (simulating policy application start)
        updated_rec = await optimization_service.update_recommendation_status(
            recommendation_id=rec.id,
            status=RecommendationStatus.IN_PROGRESS
        )
        assert updated_rec.status == RecommendationStatus.IN_PROGRESS
        
        # Mark as IMPLEMENTED (simulating successful policy application)
        implemented_rec = await optimization_service.update_recommendation_status(
            recommendation_id=rec.id,
            status=RecommendationStatus.IMPLEMENTED
        )
        assert implemented_rec.status == RecommendationStatus.IMPLEMENTED
        assert implemented_rec.implemented_at is not None
        
        # Cleanup
        for rec in recommendations:
            try:
                await optimization_service.recommendation_repo.delete(rec.id)
            except Exception:
                pass


# Made with Bob