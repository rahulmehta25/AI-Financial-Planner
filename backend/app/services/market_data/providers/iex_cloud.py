"""
IEX Cloud Provider

Market data provider integration for IEX Cloud API.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal
import asyncio
import aiohttp
import logging

from .base import BaseProvider
from ..models import MarketDataPoint, MarketDataType, DataProvider, HistoricalData, CompanyInfo
from ..config import config, get_provider_config


class IEXCloudProvider(BaseProvider):
    """IEX Cloud market data provider"""
    
    def __init__(self):
        provider_config = get_provider_config(DataProvider.IEX_CLOUD)
        super().__init__(
            DataProvider.IEX_CLOUD, 
            provider_config.get('rate_limit', 100)
        )
        self.api_key = provider_config.get('api_key')
        self.base_url = provider_config.get('base_url')
        
        if not self.api_key:
            self.logger.warning("IEX Cloud API key not configured")
    
    async def _initialize_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=config.request_timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def _cleanup_session(self):
        """Cleanup HTTP session"""
        if self._session:
            await self._session.close()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make API request to IEX Cloud"""
        if not self.api_key:
            self.logger.error("IEX Cloud API key not configured")
            return None
        
        await self.rate_limiter.wait_if_needed()
        
        if params is None:
            params = {}
        
        params['token'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    self.logger.warning("Rate limit exceeded")
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"HTTP error {response.status}: {error_text}")
                    return None
        
        except asyncio.TimeoutError:
            self.logger.error("Request timeout")
            return None
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    async def get_quote(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get current quote for a symbol"""
        endpoint = f"stock/{symbol}/quote"
        
        data = await self._make_request(endpoint)
        if not data:
            return None
        
        try:
            # Parse IEX Cloud quote response
            current_price = Decimal(str(data.get('latestPrice', 0)))
            open_price = Decimal(str(data.get('open', 0))) if data.get('open') else None
            high_price = Decimal(str(data.get('high', 0))) if data.get('high') else None
            low_price = Decimal(str(data.get('low', 0))) if data.get('low') else None
            previous_close = Decimal(str(data.get('previousClose', 0))) if data.get('previousClose') else None
            
            # Calculate price change
            change = Decimal(str(data.get('change', 0)))
            change_percent = Decimal(str(data.get('changePercent', 0) * 100)) if data.get('changePercent') else Decimal('0')
            
            volume = int(data.get('volume', 0)) if data.get('volume') else None
            market_cap = Decimal(str(data.get('marketCap', 0))) if data.get('marketCap') else None
            
            # Parse timestamp
            latest_time = data.get('latestTime')
            if latest_time and data.get('latestUpdate'):
                timestamp = datetime.fromtimestamp(data['latestUpdate'] / 1000)
            else:
                timestamp = datetime.utcnow()
            
            return MarketDataPoint(
                symbol=symbol,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=previous_close,
                current_price=current_price,
                volume=volume,
                market_cap=market_cap,
                price_change=change,
                price_change_percent=change_percent,
                data_type=MarketDataType.QUOTE,
                provider=DataProvider.IEX_CLOUD,
                is_real_time=data.get('latestSource') == 'IEX real time price',
                additional_data={
                    'latest_source': data.get('latestSource'),
                    'latest_time': latest_time,
                    'pe_ratio': data.get('peRatio'),
                    'week_52_high': data.get('week52High'),
                    'week_52_low': data.get('week52Low'),
                    'ytd_change': data.get('ytdChange'),
                    'raw_data': data
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
        
        # Calculate the range for IEX Cloud
        days_diff = (end_date - start_date).days
        
        if days_diff <= 5:
            range_param = "5d"
        elif days_diff <= 30:
            range_param = "1m"
        elif days_diff <= 90:
            range_param = "3m"
        elif days_diff <= 180:
            range_param = "6m"
        elif days_diff <= 365:
            range_param = "1y"
        elif days_diff <= 730:
            range_param = "2y"
        else:
            range_param = "5y"
        
        endpoint = f"stock/{symbol}/chart/{range_param}"
        
        data = await self._make_request(endpoint)
        if not data or not isinstance(data, list):
            return None
        
        data_points = []
        
        try:
            for item in data:
                # Parse date
                date_str = item.get('date')
                if not date_str:
                    continue
                
                item_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Filter by date range
                if not (start_date <= item_date <= end_date):
                    continue
                
                open_price = Decimal(str(item.get('open', 0))) if item.get('open') else None
                high_price = Decimal(str(item.get('high', 0))) if item.get('high') else None
                low_price = Decimal(str(item.get('low', 0))) if item.get('low') else None
                close_price = Decimal(str(item.get('close', 0))) if item.get('close') else None
                volume = int(item.get('volume', 0)) if item.get('volume') else None
                
                # Calculate price change
                price_change = None
                price_change_percent = None
                if item.get('change') is not None:
                    price_change = Decimal(str(item['change']))
                if item.get('changePercent') is not None:
                    price_change_percent = Decimal(str(item['changePercent'] * 100))
                
                point = MarketDataPoint(
                    symbol=symbol,
                    timestamp=datetime.combine(item_date, datetime.min.time()),
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    current_price=close_price,
                    volume=volume,
                    price_change=price_change,
                    price_change_percent=price_change_percent,
                    data_type=MarketDataType.HISTORICAL,
                    provider=DataProvider.IEX_CLOUD,
                    is_real_time=False,
                    additional_data={
                        'unadjusted_volume': item.get('unadjustedVolume'),
                        'change_over_time': item.get('changeOverTime'),
                        'raw_data': item
                    }
                )
                data_points.append(point)
            
            # Sort by date
            data_points.sort(key=lambda x: x.timestamp)
            
            return HistoricalData(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                data_points=data_points,
                provider=DataProvider.IEX_CLOUD
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing historical data for {symbol}: {e}")
            return None
    
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company information for a symbol"""
        endpoint = f"stock/{symbol}/company"
        
        data = await self._make_request(endpoint)
        if not data:
            return None
        
        try:
            # Get additional stats
            stats_endpoint = f"stock/{symbol}/stats"
            stats_data = await self._make_request(stats_endpoint)
            
            market_cap = None
            employees = None
            
            if stats_data:
                if stats_data.get('marketcap'):
                    market_cap = Decimal(str(stats_data['marketcap']))
                if data.get('employees'):
                    employees = int(data['employees'])
            
            return CompanyInfo(
                symbol=symbol,
                name=data.get('companyName', ''),
                sector=data.get('sector'),
                industry=data.get('industry'),
                description=data.get('description'),
                website=data.get('website'),
                market_cap=market_cap,
                employees=employees,
                exchange=data.get('exchange'),
                country=data.get('country'),
                provider=DataProvider.IEX_CLOUD,
                last_updated=datetime.utcnow()
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing company info for {symbol}: {e}")
            return None
    
    async def get_intraday_data(self, symbol: str) -> Optional[List[MarketDataPoint]]:
        """Get intraday data for a symbol"""
        endpoint = f"stock/{symbol}/intraday-prices"
        
        data = await self._make_request(endpoint)
        if not data or not isinstance(data, list):
            return None
        
        data_points = []
        
        try:
            for item in data:
                if not item.get('close'):
                    continue
                
                # Parse time
                date_str = item.get('date')
                minute_str = item.get('minute')
                
                if date_str and minute_str:
                    timestamp = datetime.strptime(f"{date_str} {minute_str}", '%Y-%m-%d %H:%M')
                else:
                    timestamp = datetime.utcnow()
                
                close_price = Decimal(str(item.get('close', 0)))
                open_price = Decimal(str(item.get('open', 0))) if item.get('open') else None
                high_price = Decimal(str(item.get('high', 0))) if item.get('high') else None
                low_price = Decimal(str(item.get('low', 0))) if item.get('low') else None
                volume = int(item.get('volume', 0)) if item.get('volume') else None
                
                point = MarketDataPoint(
                    symbol=symbol,
                    timestamp=timestamp,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    current_price=close_price,
                    volume=volume,
                    data_type=MarketDataType.INTRADAY,
                    provider=DataProvider.IEX_CLOUD,
                    is_real_time=True,
                    additional_data={
                        'market_open': item.get('marketOpen'),
                        'market_close': item.get('marketClose'),
                        'market_high': item.get('marketHigh'),
                        'market_low': item.get('marketLow'),
                        'market_average': item.get('marketAverage'),
                        'market_volume': item.get('marketVolume'),
                        'market_notional': item.get('marketNotional'),
                        'market_number_of_trades': item.get('marketNumberOfTrades'),
                        'raw_data': item
                    }
                )
                data_points.append(point)
            
            return data_points
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing intraday data for {symbol}: {e}")
            return None
    
    async def get_news(self, symbol: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get news for a symbol"""
        endpoint = f"stock/{symbol}/news"
        params = {'last': limit}
        
        return await self._make_request(endpoint, params)
    
    async def get_financials(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get financial data for a symbol"""
        endpoint = f"stock/{symbol}/financials"
        
        return await self._make_request(endpoint)
    
    async def get_earnings(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get earnings data for a symbol"""
        endpoint = f"stock/{symbol}/earnings"
        
        return await self._make_request(endpoint)
    
    async def get_dividends(self, symbol: str, range_param: str = "1y") -> Optional[List[Dict[str, Any]]]:
        """Get dividend data for a symbol"""
        endpoint = f"stock/{symbol}/dividends/{range_param}"
        
        return await self._make_request(endpoint)
    
    async def get_splits(self, symbol: str, range_param: str = "1y") -> Optional[List[Dict[str, Any]]]:
        """Get stock split data for a symbol"""
        endpoint = f"stock/{symbol}/splits/{range_param}"
        
        return await self._make_request(endpoint)
    
    async def search_symbols(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Search for symbols by query"""
        endpoint = f"search/{query}"
        
        return await self._make_request(endpoint)
    
    async def get_market_status(self) -> Optional[Dict[str, Any]]:
        """Get market status"""
        endpoint = "stock/market/today-market-status"
        
        return await self._make_request(endpoint)
    
    async def get_sectors(self) -> Optional[List[Dict[str, Any]]]:
        """Get sector performance data"""
        endpoint = "stock/market/sector-performance"
        
        return await self._make_request(endpoint)
    
    async def get_multiple_quotes_batch(self, symbols: List[str]) -> List[MarketDataPoint]:
        """Get quotes for multiple symbols using batch endpoint"""
        if not symbols:
            return []
        
        # IEX Cloud supports batch requests
        symbol_string = ','.join(symbols)
        endpoint = f"stock/market/batch"
        params = {
            'symbols': symbol_string,
            'types': 'quote',
            'range': '1d'
        }
        
        data = await self._make_request(endpoint, params)
        if not data:
            return []
        
        quotes = []
        
        for symbol, symbol_data in data.items():
            if 'quote' not in symbol_data:
                continue
            
            quote_data = symbol_data['quote']
            
            try:
                quote = self._parse_quote_data(symbol, quote_data)
                if quote:
                    quotes.append(quote)
            except Exception as e:
                self.logger.error(f"Error parsing batch quote for {symbol}: {e}")
        
        return quotes
    
    def _parse_quote_data(self, symbol: str, data: Dict[str, Any]) -> Optional[MarketDataPoint]:
        """Parse quote data from IEX Cloud response"""
        try:
            current_price = Decimal(str(data.get('latestPrice', 0)))
            open_price = Decimal(str(data.get('open', 0))) if data.get('open') else None
            high_price = Decimal(str(data.get('high', 0))) if data.get('high') else None
            low_price = Decimal(str(data.get('low', 0))) if data.get('low') else None
            previous_close = Decimal(str(data.get('previousClose', 0))) if data.get('previousClose') else None
            
            change = Decimal(str(data.get('change', 0)))
            change_percent = Decimal(str(data.get('changePercent', 0) * 100)) if data.get('changePercent') else Decimal('0')
            
            volume = int(data.get('volume', 0)) if data.get('volume') else None
            market_cap = Decimal(str(data.get('marketCap', 0))) if data.get('marketCap') else None
            
            timestamp = datetime.utcnow()
            if data.get('latestUpdate'):
                timestamp = datetime.fromtimestamp(data['latestUpdate'] / 1000)
            
            return MarketDataPoint(
                symbol=symbol,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=previous_close,
                current_price=current_price,
                volume=volume,
                market_cap=market_cap,
                price_change=change,
                price_change_percent=change_percent,
                data_type=MarketDataType.QUOTE,
                provider=DataProvider.IEX_CLOUD,
                is_real_time=data.get('latestSource') == 'IEX real time price',
                additional_data=data
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing quote data for {symbol}: {e}")
            return None