"""
Financial data endpoints for accounts, transactions, and budgeting
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User

router = APIRouter()


@router.get("/accounts")
async def get_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get user's financial accounts"""
    # Mock data for now
    return {
        "accounts": [
            {
                "id": "acc-1",
                "name": "Chase Checking",
                "type": "checking",
                "balance": 12500.75,
                "currency": "USD",
                "last_updated": "2024-01-15T10:30:00Z"
            },
            {
                "id": "acc-2", 
                "name": "Savings Account",
                "type": "savings",
                "balance": 25000.00,
                "currency": "USD",
                "last_updated": "2024-01-15T10:30:00Z"
            },
            {
                "id": "acc-3",
                "name": "401k Investment",
                "type": "investment",
                "balance": 85000.50,
                "currency": "USD",
                "last_updated": "2024-01-15T10:30:00Z"
            }
        ],
        "total_balance": 122501.25,
        "total_accounts": 3
    }


@router.get("/transactions")
async def get_transactions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
) -> Any:
    """Get user's recent transactions"""
    # Mock data for now
    return {
        "transactions": [
            {
                "id": "txn-1",
                "account_id": "acc-1",
                "amount": -150.75,
                "description": "Grocery Store Purchase",
                "category": "food",
                "date": "2024-01-15T14:30:00Z",
                "type": "expense"
            },
            {
                "id": "txn-2", 
                "account_id": "acc-1",
                "amount": 2500.00,
                "description": "Salary Deposit",
                "category": "income",
                "date": "2024-01-15T08:00:00Z",
                "type": "income"
            },
            {
                "id": "txn-3",
                "account_id": "acc-3",
                "amount": 280.50,
                "description": "Investment Dividend",
                "category": "investment",
                "date": "2024-01-14T16:45:00Z",
                "type": "income"
            }
        ],
        "total_transactions": 125,
        "limit": limit,
        "offset": offset
    }


@router.get("/goals")
async def get_financial_goals(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get user's financial goals"""
    # Mock data for now
    return {
        "goals": [
            {
                "id": "goal-1",
                "name": "Emergency Fund",
                "target_amount": 25000.00,
                "current_amount": 15000.00,
                "target_date": "2024-12-31",
                "category": "emergency",
                "progress_percent": 60.0,
                "status": "in_progress"
            },
            {
                "id": "goal-2",
                "name": "Retirement Savings", 
                "target_amount": 500000.00,
                "current_amount": 85000.00,
                "target_date": "2054-01-01",
                "category": "retirement",
                "progress_percent": 17.0,
                "status": "in_progress"
            },
            {
                "id": "goal-3",
                "name": "House Down Payment",
                "target_amount": 100000.00,
                "current_amount": 30000.00,
                "target_date": "2025-06-01",
                "category": "real_estate",
                "progress_percent": 30.0,
                "status": "in_progress"
            }
        ],
        "total_goals": 3,
        "average_progress": 35.7
    }


@router.get("/budget")
async def get_budget(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get user's budget information"""
    # Mock data for now
    return {
        "budget": {
            "monthly_income": 6500.00,
            "monthly_expenses": 4200.00,
            "monthly_savings": 2300.00,
            "categories": [
                {
                    "name": "Housing",
                    "budgeted": 2000.00,
                    "spent": 1950.00,
                    "remaining": 50.00,
                    "percent_used": 97.5
                },
                {
                    "name": "Food",
                    "budgeted": 600.00,
                    "spent": 585.25,
                    "remaining": 14.75,
                    "percent_used": 97.5
                },
                {
                    "name": "Transportation",
                    "budgeted": 400.00,
                    "spent": 325.50,
                    "remaining": 74.50,
                    "percent_used": 81.4
                },
                {
                    "name": "Entertainment",
                    "budgeted": 300.00,
                    "spent": 245.75,
                    "remaining": 54.25,
                    "percent_used": 81.9
                }
            ]
        },
        "summary": {
            "total_budgeted": 4200.00,
            "total_spent": 3893.50,
            "remaining": 306.50,
            "savings_rate": 35.4
        }
    }