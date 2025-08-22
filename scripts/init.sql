-- Initial database setup script for AI Financial Planning System

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for performance
-- Note: Actual table creation will be handled by SQLAlchemy migrations

-- Initial data seeding can be added here
-- For example, default asset classes, risk profiles, etc.

-- Example: Insert default asset classes
-- INSERT INTO asset_classes (name, description, risk_level) VALUES
-- ('Stocks', 'Equity investments', 'high'),
-- ('Bonds', 'Fixed income securities', 'medium'),
-- ('Cash', 'Cash equivalents', 'low');

-- Create function for updating updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- This function will be applied to tables via SQLAlchemy triggers