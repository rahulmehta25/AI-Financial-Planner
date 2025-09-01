"""
Transaction and import API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import logging

from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.models.all_models import Transaction, Account, Position
from app.schemas.transaction import TransactionResponse, ImportResponse
from app.services.transaction_import import CSVParser, BrokerFormat, TransactionProcessor

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/import", response_model=ImportResponse)
async def import_transactions(
    file: UploadFile = File(...),
    broker_format: str = Form(...),
    account_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import transactions from CSV file"""
    
    # Validate broker format
    try:
        broker = BrokerFormat(broker_format.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid broker format. Must be one of: {[b.value for b in BrokerFormat]}"
        )
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    # Read file content
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    # Get or create account
    account_query = select(Account).where(
        and_(
            Account.user_id == current_user.id,
            Account.name == account_name
        )
    )
    result = await db.execute(account_query)
    account = result.scalar_one_or_none()
    
    if not account:
        # Create new account
        account = Account(
            user_id=current_user.id,
            name=account_name,
            type="BROKERAGE",
            currency="USD",
            is_active=True
        )
        db.add(account)
        await db.flush()
    
    # Parse CSV
    parser = CSVParser()
    parsed_transactions = parser.parse(csv_content, broker)
    
    if not parsed_transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No valid transactions found. Errors: {parser.errors[:5]}"
        )
    
    # Process transactions
    processor = TransactionProcessor(db)
    results = await processor.process_transactions(
        parsed_transactions,
        account_id=str(account.id),
        user_id=str(current_user.id)
    )
    
    return ImportResponse(
        success=True,
        processed=results["processed"],
        duplicates=results["duplicates"],
        errors=results["errors"],
        message=f"Imported {results['processed']} transactions successfully",
        details=results.get("transactions", [])[:10]  # Return first 10 for preview
    )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    account_id: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's transactions with optional filtering"""
    
    # Build query
    query = select(Transaction).join(Account).where(
        Account.user_id == current_user.id
    )
    
    # Apply filters
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    
    if symbol:
        query = query.join(Transaction.instrument).where(
            Transaction.instrument.has(symbol=symbol)
        )
    
    # Order by date descending and apply pagination
    query = query.order_by(Transaction.trade_date.desc()).limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    # Convert to response format
    return [
        TransactionResponse(
            id=str(tx.id),
            account_id=str(tx.account_id),
            instrument_id=str(tx.instrument_id) if tx.instrument_id else None,
            symbol=tx.instrument.symbol if tx.instrument else None,
            type=tx.side.value if tx.side else 'UNKNOWN',
            date=tx.trade_date,
            quantity=tx.quantity,
            price=tx.price,
            amount=tx.amount,
            fees=tx.fees,
            description=tx.description
        )
        for tx in transactions
    ]


@router.get("/transactions/summary")
async def get_transaction_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics of user's transactions"""
    
    # Count total transactions
    count_query = select(func.count(Transaction.id)).join(Account).where(
        Account.user_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    # Count by type
    type_query = select(
        Transaction.type,
        func.count(Transaction.id)
    ).join(Account).where(
        Account.user_id == current_user.id
    ).group_by(Transaction.type)
    
    type_result = await db.execute(type_query)
    type_counts = dict(type_result.all())
    
    # Get date range
    date_query = select(
        func.min(Transaction.trade_date),
        func.max(Transaction.trade_date)
    ).join(Account).where(
        Account.user_id == current_user.id
    )
    
    date_result = await db.execute(date_query)
    min_date, max_date = date_result.first()
    
    return {
        "total_transactions": total_count,
        "transactions_by_type": type_counts,
        "date_range": {
            "start": min_date.isoformat() if min_date else None,
            "end": max_date.isoformat() if max_date else None
        }
    }


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific transaction (admin only for now)"""
    
    # Get transaction
    query = select(Transaction).join(Account).where(
        and_(
            Transaction.id == transaction_id,
            Account.user_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Delete transaction
    await db.delete(transaction)
    await db.commit()
    
    return {"message": "Transaction deleted successfully"}