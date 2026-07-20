# AI Financial Planner - Development Roadmap

## Project Vision
Build a sophisticated portfolio tracker with AI-powered financial education that helps DIY investors manage their investments across multiple accounts, optimize taxes, and learn sound financial principles - without providing risky investment advice.

## Core Principles
- **Real portfolio tracking** over theoretical simulations
- **Educational AI guidance** over predictive advice
- **Tax optimization** as a key differentiator
- **Privacy-first** with no data selling
- **Transparent calculations** users can verify

---

## Phase 1: MVP - Core Portfolio Tracking (Weeks 1-2)

### Database Foundation
- [ ] Set up PostgreSQL with TimescaleDB extension:
  ```sql
  CREATE EXTENSION IF NOT EXISTS timescaledb;
  ```
- [ ] Implement core data models with Row-Level Security:
  - [ ] `users` table with authentication
  - [ ] `accounts` table with RLS policy:
    ```sql
    ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
    CREATE POLICY accounts_isolation ON accounts
      FOR ALL USING (user_id = current_user_id());
    ```
  - [ ] `instruments` table for stocks/ETFs metadata
  - [ ] `transactions` table (immutable, with idempotency keys):
    ```sql
    UNIQUE(idempotency_key)
    ```
  - [ ] `positions` table (cached current holdings)
  - [ ] `prices` table (TimescaleDB hypertable):
    ```sql
    SELECT create_hypertable('prices', 'ts');
    ```
- [ ] Create critical indexes:
  ```sql
  CREATE INDEX idx_prices_symbol_ts ON prices(symbol, ts DESC);
  CREATE INDEX idx_transactions_account_trade ON transactions(account_id, trade_date DESC);
  CREATE UNIQUE INDEX idx_instruments_symbol ON instruments(symbol, exchange);
  ```
- [ ] Set up PgBouncer for connection pooling

### Backend Foundation
- [ ] Create data provider abstraction layer:
  - [ ] `YFinanceProvider` as primary (with 15-min delay disclaimer)
  - [ ] Circuit breaker implementation (3 failures = 60s timeout)
  - [ ] Retry policy with exponential backoff [1s, 2s, 4s, 8s]
  - [ ] Cache layer with Redis for last good quotes
- [ ] Implement transaction processing:
  - [ ] CSV import parser (support Fidelity, Vanguard, Schwab formats)
  - [ ] Idempotency key generation for imports
  - [ ] Position calculation from transactions
  - [ ] Basic FIFO cost basis tracking
  - [ ] **Basic reconciliation process** (flag discrepancies)
- [ ] Set up RQ (Redis Queue) for background jobs:
  - [ ] Nightly EOD price snapshot job
  - [ ] Position reconciliation job
  - [ ] Failed job alerting

### API Layer
- [ ] FastAPI endpoints with rate limiting:
  - [ ] `POST /api/v1/import` - CSV import (idempotent)
  - [ ] `GET /api/v1/portfolio` - Portfolio overview
  - [ ] `GET /api/v1/positions` - Current positions
  - [ ] `GET /api/v1/transactions` - Transaction history
  - [ ] `GET /api/v1/quotes/{symbols}` - Bulk quote endpoint
  - [ ] `GET /health` - Health check with dependency status
- [ ] JWT authentication with user scoping
- [ ] Request validation with Pydantic models
- [ ] Structured logging with request IDs

### Frontend Foundation
- [ ] Set up React + TypeScript + Vite
- [ ] Implement TanStack Query for server state
- [ ] Core components:
  - [ ] Portfolio Overview Card (NAV, day change, total return)
  - [ ] Holdings Table (symbol, shares, cost basis, current value, gain/loss)
  - [ ] **Data Freshness Indicator** ("Last updated: 15-min delayed")
  - [ ] Simple Allocation Pie Chart (using Recharts)
  - [ ] CSV Import Wizard with error handling
- [ ] Basic responsive layout with Tailwind CSS

### Observability & Testing (From Day 1)
- [ ] Structured JSON logging with correlation IDs
- [ ] Basic Prometheus metrics:
  - [ ] API request count/latency
  - [ ] Job queue depth
  - [ ] Database connection pool usage
- [ ] Error tracking with Sentry
- [ ] Unit tests for:
  - [ ] Cost basis calculations (>95% coverage)
  - [ ] Position reconciliation
  - [ ] CSV parsing
- [ ] Integration tests for transaction import flow

### Database & DevOps
- [ ] Alembic migration setup with rollback scripts
- [ ] Daily PITR backup configuration
- [ ] Docker Compose for local development:
  - [ ] PostgreSQL + TimescaleDB
  - [ ] PgBouncer
  - [ ] Redis
  - [ ] API service
  - [ ] Worker service
  - [ ] Frontend dev server

**MVP Success Criteria:**
- Import transactions from CSV with 99.9% accuracy
- Portfolio NAV matches broker statements within $0.01
- Calculations complete in <100ms for 1000 transactions
- Health endpoint responds in <50ms
- All tests passing with >90% coverage

---

## Phase 2: Real-Time Updates & Better Calculations (Weeks 3-4)

### Real-Time Data Infrastructure
- [ ] WebSocket implementation with scaling strategy:
  - [ ] `/ws/market_data` endpoint
  - [ ] Connection pooling (max 5 per user)
  - [ ] Heartbeat/ping-pong every 30 seconds
  - [ ] Message queuing for disconnection (max 1000 messages)
  - [ ] Graceful fallback to polling with user notification
  - [ ] Redis Cluster setup plan for >5k connections:
    ```yaml
    # Document scaling thresholds
    < 5k connections: Single Redis
    > 5k connections: Redis Cluster with pub/sub nodes
    ```
- [ ] Redis Pub/Sub for quote fan-out:
  - [ ] Channel per symbol pattern
  - [ ] Batch updates for efficiency
  - [ ] TTL on cached quotes (1s market hours, 5m after)
- [ ] Enhanced data provider chain:
  - [ ] Add fallback providers (Alpha Vantage, IEX free tier)
  - [ ] Provider health monitoring dashboard
  - [ ] Automatic fallback on circuit breaker open
- [ ] Market hours awareness:
  - [ ] NYSE calendar integration
  - [ ] Pre/post-market flags with UI indicators
  - [ ] Auto-throttle updates outside market hours

### Enhanced Financial Calculations
- [ ] Returns calculation with proper edge cases:
  - [ ] Time-Weighted Rate of Return (TWRR) with same-day handling
  - [ ] Money-Weighted Rate of Return (MWRR/IRR) with Newton-Raphson
  - [ ] Handle zero-value periods and -100% returns
- [ ] Risk metrics with caching:
  - [ ] Volatility (252 trading days for annual)
  - [ ] Sharpe ratio with configurable risk-free rate
  - [ ] Maximum drawdown with recovery tracking
  - [ ] Beta calculation vs S&P 500
- [ ] Advanced cost basis:
  - [ ] FIFO/LIFO/Specific-ID methods
  - [ ] Lot selection UI with tax impact preview
  - [ ] Wash sale detection (30-day window)
- [ ] Corporate actions handling:
  - [ ] Stock splits with back-adjustment
  - [ ] Dividend tracking (ordinary vs qualified)
  - [ ] Spin-off handling
  - [ ] Symbol change mapping

### Data Quality & Reconciliation
- [ ] Automated reconciliation system:
  - [ ] Daily position vs transaction reconciliation
  - [ ] Cost basis verification
  - [ ] Corporate action adjustment validation
- [ ] Data quality monitoring:
  - [ ] Anomaly detection for price spikes
  - [ ] Stale quote detection
  - [ ] Missing data alerts

### Frontend Enhancements
- [ ] WebSocket integration with reconnection logic
- [ ] Interactive performance charts:
  - [ ] Portfolio value over time with zoom
  - [ ] Benchmark comparison (SPY, QQQ, AGG)
  - [ ] Drawdown visualization
  - [ ] Contribution vs growth breakdown
- [ ] Enhanced transaction management:
  - [ ] Edit with optimistic updates and conflict resolution
  - [ ] Bulk operations support
  - [ ] Undo/redo functionality
- [ ] Advanced position views:
  - [ ] Lot-level breakdown
  - [ ] Unrealized gains by tax status (short/long term)
  - [ ] Tax loss harvesting opportunities

### Testing & Performance
- [ ] Load testing WebSocket connections:
  - [ ] Simulate 1000 concurrent connections
  - [ ] Measure message latency distribution
  - [ ] Test reconnection storms
- [ ] Calculation accuracy tests:
  - [ ] TWRR/MWRR against known results
  - [ ] Cost basis with complex scenarios
  - [ ] Corporate action adjustments

---

## Phase 3: AI Financial Education Layer (Weeks 5-6)

### Safe AI Integration
- [ ] LLM integration (GPT-4 or Claude):
  - [ ] System prompts for financial education focus
  - [ ] Response filtering to prevent speculation
  - [ ] Confidence scoring for responses
- [ ] AI Safety Framework:
  - [ ] Level 1: Math & Facts only endpoints
  - [ ] Level 2: Established principles responses
  - [ ] Level 3: Contextual guidance with disclaimers
  - [ ] Stock mention governor (max 3/week)

### Portfolio Analysis AI Features
- [ ] Portfolio Health Checker:
  - [ ] Concentration risk analysis
  - [ ] Sector allocation review
  - [ ] Fee analysis
  - [ ] Diversification scoring
- [ ] Educational explanations:
  - [ ] "Why is my portfolio risky?"
  - [ ] "What is dividend yield?"
  - [ ] "How do expense ratios affect returns?"
- [ ] Safe portfolio templates:
  - [ ] Three-fund portfolio explainer
  - [ ] Target-date fund matcher
  - [ ] Age-appropriate allocation suggestions

### Market Awareness Features
- [ ] Daily Market Brief:
  - [ ] Major market moves explanation
  - [ ] Portfolio impact analysis
  - [ ] Historical context for volatility
- [ ] Exceptional events narrator:
  - [ ] Only mention individual stocks for 15%+ moves
  - [ ] Always include ETF alternatives
  - [ ] Historical humility (past "winners" that failed)

### Tax Strategy Assistant
- [ ] Tax loss harvesting identifier:
  - [ ] Show harvestable losses
  - [ ] Wash sale warning system
  - [ ] Tax lot optimization suggestions
- [ ] Contribution optimizer:
  - [ ] 401(k) match calculator
  - [ ] IRA vs Roth analyzer
  - [ ] HSA priority reminder
- [ ] Year-end tax planning checklist

---

## Phase 4: Tax Optimization & Multi-Account (Weeks 7-8)

### Advanced Tax Features
- [ ] Tax lot management:
  - [ ] Specific lot identification
  - [ ] Tax-efficient sale suggestions
  - [ ] Wash sale rule tracking (30-day window)
- [ ] Multi-account optimization:
  - [ ] Asset location optimizer (bonds in IRA, stocks in taxable)
  - [ ] Rebalancing across accounts
- [ ] Tax reports:
  - [ ] Realized gains/losses report
  - [ ] Estimated tax liability
  - [ ] Form 8949 draft data

### Account Types Support
- [ ] Account classifications:
  - [ ] Taxable
  - [ ] Traditional IRA
  - [ ] Roth IRA
  - [ ] 401(k)
  - [ ] HSA
- [ ] Account-specific rules:
  - [ ] Contribution limits tracking
  - [ ] RMD calculations
  - [ ] Early withdrawal penalties

### Multi-Currency Support
- [ ] FX rate integration
- [ ] Base currency selection per user
- [ ] Multi-currency portfolio valuation
- [ ] Currency impact reporting

---

## Phase 5: Retirement & Goals Planning (Weeks 9-10)

### Retirement Calculator
- [ ] Monte Carlo simulation (simplified):
  - [ ] Based on historical returns only
  - [ ] No speculation, just probabilities
  - [ ] Success rate visualization
- [ ] Safe withdrawal rate calculator:
  - [ ] 4% rule implementation
  - [ ] Dynamic withdrawal strategies
  - [ ] Social Security integration
- [ ] Retirement readiness score:
  - [ ] Years to retirement
  - [ ] Required vs projected savings
  - [ ] Healthcare gap analysis

### Goal Tracking
- [ ] Goal creation interface:
  - [ ] Retirement
  - [ ] House purchase
  - [ ] Education funding
  - [ ] Custom goals
- [ ] Progress tracking:
  - [ ] Current vs required savings rate
  - [ ] Projected achievement date
  - [ ] Contribution recommendations

### AI Retirement Advisor
- [ ] Safe retirement guidance:
  - [ ] "Can I retire?" calculator
  - [ ] Healthcare cost estimates
  - [ ] Geographic arbitrage education
- [ ] Scenario testing:
  - [ ] "What if market drops 30%?"
  - [ ] "What if I retire 5 years early?"
  - [ ] "What if inflation is 5%?"

---

## Phase 6: Production Readiness (Weeks 11-12)

### Security & Compliance
- [ ] Security hardening:
  - [ ] Rate limiting per endpoint
  - [ ] CORS configuration
  - [ ] SQL injection prevention
  - [ ] XSS protection
- [ ] Data privacy:
  - [ ] Encryption at rest (PII columns)
  - [ ] Audit logging (immutable)
  - [ ] Data export API (GDPR)
  - [ ] Account deletion flow
- [ ] Legal disclaimers:
  - [ ] "Not investment advice" banners
  - [ ] Terms of service
  - [ ] Privacy policy

### Performance Optimization
- [ ] Database optimization:
  - [ ] Proper indexes on all queries
  - [ ] Query performance monitoring
  - [ ] Connection pooling with PgBouncer
- [ ] Caching strategy:
  - [ ] Redis for quotes (1s TTL market hours)
  - [ ] CDN for static assets
  - [ ] Service worker for offline mode
- [ ] Frontend optimization:
  - [ ] Code splitting
  - [ ] Lazy loading
  - [ ] Image optimization

### Observability
- [ ] Monitoring stack:
  - [ ] Prometheus metrics
  - [ ] Grafana dashboards
  - [ ] Sentry error tracking
- [ ] Key metrics:
  - [ ] API latency (p50, p95, p99)
  - [ ] WebSocket connection count
  - [ ] Job queue depth
  - [ ] Error rates by endpoint
- [ ] Alerting rules:
  - [ ] API down
  - [ ] High error rate
  - [ ] Queue backup
  - [ ] Database connection exhaustion

### Testing
- [ ] Test coverage:
  - [ ] Unit tests for calculations (>90% coverage)
  - [ ] Integration tests for data flow
  - [ ] E2E tests for critical paths
- [ ] Test scenarios:
  - [ ] Cost basis calculations
  - [ ] Corporate actions
  - [ ] Tax lot selection
  - [ ] Return calculations
- [ ] Load testing:
  - [ ] 1000 concurrent users
  - [ ] 10k WebSocket connections

---

## Phase 7: Growth Features (Future)

### Broker Integration
- [ ] Plaid integration for account sync
- [ ] Direct broker APIs (Alpaca, TD Ameritrade)
- [ ] Automated transaction import

### Advanced Analytics
- [ ] Factor analysis
- [ ] Correlation matrices
- [ ] Custom benchmarks
- [ ] Peer comparison (anonymized)

### Mobile App
- [ ] React Native implementation
- [ ] Biometric authentication
- [ ] Push notifications for alerts

### Premium Features
- [ ] Advisor collaboration tools
- [ ] Family account management
- [ ] Estate planning features
- [ ] Advanced tax strategies

---

## Non-Goals (Explicitly Out of Scope)

- ❌ Trade execution capabilities
- ❌ Margin trading support
- ❌ Options pricing models
- ❌ Cryptocurrency trading
- ❌ Social trading features
- ❌ Payment processing
- ❌ Direct investment advice
- ❌ Market predictions

---

## Success Metrics

### MVP Success (End of Week 2):
- [ ] 10 beta users successfully import portfolios
- [ ] NAV calculation matches broker statements within $0.01
- [ ] Successfully fetch and display daily prices
- [ ] Data accuracy: 99.9% match with broker statements
- [ ] Cost basis calculation <100ms for 1000 transactions
- [ ] Zero data loss incidents

### V1 Success (End of Week 6):
- [ ] 100 active users
- [ ] Real-time updates working for 50+ concurrent users
- [ ] WebSocket message latency <300ms (p95)
- [ ] AI provides helpful education without speculation
- [ ] Tax loss harvesting identifies real opportunities
- [ ] Reconciliation catches 100% of discrepancies

### Production Success (End of Week 12):
- [ ] 99.9% uptime during market hours
- [ ] API response time: p50 <100ms, p95 <500ms, p99 <1s
- [ ] 500+ active users with 5k+ portfolios tracked
- [ ] Zero security incidents or data breaches
- [ ] Positive user feedback on AI education (NPS >50)
- [ ] Calculation accuracy: 99.99% for all financial metrics

## Performance Benchmarks

### Calculation Performance Targets
- Portfolio NAV calculation: <50ms for 100 positions
- Cost basis (FIFO): <100ms for 1000 transactions
- TWRR calculation: <200ms for 5 years of daily data
- Tax loss harvesting scan: <500ms for 100 positions
- Full portfolio reconciliation: <5s for 1000 transactions

### Data Pipeline Targets
- Quote fetch latency: <100ms from provider
- WebSocket broadcast: <50ms from receipt to client
- Bulk price update: <1s for 500 symbols
- EOD snapshot job: <5 minutes for all users
- CSV import: <10s for 10,000 transactions

### Scale Targets
- Concurrent WebSocket connections: 5,000
- Transactions per portfolio: 10,000
- Portfolios per user: 10
- API requests/second: 1,000
- Background jobs/minute: 10,000

---

## Data Provider Licensing Timeline

### Current State (MVP-V1)
- **yfinance**: Free, 15-minute delayed data
- **Alpha Vantage**: Free tier, 5 requests/minute
- **IEX Cloud**: Free tier, 50k messages/month

### Future Licensing Needs (V2+)
- **Month 3-6**: 
  - IEX Cloud Launch plan ($199/month) for reliable data
  - Polygon.io Stocks Starter ($29/month) for better coverage
- **Month 6-12**:
  - Polygon.io Stocks Pro ($299/month) for real-time WebSocket
  - Consider Databento for tick-level data
- **Year 2+**:
  - Direct exchange feeds (expensive, regulatory requirements)
  - Professional terminal access for institutional features

**Important**: Always display data delay disclaimers until licensed feeds are obtained.

---

## Technical Debt to Track

- [ ] Add comprehensive data provider abstraction
- [ ] Implement proper event sourcing for transactions
- [ ] Build comprehensive reconciliation system
- [ ] Create testing fixtures with known calculations
- [ ] Document API with OpenAPI spec
- [ ] Add request tracing with correlation IDs
- [ ] Implement proper secret management (HashiCorp Vault)
- [ ] Automate database backup testing
- [ ] Add calculation versioning system
- [ ] Implement audit log with WORM storage

---

## Development Principles

1. **Start Simple**: Get basic portfolio tracking working before adding complex features
2. **Real Data First**: Use actual market data, not simulations
3. **User Safety**: Never provide specific investment advice
4. **Educational Focus**: Teach principles, not predictions
5. **Progressive Enhancement**: Each phase should be independently valuable
6. **Test Everything**: Financial calculations must be 100% accurate
7. **Security First**: Handle user financial data with extreme care

---

## Quick Start Commands

```bash
# Local development
docker-compose up

# Run tests
pytest backend/tests

# Database migrations
alembic upgrade head

# Start workers
rq worker high default low

# Frontend dev
cd frontend && npm run dev
```

---

*Last Updated: [Current Date]*
*Version: 1.0.0*