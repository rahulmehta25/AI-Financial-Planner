# Consolidated API Endpoints

This directory contains 6 serverless API functions that consolidate all functionality into fewer endpoints to stay within Vercel's limits.

## Endpoints

### 1. `/api/health`
- **Method**: GET
- **Description**: Health check endpoint
- **Response**: System status and uptime

### 2. `/api/simulate`
- **Method**: POST
- **Description**: Financial Monte Carlo simulation
- **Body**: `{ age, income, savings, risk_tolerance }`
- **Response**: Simulation results with success probability and recommendations

### 3. `/api/auth`
- **Methods**: POST, DELETE
- **Description**: Authentication operations
- **Operations**:
  - Login: `POST /api/auth?operation=login` or `POST /api/auth` with `{email, password}`
  - Register: `POST /api/auth?operation=register` with `{email, password, firstName, lastName}`
  - Refresh: `POST /api/auth?operation=refresh` with `{refresh_token}`
  - Logout: `DELETE /api/auth`

### 4. `/api/portfolio`
- **Method**: GET
- **Description**: Portfolio management operations
- **Operations**:
  - Overview: `GET /api/portfolio?operation=overview` (requires auth)
  - Optimization: `GET /api/portfolio?operation=optimization&risk_tolerance=moderate`

### 5. `/api/ai`
- **Methods**: GET, POST
- **Description**: AI-powered financial advice
- **Operations**:
  - Chat: `POST /api/ai?operation=chat` with `{message, sessionId?, context?}`
  - Get Sessions: `GET /api/ai?operation=chat&sessionId=xyz`
  - Insights: `GET /api/ai?operation=insights`
  - Recommendations: `GET /api/ai?operation=recommendations&risk_profile=moderate`

### 6. `/api/user`
- **Methods**: GET, PUT, DELETE
- **Description**: User profile and settings management
- **Operations**:
  - Get Profile: `GET /api/user?operation=profile` (requires auth)
  - Update Profile: `PUT /api/user?operation=profile` (requires auth)
  - Get Settings: `GET /api/user?operation=settings` (requires auth)
  - Update Settings: `PUT /api/user?operation=settings` (requires auth)
  - Delete Account: `DELETE /api/user?operation=delete` (requires auth)

## Authentication

Most endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer acc_timestamp_userid_random
```

## CORS

All endpoints support CORS with the following headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Authorization`

## Error Handling

All endpoints return consistent error responses:
```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "detail": "Additional details"
}
```

## Development Notes

- All endpoints use TypeScript with proper typing
- Mock data is used for demonstration purposes
- In production, replace mock databases with real database connections
- Implement proper password hashing for security
- Add rate limiting and input sanitization
- Use environment variables for configuration