# Security Feature Demo Scenarios

This guide provides specific scenarios and use cases for demonstrating the Security feature using the generated mock data.

## Quick Demo Setup

```bash
# 1. Ensure OpenSearch is running
docker-compose up -d opensearch

# 2. Generate security mock data
cd backend
python3 scripts/generate_mock_security_data.py --count 50 --summary

# 3. Start the backend
uvicorn app.main:app --reload

# 4. Start the frontend
cd ../frontend
npm run dev
```

## Demo Scenarios

### Scenario 1: Security Dashboard Overview

**Use Case**: Monitor overall security posture

**Steps**:
1. Navigate to Security page in frontend
2. View Security Dashboard showing:
   - Total vulnerabilities count
   - Severity breakdown (Critical, High, Medium, Low)
   - Status distribution (Open, In Progress, Remediated)
   - Risk score and risk level
   - Remediation rate percentage

**API Endpoint**:
```bash
curl http://localhost:8000/api/v1/security/posture
```

**Expected Result**: Dashboard displays comprehensive security metrics with visual charts

---

### Scenario 2: Critical Vulnerabilities Requiring Immediate Attention

**Use Case**: Identify and prioritize critical security issues

**Steps**:
1. Filter vulnerabilities by severity: "Critical"
2. Review list of critical vulnerabilities
3. Note affected APIs and endpoints
4. Check remediation status

**API Endpoint**:
```bash
curl "http://localhost:8000/api/v1/security/vulnerabilities?severity=critical"
```

**Expected Result**: List of ~5 critical vulnerabilities with details

---

### Scenario 3: Track Automated Remediation Progress

**Use Case**: Monitor automated remediation workflow

**Steps**:
1. View vulnerabilities with status "In Progress"
2. Examine remediation actions taken
3. Check verification status
4. Review timeline of remediation steps

**API Endpoint**:
```bash
curl "http://localhost:8000/api/v1/security/vulnerabilities?status=in_progress"
```

**Expected Result**: ~12-13 vulnerabilities showing active remediation with action history

---

### Scenario 4: Verify Successfully Remediated Issues

**Use Case**: Confirm remediation effectiveness

**Steps**:
1. Filter by status: "Remediated"
2. Review remediation actions performed
3. Check verification status (Verified/Pending)
4. Note time to remediation

**API Endpoint**:
```bash
curl "http://localhost:8000/api/v1/security/vulnerabilities?status=remediated"
```

**Expected Result**: ~17-18 remediated vulnerabilities with completed actions

---

### Scenario 5: Authentication & Authorization Issues

**Use Case**: Review access control vulnerabilities

**Steps**:
1. Filter by vulnerability type: "Authentication" or "Authorization"
2. Review specific issues:
   - Weak JWT validation
   - Missing RBAC
   - Broken authorization
3. Check automated remediation recommendations

**API Endpoint**:
```bash
# Authentication issues
curl "http://localhost:8000/api/v1/security/vulnerabilities" | jq '.[] | select(.vulnerability_type=="authentication")'

# Authorization issues
curl "http://localhost:8000/api/v1/security/vulnerabilities" | jq '.[] | select(.vulnerability_type=="authorization")'
```

**Expected Result**: Multiple authentication/authorization vulnerabilities with remediation plans

---

### Scenario 6: Injection Vulnerabilities

**Use Case**: Identify and remediate injection attacks

**Steps**:
1. Filter by type: "Injection"
2. Review SQL, NoSQL, Command injection issues
3. Check affected endpoints
4. Review remediation actions (input validation, parameterized queries)

**API Endpoint**:
```bash
curl "http://localhost:8000/api/v1/security/vulnerabilities" | jq '.[] | select(.vulnerability_type=="injection")'
```

**Expected Result**: ~6-8 injection vulnerabilities with code-level remediation actions

---

### Scenario 7: Configuration Security Issues

**Use Case**: Fix security misconfigurations

**Steps**:
1. Filter by type: "Configuration"
2. Review issues:
   - Missing rate limiting
   - CORS misconfiguration
   - Insecure TLS settings
3. Note automated remediation (policy application)

**API Endpoint**:
```bash
curl "http://localhost:8000/api/v1/security/vulnerabilities" | jq '.[] | select(.vulnerability_type=="configuration")'
```

**Expected Result**: Configuration issues with automated policy-based remediation

---

### Scenario 8: Dependency Vulnerabilities

**Use Case**: Track vulnerable dependencies

**Steps**:
1. Filter by type: "Dependency"
2. Review CVE identifiers
3. Check CVSS scores
4. Review upgrade recommendations

**API Endpoint**:
```bash
curl "http://localhost:8000/api/v1/security/vulnerabilities" | jq '.[] | select(.vulnerability_type=="dependency")'
```

**Expected Result**: Dependency vulnerabilities with CVE IDs and upgrade paths

---

### Scenario 9: API-Specific Security Analysis

**Use Case**: Review security for a specific API

**Steps**:
1. Select an API from the list
2. View all vulnerabilities for that API
3. Check severity distribution
4. Review remediation progress

**API Endpoint**:
```bash
# Replace {api_id} with actual API ID
curl "http://localhost:8000/api/v1/security/vulnerabilities?api_id={api_id}"
```

**Expected Result**: All vulnerabilities affecting the selected API

---

### Scenario 10: Remediation Timeline Analysis

**Use Case**: Analyze remediation efficiency

**Steps**:
1. View remediated vulnerabilities
2. Compare detected_at vs remediated_at timestamps
3. Calculate average time to remediation
4. Identify patterns in remediation speed

**API Endpoint**:
```bash
curl "http://localhost:8000/api/v1/security/posture" | jq '.avg_remediation_time_ms'
```

**Expected Result**: Average remediation time in milliseconds

---

## Advanced Demo Features

### Trigger Automated Remediation

```bash
# Get a remediable vulnerability ID
VULN_ID=$(curl -s "http://localhost:8000/api/v1/security/vulnerabilities?status=open" | jq -r '.[0].id')

# Trigger remediation
curl -X POST "http://localhost:8000/api/v1/security/vulnerabilities/${VULN_ID}/remediate"
```

### Verify Remediation

```bash
# Verify a remediated vulnerability
curl -X POST "http://localhost:8000/api/v1/security/vulnerabilities/${VULN_ID}/verify"
```

### Scan Specific API

```bash
# Trigger security scan for specific API
curl -X POST "http://localhost:8000/api/v1/security/scan" \
  -H "Content-Type: application/json" \
  -d '{"api_id": "your-api-id", "use_ai_enhancement": true}'
```

## Key Metrics to Highlight

1. **Total Vulnerabilities**: ~50 across all severity levels
2. **Remediation Rate**: ~35-40% (showing active remediation)
3. **Risk Score**: Calculated based on severity distribution
4. **Average Remediation Time**: Varies by vulnerability type
5. **Automated vs Manual**: ~60% can be automatically remediated

## Demo Talking Points

### For Security Teams
- "Continuous automated scanning detects vulnerabilities across all APIs"
- "AI-enhanced analysis provides context and prioritization"
- "Automated remediation reduces manual effort by 60%"
- "Verification ensures fixes remain effective over time"

### For DevOps Teams
- "Integration with existing API gateways for policy enforcement"
- "Automated remediation applies fixes at gateway level"
- "No code changes required for configuration-based fixes"
- "Track remediation progress in real-time"

### For Management
- "Comprehensive security posture visibility"
- "Proactive vulnerability management reduces risk"
- "Automated workflows improve efficiency"
- "Compliance-ready audit trail of all security actions"

## Troubleshooting

### No Vulnerabilities Showing
```bash
# Check if data was generated
curl http://localhost:9200/security-findings/_count

# Regenerate if needed
python3 scripts/generate_mock_security_data.py --count 50
```

### API Errors
```bash
# Check backend logs
docker-compose logs backend

# Verify OpenSearch is running
curl http://localhost:9200/_cluster/health
```

### Frontend Not Displaying Data
```bash
# Check browser console for errors
# Verify API endpoint is accessible
curl http://localhost:8000/api/v1/security/posture
```

---

**Made with Bob**