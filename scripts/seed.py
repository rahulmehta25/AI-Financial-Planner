"""Seed the AIFP database with the three demo personas.

Reads docs/personas.json and inserts users + accounts + goals + transactions
into the Cloud SQL `aifp` database. Idempotent: existing personas (by email) are
skipped on conflict.

Usage:
    # Make sure scripts/db-proxy.sh is running in another terminal,
    # and DATABASE_URL is set in api/.env.

    cd api
    python -m scripts.seed
"""
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add api/ to sys.path so we can import app.db when run from repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "api"))

from sqlalchemy import text  # noqa: E402

from app.db import get_session_factory  # noqa: E402

PERSONAS_PATH = REPO_ROOT / "docs" / "personas.json"


async def seed() -> None:
    if not PERSONAS_PATH.exists():
        raise SystemExit(f"personas.json not found at {PERSONAS_PATH}")

    personas = json.loads(PERSONAS_PATH.read_text())
    if not isinstance(personas, list):
        personas = personas.get("personas", [])

    session_factory = get_session_factory()
    async with session_factory() as session:
        inserted_users = 0
        inserted_accounts = 0
        inserted_goals = 0
        inserted_transactions = 0

        for p in personas:
            email = p.get("email") or f"{p['persona_key']}@aifp.demo"
            user_id = uuid.uuid4()

            # users: insert if not exists
            existing = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email},
            )
            row = existing.first()
            if row:
                user_id = row[0]
            else:
                await session.execute(
                    text(
                        "INSERT INTO users (id, email, display_name, persona_key, risk_tolerance) "
                        "VALUES (:id, :email, :display_name, :persona_key, :risk_tolerance)"
                    ),
                    {
                        "id": user_id,
                        "email": email,
                        "display_name": p.get("display_name", p["persona_key"]),
                        "persona_key": p["persona_key"],
                        "risk_tolerance": p.get("risk_tolerance", "moderate"),
                    },
                )
                inserted_users += 1

            for acct in p.get("accounts", []):
                acct_id = uuid.uuid4()
                await session.execute(
                    text(
                        "INSERT INTO accounts (id, user_id, name, account_type, account_subtype, "
                        "institution, currency_code, current_balance, available_balance, last_synced_at) "
                        "VALUES (:id, :user_id, :name, :account_type, :account_subtype, :institution, "
                        ":currency_code, :current_balance, :available_balance, :last_synced_at) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "id": acct_id,
                        "user_id": user_id,
                        "name": acct["name"],
                        "account_type": acct.get("account_type", "depository"),
                        "account_subtype": acct.get("account_subtype"),
                        "institution": acct.get("institution"),
                        "currency_code": acct.get("currency_code", "USD"),
                        "current_balance": Decimal(str(acct.get("current_balance", 0))),
                        "available_balance": Decimal(str(acct.get("available_balance", acct.get("current_balance", 0)))),
                        "last_synced_at": datetime.utcnow(),
                    },
                )
                inserted_accounts += 1

                for tx in acct.get("transactions", []):
                    await session.execute(
                        text(
                            "INSERT INTO transactions (account_id, amount, currency_code, description, "
                            "merchant_name, category, date, pending) "
                            "VALUES (:account_id, :amount, :currency_code, :description, :merchant_name, "
                            ":category, :date, :pending)"
                        ),
                        {
                            "account_id": acct_id,
                            "amount": Decimal(str(tx["amount"])),
                            "currency_code": tx.get("currency_code", "USD"),
                            "description": tx["description"],
                            "merchant_name": tx.get("merchant_name"),
                            "category": tx.get("category", []),
                            "date": tx.get("date") or date.today(),
                            "pending": tx.get("pending", False),
                        },
                    )
                    inserted_transactions += 1

            for goal in p.get("goals", []):
                await session.execute(
                    text(
                        "INSERT INTO goals (user_id, name, goal_type, target_amount, target_date, "
                        "current_amount, priority) "
                        "VALUES (:user_id, :name, :goal_type, :target_amount, :target_date, "
                        ":current_amount, :priority)"
                    ),
                    {
                        "user_id": user_id,
                        "name": goal["name"],
                        "goal_type": goal.get("goal_type", "custom"),
                        "target_amount": Decimal(str(goal["target_amount"])),
                        "target_date": goal.get("target_date"),
                        "current_amount": Decimal(str(goal.get("current_amount", 0))),
                        "priority": goal.get("priority", 3),
                    },
                )
                inserted_goals += 1

        await session.commit()

    print(
        f"Seed complete. Inserted: {inserted_users} users, {inserted_accounts} accounts, "
        f"{inserted_goals} goals, {inserted_transactions} transactions."
    )


if __name__ == "__main__":
    asyncio.run(seed())
