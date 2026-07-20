"""
Transaction processor with idempotency and position calculation
"""
import hashlib
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.all_models import Transaction, Position, Lot, Account, Instrument
from .csv_parser import ParsedTransaction, TransactionType

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Process transactions with idempotency and FIFO cost basis tracking"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.processed_count = 0
        self.duplicate_count = 0
        self.error_count = 0
        
    async def process_transactions(
        self,
        transactions: List[ParsedTransaction],
        account_id: str,
        user_id: str
    ) -> Dict[str, any]:
        """Process list of transactions with idempotency"""
        results = {
            "processed": 0,
            "duplicates": 0,
            "errors": 0,
            "transactions": []
        }
        
        for parsed_tx in transactions:
            try:
                # Generate idempotency key
                idempotency_key = self._generate_idempotency_key(parsed_tx, account_id)
                
                # Check if transaction already exists
                existing = await self._check_duplicate(idempotency_key)
                if existing:
                    results["duplicates"] += 1
                    logger.info(f"Duplicate transaction skipped: {idempotency_key}")
                    continue
                
                # Get or create instrument if needed
                instrument_id = None
                if parsed_tx.symbol:
                    instrument = await self._get_or_create_instrument(parsed_tx.symbol)
                    instrument_id = instrument.id
                
                # Create transaction
                transaction = Transaction(
                    account_id=account_id,
                    instrument_id=instrument_id,
                    type=parsed_tx.type.value,
                    date=parsed_tx.date,
                    quantity=parsed_tx.quantity,
                    price=parsed_tx.price,
                    amount=parsed_tx.amount,
                    fees=parsed_tx.fees,
                    description=parsed_tx.description,
                    idempotency_key=idempotency_key,
                    broker_transaction_id=parsed_tx.broker_transaction_id
                )
                
                self.db.add(transaction)
                
                # Update positions for BUY/SELL transactions
                if parsed_tx.type in [TransactionType.BUY, TransactionType.SELL]:
                    await self._update_position(
                        account_id=account_id,
                        instrument_id=instrument_id,
                        transaction=transaction,
                        parsed_tx=parsed_tx
                    )
                
                results["processed"] += 1
                results["transactions"].append({
                    "date": parsed_tx.date.isoformat(),
                    "type": parsed_tx.type.value,
                    "symbol": parsed_tx.symbol,
                    "amount": str(parsed_tx.amount)
                })
                
            except Exception as e:
                results["errors"] += 1
                logger.error(f"Failed to process transaction: {e}")
        
        # Commit all transactions
        await self.db.commit()
        
        # Recalculate all positions
        await self._recalculate_positions(account_id)
        
        return results
    
    def _generate_idempotency_key(self, tx: ParsedTransaction, account_id: str) -> str:
        """Generate unique key for transaction to prevent duplicates"""
        # Create a unique hash from transaction details
        key_parts = [
            account_id,
            tx.date.isoformat(),
            tx.type.value,
            str(tx.amount),
            tx.symbol or "",
            str(tx.quantity) if tx.quantity else "",
            str(tx.price) if tx.price else ""
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def _check_duplicate(self, idempotency_key: str) -> bool:
        """Check if transaction with this key already exists"""
        query = select(Transaction).where(
            Transaction.idempotency_key == idempotency_key
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _get_or_create_instrument(self, symbol: str) -> Instrument:
        """Get existing instrument or create new one"""
        # Check if instrument exists
        query = select(Instrument).where(Instrument.symbol == symbol)
        result = await self.db.execute(query)
        instrument = result.scalar_one_or_none()
        
        if not instrument:
            # Create new instrument
            instrument = Instrument(
                symbol=symbol,
                name=symbol,  # Will be updated by market data service
                type="STOCK",  # Default, will be updated
                exchange="US",  # Default
                currency="USD",
                is_active=True
            )
            self.db.add(instrument)
            await self.db.flush()  # Get the ID without committing
        
        return instrument
    
    async def _update_position(
        self,
        account_id: str,
        instrument_id: str,
        transaction: Transaction,
        parsed_tx: ParsedTransaction
    ):
        """Update position and lots using FIFO for sales"""
        # Get or create position
        query = select(Position).where(
            and_(
                Position.account_id == account_id,
                Position.instrument_id == instrument_id
            )
        )
        result = await self.db.execute(query)
        position = result.scalar_one_or_none()
        
        if not position:
            position = Position(
                account_id=account_id,
                instrument_id=instrument_id,
                quantity=Decimal("0"),
                cost_basis=Decimal("0"),
                market_value=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                realized_pnl=Decimal("0")
            )
            self.db.add(position)
        
        if parsed_tx.type == TransactionType.BUY:
            # Add to position
            position.quantity += parsed_tx.quantity
            position.cost_basis += (parsed_tx.amount + parsed_tx.fees)
            
            # Create new lot for FIFO tracking
            lot = Lot(
                position_id=position.id,
                transaction_id=transaction.id,
                acquisition_date=parsed_tx.date,
                quantity=parsed_tx.quantity,
                remaining_quantity=parsed_tx.quantity,
                cost_per_share=parsed_tx.price,
                total_cost=parsed_tx.amount + parsed_tx.fees
            )
            self.db.add(lot)
            
        elif parsed_tx.type == TransactionType.SELL:
            # Reduce position using FIFO
            remaining_to_sell = parsed_tx.quantity
            total_cost_basis_sold = Decimal("0")
            
            # Get lots ordered by acquisition date (FIFO)
            lots_query = select(Lot).where(
                and_(
                    Lot.position_id == position.id,
                    Lot.remaining_quantity > 0
                )
            ).order_by(Lot.acquisition_date)
            
            lots_result = await self.db.execute(lots_query)
            lots = lots_result.scalars().all()
            
            for lot in lots:
                if remaining_to_sell <= 0:
                    break
                
                # Calculate how much to sell from this lot
                sell_from_lot = min(remaining_to_sell, lot.remaining_quantity)
                
                # Calculate cost basis for this portion
                cost_per_share = lot.total_cost / lot.quantity
                cost_basis_sold = cost_per_share * sell_from_lot
                total_cost_basis_sold += cost_basis_sold
                
                # Update lot
                lot.remaining_quantity -= sell_from_lot
                remaining_to_sell -= sell_from_lot
            
            # Update position
            position.quantity -= parsed_tx.quantity
            position.cost_basis -= total_cost_basis_sold
            
            # Calculate realized P&L
            sale_proceeds = parsed_tx.amount - parsed_tx.fees
            realized_pnl = sale_proceeds - total_cost_basis_sold
            position.realized_pnl += realized_pnl
    
    async def _recalculate_positions(self, account_id: str):
        """Recalculate all positions for an account"""
        # Get all positions for the account
        query = select(Position).where(Position.account_id == account_id)
        result = await self.db.execute(query)
        positions = result.scalars().all()
        
        for position in positions:
            # Get all transactions for this position
            tx_query = select(Transaction).where(
                and_(
                    Transaction.account_id == account_id,
                    Transaction.instrument_id == position.instrument_id
                )
            ).order_by(Transaction.date)
            
            tx_result = await self.db.execute(tx_query)
            transactions = tx_result.scalars().all()
            
            # Recalculate from scratch
            total_quantity = Decimal("0")
            total_cost = Decimal("0")
            
            for tx in transactions:
                if tx.type == "BUY":
                    total_quantity += tx.quantity
                    total_cost += (tx.amount + tx.fees)
                elif tx.type == "SELL":
                    # For simplicity, using average cost for now
                    # Production would use proper FIFO from lots
                    if total_quantity > 0:
                        avg_cost = total_cost / total_quantity
                        cost_sold = avg_cost * tx.quantity
                        total_cost -= cost_sold
                    total_quantity -= tx.quantity
            
            position.quantity = total_quantity
            position.cost_basis = total_cost
        
        await self.db.commit()