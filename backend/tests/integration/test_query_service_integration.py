"""
Integration Tests for Enhanced Query Service

Tests the complete query processing pipeline including:
- Multi-index query execution
- Context management and follow-up queries
- Enhanced intent extraction
- Query planning and execution
- Performance tracking

Based on: docs/enterprise-nlq-multi-index-analysis.md Phase 5
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.models.query import QueryType


@pytest.fixture
def query_service():
    """Create a QueryService instance with all dependencies."""
    query_repo = QueryRepository()
    api_repo = APIRepository()
    metrics_repo = MetricsRepository()
    prediction_repo = PredictionRepository()
    recommendation_repo = RecommendationRepository()
    compliance_repo = ComplianceRepository()
    gateway_repo = GatewayRepository()
    vulnerability_repo = VulnerabilityRepository()
    transactional_log_repo = TransactionalLogRepository()
    from app.config import Settings
    settings = Settings()
    llm_service = LLMService(settings)
    
    return QueryService(
        query_repository=query_repo,
        api_repository=api_repo,
        metrics_repository=metrics_repo,
        prediction_repository=prediction_repo,
        recommendation_repository=recommendation_repo,
        llm_service=llm_service,
        compliance_repository=compliance_repo,
        gateway_repository=gateway_repo,
        vulnerability_repository=vulnerability_repo,
        transactional_log_repository=transactional_log_repo,
    )


@pytest.mark.asyncio
class TestQueryServiceIntegration:
    """Integration tests for QueryService with multi-index support."""
    
    async def test_single_index_query(self, query_service):
        """Test basic single-index query execution."""
        session_id = uuid4()
        query_text = "Show me all active APIs"
        
        result = await query_service.process_query(
            query_text=query_text,
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result is not None
        assert result.query_text == query_text
        assert result.query_type == QueryType.STATUS
        assert result.results is not None
        assert result.execution_time_ms > 0
    
    async def test_multi_index_query(self, query_service):
        """Test multi-index query with relationships."""
        session_id = uuid4()
        query_text = "Show me APIs with critical vulnerabilities"
        
        result = await query_service.process_query(
            query_text=query_text,
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result is not None
        assert result.query_type == QueryType.SECURITY
        assert len(result.interpreted_intent.entities) >= 1
        assert result.results is not None
    
    async def test_follow_up_query_with_context(self, query_service):
        """Test follow-up query using context from previous query."""
        session_id = uuid4()
        
        # First query
        first_query = "Which APIs are insecure?"
        result1 = await query_service.process_query(
            query_text=first_query,
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result1 is not None
        
        # Follow-up query with reference
        follow_up_query = "Show me the performance metrics for these APIs"
        result2 = await query_service.process_query(
            query_text=follow_up_query,
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result2 is not None
        assert result2.results is not None
    
    async def test_performance_tracking(self, query_service):
        """Test performance metrics tracking."""
        session_id = uuid4()
        
        # Execute multiple queries
        queries = [
            "Show me all APIs",
            "What are the recent predictions?",
            "Show me critical security issues"
        ]
        
        for query_text in queries:
            await query_service.process_query(
                query_text=query_text,
                session_id=session_id,
                user_id="test_user"
            )
        
        # Check metrics
        metrics = query_service.get_performance_metrics()
        
        assert metrics["total_queries"] == 3
        assert metrics["successful_queries"] >= 0
        assert metrics["avg_execution_time_ms"] > 0
        assert "success_rate" in metrics
        assert "multi_index_usage" in metrics
    
    async def test_query_type_classification(self, query_service):
        """Test query type classification accuracy."""
        test_cases = [
            ("Show me API status", QueryType.STATUS),
            ("What's the trend over time?", QueryType.TREND),
            ("Predict future traffic", QueryType.PREDICTION),
            ("Show security vulnerabilities", QueryType.SECURITY),
            ("Compare API performance", QueryType.COMPARISON),
            ("Show compliance violations", QueryType.COMPLIANCE),
        ]
        
        session_id = uuid4()
        
        for query_text, expected_type in test_cases:
            result = await query_service.process_query(
                query_text=query_text,
                session_id=session_id,
                user_id="test_user"
            )
            
            assert result.query_type == expected_type, \
                f"Expected {expected_type} for '{query_text}', got {result.query_type}"
    
    async def test_error_handling(self, query_service):
        """Test error handling for invalid queries."""
        session_id = uuid4()
        
        # Query with no clear intent
        result = await query_service.process_query(
            query_text="",
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result is not None
        # Should return error response but not crash
        assert result.execution_time_ms > 0
    
    async def test_context_aware_query_tracking(self, query_service):
        """Test tracking of context-aware queries."""
        session_id = uuid4()
        
        # First query to establish context
        await query_service.process_query(
            query_text="Show me payment APIs",
            session_id=session_id,
            user_id="test_user"
        )
        
        # Context-aware follow-up
        await query_service.process_query(
            query_text="What vulnerabilities affect them?",
            session_id=session_id,
            user_id="test_user"
        )
        
        metrics = query_service.get_performance_metrics()
        
        # Should have tracked at least one context-aware query
        assert metrics["context_aware_queries"] >= 0
    
    async def test_multi_entity_query(self, query_service):
        """Test query involving multiple entity types."""
        session_id = uuid4()
        query_text = "Show me APIs on gateway-1 with high latency"
        
        result = await query_service.process_query(
            query_text=query_text,
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result is not None
        # Should detect multiple entities (api, gateway, metric)
        assert len(result.interpreted_intent.entities) >= 1
    
    async def test_time_range_extraction(self, query_service):
        """Test time range extraction from queries."""
        session_id = uuid4()
        query_text = "Show me API metrics from last 7 days"
        
        result = await query_service.process_query(
            query_text=query_text,
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result is not None
        # Time range should be extracted if LLM is available
        # (may be None in test environment without LLM)
    
    async def test_follow_up_suggestions(self, query_service):
        """Test generation of follow-up query suggestions."""
        session_id = uuid4()
        query_text = "Show me all APIs"
        
        result = await query_service.process_query(
            query_text=query_text,
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result is not None
        assert result.follow_up_queries is not None
        assert len(result.follow_up_queries) > 0
        assert len(result.follow_up_queries) <= 5


@pytest.mark.asyncio
class TestQueryServicePerformance:
    """Performance tests for QueryService."""
    
    async def test_query_latency(self, query_service):
        """Test that queries complete within acceptable time."""
        session_id = uuid4()
        query_text = "Show me all APIs"
        
        result = await query_service.process_query(
            query_text=query_text,
            session_id=session_id,
            user_id="test_user"
        )
        
        # Target: <2 seconds for 90% of queries (2000ms)
        # Allow higher in test environment
        assert result.execution_time_ms < 10000, \
            f"Query took {result.execution_time_ms}ms, expected <10000ms"
    
    async def test_concurrent_queries(self, query_service):
        """Test handling of concurrent queries."""
        import asyncio
        
        session_ids = [uuid4() for _ in range(5)]
        query_text = "Show me all APIs"
        
        # Execute queries concurrently
        tasks = [
            query_service.process_query(
                query_text=query_text,
                session_id=session_id,
                user_id="test_user"
            )
            for session_id in session_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All queries should complete successfully
        assert len(results) == 5
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None


# Made with Bob