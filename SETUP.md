# Setup

## Credential gaps as of scaffold

The repo was scaffolded without the following environment variables available:

| Variable | Status | Impact |
| --- | --- | --- |
| `PLAID_CLIENT_ID` | unset | Plaid link flow runs in mock mode; only persona data is available. |
| `PLAID_SECRET_SANDBOX` | unset | Same as above. |
| `ANTHROPIC_API_KEY` | unset | The advisor chat returns a stub response explaining the missing key. |

Copy `.env.example` to `.env` and fill in credentials. Even sandbox-only Plaid keys plus an Anthropic key are enough to unlock the full demo.

```bash
cp .env.example .env
# edit .env with your values
```

## Architecture decisions

- **Persona-first storage**: personas live in `api/app/personas.py` as plain Python objects. The portfolio demo does not need Supabase or pgvector to tell its story, so a full Supabase local stack is intentionally out of scope for the initial scaffold. The README draft in DELTA.md lists Supabase; adopt it later if document retrieval is added.
- **Plaid is optional**: if credentials are missing, the `/plaid/*` endpoints fall back to a deterministic mock that mirrors the sandbox shape. The frontend picks the persona and uses persona accounts directly.
- **Anthropic is optional**: without a key the chat endpoint returns a message explaining the gap and still demonstrates the tool-call protocol with a canned response.

## One-time setup

```bash
# Python backend
cd api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../web
pnpm install
```

Or from the repo root:

```bash
make install
```

## Running

```bash
make dev  # runs API on :8000 and web on :3000
```

## Testing Plaid without real credentials

Pick a persona in the UI. The app bypasses Plaid entirely and uses the persona's accounts. Useful for local dev, CI, and the portfolio demo recording.

## Testing with real sandbox credentials

1. Create a Plaid developer account.
2. Copy the sandbox Client ID and sandbox Secret into `.env`.
3. Restart the API server.
4. Click "Link an account" in the UI. Plaid's sandbox test user is `user_good` / `pass_good`.

## Deployment

Frontend: Vercel. Backend: Cloud Run (Dockerfile under `api/`). Both are stubs for now.
