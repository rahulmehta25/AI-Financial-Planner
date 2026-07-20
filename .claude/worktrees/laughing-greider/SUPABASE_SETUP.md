# Supabase Setup Guide for Financial Planner

## Step 1: Create Supabase Account & Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up with GitHub (recommended) or email
3. Create a new project:
   - **Project name**: `financial-planner`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to you
   - **Plan**: Free tier

## Step 2: Set Up Database Schema

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy and paste the entire contents of `supabase/schema.sql`
4. Click **Run** to create all tables and policies

## Step 3: Configure Authentication

1. Go to **Authentication** → **Providers**
2. Enable **Email** provider (already enabled by default)
3. Optional: Enable social providers (Google, GitHub, etc.)
4. Go to **Authentication** → **URL Configuration**
5. Add your frontend URL to **Redirect URLs**:
   - `http://localhost:3000/*`
   - `https://your-app.vercel.app/*`

## Step 4: Get Your API Keys

1. Go to **Settings** → **API**
2. Copy these values:
   ```
   Project URL: https://[YOUR-PROJECT-ID].supabase.co
   Anon/Public Key: eyJ....[long string]
   Service Role Key: eyJ....[keep this secret!]
   ```

## Step 5: Create Edge Functions for Market Data

Create a new Edge Function for fetching market data:

1. Install Supabase CLI:
   ```bash
   brew install supabase/tap/supabase
   ```

2. Initialize Supabase in your project:
   ```bash
   cd /Users/rahulmehta/Desktop/AI-ML\ Projects/AI-Financial-Planner
   supabase init
   ```

3. Create the market data function:
   ```bash
   supabase functions new get-market-data
   ```

4. This creates `supabase/functions/get-market-data/index.ts`

## Step 6: Update Frontend Environment Variables

Create `.env.local` in your frontend directory:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://[YOUR-PROJECT-ID].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...[your anon key]

# Optional: For server-side operations only
SUPABASE_SERVICE_ROLE_KEY=eyJ...[your service key - keep secret!]
```

## Step 7: Install Supabase Client in Frontend

```bash
cd frontend
npm install @supabase/supabase-js
```

## Step 8: Create Supabase Client

Create `frontend/src/lib/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  }
})

// Types for your database
export type Portfolio = {
  id: string
  user_id: string
  name: string
  description?: string
  currency: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export type Holding = {
  id: string
  portfolio_id: string
  symbol: string
  quantity: number
  cost_basis: number
  purchase_date: string
  asset_type: string
  notes?: string
  created_at: string
  updated_at: string
}
```

## Step 9: Test the Connection

Create a test component to verify everything works:

```typescript
// frontend/src/components/TestSupabase.tsx
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function TestSupabase() {
  const [user, setUser] = useState(null)
  
  useEffect(() => {
    // Check if user is logged in
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user)
    })
    
    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null)
      }
    )
    
    return () => subscription.unsubscribe()
  }, [])
  
  const signUp = async () => {
    const { data, error } = await supabase.auth.signUp({
      email: 'test@example.com',
      password: 'test123456',
    })
    console.log('Sign up:', data, error)
  }
  
  const signIn = async () => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: 'test@example.com',
      password: 'test123456',
    })
    console.log('Sign in:', data, error)
  }
  
  const signOut = async () => {
    await supabase.auth.signOut()
  }
  
  const fetchPortfolios = async () => {
    const { data, error } = await supabase
      .from('portfolios')
      .select('*, holdings(*)')
    console.log('Portfolios:', data, error)
  }
  
  return (
    <div>
      <h2>Supabase Test</h2>
      {user ? (
        <>
          <p>Logged in as: {user.email}</p>
          <button onClick={signOut}>Sign Out</button>
          <button onClick={fetchPortfolios}>Fetch Portfolios</button>
        </>
      ) : (
        <>
          <button onClick={signUp}>Sign Up</button>
          <button onClick={signIn}>Sign In</button>
        </>
      )}
    </div>
  )
}
```

## Step 10: Deploy Edge Function

```bash
# Link to your project
supabase link --project-ref [YOUR-PROJECT-ID]

# Deploy the function
supabase functions deploy get-market-data
```

## Migration Checklist

- [x] Create Supabase project
- [x] Set up database schema
- [ ] Configure authentication providers
- [ ] Get API keys
- [ ] Create Edge Functions for market data
- [ ] Update frontend environment variables
- [ ] Install Supabase client
- [ ] Create Supabase client helper
- [ ] Test authentication flow
- [ ] Test database operations
- [ ] Deploy Edge Functions
- [ ] Update all frontend API calls
- [ ] Remove old backend references

## Common Issues & Solutions

### CORS Errors
- Add your frontend URL to Supabase dashboard under Authentication → URL Configuration

### RLS (Row Level Security) Blocking Queries
- Make sure user is authenticated before querying
- Check RLS policies in SQL editor
- Use `service_role` key for admin operations (backend only)

### Edge Function Not Working
- Check function logs in Supabase dashboard
- Ensure function is deployed: `supabase functions deploy [name]`
- Verify CORS headers in function response

## Next Steps

1. Implement authentication flow in frontend
2. Create portfolio management components
3. Add market data fetching via Edge Functions
4. Implement real-time updates for portfolio values
5. Add data export functionality

## Resources

- [Supabase Docs](https://supabase.com/docs)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)