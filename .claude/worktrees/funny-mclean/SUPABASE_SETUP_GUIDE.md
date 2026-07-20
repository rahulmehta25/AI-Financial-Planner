# Supabase Backend Setup Guide

## Why Supabase Instead of Separate Backend?

You're absolutely right! Since we're already using Supabase for authentication, we can use it as our complete backend solution. This eliminates the need for:
- Separate backend hosting (Railway/Render)
- Additional server costs
- Complex deployment configurations
- CORS issues between frontend and backend

## What Supabase Provides

1. **Database**: PostgreSQL with real-time subscriptions
2. **Authentication**: Already configured and working
3. **Storage**: For file uploads (documents, avatars)
4. **Edge Functions**: Serverless functions for AI features
5. **Row Level Security**: Automatic data protection
6. **Real-time**: WebSocket subscriptions for live updates

## Setup Instructions

### 1. Database Tables Setup

1. Go to your Supabase project dashboard: https://app.supabase.com
2. Navigate to the **SQL Editor** section
3. Copy and run the SQL from `supabase_schema.sql` file
4. This creates all necessary tables:
   - `profiles` - User profiles
   - `portfolios` - User portfolios
   - `holdings` - Stock/asset holdings
   - `transactions` - Buy/sell transactions
   - `goals` - Financial goals
   - `market_data` - Cached market data

### 2. Edge Functions for AI Features

Create an Edge Function for AI chat (if you want AI features):

```bash
# Install Supabase CLI if not already installed
brew install supabase/tap/supabase

# Login to Supabase
supabase login

# Create a new Edge Function
supabase functions new ai-chat
```

Example Edge Function for AI chat (`supabase/functions/ai-chat/index.ts`):

```typescript
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { message, userId } = await req.json()

    // Here you would integrate with OpenAI, Claude, or another AI service
    // For now, return a simple response
    const aiResponse = {
      message: `I understand you're asking about: "${message}". As your AI financial advisor, I can help with portfolio optimization, investment strategies, and financial planning.`,
      suggestions: [
        'Review your current portfolio allocation',
        'Analyze risk tolerance',
        'Set financial goals',
        'Explore tax-efficient strategies'
      ]
    }

    return new Response(
      JSON.stringify(aiResponse),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400
      }
    )
  }
})
```

Deploy the function:
```bash
supabase functions deploy ai-chat
```

### 3. Market Data Integration

For real-time market data, you have options:

#### Option A: Use Free APIs with Edge Functions
Create an Edge Function that fetches from free APIs:

```typescript
// supabase/functions/market-data/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

serve(async (req) => {
  const { symbols } = await req.json()
  
  // Use free APIs like Alpha Vantage, Yahoo Finance, or IEX Cloud
  // Example with a mock response:
  const marketData = symbols.map(symbol => ({
    symbol,
    price: Math.random() * 1000,
    change: (Math.random() - 0.5) * 10,
    changePercent: (Math.random() - 0.5) * 5,
    volume: Math.floor(Math.random() * 1000000)
  }))
  
  return new Response(JSON.stringify(marketData), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

#### Option B: Use Cached Data
Store and update market data periodically in the `market_data` table using a scheduled function.

### 4. Frontend Configuration

The frontend is already configured to use Supabase! The services are in:
- `/frontend/src/lib/supabase.ts` - Main Supabase client and helpers
- `/frontend/src/services/portfolio.ts` - Portfolio management using Supabase

### 5. Environment Variables

Your frontend already has the correct Supabase configuration:
```env
VITE_SUPABASE_URL=https://tqxhvrsdroafvigbgaxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

## Testing the Setup

1. **Test Authentication**:
   - Sign up/Login should already work
   - Check the Auth section in Supabase dashboard

2. **Test Portfolio Creation**:
   ```javascript
   // In browser console on your app
   const { data, error } = await portfolios.create({
     name: 'My Investment Portfolio',
     description: 'Long-term investments',
     currency: 'USD'
   })
   ```

3. **Test Adding Holdings**:
   ```javascript
   const { data, error } = await holdings.create({
     portfolio_id: 'your-portfolio-id',
     symbol: 'AAPL',
     quantity: 10,
     cost_basis: 150.00,
     purchase_date: '2024-01-01'
   })
   ```

## Advantages of This Approach

1. **Cost**: Supabase free tier is generous (500MB database, 2GB bandwidth, 50K MAUs)
2. **Simplicity**: One service to manage instead of multiple
3. **Performance**: Direct database access, no API middleman
4. **Real-time**: Built-in WebSocket support for live updates
5. **Security**: Row Level Security ensures users only see their own data
6. **Scalability**: Supabase scales automatically

## Current Status

✅ **Working:**
- Frontend deployed on Vercel
- Supabase authentication configured
- Database schema created
- Frontend services ready to use Supabase

📝 **To Complete:**
1. Run the SQL schema in your Supabase project
2. Test portfolio operations
3. Add Edge Functions for AI features (optional)
4. Configure market data source (free API or mock data)

## Next Steps

1. **Run the SQL Schema**: 
   - Go to Supabase SQL Editor
   - Paste and run the contents of `supabase_schema.sql`

2. **Test Portfolio Features**:
   - Create a portfolio
   - Add holdings
   - View dashboard

3. **Optional AI Integration**:
   - Set up Edge Functions
   - Integrate with OpenAI/Claude API
   - Add your API keys to Supabase secrets

That's it! Your financial planner now has a complete backend powered by Supabase, eliminating the need for a separate backend service.