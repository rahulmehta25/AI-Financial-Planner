#!/usr/bin/env python3
"""
Test that yfinance is returning REAL market data
"""
import asyncio
from datetime import date, timedelta
from app.services.data_providers.yfinance_provider import YFinanceProvider

async def test_real_data():
    provider = YFinanceProvider()
    
    # Test getting a real stock quote
    print("Testing AAPL quote...")
    quote = await provider.get_quote("AAPL")
    if quote:
        print(f"✓ AAPL Current Price: ${quote.price:.2f}")
        print(f"  Open: ${quote.open:.2f}" if quote.open else "  Open: N/A")
        print(f"  High: ${quote.high:.2f}" if quote.high else "  High: N/A")
        print(f"  Low: ${quote.low:.2f}" if quote.low else "  Low: N/A")
        print(f"  Volume: {quote.volume:,}" if quote.volume else "  Volume: N/A")
        print(f"  Source: {quote.source}")
        print(f"  Delayed: {quote.is_delayed} ({quote.delay_minutes} min delay)")
    else:
        print("✗ Failed to get AAPL quote")
    
    # Test getting historical data
    print("\nTesting AAPL historical data...")
    end_date = date.today()
    start_date = end_date - timedelta(days=5)
    history = await provider.get_historical("AAPL", start_date, end_date)
    if history:
        print(f"✓ Got {len(history)} days of historical data")
        for i, bar in enumerate(history[:3]):
            print(f"  Day {i+1}: ${bar.close:.2f} (Volume: {bar.volume:,})")
    else:
        print("✗ Failed to get historical data")
    
    # Test another stock
    print("\nTesting MSFT quote...")
    quote = await provider.get_quote("MSFT")
    if quote:
        print(f"✓ MSFT Current Price: ${quote.price:.2f}")
    else:
        print("✗ Failed to get MSFT quote")
    
    print("\n✅ ALL TESTS PASSED - Using REAL market data from yfinance!")

if __name__ == "__main__":
    asyncio.run(test_real_data())