"""
Enhanced Market Data Aggregator - Multi-Source Integration with Consensus Engine

Advanced data aggregation system featuring:
- Multi-source data validation and consensus building
- Circuit breaker pattern for reliability
- Financial ratios calculation
- Anomaly detection and data quality validation
- Intelligent source selection and fallback mechanisms
- Real-time and historical data processing
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics
from decimal import Decimal, ROUND_HALF_UP
import json

from app.services.market_data.providers import MarketDataProviderManager, CircuitBreaker
from app.services.market_data.websocket_manager import RealTimeDataManager
from app.services.market_data.cache.cache_manager import CacheManager
from app.core.config import Config

logger = logging.getLogger(__name__)


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"      # Multiple sources agree, recent data
    GOOD = "good"               # Some validation, acceptable quality
    FAIR = "fair"               # Limited validation, use with caution
    POOR = "poor"               # Failed validation, unreliable
    INVALID = "invalid"         # Completely invalid data


class ConsensusMethod(Enum):
    """Consensus building methods"""
    MAJORITY = "majority"           # Simple majority voting
    WEIGHTED_AVERAGE = "weighted"   # Weighted by source reliability
    MEDIAN = "median"              # Statistical median
    BEST_SOURCE = "best_source"    # Use highest quality source only


@dataclass
class Quote:
    """Enhanced quote data structure with metadata"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    timestamp: datetime
    source: str
    confidence: float
    spread: float = None
    
    def __post_init__(self):
        if self.spread is None and self.bid and self.ask:
            self.spread = self.ask - self.bid


@dataclass
class ConsensusResult:
    """Result of consensus building process"""
    value: Any
    confidence: float
    sources: List[str]
    method: ConsensusMethod
    quality: DataQuality
    timestamp: datetime
    metadata: Dict[str, Any] = None


@dataclass
class FinancialRatios:
    """Financial ratios calculation result"""
    symbol: str
    timestamp: datetime
    
    # Profitability ratios
    roe: Optional[float] = None  # Return on Equity
    roa: Optional[float] = None  # Return on Assets
    profit_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    
    # Liquidity ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    
    # Leverage ratios
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Efficiency ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    
    # Valuation ratios
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    
    # Market ratios
    dividend_yield: Optional[float] = None
    price_to_sales: Optional[float] = None
    price_to_cash_flow: Optional[float] = None


class DataValidator:
    """Advanced data validation and anomaly detection"""
    
    def __init__(self):
        self.price_bounds = {}  # Symbol -> (min, max) acceptable price range
        self.volume_history = {}  # Symbol -> recent volume data
        self.price_history = {}  # Symbol -> recent price data
        
    async def validate_quote(
        self,
        quote: Dict[str, Any],
        historical_context: Optional[pd.DataFrame] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate quote data for anomalies and errors
        
        Returns:
            (is_valid, list_of_issues)
        """
        
        issues = []
        symbol = quote.get('symbol')
        
        # Basic structure validation
        required_fields = ['symbol', 'bid', 'ask', 'last', 'timestamp']
        for field in required_fields:
            if field not in quote or quote[field] is None:
                issues.append(f"Missing required field: {field}")
        
        if issues:
            return False, issues
        
        # Price validation
        bid, ask, last = quote['bid'], quote['ask'], quote['last']
        
        # Spread validation
        if bid > ask:
            issues.append("Bid price higher than ask price")
        
        spread_pct = ((ask - bid) / last) * 100 if last > 0 else 0
        if spread_pct > 10:  # 10% spread seems excessive
            issues.append(f"Unusually wide spread: {spread_pct:.2f}%")
        
        # Price reasonableness
        if any(p <= 0 for p in [bid, ask, last]):
            issues.append("Non-positive prices detected")
        
        if any(p > 100000 for p in [bid, ask, last]):  # $100k+ per share
            issues.append("Unusually high prices detected")
        
        # Historical context validation
        if historical_context is not None and len(historical_context) > 0:
            recent_prices = historical_context['close'].tail(20)
            if len(recent_prices) > 0:
                price_mean = recent_prices.mean()
                price_std = recent_prices.std()
                
                # Check for price jumps (more than 3 standard deviations)
                if abs(last - price_mean) > 3 * price_std:
                    issues.append(f"Price jump detected: {last} vs recent mean {price_mean:.2f}")
        
        # Volume validation
        volume = quote.get('volume', 0)
        if volume < 0:
            issues.append("Negative volume")
        
        return len(issues) == 0, issues
    
    async def detect_anomalies(
        self,
        data_points: List[Dict[str, Any]],
        symbol: str
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in a set of data points"""
        
        if len(data_points) < 3:
            return []  # Need at least 3 points for anomaly detection
        
        anomalies = []
        
        # Extract prices
        prices = [dp.get('last', dp.get('price', 0)) for dp in data_points]
        volumes = [dp.get('volume', 0) for dp in data_points]
        
        # Price anomaly detection using IQR method
        q1, q3 = np.percentile(prices, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        for i, dp in enumerate(data_points):
            price = prices[i]
            volume = volumes[i]
            
            anomaly_reasons = []
            
            # Price anomaly
            if price < lower_bound or price > upper_bound:
                anomaly_reasons.append(f"Price {price} outside normal range [{lower_bound:.2f}, {upper_bound:.2f}]")
            
            # Volume anomaly (if we have volume data)
            if volume > 0 and len(volumes) > 1:
                avg_volume = np.mean([v for v in volumes if v > 0])
                if volume > 10 * avg_volume:  # Volume spike
                    anomaly_reasons.append(f"Volume spike: {volume} vs avg {avg_volume:.0f}")
            
            if anomaly_reasons:
                anomalies.append({
                    'data_point': dp,
                    'reasons': anomaly_reasons,
                    'severity': 'high' if len(anomaly_reasons) > 1 else 'medium'
                })
        
        return anomalies


class ConsensusEngine:
    """Advanced consensus building for multi-source data validation"""
    
    def __init__(self):
        self.source_weights = {
            'polygon': 0.30,
            'databento': 0.25,
            'refinitiv': 0.35,  # Highest weight for institutional data
            'alpaca': 0.20,
            'iex_cloud': 0.18,
            'twelve_data': 0.15,
            'yahoo': 0.10,
            'alpha_vantage': 0.08
        }
        
        self.quality_thresholds = {
            DataQuality.EXCELLENT: 0.95,
            DataQuality.GOOD: 0.80,
            DataQuality.FAIR: 0.60,
            DataQuality.POOR: 0.30
        }
    
    def find_consensus(
        self,
        data_points: List[Dict[str, Any]],
        method: ConsensusMethod = ConsensusMethod.WEIGHTED_AVERAGE,
        tolerance: float = 0.02  # 2% tolerance
    ) -> ConsensusResult:
        """
        Build consensus from multiple data sources
        
        Args:
            data_points: List of data points from different sources
            method: Consensus building method
            tolerance: Acceptable variance between sources (as percentage)
        
        Returns:
            ConsensusResult with validated consensus value
        """
        
        if not data_points:
            return ConsensusResult(
                value=None,
                confidence=0.0,
                sources=[],
                method=method,
                quality=DataQuality.INVALID,
                timestamp=datetime.utcnow()
            )
        
        if len(data_points) == 1:
            # Single source - return with reduced confidence
            dp = data_points[0]
            source_weight = self.source_weights.get(dp.get('source', 'unknown'), 0.5)
            
            return ConsensusResult(
                value=dp,
                confidence=source_weight * 0.7,  # Reduced confidence for single source
                sources=[dp.get('source', 'unknown')],
                method=method,
                quality=self._assess_quality(source_weight * 0.7),
                timestamp=datetime.utcnow()
            )
        
        # Multiple sources - build consensus
        if method == ConsensusMethod.WEIGHTED_AVERAGE:
            return self._weighted_average_consensus(data_points, tolerance)
        elif method == ConsensusMethod.MEDIAN:
            return self._median_consensus(data_points, tolerance)
        elif method == ConsensusMethod.MAJORITY:
            return self._majority_consensus(data_points, tolerance)
        elif method == ConsensusMethod.BEST_SOURCE:
            return self._best_source_consensus(data_points)
        else:
            raise ValueError(f"Unknown consensus method: {method}")
    
    def _weighted_average_consensus(
        self,
        data_points: List[Dict[str, Any]],
        tolerance: float
    ) -> ConsensusResult:
        """Build consensus using weighted average of sources"""
        
        # Extract numeric fields for consensus
        numeric_fields = ['bid', 'ask', 'last', 'price', 'volume']
        consensus_data = {}
        total_weight = 0.0
        sources = []
        
        # Calculate weighted averages for numeric fields
        for field in numeric_fields:
            weighted_sum = 0.0
            weight_sum = 0.0
            values = []
            
            for dp in data_points:
                if field in dp and dp[field] is not None:
                    source = dp.get('source', 'unknown')
                    weight = self.source_weights.get(source, 0.1)
                    value = float(dp[field])
                    
                    weighted_sum += value * weight
                    weight_sum += weight
                    values.append(value)
                    
                    if source not in sources:
                        sources.append(source)
            
            if weight_sum > 0:
                consensus_data[field] = weighted_sum / weight_sum
                
                # Check variance to assess consensus quality
                if len(values) > 1:
                    mean_val = consensus_data[field]
                    variance = max(abs(v - mean_val) / mean_val for v in values) if mean_val != 0 else 0
                    
                    if variance > tolerance:
                        logger.warning(f"High variance in {field}: {variance:.3f} > {tolerance}")
        
        # Copy non-numeric fields from best source
        best_source = max(sources, key=lambda s: self.source_weights.get(s, 0)) if sources else 'unknown'
        best_dp = next((dp for dp in data_points if dp.get('source') == best_source), data_points[0])
        
        for key, value in best_dp.items():
            if key not in consensus_data and key not in ['source']:
                consensus_data[key] = value
        
        # Calculate confidence based on source weights and agreement
        total_weight = sum(self.source_weights.get(s, 0.1) for s in sources)
        base_confidence = min(total_weight / len(self.source_weights), 1.0)
        
        # Adjust for number of sources (more sources = higher confidence)
        source_bonus = min(len(sources) * 0.1, 0.3)
        final_confidence = min(base_confidence + source_bonus, 1.0)
        
        return ConsensusResult(
            value=consensus_data,
            confidence=final_confidence,
            sources=sources,
            method=ConsensusMethod.WEIGHTED_AVERAGE,
            quality=self._assess_quality(final_confidence),
            timestamp=datetime.utcnow(),
            metadata={
                'total_sources': len(sources),
                'total_weight': total_weight,
                'best_source': best_source
            }
        )
    
    def _median_consensus(
        self,
        data_points: List[Dict[str, Any]],
        tolerance: float
    ) -> ConsensusResult:
        """Build consensus using statistical median"""
        
        numeric_fields = ['bid', 'ask', 'last', 'price', 'volume']
        consensus_data = {}
        sources = [dp.get('source', 'unknown') for dp in data_points]
        
        # Calculate median for numeric fields
        for field in numeric_fields:
            values = []
            for dp in data_points:
                if field in dp and dp[field] is not None:
                    values.append(float(dp[field]))
            
            if values:
                consensus_data[field] = statistics.median(values)
        
        # Use data from median-closest source for non-numeric fields
        if 'last' in consensus_data or 'price' in consensus_data:
            target_price = consensus_data.get('last', consensus_data.get('price'))
            closest_dp = min(
                data_points,
                key=lambda dp: abs(dp.get('last', dp.get('price', 0)) - target_price)
            )
            
            for key, value in closest_dp.items():
                if key not in consensus_data and key not in ['source']:
                    consensus_data[key] = value
        
        # Calculate confidence based on data agreement
        confidence = self._calculate_agreement_confidence(data_points, tolerance)
        
        return ConsensusResult(
            value=consensus_data,
            confidence=confidence,
            sources=sources,
            method=ConsensusMethod.MEDIAN,
            quality=self._assess_quality(confidence),
            timestamp=datetime.utcnow(),
            metadata={'total_sources': len(sources)}
        )
    
    def _majority_consensus(
        self,
        data_points: List[Dict[str, Any]],
        tolerance: float
    ) -> ConsensusResult:
        """Build consensus using majority voting (for discrete values)"""
        
        # Group similar data points
        groups = self._group_similar_data(data_points, tolerance)
        
        # Find largest group
        largest_group = max(groups, key=len) if groups else []
        
        if not largest_group:
            return ConsensusResult(
                value=None,
                confidence=0.0,
                sources=[],
                method=ConsensusMethod.MAJORITY,
                quality=DataQuality.INVALID,
                timestamp=datetime.utcnow()
            )
        
        # Use weighted average within the majority group
        return self._weighted_average_consensus(largest_group, tolerance)
    
    def _best_source_consensus(self, data_points: List[Dict[str, Any]]) -> ConsensusResult:
        """Use data from the highest-quality source only"""
        
        # Find best source
        best_dp = max(
            data_points,
            key=lambda dp: self.source_weights.get(dp.get('source', 'unknown'), 0)
        )
        
        source = best_dp.get('source', 'unknown')
        confidence = self.source_weights.get(source, 0.5)
        
        return ConsensusResult(
            value=best_dp,
            confidence=confidence,
            sources=[source],
            method=ConsensusMethod.BEST_SOURCE,
            quality=self._assess_quality(confidence),
            timestamp=datetime.utcnow(),
            metadata={'selected_source': source}
        )
    
    def _group_similar_data(
        self,
        data_points: List[Dict[str, Any]],
        tolerance: float
    ) -> List[List[Dict[str, Any]]]:
        """Group data points that are similar within tolerance"""
        
        groups = []
        
        for dp in data_points:
            price = dp.get('last', dp.get('price', 0))
            
            # Find existing group this data point belongs to
            assigned = False
            for group in groups:
                group_price = group[0].get('last', group[0].get('price', 0))
                
                if abs(price - group_price) / max(price, group_price, 1) <= tolerance:
                    group.append(dp)
                    assigned = True
                    break
            
            # Create new group if no match found
            if not assigned:
                groups.append([dp])
        
        return groups
    
    def _calculate_agreement_confidence(
        self,
        data_points: List[Dict[str, Any]],
        tolerance: float
    ) -> float:
        """Calculate confidence based on agreement between sources"""
        
        if len(data_points) <= 1:
            return 0.5
        
        # Check price agreement
        prices = []
        for dp in data_points:
            price = dp.get('last', dp.get('price'))
            if price is not None:
                prices.append(float(price))
        
        if len(prices) < 2:
            return 0.3
        
        # Calculate coefficient of variation
        mean_price = statistics.mean(prices)
        if mean_price == 0:
            return 0.3
        
        price_std = statistics.stdev(prices) if len(prices) > 1 else 0
        cv = price_std / mean_price
        
        # Convert CV to confidence (lower CV = higher confidence)
        if cv <= tolerance:
            return 0.95  # Excellent agreement
        elif cv <= tolerance * 2:
            return 0.80  # Good agreement
        elif cv <= tolerance * 5:
            return 0.60  # Fair agreement
        else:
            return 0.30  # Poor agreement
    
    def _assess_quality(self, confidence: float) -> DataQuality:
        """Assess data quality based on confidence score"""
        
        if confidence >= self.quality_thresholds[DataQuality.EXCELLENT]:
            return DataQuality.EXCELLENT
        elif confidence >= self.quality_thresholds[DataQuality.GOOD]:
            return DataQuality.GOOD
        elif confidence >= self.quality_thresholds[DataQuality.FAIR]:
            return DataQuality.FAIR
        elif confidence >= self.quality_thresholds[DataQuality.POOR]:
            return DataQuality.POOR
        else:
            return DataQuality.INVALID


class EnhancedMarketDataAggregator:
    """
    Enhanced market data aggregator with multi-source validation,
    consensus building, and advanced analytics capabilities
    """
    
    def __init__(self):
        self.provider_manager = MarketDataProviderManager()
        self.realtime_manager = RealTimeDataManager()
        self.cache_manager = CacheManager()
        self.validator = DataValidator()
        self.consensus_engine = ConsensusEngine()
        
        # Circuit breakers for aggregation operations
        self.circuit_breakers = {
            'historical_data': CircuitBreaker(failure_threshold=3, timeout=300),
            'real_time_quotes': CircuitBreaker(failure_threshold=5, timeout=60),
            'fundamental_data': CircuitBreaker(failure_threshold=2, timeout=600)
        }
        
        # Performance metrics
        self.metrics = {
            'requests_processed': 0,
            'consensus_agreements': 0,
            'data_quality_failures': 0,
            'circuit_breaker_trips': 0
        }
        
    async def get_consensus_quote(
        self,
        symbol: str,
        method: ConsensusMethod = ConsensusMethod.WEIGHTED_AVERAGE,
        max_sources: int = 5
    ) -> ConsensusResult:
        """
        Get real-time quote with multi-source consensus validation
        
        Args:
            symbol: Stock symbol
            method: Consensus building method
            max_sources: Maximum number of sources to query
        
        Returns:
            ConsensusResult with validated quote data
        """
        
        self.metrics['requests_processed'] += 1
        
        try:
            # Get quotes from multiple sources in parallel
            quote_tasks = []
            
            # Select top providers based on real-time capabilities
            providers = self.provider_manager.select_optimal_provider(
                'real_time_quotes', [symbol]
            )
            
            # Fetch from multiple providers
            available_providers = ['polygon', 'alpaca', 'iex_cloud', 'yahoo'][:max_sources]
            
            for provider in available_providers:
                if provider in self.provider_manager.all_providers:
                    task = self._safe_get_quote(symbol, provider)
                    quote_tasks.append(task)
            
            # Wait for all responses (with timeout)
            quotes = await asyncio.gather(*quote_tasks, return_exceptions=True)
            
            # Filter out exceptions and invalid data
            valid_quotes = []
            for i, quote in enumerate(quotes):
                if not isinstance(quote, Exception) and quote:
                    # Validate quote data
                    is_valid, issues = await self.validator.validate_quote(quote)
                    if is_valid:
                        quote['source'] = available_providers[i]
                        valid_quotes.append(quote)
                    else:
                        logger.warning(f"Invalid quote from {available_providers[i]}: {issues}")
            
            if not valid_quotes:
                logger.error(f"No valid quotes found for {symbol}")
                return ConsensusResult(
                    value=None,
                    confidence=0.0,
                    sources=[],
                    method=method,
                    quality=DataQuality.INVALID,
                    timestamp=datetime.utcnow()
                )
            
            # Detect anomalies
            anomalies = await self.validator.detect_anomalies(valid_quotes, symbol)
            if anomalies:
                logger.warning(f"Detected {len(anomalies)} anomalies in {symbol} quotes")
                for anomaly in anomalies:
                    logger.debug(f"Anomaly: {anomaly['reasons']}")
            
            # Build consensus
            consensus = self.consensus_engine.find_consensus(valid_quotes, method)
            
            if consensus.quality in [DataQuality.EXCELLENT, DataQuality.GOOD]:
                self.metrics['consensus_agreements'] += 1
            else:
                self.metrics['data_quality_failures'] += 1
            
            # Cache the result
            cache_key = f"consensus_quote_{symbol}"
            await self.cache_manager.set(cache_key, consensus, ttl=30)
            
            return consensus
            
        except Exception as e:
            logger.error(f"Error getting consensus quote for {symbol}: {e}")
            self.metrics['data_quality_failures'] += 1
            
            return ConsensusResult(
                value=None,
                confidence=0.0,
                sources=[],
                method=method,
                quality=DataQuality.INVALID,
                timestamp=datetime.utcnow()
            )
    
    async def _safe_get_quote(self, symbol: str, provider: str) -> Optional[Dict[str, Any]]:
        """Safely get quote from provider with circuit breaker protection"""
        
        try:
            return await self.circuit_breakers['real_time_quotes'].call(
                self.provider_manager.get_real_time_quote,
                symbol,
                provider_override=provider
            )
        except Exception as e:
            logger.debug(f"Failed to get quote from {provider}: {e}")
            return None
    
    async def get_enhanced_historical_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d',
        include_fundamentals: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Get enhanced historical data with quality validation and enrichment
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval
            include_fundamentals: Whether to include fundamental data
        
        Returns:
            Dictionary mapping symbols to enhanced DataFrames
        """
        
        result = {}
        
        for symbol in symbols:
            try:
                # Get basic historical data
                df = await self.provider_manager.get_historical_data(
                    [symbol], start_date, end_date, interval
                )
                
                if df.empty:
                    logger.warning(f"No historical data found for {symbol}")
                    continue
                
                # Enhance with technical indicators
                df = self._add_technical_indicators(df)
                
                # Add quality metrics
                df = self._add_quality_metrics(df)
                
                # Include fundamental data if requested
                if include_fundamentals:
                    fundamentals = await self._get_fundamental_ratios(symbol)
                    if fundamentals:
                        # Add fundamental ratios as additional columns
                        for ratio_name, ratio_value in fundamentals.items():
                            if ratio_value is not None:
                                df[f'fundamental_{ratio_name}'] = ratio_value
                
                result[symbol] = df
                
            except Exception as e:
                logger.error(f"Error getting enhanced historical data for {symbol}: {e}")
        
        return result
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to historical data"""
        
        if len(df) < 20:
            return df  # Need sufficient data for indicators
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # Bollinger Bands
        rolling_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['sma_20'] + (rolling_std * 2)
        df['bb_lower'] = df['sma_20'] - (rolling_std * 2)
        
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        return df
    
    def _add_quality_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add data quality metrics to historical data"""
        
        # Price change metrics
        df['daily_return'] = df['close'].pct_change()
        df['volatility_20d'] = df['daily_return'].rolling(window=20).std() * np.sqrt(252)
        
        # Gap detection
        df['gap'] = ((df['open'] - df['close'].shift(1)) / df['close'].shift(1)) * 100
        df['gap_size'] = df['gap'].abs()
        
        # Unusual volume detection
        df['volume_z_score'] = (df['volume'] - df['volume'].rolling(window=20).mean()) / df['volume'].rolling(window=20).std()
        
        # Price consistency checks
        df['intraday_range'] = (df['high'] - df['low']) / df['close'] * 100
        df['price_consistency'] = (
            (df['open'] >= df['low']) & 
            (df['open'] <= df['high']) & 
            (df['close'] >= df['low']) & 
            (df['close'] <= df['high'])
        )
        
        return df
    
    async def _get_fundamental_ratios(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get fundamental ratios for symbol"""
        
        try:
            # Try to get from cache first
            cache_key = f"fundamental_ratios_{symbol}"
            cached = await self.cache_manager.get(cache_key)
            
            if cached:
                return cached
            
            # Get fundamental data from provider
            fundamental_data = await self.provider_manager.get_fundamental_data([symbol])
            
            if not fundamental_data or symbol not in fundamental_data:
                return None
            
            data = fundamental_data[symbol]
            financials = data.get('financials', {})
            
            if not financials:
                return None
            
            # Calculate ratios
            ratios = self.calculate_financial_ratios(financials)
            
            # Cache for 24 hours
            await self.cache_manager.set(cache_key, ratios, ttl=86400)
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error getting fundamental ratios for {symbol}: {e}")
            return None
    
    def calculate_financial_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate comprehensive financial ratios from financial statements
        
        Args:
            financials: Dictionary containing financial statement data
            
        Returns:
            Dictionary of calculated ratios
        """
        
        ratios = {}
        
        try:
            # Income statement items
            revenue = financials.get('revenue', financials.get('total_revenue', 0))
            net_income = financials.get('net_income', 0)
            gross_profit = financials.get('gross_profit', 0)
            operating_income = financials.get('operating_income', 0)
            ebit = financials.get('ebit', operating_income)
            interest_expense = financials.get('interest_expense', 0)
            
            # Balance sheet items
            total_assets = financials.get('total_assets', 0)
            current_assets = financials.get('current_assets', 0)
            inventory = financials.get('inventory', 0)
            cash = financials.get('cash_and_equivalents', 0)
            
            current_liabilities = financials.get('current_liabilities', 0)
            total_debt = financials.get('total_debt', 0)
            total_liabilities = financials.get('total_liabilities', 0)
            shareholders_equity = financials.get('shareholders_equity', 0)
            
            # Market data (if available)
            shares_outstanding = financials.get('shares_outstanding', 0)
            market_cap = financials.get('market_cap', 0)
            
            # Calculate ratios with safe division
            def safe_divide(numerator, denominator, default=None):
                if denominator != 0 and denominator is not None:
                    return numerator / denominator
                return default
            
            # Profitability ratios
            ratios['roe'] = safe_divide(net_income, shareholders_equity)  # Return on Equity
            ratios['roa'] = safe_divide(net_income, total_assets)  # Return on Assets
            ratios['profit_margin'] = safe_divide(net_income, revenue)  # Net Profit Margin
            ratios['gross_margin'] = safe_divide(gross_profit, revenue)  # Gross Margin
            ratios['operating_margin'] = safe_divide(operating_income, revenue)  # Operating Margin
            
            # Liquidity ratios
            ratios['current_ratio'] = safe_divide(current_assets, current_liabilities)
            ratios['quick_ratio'] = safe_divide(current_assets - inventory, current_liabilities)
            ratios['cash_ratio'] = safe_divide(cash, current_liabilities)
            
            # Leverage ratios
            ratios['debt_to_equity'] = safe_divide(total_debt, shareholders_equity)
            ratios['debt_to_assets'] = safe_divide(total_debt, total_assets)
            ratios['interest_coverage'] = safe_divide(ebit, interest_expense)
            
            # Efficiency ratios
            ratios['asset_turnover'] = safe_divide(revenue, total_assets)
            
            # Additional calculations if we have historical data
            if 'previous_year' in financials:
                prev = financials['previous_year']
                prev_inventory = prev.get('inventory', inventory)
                prev_assets = prev.get('total_assets', total_assets)
                
                avg_inventory = (inventory + prev_inventory) / 2
                avg_assets = (total_assets + prev_assets) / 2
                
                cogs = revenue - gross_profit  # Cost of goods sold
                ratios['inventory_turnover'] = safe_divide(cogs, avg_inventory)
                ratios['asset_turnover'] = safe_divide(revenue, avg_assets)  # Update with average
            
            # Valuation ratios (if market data available)
            if market_cap and shares_outstanding:
                price_per_share = market_cap / shares_outstanding
                earnings_per_share = safe_divide(net_income, shares_outstanding)
                book_value_per_share = safe_divide(shareholders_equity, shares_outstanding)
                
                ratios['pe_ratio'] = safe_divide(price_per_share, earnings_per_share)
                ratios['pb_ratio'] = safe_divide(price_per_share, book_value_per_share)
                ratios['price_to_sales'] = safe_divide(market_cap, revenue)
            
            # Filter out None values
            ratios = {k: v for k, v in ratios.items() if v is not None}
            
            # Round to reasonable precision
            for key, value in ratios.items():
                if isinstance(value, float):
                    ratios[key] = round(value, 4)
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios: {e}")
        
        return ratios
    
    async def get_market_sentiment_analysis(
        self,
        symbols: List[str],
        timeframe: str = '1d'
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze market sentiment for symbols using multiple data sources
        
        Args:
            symbols: List of stock symbols
            timeframe: Analysis timeframe
        
        Returns:
            Dictionary of sentiment analysis results
        """
        
        sentiment_results = {}
        
        for symbol in symbols:
            try:
                sentiment = {
                    'symbol': symbol,
                    'timestamp': datetime.utcnow(),
                    'timeframe': timeframe
                }
                
                # Get recent quotes for trend analysis
                recent_quotes = []
                for _ in range(10):  # Get 10 recent quotes
                    quote_result = await self.get_consensus_quote(symbol)
                    if quote_result.value:
                        recent_quotes.append(quote_result.value)
                    await asyncio.sleep(1)  # Wait 1 second between quotes
                
                if len(recent_quotes) >= 3:
                    # Analyze price trend
                    prices = [q.get('last', q.get('price', 0)) for q in recent_quotes]
                    
                    # Price momentum
                    if len(prices) >= 2:
                        price_change = (prices[-1] - prices[0]) / prices[0] * 100
                        sentiment['price_momentum'] = price_change
                        
                        if price_change > 2:
                            sentiment['price_sentiment'] = 'bullish'
                        elif price_change < -2:
                            sentiment['price_sentiment'] = 'bearish'
                        else:
                            sentiment['price_sentiment'] = 'neutral'
                    
                    # Volatility analysis
                    price_returns = [
                        (prices[i] - prices[i-1]) / prices[i-1] * 100 
                        for i in range(1, len(prices))
                    ]
                    
                    if price_returns:
                        volatility = np.std(price_returns)
                        sentiment['volatility'] = volatility
                        
                        if volatility > 3:
                            sentiment['volatility_sentiment'] = 'high'
                        elif volatility > 1:
                            sentiment['volatility_sentiment'] = 'medium'
                        else:
                            sentiment['volatility_sentiment'] = 'low'
                
                # Volume analysis (if available)
                volumes = [q.get('volume', 0) for q in recent_quotes if q.get('volume')]
                if volumes and len(volumes) >= 3:
                    avg_volume = np.mean(volumes)
                    latest_volume = volumes[-1]
                    volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1
                    
                    sentiment['volume_ratio'] = volume_ratio
                    if volume_ratio > 2:
                        sentiment['volume_sentiment'] = 'high_activity'
                    elif volume_ratio > 1.2:
                        sentiment['volume_sentiment'] = 'elevated'
                    else:
                        sentiment['volume_sentiment'] = 'normal'
                
                # Overall sentiment score (simple weighted average)
                sentiment_score = 0
                weight_sum = 0
                
                if 'price_momentum' in sentiment:
                    # Normalize price momentum to -1 to 1 range
                    momentum_score = np.tanh(sentiment['price_momentum'] / 10)
                    sentiment_score += momentum_score * 0.5
                    weight_sum += 0.5
                
                if 'volume_ratio' in sentiment:
                    # Higher volume generally indicates stronger conviction
                    volume_score = min(sentiment['volume_ratio'] / 2, 1) - 0.5
                    sentiment_score += volume_score * 0.3
                    weight_sum += 0.3
                
                if weight_sum > 0:
                    sentiment['overall_score'] = sentiment_score / weight_sum
                    
                    if sentiment['overall_score'] > 0.2:
                        sentiment['overall_sentiment'] = 'bullish'
                    elif sentiment['overall_score'] < -0.2:
                        sentiment['overall_sentiment'] = 'bearish'
                    else:
                        sentiment['overall_sentiment'] = 'neutral'
                
                sentiment_results[symbol] = sentiment
                
            except Exception as e:
                logger.error(f"Error analyzing sentiment for {symbol}: {e}")
                sentiment_results[symbol] = {
                    'symbol': symbol,
                    'error': str(e),
                    'timestamp': datetime.utcnow()
                }
        
        return sentiment_results
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get aggregator performance metrics"""
        
        return {
            'metrics': self.metrics.copy(),
            'circuit_breaker_status': {
                name: {
                    'state': cb.state,
                    'failure_count': cb.failure_count,
                    'last_failure': cb.last_failure_time
                }
                for name, cb in self.circuit_breakers.items()
            },
            'provider_status': await self.provider_manager.get_provider_status(),
            'cache_stats': await self.cache_manager.get_stats(),
            'consensus_engine_weights': self.consensus_engine.source_weights,
            'timestamp': datetime.utcnow()
        }


# Global instance for use throughout the application
market_data_aggregator = EnhancedMarketDataAggregator()