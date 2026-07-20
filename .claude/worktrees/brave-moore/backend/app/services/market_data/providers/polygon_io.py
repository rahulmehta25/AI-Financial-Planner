"""
Polygon.io Market Data Provider

Professional market data provider with real-time WebSocket capabilities,
high-frequency data, and comprehensive fundamental data.
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
import websockets
import aiohttp
from decimal import Decimal

from .base import BaseProvider
from ..models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from ..config import config


class PolygonIOProvider(BaseProvider):
    """Polygon.io provider with real-time WebSocket streaming"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.name = "Polygon.io"
        self.api_key = api_key or config.polygon_api_key
        self.base_url = "https://api.polygon.io"
        self.ws_url = "wss://socket.polygon.io"
        
        # WebSocket connection management
        self.ws_connection = None
        self.ws_subscriptions = set()
        self.ws_handlers = {}
        self.ws_reconnect_delay = 5
        self.ws_max_reconnect_attempts = 10
        self.ws_is_authenticated = False
        
        # Rate limiting
        self.requests_per_minute = 5 if not self.api_key else 100
        self.request_timestamps = []
        
        # Circuit breaker
        self.failure_count = 0
        self.failure_threshold = 5
        self.reset_timeout = 300  # 5 minutes
        self.last_failure_time = None
        
        if not self.api_key:
            self.logger.warning("Polygon.io API key not provided - using free tier limits")
    
    async def _initialize_session(self):
        """Initialize HTTP session with proper headers"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'Authorization': f'Bearer {self.api_key}' if self.api_key else None,
                    'User-Agent': 'FinancialPlanner/1.0'
                }
            )
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps if ts > minute_ago
        ]
        
        if len(self.request_timestamps) >= self.requests_per_minute:
            sleep_time = 60 - (now - min(self.request_timestamps)).total_seconds()
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        
        self.request_timestamps.append(now)
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make authenticated API request with rate limiting and circuit breaker"""
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker is open, skipping request")
            return None
        
        await self._rate_limit_check()
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if self.api_key:
            params['apikey'] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self._reset_circuit_breaker()
                    return data
                elif response.status == 429:
                    self.logger.warning("Rate limit exceeded")
                    await asyncio.sleep(60)
                    return await self._make_request(endpoint, params)
                else:
                    self.logger.error(f"API error: {response.status} - {await response.text()}")
                    self._record_failure()
                    return None
                    
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            self._record_failure()
            return None
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.failure_count >= self.failure_threshold:
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if time_since_failure < self.reset_timeout:
                    return True
                else:
                    # Reset circuit breaker after timeout
                    self._reset_circuit_breaker()
        return False
    
    def _record_failure(self):
        """Record a failure for circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker after successful request"""
        self.failure_count = 0
        self.last_failure_time = None
    
    async def get_quote(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get real-time quote for symbol"""
        endpoint = f"/v2/last/trade/{symbol.upper()}"
        data = await self._make_request(endpoint)
        
        if not data or 'results' not in data:
            return None
        
        result = data['results']
        
        return MarketDataPoint(
            symbol=symbol.upper(),
            price=float(result.get('p', 0)),
            volume=int(result.get('s', 0)),
            timestamp=datetime.fromtimestamp(result.get('t', 0) / 1000),
            bid=None,  # Would need separate quote endpoint
            ask=None,
            open_price=None,
            high_price=None,
            low_price=None,
            previous_close=None,
            change=None,
            change_percent=None,
            provider=DataProvider.POLYGON_IO
        )
    
    async def get_multiple_quotes(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get quotes for multiple symbols efficiently"""
        quotes = []
        
        # Polygon.io doesn't have a bulk quote endpoint, so we'll use semaphore for concurrency
        semaphore = asyncio.Semaphore(5)
        
        async def fetch_quote(symbol: str):
            async with semaphore:
                quote = await self.get_quote(symbol)
                if quote:
                    quotes.append(quote)
        
        tasks = [fetch_quote(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return quotes
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str = "1d"
    ) -> Optional[HistoricalData]:
        """Get historical aggregates data"""
        
        # Map interval to Polygon format
        interval_map = {
            "1m": ("1", "minute"),
            "5m": ("5", "minute"),
            "15m": ("15", "minute"),
            "1h": ("1", "hour"),
            "1d": ("1", "day"),
            "1w": ("1", "week"),
            "1M": ("1", "month")
        }
        
        multiplier, timespan = interval_map.get(interval, ("1", "day"))
        
        endpoint = f"/v2/aggs/ticker/{symbol.upper()}/range/{multiplier}/{timespan}/{start_date.isoformat()}/{end_date.isoformat()}"
        
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000
        }
        
        data = await self._make_request(endpoint, params)
        
        if not data or 'results' not in data:
            return None
        
        data_points = []
        for result in data['results']:
            data_point = MarketDataPoint(
                symbol=symbol.upper(),
                price=float(result.get('c', 0)),  # close
                volume=int(result.get('v', 0)),
                timestamp=datetime.fromtimestamp(result.get('t', 0) / 1000),
                open_price=float(result.get('o', 0)),
                high_price=float(result.get('h', 0)),
                low_price=float(result.get('l', 0)),
                previous_close=None,
                change=None,
                change_percent=None,
                bid=None,
                ask=None,
                provider=DataProvider.POLYGON_IO
            )
            data_points.append(data_point)
        
        return HistoricalData(
            symbol=symbol.upper(),
            data_points=data_points,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            provider=DataProvider.POLYGON_IO
        )
    
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company details and financials"""
        endpoint = f"/v3/reference/tickers/{symbol.upper()}"
        data = await self._make_request(endpoint)
        
        if not data or 'results' not in data:
            return None
        
        result = data['results']
        
        return CompanyInfo(
            symbol=symbol.upper(),
            name=result.get('name', ''),
            description=result.get('description', ''),
            sector=result.get('sic_description', ''),
            industry=result.get('industry', ''),
            market_cap=result.get('market_cap'),
            shares_outstanding=result.get('share_class_shares_outstanding'),
            exchange=result.get('primary_exchange', ''),
            currency=result.get('currency_name', 'USD'),
            country=result.get('locale', ''),
            website=result.get('homepage_url', ''),
            employees=None,
            pe_ratio=None,
            dividend_yield=None,
            provider=DataProvider.POLYGON_IO
        )
    
    # WebSocket Implementation
    async def connect_websocket(self) -> bool:
        """Connect to Polygon.io WebSocket stream"""
        try:
            if self.ws_connection:
                return True
            
            self.logger.info("Connecting to Polygon.io WebSocket...")
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            self.ws_connection = await websockets.connect(
                f"{self.ws_url}/stocks",
                extra_headers=headers
            )
            
            # Authenticate
            await self._authenticate_websocket()
            
            # Start message handler
            asyncio.create_task(self._handle_websocket_messages())
            
            self.logger.info("Polygon.io WebSocket connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Polygon.io WebSocket: {e}")
            self.ws_connection = None
            return False
    
    async def _authenticate_websocket(self):
        """Authenticate WebSocket connection"""
        if not self.api_key:
            self.logger.warning("No API key for WebSocket authentication")
            return
        
        auth_message = {
            "action": "auth",
            "params": self.api_key
        }
        
        await self.ws_connection.send(json.dumps(auth_message))
        
        # Wait for auth response
        response = await self.ws_connection.recv()
        response_data = json.loads(response)
        
        if response_data[0].get('status') == 'auth_success':
            self.ws_is_authenticated = True
            self.logger.info("WebSocket authenticated successfully")
        else:
            self.logger.error(f"WebSocket authentication failed: {response_data}")
    
    async def _handle_websocket_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.ws_connection:
                try:
                    data = json.loads(message)
                    await self._process_websocket_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON in WebSocket message: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            self.ws_connection = None
            self.ws_is_authenticated = False
            
            # Attempt reconnection
            await self._reconnect_websocket()
            
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            self.ws_connection = None
            self.ws_is_authenticated = False
    
    async def _process_websocket_message(self, data: List[Dict[str, Any]]):
        """Process WebSocket messages"""
        for message in data:
            event_type = message.get('ev')
            
            if event_type == 'T':  # Trade
                await self._process_trade_message(message)
            elif event_type == 'Q':  # Quote
                await self._process_quote_message(message)
            elif event_type == 'A':  # Aggregate
                await self._process_aggregate_message(message)
            elif event_type == 'status':
                self.logger.info(f"WebSocket status: {message}")
    
    async def _process_trade_message(self, message: Dict[str, Any]):
        """Process real-time trade data"""
        symbol = message.get('sym')
        if not symbol:
            return
        
        trade_data = {
            'type': 'trade',
            'symbol': symbol,
            'price': message.get('p'),
            'volume': message.get('s'),
            'timestamp': datetime.fromtimestamp(message.get('t', 0) / 1000),
            'conditions': message.get('c', [])
        }
        
        # Call registered handlers
        if symbol in self.ws_handlers:
            for handler in self.ws_handlers[symbol]:
                try:
                    await handler(trade_data)
                except Exception as e:
                    self.logger.error(f"Error in WebSocket handler: {e}")
    
    async def _process_quote_message(self, message: Dict[str, Any]):
        """Process real-time quote data"""
        symbol = message.get('sym')
        if not symbol:
            return
        
        quote_data = {
            'type': 'quote',
            'symbol': symbol,
            'bid': message.get('bp'),
            'ask': message.get('ap'),
            'bid_size': message.get('bs'),
            'ask_size': message.get('as'),
            'timestamp': datetime.fromtimestamp(message.get('t', 0) / 1000)
        }
        
        # Call registered handlers
        if symbol in self.ws_handlers:
            for handler in self.ws_handlers[symbol]:
                try:
                    await handler(quote_data)
                except Exception as e:
                    self.logger.error(f"Error in WebSocket handler: {e}")
    
    async def _process_aggregate_message(self, message: Dict[str, Any]):
        """Process real-time aggregate data"""
        symbol = message.get('sym')
        if not symbol:
            return
        
        agg_data = {
            'type': 'aggregate',
            'symbol': symbol,
            'open': message.get('o'),
            'high': message.get('h'),
            'low': message.get('l'),
            'close': message.get('c'),
            'volume': message.get('v'),
            'vwap': message.get('vw'),
            'timestamp': datetime.fromtimestamp(message.get('t', 0) / 1000)
        }
        
        # Call registered handlers
        if symbol in self.ws_handlers:
            for handler in self.ws_handlers[symbol]:
                try:
                    await handler(agg_data)
                except Exception as e:
                    self.logger.error(f"Error in WebSocket handler: {e}")
    
    async def _reconnect_websocket(self):
        """Attempt to reconnect WebSocket with exponential backoff"""
        attempt = 0
        while attempt < self.ws_max_reconnect_attempts:
            delay = min(300, self.ws_reconnect_delay * (2 ** attempt))
            self.logger.info(f"Attempting WebSocket reconnection in {delay}s (attempt {attempt + 1})")
            
            await asyncio.sleep(delay)
            
            if await self.connect_websocket():
                # Resubscribe to previous subscriptions
                await self._resubscribe()
                return
            
            attempt += 1
        
        self.logger.error("Max reconnection attempts reached, giving up")
    
    async def _resubscribe(self):
        """Resubscribe to previous WebSocket subscriptions"""
        if not self.ws_subscriptions or not self.ws_is_authenticated:
            return
        
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(self.ws_subscriptions)
        }
        
        await self.ws_connection.send(json.dumps(subscribe_message))
        self.logger.info(f"Resubscribed to {len(self.ws_subscriptions)} streams")
    
    async def subscribe_to_trades(self, symbols: List[str]) -> bool:
        """Subscribe to real-time trade data"""
        if not await self.connect_websocket() or not self.ws_is_authenticated:
            return False
        
        streams = [f"T.{symbol.upper()}" for symbol in symbols]
        
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(streams)
        }
        
        await self.ws_connection.send(json.dumps(subscribe_message))
        self.ws_subscriptions.update(streams)
        
        self.logger.info(f"Subscribed to trade streams for {len(symbols)} symbols")
        return True
    
    async def subscribe_to_quotes(self, symbols: List[str]) -> bool:
        """Subscribe to real-time quote data"""
        if not await self.connect_websocket() or not self.ws_is_authenticated:
            return False
        
        streams = [f"Q.{symbol.upper()}" for symbol in symbols]
        
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(streams)
        }
        
        await self.ws_connection.send(json.dumps(subscribe_message))
        self.ws_subscriptions.update(streams)
        
        self.logger.info(f"Subscribed to quote streams for {len(symbols)} symbols")
        return True
    
    def register_handler(self, symbol: str, handler: Callable):
        """Register handler for real-time data"""
        if symbol not in self.ws_handlers:
            self.ws_handlers[symbol] = []
        self.ws_handlers[symbol].append(handler)
    
    async def disconnect_websocket(self):
        """Disconnect WebSocket connection"""
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None
            self.ws_is_authenticated = False
            self.ws_subscriptions.clear()
            self.ws_handlers.clear()
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            # Simple API call to check connectivity
            data = await self._make_request("/v2/last/trade/AAPL")
            return data is not None
        except Exception:
            return False
    
    async def _cleanup_session(self):
        """Cleanup resources"""
        await self.disconnect_websocket()
        await super()._cleanup_session()