# Query Service Documentation

## Overview

The Query Service provides a natural language interface for querying API intelligence data. It integrates with AI agents (PredictionAgent, OptimizationAgent, and SecurityAgent) to provide enhanced insights for prediction, performance, and security queries.

## Architecture

### Components

1. **QueryService**: Core service for processing natural language queries
2. **PredictionAgent**: AI agent for enhanced prediction analysis
3. **OptimizationAgent**: AI agent for enhanced performance optimization
4. **SecurityAgent**: AI agent for enhanced security analysis
5. **LLMService**: Language model service for NLP tasks
5. **Repositories**: Data access layer for APIs, metrics, predictions, and recommendations

### Query Processing Flow

```
User Query → Intent Classification → Intent Extraction (LLM) → 
OpenSearch Query Generation → Query Execution → 
Agent Enhancement (if applicable) → Response Generation (LLM) → 
Follow-up Suggestions → Response
```

## Agent Integration

### Overview

The Query Service can optionally integrate with AI agents to provide deeper insights for specific query types:

- **Prediction Queries**: Enhanced with PredictionAgent analysis
- **Performance Queries**: Enhanced with OptimizationAgent recommendations
- **Security Queries**: Enhanced with SecurityAgent vulnerability analysis

### How It Works

1. **Query Classification**: Queries are classified into types (STATUS, TREND, PREDICTION, SECURITY, PERFORMANCE, COMPARISON, GENERAL)

2. **Agent Selection**:
   - PREDICTION queries → PredictionAgent
   - PERFORMANCE queries → OptimizationAgent
   - SECURITY queries → SecurityAgent

3. **Result Enhancement**: Top 3 results are enhanced with agent insights

4. **Caching**: Agent results are cached for 5 minutes to improve performance

5. **Graceful Fallback**: If agents fail or are unavailable, queries still work with standard results

### Agent Insights Structure

#### Prediction Agent Insights

```json
{
  "agent_insights": {
    "type": "prediction",
    "analysis": "Detailed analysis of metrics trends...",
    "predictions": [
      {
        "prediction_type": "failure",
        "confidence": 0.85,
        "predicted_time": "2026-03-12T15:30:00Z",
        "contributing_factors": [...]
      }
    ],
    "metrics_analyzed": 100
  }
}
```

#### Optimization Agent Insights

```json
{
  "agent_insights": {
    "type": "optimization",
    "performance_analysis": "Performance bottleneck analysis...",
    "recommendations": [
      {
        "type": "caching",
        "priority": "high",
        "expected_impact": "30% latency reduction",
        "implementation_effort": "medium"
      }
    ],
    "prioritization": "Recommendations ordered by impact/effort ratio",
    "metrics_analyzed": 100
  }
}
```

## Configuration

### Environment Variables

```bash
# Agent Settings
AGENT_TIMEOUT=30                    # Timeout for agent operations (seconds)
AGENT_CACHE_TTL=300                 # Cache TTL for agent results (seconds)
AGENT_MAX_RESULTS=3                 # Max results to enhance with agents

# LLM Settings (required for agents)
LLM_PROVIDER=openai                 # LLM provider
LLM_MODEL=gpt-4                     # LLM model
LLM_API_KEY=your-api-key           # API key
LLM_TEMPERATURE=0.7                 # Temperature for generation
```

### Disabling Agents

Agents can be disabled per-request using the `use_ai_agents` parameter:

```python
# API Request
POST /api/v1/query
{
  "query_text": "What are the predictions for my-api?",
  "use_ai_agents": false  # Disable agent enhancement
}
```

## API Examples

### Basic Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Show me all active APIs"
  }'
```

### Prediction Query with Agent Enhancement

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What are the predictions for payment-api?",
    "use_ai_agents": true
  }'
```

**Response:**

```json
{
  "query_id": "123e4567-e89b-12d3-a456-426614174000",
  "query_text": "What are the predictions for payment-api?",
  "response_text": "Based on AI analysis, payment-api shows concerning trends. The PredictionAgent has identified a high probability (85%) of performance degradation within the next 36 hours due to increasing error rates and degrading response times. Key contributing factors include...",
  "confidence_score": 0.92,
  "results": {
    "data": [
      {
        "id": "api-123",
        "name": "payment-api",
        "agent_insights": {
          "type": "prediction",
          "analysis": "Detailed analysis...",
          "predictions": [...]
        }
      }
    ],
    "count": 1,
    "execution_time": 1250
  },
  "follow_up_queries": [
    "What are the key factors driving these predictions?",
    "Show me the confidence levels for these predictions",
    "What preventive actions are recommended?"
  ],
  "execution_time_ms": 1250
}
```

### Performance Query with Agent Enhancement

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "How can I improve the performance of user-api?",
    "use_ai_agents": true
  }'
```

**Response:**

```json
{
  "query_id": "123e4567-e89b-12d3-a456-426614174001",
  "query_text": "How can I improve the performance of user-api?",
  "response_text": "The OptimizationAgent has analyzed user-api performance and identified several optimization opportunities. The highest priority recommendation is implementing response caching, which could reduce latency by 30% with medium implementation effort. Additional recommendations include...",
  "confidence_score": 0.88,
  "results": {
    "data": [
      {
        "id": "api-456",
        "name": "user-api",
        "agent_insights": {
          "type": "optimization",
          "performance_analysis": "Analysis shows...",
          "recommendations": [...]
        }
      }
    ],
    "count": 1,
    "execution_time": 1450
  },
  "follow_up_queries": [
    "What's the expected impact of these optimizations?",
    "Show me the implementation priority order",
    "What are the resource requirements?"
  ],
  "execution_time_ms": 1450
}
```

## Performance Considerations

### Caching Strategy

- **Cache Duration**: 5 minutes (configurable via `AGENT_CACHE_TTL`)
- **Cache Key**: Based on API ID and agent type
- **Cache Invalidation**: Automatic after TTL expires

### Result Limiting

- Only the **top 3 results** are enhanced with agent insights
- This prevents excessive latency for queries returning many results
- Configurable via `AGENT_MAX_RESULTS`

### Parallel Execution

- Agent enhancement for multiple results runs in parallel
- Timeout protection prevents hanging queries
- Individual agent failures don't block the entire query

### Timeout Protection

- Agent operations have a configurable timeout (default: 30 seconds)
- Queries complete even if agents timeout
- Timeout errors are logged but don't fail the query

## Error Handling

### Agent Unavailable

If agents are not initialized or unavailable:
- Queries proceed without agent enhancement
- Standard results are returned
- No error is thrown to the user

### Agent Execution Failure

If an agent fails during execution:
- The specific result is returned without agent insights
- Other results continue processing
- Error is logged for debugging
- Query completes successfully

### LLM Service Failure

If the LLM service fails:
- Fallback to keyword-based intent extraction
- Fallback to template-based response generation
- Query still completes with reduced quality

## Query Types

### STATUS
Keywords: status, health, state, current, now, active

Example: "What is the current status of payment-api?"

### TREND
Keywords: trend, over time, history, pattern, change

Example: "Show me the error rate trend for user-api over the last week"

### PREDICTION
Keywords: predict, forecast, future, will, expect

Example: "Will payment-api experience issues in the next 24 hours?"

**Agent Enhancement**: ✅ PredictionAgent

### SECURITY
Keywords: security, vulnerability, threat, risk, cve

Example: "What security vulnerabilities affect my APIs?"

### PERFORMANCE
Keywords: performance, latency, response time, throughput, slow

Example: "Which APIs have the worst performance?"

**Agent Enhancement**: ✅ OptimizationAgent

### COMPARISON
Keywords: compare, versus, vs, difference, between

Example: "Compare the performance of payment-api and user-api"

### GENERAL
Default type when no specific keywords match

Example: "Tell me about my APIs"

## Follow-up Suggestions

The Query Service generates contextual follow-up suggestions based on:

1. **Query Type**: Different suggestions for different query types
2. **Results**: Suggestions based on what was found
3. **Agent Insights**: Agent-specific follow-ups when insights are present

### Agent-Specific Follow-ups

#### Prediction Queries
- "What are the key factors driving these predictions?"
- "Show me the confidence levels for these predictions"
- "What preventive actions are recommended?"

#### Performance Queries
- "What's the expected impact of these optimizations?"
- "Show me the implementation priority order"
- "What are the resource requirements?"

## Testing

### Integration Tests

Run the agent integration tests:

```bash
cd backend
pytest tests/integration/test_query_agent_integration.py -v
```

### Test Coverage

The integration tests cover:
- ✅ Prediction queries with agent enhancement
- ✅ Performance queries with agent enhancement
- ✅ Graceful fallback when agents unavailable
- ✅ Agent result caching
- ✅ Parallel agent execution
- ✅ Timeout handling
- ✅ Token usage tracking
- ✅ Agent-specific follow-up suggestions

## Troubleshooting

### Agents Not Working

**Symptom**: Queries work but no agent insights in results

**Possible Causes**:
1. Agents not initialized (check logs for initialization errors)
2. LLM service not configured (check `LLM_API_KEY`)
3. Agent execution failing (check logs for agent errors)
4. `use_ai_agents=false` in request

**Solution**:
```bash
# Check agent initialization
grep "AI agents initialized" backend/logs/app.log

# Check LLM configuration
echo $LLM_API_KEY

# Enable debug logging
export DEBUG=true
```

### Slow Query Performance

**Symptom**: Queries take longer than expected

**Possible Causes**:
1. Agent timeout too high
2. Too many results being enhanced
3. Cache not working

**Solution**:
```bash
# Reduce agent timeout
export AGENT_TIMEOUT=15

# Reduce max results for enhancement
export AGENT_MAX_RESULTS=2

# Check cache TTL
export AGENT_CACHE_TTL=300
```

### Agent Timeouts

**Symptom**: Frequent timeout errors in logs

**Possible Causes**:
1. LLM service slow or overloaded
2. Large metric datasets
3. Network issues

**Solution**:
```bash
# Increase timeout
export AGENT_TIMEOUT=60

# Use faster LLM model
export LLM_MODEL=gpt-3.5-turbo

# Reduce metrics analyzed
# (modify agent implementation to limit metric window)
```

## Best Practices

### 1. Enable Caching

Always use caching in production to reduce LLM costs and improve performance:

```python
AGENT_CACHE_TTL=300  # 5 minutes
```

### 2. Limit Enhanced Results

Don't enhance too many results to maintain good performance:

```python
AGENT_MAX_RESULTS=3  # Maximum 3 results
```

### 3. Set Reasonable Timeouts

Balance between waiting for insights and query responsiveness:

```python
AGENT_TIMEOUT=30  # 30 seconds
```

### 4. Monitor Token Usage

Track LLM token usage to manage costs:

```python
# Check query metadata for token usage
query.metadata.get("token_usage")
```

### 5. Use Appropriate Models

Choose LLM models based on needs:

- **Fast queries**: `gpt-3.5-turbo`
- **High quality**: `gpt-4`
- **Cost-effective**: `gpt-3.5-turbo`

## Future Enhancements

### Planned Features

1. **Streaming Responses**: Stream agent insights as they're generated
2. **Multi-Agent Queries**: Combine insights from multiple agents
3. **Custom Agents**: Support for user-defined agents
4. **Agent Metrics**: Detailed metrics on agent performance
5. **Smart Caching**: Intelligent cache invalidation based on data changes

### Experimental Features

1. **Voice Queries**: Natural language voice input
2. **Visual Insights**: Charts and graphs in responses
3. **Proactive Alerts**: Agent-driven notifications
4. **Collaborative Queries**: Multi-user query sessions

## Support

For issues or questions:
- Check logs: `backend/logs/app.log`
- Run tests: `pytest tests/integration/test_query_agent_integration.py`
- Review code: `backend/app/services/query_service.py`

---

**Last Updated**: 2026-03-11  
**Version**: 1.0.0  
**Phase**: 11 - Query Service Agent Integration