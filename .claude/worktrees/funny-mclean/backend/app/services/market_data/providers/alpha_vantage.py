"""
Alpha Vantage Provider

Market data provider integration for Alpha Vantage API.
"""

from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import asyncio
import aiohttp
import logging

from .base import BaseProvider
from ..models import MarketDataPoint, MarketDataType, DataProvider, HistoricalData, CompanyInfo
from ..config import config, get_provider_config


class AlphaVantageProvider(BaseProvider):
    """Alpha Vantage market data provider"""
    
    def __init__(self):
        provider_config = get_provider_config(DataProvider.ALPHA_VANTAGE)
        super().__init__(
            DataProvider.ALPHA_VANTAGE, 
            provider_config.get('rate_limit', 5)
        )
        self.api_key = provider_config.get('api_key')
        self.base_url = provider_config.get('base_url')
        
        if not self.api_key:
            self.logger.warning("Alpha Vantage API key not configured")
    
    async def _initialize_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=config.request_timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def _cleanup_session(self):
        """Cleanup HTTP session"""
        if self._session:
            await self._session.close()
    
    async def _make_request(self, params: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Make API request to Alpha Vantage"""
        if not self.api_key:
            self.logger.error("Alpha Vantage API key not configured")
            return None
        
        await self.rate_limiter.wait_if_needed()
        
        params.update({
            'apikey': self.api_key,
            'datatype': 'json'
        })
        
        try:
            async with self._session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API errors
                    if 'Error Message' in data:
                        self.logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                        return None
                    
                    if 'Note' in data:
                        self.logger.warning(f"Alpha Vantage API note: {data['Note']}")
                        return None
                    
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
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = await self._make_request(params)
        if not data or 'Global Quote' not in data:
            return None
        
        quote_data = data['Global Quote']
        
        try:
            # Parse Alpha Vantage quote response
            current_price = Decimal(quote_data.get('05. price', '0'))
            open_price = Decimal(quote_data.get('02. open', '0'))
            high_price = Decimal(quote_data.get('03. high', '0'))
            low_price = Decimal(quote_data.get('04. low', '0'))
            previous_close = Decimal(quote_data.get('08. previous close', '0'))
            change = Decimal(quote_data.get('09. change', '0'))
            change_percent = quote_data.get('10. change percent', '0%').rstrip('%')
            change_percent = Decimal(change_percent) if change_percent else Decimal('0')
            volume = int(quote_data.get('06. volume', '0'))
            
            # Get latest trading day
            latest_trading_day = quote_data.get('07. latest trading day', '')
            timestamp = datetime.fromisoformat(latest_trading_day) if latest_trading_day else datetime.utcnow()
            
            return MarketDataPoint(
                symbol=symbol,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=previous_close,
                current_price=current_price,
                volume=volume,
                price_change=change,
                price_change_percent=change_percent,
                data_type=MarketDataType.QUOTE,
                provider=DataProvider.ALPHA_VANTAGE,
                is_real_time=True,
                additional_data={
                    'latest_trading_day': latest_trading_day,
                    'raw_data': quote_data
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
        
        # Map interval to Alpha Vantage function
        if interval in ['1d', 'daily']:
            function = 'TIME_SERIES_DAILY'
            output_size = 'full'
        elif interval in ['1wk', 'weekly']:
            function = 'TIME_SERIES_WEEKLY'
            output_size = 'full'
        elif interval in ['1mo', 'monthly']:
            function = 'TIME_SERIES_MONTHLY'
            output_size = 'full'
        else:
            # For intraday data
            function = 'TIME_SERIES_INTRADAY'
            output_size = 'full'
            interval = '5min'  # Default to 5-minute intervals
        
        params = {
            'function': function,
            'symbol': symbol,
            'outputsize': output_size
        }
        
        if function == 'TIME_SERIES_INTRADAY':
            params['interval'] = interval
        
        data = await self._make_request(params)
        if not data:
            return None
        
        # Find the time series data key
        time_series_key = None
        for key in data.keys():
            if 'Time Series' in key:
                time_series_key = key
                break
        
        if not time_series_key or time_series_key not in data:
            self.logger.error(f"No time series data found for {symbol}")
            return None
        
        time_series = data[time_series_key]
        data_points = []
        
        try:
            for date_str, price_data in time_series.items():
                data_date = datetime.fromisoformat(date_str).date()
                
                # Filter by date range
                if start_date <= data_date <= end_date:
                    open_price = Decimal(price_data.get('1. open', '0'))
                    high_price = Decimal(price_data.get('2. high', '0'))
                    low_price = Decimal(price_data.get('3. low', '0'))
                    close_price = Decimal(price_data.get('4. close', '0'))
                    volume = int(price_data.get('5. volume', '0'))
                    
                    point = MarketDataPoint(
                        symbol=symbol,
                        timestamp=datetime.combine(data_date, datetime.min.time()),
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        current_price=close_price,
                        volume=volume,
                        data_type=MarketDataType.HISTORICAL,
                        provider=DataProvider.ALPHA_VANTAGE,
                        is_real_time=False,
                        additional_data={
                            'raw_data': price_data
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
                provider=DataProvider.ALPHA_VANTAGE
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing historical data for {symbol}: {e}")
            return None
    
    async def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company information for a symbol"""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = await self._make_request(params)
        if not data or not data.get('Symbol'):
            return None
        
        try:
            market_cap = None
            if data.get('MarketCapitalization'):
                market_cap = Decimal(data['MarketCapitalization'])
            
            employees = None
            if data.get('FullTimeEmployees'):
                try:
                    employees = int(data['FullTimeEmployees'])
                except ValueError:
                    pass
            
            return CompanyInfo(
                symbol=symbol,
                name=data.get('Name', ''),
                sector=data.get('Sector'),
                industry=data.get('Industry'),
                description=data.get('Description'),
                website=data.get('OfficialSite'),
                market_cap=market_cap,
                employees=employees,
                exchange=data.get('Exchange'),
                country=data.get('Country'),
                provider=DataProvider.ALPHA_VANTAGE,
                last_updated=datetime.utcnow()
            )
        
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing company info for {symbol}: {e}")
            return None
    
    async def get_earnings(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get earnings data for a symbol"""
        params = {
            'function': 'EARNINGS',
            'symbol': symbol
        }
        
        return await self._make_request(params)
    
    async def get_cash_flow(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cash flow data for a symbol"""
        params = {
            'function': 'CASH_FLOW',
            'symbol': symbol
        }
        
        return await self._make_request(params)
    
    async def get_balance_sheet(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get balance sheet data for a symbol"""
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol
        }
        
        return await self._make_request(params)
    
    async def search_symbols(self, keywords: str) -> Optional[Dict[str, Any]]:
        """Search for symbols by keywords"""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        
        return await self._make_request(params)