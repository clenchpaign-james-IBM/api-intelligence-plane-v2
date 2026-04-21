# Intelligence Metadata Pipeline Testing Guide

This guide explains how to test the intelligence metadata computation pipeline to ensure all jobs are working correctly.

## Overview

The intelligence metadata pipeline consists of 7 scheduled jobs that compute real intelligence values from actual data:

1. **Health Scores** (every 5 min) - From metrics
2. **Risk Scores** (every 1 hour) - From vulnerabilities  
3. **Security Scores** (every 1 hour) - From vulnerabilities and policies
4. **Usage Trends** (every 1 hour) - From metrics
5. **Shadow API Detection** (every 5 min) - From traffic analysis
6. **Compliance Status** (every 1 hour) - From compliance violations
7. **Predictions Status** (every 5 min) - From active predictions

## Prerequisites

1. **Backend service running**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **OpenSearch running**:
   ```bash
   docker-compose up -d opensearch
   ```

3. **Data available** (at least one of):
   - APIs registered in data store
   - Metrics collected
   - Transactional logs available
   - Vulnerabilities detected
   - Compliance violations found
   - Predictions generated

## Running the Test Script

### Basic Test
```bash
cd backend
python scripts/test_intelligence_pipeline.py
```

### Expected Output

```
============================================================
INTELLIGENCE METADATA PIPELINE TEST
============================================================

[Step 1] Checking data availability...
APIs: 15 found
Metrics: 1250 found
Vulnerabilities (sample API): 3 found
✅ Sufficient data available for intelligence computation

[Step 2] Testing individual intelligence jobs...
============================================================
Testing: Health Scores Computation
============================================================
✅ Health Scores Computation completed successfully in 2.34s

============================================================
Testing: Risk Scores Computation
============================================================
✅ Risk Scores Computation completed successfully in 1.87s

... (continues for all 7 jobs)

[Step 3] Testing master intelligence job...
============================================================
Testing: Master Intelligence Job (All Jobs)
============================================================
✅ Master Intelligence Job (All Jobs) completed successfully in 8.92s

[Step 4] Verifying intelligence metadata updates...
============================================================
Verifying Intelligence Metadata Updates
============================================================
Found 15 APIs in data store
✅ API 'Payment API' has computed intelligence:
   - Health Score: 87.5
   - Risk Score: 35.0
   - Security Score: 72.0
   - Usage Trend: increasing
   - Is Shadow: False
   - Has Predictions: True

Summary:
  - APIs with computed intelligence: 15/15
  - APIs with default values: 0/15
✅ Intelligence computation is working!

============================================================
TEST SUMMARY
============================================================

Individual Jobs: 7/7 passed
  ✅ PASS: Health Scores Computation
  ✅ PASS: Risk Scores Computation
  ✅ PASS: Security Scores Computation
  ✅ PASS: Usage Trends Computation
  ✅ PASS: Shadow API Detection
  ✅ PASS: Compliance Status Computation
  ✅ PASS: Predictions Status Update

Master Job: ✅ PASS
Verification: ✅ PASS

============================================================
🎉 ALL TESTS PASSED - Intelligence pipeline is working!
============================================================
```

## Troubleshooting

### No Data Available

If you see:
```
⚠️  WARNING: Limited data available
Intelligence jobs will run but may produce default values
```

**Solution**: Generate mock data first:
```bash
# Generate mock APIs
python scripts/generate_mock_apis.py

# Generate mock metrics
python scripts/generate_mock_metrics.py

# Generate mock vulnerabilities
python scripts/generate_mock_vulnerabilities.py

# Generate mock compliance violations
python scripts/generate_mock_compliance.py
```

### Jobs Fail to Execute

If jobs fail with errors:

1. **Check OpenSearch connection**:
   ```bash
   curl -X GET "localhost:9200/_cluster/health?pretty"
   ```

2. **Check indices exist**:
   ```bash
   curl -X GET "localhost:9200/_cat/indices?v"
   ```

3. **Check backend logs**:
   ```bash
   tail -f backend/logs/app.log
   ```

### Intelligence Not Updating

If tests pass but intelligence values remain at defaults:

1. **Check scheduler is running**:
   - Verify `SCHEDULER_ENABLED=true` in `.env`
   - Check backend logs for job execution

2. **Wait for job intervals**:
   - Health scores: 5 minutes
   - Risk scores: 1 hour
   - Security scores: 1 hour
   - Usage trends: 1 hour

3. **Manually trigger jobs**:
   ```python
   from app.scheduler.intelligence_metadata_jobs import run_all_intelligence_jobs
   import asyncio
   asyncio.run(run_all_intelligence_jobs())
   ```

## Verifying Frontend Display

After confirming intelligence computation works:

1. **Open Dashboard**:
   ```
   http://localhost:5173/
   ```

2. **Check API Inventory**:
   ```
   http://localhost:5173/apis
   ```

3. **Verify Intelligence Display**:
   - Health scores should show computed values (not 100.0)
   - Risk scores should reflect vulnerabilities (not 0.0)
   - Security scores should reflect posture (not 100.0)
   - Usage trends should show actual trends (not "stable")
   - Shadow APIs should be flagged if detected

## Manual Testing

### Test Individual Jobs

```python
# In Python shell or script
from app.scheduler.intelligence_metadata_jobs import *
import asyncio

# Test health scores
asyncio.run(compute_health_scores_job())

# Test risk scores
asyncio.run(compute_risk_scores_job())

# Test security scores
asyncio.run(compute_security_scores_job())

# Test usage trends
asyncio.run(compute_usage_trends_job())

# Test shadow API detection
asyncio.run(detect_shadow_apis_job())

# Test compliance status
asyncio.run(compute_compliance_status_job())

# Test predictions status
asyncio.run(update_predictions_status_job())

# Run all jobs
asyncio.run(run_all_intelligence_jobs())
```

### Verify Data in OpenSearch

```bash
# Check API with intelligence metadata
curl -X GET "localhost:9200/api-inventory/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {"match_all": {}},
    "size": 1
  }'

# Check for shadow APIs
curl -X GET "localhost:9200/api-inventory/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "term": {"intelligence_metadata.is_shadow": true}
    }
  }'
```

## Performance Benchmarks

Expected execution times (with 100 APIs):

| Job | Expected Time | Notes |
|-----|---------------|-------|
| Health Scores | 2-5 seconds | Queries metrics-1m index |
| Risk Scores | 1-3 seconds | Queries vulnerabilities |
| Security Scores | 1-3 seconds | Queries vulnerabilities + policies |
| Usage Trends | 2-4 seconds | Queries metrics-1h index |
| Shadow API Detection | 3-6 seconds | Queries transactional logs |
| Compliance Status | 1-3 seconds | Queries compliance violations |
| Predictions Status | 1-2 seconds | Queries predictions |
| **Master Job (All)** | **8-15 seconds** | Runs all jobs sequentially |

## Next Steps

After confirming intelligence pipeline works:

1. ✅ Intelligence jobs execute successfully
2. ✅ Intelligence values are computed correctly
3. ⏳ **Dashboard metrics integration** - Implement time-bucketed metrics queries
4. ⏳ **Frontend verification** - Confirm Dashboard and API Inventory display computed values
5. ⏳ **Drill-down capability** - Enable metrics → transactional logs tracing

## Related Documentation

- [Intelligence Gap Analysis](../../docs/API_INVENTORY_INTELLIGENCE_GAP_ANALYSIS.md)
- [Dashboard Feature Analysis](../../docs/DASHBOARD_FEATURE_ANALYSIS.md)
- [Shadow API Detection Design](../../docs/SHADOW_API_DETECTION_DESIGN.md)
- [Analysis Summary](../../docs/DASHBOARD_AND_API_INVENTORY_ANALYSIS_SUMMARY.md)

## Support

If you encounter issues:

1. Check backend logs: `backend/logs/app.log`
2. Check OpenSearch logs: `docker-compose logs opensearch`
3. Review error messages in test output
4. Verify data exists in OpenSearch indices
5. Confirm scheduler is enabled and running

---

**Last Updated**: 2026-04-13  
**Version**: 1.0