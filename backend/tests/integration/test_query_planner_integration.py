"""
Integration tests for QueryPlanner

Tests query planning with real schema registry, relationship graph,
and context manager integration.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.query import InterpretedIntent, TimeRange, ExecutionStrategy
from app.services.query import (
    QueryPlanner,
    SchemaRegistry,
    RelationshipGraph,
    ContextManager,
)
from app.db.client import get_opensearch_client


@pytest.fixture
async def opensearch_client():
    """Get OpenSearch client."""
    client = get_opensearch_client()
    yield client
    # Cleanup if needed


@pytest.fixture
async def schema_registry(opensearch_client):
    """Create schema registry with real client."""
    registry = SchemaRegistry(opensearch_client)
    await registry.load_schemas()
    return registry


@pytest.fixture
def relationship_graph():
    """Create relationship graph."""
    return RelationshipGraph()


@pytest.fixture
def context_manager():
    """Create context manager."""
    return ContextManager(session_ttl_minutes=30)


@pytest.fixture
def query_planner(schema_registry, relationship_graph, context_manager):
    """Create query planner with all components."""
    return QueryPlanner(schema_registry, relationship_graph, context_manager)


class TestQueryPlannerIntegration:
    """Integration tests for QueryPlanner."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_single_index_plan(self, query_planner):
        """Test complete planning flow for single index."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={"status": "active"},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show me all active APIs",
            intent=intent
        )
        
        # Validate plan
        is_valid, errors = query_planner.validate_plan(plan)
        assert is_valid, f"Plan validation failed: {errors}"
        
        # Check plan structure
        assert plan.strategy == ExecutionStrategy.SINGLE_INDEX
        assert len(plan.index_queries) == 1
        assert plan.index_queries[0].index == "api-inventory"
    
    @pytest.mark.asyncio
    async def test_end_to_end_multi_index_plan(self, query_planner):
        """Test complete planning flow for multi-index query."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability"],
            filters={"severity": "critical"},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show APIs with critical vulnerabilities",
            intent=intent
        )
        
        # Validate plan
        is_valid, errors = query_planner.validate_plan(plan)
        assert is_valid, f"Plan validation failed: {errors}"
        
        # Check multi-index characteristics
        assert len(plan.index_queries) >= 2
        assert plan.requires_join
        
        # Verify indices are correct
        indices = [q.index for q in plan.index_queries]
        assert "api-inventory" in indices
        assert "security-findings" in indices
    
    @pytest.mark.asyncio
    async def test_context_propagation(self, query_planner, context_manager):
        """Test context propagation across queries."""
        session_id = uuid4()
        
        # First query - establish context
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Show me APIs",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001", "API-002", "API-003"]},
            result_count=3
        )
        
        # Second query - should use context
        intent = InterpretedIntent(
            action="list",
            entities=["vulnerability"],
            filters={"severity": "high"},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show vulnerabilities for these APIs",
            intent=intent
        )
        
        # Verify context was used
        assert len(plan.context_filters) > 0
        assert "api_id" in plan.context_filters
    
    @pytest.mark.asyncio
    async def test_relationship_path_finding(self, query_planner, relationship_graph):
        """Test that relationship paths are correctly found."""
        session_id = uuid4()
        
        # Query spanning multiple related indices
        intent = InterpretedIntent(
            action="list",
            entities=["gateway", "api", "vulnerability"],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show gateways, their APIs, and vulnerabilities",
            intent=intent
        )
        
        # Should find path through relationships
        assert len(plan.index_queries) >= 2
        
        # Verify dependencies are set correctly
        for query in plan.index_queries:
            for dep in query.depends_on:
                # Dependency should exist in plan
                assert any(q.index == dep for q in plan.index_queries)
    
    @pytest.mark.asyncio
    async def test_time_range_with_real_schema(self, query_planner):
        """Test time range filtering with real schema."""
        session_id = uuid4()
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        
        intent = InterpretedIntent(
            action="list",
            entities=["metric"],
            filters={},
            time_range=TimeRange(start=start, end=end)
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show metrics from last week",
            intent=intent
        )
        
        # Validate plan
        is_valid, errors = query_planner.validate_plan(plan)
        assert is_valid, f"Plan validation failed: {errors}"
        
        # Check time range is in query
        query_dsl = plan.index_queries[0].query_dsl
        assert "query" in query_dsl
        assert "bool" in query_dsl["query"]
    
    @pytest.mark.asyncio
    async def test_complex_multi_entity_query(self, query_planner):
        """Test complex query with multiple entities and filters."""
        session_id = uuid4()
        
        intent = InterpretedIntent(
            action="analyze",
            entities=["api", "vulnerability", "recommendation"],
            filters={
                "severity": "critical",
                "status": "open"
            },
            time_range=TimeRange(
                start=datetime.utcnow() - timedelta(days=30),
                end=datetime.utcnow()
            )
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Analyze APIs with critical open vulnerabilities and recommendations",
            intent=intent
        )
        
        # Validate plan
        is_valid, errors = query_planner.validate_plan(plan)
        assert is_valid, f"Plan validation failed: {errors}"
        
        # Should have multiple queries
        assert len(plan.index_queries) >= 2
        
        # Cost should be reasonable
        assert 0 <= plan.estimated_cost <= 1
    
    @pytest.mark.asyncio
    async def test_schema_field_validation(self, query_planner, schema_registry):
        """Test that fields are validated against schema."""
        session_id = uuid4()
        
        # Query with mix of valid and invalid fields
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={
                "status": "active",  # Valid
                "nonexistent_field": "value"  # Invalid
            },
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show APIs with filters",
            intent=intent
        )
        
        # Plan should be created (invalid fields logged but not blocking)
        assert plan is not None
        
        # Valid field should be in query
        query_dsl = plan.index_queries[0].query_dsl
        must_clauses = query_dsl["query"]["bool"]["must"]
        
        # Check valid filter is present
        has_status_filter = any(
            "term" in c and "status" in c.get("term", {})
            for c in must_clauses
        )
        assert has_status_filter


class TestQueryPlannerPerformance:
    """Performance tests for QueryPlanner."""
    
    @pytest.mark.asyncio
    async def test_planning_performance(self, query_planner):
        """Test that planning completes in reasonable time."""
        import time
        
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability", "metric"],
            filters={"severity": "critical"},
            time_range=None
        )
        
        start = time.time()
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Complex multi-index query",
            intent=intent
        )
        elapsed = time.time() - start
        
        # Planning should complete quickly (< 1 second)
        assert elapsed < 1.0, f"Planning took {elapsed:.2f}s, expected < 1s"
        assert plan is not None
    
    @pytest.mark.asyncio
    async def test_multiple_plans_in_session(self, query_planner, context_manager):
        """Test creating multiple plans in same session."""
        session_id = uuid4()
        
        queries = [
            ("Show APIs", ["api"]),
            ("Show vulnerabilities", ["vulnerability"]),
            ("Show metrics", ["metric"]),
            ("Show recommendations", ["recommendation"]),
        ]
        
        plans = []
        for query_text, entities in queries:
            intent = InterpretedIntent(
                action="list",
                entities=entities,
                filters={},
                time_range=None
            )
            
            plan = query_planner.create_plan(
                session_id=session_id,
                query_text=query_text,
                intent=intent
            )
            plans.append(plan)
        
        # All plans should be valid
        assert len(plans) == len(queries)
        for plan in plans:
            is_valid, errors = query_planner.validate_plan(plan)
            assert is_valid, f"Plan validation failed: {errors}"


# Made with Bob