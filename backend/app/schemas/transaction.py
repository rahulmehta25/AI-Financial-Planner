"""
Transaction schemas for API responses
"""
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any


class TransactionResponse(BaseModel):
    """Transaction response model"""
    id: str
    account_id: str
    instrument_id: Optional[str] = None
    symbol: Optional[str] = None
    type: str
    date: datetime
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Decimal
    fees: Decimal
    description: str
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class ImportResponse(BaseModel):
    """Import response model"""
    success: bool
    processed: int
    duplicates: int
    errors: int
    message: str
    details: Optional[List[Dict[str, Any]]] = None