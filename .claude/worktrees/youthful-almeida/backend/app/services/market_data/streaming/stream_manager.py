"""
Stream Manager

Manages real-time data streaming from various providers to WebSocket clients.
"""

import asyncio
import logging
from typing import Dict, Set, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .websocket_server import WebSocketServer
from ..providers import BaseProvider
from ..models import MarketDataPoint, WebSocketMessage, DataProvider
from ..config import config


class StreamManager:
    """Manages real-time market data streaming"""
    
    def __init__(self, providers: Dict[DataProvider, BaseProvider]):
        self.providers = providers
        self.websocket_server = WebSocketServer()
        self.logger = logging.getLogger("market_data.stream_manager")
        
        # Streaming state
        self._streaming = False
        self._stream_tasks: Dict[str, asyncio.Task] = {}
        
        # Symbol management
        self.active_symbols: Set[str] = set()
        self.symbol_last_update: Dict[str, datetime] = {}
        self.symbol_update_counts: Dict[str, int] = defaultdict(int)
        
        # Performance tracking
        self.update_latencies: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
    
    async def start(self, host: str = None, port: int = None):
        """Start the stream manager and WebSocket server"""
        self.logger.info("Starting stream manager")
        
        # Start WebSocket server
        self.websocket_server_task = asyncio.create_task(
            self.websocket_server.start_server(host, port)
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(1)
        
        # Start streaming
        self._streaming = True
        
        # Start monitoring task
        self.monitor_task = asyncio.create_task(self._monitor_subscriptions())
        
        self.logger.info("Stream manager started")
    
    async def stop(self):
        """Stop the stream manager"""
        self.logger.info("Stopping stream manager")
        
        self._streaming = False
        
        # Cancel all streaming tasks
        for task in self._stream_tasks.values():
            task.cancel()
        
        if self._stream_tasks:
            await asyncio.gather(*self._stream_tasks.values(), return_exceptions=True)
        
        # Cancel monitoring task
        if hasattr(self, 'monitor_task'):
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop WebSocket server
        await self.websocket_server.stop_server()
        
        # Cancel server task
        if hasattr(self, 'websocket_server_task'):
            self.websocket_server_task.cancel()
            try:
                await self.websocket_server_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stream manager stopped")
    
    async def _monitor_subscriptions(self):
        """Monitor client subscriptions and manage symbol streams"""
        while self._streaming:
            try:
                # Get current subscribed symbols from WebSocket server
                current_symbols = set(self.websocket_server.symbol_subscribers.keys())
                
                # Start streaming for new symbols
                new_symbols = current_symbols - self.active_symbols
                for symbol in new_symbols:
                    await self._start_symbol_stream(symbol)
                
                # Stop streaming for unsubscribed symbols
                removed_symbols = self.active_symbols - current_symbols
                for symbol in removed_symbols:
                    await self._stop_symbol_stream(symbol)
                
                # Update active symbols
                self.active_symbols = current_symbols
                
                # Sleep before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in subscription monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _start_symbol_stream(self, symbol: str):
        """Start streaming for a symbol"""
        if symbol in self._stream_tasks:
            return
        
        self.logger.info(f"Starting stream for symbol: {symbol}")
        
        task = asyncio.create_task(self._stream_symbol_data(symbol))
        self._stream_tasks[symbol] = task
    
    async def _stop_symbol_stream(self, symbol: str):
        """Stop streaming for a symbol"""
        if symbol not in self._stream_tasks:
            return
        
        self.logger.info(f"Stopping stream for symbol: {symbol}")
        
        task = self._stream_tasks[symbol]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self._stream_tasks[symbol]
        
        # Clean up tracking data
        if symbol in self.symbol_last_update:
            del self.symbol_last_update[symbol]
        if symbol in self.symbol_update_counts:
            del self.symbol_update_counts[symbol]
    
    async def _stream_symbol_data(self, symbol: str):
        """Stream real-time data for a symbol"""
        update_interval = config.real_time_update_interval
        
        while self._streaming and symbol in self.active_symbols:
            try:
                start_time = datetime.utcnow()
                
                # Get quote from primary provider
                quote = await self._get_quote_with_fallback(symbol)
                
                if quote:
                    # Calculate latency
                    latency = (datetime.utcnow() - start_time).total_seconds()
                    self.update_latencies[symbol].append(latency)
                    
                    # Keep only recent latency measurements
                    if len(self.update_latencies[symbol]) > 100:
                        self.update_latencies[symbol] = self.update_latencies[symbol][-50:]
                    
                    # Update tracking
                    self.symbol_last_update[symbol] = datetime.utcnow()
                    self.symbol_update_counts[symbol] += 1
                    
                    # Broadcast to WebSocket clients
                    await self.websocket_server.broadcast_market_data(quote)
                    
                    self.logger.debug(f"Streamed data for {symbol} (latency: {latency:.3f}s)")
                
                else:
                    self.error_counts[symbol] += 1
                    self.logger.warning(f"Failed to get quote for {symbol}")
                
                # Wait for next update
                await asyncio.sleep(update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_counts[symbol] += 1
                self.logger.error(f"Error streaming data for {symbol}: {e}")
                await asyncio.sleep(update_interval)
    
    async def _get_quote_with_fallback(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get quote with provider fallback"""
        # Try primary provider first
        primary_provider = self.providers.get(config.primary_provider)
        if primary_provider:
            try:
                quote = await primary_provider.get_quote(symbol)
                if quote:
                    return quote
            except Exception as e:
                self.logger.warning(f"Primary provider failed for {symbol}: {e}")
        
        # Try fallback providers
        for provider_type in config.fallback_providers:
            provider = self.providers.get(provider_type)
            if not provider:
                continue
            
            try:
                quote = await provider.get_quote(symbol)
                if quote:
                    self.logger.info(f"Used fallback provider {provider_type} for {symbol}")
                    return quote
            except Exception as e:
                self.logger.warning(f"Fallback provider {provider_type} failed for {symbol}: {e}")
        
        return None
    
    async def broadcast_market_status(self, status: Dict[str, Any]):
        """Broadcast market status to all clients"""
        message = WebSocketMessage(
            type="market_status",
            data=status
        )
        await self.websocket_server.broadcast_to_all(message)
    
    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcast alert to relevant clients"""
        message = WebSocketMessage(
            type="alert",
            data=alert_data
        )
        await self.websocket_server.broadcast_to_all(message)
    
    async def broadcast_news(self, news_data: Dict[str, Any]):
        """Broadcast news to relevant clients"""
        message = WebSocketMessage(
            type="news",
            data=news_data
        )
        await self.websocket_server.broadcast_to_all(message)
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        total_updates = sum(self.symbol_update_counts.values())
        total_errors = sum(self.error_counts.values())
        
        # Calculate average latencies
        avg_latencies = {}
        for symbol, latencies in self.update_latencies.items():
            if latencies:
                avg_latencies[symbol] = sum(latencies) / len(latencies)
        
        # Get symbol status
        symbol_status = {}
        for symbol in self.active_symbols:
            last_update = self.symbol_last_update.get(symbol)
            symbol_status[symbol] = {
                "last_update": last_update.isoformat() if last_update else None,
                "update_count": self.symbol_update_counts.get(symbol, 0),
                "error_count": self.error_counts.get(symbol, 0),
                "avg_latency": avg_latencies.get(symbol),
                "is_active": symbol in self._stream_tasks
            }
        
        return {
            "streaming": self._streaming,
            "active_symbols": list(self.active_symbols),
            "active_symbol_count": len(self.active_symbols),
            "total_updates": total_updates,
            "total_errors": total_errors,
            "error_rate": total_errors / total_updates if total_updates > 0 else 0,
            "symbol_status": symbol_status,
            "websocket_stats": self.websocket_server.get_stats(),
            "client_info": self.websocket_server.get_client_info()
        }
    
    async def add_symbols(self, symbols: List[str]):
        """Manually add symbols to stream"""
        for symbol in symbols:
            symbol = symbol.upper().strip()
            if symbol not in self.active_symbols:
                self.active_symbols.add(symbol)
                await self._start_symbol_stream(symbol)
    
    async def remove_symbols(self, symbols: List[str]):
        """Manually remove symbols from stream"""
        for symbol in symbols:
            symbol = symbol.upper().strip()
            if symbol in self.active_symbols:
                self.active_symbols.remove(symbol)
                await self._stop_symbol_stream(symbol)
    
    async def restart_symbol_stream(self, symbol: str):
        """Restart streaming for a specific symbol"""
        await self._stop_symbol_stream(symbol)
        await asyncio.sleep(1)
        await self._start_symbol_stream(symbol)
    
    def get_symbol_performance(self, symbol: str) -> Dict[str, Any]:
        """Get performance metrics for a specific symbol"""
        latencies = self.update_latencies.get(symbol, [])
        
        performance = {
            "symbol": symbol,
            "is_active": symbol in self.active_symbols,
            "last_update": self.symbol_last_update.get(symbol),
            "update_count": self.symbol_update_counts.get(symbol, 0),
            "error_count": self.error_counts.get(symbol, 0),
            "latency_stats": {}
        }
        
        if latencies:
            performance["latency_stats"] = {
                "min": min(latencies),
                "max": max(latencies),
                "avg": sum(latencies) / len(latencies),
                "count": len(latencies)
            }
        
        return performance