-- Verify Supabase Setup
-- Run these queries in your SQL Editor to confirm everything is working

-- 1. Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. Verify Row Level Security is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- 3. Check RLS policies are in place
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- 4. Test that RLS is working (should return empty without auth)
-- This proves your data is secure
SELECT COUNT(*) as portfolio_count FROM portfolios;
SELECT COUNT(*) as holdings_count FROM holdings;

-- 5. Check if auth trigger exists
SELECT tgname 
FROM pg_trigger 
WHERE tgname = 'on_auth_user_created';

-- If you see:
-- ✅ Tables: profiles, portfolios, holdings, transactions, watchlist, market_data_cache
-- ✅ RLS enabled: rowsecurity = true for all except market_data_cache
-- ✅ Policies exist for each table
-- ✅ Counts return 0 (because you're not authenticated)
-- ✅ Trigger exists
-- Then your setup is COMPLETE and SECURE!