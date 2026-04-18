# AI Financial Planner

An AI advisor that actually looks at your accounts. Links via Plaid sandbox, runs Monte Carlo retirement simulations, and answers questions about your money with Claude grounded on your real data.

## What it does

- Links accounts via Plaid (sandbox only, not production)
- Runs Monte Carlo simulations for retirement planning with p10/p50/p90 outcomes
- Claude 3.7 Sonnet answers questions like "what happens if I lose my job for six months", grounded on your accounts, transactions, and goals. Tool-calls into the simulator when needed
- 3 preset personas so you can demo without Plaid credentials

## Tech

- Next.js 14 App Router, TypeScript, Tailwind
- Python 3.11 FastAPI backend, NumPy Monte Carlo
- Plaid sandbox SDK
- Claude 3.7 Sonnet via the Anthropic SDK with tool use
- Deployed on Vercel (frontend) + Cloud Run (backend)

## Personas

- Young saver (25, $12k savings, high income, no debt)
- Mid-career (38, $180k 401k, mortgage, two kids)
- Pre-retiree (58, $1.2M savings, deciding when to retire)

## Run it locally

```bash
git clone https://github.com/rmehta2500/ai-financial-planner
cd ai-financial-planner
cp .env.example .env
# fill in PLAID_CLIENT_ID, PLAID_SECRET_SANDBOX, ANTHROPIC_API_KEY (all optional for persona demos)
make install
make dev
```

See [SETUP.md](./SETUP.md) for full details, including how to run in placeholder mode without Plaid or Anthropic credentials.

## Demo

Walk-through video: `docs/demos/aifp-demo.mp4` (coming soon).

## Disclaimer

Portfolio project. Not a registered investment advisor. Nothing here is a recommendation. Plaid integration is sandbox-only; no real financial data ever touches the app.

MIT licensed.
