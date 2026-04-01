# Natural Language Query - Security Agent Integration

## Overview

This document describes the integration of the SecurityAgent with the Natural Language Query feature, bringing AI-enhanced security analysis to natural language queries.

## Changes Made

### Backend Changes

#### 1. QueryService Enhancement (`backend/app/services/query_service.py`)

**Added SecurityAgent Parameter:**
- Added `security_agent` parameter to `__init__` method
- Stores reference to SecurityAgent for security query enhancement

**New Method: `_enhance_with_security_agent()`**
- Enhances query results with AI-powered security analysis
- Analyzes top 3 results to avoid latency
- Implements caching with 5-minute TTL
- Returns vulnerability counts, compliance issues, and remediation plans

**Updated Query Execution:**
- Added security enhancement logic in `_execute_query()` method
- Triggers SecurityAgent analysis when `QueryType.SECURITY` is detected
- Seamlessly integrates with existing prediction and optimization enhancements

#### 2. Query API Endpoint (`backend/app/api/v1/query.py`)

**SecurityAgent Initialization:**
```python
security_agent = SecurityAgent(
    llm_service=llm_service,
    metrics_repository=metrics_repo,
)
```

**QueryService Integration:**
- Passes `security_agent` to QueryService constructor
- Manages agent lifecycle (enable/disable based on request)
- Maintains consistency with prediction and optimization agents

### Frontend Changes

#### 3. QueryResponse Component (`frontend/src/components/query/QueryResponse.tsx`)

**New Security Insights Display:**
- Added dedicated section for security agent insights
- Shows vulnerability counts (total and critical)
- Displays remediation plan preview
- Uses purple color scheme for security (🔒 icon)

**Enhanced Agent Insights UI:**
- Security insights: Purple theme with shield icon
- Prediction insights: Blue theme with lightning icon
- Optimization insights: Green theme with chart icon
- Consistent card-based layout for all agent types

## Features

### Security Query Enhancement

When users ask security-related questions, the system now:

1. **Detects Security Intent:** Classifies queries containing keywords like "security", "vulnerability", "threat", "risk"
2. **Analyzes APIs:** Runs comprehensive security analysis via SecurityAgent
3. **Provides AI Insights:** Returns:
   - Total vulnerability count
   - Critical vulnerability count
   - Compliance issues
   - AI-generated remediation plan
4. **Caches Results:** Stores analysis for 5 minutes to improve performance

### Example Queries

Users can now ask questions like:

- "Show me all critical vulnerabilities"
- "What are the security issues in my APIs?"
- "Which APIs have the most security risks?"
- "Show me APIs with compliance violations"
- "What security threats should I address first?"

### Response Format

Security-enhanced responses include:

```json
{
  "agent_insights": {
    "type": "security",
    "vulnerabilities": [...],
    "compliance_issues": [...],
    "remediation_plan": "AI-generated plan...",
    "total_vulnerabilities": 5,
    "critical_count": 2
  }
}
```

## Architecture

### Integration Flow

```
User Query
    ↓
QueryService.process_query()
    ↓
_classify_query_type() → QueryType.SECURITY
    ↓
_execute_query()
    ↓
_enhance_with_security_agent()
    ↓
SecurityAgent.analyze_api_security()
    ↓
Enhanced Results with AI Insights
    ↓
Frontend Display
```

### Agent Coordination

The Natural Language Query feature now coordinates three AI agents:

1. **PredictionAgent** - For prediction queries
2. **OptimizationAgent** - For performance queries  
3. **SecurityAgent** - For security queries

Each agent:
- Operates independently
- Uses the same caching mechanism
- Follows the same enhancement pattern
- Provides consistent response format

## Performance Considerations

### Caching Strategy

- **Cache Key Format:** `sec_{api_id}`
- **TTL:** 5 minutes (300 seconds)
- **Scope:** Per-API security analysis
- **Benefits:** Reduces redundant AI analysis calls

### Optimization

- **Limit Analysis:** Only top 3 results enhanced
- **Async Processing:** Non-blocking agent calls
- **Graceful Degradation:** Falls back to basic results if agent fails
- **Error Handling:** Logs warnings but doesn't break query flow

## Testing

### Manual Testing

Test security queries:

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend
cd frontend
npm run dev

# Test queries in UI:
# 1. "Show me critical vulnerabilities"
# 2. "What are the security risks?"
# 3. "Which APIs need security attention?"
```

### Expected Behavior

1. Query classified as `QueryType.SECURITY`
2. SecurityAgent analyzes relevant APIs
3. Response includes AI-generated insights
4. Frontend displays security cards with vulnerability counts
5. Remediation plans shown in purple-themed cards

## Configuration

### Environment Variables

No new environment variables required. Uses existing:
- `LLM_PROVIDER` - AI provider for SecurityAgent
- `LLM_MODEL` - Model for security analysis
- `OPENSEARCH_*` - Database connection for metrics

### Agent Availability

SecurityAgent is optional. If initialization fails:
- Query service continues without security enhancement
- Basic security queries still work
- Warning logged: "Failed to initialize AI agents"

## Future Enhancements

Potential improvements:

1. **Real-time Security Monitoring:** Stream security updates
2. **Custom Security Rules:** User-defined security policies
3. **Compliance Templates:** Pre-built compliance checks
4. **Security Trends:** Historical security analysis
5. **Automated Remediation:** One-click fix suggestions

## Related Documentation

- [`docs/query-service.md`](query-service.md) - Natural Language Query overview
- [`docs/architecture.md`](architecture.md) - System architecture
- [`backend/app/agents/security_agent.py`](../backend/app/agents/security_agent.py) - SecurityAgent implementation
- [`backend/app/services/query_service.py`](../backend/app/services/query_service.py) - QueryService implementation

## Changelog

### 2026-04-01
- ✅ Added SecurityAgent integration to QueryService
- ✅ Implemented `_enhance_with_security_agent()` method
- ✅ Updated query execution to handle security queries
- ✅ Enhanced frontend to display security insights
- ✅ Added security-themed UI components
- ✅ Implemented caching for security analysis

---

**Status:** ✅ Complete  
**Version:** 1.0.0  
**Last Updated:** 2026-04-01