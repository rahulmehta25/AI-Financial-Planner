-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable Row Level Security functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create custom types
CREATE TYPE transaction_side AS ENUM ('buy', 'sell');
CREATE TYPE asset_class AS ENUM ('stock', 'etf', 'bond', 'mutual_fund', 'crypto', 'cash', 'other');
CREATE TYPE account_type AS ENUM ('taxable', 'ira', 'roth_ira', '401k', 'hsa', 'other');

-- Function to get current user ID (will be set by application)
CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_user_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_email ON users(email);

-- Accounts table (brokerage accounts)
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    account_type account_type NOT NULL DEFAULT 'taxable',
    broker VARCHAR(255),
    account_number VARCHAR(255),
    base_currency CHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);

-- Enable RLS on accounts
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY accounts_isolation ON accounts
    FOR ALL
    USING (user_id = current_user_id());

-- Instruments table (stocks, ETFs, etc.)
CREATE TABLE IF NOT EXISTS instruments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(50),
    name VARCHAR(255),
    asset_class asset_class NOT NULL DEFAULT 'stock',
    currency CHAR(3) DEFAULT 'USD',
    isin VARCHAR(12),
    cusip VARCHAR(9),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX idx_instruments_symbol_exchange ON instruments(symbol, exchange);
CREATE INDEX idx_instruments_symbol ON instruments(symbol);

-- Prices table (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS prices (
    instrument_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    ts TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8) NOT NULL,
    adj_close DECIMAL(20, 8),
    volume BIGINT,
    source VARCHAR(50) DEFAULT 'yfinance',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('prices', 'ts', if_not_exists => TRUE);

CREATE INDEX idx_prices_instrument_ts ON prices(instrument_id, ts DESC);

-- Transactions table (immutable buy/sell records)
CREATE TABLE IF NOT EXISTS transactions (
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
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_transactions_account_trade ON transactions(account_id, trade_date DESC);
CREATE INDEX idx_transactions_instrument ON transactions(instrument_id);

-- Enable RLS on transactions
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY transactions_isolation ON transactions
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_user_id()
    ));

-- Tax lots table
CREATE TABLE IF NOT EXISTS lots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    quantity_open DECIMAL(20, 8) NOT NULL CHECK (quantity_open >= 0),
    quantity_closed DECIMAL(20, 8) DEFAULT 0 CHECK (quantity_closed >= 0),
    cost_basis DECIMAL(20, 8) NOT NULL,
    open_date DATE NOT NULL,
    close_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lots_account_instrument ON lots(account_id, instrument_id);
CREATE INDEX idx_lots_open ON lots(instrument_id, open_date) WHERE close_date IS NULL;

-- Enable RLS on lots
ALTER TABLE lots ENABLE ROW LEVEL SECURITY;

CREATE POLICY lots_isolation ON lots
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_user_id()
    ));

-- Positions table (cached current holdings)
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    quantity DECIMAL(20, 8) NOT NULL,
    avg_cost DECIMAL(20, 8) NOT NULL,
    last_price DECIMAL(20, 8),
    market_value DECIMAL(20, 8),
    unrealized_pl DECIMAL(20, 8),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, instrument_id)
);

CREATE INDEX idx_positions_account ON positions(account_id);

-- Enable RLS on positions
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;

CREATE POLICY positions_isolation ON positions
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_user_id()
    ));

-- Corporate actions table
CREATE TABLE IF NOT EXISTS corporate_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    action_type VARCHAR(50) NOT NULL, -- 'split', 'dividend', 'spinoff', etc.
    ex_date DATE NOT NULL,
    record_date DATE,
    payment_date DATE,
    ratio DECIMAL(20, 8), -- For splits
    cash_amount DECIMAL(20, 8), -- For dividends
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_corporate_actions_instrument ON corporate_actions(instrument_id);
CREATE INDEX idx_corporate_actions_ex_date ON corporate_actions(ex_date);

-- Portfolio snapshots table
CREATE TABLE IF NOT EXISTS snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_value DECIMAL(20, 8) NOT NULL,
    cash_value DECIMAL(20, 8) DEFAULT 0,
    positions_value DECIMAL(20, 8) DEFAULT 0,
    daily_change DECIMAL(20, 8),
    daily_change_pct DECIMAL(10, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(account_id, snapshot_date)
);

CREATE INDEX idx_snapshots_account_date ON snapshots(account_id, snapshot_date DESC);

-- Enable RLS on snapshots
ALTER TABLE snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY snapshots_isolation ON snapshots
    FOR ALL
    USING (account_id IN (
        SELECT id FROM accounts WHERE user_id = current_user_id()
    ));

-- Audit log table (immutable)
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at DESC);

-- Make audit_log append-only (no updates or deletes)
CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;

-- FX rates table (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS fx_rates (
    from_currency CHAR(3) NOT NULL,
    to_currency CHAR(3) NOT NULL,
    ts TIMESTAMP WITH TIME ZONE NOT NULL,
    rate DECIMAL(20, 8) NOT NULL,
    source VARCHAR(50) DEFAULT 'yfinance',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('fx_rates', 'ts', if_not_exists => TRUE);

CREATE INDEX idx_fx_rates_currencies_ts ON fx_rates(from_currency, to_currency, ts DESC);

-- Benchmarks table
CREATE TABLE IF NOT EXISTS benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default benchmarks
INSERT INTO benchmarks (symbol, name, description) VALUES
    ('SPY', 'SPDR S&P 500 ETF', 'Tracks the S&P 500 index'),
    ('QQQ', 'Invesco QQQ Trust', 'Tracks the NASDAQ-100 index'),
    ('AGG', 'iShares Core U.S. Aggregate Bond ETF', 'Tracks the US bond market'),
    ('VTI', 'Vanguard Total Stock Market ETF', 'Tracks the entire US stock market')
ON CONFLICT (symbol) DO NOTHING;

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_instruments_updated_at BEFORE UPDATE ON instruments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lots_updated_at BEFORE UPDATE ON lots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
GRANT ALL ON ALL TABLES IN SCHEMA public TO portfolio_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO portfolio_user;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO portfolio_user;