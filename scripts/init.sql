-- Initialize financial planning database
CREATE DATABASE IF NOT EXISTS financial_planner;
CREATE DATABASE IF NOT EXISTS financial_planner_ts;

-- Create extensions for TimescaleDB
\c financial_planner_ts;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Basic user table
\c financial_planner;
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample user
INSERT INTO users (email) VALUES ('demo@financialplanner.com') ON CONFLICT DO NOTHING;
