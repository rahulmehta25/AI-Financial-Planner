# Production Backend Setup Guide

## Option 1: Heroku (Easiest - $25/month)

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Create app
heroku create your-financial-planner-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis
heroku addons:create heroku-redis:mini

# Deploy
git push heroku main

# Set environment variables
heroku config:set ALPHA_VANTAGE_API_KEY=your_key
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
```

## Option 2: Railway.app (Modern - $20/month)

1. Connect GitHub repo at railway.app
2. Add PostgreSQL service
3. Add Redis service
4. Set environment variables
5. Auto-deploys on push

## Option 3: AWS (Scalable - $50-100/month)

```bash
# Use AWS Copilot
copilot app init financial-planner
copilot env init --name production
copilot svc init --name api
copilot svc deploy --name api --env production
```

## Option 4: DigitalOcean App Platform ($40/month)

```yaml
# app.yaml
name: financial-planner
services:
- name: api
  github:
    repo: your-repo
    branch: main
  build_command: pip install -r requirements.txt
  run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
databases:
- name: db
  engine: PG
  version: "15"
- name: redis
  engine: REDIS
  version: "7"
```

## Recommended: Start with Railway.app

**Why Railway?**
- One-click PostgreSQL and Redis
- Automatic SSL certificates
- GitHub integration
- $5 free credit to start
- Scales automatically
- Great developer experience

## Essential First Steps:

1. **Get Free API Keys:**
   - Alpha Vantage: https://www.alphavantage.co/support/#api-key
   - Finnhub: https://finnhub.io/register
   - Optional: OpenAI API for AI features

2. **Set up monitoring:**
   - Sentry for error tracking (free tier)
   - Datadog or New Relic for APM (free tier)

3. **Security essentials:**
   - Use environment variables for ALL secrets
   - Enable CORS properly
   - Add rate limiting
   - Use HTTPS only

## Database Schema to Start:

```sql
-- Core tables needed first
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE portfolios (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE holdings (
    id UUID PRIMARY KEY,
    portfolio_id UUID REFERENCES portfolios(id),
    symbol VARCHAR(10) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    cost_basis DECIMAL(20, 2),
    purchased_at DATE
);

CREATE TABLE market_data (
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(20, 4),
    high DECIMAL(20, 4),
    low DECIMAL(20, 4),
    close DECIMAL(20, 4),
    volume BIGINT,
    PRIMARY KEY (symbol, date)
);
```