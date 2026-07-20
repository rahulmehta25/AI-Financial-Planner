# Testing Guide - Live Supabase Integration

## 🚀 Your App is Now Live!

Vercel should auto-deploy from the GitHub push. The deployment includes:
- Real Supabase authentication
- Real market data from Yahoo Finance
- Real portfolio tracking

## Testing Steps

### 1. Local Testing (Recommended First)
Visit: http://localhost:5173

1. **Test Page**: Go to `/supabase-test`
   - Click "Test Market Data API" - Should show AAPL, MSFT, GOOGL prices
   - Sign up with a test email
   - Sign in to test auth

2. **Portfolio Page**: Go to `/portfolio`
   - Should show empty portfolio for new users
   - Click "Add Holding" button
   - Enter a symbol (e.g., AAPL)
   - Click search icon to verify
   - Add shares and cost basis
   - Submit to see real portfolio value

3. **Login/Register**: Go to `/login` or `/register`
   - Create a new account with Supabase
   - Email confirmation may be required (check spam)

### 2. Production Testing (After Vercel Deploys)
Visit: Your Vercel URL

Same steps as above, but on production.

## What's Working Now

✅ **Authentication**
- Sign up creates user in Supabase
- Sign in uses Supabase Auth
- Passwords are securely hashed
- Sessions persist

✅ **Portfolio Management**
- Add real stock holdings
- Symbol verification via Yahoo Finance
- Real-time price updates
- Portfolio value calculation
- Individual holding performance

✅ **Market Data**
- Live prices (15-min delayed)
- Daily change percentages
- 52-week highs/lows
- Market cap, volume, etc.

## Common Test Scenarios

### Add Your First Holding
1. Sign up/Login
2. Go to Portfolio
3. Click "Add Holding"
4. Try these symbols:
   - AAPL (Apple)
   - MSFT (Microsoft)
   - TSLA (Tesla)
   - SPY (S&P 500 ETF)

### View Portfolio Performance
1. Add 2-3 holdings
2. Refresh to see latest prices
3. Check total portfolio value
4. View individual gains/losses

## Troubleshooting

### "Symbol not found"
- Make sure you're using valid ticker symbols
- Try major stocks like AAPL, GOOGL, AMZN

### Portfolio shows $0
- You need to add holdings first
- Click "Add Holding" button

### Can't login
- Check if you confirmed your email (Supabase sends confirmation)
- Try signing up with a different email

### Market data not loading
- Check browser console for errors
- Edge Function might need a moment to warm up
- Try refreshing the page

## What's NOT Working Yet

- Historical charts (TODO)
- Tax optimization features (TODO)
- AI Advisor (needs API key)
- CSV import (backend needed)

## Database Check

To verify your data in Supabase:
1. Go to Supabase Dashboard
2. Table Editor → portfolios
3. You should see your portfolio
4. Table Editor → holdings
5. You should see your stocks

## Success Metrics

If these work, your integration is successful:
- [ ] Can create account
- [ ] Can login
- [ ] Can add stock holding
- [ ] Can see real market price
- [ ] Portfolio value updates

Your financial planner is now using 100% real data!