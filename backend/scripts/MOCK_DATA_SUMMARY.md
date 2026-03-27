# Mock Data Generation Summary

This document provides an overview of all mock data generation scripts available in the API Intelligence Plane project.

## Available Mock Data Generators

### 1. General Mock Data (`generate_mock_data.py`)

Generates foundational data for the platform:
- **Gateways**: Kong, Apigee, Native gateway instances
- **APIs**: API catalog entries with endpoints
- **Metrics**: Traffic and performance metrics

**Usage**:
```bash
python3 scripts/generate_mock_data.py
```

---

### 2. Security Vulnerabilities (`generate_mock_security_data.py`) ⭐ NEW

Generates comprehensive security vulnerability data for the Security feature.

**What it generates**:
- 50+ realistic security vulnerabilities (configurable)
- Multiple vulnerability types (Authentication, Authorization, Injection, Exposure, Configuration, Dependency)
- Various severity levels (Critical, High, Medium, Low)
- Different status states (Open, In Progress, Remediated, Accepted Risk, False Positive)
- Remediation actions and tracking
- CVE identifiers and CVSS scores
- Verification status

**Usage**:
```bash
# Generate 50 vulnerabilities (default)
python3 scripts/generate_mock_security_data.py

# Generate custom number with summary
python3 scripts/generate_mock_security_data.py --count 100 --summary
```

**Documentation**:
- [`README_SECURITY_MOCK_DATA.md`](README_SECURITY_MOCK_DATA.md) - Detailed usage guide
- [`SECURITY_DEMO_SCENARIOS.md`](SECURITY_DEMO_SCENARIOS.md) - Demo scenarios and use cases

---

### 3. Predictions (`generate_mock_predictions.py`)

Generates failure predictions for APIs:
- Predicted failures with timeframes
- Contributing factors
- Confidence scores
- Recommended actions

**Usage**:
```bash
python3 scripts/generate_mock_predictions.py
```

---

### 4. Optimization Recommendations (`generate_mock_optimizations.py`)

Generates performance optimization recommendations:
- Caching strategies
- Query optimization
- Resource allocation
- Implementation tracking

**Usage**:
```bash
python3 scripts/generate_mock_optimizations.py
```

---

### 5. Rate Limit Policies (`generate_mock_rate_limits.py`)

Generates rate limiting policies:
- Consumer-based limits
- Tier-based policies
- Priority levels
- Quota management

**Usage**:
```bash
python3 scripts/generate_mock_rate_limits.py
```

---

### 6. AI-Enhanced Predictions (`generate_ai_enhanced_predictions.py`)

Generates predictions with AI-powered explanations:
- LLM-generated insights
- Detailed trend analysis
- Natural language explanations

**Usage**:
```bash
python3 scripts/generate_ai_enhanced_predictions.py
```

---

### 7. Timeline Demo Predictions (`generate_timeline_demo_predictions.py`)

Generates time-series prediction data for timeline visualization:
- Historical predictions
- Trend data
- Timeline-specific formatting

**Usage**:
```bash
python3 scripts/generate_timeline_demo_predictions.py
```

---

## Complete Setup Workflow

For a full demo environment with all features:

```bash
cd backend

# 1. Generate base data (gateways, APIs, metrics)
python3 scripts/generate_mock_data.py

# 2. Generate security vulnerabilities
python3 scripts/generate_mock_security_data.py --count 50 --summary

# 3. Generate predictions
python3 scripts/generate_mock_predictions.py

# 4. Generate optimization recommendations
python3 scripts/generate_mock_optimizations.py

# 5. Generate rate limit policies
python3 scripts/generate_mock_rate_limits.py

# 6. (Optional) Generate AI-enhanced predictions
python3 scripts/generate_ai_enhanced_predictions.py

# 7. (Optional) Generate timeline demo data
python3 scripts/generate_timeline_demo_predictions.py
```

## Data Volumes

| Generator | Default Count | Configurable |
|-----------|--------------|--------------|
| Gateways | 3 | Yes |
| APIs | 15 (5 per gateway) | Yes |
| Metrics | Varies | Yes |
| **Security Vulnerabilities** | **50** | **Yes (--count)** |
| Predictions | Varies | Yes |
| Optimizations | Varies | Yes |
| Rate Limits | Varies | Yes |

## Feature Coverage

### Security Feature (NEW) ✅
- ✅ Vulnerability scanning
- ✅ Automated remediation tracking
- ✅ Security posture monitoring
- ✅ CVE and CVSS scoring
- ✅ Verification status
- ✅ Multiple vulnerability types
- ✅ Remediation actions

### Prediction Feature ✅
- ✅ Failure predictions
- ✅ Contributing factors
- ✅ AI-enhanced explanations
- ✅ Timeline visualization

### Optimization Feature ✅
- ✅ Performance recommendations
- ✅ Impact analysis
- ✅ Implementation tracking
- ✅ AI-enhanced insights

### Rate Limiting Feature ✅
- ✅ Consumer-based policies
- ✅ Tier management
- ✅ Priority levels

## Verification

After generating mock data, verify it was created successfully:

```bash
# Check security vulnerabilities
curl http://localhost:9200/security-findings/_count

# Check APIs
curl http://localhost:9200/api-catalog/_count

# Check gateways
curl http://localhost:9200/gateway-registry/_count

# Check predictions
curl http://localhost:9200/predictions/_count

# Check recommendations
curl http://localhost:9200/recommendations/_count
```

## Cleanup

To remove all mock data:

```bash
# Delete all indices (WARNING: This removes ALL data)
curl -X DELETE "localhost:9200/security-findings"
curl -X DELETE "localhost:9200/api-catalog"
curl -X DELETE "localhost:9200/gateway-registry"
curl -X DELETE "localhost:9200/predictions"
curl -X DELETE "localhost:9200/recommendations"
curl -X DELETE "localhost:9200/rate-limits"

# Recreate indices
python3 -c "from app.db.client import get_opensearch_client; from app.db.migrations import *; # Run migrations"
```

## Integration with Features

### Security Dashboard
Uses data from: `generate_mock_security_data.py`
- Displays vulnerability statistics
- Shows remediation progress
- Tracks security posture

### Prediction Timeline
Uses data from: `generate_timeline_demo_predictions.py`
- Historical prediction trends
- Failure forecasting
- Timeline visualization

### Optimization Recommendations
Uses data from: `generate_mock_optimizations.py`
- Performance insights
- Implementation tracking
- Impact analysis

### Rate Limiting Policies
Uses data from: `generate_mock_rate_limits.py`
- Consumer management
- Policy enforcement
- Quota tracking

## Best Practices

1. **Generate in Order**: Start with base data (gateways, APIs) before feature-specific data
2. **Use Realistic Counts**: 50-100 items per feature for demo purposes
3. **Enable Summaries**: Use `--summary` flag to verify data distribution
4. **Check Logs**: Monitor script output for errors
5. **Verify Data**: Use curl commands to confirm data was created

## Troubleshooting

### Script Fails to Connect to OpenSearch
```bash
# Check if OpenSearch is running
docker-compose ps opensearch

# Start if not running
docker-compose up -d opensearch
```

### No Data Appears in Frontend
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check API endpoints
curl http://localhost:8000/api/v1/security/posture
```

### Data Distribution Looks Wrong
```bash
# Regenerate with different seed
python3 scripts/generate_mock_security_data.py --count 50

# Check summary report
python3 scripts/generate_mock_security_data.py --summary
```

## Related Documentation

- [README.md](../../README.md) - Main project documentation
- [Architecture Documentation](../../docs/architecture.md) - System architecture
- [API Reference](../../docs/api-reference.md) - API endpoints
- [Security Mock Data Guide](README_SECURITY_MOCK_DATA.md) - Detailed security data guide
- [Security Demo Scenarios](SECURITY_DEMO_SCENARIOS.md) - Demo use cases

## Support

For issues or questions:
1. Check script output for error messages
2. Verify OpenSearch is running and accessible
3. Review related documentation
4. Check backend logs: `docker-compose logs backend`

---

**Made with Bob**