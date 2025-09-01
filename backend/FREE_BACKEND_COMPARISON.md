# Free Backend Services Comparison for Financial Planner

## Top Free Options Ranked

### 1. **Supabase** 🥇 BEST OVERALL
- **Database**: 500MB PostgreSQL
- **Auth**: Unlimited users with social logins
- **Storage**: 1GB
- **Edge Functions**: 500K invocations/month
- **Realtime**: Included
- **Pros**: Most generous free tier, built-in auth, RLS
- **Cons**: 2 week pause if inactive (auto-resumes)
- **Perfect for**: Your financial planner

### 2. **PocketBase** 🥈 EXCELLENT ALTERNATIVE
- **Database**: SQLite (unlimited size)
- **Auth**: Built-in with OAuth
- **Storage**: Unlimited
- **Hosting**: Need free VPS (Oracle Cloud Forever Free)
- **Pros**: Single binary, real-time, super fast, own your data
- **Cons**: Need to self-host (but Oracle Cloud is free forever)
- **Perfect for**: Complete control + privacy

### 3. **Appwrite** 🥉 GOOD OPTION
- **Database**: Unlimited documents
- **Auth**: Unlimited users
- **Storage**: 10GB
- **Functions**: 1M executions/month
- **Pros**: Very generous limits, self-hosted option
- **Cons**: Cloud version in beta, complex setup
- **Perfect for**: Large projects

### 4. **Firebase** (Google)
- **Database**: 1GB Firestore
- **Auth**: Unlimited (phone auth limited)
- **Storage**: 5GB
- **Functions**: 125K invocations/month
- **Pros**: Mature, reliable, great SDKs
- **Cons**: Vendor lock-in, NoSQL only, functions limits low
- **Perfect for**: Simple apps

### 5. **Neon** (PostgreSQL only)
- **Database**: 3GB PostgreSQL across all branches
- **Auth**: Not included (need separate service)
- **Pros**: Serverless Postgres, branching, modern
- **Cons**: Database only, need separate auth/backend
- **Perfect for**: Database-heavy apps

### 6. **Render.com** 
- **Backend**: Free Python/Node hosting
- **Database**: 90-day PostgreSQL (then deleted!)
- **Pros**: Easy deployment, good for backends
- **Cons**: Database expires, slow cold starts
- **Perfect for**: Backend APIs only

## 🎯 Recommendation for Your Financial Planner

### BEST: **Supabase**
Your app needs auth + database + market data. Supabase gives you everything in one place with the best free tier.

### ALTERNATIVE: **PocketBase on Oracle Cloud**
If you want complete control and no limits:
1. Get Oracle Cloud Forever Free tier (2 VMs with 1GB RAM each)
2. Deploy PocketBase (single 15MB binary)
3. Unlimited everything, you own the data

## Quick Setup Comparison

### Supabase (5 minutes)
```bash
1. Sign up at supabase.com
2. Create project
3. Copy keys to frontend
4. Done!
```

### PocketBase on Oracle (30 minutes)
```bash
1. Sign up Oracle Cloud (free)
2. Create VM instance
3. SSH and download PocketBase
4. Run: ./pocketbase serve
5. Configure domain
```

## Special Mention: **Convex**
- Innovative real-time database
- Generous free tier
- BUT: Proprietary, newer, less proven

## Why Not These?

- **Planetscale**: Removed free tier
- **Heroku**: Removed free tier  
- **Railway**: No free tier ($5/month minimum)
- **Fly.io**: Requires credit card, charges after limits
- **Vercel Postgres**: Only 30-day free trial
- **CockroachDB**: Only 30-day free trial

## Decision Matrix

| Service | Database | Auth | Storage | Functions | Limits | Setup Time |
|---------|----------|------|---------|-----------|--------|------------|
| Supabase | 500MB | ✅ | 1GB | 500K/mo | Pausable | 5 min |
| PocketBase | Unlimited | ✅ | Unlimited | Unlimited | None | 30 min |
| Appwrite | Unlimited | ✅ | 10GB | 1M/mo | Beta | 20 min |
| Firebase | 1GB | ✅ | 5GB | 125K/mo | NoSQL | 10 min |

## Final Verdict

**Go with Supabase** unless you:
- Want complete control → PocketBase on Oracle
- Already use Google services → Firebase
- Need more than 500MB data → PocketBase

For your financial planner tracking portfolios and showing market data, Supabase is perfect and will scale with you.