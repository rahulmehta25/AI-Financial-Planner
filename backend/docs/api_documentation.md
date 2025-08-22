# API Documentation

## Overview
This financial planning platform provides a comprehensive set of RESTful APIs for managing personal financial data, investments, and insights.

## Base URL
`https://api.financialplanner.com/v1`

## Authentication
All API requests require authentication using JWT tokens.

### Authentication Endpoints
- `POST /auth/login`: User authentication
- `POST /auth/register`: User registration
- `POST /auth/refresh`: Token refresh

### Authentication Flow
1. Register a new user
2. Obtain JWT token via login
3. Include token in Authorization header for subsequent requests

## API Endpoints

### Users
- `GET /users/profile`: Retrieve user profile
- `PUT /users/profile`: Update user profile
- `POST /users/financial-goals`: Create financial goal
- `GET /users/financial-goals`: List financial goals

### Financial Profiles
- `POST /financial-profiles`: Create financial profile
- `GET /financial-profiles`: List financial profiles
- `PUT /financial-profiles/{id}`: Update financial profile

### Investments
- `GET /investments`: List investment opportunities
- `POST /investments`: Create investment
- `GET /investments/recommendations`: AI-powered investment recommendations

### Market Data
- `GET /market-data/stocks`: Real-time stock data
- `GET /market-data/indices`: Market indices
- `GET /market-data/cryptocurrencies`: Cryptocurrency prices

### Simulations
- `POST /simulations/monte-carlo`: Run Monte Carlo simulation
- `GET /simulations/history`: Retrieve simulation history

## Rate Limiting
- 100 requests per minute per API key
- Burst limit: 200 requests
- Exceeding limits returns 429 Too Many Requests

## Error Handling
Standard error response format:
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Detailed error description",
        "details": {}
    }
}
```

### Common Error Codes
- `UNAUTHORIZED_ACCESS`: Authentication failed
- `INVALID_INPUT`: Invalid request parameters
- `RESOURCE_NOT_FOUND`: Requested resource does not exist
- `RATE_LIMIT_EXCEEDED`: API request limit reached
- `INTERNAL_SERVER_ERROR`: Unexpected server error

## Versioning
Current API Version: v1
Deprecated versions will be supported for 6 months after deprecation notice