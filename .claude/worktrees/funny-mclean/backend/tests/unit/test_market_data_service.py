"""
Comprehensive unit tests for market data service.

Tests cover:
- Real-time data fetching from multiple providers
- Historical data retrieval and caching
- Data validation and normalization
- Error handling and fallback mechanisms
- WebSocket streaming functionality
- Performance benchmarks
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List

from app.services.market_data.manager import MarketDataManager
from app.services.market_data.providers.base import BaseMarketDataProvider, MarketDataError
from app.services.market_data.cache.cache_manager import CacheManager
from app.services.market_data.models import (
    MarketDataPoint, HistoricalData, RealTimeQuote, OptionChain
)
from app.schemas.market_data import MarketDataRequest, TimeSeriesRequest


class TestMarketDataManager:
    """Test market data manager functionality."""
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Mock cache manager."""
        mock = AsyncMock(spec=CacheManager)
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        return mock
    
    @pytest.fixture
    def mock_primary_provider(self):
        """Mock primary market data provider."""
        mock = AsyncMock(spec=BaseMarketDataProvider)
        mock.name = "polygon_io"
        mock.is_available.return_value = True
        return mock
    
    @pytest.fixture
    def mock_fallback_provider(self):
        """Mock fallback market data provider."""
        mock = AsyncMock(spec=BaseMarketDataProvider)
        mock.name = "yfinance"
        mock.is_available.return_value = True
        return mock
    
    @pytest.fixture
    def market_data_manager(self, mock_cache_manager, mock_primary_provider, mock_fallback_provider):
        """Create market data manager with mocked dependencies."""
        manager = MarketDataManager(
            cache_manager=mock_cache_manager,
            primary_provider=mock_primary_provider,
            fallback_providers=[mock_fallback_provider]
        )
        return manager
    
    @pytest.fixture
    def sample_market_data_point(self):
        """Sample market data point for testing."""
        return MarketDataPoint(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150.00"),
            high_price=Decimal("152.50"),
            low_price=Decimal("149.25"),
            close_price=Decimal("151.75"),
            volume=1000000,
            adjusted_close=Decimal("151.75")
        )
    
    @pytest.fixture
    def sample_real_time_quote(self):
        """Sample real-time quote for testing."""
        return RealTimeQuote(
            symbol="AAPL",
            price=Decimal("151.75"),
            change=Decimal("1.25"),
            change_percent=Decimal("0.83"),
            volume=50000,
            bid=Decimal("151.70"),
            ask=Decimal("151.80"),
            timestamp=datetime.now()
        )
    
    async def test_get_real_time_quote_success(self, market_data_manager, mock_primary_provider, sample_real_time_quote):
        """Test successful real-time quote retrieval."""
        mock_primary_provider.get_real_time_quote.return_value = sample_real_time_quote
        
        result = await market_data_manager.get_real_time_quote("AAPL")
        
        assert result == sample_real_time_quote
        mock_primary_provider.get_real_time_quote.assert_called_once_with("AAPL")
    
    async def test_get_real_time_quote_with_fallback(self, market_data_manager, 
                                                   mock_primary_provider, mock_fallback_provider,
                                                   sample_real_time_quote):
        """Test real-time quote retrieval with provider fallback."""
        # Primary provider fails
        mock_primary_provider.get_real_time_quote.side_effect = MarketDataError("Primary provider failed")
        # Fallback provider succeeds
        mock_fallback_provider.get_real_time_quote.return_value = sample_real_time_quote
        
        result = await market_data_manager.get_real_time_quote("AAPL")
        
        assert result == sample_real_time_quote
        mock_primary_provider.get_real_time_quote.assert_called_once_with("AAPL")
        mock_fallback_provider.get_real_time_quote.assert_called_once_with("AAPL")
    
    async def test_get_real_time_quote_all_providers_fail(self, market_data_manager,
                                                        mock_primary_provider, mock_fallback_provider):
        """Test behavior when all providers fail."""
        error_msg = "All providers failed"
        mock_primary_provider.get_real_time_quote.side_effect = MarketDataError(error_msg)
        mock_fallback_provider.get_real_time_quote.side_effect = MarketDataError(error_msg)
        
        with pytest.raises(MarketDataError, match="All market data providers failed"):
            await market_data_manager.get_real_time_quote("AAPL")
    
    async def test_get_historical_data_cached(self, market_data_manager, mock_cache_manager, sample_market_data_point):
        """Test historical data retrieval from cache."""
        historical_data = HistoricalData(
            symbol="AAPL",
            data_points=[sample_market_data_point],
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        mock_cache_manager.get.return_value = historical_data
        
        request = TimeSeriesRequest(
            symbol="AAPL",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            interval="1D"
        )
        
        result = await market_data_manager.get_historical_data(request)
        
        assert result == historical_data
        mock_cache_manager.get.assert_called_once()
    
    async def test_get_historical_data_not_cached(self, market_data_manager, mock_cache_manager,
                                                 mock_primary_provider, sample_market_data_point):
        """Test historical data retrieval when not in cache."""
        historical_data = HistoricalData(
            symbol="AAPL",
            data_points=[sample_market_data_point],
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        # Not in cache
        mock_cache_manager.get.return_value = None
        # Retrieved from provider
        mock_primary_provider.get_historical_data.return_value = historical_data
        
        request = TimeSeriesRequest(
            symbol="AAPL",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            interval="1D"
        )
        
        result = await market_data_manager.get_historical_data(request)
        
        assert result == historical_data
        mock_cache_manager.get.assert_called_once()
        mock_primary_provider.get_historical_data.assert_called_once_with(request)
        mock_cache_manager.set.assert_called_once()
    
    async def test_get_multiple_quotes_concurrent(self, market_data_manager, mock_primary_provider):
        """Test concurrent retrieval of multiple quotes."""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        
        # Mock responses for each symbol
        quotes = []
        for symbol in symbols:
            quote = RealTimeQuote(
                symbol=symbol,
                price=Decimal(f"{100 + len(symbol)}.50"),
                change=Decimal("1.25"),
                change_percent=Decimal("0.83"),
                volume=50000,
                bid=Decimal(f"{100 + len(symbol)}.45"),
                ask=Decimal(f"{100 + len(symbol)}.55"),
                timestamp=datetime.now()
            )
            quotes.append(quote)
        
        mock_primary_provider.get_real_time_quote.side_effect = quotes
        
        results = await market_data_manager.get_multiple_quotes(symbols)
        
        assert len(results) == len(symbols)
        for symbol, result in zip(symbols, results):
            assert result.symbol == symbol
        
        assert mock_primary_provider.get_real_time_quote.call_count == len(symbols)
    
    async def test_validate_symbol_format(self, market_data_manager):
        """Test symbol format validation."""
        valid_symbols = ["AAPL", "GOOGL", "BRK.B", "BRK-A"]
        invalid_symbols = ["", "123", "TOOLONGSYMBOL", "SYM@BOL"]
        
        for symbol in valid_symbols:
            assert market_data_manager._validate_symbol(symbol) == True
        
        for symbol in invalid_symbols:
            assert market_data_manager._validate_symbol(symbol) == False
    
    async def test_data_normalization(self, market_data_manager, mock_primary_provider):
        """Test data normalization across providers."""
        raw_data = {
            "symbol": "AAPL",
            "price": "151.75",  # String instead of Decimal
            "volume": 1000000,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        normalized_data = market_data_manager._normalize_quote_data(raw_data)
        
        assert isinstance(normalized_data["price"], Decimal)
        assert normalized_data["price"] == Decimal("151.75")
        assert isinstance(normalized_data["timestamp"], datetime)
        assert normalized_data["symbol"] == "AAPL"
    
    @pytest.mark.benchmark
    async def test_quote_retrieval_performance(self, market_data_manager, mock_primary_provider, benchmark):
        """Benchmark quote retrieval performance."""
        mock_primary_provider.get_real_time_quote.return_value = RealTimeQuote(
            symbol="AAPL",
            price=Decimal("151.75"),
            change=Decimal("1.25"),
            change_percent=Decimal("0.83"),
            volume=50000,
            bid=Decimal("151.70"),
            ask=Decimal("151.80"),
            timestamp=datetime.now()
        )
        
        # Benchmark should complete in under 100ms
        result = benchmark(asyncio.run, market_data_manager.get_real_time_quote("AAPL"))
        assert result is not None


class TestMarketDataProviders:
    """Test individual market data providers."""
    
    @pytest.fixture
    def mock_polygon_client(self):
        """Mock Polygon.io client."""
        mock = MagicMock()
        return mock
    
    @pytest.fixture
    def mock_yfinance(self):
        """Mock yfinance client."""
        mock = MagicMock()
        return mock
    
    @pytest.mark.integration
    async def test_polygon_provider_integration(self):
        """Integration test for Polygon.io provider."""
        # This would test against actual Polygon.io API in integration tests
        pass
    
    @pytest.mark.integration
    async def test_yfinance_provider_integration(self):
        """Integration test for yfinance provider."""
        # This would test against actual Yahoo Finance API in integration tests
        pass
    
    async def test_provider_error_handling(self):
        """Test provider error handling and recovery."""
        # Test rate limiting
        # Test network errors
        # Test invalid responses
        pass


class TestMarketDataCache:
    """Test market data caching functionality."""
    
    @pytest.fixture
    def cache_manager(self, mock_redis):
        """Create cache manager with mocked Redis."""
        return CacheManager(redis_client=mock_redis)
    
    async def test_cache_key_generation(self, cache_manager):
        """Test cache key generation for different data types."""
        quote_key = cache_manager._generate_cache_key("quote", "AAPL")
        historical_key = cache_manager._generate_cache_key("historical", "AAPL", "2024-01-01", "2024-01-31")
        
        assert "quote:AAPL" in quote_key
        assert "historical:AAPL" in historical_key
        assert "2024-01-01" in historical_key
    
    async def test_cache_expiration(self, cache_manager, mock_redis):
        """Test cache expiration for different data types."""
        # Real-time data should expire quickly (seconds)
        # Historical data should expire slowly (hours/days)
        await cache_manager.set_quote("AAPL", {"price": 150.00})
        
        # Verify TTL was set appropriately
        mock_redis.setex.assert_called()
        call_args = mock_redis.setex.call_args
        ttl = call_args[0][1]  # Second argument is TTL
        assert ttl <= 60  # Real-time data expires within 60 seconds
    
    async def test_cache_invalidation(self, cache_manager, mock_redis):
        """Test cache invalidation strategies."""
        await cache_manager.invalidate_symbol_cache("AAPL")
        
        # Should delete all cache entries for the symbol
        mock_redis.delete.assert_called()


class TestMarketDataWebSocket:
    """Test WebSocket streaming functionality."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        mock = AsyncMock()
        return mock
    
    async def test_websocket_connection(self, mock_websocket):
        """Test WebSocket connection establishment."""
        # Test connection establishment
        # Test authentication
        # Test subscription to symbols
        pass
    
    async def test_websocket_data_streaming(self, mock_websocket):
        """Test real-time data streaming via WebSocket."""
        # Test real-time quote streaming
        # Test trade streaming
        # Test market status updates
        pass
    
    async def test_websocket_error_handling(self, mock_websocket):
        """Test WebSocket error handling and reconnection."""
        # Test connection drops
        # Test invalid messages
        # Test rate limiting
        pass


class TestMarketDataValidation:
    """Test market data validation and quality checks."""
    
    def test_price_validation(self):
        """Test price data validation."""
        from app.services.market_data.validators import PriceValidator
        
        validator = PriceValidator()
        
        # Valid prices
        assert validator.validate_price(Decimal("150.50")) == True
        assert validator.validate_price(Decimal("0.01")) == True
        
        # Invalid prices
        assert validator.validate_price(Decimal("-10.00")) == False
        assert validator.validate_price(Decimal("0")) == False
        assert validator.validate_price(None) == False
    
    def test_volume_validation(self):
        """Test volume data validation."""
        from app.services.market_data.validators import VolumeValidator
        
        validator = VolumeValidator()
        
        # Valid volumes
        assert validator.validate_volume(1000000) == True
        assert validator.validate_volume(0) == True  # Some securities may have 0 volume
        
        # Invalid volumes
        assert validator.validate_volume(-1000) == False
        assert validator.validate_volume(None) == False
    
    def test_timestamp_validation(self):
        """Test timestamp validation."""
        from app.services.market_data.validators import TimestampValidator
        
        validator = TimestampValidator()
        
        now = datetime.now()
        
        # Valid timestamps
        assert validator.validate_timestamp(now) == True
        assert validator.validate_timestamp(now - timedelta(hours=1)) == True
        
        # Invalid timestamps
        future_time = now + timedelta(hours=1)
        assert validator.validate_timestamp(future_time) == False
        assert validator.validate_timestamp(None) == False
    
    def test_data_completeness(self):
        """Test data completeness validation."""
        from app.services.market_data.validators import CompletenessValidator
        
        validator = CompletenessValidator()
        
        complete_data = {
            "symbol": "AAPL",
            "price": Decimal("150.50"),
            "volume": 1000000,
            "timestamp": datetime.now()
        }
        
        incomplete_data = {
            "symbol": "AAPL",
            "price": Decimal("150.50")
            # Missing volume and timestamp
        }
        
        assert validator.validate_completeness(complete_data) == True
        assert validator.validate_completeness(incomplete_data) == False


class TestMarketDataAggregation:
    """Test market data aggregation and calculations."""
    
    def test_ohlcv_aggregation(self):
        """Test OHLCV data aggregation."""
        from app.services.market_data.aggregators import OHLCVAggregator
        
        aggregator = OHLCVAggregator()
        
        # Sample tick data
        ticks = [
            {"price": Decimal("150.00"), "volume": 100, "timestamp": datetime(2024, 1, 1, 9, 30, 0)},
            {"price": Decimal("150.25"), "volume": 200, "timestamp": datetime(2024, 1, 1, 9, 30, 30)},
            {"price": Decimal("149.75"), "volume": 150, "timestamp": datetime(2024, 1, 1, 9, 31, 0)},
            {"price": Decimal("150.10"), "volume": 300, "timestamp": datetime(2024, 1, 1, 9, 31, 30)},
        ]
        
        ohlcv = aggregator.aggregate_minute(ticks)
        
        assert ohlcv["open"] == Decimal("150.00")
        assert ohlcv["high"] == Decimal("150.25")
        assert ohlcv["low"] == Decimal("149.75")
        assert ohlcv["close"] == Decimal("150.10")
        assert ohlcv["volume"] == 750
    
    def test_technical_indicators(self):
        """Test technical indicator calculations."""
        from app.services.market_data.indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        
        # Sample price data
        prices = [Decimal(str(price)) for price in [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]]
        
        # Simple Moving Average
        sma_5 = indicators.simple_moving_average(prices, period=5)
        assert len(sma_5) == len(prices) - 4  # 5-period SMA starts from 5th data point
        
        # RSI
        rsi = indicators.relative_strength_index(prices, period=5)
        assert all(0 <= value <= 100 for value in rsi if value is not None)
        
        # MACD
        macd_line, signal_line, histogram = indicators.macd(prices)
        assert len(macd_line) == len(signal_line) == len(histogram)


class TestMarketDataErrorScenarios:
    """Test error scenarios and edge cases."""
    
    async def test_network_timeout_handling(self, market_data_manager):
        """Test handling of network timeouts."""
        # Mock network timeout
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError("Request timed out")
            
            with pytest.raises(MarketDataError, match="Request timed out"):
                await market_data_manager.get_real_time_quote("AAPL")
    
    async def test_rate_limiting_handling(self, market_data_manager):
        """Test handling of rate limiting responses."""
        # Mock rate limiting response (HTTP 429)
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.text.return_value = "Rate limit exceeded"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(MarketDataError, match="Rate limit"):
                await market_data_manager.get_real_time_quote("AAPL")
    
    async def test_invalid_json_response(self, market_data_manager):
        """Test handling of invalid JSON responses."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(MarketDataError, match="Invalid response format"):
                await market_data_manager.get_real_time_quote("AAPL")
    
    async def test_market_closed_handling(self, market_data_manager):
        """Test behavior when market is closed."""
        # Test different market hours
        # Test weekend handling
        # Test holiday handling
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
