"""
Transaction processing and CSV import service.
"""
import csv
import io
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
import logging
import re

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.portfolio import (
    Transaction, Instrument, Account, Lot, Position,
    TransactionSide, AssetClass
)

logger = logging.getLogger(__name__)


@dataclass
class ParsedTransaction:
    """Parsed transaction from CSV."""
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    trade_date: date
    settlement_date: Optional[date]
    notes: Optional[str]


class CSVParser:
    """Parse transactions from various broker CSV formats."""
    
    # Known broker CSV column mappings
    BROKER_MAPPINGS = {
        'fidelity': {
            'symbol': 'Symbol',
            'side': 'Action',
            'quantity': 'Quantity',
            'price': 'Price',
            'fee': 'Commission',
            'trade_date': 'Trade Date',
            'settlement_date': 'Settlement Date',
            'side_map': {'BUY': 'buy', 'SELL': 'sell', 'Buy': 'buy', 'Sell': 'sell'}
        },
        'vanguard': {
            'symbol': 'Symbol',
            'side': 'Transaction Type',
            'quantity': 'Shares',
            'price': 'Share Price',
            'fee': 'Commission',
            'trade_date': 'Trade Date',
            'settlement_date': 'Settlement Date',
            'side_map': {'Buy': 'buy', 'Sell': 'sell'}
        },
        'schwab': {
            'symbol': 'Symbol',
            'side': 'Action',
            'quantity': 'Quantity',
            'price': 'Price',
            'fee': 'Fees & Comm',
            'trade_date': 'Date',
            'settlement_date': None,
            'side_map': {'Buy': 'buy', 'Sell': 'sell', 'Bought': 'buy', 'Sold': 'sell'}
        }
    }
    
    def detect_broker(self, headers: List[str]) -> Optional[str]:
        """Detect broker format from CSV headers."""
        headers_lower = [h.lower() for h in headers]
        
        for broker, mapping in self.BROKER_MAPPINGS.items():
            required_cols = ['symbol', 'side', 'quantity', 'price', 'trade_date']
            matches = 0
            
            for col in required_cols:
                if mapping[col] and mapping[col].lower() in headers_lower:
                    matches += 1
                    
            if matches >= 4:  # At least 4 out of 5 required columns
                logger.info(f"Detected {broker} CSV format")
                return broker
                
        return None
    
    def parse_csv(self, csv_content: str, broker: Optional[str] = None) -> List[ParsedTransaction]:
        """Parse CSV content into transactions."""
        transactions = []
        
        # Try to detect broker if not specified
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        headers = reader.fieldnames
        
        if not broker:
            broker = self.detect_broker(headers)
            if not broker:
                raise ValueError("Unable to detect broker format. Please specify broker type.")
        
        mapping = self.BROKER_MAPPINGS.get(broker)
        if not mapping:
            raise ValueError(f"Unsupported broker: {broker}")
        
        # Reset reader
        csv_file.seek(0)
        reader = csv.DictReader(csv_file)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Extract values using mapping
                symbol = self._clean_symbol(row.get(mapping['symbol'], ''))
                side_raw = row.get(mapping['side'], '')
                side = mapping['side_map'].get(side_raw, side_raw.lower())
                
                quantity = self._parse_decimal(row.get(mapping['quantity'], '0'))
                price = self._parse_decimal(row.get(mapping['price'], '0'))
                fee = self._parse_decimal(row.get(mapping.get('fee', ''), '0'))
                
                trade_date = self._parse_date(row.get(mapping['trade_date'], ''))
                settlement_date = None
                if mapping.get('settlement_date'):
                    settlement_date = self._parse_date(row.get(mapping['settlement_date'], ''))
                
                # Validate transaction
                if not symbol or not side or quantity <= 0 or price < 0:
                    logger.warning(f"Skipping invalid transaction at row {row_num}")
                    continue
                
                transactions.append(ParsedTransaction(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    fee=fee,
                    trade_date=trade_date,
                    settlement_date=settlement_date,
                    notes=f"Imported from {broker} CSV"
                ))
                
            except Exception as e:
                logger.error(f"Error parsing row {row_num}: {e}")
                continue
        
        logger.info(f"Parsed {len(transactions)} transactions from CSV")
        return transactions
    
    def _clean_symbol(self, symbol: str) -> str:
        """Clean and normalize symbol."""
        # Remove common suffixes and clean up
        symbol = symbol.strip().upper()
        symbol = re.sub(r'\s+', '', symbol)  # Remove spaces
        symbol = re.sub(r'[^\w\.]', '', symbol)  # Keep only alphanumeric and dots
        return symbol
    
    def _parse_decimal(self, value: str) -> Decimal:
        """Parse decimal value from string."""
        if not value:
            return Decimal('0')
        # Remove currency symbols and commas
        value = re.sub(r'[,$]', '', value.strip())
        try:
            return Decimal(value)
        except:
            return Decimal('0')
    
    def _parse_date(self, value: str) -> Optional[date]:
        """Parse date from various formats."""
        if not value:
            return None
            
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%b %d, %Y',
            '%B %d, %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except:
                continue
                
        logger.warning(f"Unable to parse date: {value}")
        return None


class TransactionProcessor:
    """Process and import transactions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.csv_parser = CSVParser()
        
    def import_csv(
        self,
        csv_content: str,
        account_id: str,
        broker: Optional[str] = None
    ) -> Tuple[int, List[str]]:
        """Import transactions from CSV."""
        errors = []
        imported_count = 0
        
        # Parse CSV
        try:
            parsed_transactions = self.csv_parser.parse_csv(csv_content, broker)
        except Exception as e:
            errors.append(f"CSV parsing error: {e}")
            return 0, errors
        
        # Process each transaction
        for parsed_tx in parsed_transactions:
            try:
                # Generate idempotency key
                idempotency_key = self._generate_idempotency_key(account_id, parsed_tx)
                
                # Check if already exists
                existing = self.db.query(Transaction).filter_by(
                    idempotency_key=idempotency_key
                ).first()
                
                if existing:
                    logger.info(f"Transaction already exists: {parsed_tx.symbol} on {parsed_tx.trade_date}")
                    continue
                
                # Get or create instrument
                instrument = self._get_or_create_instrument(parsed_tx.symbol)
                
                # Create transaction
                transaction = Transaction(
                    account_id=account_id,
                    instrument_id=instrument.id,
                    side=TransactionSide.BUY if parsed_tx.side == 'buy' else TransactionSide.SELL,
                    quantity=parsed_tx.quantity,
                    price=parsed_tx.price,
                    fee=parsed_tx.fee,
                    trade_date=parsed_tx.trade_date,
                    settlement_date=parsed_tx.settlement_date,
                    idempotency_key=idempotency_key,
                    notes=parsed_tx.notes
                )
                
                self.db.add(transaction)
                self.db.flush()  # Get transaction ID
                
                # Create or update lots
                self._process_lots(transaction)
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error processing {parsed_tx.symbol}: {e}")
                logger.error(f"Transaction import error: {e}")
                continue
        
        # Update positions after all transactions
        self._update_positions(account_id)
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"Successfully imported {imported_count} transactions")
        except IntegrityError as e:
            self.db.rollback()
            errors.append(f"Database error: {e}")
            return 0, errors
        
        return imported_count, errors
    
    def _generate_idempotency_key(self, account_id: str, tx: ParsedTransaction) -> str:
        """Generate unique idempotency key for transaction."""
        key_data = f"{account_id}:{tx.symbol}:{tx.side}:{tx.quantity}:{tx.price}:{tx.trade_date}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_or_create_instrument(self, symbol: str) -> Instrument:
        """Get existing instrument or create new one."""
        instrument = self.db.query(Instrument).filter_by(symbol=symbol).first()
        
        if not instrument:
            # Determine asset class (simplified logic)
            asset_class = self._determine_asset_class(symbol)
            
            instrument = Instrument(
                symbol=symbol,
                name=symbol,  # Will be updated later by data provider
                asset_class=asset_class,
                currency='USD'
            )
            self.db.add(instrument)
            self.db.flush()
            
        return instrument
    
    def _determine_asset_class(self, symbol: str) -> AssetClass:
        """Determine asset class from symbol (simplified)."""
        # ETF detection (ends with specific patterns)
        etf_patterns = ['ETF', 'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO']
        if any(symbol.endswith(p) for p in etf_patterns):
            return AssetClass.ETF
        
        # Crypto detection
        crypto_symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'LINK', 'UNI']
        if symbol in crypto_symbols:
            return AssetClass.CRYPTO
        
        # Default to equity
        return AssetClass.EQUITY
    
    def _process_lots(self, transaction: Transaction):
        """Process tax lots for a transaction."""
        if transaction.side == TransactionSide.BUY:
            # Create new lot for buy
            lot = Lot(
                transaction_id=transaction.id,
                account_id=transaction.account_id,
                instrument_id=transaction.instrument_id,
                quantity_open=transaction.quantity,
                quantity_closed=0,
                cost_basis=transaction.price + (transaction.fee / transaction.quantity),
                open_date=transaction.trade_date
            )
            self.db.add(lot)
            
        else:  # SELL
            # Close lots using FIFO
            remaining_qty = transaction.quantity
            
            # Get open lots ordered by date (FIFO)
            open_lots = self.db.query(Lot).filter(
                Lot.account_id == transaction.account_id,
                Lot.instrument_id == transaction.instrument_id,
                Lot.close_date.is_(None)
            ).order_by(Lot.open_date).all()
            
            for lot in open_lots:
                if remaining_qty <= 0:
                    break
                    
                available_qty = lot.quantity_open - lot.quantity_closed
                close_qty = min(available_qty, remaining_qty)
                
                lot.quantity_closed += close_qty
                if lot.quantity_closed >= lot.quantity_open:
                    lot.close_date = transaction.trade_date
                    
                remaining_qty -= close_qty
            
            if remaining_qty > 0:
                logger.warning(f"Short sale detected: {remaining_qty} shares of {transaction.instrument_id}")
    
    def _update_positions(self, account_id: str):
        """Update cached positions for an account."""
        # Clear existing positions
        self.db.query(Position).filter_by(account_id=account_id).delete()
        
        # Calculate positions from lots
        lot_summary = self.db.query(
            Lot.instrument_id,
            func.sum(Lot.quantity_open - Lot.quantity_closed).label('quantity'),
            func.sum((Lot.quantity_open - Lot.quantity_closed) * Lot.cost_basis).label('total_cost')
        ).filter(
            Lot.account_id == account_id,
            Lot.quantity_open > Lot.quantity_closed
        ).group_by(Lot.instrument_id).all()
        
        for instrument_id, quantity, total_cost in lot_summary:
            if quantity > 0:
                position = Position(
                    account_id=account_id,
                    instrument_id=instrument_id,
                    quantity=quantity,
                    average_cost=total_cost / quantity if quantity > 0 else 0,
                    last_updated=datetime.utcnow()
                )
                self.db.add(position)
        
        self.db.flush()