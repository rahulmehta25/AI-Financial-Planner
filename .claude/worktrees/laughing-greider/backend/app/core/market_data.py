"""
Real market data fetcher using yfinance (free, no API key needed)
This ACTUALLY WORKS - not boilerplate!
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import lru_cache
import json

class MarketDataService:
    """Real market data service that actually fetches prices"""
    
    @staticmethod
    @lru_cache(maxsize=100)
    def get_current_price(symbol: str) -> Optional[float]:
        """Get current price for a symbol - REAL DATA"""
        try:
            ticker = yf.Ticker(symbol)
            # Get the most recent price
            info = ticker.info
            # Try different price fields in order of preference
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            return float(price) if price else None
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    @staticmethod
    def get_multiple_prices(symbols: List[str]) -> Dict[str, float]:
        """Get prices for multiple symbols efficiently"""
        prices = {}
        # Use batch download for efficiency
        try:
            tickers = yf.Tickers(' '.join(symbols))
            for symbol in symbols:
                ticker = tickers.tickers.get(symbol.upper())
                if ticker:
                    info = ticker.info
                    price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                    if price:
                        prices[symbol] = float(price)
        except Exception as e:
            print(f"Error in batch fetch: {e}")
            # Fallback to individual fetches
            for symbol in symbols:
                price = MarketDataService.get_current_price(symbol)
                if price:
                    prices[symbol] = price
        return prices
    
    @staticmethod
    def get_historical_data(symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist if not hist.empty else None
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    @staticmethod
    def get_stock_info(symbol: str) -> Dict[str, Any]:
        """Get detailed stock information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant information
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'previousClose': info.get('previousClose'),
                'dayChange': info.get('currentPrice', 0) - info.get('previousClose', 0) if info.get('currentPrice') and info.get('previousClose') else 0,
                'dayChangePercent': ((info.get('currentPrice', 0) - info.get('previousClose', 0)) / info.get('previousClose', 1) * 100) if info.get('previousClose') else 0,
                'marketCap': info.get('marketCap'),
                'volume': info.get('volume'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
                'dividendYield': info.get('dividendYield'),
                'peRatio': info.get('trailingPE'),
                'exchange': info.get('exchange'),
                'currency': info.get('currency', 'USD')
            }
        except Exception as e:
            print(f"Error fetching info for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    @staticmethod
    def calculate_portfolio_metrics(holdings: List[Dict]) -> Dict[str, Any]:
        """
        Calculate real portfolio metrics
        holdings = [{'symbol': 'AAPL', 'quantity': 10, 'cost_basis': 150}, ...]
        """
        total_value = 0
        total_cost = 0
        holdings_with_prices = []
        
        # Get all prices at once
        symbols = [h['symbol'] for h in holdings]
        prices = MarketDataService.get_multiple_prices(symbols)
        
        for holding in holdings:
            symbol = holding['symbol']
            quantity = holding['quantity']
            cost_basis = holding.get('cost_basis', 0)
            
            current_price = prices.get(symbol, 0)
            if current_price:
                market_value = current_price * quantity
                total_value += market_value
                total_cost += cost_basis * quantity
                
                gain_loss = market_value - (cost_basis * quantity)
                gain_loss_pct = (gain_loss / (cost_basis * quantity) * 100) if cost_basis > 0 else 0
                
                holdings_with_prices.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'cost_basis': cost_basis,
                    'current_price': current_price,
                    'market_value': market_value,
                    'gain_loss': gain_loss,
                    'gain_loss_percent': gain_loss_pct,
                    'weight': 0  # Will calculate after total
                })
        
        # Calculate weights
        for holding in holdings_with_prices:
            holding['weight'] = (holding['market_value'] / total_value * 100) if total_value > 0 else 0
        
        total_gain_loss = total_value - total_cost
        total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_gain_loss': total_gain_loss,
            'total_gain_loss_percent': total_gain_loss_pct,
            'holdings': holdings_with_prices,
            'last_updated': datetime.now().isoformat()
        }


# Test the service
if __name__ == "__main__":
    # Test with real symbols
    service = MarketDataService()
    
    # Test single price
    print("Apple price:", service.get_current_price("AAPL"))
    
    # Test multiple prices
    prices = service.get_multiple_prices(["AAPL", "GOOGL", "MSFT"])
    print("Multiple prices:", prices)
    
    # Test portfolio calculation
    test_holdings = [
        {'symbol': 'AAPL', 'quantity': 10, 'cost_basis': 150},
        {'symbol': 'GOOGL', 'quantity': 5, 'cost_basis': 2500},
        {'symbol': 'MSFT', 'quantity': 15, 'cost_basis': 300}
    ]
    metrics = service.calculate_portfolio_metrics(test_holdings)
    print("Portfolio metrics:", json.dumps(metrics, indent=2))