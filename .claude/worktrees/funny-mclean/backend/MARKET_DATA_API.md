# Market Data API Documentation

## Overview

The Market Data API provides comprehensive financial market data with historical stock trends, S&P 500 integration, and advanced technical analysis. This API leverages multiple data providers with intelligent failover and caching for optimal performance.

## Features

### 🚀 Core Features
- **Real-time stock quotes** with 1-minute cache TTL
- **Historical data** with flexible time periods (1D, 1W, 1M, 3M, 1Y, 5Y, MAX)
- **S&P 500 benchmark comparison** for portfolio performance analysis
- **Technical indicators** (SMA, EMA, RSI, MACD, Bollinger Bands)
- **Volume analysis** with relative volume ratios
- **Sector performance tracking** via sector ETFs
- **Market indices** (S&P 500, Dow, NASDAQ, Russell 2000, VIX)
- **Company news** integration

### 🎯 Technical Analysis
- Moving Averages: SMA (20, 50, 200), EMA (12, 26)
- Momentum: RSI (14), MACD with signal line and histogram
- Volatility: Bollinger Bands with configurable standard deviations
- Trend Analysis: Automated trend detection with strength scoring
- Volume Analysis: Volume SMA and relative volume ratios

### 💾 Caching & Performance
- **Redis-based caching** with intelligent TTL management
- **Multi-level caching** for quotes, historical data, and technical indicators
- **Batch processing** for multiple symbol requests
- **Provider failover** (Yahoo Finance primary, Alpha Vantage/IEX Cloud fallback)
- **Rate limiting** and request optimization

## API Endpoints

### Base URL
```
/api/v1/market-data
```

### Authentication
All endpoints require authentication via Bearer token.

---

## 📈 Quote & Real-time Data

### Get Current Quote
```http
GET /quote/{symbol}
```

**Parameters:**
- `symbol` (path): Stock symbol (e.g., "AAPL", "TSLA")

**Response:**
```json
{
  "symbol": "AAPL",
  "current_price": 175.25,
  "open_price": 174.50,
  "high_price": 176.80,
  "low_price": 173.90,
  "close_price": 174.25,
  "volume": 52847392,
  "price_change": 1.00,
  "price_change_percent": 0.57,
  "timestamp": "2025-01-27T15:30:00.000Z",
  "provider": "yahoo_finance"
}
```

**Cache TTL:** 60 seconds

---

## 📊 Historical Data

### Get Historical Data
```http
GET /historical/{symbol}
```

**Parameters:**
- `symbol` (path): Stock symbol
- `start_date` (query, optional): Start date (YYYY-MM-DD)
- `end_date` (query, optional): End date (YYYY-MM-DD)
- `period` (query, optional): Time period - `1D`, `1W`, `1M`, `3M`, `1Y`, `5Y`, `MAX`
- `interval` (query, optional): Data interval - `1m`, `5m`, `1h`, `1d`, `1wk`, `1mo`

**Response:**
```json
{
  "symbol": "AAPL",
  "start_date": "2024-01-27",
  "end_date": "2025-01-27",
  "interval": "1d",
  "data_points": [
    {
      "date": "2024-01-27",
      "timestamp": "2024-01-27T00:00:00",
      "open": 174.50,
      "high": 176.80,
      "low": 173.90,
      "close": 175.25,
      "volume": 52847392
    }
  ],
  "provider": "yahoo_finance"
}
```

**Cache TTL:** 1 hour (daily data), 5 minutes (intraday)

### Get Historical Data with S&P 500 Comparison
```http
GET /historical/{symbol}/sp500-comparison
```

**Parameters:**
- Same as historical data endpoint

**Response:**
```json
{
  "symbol": "AAPL",
  "data_points": [...],
  "sp500_comparison": {
    "comparison_data": [
      {
        "date": "2024-01-27",
        "stock_pct_change": 12.5,
        "sp500_pct_change": 8.2
      }
    ],
    "correlation": 0.75
  }
}
```

### Get S&P 500 Historical Data
```http
GET /sp500/historical
```

**Parameters:**
- Same as historical data endpoint (no symbol required)

---

## 🔍 Technical Analysis

### Get Technical Analysis
```http
GET /analysis/{symbol}
```

**Parameters:**
- `symbol` (path): Stock symbol
- `period` (query, optional): Analysis period - default `1Y`
- `interval` (query, optional): Data interval - default `1d`

**Response:**
```json
{
  "symbol": "AAPL",
  "period": "1Y",
  "last_updated": "2025-01-27T15:30:00.000Z",
  "price_data": {
    "current_price": 175.25,
    "price_change": 1.00,
    "price_change_percent": 0.57
  },
  "moving_averages": {
    "sma_20": 170.25,
    "sma_50": 168.50,
    "sma_200": 165.75,
    "ema_12": 171.80,
    "ema_26": 169.90
  },
  "momentum_indicators": {
    "rsi": 58.5,
    "macd": {
      "macd": [1.25, 1.30, 1.35],
      "signal": [1.20, 1.25, 1.28],
      "histogram": [0.05, 0.05, 0.07]
    }
  },
  "volatility_indicators": {
    "bollinger_bands": {
      "upper": [178.50, 179.00],
      "middle": [175.00, 175.25],
      "lower": [171.50, 171.50]
    }
  },
  "volume_analysis": {
    "current_volume": 52847392,
    "avg_volume_20": 48500000,
    "volume_ratio": 1.09
  },
  "trend_analysis": {
    "trend": "bullish",
    "strength": 2,
    "signals": [
      "Price above SMA 20",
      "Price above SMA 50",
      "Golden Cross - SMA 20 above SMA 50"
    ]
  },
  "detailed_indicators": {
    "sma_20_series": [...],
    "rsi_series": [...],
    "macd_series": {...}
  }
}
```

**Cache TTL:** 5 minutes

---

## 📋 Chart Data

### Get Comprehensive Chart Data
```http
POST /chart
```

**Request Body:**
```json
{
  "symbol": "AAPL",
  "period": "1Y",
  "interval": "1d",
  "include_sp500": true,
  "include_technical_indicators": true
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "period": "1Y",
  "interval": "1d",
  "price_data": [...],
  "sp500_comparison": {...},
  "technical_indicators": {...},
  "last_updated": "2025-01-27T15:30:00.000Z"
}
```

---

## 🔗 Market Correlation

### Get Market Correlation Analysis
```http
GET /correlation/{symbol}
```

**Parameters:**
- `symbol` (path): Stock symbol
- `period` (query, optional): Analysis period

**Response:**
```json
{
  "symbol": "AAPL",
  "period": "1Y",
  "correlations": {
    "^GSPC": {
      "correlation": 0.75,
      "name": "S&P 500"
    },
    "^DJI": {
      "correlation": 0.72,
      "name": "Dow Jones"
    }
  },
  "last_updated": "2025-01-27T15:30:00.000Z"
}
```

---

## 🔍 Symbol Search

### Search Symbols
```http
GET /search
```

**Parameters:**
- `query` (query): Search term
- `limit` (query, optional): Maximum results (default: 10)

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "type": "EQUITY",
    "exchange": "NASDAQ"
  }
]
```

---

## 📊 Market Overview

### Get Sector Performance
```http
GET /sectors
```

**Response:**
```json
[
  {
    "sector": "Technology",
    "symbol": "XLK",
    "price": 185.50,
    "change": 2.25,
    "change_percent": 1.23
  }
]
```

### Get Market Indices
```http
GET /indices
```

**Response:**
```json
[
  {
    "name": "S&P 500",
    "symbol": "^GSPC",
    "value": 4750.25,
    "change": 15.80,
    "change_percent": 0.33,
    "timestamp": "2025-01-27T15:30:00.000Z"
  }
]
```

### Get Economic Indicators
```http
GET /economic-indicators
```

**Response:**
```json
{
  "last_updated": "2025-01-27T15:30:00.000Z",
  "indicators": [
    {
      "name": "10-Year Treasury",
      "symbol": "^TNX",
      "value": 4.25,
      "change": 0.05,
      "description": "10-Year Treasury Bond Yield"
    }
  ]
}
```

---

## 📰 News Integration

### Get Symbol News
```http
GET /news/{symbol}
```

**Parameters:**
- `symbol` (path): Stock symbol
- `limit` (query, optional): Maximum articles (default: 10)

**Response:**
```json
[
  {
    "title": "Apple Reports Strong Q4 Earnings",
    "summary": "Apple Inc. reported better-than-expected quarterly results...",
    "url": "https://example.com/news/apple-earnings",
    "publisher": "Reuters",
    "published_at": "2025-01-27T14:00:00.000Z",
    "type": "news"
  }
]
```

---

## 📋 Watchlist Management

### Add to Watchlist
```http
POST /watchlist
```

**Request Body:**
```json
["AAPL", "TSLA", "MSFT"]
```

### Get Watchlist
```http
GET /watchlist
```

### Remove from Watchlist
```http
DELETE /watchlist/{symbol}
```

---

## 🗄️ Cache Management

### Get Cache Statistics
```http
GET /cache/statistics
```

**Response:**
```json
{
  "status": "connected",
  "memory_usage": "256MB",
  "connected_clients": 5,
  "total_keys": 1250,
  "key_counts_by_type": {
    "quote": 150,
    "historical_1d": 75,
    "technical_analysis": 25
  },
  "cache_ttl_settings": {
    "quote": 60,
    "historical_1d": 3600,
    "technical_analysis": 300
  }
}
```

### Invalidate Cache Pattern (Admin)
```http
DELETE /cache/invalidate/{pattern}
```

**Parameters:**
- `pattern` (path): Cache key pattern to invalidate

---

## 📝 Data Providers & Failover

### Primary Provider
- **Yahoo Finance** - Free, comprehensive data
- Real-time quotes, historical data, company info
- News integration, symbol search

### Fallback Providers
- **Alpha Vantage** - Requires API key
- **IEX Cloud** - Requires API key
- Automatic failover on provider errors

### Provider Health Monitoring
- Automatic health checks every 5 minutes
- Error rate tracking per provider
- Intelligent routing based on provider status

---

## ⚡ Performance & Caching

### Cache Strategy
| Data Type | TTL | Strategy |
|-----------|-----|----------|
| Live Quotes | 60s | Per symbol |
| Historical Daily | 1 hour | Per symbol + date range |
| Intraday Data | 5 minutes | Per symbol + date range |
| Technical Analysis | 5 minutes | Per symbol + period |
| S&P 500 Data | 30 minutes | Per period |
| Sector Performance | 15 minutes | Global |
| News | 10 minutes | Per symbol |

### Rate Limiting
- 2000 requests/hour per provider
- Intelligent batching for multiple symbols
- Concurrent request limiting via semaphores

---

## 🚨 Error Handling

### Error Codes
- `404` - Symbol/data not found
- `429` - Rate limit exceeded
- `503` - Data provider error
- `500` - Internal server error

### Error Response Format
```json
{
  "detail": "Quote not found for symbol: INVALID",
  "error_code": "NOT_FOUND"
}
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Keys (Optional)
ALPHA_VANTAGE_API_KEY=your_key_here
IEX_CLOUD_API_KEY=your_key_here

# Cache Settings
MARKET_DATA_CACHE_TTL_QUOTE=60
MARKET_DATA_CACHE_TTL_HISTORICAL=3600
```

### Provider Priority
1. Yahoo Finance (Primary - No API key required)
2. Alpha Vantage (Fallback - API key required)
3. IEX Cloud (Fallback - API key required)

---

## 📱 Usage Examples

### Frontend Integration
```javascript
// Get stock quote with technical analysis
const response = await fetch('/api/v1/market-data/chart', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    symbol: 'AAPL',
    period: '1Y',
    include_sp500: true,
    include_technical_indicators: true
  })
});

const data = await response.json();
// data.price_data - for price chart
// data.sp500_comparison - for benchmark overlay
// data.technical_indicators - for indicator charts
```

### Portfolio Performance Comparison
```javascript
// Compare portfolio against S&P 500
const symbols = ['AAPL', 'TSLA', 'MSFT'];
const comparisons = await Promise.all(
  symbols.map(symbol => 
    fetch(`/api/v1/market-data/historical/${symbol}/sp500-comparison?period=1Y`)
      .then(r => r.json())
  )
);
```

---

## 🎯 Best Practices

### 1. Caching Strategy
- Use appropriate time periods for your use case
- Leverage the built-in caching to minimize API calls
- Monitor cache hit rates via `/cache/statistics`

### 2. Error Handling
- Always handle provider errors gracefully
- Implement retry logic for transient failures
- Use fallback data when possible

### 3. Performance Optimization
- Batch multiple symbol requests when possible
- Use appropriate intervals (don't request 1-minute data for yearly charts)
- Monitor rate limits and implement client-side throttling

### 4. Data Freshness
- Real-time quotes: Use for current market decisions
- Historical data: Cache aggressively for analysis
- Technical indicators: Balance freshness with performance

---

This API provides a comprehensive foundation for building sophisticated financial applications with real-time market data, advanced analytics, and reliable performance through intelligent caching and provider failover mechanisms.