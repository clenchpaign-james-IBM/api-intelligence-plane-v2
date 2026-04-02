# Compliance Monitoring and Audit Reporting

## Overview

The Compliance Monitoring feature provides continuous compliance monitoring with automated detection of regulatory violations and comprehensive audit reporting capabilities. This feature supports 5 major compliance standards with AI-driven analysis and scheduled reporting.

## Supported Compliance Standards

1. **GDPR** (General Data Protection Regulation)
   - 24 violation types covering data protection, privacy, and consent
   
2. **HIPAA** (Health Insurance Portability and Accountability Act)
   - 24 violation types covering healthcare data security and privacy
   
3. **SOC2** (Service Organization Control 2)
   - 24 violation types covering security, availability, and confidentiality
   
4. **PCI-DSS** (Payment Card Industry Data Security Standard)
   - 24 violation types covering payment card data security
   
5. **ISO 27001** (Information Security Management)
   - 24 violation types covering information security controls

## Architecture

### Backend Components

#### 1. Pydantic Models (`backend/app/models/compliance.py`)

**ComplianceViolation Model**:
```python
class ComplianceViolation(BaseModel):
    id: str
    api_id: str
    api_name: str
    compliance_standard: ComplianceStandard  # GDPR, HIPAA, SOC2, PCI_DSS, ISO_27001
    violation_type: str
    severity: ComplianceSeverity  # critical, high, medium, low
    status: ComplianceStatus  # open, in_progress, resolved, false_positive
    description: str
    detected_at: datetime
    last_checked: datetime
    remediation_deadline: Optional[datetime]
    remediation_actions: List[str]
    affected_endpoints: List[str]
    evidence: Dict[str, Any]
    metadata: Dict[str, Any]
```

#### 2. Repository Layer (`backend/app/db/repositories/compliance_repository.py`)

**Key Methods**:
- `create()`: Store new compliance violations
- `get_by_id()`: Retrieve specific violation
- `get_by_api()`: Get all violations for an API
- `get_by_standard()`: Filter by compliance standard
- `get_by_severity()`: Filter by severity level
- `get_by_status()`: Filter by remediation status
- `update_status()`: Update violation status
- `generate_audit_report_data()`: Aggregate data for audit reports

**Aggregation Support**:
```python
# Returns comprehensive statistics
{
    "summary": {
        "total_violations": 150,
        "open_violations": 45,
        "remediated_violations": 105,
        "remediation_rate": 70.0
    },
    "by_severity": {"critical": 10, "high": 20, "medium": 50, "low": 70},
    "by_status": {"open": 45, "in_progress": 15, "resolved": 90},
    "by_standard": {"GDPR": 30, "HIPAA": 25, "SOC2": 40, "PCI_DSS": 30, "ISO_27001": 25}
}
```

#### 3. Service Layer (`backend/app/services/compliance_service.py`)

**ComplianceService Features**:
- **Hybrid Detection**: Rule-based + AI-enhanced compliance analysis
- **Multi-Source Analysis**: API specs, configurations, traffic patterns, security findings
- **Scheduled Scanning**: Automated 24-hour compliance checks
- **Audit Report Generation**: Comprehensive compliance reports with executive summaries

**Key Methods**:
```python
async def scan_api_compliance(api_id: str, standards: List[str]) -> List[ComplianceViolation]
async def get_compliance_posture(filters: dict) -> CompliancePosture
async def generate_audit_report(request: AuditReportRequest) -> AuditReport
```

#### 4. Agent Layer (`backend/app/agents/compliance_agent.py`)

**ComplianceAgent (LangChain/LangGraph)**:
- AI-driven compliance analysis using LLM
- Context-aware violation detection
- Natural language explanations
- Remediation recommendations

**Workflow**:
1. Analyze API configuration and traffic patterns
2. Check against compliance standard requirements
3. Identify violations with evidence
4. Generate remediation actions
5. Provide executive summary

#### 5. Scheduler (`backend/app/scheduler/compliance_jobs.py`)

**Automated Compliance Scanning**:
- Runs every 24 hours
- Scans all APIs for all standards
- Updates violation status
- Triggers alerts for critical violations

#### 6. REST API Endpoints (`backend/app/api/v1/compliance.py`)

**Available Endpoints**:

```
GET /api/v1/compliance/violations
  - Query parameters: api_id, standard, severity, status, limit, offset
  - Returns: List of compliance violations with pagination

GET /api/v1/compliance/violations/{violation_id}
  - Returns: Detailed violation information

PUT /api/v1/compliance/violations/{violation_id}/status
  - Body: { "status": "resolved", "notes": "..." }
  - Returns: Updated violation

GET /api/v1/compliance/posture
  - Query parameters: api_id, standard, start_date, end_date
  - Returns: Compliance posture with statistics

POST /api/v1/compliance/reports/audit
  - Body: AuditReportRequest
  - Returns: Comprehensive audit report

GET /api/v1/compliance/reports/audit/{report_id}
  - Returns: Previously generated audit report

POST /api/v1/compliance/scan
  - Body: { "api_id": "...", "standards": [...] }
  - Returns: Scan results with detected violations
```

### MCP Server (`mcp-servers/compliance_server.py`)

**Available Tools**:

1. **scan_api_compliance**
   - Scans API for compliance violations
   - Parameters: api_id, standards (optional)
   - Returns: List of detected violations

2. **generate_audit_report**
   - Generates comprehensive audit report
   - Parameters: report_type, standards, api_ids, period
   - Returns: Audit report with executive summary

3. **get_compliance_posture**
   - Retrieves compliance posture statistics
   - Parameters: api_id, standard, date_range
   - Returns: Compliance metrics and trends

### Frontend Components

#### 1. Compliance Page (`frontend/src/pages/Compliance.tsx`)

**Features**:
- Tabbed interface: Violations, Audit Reports, Posture
- Real-time violation list with filtering
- Interactive compliance dashboard
- Audit report generation and export

**Filters**:
- By compliance standard (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
- By severity (critical, high, medium, low)
- By status (open, in_progress, resolved, false_positive)
- By API
- By date range

#### 2. ComplianceDashboard Component

**Displays**:
- Total violations count
- Open violations (clickable → filters to open)
- Resolved violations (clickable → filters to resolved)
- Violations by standard (bar chart)
- Violations by severity (pie chart)
- Remediation rate trend
- Critical violations requiring immediate attention

#### 3. ComplianceViolationCard Component

**Shows**:
- Violation type and description
- Compliance standard badge
- Severity indicator
- Status badge
- Affected endpoints
- Remediation actions
- Evidence details
- Status update controls

#### 4. AuditReportGenerator Component

**Capabilities**:
- Report type selection (comprehensive, standard-specific, API-specific)
- Standard selection (multi-select)
- API selection (multi-select with search)
- Date range picker
- Include/exclude resolved violations
- Export formats: PDF, HTML, JSON

**Generated Report Sections**:
- Report metadata (ID, period, generation date)
- Executive summary (AI-generated)
- Compliance posture summary
- Violations by severity
- Violations by standard
- Remediation status
- Recommendations

## Usage Examples

### 1. Scan API for Compliance

```bash
# Via REST API
curl -X POST http://localhost:8000/api/v1/compliance/scan \
  -H "Content-Type: application/json" \
  -d '{
    "api_id": "api-123",
    "standards": ["GDPR", "HIPAA"]
  }'

# Via MCP Tool
{
  "tool": "scan_api_compliance",
  "arguments": {
    "api_id": "api-123",
    "standards": ["GDPR", "HIPAA"]
  }
}
```

### 2. Get Compliance Posture

```bash
# Via REST API
curl "http://localhost:8000/api/v1/compliance/posture?standard=GDPR&start_date=2024-01-01"

# Via MCP Tool
{
  "tool": "get_compliance_posture",
  "arguments": {
    "standard": "GDPR",
    "start_date": "2024-01-01"
  }
}
```

### 3. Generate Audit Report

```bash
# Via REST API
curl -X POST http://localhost:8000/api/v1/compliance/reports/audit \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "comprehensive",
    "standards": ["GDPR", "HIPAA", "SOC2"],
    "period_start": "2024-01-01",
    "period_end": "2024-03-31",
    "include_resolved": true
  }'

# Via MCP Tool
{
  "tool": "generate_audit_report",
  "arguments": {
    "report_type": "comprehensive",
    "standards": ["GDPR", "HIPAA", "SOC2"],
    "period_start": "2024-01-01",
    "period_end": "2024-03-31"
  }
}
```

### 4. Update Violation Status

```bash
curl -X PUT http://localhost:8000/api/v1/compliance/violations/viol-123/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "notes": "Implemented data encryption and access controls"
  }'
```

## Configuration

### Environment Variables

```bash
# Compliance scanning schedule (cron format)
COMPLIANCE_SCAN_SCHEDULE="0 0 * * *"  # Daily at midnight

# AI enhancement for compliance analysis
COMPLIANCE_AI_ENABLED=true

# Compliance standards to monitor
COMPLIANCE_STANDARDS="GDPR,HIPAA,SOC2,PCI_DSS,ISO_27001"

# Alert thresholds
COMPLIANCE_CRITICAL_ALERT_THRESHOLD=5
COMPLIANCE_HIGH_ALERT_THRESHOLD=10
```

### OpenSearch Index

**Index Name**: `compliance-violations`

**Mapping**:
```json
{
  "mappings": {
    "properties": {
      "api_id": {"type": "keyword"},
      "compliance_standard": {"type": "keyword"},
      "violation_type": {"type": "keyword"},
      "severity": {"type": "keyword"},
      "status": {"type": "keyword"},
      "detected_at": {"type": "date"},
      "last_checked": {"type": "date"},
      "remediation_deadline": {"type": "date"}
    }
  }
}
```

## Testing

### Integration Tests

**Location**: `tests/integration/test_compliance_scanning.py`

**Test Cases**:
- Compliance violation detection
- Multi-standard scanning
- Violation status updates
- Compliance posture calculation
- Audit report generation

### End-to-End Tests

**Location**: `tests/e2e/test_audit_workflow.py`

**Test Scenarios**:
- Complete audit workflow
- Report generation and export
- Violation remediation tracking
- Compliance posture monitoring

### Manual Testing

1. **Navigate to Compliance Page**: http://localhost:3000/compliance
2. **View Violations**: Check violations list with filters
3. **Generate Report**: Use Audit Reports tab to generate comprehensive report
4. **Update Status**: Mark violations as resolved
5. **Monitor Posture**: View compliance dashboard metrics

## Troubleshooting

### Common Issues

**1. No violations detected**
- Verify APIs are registered in the system
- Check compliance scanning scheduler is running
- Ensure OpenSearch index exists and is accessible

**2. Audit report generation fails**
- Check date range is valid
- Verify selected standards have violations
- Ensure sufficient data exists for the period

**3. Frontend shows "Failed to load compliance data"**
- Verify backend is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`
- Ensure OpenSearch is healthy: `curl http://localhost:9200/_cluster/health`

**4. MCP tools not working**
- Verify MCP server is running: `docker-compose ps compliance-server`
- Check MCP server logs: `docker-compose logs compliance-server`
- Test MCP connection: Use MCP client test script

## Performance Considerations

### Optimization Strategies

1. **Batch Scanning**: Scan multiple APIs in parallel
2. **Caching**: Cache compliance posture for 5 minutes
3. **Incremental Updates**: Only scan changed APIs
4. **Aggregation Optimization**: Use OpenSearch aggregations for statistics
5. **Report Caching**: Cache generated reports for 1 hour

### Scalability

- **Horizontal Scaling**: Run multiple compliance scanner instances
- **Database Sharding**: Partition violations by compliance standard
- **Async Processing**: Use background jobs for large scans
- **Rate Limiting**: Limit concurrent scans to prevent overload

## Security Considerations

1. **Access Control**: Restrict compliance data access to authorized users
2. **Audit Logging**: Log all compliance-related operations
3. **Data Encryption**: Encrypt sensitive violation evidence
4. **Retention Policy**: Retain compliance data for regulatory periods
5. **Export Security**: Secure audit report exports with encryption

## Compliance Standards Details

### GDPR Violation Types (24 types)
- Data processing without consent
- Inadequate data protection measures
- Missing privacy policy
- Lack of data subject rights implementation
- Insufficient data breach notification
- And 19 more...

### HIPAA Violation Types (24 types)
- Unauthorized PHI access
- Inadequate access controls
- Missing encryption for PHI
- Insufficient audit logging
- Lack of business associate agreements
- And 19 more...

### SOC2 Violation Types (24 types)
- Inadequate security controls
- Missing change management
- Insufficient monitoring
- Lack of incident response
- Inadequate access reviews
- And 19 more...

### PCI-DSS Violation Types (24 types)
- Unencrypted cardholder data
- Weak access controls
- Missing network segmentation
- Insufficient logging
- Lack of vulnerability management
- And 19 more...

### ISO 27001 Violation Types (24 types)
- Missing information security policy
- Inadequate risk assessment
- Insufficient asset management
- Lack of access control policy
- Missing incident management
- And 19 more...

## Future Enhancements

1. **Automated Remediation**: Auto-fix common compliance violations
2. **Compliance Scoring**: Calculate overall compliance score
3. **Trend Analysis**: Predict compliance risks
4. **Integration**: Connect with GRC platforms
5. **Custom Standards**: Support custom compliance frameworks
6. **Real-time Alerts**: Immediate notifications for critical violations
7. **Compliance Dashboard**: Executive-level compliance overview
8. **Remediation Workflows**: Guided remediation processes

## References

- [GDPR Official Text](https://gdpr-info.eu/)
- [HIPAA Compliance Guide](https://www.hhs.gov/hipaa/index.html)
- [SOC2 Framework](https://www.aicpa.org/soc2)
- [PCI-DSS Standards](https://www.pcisecuritystandards.org/)
- [ISO 27001 Overview](https://www.iso.org/isoiec-27001-information-security.html)

---

**Last Updated**: 2026-04-02
**Version**: 1.0.0
**Status**: Production Ready