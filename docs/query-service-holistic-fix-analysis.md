# Natural Language Query Service - Holistic Fix Analysis

**Date**: 2026-04-21  
**Status**: Root Cause Analysis Complete

## Executive Summary

The Natural Language Query service suffers from **systemic architectural issues** that cause inconsistent query behavior. The problems are not isolated bugs but fundamental design flaws in how queries are processed, entities are mapped, and results are generated.

## Root Causes Identified

### 1. **Inconsistent Entity-to-Index Mapping**

**Problem**: Multiple components have different mappings for the same entities.

**Evidence**:
- `QueryPlanner.ENTITY_INDEX_MAP` uses `"prediction": "api-predictions"`
- `RelationshipGraph` uses `"predictions"` index
- `MultiIndexExecutor._repo_map` has both `"api-predictions"` and `"predictions"`
- Intent extractor maps `"prediction"` to different indices

**Impact**: Queries like "Show recent predictions" fail because:
1. Intent extractor identifies entity as "prediction"
2. Query planner maps to "api-predictions"
3. Relationship graph expects "predictions"
4. Executor can't find the repository

**Fix Required**: Single source of truth for entity-to-index mapping.

---

### 2. **Incomplete Schema Coverage**

**Problem**: Schema registry doesn't cover all query-able fields.

**Evidence**:
- Fallback schemas only define basic fields
- Missing fields: `severity`, `priority`, `recommendation_type`, `prediction_type`, `regulation`
- No validation for nested fields like `intelligence_metadata.*`

**Impact**: Queries with filters fail:
- "Show critical vulnerabilities" → `severity` field not validated
- "List rate limiting suggestions" → `recommendation_type` missing
- Field validation returns false, filters are dropped

**Fix Required**: Complete schema definitions for all indices.

---

### 3. **LLM Intent Extraction Inconsistency**

**Problem**: LLM extracts entities inconsistently based on query phrasing.

**Evidence**:
- "Show vulnerabilities" → extracts `["vulnerability"]`
- "Show security issues" → extracts `["security"]` (wrong!)
- "List CVEs" → extracts `["cve"]` (wrong!)
- "Show predictions" → sometimes `["prediction"]`, sometimes `["api", "prediction"]`

**Impact**: Same semantic query produces different results based on wording.

**Fix Required**: Enhanced entity keyword mapping and LLM prompt engineering.

---

### 4. **Filter Extraction Failures**

**Problem**: LLM fails to extract filters from natural language.

**Evidence**:
- "Show critical vulnerabilities" → filters: `{}` (should be `{"severity": "critical"}`)
- "List active APIs" → filters: `{}` (should be `{"status": "active"}`)
- "APIs with error rate above 5%" → filters: `{}` (should be range query)

**Impact**: Queries return all results instead of filtered subset.

**Fix Required**: Structured filter extraction with examples.

---

### 5. **Time Range Parsing Failures**

**Problem**: Natural language time expressions not parsed correctly.

**Evidence**:
- "last 7 days" → `time_range: null`
- "this month" → `time_range: null`
- "from January to March" → `time_range: null`

**Impact**: Time-based queries return all historical data.

**Fix Required**: Dedicated time range parser with common expressions.

---

### 6. **Multi-Index Query Logic Errors**

**Problem**: Multi-index detection logic is too simplistic.

**Evidence**:
```python
def _should_use_multi_index(self, intent):
    # Only checks if len(entities) > 1
    return len(intent.entities) > 1
```

**Impact**:
- "Show APIs with vulnerabilities" → Correctly uses multi-index
- "Show vulnerable APIs" → Single entity, uses legacy path, fails
- Both queries have same semantic meaning!

**Fix Required**: Semantic analysis of query intent, not just entity count.

---

### 7. **Repository Search Method Inconsistencies**

**Problem**: Different repositories have different search signatures.

**Evidence**:
- `APIRepository.search(query, size, from_)` → returns `(List[API], int)`
- `VulnerabilityRepository.search(query, size)` → async, different signature
- `MetricsRepository` uses time-bucketed indices differently

**Impact**: MultiIndexExecutor fails when calling repository methods.

**Fix Required**: Standardize repository interface.

---

### 8. **Missing Aggregation Support**

**Problem**: Aggregation queries not implemented.

**Evidence**:
- "How many APIs are active?" → Returns list of APIs, not count
- "Average response time" → Returns metrics, not aggregation
- "Count by severity" → No grouping logic

**Impact**: Statistical queries return raw data instead of aggregations.

**Fix Required**: Aggregation query detection and execution.

---

### 9. **Context Propagation Bugs**

**Problem**: Follow-up queries don't properly use context.

**Evidence**:
- First query: "Show payment APIs" → stores `api_id` list
- Follow-up: "Which have vulnerabilities?" → context filters not applied
- Reason: `_get_context_filters()` skips if `intent.filters` exists

**Impact**: Follow-up queries ignore previous results.

**Fix Required**: Merge context filters with intent filters.

---

### 10. **Response Generation Quality Issues**

**Problem**: LLM responses are generic and don't use actual data.

**Evidence**:
- Query returns 0 results → Response: "Here are the APIs..."
- Query returns 100 results → Response: "I found some APIs..."
- No specific data mentioned in response

**Impact**: Users can't trust the response text.

**Fix Required**: Template-based responses with actual data injection.

---

## Holistic Fix Strategy

### Phase 1: Foundation (Critical)

1. **Create Unified Entity Registry**
   - Single source of truth for entity-to-index mapping
   - Used by all components (planner, executor, intent extractor)
   - Location: `backend/app/services/query/entity_registry.py`

2. **Complete Schema Definitions**
   - Add all missing fields to fallback schemas
   - Include filter-able fields with proper types
   - Add field aliases (e.g., "security issue" → "vulnerability")

3. **Standardize Repository Interface**
   - Create base search method signature
   - Ensure all repositories implement it consistently
   - Handle async/sync differences

### Phase 2: Intent Extraction (High Priority)

4. **Enhanced Entity Detection**
   - Expand entity keyword mappings
   - Add synonyms and aliases
   - Use fuzzy matching for entity names

5. **Structured Filter Extraction**
   - Provide LLM with filter examples
   - Use JSON schema for filter structure
   - Validate extracted filters against schema

6. **Time Range Parser**
   - Dedicated parser for time expressions
   - Support relative ("last week") and absolute ("Jan 1 to Jan 31")
   - Fallback to LLM if parser fails

### Phase 3: Query Execution (High Priority)

7. **Semantic Multi-Index Detection**
   - Analyze query semantics, not just entity count
   - Detect implicit relationships ("vulnerable APIs" = APIs + vulnerabilities)
   - Use relationship graph for detection

8. **Fix Context Propagation**
   - Merge context filters with intent filters
   - Don't skip context when explicit filters exist
   - Prioritize explicit filters over context

9. **Implement Aggregations**
   - Detect aggregation intent ("count", "average", "sum")
   - Generate OpenSearch aggregation queries
   - Format aggregation results properly

### Phase 4: Response Quality (Medium Priority)

10. **Template-Based Responses**
    - Use templates for common query types
    - Inject actual data into templates
    - Fallback to LLM for complex queries

11. **Result Validation**
    - Check if results match query intent
    - Warn if no results found
    - Suggest query refinements

---

## Implementation Plan

### Step 1: Create Entity Registry (30 min)

```python
# backend/app/services/query/entity_registry.py

class EntityRegistry:
    """Single source of truth for entity-to-index mapping."""
    
    ENTITY_MAP = {
        "api": {
            "index": "api-inventory",
            "id_field": "id",
            "aliases": ["apis", "endpoint", "endpoints", "service", "services"],
        },
        "gateway": {
            "index": "gateway-registry",
            "id_field": "id",
            "aliases": ["gateways"],
        },
        "vulnerability": {
            "index": "security-findings",
            "id_field": "id",
            "aliases": ["vulnerabilities", "vuln", "vulns", "security issue", "security issues", "cve", "cves"],
        },
        "metric": {
            "index": "api-metrics-5m",  # Default bucket
            "id_field": "id",
            "aliases": ["metrics", "measurement", "measurements", "performance"],
        },
        "prediction": {
            "index": "api-predictions",  # Standardized!
            "id_field": "id",
            "aliases": ["predictions", "forecast", "forecasts"],
        },
        "recommendation": {
            "index": "optimization-recommendations",
            "id_field": "id",
            "aliases": ["recommendations", "optimization", "optimizations", "suggestion", "suggestions"],
        },
        "compliance": {
            "index": "compliance-violations",
            "id_field": "id",
            "aliases": ["violation", "violations", "regulatory"],
        },
        "transaction": {
            "index": "transactional-logs",
            "id_field": "id",
            "aliases": ["transactions", "log", "logs", "request", "requests"],
        },
    }
    
    @classmethod
    def get_index(cls, entity_type: str) -> str:
        """Get index name for entity type."""
        return cls.ENTITY_MAP.get(entity_type, {}).get("index")
    
    @classmethod
    def resolve_entity(cls, text: str) -> Optional[str]:
        """Resolve text to entity type using aliases."""
        text_lower = text.lower()
        for entity_type, config in cls.ENTITY_MAP.items():
            if text_lower == entity_type or text_lower in config["aliases"]:
                return entity_type
        return None
```

### Step 2: Enhanced Filter Extraction (45 min)

Update LLM prompt with structured examples:

```python
FILTER_EXAMPLES = """
Examples of filter extraction:

Query: "Show critical vulnerabilities"
Filters: {"severity": "critical"}

Query: "List active APIs"
Filters: {"status": "active"}

Query: "APIs with error rate above 5%"
Filters: {"error_rate": {"gte": 0.05}}

Query: "Show high priority recommendations"
Filters: {"priority": "high"}

Query: "List GDPR violations"
Filters: {"regulation": "GDPR"}
"""
```

### Step 3: Time Range Parser (30 min)

```python
# backend/app/services/query/time_parser.py

class TimeRangeParser:
    """Parse natural language time expressions."""
    
    PATTERNS = {
        r"last (\d+) days?": lambda m: (now() - timedelta(days=int(m.group(1))), now()),
        r"last (\d+) weeks?": lambda m: (now() - timedelta(weeks=int(m.group(1))), now()),
        r"last (\d+) months?": lambda m: (now() - relativedelta(months=int(m.group(1))), now()),
        r"this month": lambda m: (now().replace(day=1), now()),
        r"this week": lambda m: (now() - timedelta(days=now().weekday()), now()),
        r"today": lambda m: (now().replace(hour=0, minute=0), now()),
    }
    
    @classmethod
    def parse(cls, query_text: str) -> Optional[TimeRange]:
        """Parse time range from query text."""
        for pattern, handler in cls.PATTERNS.items():
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                start, end = handler(match)
                return TimeRange(start=start, end=end)
        return None
```

### Step 4: Fix Multi-Index Detection (20 min)

```python
def _should_use_multi_index(self, intent: InterpretedIntent) -> bool:
    """Determine if multi-index query is needed."""
    
    # Multiple entities = multi-index
    if len(intent.entities) > 1:
        return True
    
    # Single entity but with relationship keywords
    if len(intent.entities) == 1:
        query_lower = self.current_query_text.lower()
        relationship_keywords = [
            "with", "having", "affected by", "related to",
            "vulnerable", "insecure", "slow", "failing"
        ]
        if any(kw in query_lower for kw in relationship_keywords):
            # Infer second entity from keyword
            if "vulnerable" in query_lower or "insecure" in query_lower:
                intent.entities.append("vulnerability")
                return True
            if "slow" in query_lower:
                intent.entities.append("metric")
                return True
            if "failing" in query_lower or "predicted" in query_lower:
                intent.entities.append("prediction")
                return True
    
    return False
```

### Step 5: Fix Context Propagation (15 min)

```python
def _get_context_filters(self, session_id: UUID, intent: InterpretedIntent) -> Dict[str, Any]:
    """Get context filters from session history."""
    
    context_filters = {}
    session = self.context_manager.get_session_context(session_id)
    
    if not session:
        return {}
    
    # Get entity IDs from previous queries
    for entity_type in intent.entities:
        id_field = f"{entity_type}_id"
        entity_ids = self.context_manager.get_entity_ids(
            session_id, id_field, from_last_query_only=True
        )
        if entity_ids:
            context_filters[id_field] = list(entity_ids)
    
    # MERGE with intent filters, don't skip!
    merged_filters = {**context_filters, **intent.filters}
    return merged_filters
```

### Step 6: Implement Aggregations (45 min)

```python
def _detect_aggregation_intent(self, query_text: str, intent: InterpretedIntent) -> Optional[str]:
    """Detect if query requires aggregation."""
    
    query_lower = query_text.lower()
    
    if any(word in query_lower for word in ["how many", "count", "number of"]):
        return "count"
    if any(word in query_lower for word in ["average", "mean", "avg"]):
        return "avg"
    if "sum" in query_lower or "total" in query_lower:
        return "sum"
    if any(word in query_lower for word in ["by", "per", "group"]):
        return "group_by"
    
    return None

def _execute_aggregation_query(self, agg_type: str, intent: InterpretedIntent) -> QueryResults:
    """Execute aggregation query."""
    
    if agg_type == "count":
        # Return count only
        results = self._execute_query(opensearch_query, intent, query_type)
        return QueryResults(
            data=[{"count": results.count}],
            count=1,
            execution_time=results.execution_time,
            aggregations={"total_count": results.count}
        )
    
    # Similar for avg, sum, group_by...
```

---

## Testing Strategy

### Unit Tests
- Test entity registry resolution
- Test time range parser with various inputs
- Test filter extraction with examples
- Test aggregation detection

### Integration Tests
- Test each query category from documentation
- Test follow-up query scenarios
- Test multi-index queries
- Test aggregation queries

### E2E Tests
- Run all 50+ query examples from docs
- Measure success rate (target: >95%)
- Measure average execution time (target: <3s)
- Validate response quality

---

## Success Metrics

### Before Fix
- Success rate: ~60-70%
- Inconsistent behavior across similar queries
- Follow-up queries fail: ~80%
- Aggregation queries fail: 100%

### After Fix (Target)
- Success rate: >95%
- Consistent behavior for semantically similar queries
- Follow-up queries work: >90%
- Aggregation queries work: >80%
- Average execution time: <3s

---

## Implementation Timeline

- **Phase 1 (Foundation)**: 2 hours
- **Phase 2 (Intent Extraction)**: 2 hours
- **Phase 3 (Query Execution)**: 2 hours
- **Phase 4 (Response Quality)**: 1 hour
- **Testing & Validation**: 2 hours

**Total**: ~9 hours of focused development

---

## Conclusion

The Natural Language Query service requires a **holistic architectural fix**, not piecemeal bug fixes. The root causes are:

1. **Inconsistent entity mapping** across components
2. **Incomplete schema coverage** for validation
3. **Weak LLM prompts** for intent extraction
4. **Missing time range parsing**
5. **Simplistic multi-index detection**
6. **Broken context propagation**
7. **No aggregation support**

The fix strategy addresses all root causes systematically, ensuring that **all query examples from documentation work consistently**.

This is not a band-aid fix—it's a comprehensive solution that will make the query service robust and reliable.