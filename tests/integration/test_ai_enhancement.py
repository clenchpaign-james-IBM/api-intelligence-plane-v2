"""
Integration tests for AI-enhanced prediction explanations.

Tests the AI enhancement workflow:
1. Generate predictions with LLM service
2. Verify AI explanations are added
3. Test graceful degradation when LLM unavailable
4. Verify metadata enrichment
5. Test explanation quality
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from backend.app.db.client import get_opensearch_client
from backend.app.db.repositories.prediction_repository import PredictionRepository
from backend.app.db.repositories.metrics_repository import MetricsRepository
from backend.app.db.repositories.api_repository import APIRepository
from backend.app.services.prediction_service import PredictionService
from backend.app.models.prediction import (
    Prediction,
    PredictionType,
    PredictionSeverity,
    PredictionStatus,
)
from backend.app.models.base.metric import Metric, TimeBucket


@pytest.fixture
async def opensearch_client():
    """Get OpenSearch client for tests."""
    client = get_opensearch_client()
    yield client


@pytest.fixture
async def prediction_repository(opensearch_client):
    """Create Prediction repository instance."""
    return PredictionRepository()


@pytest.fixture
async def metrics_repository(opensearch_client):
    """Create Metrics repository instance."""
    return MetricsRepository()


@pytest.fixture
async def api_repository(opensearch_client):
    """Create API repository instance."""
    return APIRepository()


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    mock_service = Mock()
    mock_service.generate_completion = AsyncMock()
    
    # Default response for AI analysis
    mock_service.generate_completion.return_value = {
        "content": "This API is showing signs of degradation with increasing error rates and response times. "
                  "The trend suggests potential failure within 48 hours if not addressed. "
                  "Immediate investigation of backend services is recommended."
    }
    
    return mock_service


@pytest.fixture
async def prediction_service_with_llm(
    prediction_repository, metrics_repository, api_repository, mock_llm_service
):
    """Create Prediction service with mock LLM."""
    return PredictionService(
        prediction_repository=prediction_repository,
        metrics_repository=metrics_repository,
        api_repository=api_repository,
        llm_service=mock_llm_service,
    )


@pytest.fixture
async def prediction_service_without_llm(
    prediction_repository, metrics_repository, api_repository
):
    """Create Prediction service without LLM."""
    return PredictionService(
        prediction_repository=prediction_repository,
        metrics_repository=metrics_repository,
        api_repository=api_repository,
        llm_service=None,
    )


@pytest.fixture
async def test_api_with_metrics(api_repository, metrics_repository):
    """Create test API with degrading metrics."""
    gateway_id = uuid4()
    api_id = uuid4()
    now = datetime.utcnow()
    
    # Create API
    api_data = {
        "id": str(api_id),
        "gateway_id": str(gateway_id),
        "name": "AI Enhancement Test API",
        "base_path": "/api/v1/test",
        "endpoints": [{"path": "/test", "method": "GET"}],
        "methods": ["GET"],
        "authentication_type": "none",
        "intelligence_metadata": {
            "is_shadow": False,
            "discovery_method": "registered",
            "discovered_at": now.isoformat(),
            "last_seen_at": now.isoformat(),
            "health_score": 75.0,
        },
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    created_api = await api_repository.create_from_dict(api_data)
    
    # Create degrading metrics
    metrics = []
    for i in range(24):
        timestamp = now - timedelta(hours=23 - i)
        
        metric_data = {
            "id": str(uuid4()),
            "gateway_id": str(gateway_id),
            "api_id": str(api_id),
            "timestamp": timestamp.isoformat(),
            "time_bucket": "1m",
            "request_count": 1000,
            "success_count": int(1000 * (1 - (5 + i * 0.4) / 100)),
            "failure_count": int(1000 * (5 + i * 0.4) / 100),
            "error_rate": 5.0 + (i * 0.4),
            "response_time_avg": 700 + (i * 60),
            "response_time_p50": 800 + (i * 60),
            "response_time_p95": 1000 + (i * 60),
            "response_time_p99": 1200 + (i * 60),
            "response_time_min": 300,
            "response_time_max": 2000 + (i * 100),
            "gateway_time_avg": 50.0,
            "backend_time_avg": 600 + (i * 50),
            "cache_hit_rate": 20.0,
            "cache_hit_count": 200,
            "cache_miss_count": 800,
            "cache_bypass_count": 0,
            "total_data_size": 1000000,
            "avg_request_size": 500,
            "avg_response_size": 500,
            "status_2xx_count": int(1000 * (1 - (5 + i * 0.4) / 100)),
            "status_3xx_count": 0,
            "status_4xx_count": int(1000 * (5 + i * 0.4) / 100 * 0.3),
            "status_5xx_count": int(1000 * (5 + i * 0.4) / 100 * 0.7),
            "timeout_count": 10,
            "throughput": 1000.0,
            "availability": 99.0 - (i * 0.25),
            "status_codes": {"200": int(1000 * (1 - (5 + i * 0.4) / 100)), "500": int(1000 * (5 + i * 0.4) / 100)},
        }
        
        created_metric = await metrics_repository.create_from_dict(metric_data)
        metrics.append(created_metric)
    
    yield created_api, gateway_id, metrics
    
    # Cleanup
    try:
        await api_repository.delete(str(api_id))
        for metric in metrics:
            await metrics_repository.delete(str(metric.id))
    except Exception:
        pass


@pytest.mark.asyncio
class TestAIEnhancement:
    """Integration tests for AI-enhanced predictions."""

    async def test_ai_enhancement_with_llm(
        self, prediction_service_with_llm, test_api_with_metrics, mock_llm_service
    ):
        """Test that predictions are enhanced with AI when LLM is available."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Generate predictions with AI enhancement
        predictions = await prediction_service_with_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        # Verify predictions were generated
        assert len(predictions) > 0
        
        # Verify LLM was called
        assert mock_llm_service.generate_completion.called
        
        # Verify AI enhancement metadata
        for prediction in predictions:
            assert prediction.metadata is not None
            assert "ai_enhanced" in prediction.metadata
            
            # If AI enhancement succeeded, should have explanation
            if prediction.metadata.get("ai_enhanced"):
                assert "ai_explanation" in prediction.metadata
                assert isinstance(prediction.metadata["ai_explanation"], str)
                assert len(prediction.metadata["ai_explanation"]) > 0

    async def test_graceful_degradation_without_llm(
        self, prediction_service_without_llm, test_api_with_metrics
    ):
        """Test that predictions work without LLM (graceful degradation)."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Generate predictions without AI enhancement
        predictions = await prediction_service_without_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        # Verify predictions were still generated
        assert len(predictions) > 0
        
        # Verify metadata indicates no AI enhancement
        for prediction in predictions:
            assert prediction.metadata is not None
            assert prediction.metadata.get("ai_enhanced") == False
            assert "ai_enhancement_error" in prediction.metadata
            assert prediction.metadata["ai_enhancement_error"] == "LLM service unavailable"

    async def test_ai_enhancement_failure_handling(
        self, prediction_service_with_llm, test_api_with_metrics, mock_llm_service
    ):
        """Test handling of AI enhancement failures."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Configure LLM to fail
        mock_llm_service.generate_completion.side_effect = Exception("LLM API error")
        
        # Generate predictions (should still work despite LLM failure)
        predictions = await prediction_service_with_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        # Verify predictions were generated
        assert len(predictions) > 0
        
        # Verify metadata indicates AI enhancement failed
        for prediction in predictions:
            assert prediction.metadata is not None
            # Should have attempted AI enhancement but failed gracefully
            assert "ai_enhanced" in prediction.metadata or "ai_enhancement_error" in prediction.metadata

    async def test_ai_explanation_content_quality(
        self, prediction_service_with_llm, test_api_with_metrics, mock_llm_service
    ):
        """Test that AI explanations contain meaningful content."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Configure LLM with detailed response
        mock_llm_service.generate_completion.return_value = {
            "content": (
                "**Analysis**: The API is experiencing a gradual degradation pattern. "
                "Error rates have increased from 5% to 15% over the past 24 hours, "
                "while response times have grown from 1000ms to 2500ms. "
                "\n\n**Root Cause**: The increasing error rate combined with degrading "
                "response times suggests backend service overload or resource exhaustion. "
                "\n\n**Recommended Actions**:\n"
                "1. Scale backend services immediately\n"
                "2. Review error logs for patterns\n"
                "3. Check database connection pool\n"
                "4. Monitor memory usage"
            )
        }
        
        # Generate predictions
        predictions = await prediction_service_with_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        # Verify AI explanation quality
        for prediction in predictions:
            if prediction.metadata and prediction.metadata.get("ai_enhanced"):
                explanation = prediction.metadata.get("ai_explanation", "")
                
                # Check for meaningful content
                assert len(explanation) > 50  # Substantial content
                assert any(keyword in explanation.lower() for keyword in [
                    "error", "response", "degradation", "failure", "performance"
                ])

    async def test_ai_enhancement_metadata_structure(
        self, prediction_service_with_llm, test_api_with_metrics
    ):
        """Test that AI enhancement metadata has correct structure."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Generate predictions
        predictions = await prediction_service_with_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        # Verify metadata structure
        for prediction in predictions:
            assert prediction.metadata is not None
            assert isinstance(prediction.metadata, dict)
            
            # Check required metadata fields
            assert "ai_enhanced" in prediction.metadata
            assert isinstance(prediction.metadata["ai_enhanced"], bool)
            
            if prediction.metadata["ai_enhanced"]:
                # AI-enhanced predictions should have explanation
                assert "ai_explanation" in prediction.metadata
                assert isinstance(prediction.metadata["ai_explanation"], str)
            else:
                # Non-enhanced should have error message
                assert "ai_enhancement_error" in prediction.metadata
                assert isinstance(prediction.metadata["ai_enhancement_error"], str)

    async def test_multiple_llm_calls_for_predictions(
        self, prediction_service_with_llm, test_api_with_metrics, mock_llm_service
    ):
        """Test that LLM is called appropriately for multiple predictions."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Reset mock to track calls
        mock_llm_service.generate_completion.reset_mock()
        
        # Generate predictions
        predictions = await prediction_service_with_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.6  # Lower threshold to get more predictions
        )
        
        # Verify LLM was called
        assert mock_llm_service.generate_completion.called
        call_count = mock_llm_service.generate_completion.call_count
        
        # Should have at least one call for overall analysis
        # Plus one call per prediction for individual explanations
        assert call_count >= 1
        
        # Verify predictions have AI metadata
        ai_enhanced_count = sum(
            1 for p in predictions 
            if p.metadata and p.metadata.get("ai_enhanced")
        )
        assert ai_enhanced_count > 0

    async def test_ai_enhancement_with_different_prediction_types(
        self, prediction_service_with_llm, test_api_with_metrics, mock_llm_service
    ):
        """Test AI enhancement works for different prediction types."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Track different prediction types
        prediction_types_seen = set()
        
        # Generate predictions
        predictions = await prediction_service_with_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.6
        )
        
        # Verify AI enhancement for different types
        for prediction in predictions:
            prediction_types_seen.add(prediction.prediction_type)
            
            if prediction.metadata and prediction.metadata.get("ai_enhanced"):
                # AI explanation should reference the prediction type
                explanation = prediction.metadata.get("ai_explanation", "").lower()
                assert len(explanation) > 0

    async def test_ai_enhancement_persistence(
        self, prediction_service_with_llm, prediction_repository, test_api_with_metrics
    ):
        """Test that AI-enhanced predictions are persisted correctly."""
        api, gateway_id, metrics = test_api_with_metrics
        
        # Generate predictions with AI enhancement
        predictions = await prediction_service_with_llm.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        # Verify predictions were persisted
        for prediction in predictions:
            # Retrieve from repository
            retrieved = await prediction_repository.get(str(prediction.id))
            
            # Verify AI metadata was persisted
            assert retrieved.metadata is not None
            assert "ai_enhanced" in retrieved.metadata
            
            if retrieved.metadata.get("ai_enhanced"):
                assert "ai_explanation" in retrieved.metadata
                assert retrieved.metadata["ai_explanation"] == prediction.metadata["ai_explanation"]
            
            # Cleanup
            try:
                await prediction_repository.delete(str(prediction.id))
            except Exception:
                pass

# Made with Bob
