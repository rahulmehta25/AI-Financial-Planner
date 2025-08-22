"""
Yahoo Finance Provider

Market data provider integration for Yahoo Finance API.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal
import asyncio
import aiohttp
import json
import logging

from .base import BaseProvider
from ..models import MarketDataPoint, MarketDataType, DataProvider, HistoricalData, CompanyInfo
from ..config import config, get_provider_config


class YahooFinanceProvider(BaseProvider):
    """Yahoo Finance market data provider"""
    
    def __init__(self):
        provider_config = get_provider_config(DataProvider.YAHOO_FINANCE)
        super().__init__(
            DataProvider.YAHOO_FINANCE, 
            provider_config.get('rate_limit', 2000)
        )
        self.base_url = provider_config.get('base_url')
        self.quote_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        self.search_url = "https://query1.finance.yahoo.com/v1/finance/search"
        self.summary_url = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/"
    
    async def _initialize_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=config.request_timeout)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
    
    async def _cleanup_session(self):
        """Cleanup HTTP session"""
        if self._session:
            await self._session.close()
    
    async def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make API request to Yahoo Finance"""
        await self.rate_limiter.wait_if_needed()
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    self.logger.error(f"HTTP error {response.status}: {await response.text()}")
                    return None
        
        except asyncio.TimeoutError:
            self.logger.error("Request timeout")
            return None
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    async def get_quote(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get current quote for a symbol"""
        url = f"{self.quote_url}{symbol}"
        params = {
            'interval': '1m',
            'range': '1d',
            'includePrePost': 'true'
        }
        
        data = await self._make_request(url, params)
        if not data or 'chart' not in data:
            return None
        
        chart = data['chart']
        if not chart.get('result') or len(chart['result']) == 0:
            return None
        
        result = chart['result'][0]
        meta = result.get('meta', {})
        
        try:
            # Get current price from meta
            current_price = Decimal(str(meta.get('regularMarketPrice', 0)))
            previous_close = Decimal(str(meta.get('previousClose', 0)))
            
            # Calculate price change
            price_change = current_price - previous_close if previous_close else Decimal('0')
            price_change_percent = (price_change / previous_close * 100) if previous_close else Decimal('0')
            
            # Get today's OHLV data
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {})
            quote_data = indicators.get('quote', [{}])[0] if indicators.get('quote') else {}
            
            open_price = None
            high_price = None
            low_price = None
            volume = None
            
            if timestamps and quote_data:
                # Get latest available data point
                opens = quote_data.get('open', [])
                highs = quote_data.get('high', [])
                lows = quote_data.get('low', [])
                volumes = quote_data.get('volume', [])
                
                # Find the most recent non-null values
                for i in reversed(range(len(timestamps))):
                    if opens and i < len(opens) and opens[i] is not None:
                        open_price = Decimal(str(opens[i]))
                        break
                
                for i in reversed(range(len(timestamps))):
                    if highs and i < len(highs) and highs[i] is not None:
                        high_price = Decimal(str(highs[i]))
                        break
                
                for i in reversed(range(len(timestamps))):
                    if lows and i < len(lows) and lows[i] is not None:
                        low_price = Decimal(str(lows[i]))
                        break
                
                for i in reversed(range(len(timestamps))):
                    if volumes and i < len(volumes) and volumes[i] is not None:
                        volume = int(volumes[i])
                        break
            
            # Use meta data as fallback
            if not open_price and meta.get('regularMarketOpen'):
                open_price = Decimal(str(meta['regularMarketOpen']))
            if not high_price and meta.get('regularMarketDayHigh'):
                high_price = Decimal(str(meta['regularMarketDayHigh']))
            if not low_price and meta.get('regularMarketDayLow'):
                low_price = Decimal(str(meta['regularMarketDayLow']))
            if not volume and meta.get('regularMarketVolume'):
                volume = int(meta['regularMarketVolume'])
            
            # Get market cap if available
            market_cap = None
            if meta.get('marketCap'):
                market_cap = Decimal(str(meta['marketCap']))
            
            return MarketDataPoint(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=previous_close,
                current_price=current_price,
                volume=volume,
                market_cap=market_cap,
                price_change=price_change,
                price_change_percent=price_change_percent,
                data_type=MarketDataType.QUOTE,
                provider=DataProvider.YAHOO_FINANCE,
                is_real_time=True,
                additional_data={
                    'exchange': meta.get('exchangeName'),
                    'currency': meta.get('currency'),
                    'timezone': meta.get('timezone'),
                    'raw_meta': meta
                }
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing quote data for {symbol}: {e}")
            return None
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        interval: str = "1d"
    ) -> Optional[HistoricalData]:
        """Get historical data for a symbol"""
        
        # Convert dates to timestamps
        start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        
        # Map interval to Yahoo Finance format
        yahoo_interval = interval
        if interval == 'daily':
            yahoo_interval = '1d'
        elif interval == 'weekly':
            yahoo_interval = '1wk'
        elif interval == 'monthly':
            yahoo_interval = '1mo'
        
        url = f"{self.quote_url}{symbol}"
        params = {
            'period1': start_timestamp,
            'period2': end_timestamp,
            'interval': yahoo_interval,
            'includeAdjustedClose': 'true'
        }
        
        data = await self._make_request(url, params)
        if not data or 'chart' not in data:
            return None
        
        chart = data['chart']
        if not chart.get('result') or len(chart['result']) == 0:
            return None
        
        result = chart['result'][0]
        timestamps = result.get('timestamp', [])
        indicators = result.get('indicators', {})
        quote_data = indicators.get('quote', [{}])[0] if indicators.get('quote') else {}
        
        if not timestamps:
            return None
        
        data_points = []
        
        try:
            opens = quote_data.get('open', [])
            highs = quote_data.get('high', [])
            lows = quote_data.get('low', [])
            closes = quote_data.get('close', [])
            volumes = quote_data.get('volume', [])
            
            for i, timestamp in enumerate(timestamps):
                # Skip if any required data is missing
                if (i >= len(opens) or opens[i] is None or
                    i >= len(highs) or highs[i] is None or
                    i >= len(lows) or lows[i] is None or
                    i >= len(closes) or closes[i] is None):
                    continue
                
                data_datetime = datetime.fromtimestamp(timestamp)
                
                open_price = Decimal(str(opens[i]))
                high_price = Decimal(str(highs[i]))
                low_price = Decimal(str(lows[i]))
                close_price = Decimal(str(closes[i]))
                volume = int(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0
                
                point = MarketDataPoint(
                    symbol=symbol,
                    timestamp=data_datetime,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    current_price=close_price,
                    volume=volume,
                    data_type=MarketDataType.HISTORICAL,
                    provider=DataProvider.YAHOO_FINANCE,
                    is_real_time=False
                )
                data_points.append(point)
            
            return HistoricalData(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                data_points=data_points,
                provider=DataProvider.YAHOO_FINANCE
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing historical data for {symbol}: {e}")
            return None
    
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company information for a symbol"""
        url = f"{self.summary_url}{symbol}"
        params = {
            'modules': 'assetProfile,summaryProfile,price,defaultKeyStatistics'
        }
        
        data = await self._make_request(url, params)
        if not data or 'quoteSummary' not in data:
            return None
        
        quote_summary = data['quoteSummary']
        if not quote_summary.get('result') or len(quote_summary['result']) == 0:
            return None
        
        result = quote_summary['result'][0]
        
        try:
            asset_profile = result.get('assetProfile', {})
            summary_profile = result.get('summaryProfile', {})
            price_info = result.get('price', {})
            key_stats = result.get('defaultKeyStatistics', {})
            
            # Get market cap
            market_cap = None
            if price_info.get('marketCap') and price_info['marketCap'].get('raw'):
                market_cap = Decimal(str(price_info['marketCap']['raw']))
            
            # Get employees count
            employees = None
            if asset_profile.get('fullTimeEmployees'):
                employees = int(asset_profile['fullTimeEmployees'])
            
            return CompanyInfo(
                symbol=symbol,
                name=price_info.get('longName') or price_info.get('shortName', ''),
                sector=asset_profile.get('sector') or summary_profile.get('sector'),
                industry=asset_profile.get('industry') or summary_profile.get('industry'),
                description=asset_profile.get('longBusinessSummary') or summary_profile.get('longBusinessSummary'),
                website=asset_profile.get('website'),
                market_cap=market_cap,
                employees=employees,
                exchange=price_info.get('exchangeName'),
                country=asset_profile.get('country'),
                provider=DataProvider.YAHOO_FINANCE,
                last_updated=datetime.utcnow()
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing company info for {symbol}: {e}")
            return None
    
    async def search_symbols(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Search for symbols by query"""
        params = {
            'q': query,
            'quotesCount': 10,
            'newsCount': 0
        }
        
        data = await self._make_request(self.search_url, params)
        if not data or 'quotes' not in data:
            return None
        
        return data['quotes']
    
    async def get_multiple_quotes(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get quotes for multiple symbols efficiently"""
        # Yahoo Finance allows batch requests
        if len(symbols) <= 10:
            return await self._get_batch_quotes(symbols)
        else:
            # Split into batches and process
            quotes = []
            for i in range(0, len(symbols), 10):
                batch = symbols[i:i+10]
                batch_quotes = await self._get_batch_quotes(batch)
                quotes.extend(batch_quotes)
            return quotes
    
    async def _get_batch_quotes(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get quotes for a batch of symbols"""
        symbol_string = ','.join(symbols)
        url = f"{self.quote_url}{symbol_string}"
        params = {
            'interval': '1m',
            'range': '1d'
        }
        
        data = await self._make_request(url, params)
        if not data or 'chart' not in data:
            return []
        
        chart = data['chart']
        if not chart.get('result'):
            return []
        
        quotes = []
        for result in chart['result']:
            meta = result.get('meta', {})
            symbol = meta.get('symbol')
            
            if not symbol:
                continue
            
            try:
                quote = await self._parse_quote_from_result(result)
                if quote:
                    quotes.append(quote)
            except Exception as e:
                self.logger.error(f"Error parsing batch quote for {symbol}: {e}")
        
        return quotes
    
    async def _parse_quote_from_result(self, result: Dict[str, Any]) -> Optional[MarketDataPoint]:
        """Parse quote data from Yahoo Finance result"""
        meta = result.get('meta', {})
        symbol = meta.get('symbol')
        
        if not symbol:
            return None
        
        try:
            current_price = Decimal(str(meta.get('regularMarketPrice', 0)))
            previous_close = Decimal(str(meta.get('previousClose', 0)))
            
            price_change = current_price - previous_close if previous_close else Decimal('0')
            price_change_percent = (price_change / previous_close * 100) if previous_close else Decimal('0')
            
            return MarketDataPoint(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                open_price=Decimal(str(meta.get('regularMarketOpen', 0))) or None,
                high_price=Decimal(str(meta.get('regularMarketDayHigh', 0))) or None,
                low_price=Decimal(str(meta.get('regularMarketDayLow', 0))) or None,
                close_price=previous_close,
                current_price=current_price,
                volume=int(meta.get('regularMarketVolume', 0)) or None,
                price_change=price_change,
                price_change_percent=price_change_percent,
                data_type=MarketDataType.QUOTE,
                provider=DataProvider.YAHOO_FINANCE,
                is_real_time=True,
                additional_data=meta
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing quote result for {symbol}: {e}")
            return None