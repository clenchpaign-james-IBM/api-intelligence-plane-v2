"""
Unit tests for QueryPlanner

Tests query planning, index selection, relationship resolution,
and execution optimization.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.query import (
    ExecutionStrategy,
    InterpretedIntent,
    TimeRange,
)
from app.services.query import (
    QueryPlanner,
    SchemaRegistry,
    RelationshipGraph,
    ContextManager,
)


class MockOpenSearchClient:
    """Mock OpenSearch client for testing."""
    
    def __init__(self):
        self.indices = MockIndices()


class MockIndices:
    """Mock indices interface."""
    
    def get_mapping(self, index):
        """Return mock mappings."""
        mappings = {
            "api-inventory": {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "gateway_id": {"type": "keyword"},
                        "name": {"type": "text"},
                        "status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                    }
                }
            },
            "security-findings": {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "api_id": {"type": "keyword"},
                        "gateway_id": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "detected_at": {"type": "date"},
                    }
                }
            },
            "api-metrics-5m": {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "api_id": {"type": "keyword"},
                        "gateway_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "request_count": {"type": "long"},
                        "error_rate": {"type": "float"},
                    }
                }
            },
        }
        
        # Return matching mappings
        result = {}
        for idx, mapping in mappings.items():
            if idx.startswith(index.replace("*", "")):
                result[idx] = mapping
        
        return result if result else {index: {"mappings": {"properties": {}}}}


@pytest.fixture
def mock_client():
    """Create mock OpenSearch client."""
    return MockOpenSearchClient()


@pytest.fixture
async def schema_registry(mock_client):
    """Create schema registry with mock client."""
    registry = SchemaRegistry(mock_client)
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
    """Create query planner."""
    return QueryPlanner(schema_registry, relationship_graph, context_manager)


class TestQueryPlanner:
    """Test QueryPlanner functionality."""
    
    def test_single_index_query(self, query_planner):
        """Test planning a single-index query."""
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
        
        assert plan.strategy == ExecutionStrategy.SINGLE_INDEX
        assert len(plan.index_queries) == 1
        assert plan.index_queries[0].index == "api-inventory"
        assert not plan.requires_join
        assert plan.join_strategy is None
        assert "status" in plan.index_queries[0].filters
    
    def test_multi_index_query_with_relationship(self, query_planner):
        """Test planning a multi-index query with relationships."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability"],
            filters={"severity": "critical"},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show me APIs with critical vulnerabilities",
            intent=intent
        )
        
        assert plan.strategy in [ExecutionStrategy.SEQUENTIAL, ExecutionStrategy.NESTED]
        assert len(plan.index_queries) >= 2
        assert plan.requires_join
        assert plan.join_strategy is not None
        
        # Check that indices are included
        indices = [q.index for q in plan.index_queries]
        assert "api-inventory" in indices
        assert "security-findings" in indices
    
    def test_time_range_filter(self, query_planner):
        """Test query with time range filter."""
        session_id = uuid4()
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()
        
        intent = InterpretedIntent(
            action="list",
            entities=["vulnerability"],
            filters={"severity": "high"},
            time_range=TimeRange(start=start, end=end)
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show high severity vulnerabilities in the last week",
            intent=intent
        )
        
        assert len(plan.index_queries) == 1
        query_dsl = plan.index_queries[0].query_dsl
        
        # Check that time range is in the query
        assert "query" in query_dsl
        assert "bool" in query_dsl["query"]
        must_clauses = query_dsl["query"]["bool"]["must"]
        
        # Find range clause
        range_clause = next((c for c in must_clauses if "range" in c), None)
        assert range_clause is not None
    
    def test_context_filters(self, query_planner, context_manager):
        """Test query with context filters from session."""
        session_id = uuid4()
        
        # Store previous query context
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Show me APIs",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001", "API-002"]},
            result_count=2
        )
        
        # Create new query that should use context
        intent = InterpretedIntent(
            action="list",
            entities=["vulnerability"],
            filters={"severity": "critical"},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show vulnerabilities for these APIs",
            intent=intent
        )
        
        # Check that context filters are applied
        assert len(plan.context_filters) > 0
    
    def test_execution_order_optimization(self, query_planner):
        """Test that queries are ordered by dependencies."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability"],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show APIs and their vulnerabilities",
            intent=intent
        )
        
        # Check that dependent queries come after their dependencies
        for i, query in enumerate(plan.index_queries):
            for dep in query.depends_on:
                # Find the dependency
                dep_indices = [j for j, q in enumerate(plan.index_queries) if q.index == dep]
                if dep_indices:
                    assert dep_indices[0] < i, f"Dependency {dep} should come before {query.index}"
    
    def test_cost_estimation(self, query_planner):
        """Test execution cost estimation."""
        session_id = uuid4()
        
        # Simple single-index query should have low cost
        simple_intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={"status": "active"},
            time_range=None
        )
        
        simple_plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show active APIs",
            intent=simple_intent
        )
        
        # Complex multi-index query should have higher cost
        complex_intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability", "metric"],
            filters={},
            time_range=None
        )
        
        complex_plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show APIs with vulnerabilities and metrics",
            intent=complex_intent
        )
        
        assert simple_plan.estimated_cost < complex_plan.estimated_cost
    
    def test_parallel_strategy_selection(self, query_planner):
        """Test that parallel strategy is selected for independent queries."""
        session_id = uuid4()
        
        # Query with entities that don't have direct relationships
        intent = InterpretedIntent(
            action="list",
            entities=["gateway", "prediction"],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show gateways and predictions",
            intent=intent
        )
        
        # Should use parallel or sequential strategy
        assert plan.strategy in [ExecutionStrategy.PARALLEL, ExecutionStrategy.SEQUENTIAL]
    
    def test_required_fields_selection(self, query_planner):
        """Test that required fields are correctly selected."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show APIs",
            intent=intent
        )
        
        required_fields = plan.index_queries[0].required_fields
        
        # Should include base fields
        assert "id" in required_fields
        
        # Should include API-specific fields
        assert "name" in required_fields
        assert "base_path" in required_fields
        assert "status" in required_fields
    
    def test_plan_validation_success(self, query_planner):
        """Test validation of a valid query plan."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={"status": "active"},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show active APIs",
            intent=intent
        )
        
        is_valid, errors = query_planner.validate_plan(plan)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_index_selection_default(self, query_planner):
        """Test that api-inventory is default when no entities specified."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=[],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show me everything",
            intent=intent
        )
        
        assert len(plan.index_queries) == 1
        assert plan.index_queries[0].index == "api-inventory"
    
    def test_join_fields_resolution(self, query_planner):
        """Test that join fields are correctly resolved."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability"],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show APIs and vulnerabilities",
            intent=intent
        )
        
        if plan.requires_join:
            # Find query with join fields
            queries_with_joins = [q for q in plan.index_queries if q.join_fields]
            assert len(queries_with_joins) > 0
            
            # Check join fields are valid
            for query in queries_with_joins:
                assert len(query.join_fields) > 0
    
    def test_filter_validation(self, query_planner):
        """Test that filters are validated against schema."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={
                "status": "active",  # Valid field
                "invalid_field": "value"  # Invalid field
            },
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show APIs with filters",
            intent=intent
        )
        
        # Valid filter should be in query DSL
        query_dsl = plan.index_queries[0].query_dsl
        must_clauses = query_dsl["query"]["bool"]["must"]
        
        # Check that valid filter is present
        status_filter = next((c for c in must_clauses if "term" in c and "status" in c["term"]), None)
        assert status_filter is not None
        
        # Invalid filter should be logged but not cause failure
        assert plan is not None


class TestQueryPlannerEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_intent(self, query_planner):
        """Test handling of empty intent."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=[],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="",
            intent=intent
        )
        
        # Should create a valid plan with defaults
        assert plan is not None
        assert len(plan.index_queries) > 0
    
    def test_unknown_entity_type(self, query_planner):
        """Test handling of unknown entity types."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["unknown_entity"],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show unknown entities",
            intent=intent
        )
        
        # Should fall back to default index
        assert plan is not None
        assert len(plan.index_queries) > 0
    
    def test_circular_dependencies(self, query_planner):
        """Test handling of potential circular dependencies."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "gateway", "metric"],
            filters={},
            time_range=None
        )
        
        plan = query_planner.create_plan(
            session_id=session_id,
            query_text="Show complex relationships",
            intent=intent
        )
        
        # Should create a valid plan without circular dependencies
        assert plan is not None
        
        # Verify no circular dependencies
        for i, query in enumerate(plan.index_queries):
            for dep in query.depends_on:
                dep_indices = [j for j, q in enumerate(plan.index_queries) if q.index == dep]
                if dep_indices:
                    assert all(j < i for j in dep_indices)


# Made with Bob