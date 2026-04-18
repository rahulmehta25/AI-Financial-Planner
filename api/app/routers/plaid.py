from fastapi import APIRouter
from pydantic import BaseModel

from .. import plaid_client

router = APIRouter(prefix="/plaid", tags=["plaid"])


class LinkTokenRequest(BaseModel):
    user_id: str = "demo-user"


class ExchangeRequest(BaseModel):
    public_token: str


class AccountsRequest(BaseModel):
    access_token: str


class TransactionsRequest(BaseModel):
    access_token: str
    start_date: str = "2026-01-01"
    end_date: str = "2026-04-30"


@router.post("/link-token")
def link_token(body: LinkTokenRequest) -> dict:
    return plaid_client.create_link_token(body.user_id)


@router.post("/exchange")
def exchange(body: ExchangeRequest) -> dict:
    return plaid_client.exchange_public_token(body.public_token)


@router.post("/accounts")
def accounts(body: AccountsRequest) -> dict:
    return plaid_client.get_accounts(body.access_token)


@router.post("/transactions")
def transactions(body: TransactionsRequest) -> dict:
    return plaid_client.get_transactions(body.access_token, body.start_date, body.end_date)
