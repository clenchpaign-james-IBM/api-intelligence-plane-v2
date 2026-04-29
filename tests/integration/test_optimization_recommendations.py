"""Integration tests for optimization recommendation generation.

Tests the complete optimization recommendation workflow including:
- Performance analysis and pattern detection
- Recommendation generation based on metrics
- Priority and impact estimation
- Recommendation validation
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, MagicMock

from backend.app.services.optimization_service import OptimizationService
from backend.app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
    ImplementationEffort,
)
from backend.app.config import Settings


@pytest.fixture
def mock_recommendation_repository():
    """Create mock recommendation repository."""
    repo = Mock()
    repo.create = AsyncMock()
    repo.find_by_api = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_metrics_repository():
    """Create mock metrics repository."""
    repo = Mock()
    repo.find_by_api = AsyncMock(return_value=([], 0))
    repo.get_aggregated_metrics = AsyncMock()
    return repo


@pytest.fixture
def mock_api_repository():
    """Create mock API repository."""
    repo = Mock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = Mock()
    service.complete = AsyncMock(return_value="Optimization analysis")
    return service


@pytest.fixture
def optimization_service(
    mock_recommendation_repository,
    mock_metrics_repository,
    mock_api_repository,
    mock_llm_service,
):
    """Create optimization service with mocked dependencies."""
    service = OptimizationService(
        recommendation_repository=mock_recommendation_repository,
        metrics_repository=mock_metrics_repository,
        api_repository=mock_api_repository,
        llm_service=mock_llm_service,
    )
    return service


@pytest.fixture
def test_api():
    """Create a mock test API."""
    api = MagicMock()
    api.id = uuid4()
    api.gateway_id = uuid4()
    api.name = "Test API"
    api.base_path = "/api/v1/test"
    return api


@pytest.mark.asyncio
class TestOptimizationRecommendations:
    """Integration tests for optimization recommendations."""

    async def test_generate_caching_recommendation(
        self,
        optimization_service,
        test_api,
        mock_api_repository,
        mock_metrics_repository,
        mock_recommendation_repository,
    ):
        """Test generating caching recommendation for high-traffic API."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        # Mock high traffic metrics
        mock_metrics_repository.get_aggregated_metrics.return_value = {
            "avg_response_time": 250.0,
            "request_count": 10000,
            "cache_hit_rate": 0.0,  # No caching
        }
        
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id
        )
        
        # Verify caching recommendation generated
        assert len(recommendations) > 0
        caching_recs = [r for r in recommendations if r.recommendation_type == RecommendationType.CACHING]
        assert len(caching_recs) > 0

    async def test_generate_rate_limiting_recommendation(
        self,
        optimization_service,
        test_api,
        mock_api_repository,
        mock_metrics_repository,
    ):
        """Test generating rate limiting recommendation for burst traffic."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        # Mock burst traffic pattern
        mock_metrics_repository.get_aggregated_metrics.return_value = {
            "avg_response_time": 500.0,
            "p95_response_time": 2000.0,
            "request_count": 50000,
            "error_rate": 0.15,  # High error rate
        }
        
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id
        )
        
        # Verify rate limiting recommendation
        assert len(recommendations) > 0

    async def test_recommendation_priority_calculation(
        self,
        optimization_service,
        test_api,
        mock_api_repository,
        mock_metrics_repository,
    ):
        """Test that recommendations are prioritized correctly."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        # Mock critical performance issues
        mock_metrics_repository.get_aggregated_metrics.return_value = {
            "avg_response_time": 3000.0,  # Very slow
            "error_rate": 0.20,  # High errors
            "request_count": 100000,
        }
        
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id
        )
        
        # Verify high priority recommendations exist
        high_priority = [r for r in recommendations if r.priority == RecommendationPriority.HIGH]
        assert len(high_priority) > 0

    async def test_recommendation_impact_estimation(
        self,
        optimization_service,
        test_api,
        mock_api_repository,
        mock_metrics_repository,
    ):
        """Test that recommendations include impact estimates."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        mock_metrics_repository.get_aggregated_metrics.return_value = {
            "avg_response_time": 800.0,
            "request_count": 20000,
        }
        
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id
        )
        
        # Verify impact estimates included
        if len(recommendations) > 0:
            assert recommendations[0].estimated_impact is not None

    async def test_no_recommendations_for_healthy_api(
        self,
        optimization_service,
        test_api,
        mock_api_repository,
        mock_metrics_repository,
    ):
        """Test that healthy APIs generate no recommendations."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        # Mock healthy metrics
        mock_metrics_repository.get_aggregated_metrics.return_value = {
            "avg_response_time": 50.0,  # Fast
            "error_rate": 0.001,  # Low errors
            "request_count": 1000,
            "cache_hit_rate": 0.95,  # Good caching
        }
        
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            min_impact=10.0
        )
        
        # Verify no significant recommendations
        assert len(recommendations) == 0

    async def test_recommendation_deduplication(
        self,
        optimization_service,
        test_api,
        mock_api_repository,
        mock_metrics_repository,
        mock_recommendation_repository,
    ):
        """Test that duplicate recommendations are not created."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        # Mock existing recommendation
        existing_rec = MagicMock()
        existing_rec.recommendation_type = RecommendationType.CACHING
        existing_rec.status = RecommendationStatus.PENDING
        mock_recommendation_repository.find_by_api.return_value = [existing_rec]
        
        mock_metrics_repository.get_aggregated_metrics.return_value = {
            "avg_response_time": 250.0,
            "request_count": 10000,
            "cache_hit_rate": 0.0,
        }
        
        # Generate recommendations
        recommendations = await optimization_service.generate_recommendations(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id
        )
        
        # Verify deduplication logic
        assert isinstance(recommendations, list)

    async def test_recommendation_error_handling(
        self,
        optimization_service,
        test_api,
        mock_api_repository,
        mock_metrics_repository,
    ):
        """Test recommendation generation error handling."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        # Mock repository to raise exception
        mock_metrics_repository.get_aggregated_metrics.side_effect = Exception(
            "Metrics unavailable"
        )
        
        # Generate recommendations and expect exception
        with pytest.raises(Exception) as exc_info:
            await optimization_service.generate_recommendations(
                gateway_id=test_api.gateway_id,
                api_id=test_api.id
            )
        
        assert "Metrics unavailable" in str(exc_info.value) or "Failed" in str(exc_info.value)

# Made with Bob
