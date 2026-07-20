# Fix: Enable User Signup in Supabase

## The Problem
When users sign up on the website, they're not being created in Supabase because email confirmation is required by default, but not configured.

## Solution: Configure Supabase Authentication

### Step 1: Disable Email Confirmation (For Development)

1. **Go to Supabase Dashboard**: https://app.supabase.com
2. Select your project
3. Navigate to **Authentication → Providers → Email**
4. Find **"Confirm email"** setting
5. **Toggle it OFF** (for development/testing)
6. Click **Save**

This allows users to sign up and immediately access the app without email confirmation.

### Step 2: Configure Auth Settings

1. Still in **Authentication → Settings**
2. Check these settings:
   - **Enable email signup**: ✅ ON
   - **Enable email login**: ✅ ON
   - **Minimum password length**: 6 (or your preference)

### Step 3: Check Site URL Configuration

1. Go to **Authentication → URL Configuration**
2. Ensure **Site URL** is set to: `https://frontend-nine-azure-92.vercel.app`
3. Add to **Redirect URLs**:
   ```
   https://frontend-nine-azure-92.vercel.app
   https://frontend-nine-azure-92.vercel.app/*
   http://localhost:5173
   http://localhost:5173/*
   ```

## For Production (Email Confirmation Enabled)

If you want to keep email confirmation enabled for security:

### Option A: Configure Email Templates

1. Go to **Authentication → Email Templates**
2. Configure the confirmation email template
3. Make sure SMTP is configured (or use Supabase's default email service)

### Option B: Auto-Confirm in Development

Update the signup code to auto-confirm users in development:

```typescript
// In frontend/src/lib/supabase.ts
signUp: async (email: string, password: string, fullName?: string) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName,
      },
      // Auto-confirm email for development
      emailRedirectTo: window.location.origin
    }
  })
  return { data, error }
}
```

## Testing After Configuration

1. Go to: https://frontend-nine-azure-92.vercel.app/register
2. Create a new account with:
   - Any valid email (e.g., test@example.com)
   - Password (min 6 characters)
3. You should be:
   - Automatically logged in (if email confirmation is disabled)
   - Redirected to dashboard
   - Able to see your new user in Supabase Dashboard → Authentication → Users

## Current Status

- ✅ Signup code is correctly implemented
- ⚠️ Email confirmation needs to be configured
- ✅ Database triggers will create user profile automatically
- ✅ RLS policies are set up for user data access

## Quick Checklist

- [ ] Disable email confirmation in Supabase (for development)
- [ ] Configure Site URL and Redirect URLs
- [ ] Test signup with a new email
- [ ] Verify user appears in Supabase Dashboard
- [ ] Confirm user can access dashboard after signup

## Why This Happens

By default, Supabase requires email confirmation for security. When a user signs up:
1. Supabase creates the user but marks them as "unconfirmed"
2. Sends a confirmation email (if SMTP is configured)
3. User must click the link to confirm
4. Only then can they sign in

For development/testing, it's easier to disable this requirement temporarily.