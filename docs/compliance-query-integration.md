# Compliance Query Integration

## Overview

The Natural Language Query feature now includes full support for compliance-related queries. Users can ask questions about compliance violations, regulatory standards, and audit findings using natural language.

## Features

### Query Type: COMPLIANCE

A new query type `COMPLIANCE` has been added to support compliance-specific queries.

**Keywords**: compliance, regulatory, regulation, gdpr, hipaa, soc2, pci, iso, audit, violation

### Compliance Entity

A new entity type `compliance` has been added to the query system for identifying compliance-related queries.

**Keywords**: compliance, violation, violations, regulatory, audit

### AI-Enhanced Compliance Analysis

When the ComplianceAgent is available, compliance queries are automatically enhanced with:

- **Compliance Score**: Overall compliance posture (0-100)
- **Violation Analysis**: Detailed breakdown of violations by standard
- **Audit Evidence**: Supporting evidence for compliance findings
- **Standards Coverage**: Which compliance standards were checked (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
- **Critical Violations**: Count of critical compliance issues

## Example Queries

### Basic Compliance Queries

```
"Show me all compliance violations"
"What are the GDPR compliance issues?"
"Show me critical compliance violations"
"Which APIs have HIPAA violations?"
"Show me compliance violations from the last week"
```

### Advanced Compliance Queries

```
"What's the compliance status of payment-api?"
"Show me PCI-DSS violations that need immediate attention"
"Which APIs are non-compliant with SOC2?"
"Show me compliance violations by severity"
"What are the most common compliance issues?"
```

## Query Response Structure

### Without AI Enhancement

```json
{
  "query_id": "uuid",
  "query_text": "Show me GDPR violations",
  "query_type": "compliance",
  "response_text": "I found 5 GDPR compliance violations...",
  "confidence_score": 0.92,
  "results": {
    "data": [
      {
        "id": "violation-id",
        "api_id": "api-id",
        "compliance_standard": "gdpr",
        "violation_type": "gdpr_data_protection_by_design",
        "severity": "critical",
        "title": "Missing Data Protection Controls",
        "status": "open"
      }
    ],
    "count": 5,
    "execution_time": 245
  },
  "follow_up_queries": [
    "Show me critical compliance violations",
    "What's the remediation status?",
    "Which APIs have the most violations?"
  ]
}
```

### With AI Enhancement (ComplianceAgent)

```json
{
  "query_id": "uuid",
  "query_text": "Show me GDPR violations",
  "query_type": "compliance",
  "response_text": "Based on AI analysis, I found 5 GDPR compliance violations affecting 3 APIs. The ComplianceAgent has identified critical data protection gaps...",
  "confidence_score": 0.95,
  "results": {
    "data": [
      {
        "id": "violation-id",
        "api_id": "api-id",
        "compliance_standard": "gdpr",
        "violation_type": "gdpr_data_protection_by_design",
        "severity": "critical",
        "title": "Missing Data Protection Controls",
        "status": "open",
        "agent_insights": {
          "type": "compliance",
          "violations": [...],
          "standards_checked": ["gdpr", "hipaa", "soc2"],
          "compliance_score": 65,
          "audit_evidence": [...],
          "total_violations": 5,
          "critical_count": 2
        }
      }
    ],
    "count": 5,
    "execution_time": 1450
  },
  "follow_up_queries": [
    "What are the remediation steps for these violations?",
    "Show me the audit evidence for these findings",
    "Which compliance standards are most affected?"
  ]
}
```

## Follow-up Suggestions

### Compliance-Specific Follow-ups

When compliance agent insights are present:
- "What are the remediation steps for these violations?"
- "Show me the audit evidence for these findings"
- "Which compliance standards are most affected?"

### Entity-Based Follow-ups

For compliance entity queries:
- "Show me critical compliance violations"
- "What's the remediation status?"
- "Which APIs have the most violations?"
- "Show GDPR compliance violations"

## Integration Points

### Backend Components

1. **QueryType Enum** (`backend/app/models/query.py`)
   - Added `COMPLIANCE = "compliance"` type

2. **QueryService** (`backend/app/services/query_service.py`)
   - Added compliance keywords to `QUERY_TYPE_KEYWORDS`
   - Added compliance entity to `ENTITY_KEYWORDS`
   - Added `compliance_agent` parameter to `__init__`
   - Added `_enhance_with_compliance_agent()` method
   - Updated `_execute_query()` to handle compliance entities
   - Updated `_generate_response()` to include compliance insights
   - Updated `_generate_follow_ups()` with compliance suggestions

3. **Query API** (`backend/app/api/v1/query.py`)
   - Added `ComplianceRepository` import
   - Added `ComplianceAgent` initialization
   - Added compliance agent to QueryService initialization

4. **ComplianceAgent** (`backend/app/agents/compliance_agent.py`)
   - Provides AI-enhanced compliance analysis
   - Analyzes APIs for compliance with 5 standards
   - Generates audit evidence and remediation recommendations

## Configuration

### Environment Variables

```bash
# Enable AI agents (includes ComplianceAgent)
USE_AI_AGENTS=true

# LLM Configuration (required for ComplianceAgent)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=your-api-key
LLM_TEMPERATURE=0.7
```

### Disabling Compliance Agent

The ComplianceAgent can be disabled by setting `use_ai_agents=false` in the query request:

```python
POST /api/v1/query
{
  "query_text": "Show me compliance violations",
  "use_ai_agents": false
}
```

## Testing

### Manual Testing

```bash
# Run the test script
cd backend
python scripts/test_compliance_query.py
```

### API Testing

```bash
# Test compliance query via API
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Show me all GDPR compliance violations",
    "use_ai_agents": true
  }'
```

## Performance Considerations

### Caching

- Compliance agent results are cached for 5 minutes
- Cache key format: `comp_{api_id}`
- Reduces LLM costs and improves response times

### Result Limiting

- Only top 3 results are enhanced with agent insights
- Prevents excessive latency for large result sets
- Configurable via `AGENT_MAX_RESULTS` environment variable

### Graceful Degradation

- Queries work without ComplianceAgent if unavailable
- Standard compliance data is always returned
- Agent enhancement is optional and non-blocking

## Compliance Standards Supported

1. **GDPR** (General Data Protection Regulation)
   - Data protection by design
   - Security of processing
   - Records of processing
   - Data breach notification

2. **HIPAA** (Health Insurance Portability and Accountability Act)
   - Access control
   - Audit controls
   - Transmission security
   - Integrity controls

3. **SOC2** (Service Organization Control 2)
   - Security availability
   - System monitoring
   - Logical access
   - Confidentiality

4. **PCI-DSS** (Payment Card Industry Data Security Standard)
   - Network security
   - Encryption in transit
   - Access control
   - Monitoring and testing

5. **ISO 27001** (Information Security Management)
   - Access control
   - Cryptography
   - Operations security
   - Communications security

## Future Enhancements

### Planned Features

1. **Compliance Trends**: Track compliance posture over time
2. **Remediation Tracking**: Monitor remediation progress
3. **Audit Report Generation**: Generate compliance reports from queries
4. **Multi-Standard Analysis**: Compare compliance across standards
5. **Predictive Compliance**: Predict future compliance issues

### Experimental Features

1. **Voice Queries**: Natural language voice input for compliance queries
2. **Visual Dashboards**: Interactive compliance dashboards
3. **Automated Remediation**: AI-suggested remediation actions
4. **Compliance Scoring**: Real-time compliance score calculation

## Related Documentation

- [Query Service Documentation](query-service.md)
- [Compliance Service Documentation](../specs/001-api-intelligence-plane/spec.md#user-story-4)
- [ComplianceAgent Documentation](../backend/app/agents/compliance_agent.py)
- [Natural Language Query Security Integration](natural-language-query-security-integration.md)

---

**Last Updated**: 2026-04-03  
**Version**: 1.0.0  
**Status**: Implemented