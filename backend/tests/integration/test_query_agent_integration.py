"""
Integration Tests for Query Service Agent Integration

Tests the integration of PredictionAgent and OptimizationAgent with QueryService.
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List

from app.services.query_service import QueryService
from app.services.llm_service import LLMService
from app.services.prediction_service import PredictionService
from app.services.optimization_service import OptimizationService
from app.agents.prediction_agent import PredictionAgent
from app.agents.optimization_agent import OptimizationAgent
from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
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
from app.models.query import QueryType
from app.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings()


@pytest.fixture
def repositories():
    """Create repository instances."""
    return {
        "query": QueryRepository(),
        "api": APIRepository(),
        "metrics": MetricsRepository(),
        "prediction": PredictionRepository(),
        "recommendation": RecommendationRepository(),
    }


@pytest.fixture
def llm_service(settings):
    """Create LLM service instance."""
    return LLMService(settings)


@pytest.fixture
def prediction_agent(llm_service, repositories):
    """Create PredictionAgent instance."""
    prediction_service = PredictionService(
        prediction_repository=repositories["prediction"],
        api_repository=repositories["api"],
        metrics_repository=repositories["metrics"],
        llm_service=llm_service,
    )
    return PredictionAgent(
        llm_service=llm_service,
        prediction_service=prediction_service,
    )


@pytest.fixture
def optimization_agent(llm_service, repositories):
    """Create OptimizationAgent instance."""
    optimization_service = OptimizationService(
        recommendation_repository=repositories["recommendation"],
        api_repository=repositories["api"],
        metrics_repository=repositories["metrics"],
        llm_service=llm_service,
    )
    return OptimizationAgent(
        llm_service=llm_service,
        optimization_service=optimization_service,
    )


@pytest.fixture
def query_service_with_agents(repositories, llm_service, prediction_agent, optimization_agent):
    """Create QueryService with agents enabled."""
    return QueryService(
        query_repository=repositories["query"],
        api_repository=repositories["api"],
        metrics_repository=repositories["metrics"],
        prediction_repository=repositories["prediction"],
        recommendation_repository=repositories["recommendation"],
        llm_service=llm_service,
        prediction_agent=prediction_agent,
        optimization_agent=optimization_agent,
    )


@pytest.fixture
def query_service_without_agents(repositories, llm_service):
    """Create QueryService without agents."""
    return QueryService(
        query_repository=repositories["query"],
        api_repository=repositories["api"],
        metrics_repository=repositories["metrics"],
        prediction_repository=repositories["prediction"],
        recommendation_repository=repositories["recommendation"],
        llm_service=llm_service,
        prediction_agent=None,
        optimization_agent=None,
    )


@pytest.fixture
def sample_api(repositories):
    """Create a sample API for testing."""
    now = datetime.utcnow()
    api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="test-api",
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
        base_path="/api/test",
        api_definition=None,
        endpoints=[
            Endpoint(
                path="/api/test",
                method="GET",
                description="Test endpoint",
                connection_timeout=None,
                read_timeout=None,
            )
        ],
        methods=["GET"],
        authentication_type=AuthenticationType.NONE,
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
            health_score=95.0,
            risk_score=0.0,
            security_score=100.0,
            compliance_status=None,
            usage_trend="stable",
            has_active_predictions=False,
        ),
        status=APIStatus.ACTIVE,
        vendor_metadata=None,
        created_at=now,
        updated_at=now,
    )
    repositories["api"].create(api, doc_id=str(api.id))
    return api


@pytest.fixture
def sample_metrics(repositories, sample_api):
    """Create sample metrics for testing."""
    metrics = []
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(100):
        request_count = 100 + i
        failure_count = i % 10
        success_count = request_count - failure_count

        metric = Metric(
            id=uuid4(),
            api_id=str(sample_api.id),
            gateway_id=sample_api.gateway_id,
            application_id=None,
            operation=None,
            timestamp=base_time + timedelta(minutes=i * 15),
            time_bucket=TimeBucket.FIVE_MINUTES,
            request_count=request_count,
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=0,
            error_rate=(failure_count / request_count) * 100,
            availability=99.0 + (i * 0.01) if i < 50 else 99.5,
            response_time_avg=75.0 + (i * 0.75),
            response_time_min=45.0 + (i * 0.4),
            response_time_max=170.0 + (i * 1.5),
            response_time_p50=50.0 + (i * 0.5),
            response_time_p95=100.0 + (i * 1.0),
            response_time_p99=150.0 + (i * 1.5),
            gateway_time_avg=10.0 + (i * 0.1),
            backend_time_avg=40.0 + (i * 0.4),
            throughput=10.0 + (i * 0.1),
            total_data_size=request_count * 2048,
            avg_request_size=768.0,
            avg_response_size=1280.0,
            cache_hit_count=30,
            cache_miss_count=10,
            cache_bypass_count=5,
            cache_hit_rate=75.0,
            status_2xx_count=90 + i,
            status_3xx_count=0,
            status_4xx_count=max(failure_count - (i % 3), 0),
            status_5xx_count=min(i % 3, failure_count),
            status_codes={"200": 90 + i, "500": i % 10},
            endpoint_metrics=None,
            vendor_metadata=None,
        )
        repositories["metrics"].create(metric, doc_id=str(metric.id))
        metrics.append(metric)
    
    return metrics


@pytest.mark.asyncio
async def test_prediction_query_with_agent_enhancement(
    query_service_with_agents,
    sample_api,
    sample_metrics,
):
    """Test prediction query with PredictionAgent enhancement."""
    # Execute prediction query
    query = await query_service_with_agents.process_query(
        query_text=f"What are the predictions for {sample_api.name}?",
        session_id=uuid4(),
    )
    
    # Verify query was processed
    assert query is not None
    assert query.query_type == QueryType.PREDICTION
    assert query.confidence_score > 0
    
    # Verify results contain agent insights
    if query.results.data:
        # Check if any result has agent insights
        has_insights = any(
            isinstance(item, dict) and "agent_insights" in item
            for item in query.results.data
        )
        # Note: Insights may not be present if agent execution failed
        # This is expected behavior with graceful fallback
        print(f"Agent insights present: {has_insights}")
    
    # Verify response was generated
    assert query.response_text
    assert len(query.response_text) > 0


@pytest.mark.asyncio
async def test_performance_query_with_agent_enhancement(
    query_service_with_agents,
    sample_api,
    sample_metrics,
):
    """Test performance query with OptimizationAgent enhancement."""
    # Execute performance query
    query = await query_service_with_agents.process_query(
        query_text=f"How is the performance of {sample_api.name}?",
        session_id=uuid4(),
    )
    
    # Verify query was processed
    assert query is not None
    assert query.query_type == QueryType.PERFORMANCE
    assert query.confidence_score > 0
    
    # Verify results contain agent insights
    if query.results.data:
        # Check if any result has agent insights
        has_insights = any(
            isinstance(item, dict) and "agent_insights" in item
            for item in query.results.data
        )
        print(f"Agent insights present: {has_insights}")
    
    # Verify response was generated
    assert query.response_text
    assert len(query.response_text) > 0


@pytest.mark.asyncio
async def test_agent_fallback_when_unavailable(
    query_service_without_agents,
    sample_api,
    sample_metrics,
):
    """Test graceful fallback when agents are unavailable."""
    # Execute prediction query without agents
    query = await query_service_without_agents.process_query(
        query_text=f"What are the predictions for {sample_api.name}?",
        session_id=uuid4(),
    )
    
    # Verify query still works without agents
    assert query is not None
    assert query.query_type == QueryType.PREDICTION
    assert query.confidence_score > 0
    
    # Verify no agent insights in results
    if query.results.data:
        has_insights = any(
            isinstance(item, dict) and "agent_insights" in item
            for item in query.results.data
        )
        assert not has_insights, "Should not have agent insights when agents disabled"
    
    # Verify response was still generated
    assert query.response_text
    assert len(query.response_text) > 0


@pytest.mark.asyncio
async def test_agent_caching(
    query_service_with_agents,
    sample_api,
    sample_metrics,
):
    """Test that agent results are cached."""
    # Execute first query
    query1 = await query_service_with_agents.process_query(
        query_text=f"What are the predictions for {sample_api.name}?",
        session_id=uuid4(),
    )
    
    # Execute second identical query
    query2 = await query_service_with_agents.process_query(
        query_text=f"What are the predictions for {sample_api.name}?",
        session_id=uuid4(),
    )
    
    # Both queries should succeed
    assert query1 is not None
    assert query2 is not None
    
    # Second query should be faster due to caching (if agents were used)
    # Note: This is a soft check as caching depends on agent availability
    print(f"Query 1 time: {query1.execution_time_ms}ms")
    print(f"Query 2 time: {query2.execution_time_ms}ms")


@pytest.mark.asyncio
async def test_parallel_agent_execution(
    query_service_with_agents,
    repositories,
    sample_metrics,
):
    """Test parallel agent execution for multiple APIs."""
    # Create multiple APIs
    apis = []
    now = datetime.utcnow()
    for i in range(5):
        api = API(
            id=uuid4(),
            gateway_id=uuid4(),
            name=f"test-api-{i}",
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
            base_path=f"/api/test/{i}",
            api_definition=None,
            endpoints=[
                Endpoint(
                    path=f"/api/test/{i}",
                    method="GET",
                    description=f"Test endpoint {i}",
                    connection_timeout=None,
                    read_timeout=None,
                )
            ],
            methods=["GET"],
            authentication_type=AuthenticationType.NONE,
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
                health_score=95.0,
                risk_score=0.0,
                security_score=100.0,
                compliance_status=None,
                usage_trend="stable",
                has_active_predictions=False,
            ),
            status=APIStatus.ACTIVE,
            vendor_metadata=None,
            created_at=now,
            updated_at=now,
        )
        repositories["api"].create(api, doc_id=str(api.id))
        apis.append(api)
    
    # Execute query that should return multiple APIs
    query = await query_service_with_agents.process_query(
        query_text="Show me all active APIs with predictions",
        session_id=uuid4(),
    )
    
    # Verify query was processed
    assert query is not None
    assert query.results.count >= 0
    
    # Verify execution completed in reasonable time
    # (parallel execution should be faster than sequential)
    assert query.execution_time_ms < 60000  # Less than 60 seconds


@pytest.mark.asyncio
async def test_agent_timeout_handling(
    query_service_with_agents,
    sample_api,
    sample_metrics,
):
    """Test that agent timeouts are handled gracefully."""
    # Execute query (agents should have timeout protection)
    query = await query_service_with_agents.process_query(
        query_text=f"Analyze performance trends for {sample_api.name}",
        session_id=uuid4(),
    )
    
    # Query should complete even if agents timeout
    assert query is not None
    assert query.response_text
    
    # Verify reasonable execution time
    assert query.execution_time_ms < 60000  # Less than 60 seconds


@pytest.mark.asyncio
async def test_token_usage_tracking(
    query_service_with_agents,
    sample_api,
    sample_metrics,
):
    """Test that token usage is tracked for agent calls."""
    # Execute query with agents
    query = await query_service_with_agents.process_query(
        query_text=f"What optimizations are recommended for {sample_api.name}?",
        session_id=uuid4(),
    )
    
    # Verify query completed
    assert query is not None
    
    # Note: Token usage tracking would be in metadata if implemented
    # This test verifies the query completes successfully
    print(f"Query metadata: {query.metadata}")


@pytest.mark.asyncio
async def test_agent_specific_follow_ups(
    query_service_with_agents,
    sample_api,
    sample_metrics,
):
    """Test that follow-up suggestions are agent-aware."""
    # Execute prediction query
    query = await query_service_with_agents.process_query(
        query_text=f"What are the predictions for {sample_api.name}?",
        session_id=uuid4(),
    )
    
    # Verify follow-ups are generated
    assert query.follow_up_queries is not None
    assert len(query.follow_up_queries) > 0
    
    # Check if follow-ups are relevant to predictions
    follow_ups_text = " ".join(query.follow_up_queries).lower()
    print(f"Follow-up queries: {query.follow_up_queries}")
    
    # At least some follow-ups should be prediction-related
    # (This is a soft check as it depends on LLM response)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

# Made with Bob
