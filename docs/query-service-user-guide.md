# Query Service User Guide

**Version**: 2.0 (Multi-Index Support)  
**Last Updated**: 2026-04-21

---

## Overview

The Query Service enables natural language querying of your API management platform. Ask questions in plain English and get intelligent responses with data from multiple sources.

### What's New in v2.0

- 🎯 **Multi-index queries**: Ask about relationships between APIs, gateways, metrics, and more
- 💬 **Context-aware follow-ups**: Reference previous results with "these", "those", "them"
- 🚀 **Improved accuracy**: 95%+ success rate for follow-up questions
- ⚡ **Faster responses**: 30-50% reduction in query latency
- 📊 **Better insights**: Automatic relationship detection and data joining

---

## Getting Started

### Basic Query Structure

Simply type your question in natural language:

```
"Show me all active APIs"
"What are the recent predictions?"
"Which APIs have critical vulnerabilities?"
```

### Query Types

The system automatically detects your intent and classifies queries into types:

| Type | Keywords | Example |
|------|----------|---------|
| **Status** | status, health, active, current | "Show me API status" |
| **Trend** | trend, over time, history, pattern | "API traffic trends last week" |
| **Prediction** | predict, forecast, future, will | "Predict API failures" |
| **Security** | security, vulnerability, threat | "Show critical vulnerabilities" |
| **Performance** | performance, latency, slow, fast | "Which APIs are slow?" |
| **Comparison** | compare, versus, vs, difference | "Compare API performance" |
| **Compliance** | compliance, violation, regulatory | "Show GDPR violations" |

---

## Query Examples

### Single-Entity Queries

**APIs**:
```
"Show me all APIs"
"List payment APIs"
"Which APIs are deprecated?"
"Show me APIs created last month"
```

**Gateways**:
```
"Show all gateways"
"Which gateways are offline?"
"List gateways in production"
```

**Metrics**:
```
"Show API metrics"
"What's the average response time?"
"Show error rates for today"
```

**Security**:
```
"Show all vulnerabilities"
"List critical security issues"
"Which CVEs are unpatched?"
```

**Predictions**:
```
"Show recent predictions"
"What failures are predicted?"
"Show high-confidence predictions"
```

**Recommendations**:
```
"Show optimization recommendations"
"List rate limiting suggestions"
"What caching recommendations exist?"
```

**Compliance**:
```
"Show compliance violations"
"List GDPR violations"
"Which APIs are non-compliant?"
```

### Multi-Entity Queries

**APIs + Vulnerabilities**:
```
"Show me APIs with critical vulnerabilities"
"Which payment APIs have security issues?"
"List APIs affected by CVE-2024-1234"
```

**APIs + Metrics**:
```
"Show me APIs with high latency"
"Which APIs have error rates above 5%?"
"List slow payment APIs"
```

**APIs + Predictions**:
```
"Show me APIs predicted to fail"
"Which APIs will have high traffic?"
"List APIs with failure predictions"
```

**Gateways + APIs**:
```
"Show me APIs on gateway-1"
"Which gateways have the most APIs?"
"List APIs per gateway"
```

**APIs + Recommendations**:
```
"Show me APIs with rate limiting recommendations"
"Which APIs need caching?"
"List optimization suggestions for payment APIs"
```

### Follow-up Queries (Context-Aware)

The system remembers your previous queries and understands references:

**Example Conversation 1**:
```
You: "Which APIs are insecure?"
Bot: [Returns list of APIs with vulnerabilities]

You: "Show me their performance metrics"
Bot: [Automatically queries metrics for those specific APIs]

You: "What recommendations exist for them?"
Bot: [Shows recommendations for the same APIs]
```

**Example Conversation 2**:
```
You: "Show me payment APIs"
Bot: [Returns payment APIs]

You: "Which of these have high latency?"
Bot: [Filters to payment APIs with high latency]

You: "Show me the vulnerabilities affecting them"
Bot: [Shows vulnerabilities for high-latency payment APIs]
```

**Reference Keywords**:
- **Demonstrative**: "these", "those", "this", "that"
- **Pronoun**: "them", "it", "they", "their"
- **Implicit**: "for the above", "for the previous"

---

## Advanced Features

### Time Range Queries

Specify time ranges in natural language:

```
"Show me API metrics from last 7 days"
"List vulnerabilities discovered this month"
"Show predictions for next week"
"API traffic from January to March"
```

### Filtering

Add filters to narrow results:

```
"Show me critical vulnerabilities"
"List active APIs in production"
"Show high-severity compliance violations"
"APIs with status code 500"
```

### Aggregations

Ask for summaries and statistics:

```
"How many APIs are active?"
"What's the average API response time?"
"Count vulnerabilities by severity"
"Show API distribution by gateway"
```

### Comparisons

Compare entities or metrics:

```
"Compare payment APIs vs auth APIs"
"Show latency difference between gateways"
"Compare this week's traffic to last week"
```

---

## Best Practices

### 1. Start Broad, Then Narrow

```
✅ Good:
"Show me all APIs"
→ "Which of these have vulnerabilities?"
→ "Show me the critical ones"

❌ Less Effective:
"Show me critical vulnerabilities for payment APIs on gateway-1 from last week"
```

### 2. Use Natural Language

```
✅ Good:
"Which APIs are slow?"
"Show me security issues"

❌ Unnecessary:
"SELECT * FROM apis WHERE latency > 1000"
"api.status == 'active' AND severity == 'critical'"
```

### 3. Leverage Context

```
✅ Good:
"Show me payment APIs"
→ "What's their average response time?"
→ "Show me the slowest ones"

❌ Repetitive:
"Show me payment APIs"
→ "Show me response time for payment APIs"
→ "Show me slowest payment APIs"
```

### 4. Be Specific When Needed

```
✅ Good:
"Show me APIs with CVE-2024-1234"
"List APIs on gateway-prod-1"
"Show metrics from March 15 to March 20"

❌ Too Vague:
"Show me some APIs"
"List things"
```

---

## Understanding Responses

### Response Format

Responses include:

1. **Summary**: Brief overview of results
2. **Key Findings**: Bullet points with important data
3. **Data**: Structured results
4. **Follow-up Suggestions**: Related questions you can ask

**Example Response**:
```markdown
Found **15 APIs** with critical vulnerabilities.

## Key Findings
- **Payment API v2**: 3 critical CVEs
- **Auth Service**: 2 critical CVEs
- **User API**: 1 critical CVE

Try asking about specific aspects for more details.

Suggested follow-ups:
- Show me the performance metrics for these APIs
- What recommendations exist for these APIs?
- Show me the remediation status
```

### Confidence Scores

Each query has a confidence score (0-1):

- **0.9-1.0**: High confidence, results are very accurate
- **0.7-0.9**: Good confidence, results are reliable
- **0.5-0.7**: Moderate confidence, verify results
- **<0.5**: Low confidence, consider rephrasing

### Execution Time

Response includes execution time:
- **<1s**: Excellent
- **1-2s**: Good
- **2-5s**: Acceptable
- **>5s**: Consider simplifying query

---

## Troubleshooting

### "I couldn't find any results"

**Possible Causes**:
- No data matches your criteria
- Filters are too restrictive
- Time range is outside available data

**Solutions**:
- Broaden your search criteria
- Remove some filters
- Check time range
- Try a related query

### "I encountered an error"

**Possible Causes**:
- Service temporarily unavailable
- Query too complex
- Invalid reference in follow-up

**Solutions**:
- Try again in a moment
- Simplify your query
- Start a new conversation
- Contact support if persistent

### Context Not Working

**Possible Causes**:
- Session expired (30 minutes)
- Too many queries in between
- Ambiguous reference

**Solutions**:
- Repeat the original query
- Be more specific with references
- Use explicit entity names

---

## API Integration

### REST API

**Endpoint**: `POST /api/v1/queries`

**Request**:
```json
{
  "query_text": "Show me all active APIs",
  "session_id": "uuid-here",
  "user_id": "optional-user-id"
}
```

**Response**:
```json
{
  "id": "query-uuid",
  "session_id": "session-uuid",
  "query_text": "Show me all active APIs",
  "query_type": "status",
  "interpreted_intent": {
    "action": "list",
    "entities": ["api"],
    "filters": {"status": "active"}
  },
  "results": {
    "data": [...],
    "count": 42,
    "execution_time": 1250
  },
  "response_text": "Found 42 active APIs...",
  "confidence_score": 0.95,
  "execution_time_ms": 1250,
  "follow_up_queries": [
    "Show me the performance metrics for these APIs",
    "Are there any predictions for these APIs?",
    "What security vulnerabilities affect these APIs?"
  ],
  "created_at": "2026-04-21T07:00:00Z"
}
```

### Performance Metrics

**Endpoint**: `GET /api/v1/queries/metrics`

**Response**:
```json
{
  "total_queries": 1000,
  "successful_queries": 950,
  "failed_queries": 50,
  "avg_execution_time_ms": 1850,
  "multi_index_queries": 300,
  "context_aware_queries": 200,
  "success_rate": 95.0,
  "failure_rate": 5.0,
  "multi_index_usage": 30.0,
  "context_aware_usage": 20.0
}
```

---

## Limitations

### Current Limitations

1. **Session Timeout**: 30 minutes of inactivity
2. **Context Window**: Last 5 queries per session
3. **Result Limit**: Maximum 50 results per query
4. **Query Complexity**: Maximum 3-level nested queries
5. **Time Range**: Limited to available data retention (90 days)

### Unsupported Queries

- Data modification (updates, deletes)
- Administrative operations
- Real-time streaming queries
- Queries requiring external data sources

---

## Tips & Tricks

### 1. Use Follow-up Suggestions

The system provides intelligent follow-up suggestions after each query. These are optimized for your current context.

### 2. Combine Multiple Filters

```
"Show me critical vulnerabilities in payment APIs from last week"
```

### 3. Ask for Explanations

```
"Why is API-123 slow?"
"What's causing the high error rate?"
"Explain the prediction for API-456"
```

### 4. Request Specific Formats

```
"Show me API metrics as a table"
"List vulnerabilities by severity"
"Group recommendations by API"
```

### 5. Use Relative Time

```
"last 7 days"
"this month"
"yesterday"
"last hour"
```

---

## Support

### Getting Help

- **Documentation**: [docs/enterprise-nlq-multi-index-analysis.md](./enterprise-nlq-multi-index-analysis.md)
- **Performance Report**: [docs/query-service-performance-report.md](./query-service-performance-report.md)
- **API Reference**: `/api/docs` (Swagger UI)

### Feedback

Help us improve! Rate your query experience and provide feedback:
- Thumbs up/down on responses
- Report inaccurate results
- Suggest new query types

---

## Changelog

### Version 2.0 (2026-04-21)

**New Features**:
- Multi-index query support
- Context-aware follow-up queries
- Enhanced intent extraction
- Query planning and optimization
- Performance tracking

**Improvements**:
- 95%+ success rate for follow-up queries
- 30-50% reduction in query latency
- Better accuracy for multi-entity queries
- Improved error handling

**Bug Fixes**:
- Fixed context resolution for ambiguous references
- Improved time range parsing
- Better handling of complex filters

### Version 1.0 (2026-03-01)

- Initial release
- Basic natural language query support
- Single-index queries
- LLM-powered intent extraction

---

**Last Updated**: 2026-04-21  
**Version**: 2.0  
**Status**: Production Ready

<!-- Made with Bob -->