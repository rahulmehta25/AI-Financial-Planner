"""
Market Data Quality Validator

Unified entry point for data quality validation with comprehensive
anomaly detection, cross-provider validation, and data integrity checks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
from enum import Enum
import statistics
from decimal import Decimal

from .models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from .storage.data_validator import DataValidator as StorageDataValidator
from .config import config


class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self):
        self.is_valid = True
        self.issues = []
        self.warnings = []
        self.errors = []
        self.metadata = {}
        self.validated_data = []
    
    def add_issue(self, message: str, severity: ValidationSeverity, context: Dict[str, Any] = None):
        """Add a validation issue"""
        issue = {
            'message': message,
            'severity': severity.value,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context or {}
        }
        
        self.issues.append(issue)
        
        if severity == ValidationSeverity.WARNING:
            self.warnings.append(issue)
        elif severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.errors.append(issue)
            self.is_valid = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        return {
            'is_valid': self.is_valid,
            'total_issues': len(self.issues),
            'warnings': len(self.warnings),
            'errors': len(self.errors),
            'validated_items': len(self.validated_data)
        }


class MarketDataQualityValidator:
    """Comprehensive market data quality validator"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.quality_validator")
        self.storage_validator = StorageDataValidator()
        
        # Statistical tracking for anomaly detection
        self.price_history = defaultdict(list)  # symbol -> recent prices
        self.volume_history = defaultdict(list)  # symbol -> recent volumes
        self.volatility_history = defaultdict(list)  # symbol -> recent volatility
        
        # Cross-provider comparison data
        self.provider_data_cache = defaultdict(dict)  # symbol -> provider -> recent data
        
        # Validation configuration
        self.max_price_change_threshold = config.max_price_change_percent or 20  # 20%
        self.max_volume_spike_threshold = 10  # 10x average volume
        self.min_data_freshness_minutes = 15
        self.max_provider_discrepancy_percent = 5  # 5%
        
        # Historical context window
        self.history_window_size = 100
        
        # Validation statistics
        self.stats = {
            'validations_performed': 0,
            'data_points_validated': 0,
            'anomalies_detected': 0,
            'cross_provider_discrepancies': 0,
            'data_quality_score': 100.0
        }
    
    async def validate_quote(self, quote: MarketDataPoint, compare_providers: bool = True) -> ValidationResult:
        """Comprehensive quote validation with anomaly detection"""
        result = ValidationResult()
        
        try:
            self.stats['validations_performed'] += 1
            self.stats['data_points_validated'] += 1
            
            # Basic validation using storage validator
            is_valid, errors = self.storage_validator.validate_market_data_point(quote)
            
            for error in errors:
                result.add_issue(
                    f"Basic validation error: {error}",
                    ValidationSeverity.ERROR,
                    {'symbol': quote.symbol, 'provider': quote.provider.value if quote.provider else None}
                )
            
            if is_valid:
                result.validated_data.append(quote)
            
            # Advanced anomaly detection
            await self._detect_price_anomalies(quote, result)
            await self._detect_volume_anomalies(quote, result)
            await self._detect_timing_anomalies(quote, result)
            
            # Data freshness check
            self._validate_data_freshness(quote, result)
            
            # Cross-provider validation if requested
            if compare_providers:
                await self._validate_cross_provider_consistency(quote, result)
            
            # Update historical tracking
            self._update_historical_tracking(quote)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(result)
            result.metadata['quality_score'] = quality_score
            
        except Exception as e:
            self.logger.error(f"Error validating quote for {quote.symbol}: {e}")
            result.add_issue(
                f"Validation system error: {str(e)}",
                ValidationSeverity.CRITICAL,
                {'symbol': quote.symbol}
            )
        
        return result
    
    async def validate_historical_data(self, historical: HistoricalData) -> ValidationResult:
        """Comprehensive historical data validation"""
        result = ValidationResult()
        
        try:
            self.stats['validations_performed'] += 1
            
            # Basic validation using storage validator
            is_valid, errors, valid_points = self.storage_validator.validate_historical_data(historical)
            
            for error in errors:
                result.add_issue(
                    f"Historical validation error: {error}",
                    ValidationSeverity.ERROR,
                    {'symbol': historical.symbol, 'provider': historical.provider.value if historical.provider else None}
                )
            
            result.validated_data = valid_points
            self.stats['data_points_validated'] += len(valid_points)
            
            # Advanced historical analysis
            if valid_points:
                await self._analyze_price_patterns(valid_points, result)
                await self._detect_data_gaps(valid_points, historical.interval, result)
                await self._validate_ohlc_relationships(valid_points, result)
                await self._detect_outliers_in_sequence(valid_points, result)
            
            # Calculate completeness score
            if historical.data_points:
                completeness = len(valid_points) / len(historical.data_points)
                result.metadata['completeness'] = completeness
                
                if completeness < 0.8:
                    result.add_issue(
                        f"Low data completeness: {completeness:.1%}",
                        ValidationSeverity.WARNING,
                        {'expected': len(historical.data_points), 'valid': len(valid_points)}
                    )
            
        except Exception as e:
            self.logger.error(f"Error validating historical data for {historical.symbol}: {e}")
            result.add_issue(
                f"Historical validation system error: {str(e)}",
                ValidationSeverity.CRITICAL,
                {'symbol': historical.symbol}
            )
        
        return result
    
    async def validate_company_info(self, company_info: CompanyInfo) -> ValidationResult:
        """Validate company information data"""
        result = ValidationResult()
        
        try:
            self.stats['validations_performed'] += 1
            self.stats['data_points_validated'] += 1
            
            # Basic field validation
            if not company_info.symbol:
                result.add_issue("Symbol is required", ValidationSeverity.ERROR)
            
            if not company_info.name:
                result.add_issue("Company name is required", ValidationSeverity.WARNING, 
                               {'symbol': company_info.symbol})
            
            # Financial metrics validation
            if company_info.market_cap is not None:
                if company_info.market_cap < 0:
                    result.add_issue("Market cap cannot be negative", ValidationSeverity.ERROR,
                                   {'symbol': company_info.symbol, 'market_cap': company_info.market_cap})
                elif company_info.market_cap > 10e12:  # $10 trillion
                    result.add_issue("Market cap seems unreasonably high", ValidationSeverity.WARNING,
                                   {'symbol': company_info.symbol, 'market_cap': company_info.market_cap})
            
            if company_info.pe_ratio is not None:
                if company_info.pe_ratio < 0:
                    result.add_issue("P/E ratio cannot be negative", ValidationSeverity.ERROR,
                                   {'symbol': company_info.symbol, 'pe_ratio': company_info.pe_ratio})
                elif company_info.pe_ratio > 1000:
                    result.add_issue("P/E ratio seems unreasonably high", ValidationSeverity.WARNING,
                                   {'symbol': company_info.symbol, 'pe_ratio': company_info.pe_ratio})
            
            if company_info.dividend_yield is not None:
                if company_info.dividend_yield < 0:
                    result.add_issue("Dividend yield cannot be negative", ValidationSeverity.ERROR,
                                   {'symbol': company_info.symbol, 'dividend_yield': company_info.dividend_yield})
                elif company_info.dividend_yield > 0.5:  # 50%
                    result.add_issue("Dividend yield seems unreasonably high", ValidationSeverity.WARNING,
                                   {'symbol': company_info.symbol, 'dividend_yield': company_info.dividend_yield})
            
            if result.is_valid:
                result.validated_data.append(company_info)
            
        except Exception as e:
            self.logger.error(f"Error validating company info for {company_info.symbol}: {e}")
            result.add_issue(
                f"Company info validation error: {str(e)}",
                ValidationSeverity.CRITICAL,
                {'symbol': company_info.symbol}
            )
        
        return result
    
    async def _detect_price_anomalies(self, quote: MarketDataPoint, result: ValidationResult):
        """Detect price-based anomalies"""
        symbol = quote.symbol
        current_price = quote.price
        
        if not current_price or current_price <= 0:
            return
        
        # Get historical price data for comparison
        historical_prices = self.price_history.get(symbol, [])
        
        if len(historical_prices) >= 5:  # Need at least 5 data points
            # Calculate recent average and standard deviation
            avg_price = statistics.mean(historical_prices)
            if len(historical_prices) > 1:
                price_std = statistics.stdev(historical_prices)
                
                # Z-score based anomaly detection
                z_score = abs(current_price - avg_price) / price_std if price_std > 0 else 0
                
                if z_score > 3:  # 3 standard deviations
                    self.stats['anomalies_detected'] += 1
                    result.add_issue(
                        f"Extreme price deviation detected: {z_score:.2f} standard deviations from mean",
                        ValidationSeverity.WARNING,
                        {
                            'symbol': symbol,
                            'current_price': current_price,
                            'mean_price': avg_price,
                            'z_score': z_score
                        }
                    )
                
                # Percentage change from recent average
                price_change_percent = abs((current_price - avg_price) / avg_price) * 100
                
                if price_change_percent > self.max_price_change_threshold:
                    self.stats['anomalies_detected'] += 1
                    result.add_issue(
                        f"Large price change detected: {price_change_percent:.2f}% from recent average",
                        ValidationSeverity.WARNING,
                        {
                            'symbol': symbol,
                            'price_change_percent': price_change_percent,
                            'threshold': self.max_price_change_threshold
                        }
                    )
    
    async def _detect_volume_anomalies(self, quote: MarketDataPoint, result: ValidationResult):
        """Detect volume-based anomalies"""
        symbol = quote.symbol
        current_volume = quote.volume
        
        if not current_volume or current_volume <= 0:
            return
        
        historical_volumes = self.volume_history.get(symbol, [])
        
        if len(historical_volumes) >= 5:
            avg_volume = statistics.mean(historical_volumes)
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                
                if volume_ratio > self.max_volume_spike_threshold:
                    self.stats['anomalies_detected'] += 1
                    result.add_issue(
                        f"Volume spike detected: {volume_ratio:.1f}x average volume",
                        ValidationSeverity.WARNING,
                        {
                            'symbol': symbol,
                            'current_volume': current_volume,
                            'average_volume': avg_volume,
                            'volume_ratio': volume_ratio
                        }
                    )
    
    async def _detect_timing_anomalies(self, quote: MarketDataPoint, result: ValidationResult):
        """Detect timing-based anomalies"""
        if not quote.timestamp:
            return
        
        now = datetime.utcnow()
        
        # Check for stale data
        age_minutes = (now - quote.timestamp).total_seconds() / 60
        
        if age_minutes > self.min_data_freshness_minutes:
            result.add_issue(
                f"Stale data detected: {age_minutes:.1f} minutes old",
                ValidationSeverity.WARNING,
                {
                    'symbol': quote.symbol,
                    'data_age_minutes': age_minutes,
                    'freshness_threshold': self.min_data_freshness_minutes
                }
            )
        
        # Check for future timestamps
        if quote.timestamp > now + timedelta(minutes=5):
            result.add_issue(
                f"Future timestamp detected: {quote.timestamp}",
                ValidationSeverity.ERROR,
                {'symbol': quote.symbol, 'timestamp': quote.timestamp.isoformat()}
            )
    
    def _validate_data_freshness(self, quote: MarketDataPoint, result: ValidationResult):
        """Validate data freshness"""
        if not quote.timestamp:
            result.add_issue(
                "Missing timestamp",
                ValidationSeverity.ERROR,
                {'symbol': quote.symbol}
            )
            return
        
        now = datetime.utcnow()
        age = now - quote.timestamp
        
        # Market hours consideration (simplified - assumes US market hours)
        market_hours = self._is_market_hours(now)
        
        if market_hours and age.total_seconds() > 300:  # 5 minutes during market hours
            result.add_issue(
                f"Data may be stale during market hours: {age.total_seconds():.0f}s old",
                ValidationSeverity.WARNING,
                {'symbol': quote.symbol, 'age_seconds': age.total_seconds()}
            )
    
    def _is_market_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during market hours (simplified)"""
        # US market hours: 9:30 AM - 4:00 PM ET (simplified, no holidays)
        weekday = timestamp.weekday()
        hour = timestamp.hour
        
        return weekday < 5 and 14 <= hour < 21  # Assuming UTC time
    
    async def _validate_cross_provider_consistency(self, quote: MarketDataPoint, result: ValidationResult):
        """Validate consistency across providers"""
        symbol = quote.symbol
        provider = quote.provider
        
        # Store current provider data
        self.provider_data_cache[symbol][provider] = {
            'price': quote.price,
            'timestamp': quote.timestamp,
            'volume': quote.volume
        }
        
        # Compare with other providers
        other_providers = {p: data for p, data in self.provider_data_cache[symbol].items() if p != provider}
        
        for other_provider, other_data in other_providers.items():
            if not other_data.get('price') or not quote.price:
                continue
            
            # Check timestamp proximity (within 5 minutes)
            time_diff = abs((quote.timestamp - other_data['timestamp']).total_seconds())
            if time_diff > 300:  # 5 minutes
                continue
            
            # Calculate price discrepancy
            price_diff_percent = abs(quote.price - other_data['price']) / other_data['price'] * 100
            
            if price_diff_percent > self.max_provider_discrepancy_percent:
                self.stats['cross_provider_discrepancies'] += 1
                result.add_issue(
                    f"Cross-provider price discrepancy: {price_diff_percent:.2f}% difference with {other_provider.value}",
                    ValidationSeverity.WARNING,
                    {
                        'symbol': symbol,
                        'provider1': provider.value,
                        'provider2': other_provider.value,
                        'price1': quote.price,
                        'price2': other_data['price'],
                        'discrepancy_percent': price_diff_percent
                    }
                )
    
    def _update_historical_tracking(self, quote: MarketDataPoint):
        """Update historical data tracking for anomaly detection"""
        symbol = quote.symbol
        
        if quote.price and quote.price > 0:
            self.price_history[symbol].append(quote.price)
            if len(self.price_history[symbol]) > self.history_window_size:
                self.price_history[symbol].pop(0)
        
        if quote.volume and quote.volume > 0:
            self.volume_history[symbol].append(quote.volume)
            if len(self.volume_history[symbol]) > self.history_window_size:
                self.volume_history[symbol].pop(0)
    
    async def _analyze_price_patterns(self, data_points: List[MarketDataPoint], result: ValidationResult):
        """Analyze price patterns in historical data"""
        if len(data_points) < 10:
            return
        
        prices = [dp.price for dp in data_points if dp.price and dp.price > 0]
        if len(prices) < 10:
            return
        
        # Calculate volatility
        if len(prices) > 1:
            returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0
            
            # Extremely high volatility warning
            if volatility > 0.1:  # 10% daily volatility
                result.add_issue(
                    f"High volatility detected: {volatility:.2%} daily volatility",
                    ValidationSeverity.WARNING,
                    {
                        'symbol': data_points[0].symbol,
                        'volatility': volatility,
                        'data_points': len(prices)
                    }
                )
    
    async def _detect_data_gaps(self, data_points: List[MarketDataPoint], interval: str, result: ValidationResult):
        """Detect gaps in time series data"""
        if len(data_points) < 2:
            return
        
        # Expected interval in seconds
        interval_seconds = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '1d': 86400,
            '1w': 604800,
            '1M': 2592000
        }.get(interval, 86400)
        
        sorted_points = sorted(data_points, key=lambda x: x.timestamp)
        
        for i in range(1, len(sorted_points)):
            time_diff = (sorted_points[i].timestamp - sorted_points[i-1].timestamp).total_seconds()
            
            # Allow for some flexibility in timing
            if time_diff > interval_seconds * 1.5:
                result.add_issue(
                    f"Data gap detected: {time_diff/60:.1f} minutes between data points",
                    ValidationSeverity.WARNING,
                    {
                        'symbol': sorted_points[0].symbol,
                        'gap_minutes': time_diff / 60,
                        'expected_interval': interval
                    }
                )
    
    async def _validate_ohlc_relationships(self, data_points: List[MarketDataPoint], result: ValidationResult):
        """Validate OHLC price relationships"""
        for dp in data_points:
            if not all([dp.open_price, dp.high_price, dp.low_price, dp.price]):
                continue
            
            # High should be >= max(open, close)
            if dp.high_price < max(dp.open_price, dp.price):
                result.add_issue(
                    f"Invalid OHLC: High ({dp.high_price}) < max(Open, Close)",
                    ValidationSeverity.ERROR,
                    {'symbol': dp.symbol, 'timestamp': dp.timestamp.isoformat()}
                )
            
            # Low should be <= min(open, close)
            if dp.low_price > min(dp.open_price, dp.price):
                result.add_issue(
                    f"Invalid OHLC: Low ({dp.low_price}) > min(Open, Close)",
                    ValidationSeverity.ERROR,
                    {'symbol': dp.symbol, 'timestamp': dp.timestamp.isoformat()}
                )
    
    async def _detect_outliers_in_sequence(self, data_points: List[MarketDataPoint], result: ValidationResult):
        """Detect statistical outliers in price sequence"""
        prices = [dp.price for dp in data_points if dp.price and dp.price > 0]
        
        if len(prices) < 10:
            return
        
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0
        
        if std_price == 0:
            return
        
        outliers = []
        for i, price in enumerate(prices):
            z_score = abs(price - mean_price) / std_price
            if z_score > 3:  # 3 standard deviations
                outliers.append((i, price, z_score))
        
        if outliers:
            result.add_issue(
                f"Statistical outliers detected: {len(outliers)} data points with z-score > 3",
                ValidationSeverity.WARNING,
                {
                    'symbol': data_points[0].symbol,
                    'outliers_count': len(outliers),
                    'total_points': len(prices),
                    'outlier_details': [{'index': i, 'price': p, 'z_score': z} for i, p, z in outliers[:5]]  # First 5
                }
            )
    
    def _calculate_quality_score(self, result: ValidationResult) -> float:
        """Calculate overall data quality score (0-100)"""
        base_score = 100.0
        
        # Deduct points for issues
        for issue in result.issues:
            if issue['severity'] == 'critical':
                base_score -= 25
            elif issue['severity'] == 'error':
                base_score -= 10
            elif issue['severity'] == 'warning':
                base_score -= 2
        
        return max(0.0, base_score)
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        return {
            **self.stats,
            'storage_validator_stats': self.storage_validator.get_validation_stats(),
            'tracked_symbols': {
                'price_history': len(self.price_history),
                'volume_history': len(self.volume_history),
                'provider_cache': len(self.provider_data_cache)
            }
        }
    
    def clear_historical_data(self, symbol: Optional[str] = None):
        """Clear historical tracking data"""
        if symbol:
            symbol = symbol.upper()
            self.price_history.pop(symbol, None)
            self.volume_history.pop(symbol, None)
            self.provider_data_cache.pop(symbol, None)
        else:
            self.price_history.clear()
            self.volume_history.clear()
            self.provider_data_cache.clear()
        
        self.logger.info(f"Cleared historical data for {'all symbols' if not symbol else symbol}")


# Global validator instance
market_data_validator = MarketDataQualityValidator()