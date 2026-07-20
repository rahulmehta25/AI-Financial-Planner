# Financial Planning Platform - Quick Start Guide

## Prerequisites
- Python 3.8+
- `requests` library
- API Credentials

## Installation
```bash
pip install requests
```

## Authentication

### 1. Basic Authentication
```python
from financial_planner_sdk import FinancialPlannerClient

# Initialize client
client = FinancialPlannerClient()

# Authenticate
client.authenticate('user@example.com', 'password123')
```

## Running Simulations

### Monte Carlo Financial Simulation
```python
# Run comprehensive simulation
results = client.run_monte_carlo_simulation(
    initial_investment=10000,   # Starting amount
    monthly_contribution=500,   # Monthly additional investment
    years=20,                   # Investment horizon
    risk_tolerance='medium'     # Risk profile
)

# Print results
print(results)
```

## Curl Examples

### Authentication
```bash
curl -X POST https://api.financialplanner.com/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password123"}'
```

### Monte Carlo Simulation
```bash
curl -X POST https://api.financialplanner.com/v1/simulations/monte-carlo \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
         "initial_investment": 10000,
         "monthly_contribution": 500,
         "years": 20,
         "risk_tolerance": "medium"
     }'
```

## Error Handling
```python
try:
    results = client.run_monte_carlo_simulation(...)
except FinancialPlannerSDKError as e:
    print(f"Simulation Error: {e}")
```

## Rate Limits
- 100 requests per minute
- Burst limit: 200 requests
- Exceeding limits returns 429 Too Many Requests

## Support
- Email: api-support@financialplanner.com
- Documentation: https://financialplanner.com/docs