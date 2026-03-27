# Security Mock Data Generator

This document explains how to use the security mock data generator for the API Intelligence Plane Security feature.

## Overview

The `generate_mock_security_data.py` script generates realistic mock security vulnerability data for testing and demonstration purposes. It creates vulnerabilities across different:

- **Severity levels**: Critical, High, Medium, Low
- **Vulnerability types**: Authentication, Authorization, Injection, Exposure, Configuration, Dependency
- **Status states**: Open, In Progress, Remediated, Accepted Risk, False Positive
- **Remediation tracking**: Actions, verification status, timestamps

## Use Case

This mock data supports the Security feature use case:
**"Monitor security vulnerabilities and track automated remediation"**

## Prerequisites

1. OpenSearch must be running and accessible
2. The `security-findings` index must exist (created by migration_005)
3. API data should exist in the `api-catalog` index (or mock API IDs will be generated)

## Usage

### Basic Usage

Generate 50 vulnerabilities (default):

```bash
cd backend
python scripts/generate_mock_security_data.py
```

### Custom Number of Vulnerabilities

Generate a specific number of vulnerabilities:

```bash
python scripts/generate_mock_security_data.py --count 100
```

### With Summary Report

Generate vulnerabilities and display a summary report:

```bash
python scripts/generate_mock_security_data.py --count 50 --summary
```

## Generated Data Structure

### Vulnerability Distribution

The script generates realistic distributions:

**By Severity:**
- Critical: 10%
- High: 25%
- Medium: 40%
- Low: 25%

**By Status:**
- Open: 30%
- In Progress: 25%
- Remediated: 35%
- Accepted Risk: 5%
- False Positive: 5%

**By Detection Method:**
- Automated Scan: 60%
- Manual Review: 30%
- External Report: 10%

### Vulnerability Types

1. **Authentication Issues**
   - Weak JWT token validation
   - Missing API key validation
   - Insecure basic authentication
   - OAuth2 token expiration issues

2. **Authorization Issues**
   - Missing RBAC
   - Broken object-level authorization
   - Privilege escalation
   - Insufficient function-level authorization

3. **Injection Vulnerabilities**
   - SQL injection
   - NoSQL injection
   - Command injection
   - LDAP injection
   - XXE injection

4. **Data Exposure**
   - Sensitive data in logs
   - API keys in response headers
   - Unencrypted PII data
   - Internal system details leaked

5. **Configuration Issues**
   - Missing rate limiting
   - CORS misconfiguration
   - Insecure TLS configuration
   - Default credentials
   - Debug mode in production

6. **Dependency Issues**
   - Vulnerable third-party libraries
   - Outdated frameworks
   - Known CVEs
   - End-of-life components

### Remediation Actions

Each vulnerability includes realistic remediation actions based on its type:

- **Automated remediation**: Configuration changes, policy applications
- **Manual remediation**: Code changes, security reviews
- **Upgrade remediation**: Dependency updates, patches
- **Configuration remediation**: Gateway policy updates

### Tracking Information

Each vulnerability includes:
- CVE identifiers (50% of vulnerabilities)
- CVSS scores (aligned with severity)
- Detection timestamps (within last 90 days)
- Affected endpoints
- Remediation actions with timestamps
- Verification status
- References to OWASP, NVD, CWE

## Example Output

```
INFO:__main__:Starting security mock data generation...
INFO:__main__:Found 10 existing APIs
INFO:__main__:Generating 50 mock vulnerabilities...
INFO:__main__:Generated 10/50 vulnerabilities...
INFO:__main__:Generated 20/50 vulnerabilities...
INFO:__main__:Generated 30/50 vulnerabilities...
INFO:__main__:Generated 40/50 vulnerabilities...
INFO:__main__:Generated 50/50 vulnerabilities...
INFO:__main__:Successfully generated 50 vulnerabilities
INFO:__main__:Security mock data generation complete!
INFO:__main__:Created 50 vulnerabilities

================================================================================
SECURITY MOCK DATA SUMMARY
================================================================================
Total Vulnerabilities: 50

By Severity:
  CRITICAL: 5
  HIGH: 13
  MEDIUM: 20
  LOW: 12

By Status:
  OPEN: 15
  IN_PROGRESS: 13
  REMEDIATED: 18
  ACCEPTED_RISK: 2
  FALSE_POSITIVE: 2

By Type:
  AUTHENTICATION: 9
  AUTHORIZATION: 8
  INJECTION: 8
  EXPOSURE: 8
  CONFIGURATION: 9
  DEPENDENCY: 8
================================================================================
```

## Integration with Security Feature

The generated data can be used to:

1. **Test Security Dashboard**: View vulnerability statistics and trends
2. **Test Remediation Tracker**: Monitor automated remediation progress
3. **Test Vulnerability Cards**: Display detailed vulnerability information
4. **Test Security Scanning**: Verify scan results and detection
5. **Test API Endpoints**: Query vulnerabilities by various filters
6. **Test Automated Remediation**: Simulate remediation workflows

## Viewing Generated Data

### Via API

```bash
# Get all vulnerabilities
curl http://localhost:8000/api/v1/security/vulnerabilities

# Get security posture
curl http://localhost:8000/api/v1/security/posture

# Get vulnerabilities by severity
curl http://localhost:8000/api/v1/security/vulnerabilities?severity=critical

# Get vulnerabilities by status
curl http://localhost:8000/api/v1/security/vulnerabilities?status=open
```

### Via Frontend

1. Navigate to the Security page in the frontend
2. View the Security Dashboard with statistics
3. Browse vulnerabilities in the Vulnerability Cards
4. Track remediation progress in the Remediation Tracker

### Via OpenSearch

```bash
# Query OpenSearch directly
curl -X GET "localhost:9200/security-findings/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match_all": {}}}'
```

## Cleanup

To remove all generated security data:

```bash
# Delete all documents from security-findings index
curl -X POST "localhost:9200/security-findings/_delete_by_query?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match_all": {}}}'
```

## Troubleshooting

### No APIs Found

If the script reports "No APIs available", either:
1. Run `generate_mock_data.py` first to create API data
2. The script will automatically generate mock API IDs

### OpenSearch Connection Error

Ensure OpenSearch is running:
```bash
docker-compose ps opensearch
```

If not running:
```bash
docker-compose up -d opensearch
```

### Index Not Found

Run the migration to create the security-findings index:
```bash
python -c "from app.db.migrations.migration_005_security_findings import create_security_findings_index; from app.db.client import get_opensearch_client; create_security_findings_index(get_opensearch_client().client)"
```

## Advanced Usage

### Generate Specific Scenarios

You can modify the script to generate specific test scenarios:

1. **High-severity vulnerabilities only**: Adjust `severity_distribution`
2. **All open vulnerabilities**: Adjust `status_distribution`
3. **Specific vulnerability types**: Filter `vulnerability_templates`

### Integration Testing

Use this script in integration tests:

```python
from scripts.generate_mock_security_data import SecurityMockDataGenerator

def test_security_feature():
    generator = SecurityMockDataGenerator()
    generator.generate_all(num_vulnerabilities=10)
    # Run your tests
```

## Related Files

- `backend/app/models/vulnerability.py` - Vulnerability data models
- `backend/app/services/security_service.py` - Security service logic
- `backend/app/api/v1/security.py` - Security API endpoints
- `backend/app/scheduler/security_jobs.py` - Automated scanning jobs
- `frontend/src/pages/Security.tsx` - Security dashboard UI

## Support

For issues or questions, refer to:
- Main README.md
- docs/api-reference.md
- docs/architecture.md

---

**Made with Bob**