# AI-Enhanced Analysis Setup Guide

## Overview

The API Intelligence Plane includes optional AI-enhanced analysis features powered by Large Language Models (LLMs). These features provide:

- **Enhanced Predictions**: AI-powered analysis of metrics trends with detailed explanations
- **Smart Recommendations**: LLM-generated optimization insights with implementation guidance
- **Natural Language Explanations**: Human-readable interpretations of technical predictions

## Prerequisites

### Required Dependencies

The following dependencies are already included in `backend/requirements.txt`:

```
langchain>=0.3.0
langchain-community>=0.3.0
langchain-openai>=0.2.0
langgraph>=0.2.0
litellm>=1.52.0
```

### Optional: LangGraph

LangGraph is optional. If not installed, the system automatically falls back to direct execution mode without workflow orchestration.

## Configuration

### 1. Environment Variables

Copy `.env.example` to `.env` and configure your LLM provider:

```bash
# Primary LLM Provider
LLM_PROVIDER=openai                    # Options: openai, anthropic, google, azure, ollama
LLM_MODEL=gpt-4-turbo-preview         # Model name
LLM_API_KEY=your-api-key-here         # API key for the provider
LLM_TEMPERATURE=0.7                    # Temperature (0-1)
LLM_MAX_TOKENS=2000                    # Max tokens per response

# Optional: Fallback Provider
LLM_FALLBACK_PROVIDER=anthropic
LLM_FALLBACK_MODEL=claude-3-sonnet-20240229
LLM_FALLBACK_API_KEY=your-fallback-key
```

### 2. Supported Providers

#### OpenAI
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=sk-...
```

#### Anthropic
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

#### Google (Gemini)
```bash
LLM_PROVIDER=google
LLM_MODEL=gemini-pro
GOOGLE_API_KEY=...
```

#### Azure OpenAI
```bash
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

#### Ollama (Local)
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
```

## Usage

### API Endpoints

#### 1. AI-Enhanced Predictions

Generate predictions with LLM analysis:

```bash
POST /api/v1/predictions/ai-enhanced?api_id={uuid}&min_confidence=0.7
```

Or use the `use_ai` parameter on existing endpoints:

```bash
POST /api/v1/predictions/generate?api_id={uuid}&use_ai=true
```

#### 2. Get Prediction Explanation

Get AI-generated explanation for a specific prediction:

```bash
GET /api/v1/predictions/{prediction_id}/explanation
```

#### 3. AI-Enhanced Recommendations

Generate optimization recommendations with LLM analysis:

```bash
POST /api/v1/optimization/ai-enhanced?api_id={uuid}&min_impact=10.0
```

Or use the `use_ai` parameter:

```bash
POST /api/v1/recommendations/generate?api_id={uuid}&use_ai=true
```

#### 4. Get Recommendation Insights

Get AI-generated insights for a specific recommendation:

```bash
GET /api/v1/recommendations/{recommendation_id}/insights
```

### Python SDK Example

```python
from app.services.prediction_service import PredictionService
from app.services.llm_service import LLMService
from app.config import Settings

# Initialize services
settings = Settings()
llm_service = LLMService(settings)
prediction_service = PredictionService(
    prediction_repository=prediction_repo,
    metrics_repository=metrics_repo,
    api_repository=api_repo,
    llm_service=llm_service,
)

# Generate AI-enhanced predictions
result = await prediction_service.generate_ai_enhanced_predictions(
    api_id=api_id,
    min_confidence=0.7,
)

print(f"Analysis: {result['analysis']}")
print(f"Predictions: {len(result['predictions'])}")
```

## Fallback Behavior

The system is designed with graceful degradation:

1. **LLM Unavailable**: Falls back to rule-based predictions/recommendations
2. **LangGraph Missing**: Uses direct execution mode without workflow orchestration
3. **Provider Failure**: Automatically tries fallback provider if configured
4. **API Errors**: Returns basic explanations instead of AI-generated ones

## Testing

### Test LLM Connection

```bash
python backend/scripts/test_llm.py
```

### Test AI-Enhanced Features

```bash
# Test predictions
curl -X POST "http://localhost:8000/api/v1/predictions/ai-enhanced?api_id=<uuid>"

# Test recommendations
curl -X POST "http://localhost:8000/api/v1/optimization/ai-enhanced?api_id=<uuid>"
```

## Performance Considerations

### Response Times

- **Rule-based**: <100ms
- **AI-enhanced**: 2-5 seconds (depends on LLM provider)
- **With caching**: 500ms-1s

### Token Usage

Typical token usage per request:

- **Prediction Analysis**: 500-1000 tokens
- **Recommendation Generation**: 800-1500 tokens
- **Explanation**: 200-400 tokens

### Cost Optimization

1. **Use caching**: Cache LLM responses for similar inputs
2. **Adjust temperature**: Lower temperature (0.3-0.5) for more consistent, cheaper responses
3. **Limit max_tokens**: Set appropriate limits based on use case
4. **Use local models**: Consider Ollama for development/testing

## Troubleshooting

### LLM Service Not Working

1. Check API key is set correctly
2. Verify provider is accessible
3. Check logs for specific error messages
4. Test with `backend/scripts/test_llm.py`

### Slow Response Times

1. Check network latency to LLM provider
2. Consider using a local model (Ollama)
3. Reduce `LLM_MAX_TOKENS` setting
4. Enable response caching

### High Costs

1. Monitor token usage in logs
2. Use cheaper models for non-critical features
3. Implement request rate limiting
4. Cache frequent queries

## Security Best Practices

1. **Never commit API keys**: Use environment variables
2. **Rotate keys regularly**: Update API keys periodically
3. **Monitor usage**: Track API calls and costs
4. **Sanitize inputs**: Validate all data sent to LLM
5. **Review outputs**: Don't blindly trust LLM responses

## Advanced Configuration

### Custom Prompts

Modify prompts in `backend/app/agents/`:
- `prediction_agent.py`: Prediction analysis prompts
- `optimization_agent.py`: Optimization recommendation prompts

### Workflow Customization

Edit LangGraph workflows in agent files to add custom nodes or modify execution flow.

### Provider-Specific Settings

```python
# In backend/app/services/llm_service.py
providers = [
    {
        "model": "gpt-4-turbo-preview",
        "api_key": settings.OPENAI_API_KEY,
        "temperature": 0.7,
        "max_tokens": 2000,
    }
]
```

## Support

For issues or questions:
- Check logs in `backend/app/utils/logging.py`
- Review error messages in API responses
- Consult LiteLLM documentation for provider-specific issues