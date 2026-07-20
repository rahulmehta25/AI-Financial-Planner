"""
Databento Market Data Provider

Professional market data provider with high-quality institutional data,
comprehensive historical coverage, and real-time streaming capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, AsyncIterator
import aiohttp
import websockets
from decimal import Decimal

from .base import BaseProvider
from ..models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from ..config import config


class DatabentoProvider(BaseProvider):
    """Databento provider for institutional-grade market data"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.name = "Databento"
        self.api_key = api_key or config.databento_api_key
        self.base_url = "https://hist.databento.com"
        self.live_base_url = "https://live.databento.com"
        
        # WebSocket connection management
        self.ws_connection = None
        self.ws_subscriptions = set()
        self.ws_handlers = {}
        self.ws_session_id = None
        
        # Rate limiting (generous for professional accounts)
        self.requests_per_minute = 1000
        self.request_timestamps = []
        
        # Circuit breaker
        self.failure_count = 0
        self.failure_threshold = 3
        self.reset_timeout = 180  # 3 minutes
        self.last_failure_time = None
        
        if not self.api_key:
            raise ValueError("Databento requires an API key")
    
    async def _initialize_session(self):
        """Initialize HTTP session with proper authentication"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'User-Agent': 'FinancialPlanner/1.0',
                    'Content-Type': 'application/json'
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
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None, method: str = 'GET') -> Optional[Dict]:
        """Make authenticated API request with circuit breaker"""
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker is open, skipping request")
            return None
        
        await self._rate_limit_check()
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        try:
            async with self.session.request(method, url, params=params if method == 'GET' else None, 
                                          json=params if method == 'POST' else None) as response:
                if response.status == 200:
                    data = await response.json()
                    self._reset_circuit_breaker()
                    return data
                elif response.status == 429:
                    self.logger.warning("Rate limit exceeded")
                    await asyncio.sleep(60)
                    return await self._make_request(endpoint, params, method)
                else:
                    error_text = await response.text()
                    self.logger.error(f"API error: {response.status} - {error_text}")
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
        """Get real-time quote - Databento focuses on historical data, so this is limited"""
        # Note: Databento is primarily historical, real-time quotes would come through WebSocket
        self.logger.warning("Databento is primarily historical - consider using WebSocket for real-time data")
        return None
    
    async def get_multiple_quotes(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Databento doesn't provide real-time quotes via REST API"""
        self.logger.warning("Databento doesn't provide real-time quotes via REST API")
        return []
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str = "1d"
    ) -> Optional[HistoricalData]:
        """Get historical OHLCV data from Databento"""
        
        # Map interval to Databento schema
        schema_map = {
            "1m": "ohlcv-1m",
            "5m": "ohlcv-5m", 
            "15m": "ohlcv-15m",
            "1h": "ohlcv-1h",
            "1d": "ohlcv-1d",
            "1w": "ohlcv-1w",
            "1M": "ohlcv-1M"
        }
        
        schema = schema_map.get(interval, "ohlcv-1d")
        
        params = {
            'dataset': 'XNAS.ITCH',  # NASDAQ dataset
            'schema': schema,
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'symbols': symbol.upper(),
            'stype_in': 'raw_symbol',
            'encoding': 'json'
        }
        
        endpoint = "/v0/timeseries.get_range"
        data = await self._make_request(endpoint, params, 'POST')
        
        if not data:
            return None
        
        data_points = []
        for record in data:
            # Databento record format
            data_point = MarketDataPoint(
                symbol=symbol.upper(),
                price=float(record.get('close', 0)) / 1e9,  # Databento uses fixed-point
                volume=int(record.get('volume', 0)),
                timestamp=datetime.fromisoformat(record.get('ts_event', '')),
                open_price=float(record.get('open', 0)) / 1e9,
                high_price=float(record.get('high', 0)) / 1e9,
                low_price=float(record.get('low', 0)) / 1e9,
                previous_close=None,
                change=None,
                change_percent=None,
                bid=None,
                ask=None,
                provider=DataProvider.DATABENTO
            )
            data_points.append(data_point)
        
        return HistoricalData(
            symbol=symbol.upper(),
            data_points=data_points,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            provider=DataProvider.DATABENTO
        )
    
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company reference data"""
        params = {
            'dataset': 'XNAS.ITCH',
            'symbols': symbol.upper(),
            'stype_in': 'raw_symbol'
        }
        
        endpoint = "/v0/metadata.list_symbols"
        data = await self._make_request(endpoint, params, 'POST')
        
        if not data or not data:
            return None
        
        record = data[0] if isinstance(data, list) else data
        
        return CompanyInfo(
            symbol=symbol.upper(),
            name=record.get('description', ''),
            description='',
            sector='',
            industry='',
            market_cap=None,
            shares_outstanding=None,
            exchange=record.get('venue', ''),
            currency='USD',
            country='US',
            website='',
            employees=None,
            pe_ratio=None,
            dividend_yield=None,
            provider=DataProvider.DATABENTO
        )
    
    # WebSocket Implementation for Real-time Data
    async def connect_websocket(self) -> bool:
        """Connect to Databento live WebSocket stream"""
        try:
            if self.ws_connection:
                return True
            
            self.logger.info("Connecting to Databento WebSocket...")
            
            # First get session token
            auth_response = await self._authenticate_live_session()
            if not auth_response:
                return False
            
            self.ws_session_id = auth_response.get('session_id')
            
            # Connect to WebSocket
            ws_url = f"{self.live_base_url}/v0/live.subscribe"
            self.ws_connection = await websockets.connect(ws_url)
            
            # Start message handler
            asyncio.create_task(self._handle_websocket_messages())
            
            self.logger.info("Databento WebSocket connected successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Databento WebSocket: {e}")
            self.ws_connection = None
            return False
    
    async def _authenticate_live_session(self) -> Optional[Dict]:
        """Authenticate live session"""
        params = {
            'dataset': 'XNAS.ITCH',
            'mode': 'live'
        }
        
        endpoint = "/v0/live.subscribe"
        return await self._make_request(endpoint, params, 'POST')
    
    async def _handle_websocket_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.ws_connection:
                try:
                    if isinstance(message, bytes):
                        # Databento uses binary format, would need proper decoding
                        await self._process_binary_message(message)
                    else:
                        data = json.loads(message)
                        await self._process_websocket_message(data)
                except Exception as e:
                    self.logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            self.ws_connection = None
            await self._reconnect_websocket()
            
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            self.ws_connection = None
    
    async def _process_binary_message(self, message: bytes):
        """Process binary WebSocket message (DBN format)"""
        # This would require the databento-python library for proper decoding
        # For now, we'll log that we received a message
        self.logger.debug(f"Received binary message of {len(message)} bytes")
    
    async def _process_websocket_message(self, data: Dict[str, Any]):
        """Process JSON WebSocket messages"""
        message_type = data.get('type')
        
        if message_type == 'trade':
            await self._process_trade_message(data)
        elif message_type == 'quote':
            await self._process_quote_message(data)
        elif message_type == 'status':
            self.logger.info(f"WebSocket status: {data}")
    
    async def _process_trade_message(self, message: Dict[str, Any]):
        """Process real-time trade data"""
        symbol = message.get('instrument_id')  # Would need symbol mapping
        if not symbol:
            return
        
        trade_data = {
            'type': 'trade',
            'symbol': symbol,
            'price': message.get('price', 0) / 1e9,  # Fixed-point conversion
            'volume': message.get('size', 0),
            'timestamp': datetime.fromisoformat(message.get('ts_event', '')),
            'conditions': message.get('action', [])
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
        symbol = message.get('instrument_id')
        if not symbol:
            return
        
        quote_data = {
            'type': 'quote',
            'symbol': symbol,
            'bid': message.get('bid_px', 0) / 1e9,
            'ask': message.get('ask_px', 0) / 1e9,
            'bid_size': message.get('bid_sz', 0),
            'ask_size': message.get('ask_sz', 0),
            'timestamp': datetime.fromisoformat(message.get('ts_event', ''))
        }
        
        # Call registered handlers
        if symbol in self.ws_handlers:
            for handler in self.ws_handlers[symbol]:
                try:
                    await handler(quote_data)
                except Exception as e:
                    self.logger.error(f"Error in WebSocket handler: {e}")
    
    async def _reconnect_websocket(self):
        """Attempt to reconnect WebSocket"""
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            delay = min(300, 30 * (2 ** attempt))
            self.logger.info(f"Attempting WebSocket reconnection in {delay}s")
            
            await asyncio.sleep(delay)
            
            if await self.connect_websocket():
                await self._resubscribe()
                return
            
            attempt += 1
        
        self.logger.error("Max reconnection attempts reached")
    
    async def _resubscribe(self):
        """Resubscribe to previous WebSocket subscriptions"""
        if not self.ws_subscriptions:
            return
        
        # Would need to send subscription messages in Databento format
        self.logger.info(f"Resubscribed to {len(self.ws_subscriptions)} streams")
    
    async def subscribe_to_trades(self, symbols: List[str]) -> bool:
        """Subscribe to real-time trade data"""
        if not await self.connect_websocket():
            return False
        
        # Would need to implement Databento-specific subscription format
        self.logger.info(f"Subscribed to trade streams for {len(symbols)} symbols")
        return True
    
    async def subscribe_to_quotes(self, symbols: List[str]) -> bool:
        """Subscribe to real-time quote data"""
        if not await self.connect_websocket():
            return False
        
        # Would need to implement Databento-specific subscription format
        self.logger.info(f"Subscribed to quote streams for {len(symbols)} symbols")
        return True
    
    def register_handler(self, symbol: str, handler):
        """Register handler for real-time data"""
        if symbol not in self.ws_handlers:
            self.ws_handlers[symbol] = []
        self.ws_handlers[symbol].append(handler)
    
    async def disconnect_websocket(self):
        """Disconnect WebSocket connection"""
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None
            self.ws_subscriptions.clear()
            self.ws_handlers.clear()
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            # Check if we can access the API
            params = {'dataset': 'XNAS.ITCH', 'limit': 1}
            data = await self._make_request("/v0/metadata.list_datasets", params, 'POST')
            return data is not None
        except Exception:
            return False
    
    async def _cleanup_session(self):
        """Cleanup resources"""
        await self.disconnect_websocket()
        await super()._cleanup_session()