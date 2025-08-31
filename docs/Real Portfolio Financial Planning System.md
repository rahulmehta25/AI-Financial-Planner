Real Portfolio Financial Planning System Implementation Guide

I'll create the updated technical implementation guide incorporating all the improvements from your feedback document.

# Technical Implementation Guide: Advanced Financial Planner Features

## 1. Introduction

This document provides a detailed technical implementation guide for enhancing the existing AI-driven financial planner with advanced features, focusing on data reliability, real-time updates, sophisticated financial calculations, and improved user experience. It outlines the architectural considerations, technology choices, and implementation strategies for each new component.

## 2. Backend Enhancements (FastAPI)

### 2.1. Data Reliability

Ensuring data reliability is paramount for a financial application. The strategy involves a pluggable data layer, robust timezone handling, and comprehensive management of corporate actions.

#### 2.1.1. Pluggable Data Layer with Provider Fallback

While `yfinance` serves as a convenient initial data source, a pluggable data layer will be implemented to allow for seamless integration with alternative data providers (e.g., Alpha Vantage, IEX, Polygon) in the future. This design ensures resilience against single-provider outages and allows for easy switching or adding new data sources without significant code changes.

*   **Implementation:** An abstract `DataProvider` interface will define methods for fetching historical and real-time data. Concrete implementations (e.g., `YFinanceProvider`, `AlphaVantageProvider`) will adhere to this interface. A `DataProviderChain` will manage provider selection with explicit ordering and timeouts:
    ```python
    class DataProviderChain:
        providers = [
            (YFinanceProvider(), timeout=5),
            (AlphaVantageProvider(), timeout=3),
            (CachedProvider(), timeout=1)  # Always last resort
        ]
    ```
    Circuit breaker patterns will prevent cascading failures when providers are down.

*   **Data Freshness Disclaimer:** Yahoo Finance/yfinance provides data with approximately 15-minute delay. Real-time feeds require licensed APIs from professional data providers (e.g., IEX Cloud, Polygon.io, or direct exchange feeds).

*   **Circuit Breaker & Retry Policy:** Each provider implementation must include:
    - Circuit breaker with failure threshold (3 failures = open circuit for 60 seconds)
    - Exponential backoff retry: [1s, 2s, 4s, 8s] with max 3 retries
    - Jitter to prevent thundering herd: `retry_delay * (0.5 + random())`

*   **Caching:** A robust caching mechanism (Redis) will store the last good quote to mask brief outages and reduce redundant API calls. This cache will be integrated into the `market_data_cache.py` service.

#### 2.1.2. Timezone Normalization & Market Hours

Accurate handling of timezones and market hours is critical for financial data. All timestamps will be normalized to a consistent timezone (e.g., UTC) internally, and converted to the user's local timezone for display.

*   **NYSE Calendar:** Integration with a NYSE trading calendar will allow the system to accurately identify trading days, holidays, and pre/post-market hours. This is essential for scheduling data fetches and processing.
*   **Pre/Post-Market Flags:** Data fetched will include flags to indicate if it pertains to pre-market, regular market, or post-market hours, enabling precise analysis and display.

#### 2.1.3. Corporate Actions and Delistings

Corporate actions (splits, dividends) and delistings significantly impact historical price data and portfolio valuation. The system will implement mechanisms to handle these events accurately.

*   **Back-Adjusted Historical Prices:** Historical prices will be back-adjusted for splits and dividends to ensure continuity and accuracy in long-term performance analysis. This involves applying adjustment factors to historical data points.
*   **Adjustment Formulas:** 
    - Stock splits: `price_adjusted = price_original / split_ratio`
    - Regular dividends: Adjust using dividend amount relative to price
    - Special dividends: Track separately with different tax implications
*   **Reconciliation Process:** Daily reconciliation against known sources (e.g., Yahoo Finance adjusted close) to verify adjustment accuracy.
*   **Delisting Management:** A process will be in place to identify and manage delisted securities, ensuring they are correctly reflected in historical portfolios and do not cause data inconsistencies.
*   **Data Model Impact:** The `corporate_actions` table will store details of these events, allowing the system to apply the necessary adjustments during data retrieval and calculation.

### 2.2. Real-time Updates

Real-time updates are crucial for providing users with up-to-the-minute market data and portfolio changes. The system will primarily leverage WebSockets or Server-Sent Events (SSE) for efficient data push, with polling as a fallback.

**Expected SLOs:**
- Latency: <300ms from market data receipt to client update
- Message delivery: 99.9% reliability
- Connection uptime: 99.5% during market hours

#### 2.2.1. WebSockets or Server-Sent Events (SSE)

*   **WebSockets:** For continuous, bidirectional communication, WebSockets are ideal for pushing real-time stock quotes, portfolio value changes, and other dynamic data to the frontend. FastAPI has built-in support for WebSockets, making implementation straightforward.
    *   **Implementation:** A WebSocket endpoint (e.g., `/ws/market_data`) will be established on the FastAPI backend. Clients will connect to this endpoint to subscribe to real-time updates for specific instruments or portfolios. The backend will manage active connections and broadcast updates as data becomes available.
*   **Server-Sent Events (SSE):** As a simpler, unidirectional alternative, SSE can be used for pushing data from the server to the client over a standard HTTP connection. This might be suitable for less frequent updates or scenarios where full-duplex communication is not strictly necessary.
    *   **Implementation:** An SSE endpoint (e.g., `/sse/market_data`) would stream data to connected clients. The client would then process these events to update the UI.

##### 2.2.1.1 Connection Management
*   **Connection Pooling:** Maximum 5 WebSocket connections per user account
*   **Heartbeat:** Ping/pong every 30 seconds to detect stale connections
*   **Graceful Degradation:** When WebSocket capacity reached, fall back to polling with user notification
*   **Message Queuing:** Buffer messages during disconnection, replay on reconnect (max 1000 messages)
*   **Redis Pub/Sub Scaling:** For >5,000 WebSocket clients, implement Redis Cluster with dedicated pub/sub nodes and connection multiplexing through a WebSocket gateway layer

#### 2.2.2. Fallback to Polling with Staggered Backoff

Outside market hours or in cases where WebSocket/SSE connections are not feasible, the system will gracefully fall back to polling with a staggered backoff strategy.

*   **Polling Mechanism:** The frontend will periodically send requests to a REST API endpoint (e.g., `/api/quote/{symbol}`) to fetch the latest data. The polling interval will be adjusted based on market hours (e.g., less frequent outside trading hours).
*   **Staggered Backoff:** To prevent overwhelming the backend and external data providers, polling requests will be staggered and implement an exponential backoff strategy in case of errors or rate limits.

#### 2.2.3. Redis for Fast Quote Fan-Out

To efficiently fan out real-time quotes to multiple connected clients and deduplicate polling requests, Redis will be used as the message broker.

*   **Redis Pub/Sub:** When a new quote is received from an external data provider, it will be published to a Redis channel. WebSocket/SSE handlers will subscribe to these channels and broadcast the updates to their respective clients.
*   **Scaling Strategy:** 
    - Single Redis instance: <5k concurrent connections
    - Redis Cluster: >5k connections with dedicated pub/sub nodes
    - Consider Redis Streams for guaranteed delivery requirements

### 2.3. Jobs & Backfills

To manage periodic tasks, data ingestion, and historical data backfills, a robust task runner will be integrated into the backend. This ensures that data remains up-to-date and consistent.

#### 2.3.1. Task Runner Selection

**Decision: Use RQ (Redis Queue) for MVP and V1**

RQ provides the optimal balance of simplicity and scalability for this architecture. Since Redis is already required for real-time updates, RQ adds minimal operational overhead while providing proper task isolation and worker scaling.

*   **Implementation:** 
    ```python
    # worker.py
    from redis import Redis
    from rq import Worker, Queue, Connection
    import uuid
    
    redis_conn = Redis()
    
    # Separate queues for different priorities
    high_queue = Queue('high', connection=redis_conn)  # Real-time price updates
    default_queue = Queue('default', connection=redis_conn)  # EOD snapshots
    low_queue = Queue('low', connection=redis_conn)  # Reports, backfills
    
    # Idempotency wrapper
    def idempotent_job(func):
        def wrapper(*args, idempotency_key=None, **kwargs):
            if not idempotency_key:
                idempotency_key = str(uuid.uuid4())
            
            # Check if job already processed
            if redis_conn.exists(f"job:{idempotency_key}"):
                return redis_conn.get(f"job:{idempotency_key}")
            
            result = func(*args, **kwargs)
            redis_conn.setex(f"job:{idempotency_key}", 86400, result)
            return result
        return wrapper
    ```

*   **Retry Limits & Alerting:**
    - Max retries: 3 with exponential backoff
    - On final failure: Send alert to Slack/email
    - Dead letter queue for manual investigation

#### 2.3.2. Scheduled Jobs

The chosen task runner will be used to schedule the following critical jobs:

*   **Nightly End-of-Day (EOD) Backfills:** Automated fetching and processing of EOD historical data for all tracked instruments. Uses idempotency keys based on date + symbol to prevent duplicate ingestion.
*   **Dividend/Split Ingestion:** Regular ingestion of corporate action data with idempotency keys based on corporate action ID to prevent double-processing.
*   **Benchmark & FX Rate Updates:** Daily or intra-day updates for benchmark indices and foreign exchange rates.
*   **Snapshotting Portfolio NAV:** Periodic snapshotting of portfolio Net Asset Value (NAV) for historical tracking.

### 2.4. Performance & Correctness

Optimizing for performance and ensuring data correctness are critical for a reliable financial application. This involves careful data storage strategies and robust handling of financial calculations.

#### 2.4.1. Data Storage for Prices, Holdings, and Transactions

*   **Prices Table:** The `prices` table will store tick-level or End-of-Day (EOD) data for instruments. 
    - **TimescaleDB Extension:** Use TimescaleDB for automatic time-series partitioning and compression
    - **Indexes:** 
      ```sql
      CREATE INDEX idx_prices_symbol_ts ON prices(symbol, ts DESC);
      CREATE INDEX idx_prices_ts ON prices(ts DESC) WHERE source = 'primary';
      ```

*   **Separation of Holdings and Transactions:**
    *   **Transactions (Immutable Lot-Level):** The `transactions` table will store immutable records.
        - **Index:** `CREATE INDEX idx_transactions_account_trade ON transactions(account_id, trade_date DESC);`
    *   **Holdings (Derived or Cached):** The `positions` table represents current holdings.
    *   **Tax Lots (FIFO/LIFO/Specific-ID):** 
        - **Index:** `CREATE INDEX idx_lots_instrument_open ON lots(instrument_id, open_ts) WHERE close_ts IS NULL;`

#### 2.4.2. Recomputing Holdings from Transactions

To ensure correctness, a process will be implemented to recompute holdings from transactions:

*   **On Demand:** Process all relevant transactions to derive current positions
*   **Incrementally:** Update the `positions` table based on latest buy/sell activities

##### 2.4.2.1 Position Calculation Order
1. Process transactions chronologically by settlement date (not trade date)
2. Apply corporate actions at exact ex-dividend/split dates
3. Handle partial fills as separate transactions
4. Account for T+2 settlement for US equities, T+1 for options
5. Use Decimal type for all monetary calculations:
    ```python
    from decimal import Decimal, ROUND_HALF_UP
    price = Decimal('123.456789').quantize(Decimal('0.01'), ROUND_HALF_UP)
    ```

### 2.5. APIs

The API layer will be designed to support both real-time updates and traditional RESTful interactions.

*   **RESTful Endpoints:** 
    *   `/api/v1/accounts`: CRUD operations for user accounts
    *   `/api/v1/instruments`: Lookup and management of financial instruments
    *   `/api/v1/transactions`: Recording and retrieving transaction history
    *   `/api/v1/prices/bulk`: Bulk price queries for multiple symbols (saves roundtrips)
    
*   **Pagination Format:**
    ```json
    {
      "items": [...],
      "next_cursor": "eyJvZmZzZXQiOjEwMH0=",
      "has_more": true,
      "total_count": 1543
    }
    ```

*   **Rate Limits:** 
    - Per user: 100 requests/minute for standard endpoints
    - Bulk endpoints: 20 requests/minute
    - WebSocket connections: 5 per user

*   **Key Endpoints:**
    *   `/import` (CSV from broker)
    *   `/export`: Export user data or reports
    *   `/rebalance/suggest`: Rebalancing suggestions
    *   `/alerts`: User-defined alerts management

*   **Authentication:** JWT-based with multi-tenant user scoping

### 2.6. Migrations & Typing

Maintaining a clean and consistent codebase is crucial for long-term development and stability.

*   **Alembic for Schema Migrations:** Version control of database schema
*   **Pydantic Models with Strict Types:** Data validation and documentation
*   **Contract Tests:** Schemathesis against OpenAPI spec for API contract validation
*   **Static Analysis:**
    *   **mypy:** Static type checking
    *   **ruff:** Fast linting and formatting
    *   **pytest:** Comprehensive test suite

### 2.7. Observability

Comprehensive observability is essential for monitoring the health, performance, and behavior of the application in production.

*   **Structured Logs:** JSON format with request IDs for tracing
*   **Log Sampling Policy:**
    - Errors: 100% logged
    - Warnings: 100% logged
    - Info: 1% sampling in production
    - Debug: Disabled in production

*   **OpenTelemetry Traces:** Distributed tracing for request flow visualization
*   **Metrics (Prometheus):** Key performance indicators and operational metrics
*   **Error Tracking (Sentry):** Real-time error tracking and alerting
*   **Synthetic Canary Portfolio:** Continuous validation test portfolio that runs P&L calculations every 5 minutes to detect calculation drift

### 2.8. Database Decision

**PostgreSQL will be used from MVP onwards**, not SQLite. Rationale:
- Concurrent writes required for real-time updates and multi-user access
- LISTEN/NOTIFY can replace some Redis pub/sub functionality
- Better suited for the multi-tenant architecture
- Native JSONB support for flexible schema evolution
- Row-level security for multi-tenancy

**Connection pooling:** Use PgBouncer with transaction pooling mode

**Row-Level Security:** Every table must have RLS policies defined. Example for `transactions`:
```sql
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY transactions_isolation ON transactions
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_user_id()
    ));
```

**Backup Strategy:** 
- Daily PITR (Point-In-Time Recovery) backups
- Weekly restore testing in staging environment
- 30-day retention for daily backups

## 3. Data Model

The financial planner's data model will be significantly expanded to support the new features.

### 3.1. Minimum Viable Tables

The following tables represent the minimum viable data model:

*   **`users`**: User authentication and profile information
*   **`accounts`**: Brokerage accounts linked by user
    - Attributes: `id`, `user_id`, `broker/source`, `base_currency`
    - RLS Policy: `user_id = current_user_id()`

*   **`instruments`**: Financial instrument metadata
    - Attributes: `id`, `symbol`, `exchange`, `asset_class`, `currency`, `name`, `isin/cusip`
    - Index: `CREATE UNIQUE INDEX idx_instruments_symbol ON instruments(symbol, exchange);`

*   **`prices`**: Historical and real-time price data (TimescaleDB hypertable)
    - Attributes: `instrument_id`, `ts`, `ohlc`, `adj_close`, `volume`, `source`
    - Partitioning: Monthly partitions via TimescaleDB

*   **`transactions`**: Immutable buy/sell records
    - Attributes: `id`, `account_id`, `instrument_id`, `side`, `qty`, `price`, `fee`, `trade_date`, `settlement_date`, `idempotency_key`, `note`
    - Unique constraint: `UNIQUE(idempotency_key)`
    - RLS Policy: Via account_id relationship

*   **`lots`**: Tax lot tracking
    - Attributes: `id`, `transaction_id`, `qty_open/closed`, `cost_basis`, `open_ts`, `close_ts`

*   **`positions`**: Cached current holdings
    - Attributes: `account_id`, `instrument_id`, `qty`, `avg_cost`, `last_update`

*   **`corporate_actions`**: Stock splits, dividends, etc.
    - Attributes: `id`, `type`, `instrument_id`, `ex_date`, `ratio`, `cash_amount`

*   **`benchmarks`**: Market benchmark data
*   **`fx_rates`**: Foreign exchange rates (TimescaleDB hypertable)
*   **`snapshots`**: Portfolio NAV snapshots
*   **`audit_log`**: Immutable audit trail (append-only)
    - Attributes: `id`, `user_id`, `action`, `entity_type`, `entity_id`, `old_value`, `new_value`, `timestamp`, `request_id`

### 3.2. Implications of the Expanded Data Model

*   **Immutability for Auditability:** Transactions and audit logs are immutable
*   **Granularity for Calculations:** Lot-level tracking for accurate tax calculations
*   **Performance Optimization:** Cached positions table for fast UI access
*   **Multi-Currency Support:** FX rates table for accurate multi-currency valuation
*   **Comprehensive Historical Analysis:** Complete data for performance analysis

## 4. Calculations

The financial planner will implement a comprehensive suite of calculations. All calculations must maintain version tracking via the `calculation_versions` table for auditability and reproducibility.

### 4.1. Cost Basis

*   **Per Lot:** Each lot stores original cost basis (purchase price + fees)
*   **Aggregation:** Average cost basis derived from open lots
*   **Tax Lot Methods:** FIFO, LIFO, and Specific-ID support

**Unit Test Example:**
```python
def test_fifo_cost_basis():
    transactions = [
        Buy(qty=100, price=10.00),  # Lot 1
        Buy(qty=50, price=12.00),   # Lot 2
        Sell(qty=75, price=15.00)   # Closes Lot 1 fully, Lot 2 partially
    ]
    assert calculate_cost_basis(transactions, method='FIFO') == {
        'realized_gain': 375.00,  # (75 * 15) - (75 * 10)
        'remaining_lots': [{'qty': 25, 'cost_basis': 12.00}]
    }
```

### 4.2. Returns

*   **Time-Weighted Rate of Return (TWRR):** Geometric linking of sub-period returns
*   **Money-Weighted Rate of Return (MWRR):** IRR calculation with Newton-Raphson
*   **Edge Cases:**
    - Zero-value periods: Special handling for -100% returns
    - Same-day deposits/withdrawals: Beginning-of-day for TWRR, actual time for MWRR
    - Iteration method: Newton-Raphson (max 100 iterations), fallback to bisection

**Benchmark Alignment Rule:** All returns must be calculated on the same trading-day calendar as the benchmark for accurate comparison.

### 4.3. Risk Metrics

*   **Volatility:** Standard deviation of returns (daily and annualized)
*   **Sharpe Ratio:** Risk-adjusted return metric
*   **Sortino Ratio:** Downside volatility focus
*   **Maximum Drawdown:** Largest peak-to-trough decline
*   **Beta:** Portfolio volatility relative to market
*   **Value at Risk (VaR):** 
    - Historical simulation using 252 trading days
    - 95% and 99% confidence levels
    - Update daily, cache for 1 hour during trading

**Unit Test Example:**
```python
def test_var_calculation():
    returns = [-0.05, -0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03, 0.04, 0.05]
    var_95 = calculate_var(returns, confidence=0.95)
    assert var_95 == -0.045  # 5th percentile of sorted returns
```

### 4.4. Attribution

*   **Sector/Asset-Class Contributions:** Performance breakdown by category
*   **Contributions by Trade:** Individual trade P&L analysis

### 4.5. FX (Foreign Exchange)

*   **Multi-Currency Valuation:** Daily FX rates for accurate valuation
*   **User's Base Currency:** All displays in user's chosen base currency

### 4.6. Dividends

*   **Reinvest or Cash:** Track dividend handling preference
*   **Gross vs. Net:** Distinguish pre/post withholding tax amounts
*   **Yield and Income Timeline:** Calculate yield and project income

**Note:** Monte Carlo simulations for stress testing will be added in future roadmap phases.

## 5. Frontend Enhancements (React + TS)

### 5.1. State/Data Management

*   **TanStack Query (React Query):** Server state management
*   **WebSocket Subscription:** Real-time price updates
*   **URL-Driven Filters:** Shareable links via query parameters
*   **Persist User Preferences:** localStorage for settings persistence
*   **Conflict Resolution:** Version numbers for optimistic updates
*   **Cache Invalidation:** 
    - Prices: 1-second TTL (market hours), 5-minute TTL (after hours)
    - Positions: Invalidate on transaction/corporate action
    - Corporate actions: 24-hour TTL
*   **Offline Mode:** Cache NAV and positions in localStorage for offline viewing

### 5.2. User Experience (UX)

*   **Portfolio Overview Card:** NAV, day change, YTD, movers
*   **Freshness Badge:** Display "Last quote: 15:32 ET (15-min delayed)" for data transparency
*   **Editable Transactions Grid:** CSV import, undo/redo, optimistic updates
*   **Allocation Visualization:** Interactive pie charts and treemaps
*   **Performance Metrics Display:** TWRR/MWRR toggle, drawdown chart
*   **Drill-Downs:** Lot view, dividend calendar, realized vs unrealized P&L
*   **Accessibility:** Target WCAG 2.2 AA compliance (keyboard navigation, ARIA labels)
*   **Mobile:** Responsive design for all screen sizes
*   **Loading States:** Skeleton screens and explicit error states for all async operations

### 5.3. Charts

*   **Recharts/Victory:** Customizable financial charts
*   **Decimation:** Performance optimization for long histories
*   **Crosshair + Tooltips:** Interactive data exploration
*   **Timezone-Aware Axes:** Accurate time display

## 6. Edge Cases & Rules

### 6.1. Data Anomalies and Market Conditions

*   **Non-trading Days, Halts, Stale Quotes:** Graceful handling with user notification
*   **Missing `adj_close`:** Fallback imputation strategy
*   **Splits/Symbol Changes:** Correct historical data mapping
*   **Penny Stocks/ETF Distributions:** Special handling for edge instruments
*   **Daylight Saving Time:** Proper timezone transitions handling

### 6.2. Trading and Accounting Rules

*   **Wash Sale Warnings (US):** 30-day window detection and warnings
*   **Short Sales:** Support negative positions in lots/positions tables
*   **Concurrent Edits:** Optimistic locking with version numbers, server conflict resolution

### 6.3. User Experience During Off-Market Hours

*   **"Live" Outside Market Hours:** Throttled updates with clear market status indication

## 7. Security & Compliance

### 7.1. Data Security

*   **Rate-Limiting:** External API calls throttled
*   **Aggressive Caching:** Reduce external system exposure
*   **Encryption:** 
    - In-transit: TLS 1.3
    - At-rest: AES-256
    - PII columns: pgcrypto or application-level encryption
*   **Secure Authentication:** JWT with rotation and XSS/CSRF protection
*   **Data Classification:**
    - Market data: Public
    - Transactions: Sensitive
    - PII: Restricted (encrypted)

### 7.2. Compliance

*   **CORS:** Locked to authorized frontend domain
*   **OAuth:** For broker integrations (Plaid, Alpaca)
*   **Clear Disclaimer:** "Informational only, not investment advice"
*   **Activity Logging:** Immutable audit log with WORM storage (S3 Object Lock)
*   **License Tracking:** Maintain compliance with market data provider licenses
*   **DSR SLA:** Respond to data deletion/export requests within 30 days

## 8. Deployment Architecture

### 8.1. Development Environment

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: portfolio_db
      POSTGRES_USER: portfolio_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  api:
    build: ./backend
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://portfolio_user:${DB_PASSWORD}@postgres:5432/portfolio_db
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
  
  worker:
    build: ./backend
    command: rq worker high default low
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://portfolio_user:${DB_PASSWORD}@postgres:5432/portfolio_db
      REDIS_URL: redis://redis:6379
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    environment:
      REACT_APP_API_URL: http://localhost:8000

volumes:
  postgres_data:
```

### 8.2. Production Considerations

*   **Deployment Strategy:** Blue/green deployments with canary rollout (5% → 25% → 100%)
*   **Horizontal Scaling:** 
    - API: Scale when CPU >70% or request latency p95 >500ms
    - Workers: Scale based on queue depth >1000
    - WebSockets: Scale when connections >5k per instance
*   **Database:** 
    - Primary-replica with read replicas
    - PgBouncer for connection pooling
    - Daily PITR backups with weekly restore tests
*   **Monitoring Dashboards (Grafana):**
    - API latency (p50, p95, p99)
    - WebSocket error rate
    - Job queue depth
    - Database connection pool utilization
*   **Health Checks:**
    ```python
    @app.get("/health")
    async def health_check():
        checks = {
            "database": check_db_connection(),
            "redis": check_redis_connection(),
            "timestamp": datetime.utcnow()
        }
        status = "healthy" if all(checks.values()) else "unhealthy"
        return {"status": status, "checks": checks}
    ```

## 9. Testing Strategy

### 9.1. Test Categories

*   **Unit Tests:** Cost basis, returns, corporate actions
*   **Integration Tests:** Provider fallback, transaction processing
*   **Property-Based Tests:** Using Hypothesis for invariant testing
*   **Contract Tests:** Schemathesis against OpenAPI spec
*   **Load Testing (k6):** Simulate 10k WebSocket clients
*   **Historical Replay:** 2008 crisis data validation
*   **Disaster Recovery Drills:** Quarterly PITR restore in staging

### 9.2. Test Data Management

*   **Fixtures:** Standard test portfolios with known results
*   **Mocking:** All external APIs mocked in tests
*   **Database:** Separate test database, reset between runs

## 10. Data Governance

### 10.1. Data Retention Policies

*   **Tick Data:** 30 days → 1-minute bars
*   **Minute Bars:** 1 year → hourly bars
*   **Daily Bars:** Indefinite
*   **Transactions:** Indefinite (immutable)
*   **Audit Logs:** 7 years (regulatory)
*   **Snapshots:** Daily for 1 year, then monthly

### 10.2. Calculation Versioning

```python
class CalculationVersion:
    VERSION = "2024.1"
    
    @versioned
    def calculate_twrr(self, data, version=None):
        if version == "2023.1":
            return self._twrr_v1(data)
        return self._twrr_v2(data)
```

### 10.3. GDPR/CCPA Compliance

*   **Data Export:** `/api/v1/user/export` returns all user data
*   **Data Deletion:** Soft delete (30 days), then hard delete
*   **Consent Tracking:** Store timestamps and versions

## 11. Roadmap

### Non-Goals

The following are explicitly out of scope:
- No trade execution capabilities
- No investment advisory services
- No real-time SIP feeds (professional data feeds)
- No margin trading support
- No options/derivatives pricing models

### 11.1. MVP (Minimum Viable Product) - Weeks 1-2

*   **PostgreSQL Setup with TimescaleDB**
*   **Core Models:** Accounts, Instruments, Transactions, Positions
*   **Quotes via yfinance (Polling)**
*   **Basic UI:** NAV Card, Allocation Pie, Position Table, Basic P&L
*   **CSV Import**
*   **Nightly EOD Snapshot Job**

### 11.2. V1 - Subsequent Weeks

*   **WebSockets/SSE Stream**
*   **Dividend & Split Handling**
*   **Benchmarks (SPY, QQQ)**
*   **TWRR/MWRR + Drawdown**
*   **FX Support**
*   **Reconciliation Reports** (moved from V2 - critical for data accuracy)
*   **Alerts (Price Crosses, % Change)**
*   **Auth, Multi-Tenant Scoping**
*   **Observability Stack**
*   **Bulk API Endpoints**
*   **Basic Webhooks**

### 11.3. V2 - Future Enhancements

*   **Specific-ID Lot Selection**
*   **Tax Reports (Form 8949)**
*   **Goal Tracking vs. Targets**
*   **Broker API Import (Plaid, Alpaca)**
*   **Rebalancing Suggestions**
*   **Correlation Matrix & Beta**
*   **Mobile-Optimized Layout**
*   **Watchlists**
*   **Scenario Testing ("What if")**
*   **Offline Mode with LocalStorage**
*   **Dark Mode Theme**
*   **Monte Carlo Simulations**