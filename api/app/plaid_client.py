"""Plaid sandbox wrapper with deterministic mock fallback.

When credentials are unset, every endpoint returns mock data shaped like the Plaid API so
the frontend can still demo the link flow end to end.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from .config import get_settings


def _mock_link_token() -> dict[str, Any]:
    return {
        "link_token": f"link-sandbox-mock-{uuid.uuid4()}",
        "expiration": "2099-12-31T23:59:59Z",
        "request_id": f"mock-{int(time.time())}",
        "mock": True,
    }


def _mock_exchange(public_token: str) -> dict[str, Any]:
    return {
        "access_token": f"access-sandbox-mock-{uuid.uuid4()}",
        "item_id": f"item-mock-{public_token[-6:] if public_token else 'none'}",
        "mock": True,
    }


def _mock_accounts() -> dict[str, Any]:
    return {
        "accounts": [
            {"account_id": "mock_chk", "name": "Plaid Checking", "type": "depository", "subtype": "checking", "balances": {"current": 1100.0}},
            {"account_id": "mock_sav", "name": "Plaid Saving", "type": "depository", "subtype": "savings", "balances": {"current": 8500.0}},
            {"account_id": "mock_401k", "name": "Plaid 401k", "type": "investment", "subtype": "401k", "balances": {"current": 32400.0}},
        ],
        "mock": True,
    }


def _mock_transactions() -> dict[str, Any]:
    return {
        "transactions": [
            {"transaction_id": "m_1", "account_id": "mock_chk", "date": "2026-04-15", "amount": -52.47, "name": "Starbucks", "category": ["Food and Drink"]},
            {"transaction_id": "m_2", "account_id": "mock_chk", "date": "2026-04-10", "amount": -1850.00, "name": "Rent", "category": ["Shelter"]},
            {"transaction_id": "m_3", "account_id": "mock_chk", "date": "2026-04-01", "amount": 4800.00, "name": "Payroll", "category": ["Payroll"]},
        ],
        "mock": True,
    }


def _real_client():
    from plaid.api import plaid_api
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient

    settings = get_settings()
    env_host = {
        "sandbox": "https://sandbox.plaid.com",
        "development": "https://development.plaid.com",
        "production": "https://production.plaid.com",
    }[settings.plaid_env]

    config = Configuration(
        host=env_host,
        api_key={
            "clientId": settings.plaid_client_id,
            "secret": settings.plaid_secret_sandbox,
        },
    )
    return plaid_api.PlaidApi(ApiClient(config))


def create_link_token(user_id: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.plaid_configured:
        return _mock_link_token()

    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.country_code import CountryCode
    from plaid.model.products import Products

    client = _real_client()
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=user_id),
        client_name="AI Financial Planner",
        products=[Products(p.strip()) for p in settings.plaid_products.split(",") if p.strip()],
        country_codes=[CountryCode(c.strip()) for c in settings.plaid_country_codes.split(",") if c.strip()],
        language="en",
    )
    response = client.link_token_create(request)
    return response.to_dict()


def exchange_public_token(public_token: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.plaid_configured:
        return _mock_exchange(public_token)

    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

    client = _real_client()
    response = client.item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=public_token)
    )
    return response.to_dict()


def get_accounts(access_token: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.plaid_configured:
        return _mock_accounts()

    from plaid.model.accounts_get_request import AccountsGetRequest

    client = _real_client()
    response = client.accounts_get(AccountsGetRequest(access_token=access_token))
    return response.to_dict()


def get_transactions(access_token: str, start_date: str, end_date: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.plaid_configured:
        return _mock_transactions()

    from plaid.model.transactions_get_request import TransactionsGetRequest
    from datetime import date

    client = _real_client()
    response = client.transactions_get(
        TransactionsGetRequest(
            access_token=access_token,
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date),
        )
    )
    return response.to_dict()
