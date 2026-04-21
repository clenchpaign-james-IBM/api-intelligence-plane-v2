# Query Service Test Issues Summary

**Date**: 2026-04-21  
**Test**: scripts/test_query_examples.py  
**Status**: Multiple issues identified

---

## Critical Issues

### 1. Query History Serialization Error
**Error**: `mapper_parsing_exception` - Cannot store OpenSearch DSL with date expressions like `'now-1d/d'`
**Location**: `query_service.py:343` - `self.query_repo.create()`
**Impact**: Prevents saving query history to OpenSearch
**Fix**: Sanitize OpenSearch query DSL before saving, converting date expressions to actual dates

### 2. LLM JSON Parsing Errors
**Error**: `Expecting value: line 1 column 1 (char 0)`
**Frequency**: Multiple occurrences
**Impact**: LLM returning invalid JSON responses
**Fix**: Add better error handling and retry logic for LLM responses

### 3. Invalid Field References
**Errors**:
- `Invalid field 'intelligence_metadata.environment'`
- `Invalid field 'metadata.environment'`
- `Invalid field 'field'`
- `Invalid field 'intelligence_metadata.recommendation_type'`
- `Invalid field 'intelligence_metadata.risk_score'`

**Impact**: Query generation fails due to schema mismatches
**Fix**: Update schema registry with correct field mappings

---

## Schema Issues

### 4. Missing Entity Index Mapping
**Error**: `Unknown entity type or no index mapping: vulnerability`
**Impact**: Cannot query vulnerability data
**Fix**: Ensure EntityRegistry has correct mapping for vulnerabilities

### 5. Nested Field Type Errors
**Errors**:
- `[nested] nested object under path [intelligence_metadata.compliance_status] is not of nested type`
- `[nested] nested object under path [policy_actions] is not of nested type`

**Impact**: Cannot query nested fields properly
**Fix**: Update query generation to handle non-nested objects correctly

### 6. Invalid Filter Fields
**Errors**:
- `Filter field 'severity' not valid for entities ['api']`
- `Filter field 'error_rate' not valid for entities ['api']`
- `Field severity not found in api-inventory schema`
- `Field prediction_type not found in api-inventory schema`
- `Field recommendation_type not found in api-inventory schema`

**Impact**: Filters not applied correctly
**Fix**: Map filter fields to correct indices (severity → vulnerabilities, error_rate → metrics)

---

## Relationship Issues

### 7. Missing Relationship Paths
**Error**: `No path found from api-metrics-5m to api-inventory`
**Impact**: Cannot join metrics with APIs
**Fix**: Add bidirectional relationships in RelationshipGraph

---

## Date Parsing Issues

### 8. Invalid Date Format
**Error**: `failed to parse date field [last day of this month]`
**Impact**: Natural language date expressions not converted properly
**Fix**: Improve TimeRangeParser to convert all expressions to ISO dates

---

## Query Generation Issues

### 9. Aggregation Query Format Error
**Error**: LLM generating `avg` in query section instead of aggs section
**Impact**: Aggregation queries fail
**Fix**: Improve LLM prompts to generate correct aggregation structure

### 10. Range Query Malformation
**Error**: `[range] malformed query, expected [END_OBJECT] but found [FIELD_NAME]`
**Impact**: Range queries fail
**Fix**: Validate and fix range query structure

---

## Priority Fixes

### P0 (Critical - Blocks All Queries)
1. Query history serialization (Issue #1)
2. LLM JSON parsing (Issue #2)

### P1 (High - Breaks Many Queries)
3. Invalid field references (Issue #3)
4. Missing entity mappings (Issue #4)
5. Filter field mapping (Issue #6)

### P2 (Medium - Breaks Some Queries)
6. Nested field handling (Issue #5)
7. Relationship paths (Issue #7)
8. Date parsing (Issue #8)

### P3 (Low - Edge Cases)
9. Aggregation format (Issue #9)
10. Range query validation (Issue #10)

---

## Recommended Fix Approach

1. **Fix P0 issues first** - Enable basic query execution
2. **Fix schema mappings** - Ensure all fields are correctly defined
3. **Fix entity/filter routing** - Route filters to correct indices
4. **Improve error handling** - Better fallbacks and retries
5. **Test incrementally** - Verify each fix before moving to next

---

## Success Metrics

- Target: >90% of documentation examples should work
- Current: ~20-30% (estimated from errors)
- After fixes: Should reach 90%+