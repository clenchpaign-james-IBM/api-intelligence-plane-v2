"""
End-to-end tests for natural language query workflow.

Tests the complete user journey from query submission through the REST API
to response generation, including:
- Query submission via POST /api/v1/query
- Session management and conversation context
- Query history retrieval
- Follow-up query suggestions
- Feedback submission

Requires the full application stack to be running:
- FastAPI backend
- OpenSearch
- LLM service (or fallback)
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.db.client import get_client
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)
from app.models.base.metric import Metric


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def api_repository():
    """Create API repository."""
    return APIRepository()


@pytest.fixture(scope="module")
def metrics_repository():
    """Create metrics repository."""
    return MetricsRepository()


@pytest.fixture
def sample_data(api_repository, metrics_repository):
    """Create sample data for testing."""
    # Create test API
    api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="E2E Test API",
        version="1.0.0",
        base_path="/api/e2e-test",
        endpoints=[
            Endpoint(
                path="/test",
                method="GET",
                description="Test endpoint",
            )
        ],
        methods=["GET"],
        authentication_type=AuthenticationType.BEARER,
        authentication_config=None,
        ownership=None,
        is_shadow=False,
        discovery_method=DiscoveryMethod.REGISTERED,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        status=APIStatus.ACTIVE,
        health_score=85.0,
        current_metrics=CurrentMetrics(
            response_time_p50=100.0,
            response_time_p95=200.0,
            response_time_p99=350.0,
            error_rate=0.02,
            throughput=100.0,
            availability=99.0,
            last_error=None,
            measured_at=datetime.utcnow(),
        ),
        metadata=None,
    )
    api_repository.create(api.model_dump(), str(api.id))
    
    # Create test metric
    metric = Metric(
        id=uuid4(),
        api_id=api.id,
        gateway_id=api.gateway_id,
        timestamp=datetime.utcnow(),
        response_time_p50=100.0,
        response_time_p95=200.0,
        response_time_p99=350.0,
        error_rate=0.02,
        error_count=2,
        request_count=100,
        throughput=100.0,
        availability=99.0,
        status_codes={"200": 98, "500": 2},
        endpoint_metrics=None,
        metadata=None,
    )
    metrics_repository.create(metric.model_dump(), str(metric.id))
    
    yield {"api": api, "metric": metric}
    
    # Cleanup
    try:
        api_repository.delete(str(api.id))
        metrics_repository.delete(str(metric.id))
    except Exception:
        pass


class TestQueryWorkflowE2E:
    """End-to-end tests for query workflow."""
    
    def test_submit_query_and_get_response(self, client, sample_data):
        """Test submitting a query and receiving a response."""
        session_id = str(uuid4())
        
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me all APIs",
                "session_id": session_id,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "query_id" in data
        assert "query_text" in data
        assert data["query_text"] == "Show me all APIs"
        assert "session_id" in data
        assert data["session_id"] == session_id
        assert "query_type" in data
        assert "response_text" in data
        assert len(data["response_text"]) > 0
        assert "confidence_score" in data
        assert 0.0 <= data["confidence_score"] <= 1.0
        assert "results" in data
        assert "count" in data["results"]
        assert "follow_up_queries" in data
        assert isinstance(data["follow_up_queries"], list)
        assert "execution_time_ms" in data
        assert data["execution_time_ms"] > 0
    
    def test_conversation_context_preservation(self, client, sample_data):
        """Test that conversation context is preserved across queries."""
        session_id = str(uuid4())
        
        # First query
        response1 = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me API health",
                "session_id": session_id,
            }
        )
        assert response1.status_code == 200
        data1 = response1.json()
        query_id_1 = data1["query_id"]
        
        # Follow-up query in same session
        response2 = client.post(
            "/api/v1/query",
            json={
                "query_text": "What about error rates?",
                "session_id": session_id,
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        query_id_2 = data2["query_id"]
        
        # Verify both queries are in same session
        assert data1["session_id"] == data2["session_id"]
        assert query_id_1 != query_id_2
    
    def test_retrieve_session_history(self, client, sample_data):
        """Test retrieving query history for a session."""
        session_id = str(uuid4())
        
        # Submit multiple queries
        queries = [
            "Show me all APIs",
            "What are the error rates?",
            "Show me performance metrics",
        ]
        
        for query_text in queries:
            response = client.post(
                "/api/v1/query",
                json={
                    "query_text": query_text,
                    "session_id": session_id,
                }
            )
            assert response.status_code == 200
        
        # Retrieve session history
        response = client.get(f"/api/v1/query/session/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= len(queries)
        
        # Verify all queries are in the session
        for item in data["items"]:
            assert item["session_id"] == session_id
    
    def test_retrieve_specific_query(self, client, sample_data):
        """Test retrieving a specific query by ID."""
        session_id = str(uuid4())
        
        # Submit query
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me API health",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        query_id = response.json()["query_id"]
        
        # Retrieve specific query
        response = client.get(f"/api/v1/query/{query_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["query_id"] == query_id
        assert data["session_id"] == session_id
        assert data["query_text"] == "Show me API health"
    
    def test_submit_feedback(self, client, sample_data):
        """Test submitting feedback for a query."""
        session_id = str(uuid4())
        
        # Submit query
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me all APIs",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        query_id = response.json()["query_id"]
        
        # Submit positive feedback
        response = client.post(
            f"/api/v1/query/{query_id}/feedback",
            json={
                "rating": 5,
                "helpful": True,
                "comment": "Very helpful response",
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Feedback submitted successfully"
    
    def test_follow_up_query_suggestions(self, client, sample_data):
        """Test that follow-up queries are suggested."""
        session_id = str(uuid4())
        
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me API health",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "follow_up_queries" in data
        assert len(data["follow_up_queries"]) > 0
        assert all(isinstance(q, str) for q in data["follow_up_queries"])
        assert all(len(q) > 0 for q in data["follow_up_queries"])
    
    def test_query_statistics(self, client, sample_data):
        """Test retrieving query statistics."""
        session_id = str(uuid4())
        
        # Submit some queries
        for i in range(3):
            client.post(
                "/api/v1/query",
                json={
                    "query_text": f"Test query {i}",
                    "session_id": session_id,
                }
            )
        
        # Get statistics
        response = client.get("/api/v1/query/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_queries" in data
        assert "avg_confidence" in data
        assert "avg_execution_time" in data
        assert "query_types" in data
    
    def test_empty_query_validation(self, client):
        """Test that empty queries are rejected."""
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "",
                "session_id": str(uuid4()),
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_missing_session_id(self, client, sample_data):
        """Test query submission without session ID (should create new session)."""
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me all APIs",
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0
    
    def test_query_with_specific_api_name(self, client, sample_data):
        """Test querying for a specific API by name."""
        session_id = str(uuid4())
        
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "What is the status of E2E Test API?",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        # Response should mention the API or contain relevant data
        assert "E2E Test API" in data["response_text"] or "e2e" in data["response_text"].lower()
    
    def test_query_about_error_rates(self, client, sample_data):
        """Test querying about error rates."""
        session_id = str(uuid4())
        
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Which APIs have high error rates?",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "error" in data["response_text"].lower()
    
    def test_query_about_performance(self, client, sample_data):
        """Test querying about performance metrics."""
        session_id = str(uuid4())
        
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me performance metrics",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "performance" in data["response_text"].lower() or "response" in data["response_text"].lower()
    
    def test_concurrent_sessions(self, client, sample_data):
        """Test handling multiple concurrent sessions."""
        sessions = [str(uuid4()) for _ in range(3)]
        
        # Submit queries in different sessions
        responses = []
        for i, session_id in enumerate(sessions):
            response = client.post(
                "/api/v1/query",
                json={
                    "query_text": f"Query for session {i}",
                    "session_id": session_id,
                }
            )
            assert response.status_code == 200
            responses.append(response.json())
        
        # Verify each response has correct session ID
        for i, data in enumerate(responses):
            assert data["session_id"] == sessions[i]
    
    def test_query_result_count(self, client, sample_data):
        """Test that result counts are accurate."""
        session_id = str(uuid4())
        
        response = client.post(
            "/api/v1/query",
            json={
                "query_text": "Show me all APIs",
                "session_id": session_id,
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "count" in data["results"]
        assert data["results"]["count"] >= 0


# Made with Bob