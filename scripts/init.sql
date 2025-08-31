-- Initialize financial planning database
-- Note: CREATE DATABASE doesn't support IF NOT EXISTS in PostgreSQL
-- These databases are created via environment variables in docker-compose

-- Create extensions for main database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Basic user table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table (brokerage accounts linked by user)
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50), -- '401k', 'roth_ira', 'taxable', etc.
    institution VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Instruments table (stocks, ETFs, etc.)
CREATE TABLE IF NOT EXISTS instruments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    asset_class VARCHAR(50),
    exchange VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table (immutable buy/sell records)
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    instrument_id UUID REFERENCES instruments(id),
    transaction_type VARCHAR(20) NOT NULL, -- 'buy', 'sell', 'dividend', etc.
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    total_amount DECIMAL(20, 8),
    fee DECIMAL(20, 8) DEFAULT 0,
    trade_date DATE NOT NULL,
    settlement_date DATE,
    idempotency_key VARCHAR(255) UNIQUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Positions table (cached current holdings)
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    instrument_id UUID REFERENCES instruments(id),
    quantity DECIMAL(20, 8) NOT NULL,
    average_cost DECIMAL(20, 8),
    market_value DECIMAL(20, 8),
    unrealized_gain DECIMAL(20, 8),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, instrument_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_account_trade ON transactions(account_id, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_id);
CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);

-- Insert sample data
INSERT INTO users (email) VALUES ('demo@financialplanner.com') ON CONFLICT (email) DO NOTHING;