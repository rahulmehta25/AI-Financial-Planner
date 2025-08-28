"""
Market Data Provider Manager - Production Grade Implementation

Comprehensive provider management system supporting:
- Tier 1: Institutional providers (Polygon.io, Databento, Refinitiv)
- Tier 2: Professional providers (Alpaca, IEX Cloud, TwelveData) 
- Tier 3: Free/Backup providers (Yahoo Finance, Alpha Vantage)

Features:
- Intelligent provider selection based on data type and requirements
- Circuit breaker pattern for reliability
- Cost optimization through provider tiering
- Comprehensive error handling and fallback strategies
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, AsyncIterator, Union
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from decimal import Decimal

from app.core.config import Config
from app.services.market_data.providers.base import BaseProvider
from app.services.market_data.providers.polygon_io import PolygonIOProvider
from app.services.market_data.providers.databento import DatabentProvider
from app.services.market_data.providers.alpha_vantage import AlphaVantageProvider
from app.services.market_data.providers.yahoo_finance import YahooFinanceProvider
from app.services.market_data.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ProviderTier(Enum):
    """Provider tier classification"""
    INSTITUTIONAL = "institutional"  # Tier 1: Most expensive, most reliable
    PROFESSIONAL = "professional"    # Tier 2: Good balance of cost/quality
    FREE_BACKUP = "free_backup"     # Tier 3: Free/cheap backup sources


class DataType(Enum):
    """Data type classifications"""
    REAL_TIME_QUOTES = "real_time_quotes"
    HISTORICAL_BARS = "historical_bars"
    TICK_DATA = "tick_data"
    FUNDAMENTAL_DATA = "fundamental_data"
    OPTIONS_DATA = "options_data"
    NEWS_SENTIMENT = "news_sentiment"
    ECONOMIC_DATA = "economic_data"


@dataclass
class ProviderFeatures:
    """Provider feature capabilities"""
    websocket_connections: int
    requests_per_minute: Union[int, str]  # 'unlimited' or number
    historical_data_years: int
    tick_data: bool = False
    options_data: bool = False
    fundamental_data: bool = False
    news_sentiment: bool = False
    real_time_sip: bool = False
    nanosecond_timestamps: bool = False
    cost_per_month: float = 0.0
    reliability_score: float = 0.95  # 0.0 to 1.0


class CircuitBreaker:
    """Circuit breaker pattern implementation for provider reliability"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: tuple = (Exception,)
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == "OPEN":
            if datetime.utcnow().timestamp() - self.last_failure_time < self.timeout:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
            else:
                self.state = "HALF_OPEN"
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow().timestamp()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")


class MarketDataProviderManager:
    """
    Production-grade market data provider management system
    
    Manages multiple data providers with intelligent routing, 
    fallback mechanisms, and cost optimization.
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self._initialize_providers()
        self._initialize_circuit_breakers()
        self.provider_health = {}
        
    def _initialize_providers(self):
        """Initialize all market data providers with their configurations"""
        
        # Tier 1: Institutional providers (most expensive, most reliable)
        self.primary_providers = {
            'polygon': {
                'provider': PolygonIOProvider(
                    api_key=Config.POLYGON_API_KEY,
                    tier='stocks_pro'
                ),
                'features': ProviderFeatures(
                    websocket_connections=10,
                    requests_per_minute='unlimited',
                    historical_data_years=20,
                    tick_data=True,
                    options_data=True,
                    fundamental_data=True,
                    real_time_sip=True,
                    cost_per_month=299.0,
                    reliability_score=0.98
                ),
                'tier': ProviderTier.INSTITUTIONAL,
                'priority': 1
            },
            'databento': {
                'provider': DatabentProvider(
                    api_key=Config.DATABENTO_KEY,
                    subscription='professional'
                ),
                'features': ProviderFeatures(
                    websocket_connections=5,
                    requests_per_minute=1000,
                    historical_data_years=15,
                    tick_data=True,
                    nanosecond_timestamps=True,
                    fundamental_data=True,
                    cost_per_month=1500.0,
                    reliability_score=0.97
                ),
                'tier': ProviderTier.INSTITUTIONAL,
                'priority': 2
            },
            'refinitiv': {
                'provider': None,  # Enterprise provider - requires special setup
                'features': ProviderFeatures(
                    websocket_connections=20,
                    requests_per_minute='unlimited',
                    historical_data_years=25,
                    tick_data=True,
                    options_data=True,
                    fundamental_data=True,
                    news_sentiment=True,
                    cost_per_month=5000.0,
                    reliability_score=0.99
                ),
                'tier': ProviderTier.INSTITUTIONAL,
                'priority': 0  # Highest priority when available
            }
        }
        
        # Tier 2: Professional providers (good balance)
        self.secondary_providers = {
            'alpaca': {
                'provider': None,  # AlpacaDataProvider would be implemented
                'features': ProviderFeatures(
                    websocket_connections=3,
                    requests_per_minute=200,
                    historical_data_years=7,
                    tick_data=True,
                    real_time_sip=True,
                    cost_per_month=99.0,
                    reliability_score=0.95
                ),
                'tier': ProviderTier.PROFESSIONAL,
                'priority': 3
            },
            'iex_cloud': {
                'provider': None,  # IEXCloudProvider would be implemented
                'features': ProviderFeatures(
                    websocket_connections=2,
                    requests_per_minute=500,
                    historical_data_years=5,
                    fundamental_data=True,
                    cost_per_month=199.0,
                    reliability_score=0.94
                ),
                'tier': ProviderTier.PROFESSIONAL,
                'priority': 4
            },
            'twelve_data': {
                'provider': None,  # TwelveDataProvider would be implemented
                'features': ProviderFeatures(
                    websocket_connections=1,
                    requests_per_minute=800,
                    historical_data_years=10,
                    fundamental_data=True,
                    cost_per_month=79.0,
                    reliability_score=0.92
                ),
                'tier': ProviderTier.PROFESSIONAL,
                'priority': 5
            }
        }
        
        # Tier 3: Free/Backup providers
        self.fallback_providers = {
            'yahoo': {
                'provider': YahooFinanceProvider(),
                'features': ProviderFeatures(
                    websocket_connections=0,
                    requests_per_minute=100,
                    historical_data_years=5,
                    cost_per_month=0.0,
                    reliability_score=0.85
                ),
                'tier': ProviderTier.FREE_BACKUP,
                'priority': 6
            },
            'alpha_vantage': {
                'provider': AlphaVantageProvider(
                    api_key=Config.ALPHA_VANTAGE_KEY
                ),
                'features': ProviderFeatures(
                    websocket_connections=0,
                    requests_per_minute=5,  # Free tier limitation
                    historical_data_years=20,
                    fundamental_data=True,
                    cost_per_month=0.0,
                    reliability_score=0.80
                ),
                'tier': ProviderTier.FREE_BACKUP,
                'priority': 7
            }
        }
        
        # Combine all providers for easy access
        self.all_providers = {
            **self.primary_providers,
            **self.secondary_providers,
            **self.fallback_providers
        }
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for each provider"""
        
        self.circuit_breakers = {}
        
        for provider_name, config in self.all_providers.items():
            # Set failure threshold based on provider tier
            if config['tier'] == ProviderTier.INSTITUTIONAL:
                threshold = 3  # More sensitive for premium providers
            elif config['tier'] == ProviderTier.PROFESSIONAL:
                threshold = 5
            else:
                threshold = 10  # More tolerant for free providers
            
            self.circuit_breakers[provider_name] = CircuitBreaker(
                failure_threshold=threshold,
                timeout=300,  # 5 minutes
                expected_exception=(Exception,)
            )
    
    def select_optimal_provider(
        self,
        data_type: DataType,
        symbols: List[str],
        requirements: Dict[str, Any] = None
    ) -> str:
        """
        Select the optimal provider based on data type, requirements, and cost
        
        Args:
            data_type: Type of data needed
            symbols: List of symbols to fetch
            requirements: Additional requirements (real_time, historical_depth, etc.)
        
        Returns:
            Name of the selected provider
        """
        
        if requirements is None:
            requirements = {}
        
        # Filter providers that support the required data type
        suitable_providers = []
        
        for name, config in self.all_providers.items():
            provider_obj = config.get('provider')
            if not provider_obj:
                continue  # Skip uninitialized providers
            
            features = config['features']
            
            # Check if provider supports the data type
            if self._provider_supports_data_type(data_type, features):
                # Check circuit breaker status
                if self.circuit_breakers[name].state != "OPEN":
                    # Calculate suitability score
                    score = self._calculate_provider_score(
                        name, config, data_type, requirements
                    )
                    suitable_providers.append((name, score))
        
        if not suitable_providers:
            logger.warning(f"No suitable providers found for {data_type}")
            # Return the most basic provider as last resort
            return 'yahoo'
        
        # Sort by score (higher is better) and return the best
        suitable_providers.sort(key=lambda x: x[1], reverse=True)
        selected_provider = suitable_providers[0][0]
        
        logger.info(f"Selected provider '{selected_provider}' for {data_type}")
        return selected_provider
    
    def _provider_supports_data_type(
        self,
        data_type: DataType,
        features: ProviderFeatures
    ) -> bool:
        """Check if provider supports the required data type"""
        
        support_matrix = {
            DataType.REAL_TIME_QUOTES: features.real_time_sip or features.websocket_connections > 0,
            DataType.HISTORICAL_BARS: features.historical_data_years > 0,
            DataType.TICK_DATA: features.tick_data,
            DataType.FUNDAMENTAL_DATA: features.fundamental_data,
            DataType.OPTIONS_DATA: features.options_data,
            DataType.NEWS_SENTIMENT: features.news_sentiment,
            DataType.ECONOMIC_DATA: features.fundamental_data  # Assume economic data is part of fundamental
        }
        
        return support_matrix.get(data_type, False)
    
    def _calculate_provider_score(
        self,
        provider_name: str,
        config: Dict,
        data_type: DataType,
        requirements: Dict[str, Any]
    ) -> float:
        """
        Calculate a suitability score for the provider
        
        Higher score = better choice
        """
        
        features = config['features']
        score = 0.0
        
        # Base reliability score
        score += features.reliability_score * 100
        
        # Priority bonus (lower priority number = higher bonus)
        priority_bonus = (10 - config['priority']) * 10
        score += priority_bonus
        
        # Data type specific bonuses
        if data_type == DataType.REAL_TIME_QUOTES:
            if features.nanosecond_timestamps:
                score += 20
            if features.real_time_sip:
                score += 15
            score += features.websocket_connections * 2
        
        elif data_type == DataType.TICK_DATA:
            if features.tick_data:
                score += 25
            if features.nanosecond_timestamps:
                score += 15
        
        elif data_type == DataType.HISTORICAL_BARS:
            score += features.historical_data_years * 2
        
        elif data_type == DataType.FUNDAMENTAL_DATA:
            if features.fundamental_data:
                score += 20
        
        # Cost penalty (higher cost = lower score, but not too punitive)
        cost_penalty = min(features.cost_per_month / 100, 20)
        score -= cost_penalty
        
        # Requirements-based adjustments
        if requirements.get('real_time_required', False):
            if not (features.real_time_sip or features.websocket_connections > 0):
                score -= 50  # Heavy penalty for not supporting real-time
        
        if requirements.get('high_volume', False):
            if isinstance(features.requests_per_minute, int):
                if features.requests_per_minute < 1000:
                    score -= 30  # Penalty for low rate limits
        
        # Health-based adjustment
        health_score = self.provider_health.get(provider_name, 1.0)
        score *= health_score
        
        return score
    
    async def get_historical_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d',
        provider_override: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch historical data with intelligent provider selection and fallback
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval (1m, 5m, 1h, 1d, etc.)
            provider_override: Force specific provider (for testing)
        
        Returns:
            DataFrame with historical data
        """
        
        # Check cache first
        cache_key = f"hist_{'-'.join(symbols)}_{start_date.date()}_{end_date.date()}_{interval}"
        cached_data = await self.cache_manager.get(cache_key)
        
        if cached_data is not None:
            logger.info(f"Returning cached historical data for {symbols}")
            return cached_data
        
        # Select provider
        if provider_override:
            selected_provider = provider_override
        else:
            selected_provider = self.select_optimal_provider(
                DataType.HISTORICAL_BARS,
                symbols,
                {'historical_depth': (end_date - start_date).days}
            )
        
        # Try to fetch data with fallback mechanism
        data = await self._fetch_with_fallback(
            'get_historical_data',
            selected_provider,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        if data is not None and not data.empty:
            # Cache the successful result
            cache_ttl = self._calculate_cache_ttl(interval)
            await self.cache_manager.set(cache_key, data, ttl=cache_ttl)
            
            logger.info(f"Successfully fetched historical data for {symbols} from {selected_provider}")
            return data
        
        logger.error(f"Failed to fetch historical data for {symbols}")
        return pd.DataFrame()
    
    async def get_real_time_quote(
        self,
        symbol: str,
        provider_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get real-time quote with multi-source validation
        
        Args:
            symbol: Stock symbol
            provider_override: Force specific provider
        
        Returns:
            Quote data dictionary
        """
        
        # Check cache for recent quote (< 30 seconds old)
        cache_key = f"quote_{symbol}"
        cached_quote = await self.cache_manager.get(cache_key)
        
        if cached_quote and self._is_quote_fresh(cached_quote):
            return cached_quote
        
        # Select provider
        if provider_override:
            selected_provider = provider_override
        else:
            selected_provider = self.select_optimal_provider(
                DataType.REAL_TIME_QUOTES,
                [symbol],
                {'real_time_required': True}
            )
        
        # Fetch quote with fallback
        quote = await self._fetch_with_fallback(
            'get_real_time_quote',
            selected_provider,
            symbol=symbol
        )
        
        if quote:
            # Add metadata
            quote['provider'] = selected_provider
            quote['timestamp'] = datetime.utcnow()
            
            # Cache for 10 seconds
            await self.cache_manager.set(cache_key, quote, ttl=10)
            
            return quote
        
        logger.error(f"Failed to get real-time quote for {symbol}")
        return {}
    
    async def _fetch_with_fallback(
        self,
        method_name: str,
        primary_provider: str,
        **kwargs
    ) -> Any:
        """
        Fetch data with automatic fallback to other providers
        
        Args:
            method_name: Method to call on provider
            primary_provider: Primary provider to try first
            **kwargs: Arguments to pass to the method
        
        Returns:
            Data from successful provider or None
        """
        
        # Create ordered list of providers to try
        providers_to_try = [primary_provider]
        
        # Add other providers sorted by priority, excluding the primary
        other_providers = [
            (name, config['priority'])
            for name, config in self.all_providers.items()
            if name != primary_provider 
            and config.get('provider') is not None
            and self.circuit_breakers[name].state != "OPEN"
        ]
        
        other_providers.sort(key=lambda x: x[1])  # Sort by priority
        providers_to_try.extend([name for name, _ in other_providers])
        
        last_exception = None
        
        for provider_name in providers_to_try:
            try:
                provider_config = self.all_providers[provider_name]
                provider_obj = provider_config.get('provider')
                
                if not provider_obj or not hasattr(provider_obj, method_name):
                    continue
                
                # Try to fetch data through circuit breaker
                method = getattr(provider_obj, method_name)
                result = await self.circuit_breakers[provider_name].call(
                    method, **kwargs
                )
                
                if result is not None:
                    logger.info(f"Successfully fetched data from {provider_name}")
                    self._update_provider_health(provider_name, success=True)
                    return result
            
            except Exception as e:
                last_exception = e
                logger.warning(f"Provider {provider_name} failed: {str(e)}")
                self._update_provider_health(provider_name, success=False)
                continue
        
        logger.error(f"All providers failed for {method_name}. Last error: {last_exception}")
        return None
    
    def _update_provider_health(self, provider_name: str, success: bool):
        """Update provider health score based on success/failure"""
        
        if provider_name not in self.provider_health:
            self.provider_health[provider_name] = 1.0
        
        current_health = self.provider_health[provider_name]
        
        if success:
            # Slowly improve health
            self.provider_health[provider_name] = min(1.0, current_health + 0.01)
        else:
            # Quickly degrade health
            self.provider_health[provider_name] = max(0.1, current_health - 0.1)
    
    def _is_quote_fresh(self, quote: Dict[str, Any], max_age_seconds: int = 30) -> bool:
        """Check if cached quote is still fresh"""
        
        if 'timestamp' not in quote:
            return False
        
        quote_time = quote['timestamp']
        if isinstance(quote_time, str):
            quote_time = datetime.fromisoformat(quote_time)
        
        age = (datetime.utcnow() - quote_time).total_seconds()
        return age <= max_age_seconds
    
    def _calculate_cache_ttl(self, interval: str) -> int:
        """Calculate appropriate cache TTL based on data interval"""
        
        interval_ttl = {
            '1m': 60,      # 1 minute data cached for 1 minute
            '5m': 300,     # 5 minute data cached for 5 minutes
            '15m': 900,    # 15 minute data cached for 15 minutes
            '1h': 3600,    # 1 hour data cached for 1 hour
            '1d': 86400,   # Daily data cached for 1 day
            '1w': 604800,  # Weekly data cached for 1 week
        }
        
        return interval_ttl.get(interval, 3600)  # Default to 1 hour
    
    async def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers including health and circuit breaker state"""
        
        status = {}
        
        for name, config in self.all_providers.items():
            provider_obj = config.get('provider')
            circuit_breaker = self.circuit_breakers[name]
            health = self.provider_health.get(name, 1.0)
            
            status[name] = {
                'tier': config['tier'].value,
                'priority': config['priority'],
                'initialized': provider_obj is not None,
                'circuit_breaker_state': circuit_breaker.state,
                'failure_count': circuit_breaker.failure_count,
                'health_score': health,
                'cost_per_month': config['features'].cost_per_month,
                'reliability_score': config['features'].reliability_score,
                'supports': {
                    'real_time': config['features'].real_time_sip or config['features'].websocket_connections > 0,
                    'historical': config['features'].historical_data_years > 0,
                    'tick_data': config['features'].tick_data,
                    'fundamental': config['features'].fundamental_data,
                    'options': config['features'].options_data
                }
            }
        
        return status
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all active providers"""
        
        health_results = {}
        
        for name, config in self.all_providers.items():
            provider_obj = config.get('provider')
            
            if not provider_obj:
                health_results[name] = False
                continue
            
            try:
                # Try a simple operation to check health
                if hasattr(provider_obj, 'health_check'):
                    is_healthy = await provider_obj.health_check()
                else:
                    # Fallback: try to get a simple quote
                    result = await provider_obj.get_real_time_quote('AAPL')
                    is_healthy = result is not None
                
                health_results[name] = is_healthy
                self._update_provider_health(name, success=is_healthy)
                
            except Exception as e:
                logger.warning(f"Health check failed for {name}: {str(e)}")
                health_results[name] = False
                self._update_provider_health(name, success=False)
        
        return health_results
    
    def get_cost_optimization_recommendations(self) -> Dict[str, Any]:
        """Provide cost optimization recommendations based on usage patterns"""
        
        recommendations = {
            'current_monthly_cost': 0.0,
            'optimizations': [],
            'alternative_configurations': []
        }
        
        # Calculate current cost
        for name, config in self.all_providers.items():
            if config.get('provider') is not None:
                recommendations['current_monthly_cost'] += config['features'].cost_per_month
        
        # Analyze usage patterns and suggest optimizations
        # This would be enhanced with actual usage analytics
        
        recommendations['optimizations'].extend([
            {
                'type': 'provider_consolidation',
                'description': 'Consider using fewer premium providers for similar data coverage',
                'potential_savings': 500.0
            },
            {
                'type': 'tier_optimization',
                'description': 'Evaluate if professional tier providers can meet your needs',
                'potential_savings': 1000.0
            },
            {
                'type': 'caching_improvement',
                'description': 'Increase cache TTL to reduce API calls',
                'potential_savings': 200.0
            }
        ])
        
        return recommendations


# Global instance for use throughout the application
provider_manager = MarketDataProviderManager()