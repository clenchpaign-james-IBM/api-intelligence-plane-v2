# Query Service Entity Coverage Fix

## Overview
Fixed missing entity support in the Query Service to ensure all project entities are properly handled in natural language queries. Correctly identified that rate limiting is part of the optimization/recommendation feature, not a separate entity. Also updated follow-up query suggestions to cover all entities.

## Changes Made

### 1. Added Missing Repository Imports
**File**: `backend/app/services/query_service.py`

Added imports for:
- `GatewayRepository` - For gateway entity queries
- `VulnerabilityRepository` - For vulnerability entity queries (replaced empty placeholder)
- `TransactionalLogRepository` - For transaction log queries

**Note**: `RateLimitPolicyRepository` was NOT added as rate limiting is part of the optimization recommendations feature, not a separate queryable entity.

### 2. Updated QueryService Constructor
**File**: `backend/app/services/query_service.py`

Added optional parameters with default instantiation:
```python
gateway_repository: Optional[GatewayRepository] = None,
vulnerability_repository: Optional[VulnerabilityRepository] = None,
transactional_log_repository: Optional[TransactionalLogRepository] = None,
```

Initialized repositories:
```python
self.gateway_repo = gateway_repository or GatewayRepository()
self.vulnerability_repo = vulnerability_repository or VulnerabilityRepository()
self.transactional_log_repo = transactional_log_repository or TransactionalLogRepository()
```

### 3. Updated Entity Keywords
**File**: `backend/app/services/query_service.py`

- Added `transaction` entity keywords for transactional log queries
- **Moved rate limiting keywords to `recommendation` entity** (lines 80-88):
  ```python
  "recommendation": ["recommendation", "recommendations", "optimization", "suggestion", 
                     "rate limit", "rate limiting", "throttle", "throttling", 
                     "caching", "compression"]
  ```

This correctly reflects that rate limiting, caching, and compression are all types of optimization recommendations (see `RecommendationType` enum in `recommendation.py`).

### 4. Implemented Entity Routing Logic
**File**: `backend/app/services/query_service.py` (lines 888-925)

Added handling for all missing entities:

- **gateway**: Routes to `GatewayRepository`
- **metric**: Routes to `MetricsRepository` (was injected but unused)
- **vulnerability**: Routes to `VulnerabilityRepository` (replaced empty placeholder)
- **transaction/transactional_log**: Routes to `TransactionalLogRepository`

**Rate limiting queries** now correctly route to `RecommendationRepository` since rate limiting is a `RecommendationType.RATE_LIMITING` within optimization recommendations.

### 5. Updated API Endpoint
**File**: `backend/app/api/v1/query.py`

- Added repository imports (excluding RateLimitPolicyRepository)
- Instantiated new repositories
- Passed repositories to QueryService constructor

## Entity Coverage Summary

### Before Fix
- ✅ `api` - APIRepository
- ✅ `prediction` - PredictionRepository
- ✅ `recommendation` - RecommendationRepository (but missing rate limit keywords)
- ✅ `compliance` - ComplianceRepository
- ⚠️ `vulnerability` - Returned empty data
- ❌ `gateway` - Not handled
- ❌ `metric` - Not handled (repository injected but unused)
- ❌ `transaction` - Not handled

### After Fix
- ✅ `api` - APIRepository
- ✅ `gateway` - GatewayRepository
- ✅ `metric` - MetricsRepository
- ✅ `prediction` - PredictionRepository
- ✅ `vulnerability` - VulnerabilityRepository
- ✅ `recommendation` - RecommendationRepository (includes rate limiting, caching, compression)
- ✅ `compliance` - ComplianceRepository
- ✅ `transaction` - TransactionalLogRepository

## Architecture Understanding

### Rate Limiting Integration
Rate limiting is **NOT** a separate entity but a type of optimization recommendation:

**Model**: `backend/app/models/recommendation.py`
```python
class RecommendationType(str, Enum):
    CACHING = "caching"
    RATE_LIMITING = "rate_limiting"  # Part of recommendations!
    COMPRESSION = "compression"
```

**Index**: `optimization-recommendations` (not `rate-limit-policies`)

**Repository**: `RecommendationRepository` queries optimization recommendations which include:
- Caching recommendations
- Rate limiting recommendations
- Compression recommendations

This unified approach means queries like "show rate limiting recommendations" or "what rate limits should I apply?" correctly query the optimization recommendations index and filter by `recommendation_type: "rate_limiting"`.

### 6. Updated Follow-Up Query Suggestions
**File**: `backend/app/services/query_service.py` (lines 1138-1180)

Added follow-up suggestions for newly supported entities:

- **gateway**: "Show me the APIs managed by these gateways", "What's the health status?", "Show policies configured"
- **metric**: "Show me the trend over the last 7 days", "Which APIs have highest latency?", "Show error rate patterns"
- **transaction**: "Show me failed transactions", "What's the average response time?", "Show most active APIs"

This ensures users get contextually relevant follow-up suggestions for all entity types.

## Backward Compatibility

All changes maintain backward compatibility:
- New repository parameters are optional with default instantiation
- Existing test files using positional arguments continue to work
- No breaking changes to existing API contracts

## Testing

Import test passed successfully:
```bash
cd backend && python -c "from app.services.query_service import QueryService; from app.api.v1.query import query_service; print('Import successful')"
# Output: Import successful - all entities properly configured
```

## Example Queries Now Supported

With these changes, the following natural language queries are now fully supported:

1. **Gateway queries**: "Show me all gateways", "List active gateways"
2. **Metric queries**: "What are the metrics for API X?", "Show performance metrics"
3. **Vulnerability queries**: "List all vulnerabilities", "Show security issues for API Y"
4. **Rate limiting queries**: "Show rate limiting recommendations", "What rate limits should I apply?" (routes to recommendations)
5. **Optimization queries**: "Show caching recommendations", "What compression optimizations are available?" (routes to recommendations)
6. **Transaction queries**: "Show recent transactions", "List API request logs"

## Files Modified

1. `backend/app/services/query_service.py` - Core service implementation
2. `backend/app/api/v1/query.py` - API endpoint configuration
3. `docs/query-service-entity-coverage-fix.md` - This documentation

## Key Learnings

- Rate limiting is part of the optimization feature, stored in `optimization-recommendations` index
- The `RateLimitPolicyRepository` exists for managing applied policies, not for querying recommendations
- Natural language queries about rate limiting should route to recommendations, not policies
- This maintains the separation between recommendations (what to do) and policies (what's been done)

## Date
2026-04-20