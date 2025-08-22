# AI Narrative Generation System

## Overview

The AI Narrative Generation System provides intelligent, context-aware narratives for financial planning simulations. It integrates OpenAI GPT-4 and Anthropic Claude APIs to generate compliant, multi-language financial narratives with strict numerical validation and comprehensive audit logging.

## Features

### Core Capabilities
- **Dual LLM Integration**: Seamless integration with OpenAI GPT-4 and Anthropic Claude
- **Templated Prompts**: Structured templates with numerical placeholders for consistent output
- **Multi-Language Support**: English, Spanish, and Chinese narratives
- **Compliance & Safety**: Built-in disclaimers, content filtering, and audit logging
- **Intelligent Caching**: Redis-based caching for improved performance
- **A/B Testing**: Framework for comparing template-only vs LLM-enhanced narratives
- **Fallback Narratives**: Graceful degradation when APIs are unavailable

### Narrative Types
1. **Simulation Summary**: Overview of Monte Carlo simulation results
2. **Trade-Off Analysis**: Comparison of different financial strategies
3. **Recommendations**: Personalized action items based on analysis
4. **Risk Assessment**: Evaluation of portfolio risk metrics
5. **Goal Progress**: Tracking toward financial objectives
6. **Portfolio Review**: Performance analysis and rebalancing suggestions

## Architecture

```
app/ai/
├── config.py                    # Configuration management
├── llm_client.py               # OpenAI/Anthropic client implementations
├── narrative_generator.py      # Main narrative generation logic
├── enhanced_template_manager.py # Template management with validation
├── safety_controller.py        # Content safety and compliance
├── enhanced_audit_logger.py    # Comprehensive audit logging
├── enhanced_multilingual.py    # Multi-language support
├── integration.py              # Integration with financial planning system
├── api.py                      # FastAPI endpoints
└── templates/                  # Narrative templates directory
```

## Configuration

### Environment Variables

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# Optional Configuration
AI_NARRATIVE_TEMPERATURE=0.3
AI_MAX_OUTPUT_TOKENS=2000
AI_ENABLE_RESPONSE_CACHING=true
AI_ENABLE_AB_TESTING=true
AI_ENABLE_AUDIT_LOGGING=true
```

### Supported Models
- OpenAI: `gpt-4-turbo-preview` (default)
- Anthropic: `claude-3-opus-20240229` (default)

## API Endpoints

### Generate Narrative
```http
POST /api/v1/ai/generate
Content-Type: application/json

{
  "simulation_id": "sim123",
  "narrative_type": "SIMULATION_SUMMARY",
  "language": "en",
  "data": {
    "num_simulations": 10000,
    "success_rate": 85,
    "median_value": 850000,
    ...
  },
  "include_disclaimer": true,
  "enhance_with_llm": true
}
```

### Batch Generation
```http
POST /api/v1/ai/generate-batch
Content-Type: application/json

{
  "simulation_id": "sim123",
  "narrative_types": ["SIMULATION_SUMMARY", "TRADE_OFF_ANALYSIS"],
  "language": "en",
  "data": {...}
}
```

### List Templates
```http
GET /api/v1/ai/templates?category=SIMULATION&language=en
```

### Submit Feedback
```http
POST /api/v1/ai/feedback
Content-Type: application/json

{
  "simulation_id": "sim123",
  "narrative_type": "SIMULATION_SUMMARY",
  "satisfaction_score": 8.5,
  "feedback_text": "Clear and helpful"
}
```

## Template System

### Template Structure
Templates use Jinja2 syntax with typed placeholders:

```jinja2
Based on {{num_simulations}} simulations, your plan shows a {{success_rate}}% 
probability of achieving your goals.

Key Findings:
- Median portfolio value: ${{median_value:,.0f}}
- Best case (95th percentile): ${{best_case:,.0f}}
- Required monthly savings: ${{monthly_savings:,.0f}}
```

### Variable Types
- `number`: Plain numbers
- `percentage`: Percentage values
- `currency`: Money amounts
- `date`: Date values
- `text`: Text strings

### Creating Custom Templates
```python
template = NarrativeTemplate(
    id="custom_template_v1",
    category=TemplateCategory.SIMULATION,
    name="Custom Summary",
    language=Language.ENGLISH,
    template_text="Your template here...",
    variables=[
        TemplateVariable(name="success_rate", type="percentage"),
        TemplateVariable(name="portfolio_value", type="currency")
    ]
)
```

## Multi-Language Support

### Supported Languages
- English (`en`)
- Spanish (`es`)
- Chinese (`zh`)

### Language Detection
The system automatically detects input language and can translate narratives:

```python
narrative = await generator.generate_narrative(
    request=request,
    language=Language.SPANISH
)
```

### Localized Number Formatting
- English: $1,234.56
- Spanish: €1.234,56
- Chinese: ¥1,234.56

## Compliance & Safety

### Disclaimers
All narratives include appropriate disclaimers:
- General investment disclaimer
- Projection accuracy disclaimer
- Regulatory compliance disclaimer
- Tax advice disclaimer

### Content Validation
- Numerical consistency checking
- PII detection and removal
- Prohibited content filtering
- Output length constraints

### Audit Logging
Comprehensive logging includes:
- All prompts and responses
- API calls and errors
- Safety violations
- User feedback
- A/B test results

## Caching Strategy

### Redis Integration
```python
# Cached for 1 hour by default
cache_key = hash(template_type + data + language)
response = await redis.get(cache_key)
```

### Cache Invalidation
- TTL-based expiration (configurable)
- Manual invalidation on template updates
- Automatic invalidation on configuration changes

## A/B Testing Framework

### Test Configuration
```python
# 10% of requests use alternative approach
AI_AB_TEST_PERCENTAGE=0.1
```

### Metrics Tracked
- Response latency
- User satisfaction scores
- Token usage
- Error rates
- Cache hit rates

## Error Handling

### Fallback Strategy
1. Try primary provider (OpenAI)
2. Fallback to secondary provider (Anthropic)
3. Use template-only generation
4. Return static fallback narrative

### Error Types
- API rate limits
- Token limits exceeded
- Invalid template data
- Safety violations
- Network timeouts

## Performance Optimization

### Batch Processing
Generate multiple narratives in a single request:
```python
responses = await generator.generate_batch_narratives(requests)
```

### Token Optimization
- Template pre-validation
- Prompt compression
- Response truncation
- Token usage tracking

## Integration Examples

### With Simulation Results
```python
enhanced_results = await integration_service.enhance_simulation_results(
    simulation_result=result,
    user_id=user_id,
    language=Language.ENGLISH
)
```

### With Goal Tracking
```python
goal_narrative = await integration_service.create_goal_progress_narrative(
    financial_profile=profile,
    goal_id=goal_id,
    user_id=user_id
)
```

## Monitoring & Analytics

### Key Metrics
- Average response time: < 2 seconds
- Cache hit rate: > 60%
- API success rate: > 99%
- User satisfaction: > 4/5

### Health Check
```http
GET /api/v1/ai/health
```

Response:
```json
{
  "status": "healthy",
  "providers": {
    "openai": true,
    "anthropic": true,
    "fallback": true
  },
  "cache_active": true,
  "audit_active": true
}
```

## Best Practices

### Template Design
1. Keep templates concise and focused
2. Use clear variable names
3. Include context in templates
4. Validate all numerical placeholders
5. Test with edge cases

### API Usage
1. Batch requests when possible
2. Implement client-side caching
3. Handle rate limits gracefully
4. Monitor token usage
5. Collect user feedback

### Security
1. Never expose API keys
2. Validate all input data
3. Sanitize user-provided content
4. Implement rate limiting
5. Regular security audits

## Troubleshooting

### Common Issues

**Issue**: Narratives not generating
- Check API keys are configured
- Verify network connectivity
- Review audit logs for errors

**Issue**: Inconsistent numbers
- Validate template variables
- Check numerical formatting
- Review data extraction logic

**Issue**: Slow response times
- Enable caching
- Use batch requests
- Check API rate limits
- Review template complexity

## Development

### Running Tests
```bash
pytest app/ai/tests/ -v
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your-key
export ANTHROPIC_API_KEY=your-key

# Run the service
uvicorn app.main:app --reload
```

## Support

For issues or questions:
1. Check audit logs at `/var/log/financial_ai/`
2. Review API documentation at `/docs`
3. Contact the development team

## License

This module is part of the Financial Planning Backend system and follows the same licensing terms.