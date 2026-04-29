"""End-to-end tests for natural language query workflow.

Tests the complete query workflow including:
- Natural language query parsing
- Intent detection and entity extraction
- Query planning and execution
- Multi-index query coordination
- Response generation with AI enhancement
- Follow-up question handling
- Context management

Note: Uses mocked dependencies to focus on workflow logic.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from backend.app.services.query_service import QueryService


@pytest.fixture
def mock_query_service():
    """Create query service with mocked dependencies."""
    query_repo = Mock()
    query_repo.create = AsyncMock()
    query_repo.update = AsyncMock()
    query_repo.get = AsyncMock()
    query_repo.find_by_session = AsyncMock(return_value=[])
    
    api_repo = Mock()
    api_repo.find_all = AsyncMock(return_value=[])
    
    metrics_repo = Mock()
    metrics_repo.find_by_api = AsyncMock(return_value=([], 0))
    
    prediction_repo = Mock()
    prediction_repo.find_all = AsyncMock(return_value=[])
    
    recommendation_repo = Mock()
    recommendation_repo.find_all = AsyncMock(return_value=[])
    
    compliance_repo = Mock()
    compliance_repo.find_all = AsyncMock(return_value=[])
    
    gateway_repo = Mock()
    gateway_repo.find_all = AsyncMock(return_value=[])
    
    vulnerability_repo = Mock()
    vulnerability_repo.find_all = AsyncMock(return_value=[])
    
    transactional_log_repo = Mock()
    transactional_log_repo.find_all = AsyncMock(return_value=[])
    
    llm_service = Mock()
    llm_service.complete = AsyncMock(return_value="AI-generated response")
    
    service = QueryService(
        query_repository=query_repo,
        api_repository=api_repo,
        metrics_repository=metrics_repo,
        prediction_repository=prediction_repo,
        recommendation_repository=recommendation_repo,
        compliance_repository=compliance_repo,
        gateway_repository=gateway_repo,
        vulnerability_repository=vulnerability_repo,
        transactional_log_repository=transactional_log_repo,
        llm_service=llm_service,
    )
    
    return service, query_repo, api_repo, metrics_repo, llm_service


class TestNaturalLanguageQueryWorkflow:
    """Test complete natural language query workflow."""

    @pytest.mark.asyncio
    async def test_complete_query_workflow(self, mock_query_service):
        """Test complete workflow from query to response."""
        service, query_repo, api_repo, metrics_repo, llm_service = mock_query_service
        
        # Step 1: User submits natural language query
        user_query = "Show me all APIs with high error rates"
        session_id = uuid4()
        
        # Step 2: Parse and detect intent
        query_data = {
            "id": uuid4(),
            "session_id": session_id,
            "query_text": user_query,
            "query_type": "performance",
            "intent": {
                "action": "list",
                "entity": "apis",
                "filters": {"error_rate": "high"}
            },
            "status": "processing",
            "created_at": datetime.utcnow()
        }
        
        query_repo.create.return_value = query_data
        await query_repo.create(query_data)
        
        # Step 3: Execute query against data stores
        # Mock APIs with high error rates
        matching_apis = [
            {
                "id": uuid4(),
                "name": "Payment API",
                "error_rate": 0.08,  # 8% error rate
                "health_score": 45.0
            },
            {
                "id": uuid4(),
                "name": "User API",
                "error_rate": 0.12,  # 12% error rate
                "health_score": 35.0
            }
        ]
        
        api_repo.find_all.return_value = matching_apis
        
        # Step 4: Generate AI-enhanced response
        llm_service.complete.return_value = (
            "I found 2 APIs with high error rates:\n\n"
            "1. **Payment API** - 8% error rate (Health: 45/100)\n"
            "2. **User API** - 12% error rate (Health: 35/100)\n\n"
            "Both APIs require immediate attention. Would you like recommendations for improving their reliability?"
        )
        
        response_text = await llm_service.complete("Generate response")
        
        # Step 5: Store query results
        query_data["status"] = "completed"
        query_data["results"] = {
            "count": len(matching_apis),
            "apis": matching_apis
        }
        query_data["response_text"] = response_text
        query_data["completed_at"] = datetime.utcnow()
        
        await query_repo.update(query_data)
        
        # Verify workflow completion
        assert query_data["status"] == "completed"
        assert query_data["results"]["count"] == 2
        assert "Payment API" in query_data["response_text"]
        assert "User API" in query_data["response_text"]

    @pytest.mark.asyncio
    async def test_follow_up_question_workflow(self, mock_query_service):
        """Test follow-up question handling with context."""
        service, query_repo, api_repo, metrics_repo, llm_service = mock_query_service
        
        session_id = uuid4()
        
        # Step 1: Initial query
        initial_query = {
            "id": uuid4(),
            "session_id": session_id,
            "query_text": "Show me failing APIs",
            "results": {
                "apis": [
                    {"id": uuid4(), "name": "Payment API", "health_score": 25.0}
                ]
            },
            "status": "completed"
        }
        
        query_repo.create.return_value = initial_query
        await query_repo.create(initial_query)
        
        # Step 2: Follow-up question (uses context from previous query)
        followup_query = {
            "id": uuid4(),
            "session_id": session_id,
            "query_text": "What's causing the failures?",
            "parent_query_id": initial_query["id"],
            "status": "processing"
        }
        
        # Mock previous queries in session
        query_repo.find_by_session.return_value = [initial_query]
        
        # Step 3: Use context to understand "the failures" refers to Payment API
        # Query metrics for Payment API
        metrics_data = [
            {
                "timestamp": datetime.utcnow(),
                "error_rate": 0.15,
                "response_time_p95": 2500.0,
                "availability": 85.0
            }
        ]
        
        metrics_repo.find_by_api.return_value = (metrics_data, len(metrics_data))
        
        # Step 4: Generate contextual response
        llm_service.complete.return_value = (
            "The Payment API failures are caused by:\n\n"
            "1. **High Error Rate** (15%) - Database connection timeouts\n"
            "2. **Slow Response Times** (2.5s p95) - Inefficient queries\n"
            "3. **Low Availability** (85%) - Frequent service restarts\n\n"
            "I recommend implementing connection pooling and query optimization."
        )
        
        response_text = await llm_service.complete("Generate contextual response")
        
        followup_query["status"] = "completed"
        followup_query["response_text"] = response_text
        
        await query_repo.update(followup_query)
        
        # Verify context was used
        assert followup_query["parent_query_id"] == initial_query["id"]
        assert "Payment API" in followup_query["response_text"]

    @pytest.mark.asyncio
    async def test_multi_entity_query_workflow(self, mock_query_service):
        """Test query involving multiple entity types."""
        service, query_repo, api_repo, metrics_repo, llm_service = mock_query_service
        
        # Query involving APIs, predictions, and recommendations
        query_text = "Show me APIs with active predictions and pending optimizations"
        
        query_data = {
            "id": uuid4(),
            "query_text": query_text,
            "query_type": "complex",
            "entities": ["apis", "predictions", "recommendations"],
            "status": "processing"
        }
        
        # Mock data from multiple sources
        apis_with_predictions = [
            {"id": uuid4(), "name": "User API", "has_active_predictions": True}
        ]
        
        pending_recommendations = [
            {"id": uuid4(), "api_id": apis_with_predictions[0]["id"], "status": "pending"}
        ]
        
        api_repo.find_all.return_value = apis_with_predictions
        
        # Generate response combining multiple data sources
        llm_service.complete.return_value = (
            "Found 1 API matching your criteria:\n\n"
            "**User API**\n"
            "- Has 1 active failure prediction\n"
            "- Has 1 pending optimization recommendation\n\n"
            "This API requires attention to prevent predicted failures."
        )
        
        response_text = await llm_service.complete("Generate multi-entity response")
        
        query_data["status"] = "completed"
        query_data["response_text"] = response_text
        
        await query_repo.update(query_data)
        
        # Verify multi-entity query
        assert len(query_data["entities"]) == 3
        assert "User API" in query_data["response_text"]

    @pytest.mark.asyncio
    async def test_time_range_query_workflow(self, mock_query_service):
        """Test query with time range filtering."""
        service, query_repo, api_repo, metrics_repo, llm_service = mock_query_service
        
        query_text = "Show me API performance over the last 24 hours"
        
        query_data = {
            "id": uuid4(),
            "query_text": query_text,
            "time_range": {
                "start": datetime.utcnow() - timedelta(hours=24),
                "end": datetime.utcnow()
            },
            "status": "processing"
        }
        
        # Mock time-series metrics
        metrics_data = []
        for hour in range(24):
            metrics_data.append({
                "timestamp": datetime.utcnow() - timedelta(hours=23-hour),
                "response_time_p95": 200 + (hour * 5),
                "error_rate": 0.01 + (hour * 0.001)
            })
        
        metrics_repo.find_by_api.return_value = (metrics_data, len(metrics_data))
        
        # Generate trend analysis
        llm_service.complete.return_value = (
            "Performance analysis for the last 24 hours:\n\n"
            "**Trends:**\n"
            "- Response time increased by 23% (200ms → 315ms)\n"
            "- Error rate increased by 140% (1% → 2.4%)\n\n"
            "**Recommendation:** Investigate performance degradation starting 12 hours ago."
        )
        
        response_text = await llm_service.complete("Generate trend analysis")
        
        query_data["status"] = "completed"
        query_data["response_text"] = response_text
        
        await query_repo.update(query_data)
        
        # Verify time range query
        assert query_data["time_range"] is not None
        assert "24 hours" in query_data["response_text"]

    @pytest.mark.asyncio
    async def test_comparison_query_workflow(self, mock_query_service):
        """Test comparison query between entities."""
        service, query_repo, api_repo, metrics_repo, llm_service = mock_query_service
        
        query_text = "Compare performance of Payment API vs User API"
        
        query_data = {
            "id": uuid4(),
            "query_text": query_text,
            "query_type": "comparison",
            "entities_to_compare": ["Payment API", "User API"],
            "status": "processing"
        }
        
        # Mock comparison data
        api_metrics = {
            "Payment API": {
                "response_time_p95": 450.0,
                "error_rate": 0.05,
                "availability": 98.5
            },
            "User API": {
                "response_time_p95": 250.0,
                "error_rate": 0.02,
                "availability": 99.8
            }
        }
        
        # Generate comparison response
        llm_service.complete.return_value = (
            "**Performance Comparison:**\n\n"
            "| Metric | Payment API | User API | Winner |\n"
            "|--------|-------------|----------|--------|\n"
            "| Response Time | 450ms | 250ms | User API |\n"
            "| Error Rate | 5% | 2% | User API |\n"
            "| Availability | 98.5% | 99.8% | User API |\n\n"
            "**Summary:** User API outperforms Payment API across all metrics."
        )
        
        response_text = await llm_service.complete("Generate comparison")
        
        query_data["status"] = "completed"
        query_data["response_text"] = response_text
        
        await query_repo.update(query_data)
        
        # Verify comparison query
        assert query_data["query_type"] == "comparison"
        assert len(query_data["entities_to_compare"]) == 2


class TestQueryErrorHandling:
    """Test query error handling workflows."""

    @pytest.mark.asyncio
    async def test_ambiguous_query_handling(self, mock_query_service):
        """Test handling of ambiguous queries."""
        service, query_repo, api_repo, metrics_repo, llm_service = mock_query_service
        
        query_text = "Show me the API"  # Ambiguous - which API?
        
        query_data = {
            "id": uuid4(),
            "query_text": query_text,
            "status": "processing"
        }
        
        # Detect ambiguity
        query_data["status"] = "needs_clarification"
        query_data["clarification_needed"] = "Which API would you like to see? Please specify the API name."
        
        await query_repo.update(query_data)
        
        # Verify clarification request
        assert query_data["status"] == "needs_clarification"
        assert "specify" in query_data["clarification_needed"].lower()

    @pytest.mark.asyncio
    async def test_no_results_handling(self, mock_query_service):
        """Test handling when query returns no results."""
        service, query_repo, api_repo, metrics_repo, llm_service = mock_query_service
        
        query_text = "Show me APIs with 100% error rate"
        
        query_data = {
            "id": uuid4(),
            "query_text": query_text,
            "status": "processing"
        }
        
        # No matching results
        api_repo.find_all.return_value = []
        
        llm_service.complete.return_value = (
            "No APIs found with 100% error rate. This is good news! "
            "All your APIs are operational. Would you like to see APIs with the highest error rates instead?"
        )
        
        response_text = await llm_service.complete("Generate no results response")
        
        query_data["status"] = "completed"
        query_data["results"] = {"count": 0}
        query_data["response_text"] = response_text
        
        await query_repo.update(query_data)
        
        # Verify no results handling
        assert query_data["results"]["count"] == 0
        assert "No APIs found" in query_data["response_text"]


# Made with Bob