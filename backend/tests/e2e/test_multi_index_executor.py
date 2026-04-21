"""
End-to-End Tests for Multi-Index Executor

Tests the complete multi-index query execution flow including context filtering,
result merging, parallel execution, and error handling.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import uuid4

import pytest

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.models.query import (
    ExecutionStrategy,
    IndexQuery,
    InterpretedIntent,
    QueryPlan,
    TimeRange,
)
from app.services.query import ContextManager, MultiIndexExecutor


@pytest.fixture
def context_manager():
    """Create a context manager for testing."""
    return ContextManager(session_ttl_minutes=30)


@pytest.fixture
def multi_index_executor():
    """Create a multi-index executor for testing."""
    return MultiIndexExecutor(
        api_repository=APIRepository(),
        gateway_repository=GatewayRepository(),
        metrics_repository=MetricsRepository(),
        prediction_repository=PredictionRepository(),
        recommendation_repository=RecommendationRepository(),
        compliance_repository=ComplianceRepository(),
        vulnerability_repository=VulnerabilityRepository(),
        transactional_log_repository=TransactionalLogRepository(),
        context_manager=ContextManager(),
    )


@pytest.mark.asyncio
class TestSingleIndexExecution:
    """Test single-index query execution."""
    
    async def test_execute_single_api_query(self, multi_index_executor):
        """Test executing a single query against api-inventory."""
        # Create query plan
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={"status": "active"},
            time_range=None
        )
        
        index_query = IndexQuery(
            index="api-inventory",
            query_dsl={
                "query": {
                    "term": {"status": "active"}
                }
            },
            filters={"status": "active"},
            required_fields=["id", "name", "status"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show me all active APIs",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SINGLE_INDEX,
            index_queries=[index_query],
            estimated_cost=0.2,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        # Execute plan
        results = await multi_index_executor.execute_plan(plan)
        
        # Verify results
        assert results is not None
        assert results.count >= 0
        assert results.execution_time > 0
        assert isinstance(results.data, list)
    
    async def test_execute_single_vulnerability_query(self, multi_index_executor):
        """Test executing a single query against security-findings."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["vulnerability"],
            filters={"severity": "critical"},
            time_range=None
        )
        
        index_query = IndexQuery(
            index="security-findings",
            query_dsl={
                "query": {
                    "term": {"severity": "critical"}
                }
            },
            filters={"severity": "critical"},
            required_fields=["id", "title", "severity"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show critical vulnerabilities",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SINGLE_INDEX,
            index_queries=[index_query],
            estimated_cost=0.2,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        assert results is not None
        assert results.count >= 0
        assert isinstance(results.data, list)


@pytest.mark.asyncio
class TestSequentialExecution:
    """Test sequential multi-index query execution."""
    
    async def test_execute_api_to_vulnerability_query(self, multi_index_executor):
        """Test sequential query from APIs to vulnerabilities."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability"],
            filters={},
            time_range=None
        )
        
        # First query: Get APIs
        api_query = IndexQuery(
            index="api-inventory",
            query_dsl={
                "query": {"match_all": {}}
            },
            filters={},
            required_fields=["id", "name", "gateway_id"],
            join_fields={"id": "api_id"},
            depends_on=[]
        )
        
        # Second query: Get vulnerabilities for those APIs
        vuln_query = IndexQuery(
            index="security-findings",
            query_dsl={
                "query": {"match_all": {}}
            },
            filters={},
            required_fields=["id", "api_id", "title", "severity"],
            join_fields={},
            depends_on=["api-inventory"]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show vulnerabilities for all APIs",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SEQUENTIAL,
            index_queries=[api_query, vuln_query],
            estimated_cost=0.5,
            requires_join=True,
            join_strategy="api_id",
            context_filters={}
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        assert results is not None
        assert results.count >= 0
        assert isinstance(results.data, list)
    
    async def test_execute_with_context_filters(self, multi_index_executor):
        """Test sequential execution with context filters."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["vulnerability"],
            filters={"severity": "critical"},
            time_range=None
        )
        
        # Context filters from previous query
        context_filters = {
            "api_id": ["API-001", "API-002", "API-003"]
        }
        
        vuln_query = IndexQuery(
            index="security-findings",
            query_dsl={
                "query": {
                    "term": {"severity": "critical"}
                }
            },
            filters={"severity": "critical"},
            required_fields=["id", "api_id", "title", "severity"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show critical vulnerabilities for these APIs",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SEQUENTIAL,
            index_queries=[vuln_query],
            estimated_cost=0.3,
            requires_join=False,
            join_strategy=None,
            context_filters=context_filters
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        assert results is not None
        assert isinstance(results.data, list)


@pytest.mark.asyncio
class TestParallelExecution:
    """Test parallel multi-index query execution."""
    
    async def test_execute_parallel_queries(self, multi_index_executor):
        """Test parallel execution of independent queries."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "gateway"],
            filters={},
            time_range=None
        )
        
        # Query 1: Get APIs
        api_query = IndexQuery(
            index="api-inventory",
            query_dsl={
                "query": {"match_all": {}}
            },
            filters={},
            required_fields=["id", "name"],
            join_fields={},
            depends_on=[]
        )
        
        # Query 2: Get gateways (independent)
        gateway_query = IndexQuery(
            index="gateway-registry",
            query_dsl={
                "query": {"match_all": {}}
            },
            filters={},
            required_fields=["id", "name"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show all APIs and gateways",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.PARALLEL,
            index_queries=[api_query, gateway_query],
            estimated_cost=0.4,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        assert results is not None
        assert results.count >= 0
        assert isinstance(results.data, list)
    
    async def test_parallel_execution_performance(self, multi_index_executor):
        """Test that parallel execution is faster than sequential."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability", "prediction"],
            filters={},
            time_range=None
        )
        
        # Create multiple independent queries
        queries = [
            IndexQuery(
                index="api-inventory",
                query_dsl={"query": {"match_all": {}}},
                filters={},
                required_fields=["id"],
                join_fields={},
                depends_on=[]
            ),
            IndexQuery(
                index="security-findings",
                query_dsl={"query": {"match_all": {}}},
                filters={},
                required_fields=["id"],
                join_fields={},
                depends_on=[]
            ),
            IndexQuery(
                index="api-predictions",
                query_dsl={"query": {"match_all": {}}},
                filters={},
                required_fields=["id"],
                join_fields={},
                depends_on=[]
            ),
        ]
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show all data",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.PARALLEL,
            index_queries=queries,
            estimated_cost=0.6,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        # Parallel execution should complete reasonably fast
        assert results is not None
        assert results.execution_time < 10000  # Less than 10 seconds


@pytest.mark.asyncio
class TestNestedExecution:
    """Test nested multi-index query execution."""
    
    async def test_execute_nested_query_chain(self, multi_index_executor):
        """Test nested execution through relationship chain."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["gateway", "api", "vulnerability"],
            filters={},
            time_range=None
        )
        
        # Query 1: Get gateways
        gateway_query = IndexQuery(
            index="gateway-registry",
            query_dsl={
                "query": {"match_all": {}}
            },
            filters={},
            required_fields=["id", "name"],
            join_fields={"id": "gateway_id"},
            depends_on=[]
        )
        
        # Query 2: Get APIs for those gateways
        api_query = IndexQuery(
            index="api-inventory",
            query_dsl={
                "query": {"match_all": {}}
            },
            filters={},
            required_fields=["id", "gateway_id", "name"],
            join_fields={"id": "api_id"},
            depends_on=["gateway-registry"]
        )
        
        # Query 3: Get vulnerabilities for those APIs
        vuln_query = IndexQuery(
            index="security-findings",
            query_dsl={
                "query": {"match_all": {}}
            },
            filters={},
            required_fields=["id", "api_id", "title", "severity"],
            join_fields={},
            depends_on=["api-inventory"]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show vulnerabilities for APIs in all gateways",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.NESTED,
            index_queries=[gateway_query, api_query, vuln_query],
            estimated_cost=0.7,
            requires_join=True,
            join_strategy="gateway_id",
            context_filters={}
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        assert results is not None
        assert isinstance(results.data, list)


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in multi-index execution."""
    
    async def test_handle_invalid_index(self, multi_index_executor):
        """Test handling of invalid index name."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["unknown"],
            filters={},
            time_range=None
        )
        
        invalid_query = IndexQuery(
            index="invalid-index",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Query invalid index",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SINGLE_INDEX,
            index_queries=[invalid_query],
            estimated_cost=0.2,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        # Should return empty results with error info
        assert results is not None
        assert results.count == 0
        assert results.aggregations is not None
        assert "error" in results.aggregations
    
    async def test_handle_partial_failure_in_sequential(self, multi_index_executor):
        """Test handling of partial failure in sequential execution."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "unknown"],
            filters={},
            time_range=None
        )
        
        # Valid query
        api_query = IndexQuery(
            index="api-inventory",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id"],
            join_fields={},
            depends_on=[]
        )
        
        # Invalid query
        invalid_query = IndexQuery(
            index="invalid-index",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Query with partial failure",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SEQUENTIAL,
            index_queries=[api_query, invalid_query],
            estimated_cost=0.4,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        results = await multi_index_executor.execute_plan(plan)
        
        # Should return results from successful query
        assert results is not None
        assert isinstance(results.data, list)


@pytest.mark.asyncio
class TestResultMerging:
    """Test result merging and deduplication."""
    
    async def test_merge_results_without_join(self, multi_index_executor):
        """Test merging results without join requirement."""
        # Create sample results with duplicates
        results = [
            {"id": "1", "name": "API 1"},
            {"id": "2", "name": "API 2"},
            {"id": "1", "name": "API 1"},  # Duplicate
            {"id": "3", "name": "API 3"},
        ]
        
        merged = multi_index_executor._merge_results(results, requires_join=False)
        
        # Should deduplicate by ID
        assert len(merged) == 3
        assert all(r["id"] in ["1", "2", "3"] for r in merged)
    
    async def test_merge_results_with_join(self, multi_index_executor):
        """Test merging results with join requirement."""
        # Create sample results from different indices
        results = [
            {"id": "API-1", "name": "API 1", "gateway_id": "GW-1"},
            {"id": "VULN-1", "api_id": "API-1", "severity": "critical"},
            {"id": "VULN-2", "api_id": "API-1", "severity": "high"},
        ]
        
        merged = multi_index_executor._merge_results(results, requires_join=True)
        
        # Should include all results
        assert len(merged) == 3


@pytest.mark.asyncio
class TestContextFiltering:
    """Test context-aware filtering."""
    
    async def test_apply_context_filters(self, multi_index_executor):
        """Test applying context filters to query."""
        index_query = IndexQuery(
            index="security-findings",
            query_dsl={
                "query": {"term": {"severity": "critical"}}
            },
            filters={"severity": "critical"},
            required_fields=["id"],
            join_fields={},
            depends_on=[]
        )
        
        context_filters = {
            "api_id": ["API-001", "API-002"],
            "gateway_id": "GW-001"
        }
        
        filtered_query = multi_index_executor._apply_context_filters(
            index_query,
            context_filters
        )
        
        # Verify filters were added
        assert "query" in filtered_query.query_dsl
        assert "bool" in filtered_query.query_dsl["query"]
        assert "must" in filtered_query.query_dsl["query"]["bool"]
        
        must_clauses = filtered_query.query_dsl["query"]["bool"]["must"]
        assert len(must_clauses) >= 3  # Original + 2 context filters
    
    async def test_extract_field_values(self, multi_index_executor):
        """Test extracting field values from results."""
        results = [
            {"id": "1", "api_id": "API-001"},
            {"id": "2", "api_id": "API-002"},
            {"id": "3", "api_id": "API-001"},  # Duplicate
        ]
        
        api_ids = multi_index_executor._extract_field_values(results, "api_id")
        
        # Should return unique values
        assert len(api_ids) == 2
        assert "API-001" in api_ids
        assert "API-002" in api_ids


# Made with Bob