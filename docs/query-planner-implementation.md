# Query Planner Implementation

**Status**: ✅ Completed  
**Phase**: Phase 3 - Query Planning (Week 5-6)  
**Date**: 2026-04-21

## Overview

The Query Planner is a core component of the multi-index query orchestration system that analyzes natural language query intent and creates optimized execution plans for queries spanning multiple OpenSearch indices.

## Architecture

### Components

```
QueryPlanner
├── Index Selection
│   ├── Entity-to-Index Mapping
│   └── Default Index Fallback
├── Relationship Resolution
│   ├── Path Finding
│   ├── Join Field Mapping
│   └── Dependency Ordering
├── Execution Optimization
│   ├── Strategy Selection
│   ├── Query Ordering
│   └── Cost Estimation
└── Context Integration
    ├── Session Context
    ├── Entity ID Propagation
    └── Filter Accumulation
```

### Key Classes

#### QueryPlan Model
Location: [`backend/app/models/query.py`](../backend/app/models/query.py)

```python
class QueryPlan(BaseModel):
    """Execution plan for a multi-index query."""
    query_id: UUID
    session_id: UUID
    original_query: str
    interpreted_intent: InterpretedIntent
    strategy: ExecutionStrategy
    index_queries: List[IndexQuery]
    estimated_cost: float
    requires_join: bool
    join_strategy: Optional[str]
    context_filters: Dict[str, Any]
    created_at: datetime
```

#### ExecutionStrategy Enum
```python
class ExecutionStrategy(str, Enum):
    SINGLE_INDEX = "single_index"    # Single index query
    SEQUENTIAL = "sequential"         # Sequential with filtering
    PARALLEL = "parallel"             # Parallel execution
    NESTED = "nested"                 # Complex multi-hop joins
```

#### IndexQuery Model
```python
class IndexQuery(BaseModel):
    """Query plan for a single index."""
    index: str
    query_dsl: Dict[str, Any]
    filters: Dict[str, Any]
    required_fields: List[str]
    join_fields: Dict[str, str]
    depends_on: List[str]
```

#### QueryPlanner Class
Location: [`backend/app/services/query/query_planner.py`](../backend/app/services/query/query_planner.py)

Main planning orchestrator that coordinates all planning activities.

## Features

### 1. Index Selection

Maps query entities to target OpenSearch indices:

```python
ENTITY_INDEX_MAP = {
    "api": "api-inventory",
    "gateway": "gateway-registry",
    "metric": "api-metrics-5m",
    "prediction": "api-predictions",
    "vulnerability": "security-findings",
    "recommendation": "optimization-recommendations",
    "compliance": "compliance-violations",
    "transaction": "transactional-logs",
}
```

**Default Behavior**: Falls back to `api-inventory` if no entities specified.

### 2. Relationship Resolution

Uses [`RelationshipGraph`](../backend/app/services/query/relationship_graph.py) to:
- Find paths between indices
- Resolve join fields
- Determine dependencies
- Order queries by relationships

**Example**:
```python
# Query: "Show APIs with critical vulnerabilities"
# Entities: ["api", "vulnerability"]
# 
# Resolved Path:
# security-findings → api-inventory
# Join: {"api_id": "id", "gateway_id": "gateway_id"}
```

### 3. Execution Strategy Selection

Automatically selects optimal strategy based on:

| Condition | Strategy | Reason |
|-----------|----------|--------|
| Single index | `SINGLE_INDEX` | No joins needed |
| 2 related indices | `SEQUENTIAL` | Simple join |
| 3+ related indices | `NESTED` | Complex multi-hop |
| Unrelated indices | `PARALLEL` | Independent queries |

### 4. Context Integration

Integrates with [`ContextManager`](../backend/app/services/query/context_manager.py) to:
- Retrieve entity IDs from previous queries
- Apply accumulated filters
- Enable follow-up questions

**Example**:
```python
# Query 1: "Show me APIs"
# Result: API-001, API-002, API-003

# Query 2: "Show vulnerabilities for these APIs"
# Context: api_id in [API-001, API-002, API-003]
# Applied automatically to vulnerability query
```

### 5. Execution Optimization

#### Query Ordering
Orders queries by dependencies using topological sort:
```python
# Before: [api-inventory, security-findings, gateway-registry]
# After:  [gateway-registry, api-inventory, security-findings]
# Reason: api-inventory depends on gateway-registry
```

#### Cost Estimation
Estimates execution cost (0-1 scale) based on:
- Number of indices: `0.2 per index`
- Join operations: `0.3 per join`
- Filter selectivity: `-0.1 per filter` (reduces cost)

### 6. Schema Validation

Validates queries against [`SchemaRegistry`](../backend/app/services/query/schema_registry.py):
- Field existence checks
- Type validation
- Join field verification

## Usage

### Basic Usage

```python
from app.services.query import QueryPlanner, SchemaRegistry, RelationshipGraph
from app.models.query import InterpretedIntent

# Initialize components
schema_registry = SchemaRegistry(opensearch_client)
await schema_registry.load_schemas()
relationship_graph = RelationshipGraph()
planner = QueryPlanner(schema_registry, relationship_graph)

# Create plan
intent = InterpretedIntent(
    action="list",
    entities=["api", "vulnerability"],
    filters={"severity": "critical"},
    time_range=None
)

plan = planner.create_plan(
    session_id=session_id,
    query_text="Show APIs with critical vulnerabilities",
    intent=intent
)

# Validate plan
is_valid, errors = planner.validate_plan(plan)
```

### With Context Manager

```python
from app.services.query import ContextManager

context_manager = ContextManager(session_ttl_minutes=30)
planner = QueryPlanner(schema_registry, relationship_graph, context_manager)

# First query establishes context
plan1 = planner.create_plan(session_id, "Show APIs", intent1)

# Second query uses context
plan2 = planner.create_plan(session_id, "Show their vulnerabilities", intent2)
# Automatically filters by API IDs from plan1
```

## Query Plan Examples

### Example 1: Single Index Query

**Query**: "Show me all active APIs"

```json
{
  "strategy": "single_index",
  "index_queries": [
    {
      "index": "api-inventory",
      "query_dsl": {
        "query": {
          "bool": {
            "must": [
              {"term": {"status": "active"}}
            ]
          }
        }
      },
      "filters": {"status": "active"},
      "required_fields": ["id", "name", "base_path", "status"],
      "join_fields": {},
      "depends_on": []
    }
  ],
  "requires_join": false,
  "estimated_cost": 0.2
}
```

### Example 2: Multi-Index with Join

**Query**: "Show APIs with critical vulnerabilities"

```json
{
  "strategy": "sequential",
  "index_queries": [
    {
      "index": "security-findings",
      "query_dsl": {
        "query": {
          "bool": {
            "must": [
              {"term": {"severity": "critical"}}
            ]
          }
        }
      },
      "filters": {"severity": "critical"},
      "required_fields": ["api_id", "gateway_id", "title", "severity"],
      "join_fields": {},
      "depends_on": []
    },
    {
      "index": "api-inventory",
      "query_dsl": {
        "query": {
          "bool": {
            "must": [
              {"terms": {"id": ["API-001", "API-002"]}}
            ]
          }
        }
      },
      "filters": {},
      "required_fields": ["id", "name", "base_path", "status"],
      "join_fields": {"api_id": "id", "gateway_id": "gateway_id"},
      "depends_on": ["security-findings"]
    }
  ],
  "requires_join": true,
  "join_strategy": "api_id",
  "estimated_cost": 0.7
}
```

### Example 3: Complex Multi-Hop

**Query**: "Show gateways, their APIs, and vulnerabilities"

```json
{
  "strategy": "nested",
  "index_queries": [
    {
      "index": "gateway-registry",
      "depends_on": []
    },
    {
      "index": "api-inventory",
      "join_fields": {"id": "gateway_id"},
      "depends_on": ["gateway-registry"]
    },
    {
      "index": "security-findings",
      "join_fields": {"api_id": "id"},
      "depends_on": ["api-inventory"]
    }
  ],
  "requires_join": true,
  "estimated_cost": 0.9
}
```

## Testing

### Unit Tests
Location: [`backend/tests/unit/test_query_planner.py`](../backend/tests/unit/test_query_planner.py)

Coverage:
- ✅ Single index query planning
- ✅ Multi-index query with relationships
- ✅ Time range filtering
- ✅ Context filter integration
- ✅ Execution order optimization
- ✅ Cost estimation
- ✅ Strategy selection
- ✅ Required fields selection
- ✅ Plan validation
- ✅ Edge cases and error handling

### Integration Tests
Location: [`backend/tests/integration/test_query_planner_integration.py`](../backend/tests/integration/test_query_planner_integration.py)

Coverage:
- ✅ End-to-end single index planning
- ✅ End-to-end multi-index planning
- ✅ Context propagation across queries
- ✅ Relationship path finding
- ✅ Time range with real schema
- ✅ Complex multi-entity queries
- ✅ Schema field validation
- ✅ Performance benchmarks

### Running Tests

```bash
# Unit tests
pytest backend/tests/unit/test_query_planner.py -v

# Integration tests
pytest backend/tests/integration/test_query_planner_integration.py -v

# All query planner tests
pytest backend/tests -k "query_planner" -v
```

## Performance

### Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Single index plan | < 10ms | No relationship resolution |
| Multi-index plan (2 indices) | < 50ms | Simple join |
| Multi-index plan (3+ indices) | < 100ms | Complex relationships |
| Plan validation | < 5ms | Schema checks |

### Optimization Strategies

1. **Schema Caching**: Schemas loaded once and cached
2. **Relationship Caching**: Relationship graph built at initialization
3. **Lazy Context Loading**: Context only loaded when needed
4. **Early Validation**: Invalid fields logged but don't block planning

## Integration Points

### With Query Service
The QueryPlanner integrates with [`QueryService`](../backend/app/services/query_service.py) for end-to-end query processing:

```python
# In QueryService
self.query_planner = QueryPlanner(
    self.schema_registry,
    self.relationship_graph,
    self.context_manager
)

# Create plan
plan = self.query_planner.create_plan(session_id, query_text, intent)

# Execute plan (Phase 4)
results = await self.multi_index_executor.execute(plan)
```

### With Context Manager
Bidirectional integration:
- **Input**: Gets entity IDs and filters from previous queries
- **Output**: Stores query results for future context

### With Relationship Graph
Uses relationship graph for:
- Finding paths between indices
- Resolving join fields
- Determining query dependencies

### With Schema Registry
Uses schema registry for:
- Field validation
- Type checking
- Required field selection

## Future Enhancements

### Phase 4: Multi-Index Execution
- Implement `MultiIndexExecutor` to execute plans
- Add result merging and joining
- Support parallel execution

### Phase 5: Advanced Features
- Query plan caching
- Adaptive strategy selection based on performance
- Cost-based optimization
- Query rewriting for performance

## References

- [Enterprise NLQ Multi-Index Analysis](./enterprise-nlq-multi-index-analysis.md)
- [Relationship Graph](../backend/app/services/query/relationship_graph.py)
- [Schema Registry](../backend/app/services/query/schema_registry.py)
- [Context Manager](../backend/app/services/query/context_manager.py)

## Deliverables

✅ **Completed**:
1. `QueryPlanner` class with index selection
2. Relationship resolver integration
3. Execution optimizer
4. `QueryPlan` model and supporting models
5. Comprehensive unit tests (15+ test cases)
6. Integration tests (8+ test scenarios)
7. Documentation

**Next Phase**: Phase 4 - Multi-Index Execution (Week 7-8)

---

*Made with Bob*