"""
Enhanced Market Data Service for AI Financial Planning
Provides historical stock trends, S&P 500 integration, and technical analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

# Technical analysis imports
import talib
import yfinance as yf

from app.core.config import settings
from app.database.models import User
from app.services.market_data.manager import MarketDataManager
from app.services.market_data.models import (
    MarketDataPoint, HistoricalData, DataProvider, MarketDataType
)
from app.services.market_data_cache import MarketDataCache


class TechnicalIndicators:
    """Technical analysis indicators calculator"""
    
    @staticmethod
    def calculate_sma(prices: List[float], window: int = 20) -> List[Optional[float]]:
        """Calculate Simple Moving Average"""
        if len(prices) < window:
            return [None] * len(prices)
        
        prices_array = np.array(prices, dtype=float)
        sma = talib.SMA(prices_array, timeperiod=window)
        return [None if np.isnan(x) else float(x) for x in sma]
    
    @staticmethod
    def calculate_ema(prices: List[float], window: int = 20) -> List[Optional[float]]:
        """Calculate Exponential Moving Average"""
        if len(prices) < window:
            return [None] * len(prices)
        
        prices_array = np.array(prices, dtype=float)
        ema = talib.EMA(prices_array, timeperiod=window)
        return [None if np.isnan(x) else float(x) for x in ema]
    
    @staticmethod
    def calculate_rsi(prices: List[float], window: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index"""
        if len(prices) < window + 1:
            return [None] * len(prices)
        
        prices_array = np.array(prices, dtype=float)
        rsi = talib.RSI(prices_array, timeperiod=window)
        return [None if np.isnan(x) else float(x) for x in rsi]
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[Optional[float]]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal:
            return {
                'macd': [None] * len(prices),
                'signal': [None] * len(prices),
                'histogram': [None] * len(prices)
            }
        
        prices_array = np.array(prices, dtype=float)
        macd, macd_signal, macd_hist = talib.MACD(prices_array, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        
        return {
            'macd': [None if np.isnan(x) else float(x) for x in macd],
            'signal': [None if np.isnan(x) else float(x) for x in macd_signal],
            'histogram': [None if np.isnan(x) else float(x) for x in macd_hist]
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], window: int = 20, num_std: float = 2) -> Dict[str, List[Optional[float]]]:
        """Calculate Bollinger Bands"""
        if len(prices) < window:
            return {
                'upper': [None] * len(prices),
                'middle': [None] * len(prices),
                'lower': [None] * len(prices)
            }
        
        prices_array = np.array(prices, dtype=float)
        upper, middle, lower = talib.BBANDS(prices_array, timeperiod=window, nbdevup=num_std, nbdevdn=num_std)
        
        return {
            'upper': [None if np.isnan(x) else float(x) for x in upper],
            'middle': [None if np.isnan(x) else float(x) for x in middle],
            'lower': [None if np.isnan(x) else float(x) for x in lower]
        }
    
    @staticmethod
    def calculate_volume_sma(volumes: List[int], window: int = 20) -> List[Optional[float]]:
        """Calculate Volume Simple Moving Average"""
        if len(volumes) < window:
            return [None] * len(volumes)
        
        volumes_array = np.array(volumes, dtype=float)
        volume_sma = talib.SMA(volumes_array, timeperiod=window)
        return [None if np.isnan(x) else float(x) for x in volume_sma]


class MarketDataService:
    """Enhanced Market Data Service with S&P 500 integration and technical analysis"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger("market_data_service")
        self._market_manager = None
        self.sp500_symbol = "^GSPC"  # S&P 500 symbol
        
        # Initialize caching service
        self.cache = MarketDataCache()
        self._cache_initialized = False
        
        # Technical indicators calculator
        self.indicators = TechnicalIndicators()
    
    async def _get_market_manager(self) -> MarketDataManager:
        """Get or initialize market data manager"""
        if not self._market_manager:
            self._market_manager = MarketDataManager()
            await self._market_manager.initialize()
        return self._market_manager
    
    async def _ensure_cache_initialized(self):
        """Ensure cache is initialized"""
        if not self._cache_initialized:
            await self.cache.initialize()
            self._cache_initialized = True
    
    async def get_current_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current quote for a symbol with caching"""
        try:
            await self._ensure_cache_initialized()
            
            # Try cache first
            cached_quote = await self.cache.get_cached_quote(symbol)
            if cached_quote:
                return cached_quote
            
            # Fetch fresh data
            manager = await self._get_market_manager()
            quote = await manager.get_quote(symbol)
            
            if quote:
                quote_data = {
                    "symbol": quote.symbol,
                    "current_price": float(quote.current_price) if quote.current_price else None,
                    "open_price": float(quote.open_price) if quote.open_price else None,
                    "high_price": float(quote.high_price) if quote.high_price else None,
                    "low_price": float(quote.low_price) if quote.low_price else None,
                    "close_price": float(quote.close_price) if quote.close_price else None,
                    "volume": quote.volume,
                    "price_change": float(quote.price_change) if quote.price_change else None,
                    "price_change_percent": float(quote.price_change_percent) if quote.price_change_percent else None,
                    "timestamp": quote.timestamp.isoformat(),
                    "provider": quote.provider.value
                }
                
                # Cache the quote
                await self.cache.cache_quote(symbol, quote_data)
                return quote_data
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[Dict[str, Any]]:
        """Get historical data with flexible period support and caching"""
        try:
            await self._ensure_cache_initialized()
            
            # Handle period-based requests
            if not start_date and not end_date:
                end_date = date.today()
                
                period_mapping = {
                    "1D": 1,
                    "1W": 7,
                    "1M": 30,
                    "3M": 90,
                    "1Y": 365,
                    "5Y": 1825,
                    "MAX": 7300  # ~20 years
                }
                
                period_upper = period.upper()
                if period_upper in period_mapping:
                    start_date = end_date - timedelta(days=period_mapping[period_upper])
                else:
                    start_date = end_date - timedelta(days=365)  # Default 1 year
            
            # Check cache first
            start_date_str = start_date.isoformat() if start_date else ""
            end_date_str = end_date.isoformat() if end_date else ""
            
            cached_data = await self.cache.get_cached_historical_data(
                symbol, start_date_str, end_date_str, interval
            )
            if cached_data:
                return cached_data
            
            # Use yfinance directly for historical data to get more comprehensive data
            ticker = yf.Ticker(symbol)
            
            # Convert interval mapping
            yf_interval = interval
            if interval == "daily":
                yf_interval = "1d"
            elif interval == "weekly":
                yf_interval = "1wk"
            elif interval == "monthly":
                yf_interval = "1mo"
            
            # Get historical data
            hist_data = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_interval,
                auto_adjust=True,
                prepost=True
            )
            
            if hist_data.empty:
                return None
            
            # Convert to our format
            data_points = []
            for idx, row in hist_data.iterrows():
                data_points.append({
                    "date": idx.date().isoformat() if hasattr(idx, 'date') else str(idx)[:10],
                    "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    "open": float(row['Open']) if not np.isnan(row['Open']) else None,
                    "high": float(row['High']) if not np.isnan(row['High']) else None,
                    "low": float(row['Low']) if not np.isnan(row['Low']) else None,
                    "close": float(row['Close']) if not np.isnan(row['Close']) else None,
                    "volume": int(row['Volume']) if not np.isnan(row['Volume']) else 0
                })
            
            historical_data = {
                "symbol": symbol,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "interval": interval,
                "data_points": data_points,
                "provider": "yahoo_finance"
            }
            
            # Cache the historical data
            await self.cache.cache_historical_data(
                symbol, start_date_str, end_date_str, interval, historical_data
            )
            
            return historical_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    async def get_sp500_data(
        self, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "1y"
    ) -> Optional[Dict[str, Any]]:
        """Get S&P 500 historical data for benchmarking with caching"""
        try:
            await self._ensure_cache_initialized()
            
            # Check cache first
            cached_data = await self.cache.get_cached_sp500_data(period)
            if cached_data:
                return cached_data
            
            # Fetch S&P 500 data
            sp500_data = await self.get_historical_data(
                self.sp500_symbol,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            
            if sp500_data:
                # Cache the result
                await self.cache.cache_sp500_data(period, sp500_data)
            
            return sp500_data
            
        except Exception as e:
            self.logger.error(f"Error getting S&P 500 data: {e}")
            return None
    
    async def get_historical_with_sp500_comparison(
        self, 
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period: str = "1y"
    ) -> Optional[Dict[str, Any]]:
        """Get historical data with S&P 500 overlay for comparison"""
        try:
            # Get both stock and S&P 500 data
            stock_data_task = self.get_historical_data(symbol, start_date, end_date, period)
            sp500_data_task = self.get_sp500_data(start_date, end_date, period)
            
            stock_data, sp500_data = await asyncio.gather(stock_data_task, sp500_data_task)
            
            if not stock_data or not sp500_data:
                return stock_data  # Return at least stock data if available
            
            # Normalize both datasets to percentage change for comparison
            stock_prices = [point["close"] for point in stock_data["data_points"] if point["close"]]
            sp500_prices = [point["close"] for point in sp500_data["data_points"] if point["close"]]
            
            if stock_prices and sp500_prices:
                # Calculate percentage changes from first price
                stock_base = stock_prices[0]
                sp500_base = sp500_prices[0]
                
                stock_pct_changes = [(price / stock_base - 1) * 100 for price in stock_prices]
                sp500_pct_changes = [(price / sp500_base - 1) * 100 for price in sp500_prices]
                
                # Add comparison data to response
                comparison_data = []
                min_len = min(len(stock_data["data_points"]), len(sp500_pct_changes))
                
                for i in range(min_len):
                    if i < len(stock_pct_changes):
                        comparison_data.append({
                            "date": stock_data["data_points"][i]["date"],
                            "stock_pct_change": stock_pct_changes[i],
                            "sp500_pct_change": sp500_pct_changes[i] if i < len(sp500_pct_changes) else None
                        })
                
                stock_data["sp500_comparison"] = {
                    "comparison_data": comparison_data,
                    "correlation": self._calculate_correlation(stock_pct_changes, sp500_pct_changes)
                }
            
            return stock_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical comparison for {symbol}: {e}")
            return await self.get_historical_data(symbol, start_date, end_date, period)
    
    def _calculate_correlation(self, series1: List[float], series2: List[float]) -> Optional[float]:
        """Calculate correlation between two price series"""
        try:
            if len(series1) != len(series2) or len(series1) < 2:
                return None
            
            correlation = np.corrcoef(series1, series2)[0, 1]
            return float(correlation) if not np.isnan(correlation) else None
            
        except Exception:
            return None
    
    async def get_technical_analysis(
        self, 
        symbol: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive technical analysis for a symbol with caching"""
        try:
            await self._ensure_cache_initialized()
            
            # Check cache first
            cached_analysis = await self.cache.get_cached_technical_analysis(
                symbol, period, interval
            )
            if cached_analysis:
                return cached_analysis
            
            # Get historical data
            historical_data = await self.get_historical_data(symbol, period=period, interval=interval)
            
            if not historical_data or not historical_data["data_points"]:
                return None
            
            data_points = historical_data["data_points"]
            
            # Extract price and volume arrays
            closes = [point["close"] for point in data_points if point["close"] is not None]
            opens = [point["open"] for point in data_points if point["open"] is not None]
            highs = [point["high"] for point in data_points if point["high"] is not None]
            lows = [point["low"] for point in data_points if point["low"] is not None]
            volumes = [point["volume"] for point in data_points if point["volume"] is not None]
            
            if not closes:
                return None
            
            # Calculate technical indicators
            analysis = {
                "symbol": symbol,
                "period": period,
                "last_updated": datetime.utcnow().isoformat(),
                "price_data": {
                    "current_price": closes[-1] if closes else None,
                    "price_change": closes[-1] - closes[-2] if len(closes) >= 2 else None,
                    "price_change_percent": ((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) >= 2 and closes[-2] != 0 else None
                },
                "moving_averages": {
                    "sma_20": self.indicators.calculate_sma(closes, 20)[-1] if closes else None,
                    "sma_50": self.indicators.calculate_sma(closes, 50)[-1] if closes else None,
                    "sma_200": self.indicators.calculate_sma(closes, 200)[-1] if closes else None,
                    "ema_12": self.indicators.calculate_ema(closes, 12)[-1] if closes else None,
                    "ema_26": self.indicators.calculate_ema(closes, 26)[-1] if closes else None
                },
                "momentum_indicators": {
                    "rsi": self.indicators.calculate_rsi(closes)[-1] if closes else None,
                    "macd": self.indicators.calculate_macd(closes) if closes else None
                },
                "volatility_indicators": {
                    "bollinger_bands": self.indicators.calculate_bollinger_bands(closes) if closes else None
                },
                "volume_analysis": {
                    "current_volume": volumes[-1] if volumes else None,
                    "avg_volume_20": self.indicators.calculate_volume_sma(volumes, 20)[-1] if volumes else None,
                    "volume_ratio": None
                }
            }
            
            # Calculate volume ratio
            if (analysis["volume_analysis"]["current_volume"] and 
                analysis["volume_analysis"]["avg_volume_20"] and
                analysis["volume_analysis"]["avg_volume_20"] != 0):
                analysis["volume_analysis"]["volume_ratio"] = (
                    analysis["volume_analysis"]["current_volume"] / 
                    analysis["volume_analysis"]["avg_volume_20"]
                )
            
            # Add trend analysis
            analysis["trend_analysis"] = self._analyze_trend(closes, analysis["moving_averages"])
            
            # Add detailed indicator arrays for charting
            analysis["detailed_indicators"] = {
                "sma_20_series": self.indicators.calculate_sma(closes, 20),
                "sma_50_series": self.indicators.calculate_sma(closes, 50),
                "ema_12_series": self.indicators.calculate_ema(closes, 12),
                "ema_26_series": self.indicators.calculate_ema(closes, 26),
                "rsi_series": self.indicators.calculate_rsi(closes),
                "macd_series": self.indicators.calculate_macd(closes),
                "bollinger_series": self.indicators.calculate_bollinger_bands(closes),
                "volume_sma_series": self.indicators.calculate_volume_sma(volumes, 20) if volumes else None
            }
            
            # Cache the analysis
            await self.cache.cache_technical_analysis(symbol, period, interval, analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error getting technical analysis for {symbol}: {e}")
            return None
    
    def _analyze_trend(self, prices: List[float], moving_averages: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze price trend based on moving averages and price action"""
        if len(prices) < 20:
            return {"trend": "insufficient_data", "strength": 0, "signals": []}
        
        current_price = prices[-1]
        sma_20 = moving_averages.get("sma_20")
        sma_50 = moving_averages.get("sma_50")
        sma_200 = moving_averages.get("sma_200")
        
        signals = []
        trend = "neutral"
        strength = 0
        
        # Price vs Moving Averages
        if sma_20 and current_price > sma_20:
            signals.append("Price above SMA 20")
            strength += 1
        elif sma_20 and current_price < sma_20:
            signals.append("Price below SMA 20")
            strength -= 1
        
        if sma_50 and current_price > sma_50:
            signals.append("Price above SMA 50")
            strength += 1
        elif sma_50 and current_price < sma_50:
            signals.append("Price below SMA 50")
            strength -= 1
        
        if sma_200 and current_price > sma_200:
            signals.append("Price above SMA 200 - Long-term uptrend")
            strength += 2
        elif sma_200 and current_price < sma_200:
            signals.append("Price below SMA 200 - Long-term downtrend")
            strength -= 2
        
        # Moving Average Crossovers
        if sma_20 and sma_50:
            if sma_20 > sma_50:
                signals.append("Golden Cross - SMA 20 above SMA 50")
                strength += 1
            else:
                signals.append("Death Cross - SMA 20 below SMA 50")
                strength -= 1
        
        # Determine trend
        if strength >= 3:
            trend = "strong_bullish"
        elif strength >= 1:
            trend = "bullish"
        elif strength <= -3:
            trend = "strong_bearish"
        elif strength <= -1:
            trend = "bearish"
        
        return {
            "trend": trend,
            "strength": strength,
            "signals": signals
        }
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for symbols"""
        try:
            manager = await self._get_market_manager()
            results = await manager.providers[DataProvider.YAHOO_FINANCE].search_symbols(query)
            
            if results:
                return results[:limit]
            return []
            
        except Exception as e:
            self.logger.error(f"Error searching symbols for {query}: {e}")
            return []
    
    async def get_sector_performance(self) -> List[Dict[str, Any]]:
        """Get sector performance data"""
        try:
            # Major sector ETFs for sector performance
            sector_etfs = {
                "Technology": "XLK",
                "Healthcare": "XLV",
                "Financial": "XLF",
                "Energy": "XLE",
                "Consumer Discretionary": "XLY",
                "Consumer Staples": "XLP",
                "Industrial": "XLI",
                "Materials": "XLB",
                "Real Estate": "XLRE",
                "Utilities": "XLU",
                "Communication": "XLC"
            }
            
            sector_performance = []
            
            for sector_name, etf_symbol in sector_etfs.items():
                try:
                    quote = await self.get_current_quote(etf_symbol)
                    if quote:
                        sector_performance.append({
                            "sector": sector_name,
                            "symbol": etf_symbol,
                            "price": quote["current_price"],
                            "change": quote["price_change"],
                            "change_percent": quote["price_change_percent"]
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to get data for sector {sector_name} ({etf_symbol}): {e}")
                    continue
            
            return sorted(sector_performance, key=lambda x: x.get("change_percent", 0), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting sector performance: {e}")
            return []
    
    async def get_market_indices(self) -> List[Dict[str, Any]]:
        """Get major market indices"""
        try:
            indices = {
                "S&P 500": "^GSPC",
                "Dow Jones": "^DJI",
                "NASDAQ": "^IXIC",
                "Russell 2000": "^RUT",
                "VIX": "^VIX"
            }
            
            index_data = []
            
            for index_name, symbol in indices.items():
                try:
                    quote = await self.get_current_quote(symbol)
                    if quote:
                        index_data.append({
                            "name": index_name,
                            "symbol": symbol,
                            "value": quote["current_price"],
                            "change": quote["price_change"],
                            "change_percent": quote["price_change_percent"],
                            "timestamp": quote["timestamp"]
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to get data for index {index_name} ({symbol}): {e}")
                    continue
            
            return index_data
            
        except Exception as e:
            self.logger.error(f"Error getting market indices: {e}")
            return []
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """Get key economic indicators"""
        # This would typically integrate with FRED API or similar
        # For now, return a structure that can be implemented
        return {
            "last_updated": datetime.utcnow().isoformat(),
            "indicators": [
                {
                    "name": "10-Year Treasury",
                    "symbol": "^TNX",
                    "value": None,
                    "change": None,
                    "description": "10-Year Treasury Bond Yield"
                },
                {
                    "name": "USD Index",
                    "symbol": "DX-Y.NYB",
                    "value": None,
                    "change": None,
                    "description": "US Dollar Index"
                }
            ]
        }
    
    async def add_to_watchlist(self, user_id: int, symbols: List[str]) -> Dict[str, Any]:
        """Add symbols to user watchlist (placeholder - would integrate with user data)"""
        return {
            "message": f"Added {len(symbols)} symbols to watchlist",
            "symbols": symbols,
            "user_id": user_id
        }
    
    async def get_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user watchlist (placeholder - would integrate with user data)"""
        return []
    
    async def remove_from_watchlist(self, user_id: int, symbol: str) -> bool:
        """Remove symbol from watchlist (placeholder - would integrate with user data)"""
        return True
    
    async def get_symbol_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return []
            
            formatted_news = []
            for article in news[:limit]:
                formatted_news.append({
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "url": article.get("link", ""),
                    "publisher": article.get("publisher", ""),
                    "published_at": datetime.fromtimestamp(article.get("providerPublishTime", 0)).isoformat() if article.get("providerPublishTime") else None,
                    "type": article.get("type", "news")
                })
            
            return formatted_news
            
        except Exception as e:
            self.logger.error(f"Error getting news for {symbol}: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self._market_manager:
                await self._market_manager.shutdown()
            
            if self._cache_initialized:
                await self.cache.shutdown()
                self._cache_initialized = False
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get caching statistics"""
        try:
            await self._ensure_cache_initialized()
            return await self.cache.get_cache_statistics()
        except Exception as e:
            self.logger.error(f"Error getting cache statistics: {e}")
            return {"status": "error", "error": str(e)}