#!/usr/bin/env python3
"""
Test transaction import with real CSV parsing
"""
import asyncio
from datetime import datetime
from pathlib import Path

from app.services.transaction_import import CSVParser, BrokerFormat

async def test_csv_import():
    """Test CSV parsing functionality"""
    
    # Read the sample CSV
    csv_file = Path("test_data/fidelity_sample.csv")
    csv_content = csv_file.read_text()
    
    # Parse with Fidelity format
    parser = CSVParser()
    transactions = parser.parse(csv_content, BrokerFormat.FIDELITY)
    
    print(f"Parsed {len(transactions)} transactions from Fidelity CSV")
    print("-" * 50)
    
    for tx in transactions:
        print(f"Date: {tx.date.strftime('%Y-%m-%d')}")
        print(f"Type: {tx.type.value}")
        print(f"Symbol: {tx.symbol}")
        print(f"Quantity: {tx.quantity}")
        print(f"Price: ${tx.price}")
        print(f"Amount: ${tx.amount}")
        print(f"Fees: ${tx.fees}")
        print(f"Description: {tx.description}")
        print("-" * 50)
    
    if parser.errors:
        print("\nErrors encountered:")
        for error in parser.errors:
            print(f"  - {error}")
    
    # Test idempotency key generation
    print("\nTesting idempotency...")
    from app.services.transaction_import.transaction_processor import TransactionProcessor
    
    # Generate keys for duplicate check
    keys = set()
    for tx in transactions:
        key = hashlib.sha256(
            f"test_account|{tx.date.isoformat()}|{tx.type.value}|{tx.amount}|{tx.symbol or ''}".encode()
        ).hexdigest()
        
        if key in keys:
            print(f"  ⚠️ Duplicate detected: {tx.date} {tx.type.value} {tx.symbol}")
        else:
            keys.add(key)
            print(f"  ✓ Unique: {tx.date} {tx.type.value} {tx.symbol}")

if __name__ == "__main__":
    import hashlib
    asyncio.run(test_csv_import())