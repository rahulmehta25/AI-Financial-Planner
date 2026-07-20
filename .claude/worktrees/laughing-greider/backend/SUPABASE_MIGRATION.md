# Migrating to Supabase Architecture

## Why Supabase is Better for This Project

Your financial planner primarily needs:
- User authentication ✅ (Supabase Auth)
- Database for portfolios ✅ (Supabase PostgreSQL)  
- Real-time market data ✅ (yfinance from Edge Functions)
- Secure user data isolation ✅ (Row Level Security)

## New Architecture

```
Frontend (Vercel)
    ↓
Supabase (Backend)
├── Auth (Built-in JWT)
├── PostgreSQL Database
├── Edge Functions (for yfinance)
└── Row Level Security
```

## Option 1: Full Supabase (Recommended)

Use Supabase for everything:
- **Database**: PostgreSQL with your existing schema
- **Auth**: Replace custom JWT with Supabase Auth
- **API**: Use Supabase auto-generated APIs
- **Market Data**: Edge Functions calling yfinance

### Implementation Steps:

1. **Create Supabase Project**
   ```bash
   # Go to https://supabase.com
   # Create new project (free)
   # Get your project URL and anon key
   ```

2. **Create Database Tables**
   ```sql
   -- Users table (managed by Supabase Auth)
   
   -- Portfolios table
   CREATE TABLE portfolios (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     user_id UUID REFERENCES auth.users(id),
     name VARCHAR(100) NOT NULL,
     description TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Portfolio holdings
   CREATE TABLE holdings (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
     symbol VARCHAR(10) NOT NULL,
     quantity DECIMAL(15,4) NOT NULL,
     cost_basis DECIMAL(15,2) NOT NULL,
     purchase_date DATE NOT NULL,
     created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Enable Row Level Security
   ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
   ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;
   
   -- Policies: Users can only see their own data
   CREATE POLICY "Users can view own portfolios" ON portfolios
     FOR ALL USING (auth.uid() = user_id);
     
   CREATE POLICY "Users can view own holdings" ON holdings
     FOR ALL USING (
       portfolio_id IN (
         SELECT id FROM portfolios WHERE user_id = auth.uid()
       )
     );
   ```

3. **Create Edge Functions for Market Data**
   ```typescript
   // supabase/functions/get-quote/index.ts
   import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
   
   serve(async (req) => {
     const { symbol } = await req.json()
     
     // Fetch from yfinance API or Yahoo Finance
     const response = await fetch(
       `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${symbol}`
     )
     const data = await response.json()
     
     return new Response(JSON.stringify(data), {
       headers: { "Content-Type": "application/json" },
     })
   })
   ```

4. **Update Frontend to Use Supabase**
   ```typescript
   // Install Supabase client
   npm install @supabase/supabase-js
   
   // Initialize client
   import { createClient } from '@supabase/supabase-js'
   
   const supabase = createClient(
     process.env.NEXT_PUBLIC_SUPABASE_URL,
     process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
   )
   
   // Authentication
   const { user, error } = await supabase.auth.signUp({
     email: 'user@example.com',
     password: 'password'
   })
   
   // Get portfolios (automatically filtered by user)
   const { data: portfolios } = await supabase
     .from('portfolios')
     .select('*, holdings(*)')
   
   // Call Edge Function for market data
   const { data } = await supabase.functions.invoke('get-quote', {
     body: { symbol: 'AAPL' }
   })
   ```

## Option 2: Hybrid Approach

Keep Python backend for complex analytics, use Supabase for database/auth:

1. **Supabase**: Database + Auth
2. **Python API** (on Render.com free tier): Complex calculations only
3. **Frontend**: Talks to both

```python
# Python backend connects to Supabase PostgreSQL
DATABASE_URL = "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"

# Verify JWT tokens from Supabase
from jose import jwt
SUPABASE_JWT_SECRET = "your-jwt-secret-from-supabase"
```

## Migration Checklist

- [ ] Create Supabase account and project
- [ ] Set up database schema with RLS
- [ ] Implement Edge Functions for market data  
- [ ] Update frontend to use Supabase SDK
- [ ] Migrate user authentication
- [ ] Test portfolio CRUD operations
- [ ] Deploy and update environment variables

## Cost Comparison

### Supabase (Free Tier)
- Database: 500MB PostgreSQL ✅
- Auth: Unlimited users ✅
- Edge Functions: 500K invocations/month ✅
- Storage: 1GB ✅
- **Total: $0/month**

### Railway
- Hosting: $5/month minimum
- PostgreSQL: $5/month minimum  
- Redis: $5/month (optional)
- **Total: $10-15/month**

## Decision

For a financial planning app with user auth and portfolio tracking, Supabase provides everything needed at $0/month with better security (RLS) and simpler implementation.