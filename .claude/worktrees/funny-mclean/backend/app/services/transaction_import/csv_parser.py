"""
CSV parser for multiple broker formats with REAL parsing logic
"""
import csv
import io
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class BrokerFormat(Enum):
    """Supported broker CSV formats"""
    FIDELITY = "fidelity"
    VANGUARD = "vanguard"
    SCHWAB = "schwab"
    ETRADE = "etrade"
    GENERIC = "generic"


class TransactionType(Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    FEE = "FEE"
    TAX = "TAX"
    SPLIT = "SPLIT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


@dataclass
class ParsedTransaction:
    """Parsed transaction data"""
    date: datetime
    type: TransactionType
    symbol: Optional[str]
    quantity: Optional[Decimal]
    price: Optional[Decimal]
    amount: Decimal
    fees: Decimal = Decimal("0")
    description: str = ""
    broker_transaction_id: Optional[str] = None
    account_number: Optional[str] = None


class CSVParser:
    """Parse CSV files from different brokers"""
    
    # Fidelity CSV column mappings
    FIDELITY_COLUMNS = {
        "Run Date": "run_date",
        "Account": "account",
        "Action": "action",
        "Symbol": "symbol",
        "Security Description": "description",
        "Security Type": "security_type",
        "Quantity": "quantity",
        "Price": "price",
        "Commission": "commission",
        "Fees": "fees",
        "Accrued Interest": "accrued_interest",
        "Amount": "amount",
        "Settlement Date": "settlement_date"
    }
    
    # Vanguard CSV column mappings
    VANGUARD_COLUMNS = {
        "Trade Date": "trade_date",
        "Settlement Date": "settlement_date",
        "Transaction Type": "transaction_type",
        "Transaction Description": "description",
        "Investment Name": "investment_name",
        "Symbol": "symbol",
        "Shares": "shares",
        "Share Price": "price",
        "Principal Amount": "principal",
        "Commission Fees": "commission",
        "Net Amount": "net_amount",
        "Accrued Interest": "accrued_interest",
        "Account Number": "account"
    }
    
    # Schwab CSV column mappings
    SCHWAB_COLUMNS = {
        "Date": "date",
        "Action": "action",
        "Symbol": "symbol",
        "Description": "description",
        "Quantity": "quantity",
        "Price": "price",
        "Fees & Comm": "fees",
        "Amount": "amount"
    }
    
    def __init__(self):
        self.errors: List[str] = []
        
    def parse(self, csv_content: str, broker_format: BrokerFormat) -> List[ParsedTransaction]:
        """Parse CSV content based on broker format"""
        self.errors = []
        
        if broker_format == BrokerFormat.FIDELITY:
            return self._parse_fidelity(csv_content)
        elif broker_format == BrokerFormat.VANGUARD:
            return self._parse_vanguard(csv_content)
        elif broker_format == BrokerFormat.SCHWAB:
            return self._parse_schwab(csv_content)
        elif broker_format == BrokerFormat.GENERIC:
            return self._parse_generic(csv_content)
        else:
            raise ValueError(f"Unsupported broker format: {broker_format}")
    
    def _parse_fidelity(self, csv_content: str) -> List[ParsedTransaction]:
        """Parse Fidelity CSV format"""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Skip header rows and empty rows
                if not row.get("Amount") or row.get("Amount") == "Pending":
                    continue
                
                action = row.get("Action", "").upper()
                tx_type = self._map_fidelity_action(action)
                
                if tx_type is None:
                    continue
                
                # Parse date
                date_str = row.get("Settlement Date") or row.get("Run Date")
                tx_date = datetime.strptime(date_str, "%m/%d/%Y")
                
                # Parse amounts
                amount = self._parse_decimal(row.get("Amount", "0"))
                quantity = self._parse_decimal(row.get("Quantity")) if row.get("Quantity") else None
                price = self._parse_decimal(row.get("Price")) if row.get("Price") else None
                fees = self._parse_decimal(row.get("Fees", "0")) + self._parse_decimal(row.get("Commission", "0"))
                
                transaction = ParsedTransaction(
                    date=tx_date,
                    type=tx_type,
                    symbol=row.get("Symbol") if row.get("Symbol") and row.get("Symbol") != "N/A" else None,
                    quantity=quantity,
                    price=price,
                    amount=amount,
                    fees=fees,
                    description=row.get("Security Description", ""),
                    account_number=row.get("Account")
                )
                
                transactions.append(transaction)
                
            except Exception as e:
                self.errors.append(f"Row {row_num}: {str(e)}")
                logger.warning(f"Failed to parse row {row_num}: {e}")
        
        return transactions
    
    def _parse_vanguard(self, csv_content: str) -> List[ParsedTransaction]:
        """Parse Vanguard CSV format"""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row_num, row in enumerate(reader, start=2):
            try:
                tx_type_str = row.get("Transaction Type", "").upper()
                tx_type = self._map_vanguard_type(tx_type_str)
                
                if tx_type is None:
                    continue
                
                # Parse date
                date_str = row.get("Trade Date") or row.get("Settlement Date")
                tx_date = datetime.strptime(date_str, "%m/%d/%Y")
                
                # Parse amounts
                amount = self._parse_decimal(row.get("Net Amount", "0"))
                shares = self._parse_decimal(row.get("Shares")) if row.get("Shares") else None
                price = self._parse_decimal(row.get("Share Price")) if row.get("Share Price") else None
                fees = self._parse_decimal(row.get("Commission Fees", "0"))
                
                transaction = ParsedTransaction(
                    date=tx_date,
                    type=tx_type,
                    symbol=row.get("Symbol") if row.get("Symbol") else None,
                    quantity=shares,
                    price=price,
                    amount=amount,
                    fees=fees,
                    description=row.get("Transaction Description", ""),
                    account_number=row.get("Account Number")
                )
                
                transactions.append(transaction)
                
            except Exception as e:
                self.errors.append(f"Row {row_num}: {str(e)}")
                logger.warning(f"Failed to parse row {row_num}: {e}")
        
        return transactions
    
    def _parse_schwab(self, csv_content: str) -> List[ParsedTransaction]:
        """Parse Schwab CSV format"""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Skip totals row
                if row.get("Date", "").startswith("Transactions Total"):
                    continue
                
                action = row.get("Action", "").upper()
                tx_type = self._map_schwab_action(action)
                
                if tx_type is None:
                    continue
                
                # Parse date
                date_str = row.get("Date")
                tx_date = datetime.strptime(date_str, "%m/%d/%Y")
                
                # Parse amounts
                amount = self._parse_decimal(row.get("Amount", "0"))
                quantity = self._parse_decimal(row.get("Quantity")) if row.get("Quantity") else None
                price = self._parse_decimal(row.get("Price")) if row.get("Price") else None
                fees = self._parse_decimal(row.get("Fees & Comm", "0"))
                
                transaction = ParsedTransaction(
                    date=tx_date,
                    type=tx_type,
                    symbol=row.get("Symbol") if row.get("Symbol") else None,
                    quantity=quantity,
                    price=price,
                    amount=amount,
                    fees=fees,
                    description=row.get("Description", "")
                )
                
                transactions.append(transaction)
                
            except Exception as e:
                self.errors.append(f"Row {row_num}: {str(e)}")
                logger.warning(f"Failed to parse row {row_num}: {e}")
        
        return transactions
    
    def _parse_generic(self, csv_content: str) -> List[ParsedTransaction]:
        """Parse generic CSV format with standard columns"""
        transactions = []
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Generic format expects: Date, Type, Symbol, Quantity, Price, Amount, Fees
                tx_type = TransactionType[row.get("Type", "").upper()]
                
                # Parse date - try multiple formats
                date_str = row.get("Date")
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        tx_date = datetime.strptime(date_str, fmt)
                        break
                    except:
                        continue
                else:
                    raise ValueError(f"Could not parse date: {date_str}")
                
                # Parse amounts
                amount = self._parse_decimal(row.get("Amount", "0"))
                quantity = self._parse_decimal(row.get("Quantity")) if row.get("Quantity") else None
                price = self._parse_decimal(row.get("Price")) if row.get("Price") else None
                fees = self._parse_decimal(row.get("Fees", "0"))
                
                transaction = ParsedTransaction(
                    date=tx_date,
                    type=tx_type,
                    symbol=row.get("Symbol") if row.get("Symbol") else None,
                    quantity=quantity,
                    price=price,
                    amount=amount,
                    fees=fees,
                    description=row.get("Description", "")
                )
                
                transactions.append(transaction)
                
            except Exception as e:
                self.errors.append(f"Row {row_num}: {str(e)}")
                logger.warning(f"Failed to parse row {row_num}: {e}")
        
        return transactions
    
    def _map_fidelity_action(self, action: str) -> Optional[TransactionType]:
        """Map Fidelity action to transaction type"""
        action = action.upper()
        
        mapping = {
            "YOU BOUGHT": TransactionType.BUY,
            "BOUGHT": TransactionType.BUY,
            "YOU SOLD": TransactionType.SELL,
            "SOLD": TransactionType.SELL,
            "DIVIDEND RECEIVED": TransactionType.DIVIDEND,
            "DIVIDENDS RECEIVED": TransactionType.DIVIDEND,
            "INTEREST": TransactionType.INTEREST,
            "ELECTRONIC FUNDS TRANSFER": TransactionType.DEPOSIT,
            "TRANSFERRED": TransactionType.TRANSFER_IN,
            "FEE": TransactionType.FEE
        }
        
        for key, value in mapping.items():
            if key in action:
                return value
        
        return None
    
    def _map_vanguard_type(self, tx_type: str) -> Optional[TransactionType]:
        """Map Vanguard transaction type"""
        tx_type = tx_type.upper()
        
        mapping = {
            "BUY": TransactionType.BUY,
            "SELL": TransactionType.SELL,
            "DIVIDEND": TransactionType.DIVIDEND,
            "CAPITAL GAIN": TransactionType.DIVIDEND,
            "CONTRIBUTION": TransactionType.DEPOSIT,
            "DISTRIBUTION": TransactionType.WITHDRAWAL
        }
        
        for key, value in mapping.items():
            if key in tx_type:
                return value
        
        return None
    
    def _map_schwab_action(self, action: str) -> Optional[TransactionType]:
        """Map Schwab action to transaction type"""
        action = action.upper()
        
        mapping = {
            "BUY": TransactionType.BUY,
            "SELL": TransactionType.SELL,
            "CASH DIVIDEND": TransactionType.DIVIDEND,
            "QUALIFIED DIVIDEND": TransactionType.DIVIDEND,
            "BANK INTEREST": TransactionType.INTEREST,
            "WIRE RECEIVED": TransactionType.DEPOSIT,
            "WIRE SENT": TransactionType.WITHDRAWAL,
            "SERVICE FEE": TransactionType.FEE
        }
        
        for key, value in mapping.items():
            if key in action:
                return value
        
        return None
    
    def _parse_decimal(self, value: Optional[str]) -> Decimal:
        """Parse decimal value from string"""
        if not value:
            return Decimal("0")
        
        # Remove currency symbols and commas
        value = value.replace("$", "").replace(",", "").strip()
        
        # Handle parentheses for negative values
        if value.startswith("(") and value.endswith(")"):
            value = "-" + value[1:-1]
        
        try:
            return Decimal(value)
        except:
            return Decimal("0")