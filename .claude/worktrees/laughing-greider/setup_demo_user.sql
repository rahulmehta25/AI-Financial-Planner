-- Setup Demo User for AI Financial Planner
-- Run this in Supabase SQL editor AFTER running supabase_schema.sql

-- Note: You cannot directly insert into auth.users from SQL editor
-- Instead, create the demo user through Supabase Auth Admin panel or use this approach:

-- 1. First, create the demo user through Supabase Dashboard:
--    Go to Authentication > Users > Invite User
--    Email: demo@financeai.com
--    Password: demo123

-- 2. After the user is created, get their UUID from the auth.users table
-- You can find it in Authentication > Users section

-- 3. Replace 'YOUR_DEMO_USER_UUID' below with the actual UUID and run this script:

-- Example demo data (uncomment and modify the UUID after creating the user):
/*
-- Insert demo portfolio
INSERT INTO public.portfolios (user_id, name, description, is_default)
VALUES (
  'YOUR_DEMO_USER_UUID',  -- Replace with actual demo user UUID
  'Demo Portfolio',
  'A sample portfolio for demonstration purposes',
  true
);

-- Get the portfolio ID for subsequent inserts
WITH demo_portfolio AS (
  SELECT id FROM public.portfolios 
  WHERE user_id = 'YOUR_DEMO_USER_UUID' 
  AND name = 'Demo Portfolio'
  LIMIT 1
)
-- Insert demo holdings
INSERT INTO public.holdings (portfolio_id, symbol, quantity, cost_basis, purchase_date, asset_type, current_price, current_value, gain_loss, gain_loss_percent)
SELECT 
  dp.id,
  vals.symbol,
  vals.quantity,
  vals.cost_basis,
  vals.purchase_date,
  vals.asset_type,
  vals.current_price,
  vals.current_value,
  vals.gain_loss,
  vals.gain_loss_percent
FROM demo_portfolio dp,
(VALUES
  ('AAPL', 50, 150.00, '2024-01-15', 'stock', 175.00, 8750.00, 1250.00, 16.67),
  ('GOOGL', 20, 120.00, '2024-02-01', 'stock', 145.00, 2900.00, 500.00, 20.83),
  ('MSFT', 30, 300.00, '2024-01-20', 'stock', 380.00, 11400.00, 2400.00, 26.67),
  ('TSLA', 15, 200.00, '2024-03-01', 'stock', 250.00, 3750.00, 750.00, 25.00),
  ('BTC', 0.5, 40000.00, '2024-01-01', 'crypto', 65000.00, 32500.00, 12500.00, 62.50),
  ('ETH', 5, 2000.00, '2024-02-15', 'crypto', 3500.00, 17500.00, 7500.00, 75.00)
) AS vals(symbol, quantity, cost_basis, purchase_date, asset_type, current_price, current_value, gain_loss, gain_loss_percent);

-- Insert demo transactions
WITH demo_portfolio AS (
  SELECT id FROM public.portfolios 
  WHERE user_id = 'YOUR_DEMO_USER_UUID' 
  AND name = 'Demo Portfolio'
  LIMIT 1
)
INSERT INTO public.transactions (portfolio_id, symbol, transaction_type, quantity, price, total_amount, transaction_date, notes)
SELECT 
  dp.id,
  vals.symbol,
  vals.transaction_type,
  vals.quantity,
  vals.price,
  vals.total_amount,
  vals.transaction_date,
  vals.notes
FROM demo_portfolio dp,
(VALUES
  ('AAPL', 'buy', 50, 150.00, 7500.00, '2024-01-15'::timestamp, 'Initial purchase'),
  ('GOOGL', 'buy', 20, 120.00, 2400.00, '2024-02-01'::timestamp, 'Adding to position'),
  ('MSFT', 'buy', 30, 300.00, 9000.00, '2024-01-20'::timestamp, 'Long term hold'),
  ('TSLA', 'buy', 15, 200.00, 3000.00, '2024-03-01'::timestamp, 'Speculative buy'),
  ('BTC', 'buy', 0.5, 40000.00, 20000.00, '2024-01-01'::timestamp, 'Crypto allocation'),
  ('ETH', 'buy', 5, 2000.00, 10000.00, '2024-02-15'::timestamp, 'Diversifying crypto')
) AS vals(symbol, transaction_type, quantity, price, total_amount, transaction_date, notes);

-- Insert demo goals
INSERT INTO public.goals (user_id, name, target_amount, current_amount, target_date, category, priority)
VALUES 
  ('YOUR_DEMO_USER_UUID', 'Emergency Fund', 10000.00, 7500.00, '2025-06-01', 'Safety', 1),
  ('YOUR_DEMO_USER_UUID', 'Vacation Fund', 5000.00, 2000.00, '2025-12-01', 'Lifestyle', 3),
  ('YOUR_DEMO_USER_UUID', 'Home Down Payment', 50000.00, 15000.00, '2026-12-31', 'Real Estate', 2),
  ('YOUR_DEMO_USER_UUID', 'Retirement', 1000000.00, 76800.00, '2055-01-01', 'Retirement', 1);
*/

-- Alternative: Create demo user programmatically (requires service role key)
-- This should be run from your backend or using Supabase service role key
/*
-- You'll need to use the Supabase JavaScript client with service role key:
const { data, error } = await supabase.auth.admin.createUser({
  email: 'demo@financeai.com',
  password: 'demo123',
  email_confirm: true,
  user_metadata: {
    full_name: 'Demo User'
  }
})
*/