# AI Financial Planner

A personal finance and investment advisory web application built with React, TypeScript, Supabase, and Claude AI.

## What It Does

- **Portfolio Tracking** — Add and track holdings across accounts with market-value calculations via Supabase
- **AI Financial Advisor** — Real-time chat with Claude AI for personalized financial guidance
- **Monte Carlo Simulation** — Browser-native retirement projections with jump-diffusion and regime-switching models (no backend required)
- **Portfolio Optimizer** — Mean-variance optimization with efficient frontier visualization
- **Tax Optimization** — Tax-loss harvesting identification and Roth conversion analysis
- **Goals Tracking** — Set and monitor progress toward financial goals
- **Analytics** — Portfolio performance, allocation, and risk metrics

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| UI | Radix UI + Tailwind CSS |
| State | TanStack Query v5 |
| Auth + DB | Supabase (PostgreSQL) |
| AI Chat | Claude AI via Vercel serverless function |
| Charts | Recharts + Plotly (lazy-loaded) |
| Deployment | Vercel |

## Getting Started

### Prerequisites

- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)
- An [Anthropic API key](https://console.anthropic.com) for the AI advisor

### Local Development

```bash
# Install frontend dependencies
cd frontend
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your Supabase credentials
# VITE_SUPABASE_URL=https://your-project.supabase.co
# VITE_SUPABASE_ANON_KEY=your-anon-key

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

The AI advisor calls `/api/chat` which is a Vercel serverless function. In local development,
install the [Vercel CLI](https://vercel.com/docs/cli) and run `vercel dev` instead of `npm run dev`
to get the full serverless function support. Add `ANTHROPIC_API_KEY` to your Vercel project
environment variables (or a local `.env` file at the repo root for `vercel dev`).

### Database Setup

Run the SQL schema in your Supabase SQL editor:

```bash
# The schema is in supabase_schema.sql at the repo root
```

### Deployment to Vercel

1. Import the repository in the [Vercel dashboard](https://vercel.com/new)
2. Set the following environment variables in the Vercel project settings:
   - `ANTHROPIC_API_KEY` — your Anthropic API key (server-side only, never exposed to the browser)
   - `VITE_SUPABASE_URL` — your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` — your Supabase anon key
3. Deploy. The build command and output directory are pre-configured in `vercel.json`.

## Project Structure

```
.
├── api/                  # Vercel serverless functions
│   └── chat.ts           # AI advisor endpoint (calls Claude API)
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── contexts/     # React contexts (Auth, Demo)
│   │   ├── hooks/        # Custom hooks
│   │   ├── lib/          # Supabase client + helpers
│   │   ├── pages/        # Route-level page components
│   │   └── services/     # API/data service layer
│   ├── vite.config.ts
│   └── package.json
├── supabase_schema.sql   # Database schema
├── vercel.json           # Vercel deployment config
└── README.md
```

## Architecture Notes

- **Auth**: Managed by Supabase Auth (JWT, email/password, session refresh)
- **Data**: Stored in Supabase PostgreSQL. Portfolio holdings and transactions are user-scoped via RLS policies.
- **AI Chat**: The browser calls `/api/chat` (a Vercel serverless function). The function forwards the request to the Anthropic API using a server-side key. The API key is never exposed to the browser.
- **Monte Carlo**: Runs entirely in the browser using geometric Brownian motion with optional jump-diffusion (Merton model). No backend required.
- **Market Prices**: Fetched from the `market_data` Supabase table. You can populate this table with a scheduled job calling any market data provider.

## Environment Variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `ANTHROPIC_API_KEY` | Server (Vercel env) | Claude AI API key for the chat endpoint |
| `VITE_SUPABASE_URL` | Build + Browser | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Build + Browser | Supabase public anon key (safe to expose) |

## Known Limitations

- Market data is not auto-refreshed. Holdings show current price only if the `market_data` table has been populated.
- The mobile app (React Native) in `/mobile` is a scaffold and not connected to the backend.
- Broker integrations (Plaid, etc.) are not implemented.
- PDF export generates a report with whatever data is loaded in the browser session.

## License

MIT
