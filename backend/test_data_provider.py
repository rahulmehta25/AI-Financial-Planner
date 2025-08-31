#!/usr/bin/env python3
"""
Test the real yfinance data provider with circuit breaker and caching
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))

from app.services.data_providers.yfinance_provider import YFinanceProvider
from app.services.data_providers.cached_provider import CachedDataProvider
from app.services.data_providers.circuit_breaker import CircuitOpenError


async def test_yfinance_provider():
    """Test yfinance provider functionality"""
    print("=" * 60)
    print("TESTING YFINANCE DATA PROVIDER")
    print("=" * 60)
    
    provider = YFinanceProvider()
    
    # Test 1: Get single quote
    print("\n1. Testing single quote fetch (AAPL)...")
    try:
        quote = await provider.get_quote("AAPL")
        if quote:
            print(f"✓ AAPL Quote:")
            print(f"  Price: ${quote.price}")
            print(f"  Open: ${quote.open}")
            print(f"  High/Low: ${quote.high}/${quote.low}")
            print(f"  Volume: {quote.volume:,}" if quote.volume else "  Volume: N/A")
            print(f"  Source: {quote.source}")
            print(f"  Delayed: {quote.delay_minutes} minutes")
        else:
            print("✗ Failed to fetch AAPL quote")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Get multiple quotes
    print("\n2. Testing bulk quote fetch...")
    symbols = ["MSFT", "GOOGL", "SPY", "INVALID_SYMBOL"]
    try:
        quotes = await provider.get_quotes(symbols)
        for symbol, quote in quotes.items():
            if quote:
                print(f"✓ {symbol}: ${quote.price}")
            else:
                print(f"✗ {symbol}: No data")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Get historical data
    print("\n3. Testing historical data fetch (SPY last 5 days)...")
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=5)
        bars = await provider.get_historical("SPY", start_date, end_date)
        
        if bars:
            print(f"✓ Retrieved {len(bars)} historical bars:")
            for bar in bars[:3]:  # Show first 3
                print(f"  {bar.date}: O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close}")
        else:
            print("✗ No historical data retrieved")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Circuit breaker
    print("\n4. Testing circuit breaker...")
    print("  Simulating failures to trigger circuit breaker...")
    
    # Force failures by using invalid symbol multiple times
    for i in range(4):
        try:
            await provider.get_quote("INVALID_SYMBOL_XYZ123")
        except:
            pass
    
    # Check circuit status
    status = provider.circuit_breaker.get_status()
    print(f"  Circuit state: {status['state']}")
    print(f"  Failure count: {status['failure_count']}/{status['failure_threshold']}")
    
    # Test 5: Provider status
    print("\n5. Provider status:")
    status_info = provider.get_status_info()
    print(f"  Provider: {status_info['provider']}")
    print(f"  Status: {status_info['status']}")
    print(f"  Circuit Breaker State: {status_info['circuit_breaker']['state']}")
    print(f"  Disclaimer: {status_info['disclaimer']}")
    
    return provider


async def test_cached_provider(provider: YFinanceProvider):
    """Test cached provider wrapper"""
    print("\n" + "=" * 60)
    print("TESTING CACHED DATA PROVIDER")
    print("=" * 60)
    
    try:
        # Create cached provider
        cached = CachedDataProvider(provider)
        
        # Test 1: First fetch (cache miss)
        print("\n1. First fetch (cache miss)...")
        import time
        start = time.time()
        quote1 = await cached.get_quote("TSLA")
        time1 = time.time() - start
        
        if quote1:
            print(f"✓ TSLA: ${quote1.price} (took {time1:.2f}s)")
        
        # Test 2: Second fetch (cache hit)
        print("\n2. Second fetch (should be cached)...")
        start = time.time()
        quote2 = await cached.get_quote("TSLA")
        time2 = time.time() - start
        
        if quote2:
            print(f"✓ TSLA: ${quote2.price} (took {time2:.2f}s)")
            if time2 < time1:
                print(f"✓ Cache working! Second fetch {time1/time2:.1f}x faster")
        
        # Test 3: Bulk fetch with partial cache
        print("\n3. Bulk fetch with partial cache...")
        symbols = ["TSLA", "NVDA", "AMD"]  # TSLA should be cached
        quotes = await cached.get_quotes(symbols)
        
        for symbol, quote in quotes.items():
            if quote:
                print(f"✓ {symbol}: ${quote.price}")
        
        # Close Redis connection
        await cached.close()
        
    except Exception as e:
        print(f"✗ Cached provider error: {e}")
        print("  Make sure Redis is running:")
        print("  docker-compose -f docker-compose.dev.yml up -d redis")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("REAL DATA PROVIDER TESTS")
    print("=" * 60)
    print("\n⚠️  DISCLAIMER: yfinance data is delayed by ~15 minutes")
    print("⚠️  This is suitable for portfolio tracking, not real-time trading")
    
    # Test yfinance provider
    provider = await test_yfinance_provider()
    
    # Test cached provider
    await test_cached_provider(provider)
    
    print("\n" + "=" * 60)
    print("✓ DATA PROVIDER TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())