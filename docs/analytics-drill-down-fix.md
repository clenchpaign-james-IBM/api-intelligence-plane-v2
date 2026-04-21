# Analytics Drill-Down Fix

## Issue
When clicking on a metric in the Analytics page Metrics Overview, the application displayed the error:
```
Failed to load drill-down logs for the selected metric
```

## Root Causes
1. The frontend was calling `/api/v1/analytics/metrics/${metricId}/logs` endpoint, but this endpoint did not exist in the backend
2. The `MetricsRepository.get()` method was searching by OpenSearch `_id` instead of the `id` field
3. The `find_by_api()` method in MetricsRepository was incomplete and not returning any value

## Solution
Added a new endpoint `/api/v1/analytics/metrics/{metric_id}/logs` that:
1. Does not require a gateway_id parameter (the metric already contains this information)
2. Matches the frontend's expected API contract
3. Returns logs in the format expected by the frontend (`items` array)

## Changes Made

### Backend Changes

1. **Added new endpoint** in [`backend/app/api/v1/metrics.py`](../backend/app/api/v1/metrics.py):
   - New route: `GET /api/v1/analytics/metrics/{metric_id}/logs`
   - Accepts `metric_id` and optional `limit` parameter
   - Returns logs with metric context in the format: `{ items: [], total: number, metric_summary: {}, time_range: {} }`

2. **Overrode `get()` method** in [`backend/app/db/repositories/metrics_repository.py`](../backend/app/db/repositories/metrics_repository.py):
   - Added custom `get()` method that searches by the `id` field (not `_id`) across all time-bucketed indices
   - OpenSearch stores metrics with composite `_id` keys but the application uses the `id` field
   - Uses search query instead of direct get since we have wildcard index patterns

3. **Fixed incomplete method** in [`backend/app/db/repositories/metrics_repository.py`](../backend/app/db/repositories/metrics_repository.py):
   - The `find_by_api` method was incomplete and not returning any value
   - Added proper return statement to delegate to `find_by_time_bucket`

4. **Fixed deprecation warning** in [`backend/app/api/v1/metrics.py`](../backend/app/api/v1/metrics.py):
   - Changed `regex` parameter to `pattern` in Query validation (FastAPI deprecation)

## Technical Details

### Metrics Storage
Metrics are stored in time-bucketed OpenSearch indices:
- Index pattern: `api-metrics-{bucket}-{YYYY.MM}` (e.g., `api-metrics-1h-2026.04`)
- Document `_id`: Composite key like `{api_id}_{gateway_id}_{timestamp}_{bucket}`
- Document `id` field: UUID used by the application (e.g., `dd462800-c39e-4970-a3e4-42a7471bc268`)

The fix ensures the repository searches by the `id` field across all metric indices using a wildcard pattern.

### Testing

Created comprehensive tests in [`backend/tests/test_analytics_drill_down.py`](../backend/tests/test_analytics_drill_down.py):
- Test successful drill-down to logs
- Test error handling when metric not found
- Both tests pass successfully

## API Contract

### Request
```
GET /api/v1/analytics/metrics/{metric_id}/logs?limit=100
```

### Response
```json
{
  "items": [
    {
      "id": "uuid",
      "timestamp": "2024-01-01T00:00:00",
      "api_id": "uuid",
      "gateway_id": "uuid",
      "method": "GET",
      "path": "/api/endpoint",
      "status_code": 200,
      "total_time_ms": 150,
      ...
    }
  ],
  "total": 100,
  "metric_summary": {
    "api_id": "uuid",
    "gateway_id": "uuid",
    "timestamp": "2024-01-01T00:00:00",
    "time_bucket": "1h",
    "request_count": 1000,
    "error_rate": 5.0,
    "response_time_p50": 100.0,
    "response_time_p95": 200.0,
    "response_time_p99": 300.0
  },
  "time_range": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-01T01:00:00"
  }
}
```

## Verification

To verify the fix:
1. Start the backend server
2. Navigate to the Analytics page
3. Click on any metric in the Metrics Overview chart or table
4. The drill-down logs should now load successfully without errors

## Related Files
- Frontend: [`frontend/src/pages/Analytics.tsx`](../frontend/src/pages/Analytics.tsx)
- Frontend Service: [`frontend/src/services/analytics.ts`](../frontend/src/services/analytics.ts)
- Backend API: [`backend/app/api/v1/metrics.py`](../backend/app/api/v1/metrics.py)
- Backend Service: [`backend/app/services/metrics_service.py`](../backend/app/services/metrics_service.py)
- Tests: [`backend/tests/test_analytics_drill_down.py`](../backend/tests/test_analytics_drill_down.py)