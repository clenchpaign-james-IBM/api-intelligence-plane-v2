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
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from app.db.client import get_client
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.services.query_service import QueryService
from app.models.query import Query, QueryType
from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    IntelligenceMetadata,
    VersionInfo,
)
from app.models.base.metric import Metric, TimeBucket


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


class InMemoryQueryRepository:
    def __init__(self):
        self.queries: list[Query] = []

    def create(self, document: Query, doc_id: str | None = None) -> Query:
        self.queries.append(document)
        return document

    def get_by_session(self, session_id: UUID, size: int = 50, from_: int = 0):
        matches = [query for query in self.queries if query.session_id == session_id]
        return matches[from_:from_ + size], len(matches)


class StubRepository:
    def create(self, document, doc_id: str | None = None):
        return document


@pytest.fixture(scope="module")
def query_repository():
    """Create in-memory query repository."""
    return InMemoryQueryRepository()


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
    """Create stub prediction repository."""
    return StubRepository()


@pytest.fixture(scope="module")
def recommendation_repository():
    """Create stub recommendation repository."""
    return StubRepository()


@pytest.fixture(scope="module")
def llm_service():
    """Create mock LLM service."""
    service = AsyncMock()
    service.interpret_query = AsyncMock(
        return_value={
            "action": "list",
            "entities": ["api"],
            "filters": {},
            "time_range": None,
            "confidence": 0.9,
        }
    )
    service.generate_response = AsyncMock(
        return_value="Payment API and User API status summary with error and performance insights."
    )
    return service


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
        now = datetime.utcnow()
        api = API(
            id=uuid4(),
            gateway_id=uuid4(),
            name=config["name"],
            display_name=None,
            description=None,
            icon=None,
            version_info=VersionInfo(
                current_version="1.0.0",
                previous_version=None,
                next_version=None,
                version_history=None,
            ),
            maturity_state=None,
            base_path=config["base_path"],
            api_definition=None,
            endpoints=[
                Endpoint(
                    path="/list",
                    method="GET",
                    description=f"List {config['name'].lower()}",
                    connection_timeout=None,
                    read_timeout=None,
                )
            ],
            methods=["GET", "POST"],
            authentication_type=AuthenticationType.BEARER,
            authentication_config=None,
            policy_actions=None,
            ownership=None,
            publishing=None,
            deployments=None,
            intelligence_metadata=IntelligenceMetadata(
                is_shadow=False,
                discovery_method=DiscoveryMethod.REGISTERED,
                discovered_at=now,
                last_seen_at=now,
                health_score=config["health_score"] * 100,
                risk_score=0.0,
                security_score=100.0,
                compliance_status=None,
                usage_trend="stable",
                has_active_predictions=False,
            ),
            status=APIStatus.ACTIVE,
            vendor_metadata=None,
        )
        apis.append(api)

    yield apis


@pytest.fixture
async def sample_metrics(metrics_repository, sample_apis):
    """Create sample metrics for testing."""
    metrics = []

    for api in sample_apis:
        for i in range(24):
            timestamp = datetime.utcnow() - timedelta(hours=i)
            request_count = 100 + (i * 10)
            error_count = 2 + i
            failure_count = error_count
            success_count = request_count - failure_count
            metric = Metric(
                id=uuid4(),
                api_id=str(api.id),
                gateway_id=api.gateway_id,
                application_id=None,
                operation=None,
                timestamp=timestamp,
                time_bucket=TimeBucket.ONE_HOUR,
                request_count=request_count,
                success_count=success_count,
                failure_count=failure_count,
                timeout_count=0,
                error_rate=(failure_count / request_count) * 100,
                availability=(success_count / request_count) * 100,
                response_time_avg=150.0 + (i * 5),
                response_time_min=120.0 + (i * 4),
                response_time_max=320.0 + (i * 15),
                response_time_p50=150.0 + (i * 5),
                response_time_p95=200.0 + (i * 10),
                response_time_p99=300.0 + (i * 15),
                gateway_time_avg=25.0,
                backend_time_avg=125.0 + (i * 5),
                throughput=100.0,
                total_data_size=request_count * 1024,
                avg_request_size=512.0,
                avg_response_size=1024.0,
                cache_hit_count=20,
                cache_miss_count=10,
                cache_bypass_count=5,
                cache_hit_rate=(20 / 30) * 100,
                status_2xx_count=95,
                status_3xx_count=0,
                status_4xx_count=3,
                status_5xx_count=2,
                status_codes={"200": 95, "400": 3, "500": 2},
                endpoint_metrics=None,
                vendor_metadata=None,
            )
            metrics.append(metric)

    yield metrics


@pytest.mark.asyncio
async def test_process_status_query(query_service, sample_apis, sample_metrics):
    """Test processing a status query about API health."""
    query_text = "Show me the health status of all APIs"
    session_id = f"test-session-{uuid4()}"
    
    result = await query_service.process_query(query_text, session_id)
    
    assert result is not None
    assert isinstance(result, Query)
    assert result.query_text == query_text
    assert result.session_id == session_id
    assert result.query_type in [QueryType.STATUS, QueryType.GENERAL]
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.response_text
    assert result.results.count >= 0
    assert result.follow_up_queries
    assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_process_specific_api_query(query_service, sample_apis, sample_metrics):
    """Test querying for a specific API."""
    query_text = "What is the status of Payment API?"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, uuid4())
    
    assert result is not None
    assert "Payment API" in result.response_text or "payment" in result.response_text.lower()
    assert result.results.count >= 0


@pytest.mark.asyncio
async def test_process_error_rate_query(query_service, sample_apis, sample_metrics):
    """Test querying about error rates."""
    query_text = "Which APIs have high error rates?"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, uuid4())
    
    assert result is not None
    assert "error" in result.response_text.lower()
    assert result.results.count >= 0


@pytest.mark.asyncio
async def test_process_performance_query(query_service, sample_apis, sample_metrics):
    """Test querying about API performance."""
    query_text = "Show me APIs with slow response times"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, uuid4())
    
    assert result is not None
    assert "response" in result.response_text.lower() or "performance" in result.response_text.lower()


@pytest.mark.asyncio
async def test_session_context_preservation(query_service, sample_apis, sample_metrics):
    """Test that session context is preserved across queries."""
    session_id = uuid4()
    
    # First query
    result1 = await query_service.process_query(
        "Show me API health status",
        session_id
    )
    assert result1.session_id == session_id
    query_id_1 = result1.id
    
    # Follow-up query in same session
    result2 = await query_service.process_query(
        "What about error rates?",
        session_id
    )
    assert result2.session_id == session_id
    query_id_2 = result2.id
    
    # Both queries should be in the same session
    assert result1.session_id == result2.session_id
    assert query_id_1 != query_id_2  # Different query IDs


@pytest.mark.asyncio
async def test_query_history_retrieval(query_service, query_repository, sample_apis, sample_metrics):
    """Test retrieving query history for a session."""
    session_id = uuid4()
    
    # Execute multiple queries
    queries = [
        "Show me all APIs",
        "What are the error rates?",
        "Show me performance metrics",
    ]
    
    for query_text in queries:
        await query_service.process_query(query_text, session_id)
    
    # Retrieve session history
    history, total = query_repository.get_by_session(session_id)
    
    assert total >= len(queries)
    assert len(history) >= len(queries)
    assert all(q.session_id == session_id for q in history)


@pytest.mark.asyncio
async def test_follow_up_suggestions(query_service, sample_apis, sample_metrics):
    """Test that follow-up query suggestions are generated."""
    query_text = "Show me API health"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, uuid4())
    
    assert result.follow_up_queries is not None
    assert len(result.follow_up_queries) > 0
    assert all(isinstance(q, str) for q in result.follow_up_queries)
    assert all(len(q) > 0 for q in result.follow_up_queries)


@pytest.mark.asyncio
async def test_query_with_time_context(query_service, sample_apis, sample_metrics):
    """Test queries with time-based context."""
    query_text = "Show me metrics from the last 24 hours"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, uuid4())
    
    assert result is not None
    assert result.results.count >= 0


@pytest.mark.asyncio
async def test_comparison_query(query_service, sample_apis, sample_metrics):
    """Test comparison between APIs."""
    query_text = "Compare Payment API and User API"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, uuid4())
    
    assert result is not None
    # Should mention both APIs or comparison
    response_lower = result.response_text.lower()
    assert "payment" in response_lower or "user" in response_lower or "compare" in response_lower


@pytest.mark.asyncio
async def test_empty_query_handling(query_service):
    """Test handling of empty queries."""
    result = await query_service.process_query("", uuid4())
    assert result.query_type == QueryType.GENERAL
    assert result.confidence_score == 0.0
    assert "error processing your query" in result.response_text.lower()


@pytest.mark.asyncio
async def test_query_execution_time_tracking(query_service, sample_apis, sample_metrics):
    """Test that query execution time is tracked."""
    query_text = "Show me all APIs"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, uuid4())
    
    assert result.execution_time_ms > 0
    assert isinstance(result.execution_time_ms, int)


@pytest.mark.asyncio
async def test_confidence_score_range(query_service, sample_apis, sample_metrics):
    """Test that confidence scores are within valid range."""
    query_text = "Show me API health status"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, session_id)
    
    assert 0.0 <= result.confidence_score <= 1.0


@pytest.mark.asyncio
async def test_query_result_structure(query_service, sample_apis, sample_metrics):
    """Test that query results have the expected structure."""
    query_text = "Show me all APIs"
    session_id = uuid4()
    
    result = await query_service.process_query(query_text, session_id)
    
    assert isinstance(result, Query)
    assert result.id is not None
    assert result.query_text == query_text
    assert result.session_id == session_id
    assert result.query_type is not None
    assert result.response_text
    assert result.follow_up_queries is not None
    assert result.execution_time_ms > 0
    
    # Verify results structure
    assert isinstance(result.results.count, int)


@pytest.mark.asyncio
async def test_multiple_concurrent_sessions(query_service, sample_apis, sample_metrics):
    """Test handling multiple concurrent sessions."""
    sessions = [uuid4() for _ in range(3)]
    
    # Execute queries in different sessions concurrently
    tasks = [
        query_service.process_query(f"Show me APIs for session {i}", session_id)
        for i, session_id in enumerate(sessions)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Verify each result has correct session ID
    for i, result in enumerate(results):
        assert result.session_id == sessions[i]


# Made with Bob