# Setting Up Demo User in Supabase

## Quick Setup Guide

The 400 error you're seeing (`POST https://tqxhvrsdroafvigbgaxx.supabase.co/auth/v1/token?grant_type=password 400`) indicates that the demo user doesn't exist in your Supabase project yet.

## Option 1: Manual Setup (Recommended - Easiest)

1. **Go to your Supabase Dashboard**
   - Visit: https://app.supabase.com
   - Select your project: `AI-Financial-Planner`

2. **Create the Demo User**
   - Navigate to: `Authentication` → `Users`
   - Click `Add user` → `Create new user`
   - Enter:
     - Email: `demo@financeai.com`
     - Password: `demo123`
     - Auto Confirm Email: ✅ (check this)
   - Click `Create user`

3. **Test the Login**
   - Go to: https://frontend-nine-azure-92.vercel.app
   - Click "Sign In"
   - Use credentials:
     - Email: `demo@financeai.com`
     - Password: `demo123`

## Option 2: Using SQL Editor

1. **First create the user manually** (as described in Option 1)

2. **Get the User ID**
   - In Supabase Dashboard, go to `Authentication` → `Users`
   - Find `demo@financeai.com`
   - Copy the User UID (looks like: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)

3. **Run Demo Data Setup**
   - Go to `SQL Editor` in Supabase Dashboard
   - Open `setup_demo_user.sql`
   - Replace `YOUR_DEMO_USER_UUID` with the actual UUID
   - Uncomment and run the SQL commands

## Option 3: Programmatic Setup (Advanced)

1. **Get Service Role Key**
   - Go to: `Settings` → `API`
   - Copy the `service_role` key (starts with `eyJ...`)
   - ⚠️ **Keep this secret!** Never commit it to git

2. **Add to .env file**
   ```bash
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```

3. **Install dependencies and run script**
   ```bash
   cd /Users/rahulmehta/Desktop/AI-ML\ Projects/AI-Financial-Planner
   npm install @supabase/supabase-js dotenv
   node scripts/create-demo-user.js
   ```

## Troubleshooting

### If you still get 400 errors after creating the user:

1. **Check Email Confirmation**
   - Make sure "Auto Confirm Email" was checked when creating the user
   - Or manually confirm the email in the Users table

2. **Check Password Requirements**
   - Supabase requires passwords to be at least 6 characters
   - `demo123` meets this requirement

3. **Check RLS Policies**
   - Run the `supabase_schema.sql` file in SQL Editor if you haven't already
   - This sets up the necessary Row Level Security policies

4. **Clear Browser Cache**
   - Sometimes old auth tokens can cause issues
   - Clear site data for the Vercel app URL

### Verifying Success

Once the demo user is created, you should be able to:
1. Sign in at https://frontend-nine-azure-92.vercel.app/login
2. View the Dashboard with portfolio data
3. Access Portfolio management features
4. Use the AI Chat functionality

## Current Status

- ✅ Frontend deployed and accessible
- ✅ Authentication code fixed (no more "f is not a function" errors)
- ⚠️ Demo user needs to be created in Supabase
- ✅ Database schema is set up
- ✅ RLS policies are configured

## Next Steps

1. Create the demo user using Option 1 (easiest)
2. Test login functionality
3. Verify dashboard loads with data
4. Test portfolio and AI chat features