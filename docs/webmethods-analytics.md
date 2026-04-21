# WebMethods Analytics Integration

**Version**: 1.0.0  
**Last Updated**: 2026-04-11  
**Status**: Implementation Scaffold

---

## Overview

The WebMethods analytics integration adds a vendor-neutral analytics pipeline for collecting raw transactional logs, querying aggregated metric buckets, and drilling down from metrics to source request events.

This implementation is intentionally scoped to **fresh analytics data and scaffolding only**:
- new OpenSearch index templates
- new repository/service/API scaffolding
- new frontend analytics flow
- no old-data migration

---

## Architecture Summary

The analytics flow follows an ETL-style pattern:

1. **Collect**
   - Gateway adapters expose [`get_transactional_logs()`](../backend/app/adapters/base.py)
   - [`NativeGatewayAdapter`](../backend/app/adapters/native_gateway.py) fetches transactional events from the demo gateway

2. **Store**
   - Raw events are stored through [`TransactionalLogRepository`](../backend/app/db/repositories/transactional_log_repository.py)
   - Daily indices follow the pattern:
     - `transactional-logs-YYYY.MM.DD`

3. **Aggregate**
   - [`WMAnalyticsService`](../backend/app/services/wm_analytics_service.py) provides scaffold methods for:
     - `aggregate_to_1m_bucket()`
     - `aggregate_to_5m_bucket()`
     - `aggregate_to_1h_bucket()`
     - `aggregate_to_1d_bucket()`

4. **Serve**
   - [`backend/app/api/v1/analytics.py`](../backend/app/api/v1/analytics.py) exposes analytics endpoints
   - [`frontend/src/pages/Analytics.tsx`](../frontend/src/pages/Analytics.tsx) provides the UI

---

## OpenSearch Index Strategy

### Raw Transactional Logs
Raw gateway events are stored in daily indices:

```text
transactional-logs-YYYY.MM.DD
```

### Aggregated Metrics
Metrics are organized by time bucket and month:

```text
api-metrics-1m-YYYY.MM
api-metrics-5m-YYYY.MM
api-metrics-1h-YYYY.MM
api-metrics-1d-YYYY.MM
```

### Retention Windows

| Bucket | Retention |
|--------|-----------|
| `1m` | 24 hours |
| `5m` | 7 days |
| `1h` | 30 days |
| `1d` | 90 days |
| raw logs | 30 days |

Cleanup scaffolding is implemented in [`backend/app/scheduler/wm_analytics_jobs.py`](../backend/app/scheduler/wm_analytics_jobs.py).

---

## Drill-Down Pattern

The drill-down flow is:

```text
Aggregated metric bucket -> selected metric id -> filtered transactional logs
```

Current drill-down behavior:
- the frontend selects a metric from the chart or table
- the analytics page preserves active gateway and bucket filters
- the backend resolves the selected metric into matching transactional logs using shared identifiers

Implemented UI pieces:
- [`MetricsChart`](../frontend/src/components/analytics/MetricsChart.tsx)
- [`MetricsTable`](../frontend/src/components/analytics/MetricsTable.tsx)
- [`TransactionalLogViewer`](../frontend/src/components/analytics/TransactionalLogViewer.tsx)
- [`Analytics`](../frontend/src/pages/Analytics.tsx)

Implemented navigation behavior:
- metrics-to-logs drill-down
- breadcrumb-style metrics → logs navigation
- back-to-metrics action
- filter context preservation while drilling down

---

## Multi-Gateway Configuration

The analytics model is multi-gateway aware through `gateway_id`.

### Supported Filtering
The following filters are supported across the analytics API:
- `gateway_id`
- `api_id`
- `application_id`
- `start_time`
- `end_time`
- `time_bucket`
- `limit`
- `offset`

### Segregation Strategy
Each record keeps the originating gateway identifier so analytics queries can:
- isolate a single gateway
- compare APIs inside the same gateway context
- avoid mixing raw log data across multiple gateway instances

---

## API Endpoints

The implemented analytics endpoints are:

- `GET /api/v1/analytics/metrics`
- `GET /api/v1/analytics/metrics/{metric_id}/logs`
- `GET /api/v1/analytics/logs`

Reference details and examples are documented in [`docs/api-reference.md`](./api-reference.md).

---

## Scheduling Scaffold

[`WMAnalyticsJobs`](../backend/app/scheduler/wm_analytics_jobs.py) includes scaffold jobs for:

- `collect_logs_job()`
- `aggregate_1m_job()`
- `aggregate_5m_job()`
- `aggregate_1h_job()`
- `aggregate_1d_job()`
- `cleanup_expired_data_job()`

These jobs currently provide operational structure and retention handling, without historical migration logic.

---

## Test and Mock Data Support

Added support files include:

- mock log generator:
  - [`backend/scripts/generate_wm_logs.py`](../backend/scripts/generate_wm_logs.py)
- analytics fixtures:
  - [`backend/tests/fixtures/wm_analytics_fixtures.py`](../backend/tests/fixtures/wm_analytics_fixtures.py)

These help seed fresh transactional logs and aggregated metric test data for analytics scenarios.

---

## Current Scope and Limitations

Implemented now:
- transactional log collection scaffold
- time-bucket aggregation scaffold
- analytics REST endpoints
- analytics frontend page and drill-down flow
- mock-data generation
- retention cleanup scaffold

Not implemented as part of this slice:
- historical migration of legacy data
- full production-grade rollup persistence logic
- comprehensive analytics integration and E2E validation
- demo gateway transactional event controller/service completion

---

## References

- architecture background: [`docs/webmethods-analytics-architecture.md`](./webmethods-analytics-architecture.md)
- API examples: [`docs/api-reference.md`](./api-reference.md)
- analytics service: [`backend/app/services/wm_analytics_service.py`](../backend/app/services/wm_analytics_service.py)
- analytics API: [`backend/app/api/v1/analytics.py`](../backend/app/api/v1/analytics.py)

<!-- Made with Bob -->