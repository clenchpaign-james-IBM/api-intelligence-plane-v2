"""Integration tests for natural language query processing.

Tests the complete query workflow with real OpenSearch data:
- Query understanding and intent detection
- OpenSearch query generation and execution
- Response generation with LLM
- Session management and conversation context
- Follow-up query suggestions

Requires OpenSearch to be running and accessible.
Requires LLM service to be configured (or will use fallback).
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.client import get_client
from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.services.query_service import QueryService
from app.models.query import QueryType
from app.models.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)
from app.models.metric import Metric


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


@pytest.fixture(scope="module")
def query_repository():
    """Create query repository."""
    return QueryRepository()


@pytest.fixture(scope="module")
def api_repository():
    """Create API repository."""
    return APIRepository()


@pytest.fixture(scope="module")
def metrics_repository():
    """Create metrics repository."""
    return MetricsRepository()


@pytest.fixture(scope="module")
def prediction_repository():
    """Create prediction repository."""
    from app.db.repositories.prediction_repository import PredictionRepository
    return PredictionRepository()


@pytest.fixture(scope="module")
def recommendation_repository():
    """Create recommendation repository."""
    from app.db.repositories.recommendation_repository import RecommendationRepository
    return RecommendationRepository()


@pytest.fixture(scope="module")
def llm_service():
    """Create LLM service."""
    from app.services.llm_service import LLMService
    from app.config import Settings
    return LLMService(Settings())


@pytest.fixture(scope="module")
def query_service(
    query_repository,
    api_repository,
    metrics_repository,
    prediction_repository,
    recommendation_repository,
    llm_service
):
    """Create query service."""
    return QueryService(
        query_repository,
        api_repository,
        metrics_repository,
        prediction_repository,
        recommendation_repository,
        llm_service
    )


@pytest.fixture
async def sample_apis(api_repository):
    """Create sample APIs for testing."""
    apis = []
    
    # Create test APIs with different characteristics
    api_configs = [
        {
            "name": "Payment API",
            "base_path": "/api/payments",
            "health_score": 0.85,
            "error_rate": 0.02,
        },
        {
            "name": "User API",
            "base_path": "/api/users",
            "health_score": 0.92,
            "error_rate": 0.01,
        },
        {
            "name": "Order API",
            "base_path": "/api/orders",
            "health_score": 0.78,
            "error_rate": 0.05,
        },
    ]
    
    for config in api_configs:
        api = API(
            id=uuid4(),
            gateway_id=uuid4(),
            name=config["name"],
            version="1.0.0",
            base_path=config["base_path"],
            endpoints=[
                Endpoint(
                    path="/list",
                    method="GET",
                    description=f"List {config['name'].lower()}",
                )
            ],
            methods=["GET", "POST"],
            authentication_type=AuthenticationType.BEARER,
            authentication_config=None,
            ownership=None,
            is_shadow=False,
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=APIStatus.ACTIVE,
            health_score=config["health_score"] * 100,  # Convert to 0-100 scale
            current_metrics=CurrentMetrics(
                response_time_p50=100.0,
                response_time_p95=200.0,
                response_time_p99=350.0,
                error_rate=config["error_rate"],
                throughput=100.0,
                availability=99.0,
                last_error=None,
                measured_at=datetime.utcnow(),
            ),
            metadata=None,
        )
        api_repository.create(api.model_dump(), str(api.id))
        apis.append(api)
    
    yield apis
    
    # Cleanup
    for api in apis:
        try:
            api_repository.delete(str(api.id))
        except Exception:
            pass


@pytest.fixture
async def sample_metrics(metrics_repository, sample_apis):
    """Create sample metrics for testing."""
    metrics = []
    
    for api in sample_apis:
        # Create metrics for the last 24 hours
        for i in range(24):
            timestamp = datetime.utcnow() - timedelta(hours=i)
            request_count = 100 + (i * 10)
            error_count = 2 + i
            metric = Metric(
                id=uuid4(),
                api_id=api.id,
                gateway_id=api.gateway_id,
                timestamp=timestamp,
                response_time_p50=150.0 + (i * 5),
                response_time_p95=200.0 + (i * 10),
                response_time_p99=300.0 + (i * 15),
                error_rate=error_count / request_count,
                error_count=error_count,
                request_count=request_count,
                throughput=100.0,
                availability=99.0,
                status_codes={"200": 95, "400": 3, "500": 2},
                endpoint_metrics=None,
                metadata=None,
            )
            metrics_repository.create(metric.model_dump(), str(metric.id))
            metrics.append(metric)
    
    yield metrics
    
    # Cleanup
    for metric in metrics:
        try:
            metrics_repository.delete(str(metric.id))
        except Exception:
            pass


@pytest.mark.asyncio
async def test_process_status_query(query_service, sample_apis, sample_metrics):
    """Test processing a status query about API health."""
    query_text = "Show me the health status of all APIs"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert result is not None
    assert result["query_text"] == query_text
    assert result["session_id"] == session_id
    assert result["query_type"] in [QueryType.STATUS, QueryType.GENERAL]
    assert 0.0 <= result["confidence_score"] <= 1.0
    assert "response_text" in result
    assert len(result["response_text"]) > 0
    assert result["results"]["count"] >= 0
    assert len(result["follow_up_queries"]) > 0
    assert result["execution_time_ms"] > 0


@pytest.mark.asyncio
async def test_process_specific_api_query(query_service, sample_apis, sample_metrics):
    """Test querying for a specific API."""
    query_text = "What is the status of Payment API?"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert result is not None
    assert "Payment API" in result["response_text"] or "payment" in result["response_text"].lower()
    assert result["results"]["count"] >= 0


@pytest.mark.asyncio
async def test_process_error_rate_query(query_service, sample_apis, sample_metrics):
    """Test querying about error rates."""
    query_text = "Which APIs have high error rates?"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert result is not None
    assert "error" in result["response_text"].lower()
    assert result["results"]["count"] >= 0


@pytest.mark.asyncio
async def test_process_performance_query(query_service, sample_apis, sample_metrics):
    """Test querying about API performance."""
    query_text = "Show me APIs with slow response times"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert result is not None
    assert "response" in result["response_text"].lower() or "performance" in result["response_text"].lower()


@pytest.mark.asyncio
async def test_session_context_preservation(query_service, sample_apis, sample_metrics):
    """Test that session context is preserved across queries."""
    session_id = f"test-session-{uuid4()}"
    
    # First query
    result1 = await query_service.process_query(
        "Show me API health status",
        session_id
    )
    assert result1["session_id"] == session_id
    query_id_1 = result1["query_id"]
    
    # Follow-up query in same session
    result2 = await query_service.process_query(
        "What about error rates?",
        session_id
    )
    assert result2["session_id"] == session_id
    query_id_2 = result2["query_id"]
    
    # Both queries should be in the same session
    assert result1["session_id"] == result2["session_id"]
    assert query_id_1 != query_id_2  # Different query IDs


@pytest.mark.asyncio
async def test_query_history_retrieval(query_service, query_repository, sample_apis, sample_metrics):
    """Test retrieving query history for a session."""
    session_id = f"test-session-{uuid4()}"
    
    # Execute multiple queries
    queries = [
        "Show me all APIs",
        "What are the error rates?",
        "Show me performance metrics",
    ]
    
    for query_text in queries:
        await query_service.process_query(query_text, session_id)
    
    # Retrieve session history
    history = await query_repository.get_by_session(session_id)
    
    assert len(history) >= len(queries)
    assert all(q.session_id == session_id for q in history)


@pytest.mark.asyncio
async def test_follow_up_suggestions(query_service, sample_apis, sample_metrics):
    """Test that follow-up query suggestions are generated."""
    query_text = "Show me API health"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert "follow_up_queries" in result
    assert len(result["follow_up_queries"]) > 0
    assert all(isinstance(q, str) for q in result["follow_up_queries"])
    assert all(len(q) > 0 for q in result["follow_up_queries"])


@pytest.mark.asyncio
async def test_query_with_time_context(query_service, sample_apis, sample_metrics):
    """Test queries with time-based context."""
    query_text = "Show me metrics from the last 24 hours"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert result is not None
    assert result["results"]["count"] >= 0


@pytest.mark.asyncio
async def test_comparison_query(query_service, sample_apis, sample_metrics):
    """Test comparison between APIs."""
    query_text = "Compare Payment API and User API"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert result is not None
    # Should mention both APIs or comparison
    response_lower = result["response_text"].lower()
    assert "payment" in response_lower or "user" in response_lower or "compare" in response_lower


@pytest.mark.asyncio
async def test_empty_query_handling(query_service):
    """Test handling of empty queries."""
    session_id = f"test-session-{uuid4()}"
    
    with pytest.raises(ValueError, match="Query text cannot be empty"):
        await query_service.process_query("", session_id)


@pytest.mark.asyncio
async def test_query_execution_time_tracking(query_service, sample_apis, sample_metrics):
    """Test that query execution time is tracked."""
    query_text = "Show me all APIs"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert "execution_time_ms" in result
    assert result["execution_time_ms"] > 0
    assert isinstance(result["execution_time_ms"], (int, float))


@pytest.mark.asyncio
async def test_confidence_score_range(query_service, sample_apis, sample_metrics):
    """Test that confidence scores are within valid range."""
    query_text = "Show me API health status"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert "confidence_score" in result
    assert 0.0 <= result["confidence_score"] <= 1.0


@pytest.mark.asyncio
async def test_query_result_structure(query_service, sample_apis, sample_metrics):
    """Test that query results have the expected structure."""
    query_text = "Show me all APIs"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    # Verify required fields
    required_fields = [
        "query_id",
        "query_text",
        "session_id",
        "query_type",
        "response_text",
        "confidence_score",
        "results",
        "follow_up_queries",
        "execution_time_ms",
    ]
    
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    # Verify results structure
    assert "count" in result["results"]
    assert isinstance(result["results"]["count"], int)


@pytest.mark.asyncio
async def test_multiple_concurrent_sessions(query_service, sample_apis, sample_metrics):
    """Test handling multiple concurrent sessions."""
    sessions = [f"test-session-{uuid4()}" for _ in range(3)]
    
    # Execute queries in different sessions concurrently
    tasks = [
        query_service.process_query(f"Show me APIs for session {i}", session_id)
        for i, session_id in enumerate(sessions)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Verify each result has correct session ID
    for i, result in enumerate(results):
        assert result["session_id"] == sessions[i]


# Made with Bob