-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE transaction_side AS ENUM ('buy', 'sell');
CREATE TYPE asset_class AS ENUM ('equity', 'etf', 'mutual_fund', 'bond', 'cash', 'crypto', 'commodity', 'other');
CREATE TYPE account_type AS ENUM ('taxable', 'traditional_ira', 'roth_ira', '401k', 'hsa', 'other');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Accounts table with RLS
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    account_type account_type NOT NULL,
    broker VARCHAR(255),
    account_number VARCHAR(255),
    base_currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Enable Row Level Security
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for accounts
CREATE POLICY accounts_isolation ON accounts
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Instruments table
CREATE TABLE instruments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50),
    name VARCHAR(255),
    asset_class asset_class NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    isin VARCHAR(12),
    cusip VARCHAR(9),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, exchange)
);

-- Create indexes for instruments
CREATE UNIQUE INDEX idx_instruments_symbol ON instruments(symbol, exchange);
CREATE INDEX idx_instruments_asset_class ON instruments(asset_class);

-- Prices table (TimescaleDB hypertable)
CREATE TABLE prices (
    instrument_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL,
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8) NOT NULL,
    adj_close DECIMAL(20, 8),
    volume BIGINT,
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (instrument_id, ts)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('prices', 'ts', chunk_time_interval => INTERVAL '1 month');

-- Create indexes for prices
CREATE INDEX idx_prices_symbol_ts ON prices(instrument_id, ts DESC);
CREATE INDEX idx_prices_ts ON prices(ts DESC) WHERE source = 'primary';

-- Transactions table (immutable)
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    side transaction_side NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(20, 8) NOT NULL CHECK (price >= 0),
    fee DECIMAL(20, 8) DEFAULT 0 CHECK (fee >= 0),
    trade_date DATE NOT NULL,
    settlement_date DATE,
    idempotency_key VARCHAR(255) UNIQUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT positive_quantity CHECK (quantity > 0)
);

-- Create indexes for transactions
CREATE INDEX idx_transactions_account_trade ON transactions(account_id, trade_date DESC);
CREATE INDEX idx_transactions_account_instrument ON transactions(account_id, instrument_id);
CREATE UNIQUE INDEX idx_transactions_idempotency ON transactions(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Enable RLS on transactions
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY transactions_isolation ON transactions
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

-- Tax lots table
CREATE TABLE lots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    quantity_open DECIMAL(20, 8) NOT NULL,
    quantity_closed DECIMAL(20, 8) DEFAULT 0,
    cost_basis DECIMAL(20, 8) NOT NULL,
    open_date DATE NOT NULL,
    close_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_quantities CHECK (quantity_open >= quantity_closed AND quantity_closed >= 0)
);

-- Create indexes for lots
CREATE INDEX idx_lots_instrument_open ON lots(instrument_id, open_date) WHERE close_date IS NULL;
CREATE INDEX idx_lots_account_instrument ON lots(account_id, instrument_id);

-- Enable RLS on lots
ALTER TABLE lots ENABLE ROW LEVEL SECURITY;

CREATE POLICY lots_isolation ON lots
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

-- Positions table (cached current holdings)
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    quantity DECIMAL(20, 8) NOT NULL,
    average_cost DECIMAL(20, 8),
    market_value DECIMAL(20, 8),
    unrealized_gain DECIMAL(20, 8),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, instrument_id)
);

-- Create indexes for positions
CREATE INDEX idx_positions_account ON positions(account_id);
CREATE INDEX idx_positions_account_instrument ON positions(account_id, instrument_id);

-- Enable RLS on positions
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;

CREATE POLICY positions_isolation ON positions
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

-- Corporate actions table
CREATE TABLE corporate_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    action_type VARCHAR(50) NOT NULL, -- 'split', 'dividend', 'spinoff', etc.
    ex_date DATE NOT NULL,
    record_date DATE,
    payment_date DATE,
    ratio DECIMAL(20, 8), -- For splits
    cash_amount DECIMAL(20, 8), -- For dividends
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for corporate actions
CREATE INDEX idx_corporate_actions_instrument ON corporate_actions(instrument_id);
CREATE INDEX idx_corporate_actions_ex_date ON corporate_actions(ex_date DESC);

-- Benchmarks table
CREATE TABLE benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- FX rates table (TimescaleDB hypertable)
CREATE TABLE fx_rates (
    base_currency VARCHAR(3) NOT NULL,
    quote_currency VARCHAR(3) NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    rate DECIMAL(20, 8) NOT NULL CHECK (rate > 0),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (base_currency, quote_currency, ts)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('fx_rates', 'ts', chunk_time_interval => INTERVAL '1 month');

-- Portfolio snapshots table
CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_value DECIMAL(20, 8) NOT NULL,
    cash_value DECIMAL(20, 8) DEFAULT 0,
    positions_value DECIMAL(20, 8) DEFAULT 0,
    daily_return DECIMAL(10, 6),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_id, snapshot_date)
);

-- Create indexes for snapshots
CREATE INDEX idx_snapshots_account_date ON portfolio_snapshots(account_id, snapshot_date DESC);

-- Enable RLS on snapshots
ALTER TABLE portfolio_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY snapshots_isolation ON portfolio_snapshots
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

-- Audit log table (immutable, append-only)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for audit log
CREATE INDEX idx_audit_log_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id, timestamp DESC);
CREATE INDEX idx_audit_log_request ON audit_log(request_id);

-- Insert default benchmarks
INSERT INTO benchmarks (symbol, name, description) VALUES
    ('SPY', 'SPDR S&P 500 ETF', 'Tracks the S&P 500 index'),
    ('QQQ', 'Invesco QQQ Trust', 'Tracks the NASDAQ-100 index'),
    ('AGG', 'iShares Core US Aggregate Bond ETF', 'Tracks the US bond market'),
    ('VTI', 'Vanguard Total Stock Market ETF', 'Tracks the entire US stock market');

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_instruments_updated_at BEFORE UPDATE ON instruments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lots_updated_at BEFORE UPDATE ON lots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your user)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO portfolio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO portfolio_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO portfolio_user;