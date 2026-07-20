"""
Advanced Data Quality Validation System

Comprehensive data validation with outlier detection, cross-provider validation,
statistical analysis, and automated data quality scoring.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass, field
import statistics
from scipy import stats
import json

from .models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from .config import config


class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationRule(Enum):
    """Types of validation rules"""
    PRICE_RANGE = "price_range"
    PRICE_VOLATILITY = "price_volatility"
    VOLUME_RANGE = "volume_range"
    VOLUME_ANOMALY = "volume_anomaly"
    OHLC_CONSISTENCY = "ohlc_consistency"
    TIMESTAMP_CONTINUITY = "timestamp_continuity"
    CROSS_PROVIDER_CONSISTENCY = "cross_provider_consistency"
    STATISTICAL_OUTLIER = "statistical_outlier"
    BUSINESS_LOGIC = "business_logic"
    DATA_COMPLETENESS = "data_completeness"


@dataclass
class ValidationIssue:
    """Data validation issue"""
    rule: ValidationRule
    severity: ValidationSeverity
    message: str
    symbol: str
    timestamp: Optional[datetime] = None
    provider: Optional[DataProvider] = None
    data_point: Optional[Dict[str, Any]] = None
    suggested_fix: Optional[str] = None
    confidence_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            'rule': self.rule.value,
            'severity': self.severity.value,
            'message': self.message,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'provider': self.provider.value if self.provider else None,
            'data_point': self.data_point,
            'suggested_fix': self.suggested_fix,
            'confidence_score': self.confidence_score,
            'created_at': datetime.utcnow().isoformat()
        }


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    symbol: str
    validation_timestamp: datetime
    total_data_points: int
    issues: List[ValidationIssue] = field(default_factory=list)
    quality_score: float = 1.0
    provider_scores: Dict[DataProvider, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues by severity level"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get critical issues that require immediate attention"""
        return self.get_issues_by_severity(ValidationSeverity.CRITICAL)
    
    def calculate_quality_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive quality metrics"""
        if not self.issues:
            return {'overall_score': 1.0, 'completeness': 1.0, 'accuracy': 1.0, 'consistency': 1.0}
        
        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.INFO: 0.1,
            ValidationSeverity.WARNING: 0.3,
            ValidationSeverity.ERROR: 0.7,
            ValidationSeverity.CRITICAL: 1.0
        }
        
        total_penalty = sum(severity_weights[issue.severity] for issue in self.issues)
        max_penalty = len(self.issues)  # If all issues were critical
        
        accuracy_score = max(0.0, 1.0 - (total_penalty / max_penalty)) if max_penalty > 0 else 1.0
        
        # Calculate completeness (data availability)
        completeness_score = 1.0 - len([i for i in self.issues if i.rule == ValidationRule.DATA_COMPLETENESS]) / max(1, len(self.issues))
        
        # Calculate consistency (cross-provider agreement)
        consistency_score = 1.0 - len([i for i in self.issues if i.rule == ValidationRule.CROSS_PROVIDER_CONSISTENCY]) / max(1, len(self.issues))
        
        overall_score = (accuracy_score + completeness_score + consistency_score) / 3.0
        
        return {
            'overall_score': overall_score,
            'completeness': completeness_score,
            'accuracy': accuracy_score,
            'consistency': consistency_score
        }


class StatisticalAnalyzer:
    """Statistical analysis for data validation"""
    
    @staticmethod
    def detect_price_outliers(prices: List[float], method: str = 'iqr', threshold: float = 1.5) -> List[int]:
        """Detect price outliers using various methods"""
        if len(prices) < 4:
            return []
        
        prices_array = np.array(prices)
        outlier_indices = []
        
        if method == 'iqr':
            Q1 = np.percentile(prices_array, 25)
            Q3 = np.percentile(prices_array, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            outlier_indices = [i for i, price in enumerate(prices) 
                             if price < lower_bound or price > upper_bound]
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(prices_array))
            outlier_indices = [i for i, z in enumerate(z_scores) if z > threshold]
        
        elif method == 'modified_zscore':
            median = np.median(prices_array)
            mad = np.median(np.abs(prices_array - median))
            modified_z_scores = 0.6745 * (prices_array - median) / mad
            outlier_indices = [i for i, z in enumerate(modified_z_scores) if abs(z) > threshold]
        
        return outlier_indices
    
    @staticmethod
    def detect_volume_anomalies(volumes: List[int], window: int = 20, threshold: float = 3.0) -> List[int]:
        """Detect volume anomalies using rolling statistics"""
        if len(volumes) < window:
            return []
        
        volumes_series = pd.Series(volumes)
        rolling_mean = volumes_series.rolling(window=window).mean()
        rolling_std = volumes_series.rolling(window=window).std()
        
        anomaly_indices = []
        for i in range(window, len(volumes)):
            if rolling_std.iloc[i] > 0:
                z_score = abs(volumes[i] - rolling_mean.iloc[i]) / rolling_std.iloc[i]
                if z_score > threshold:
                    anomaly_indices.append(i)
        
        return anomaly_indices
    
    @staticmethod
    def calculate_price_volatility(prices: List[float], window: int = 20) -> List[float]:
        """Calculate rolling price volatility"""
        if len(prices) < window:
            return []
        
        prices_series = pd.Series(prices)
        returns = prices_series.pct_change().dropna()
        volatility = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
        
        return volatility.tolist()
    
    @staticmethod
    def detect_price_gaps(prices: List[float], timestamps: List[datetime], gap_threshold: float = 0.05) -> List[int]:
        """Detect significant price gaps between consecutive periods"""
        gaps = []
        
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                price_change = abs(prices[i] - prices[i-1]) / prices[i-1]
                if price_change > gap_threshold:
                    gaps.append(i)
        
        return gaps


class CrossProviderValidator:
    """Cross-provider data consistency validation"""
    
    def __init__(self, tolerance_threshold: float = 0.02):
        self.tolerance_threshold = tolerance_threshold  # 2% default tolerance
        self.provider_reliability_scores = defaultdict(float)
    
    def validate_price_consistency(
        self, 
        provider_data: Dict[DataProvider, List[MarketDataPoint]]
    ) -> List[ValidationIssue]:
        """Validate price consistency across providers"""
        issues = []
        
        if len(provider_data) < 2:
            return issues  # Need at least 2 providers for comparison
        
        # Group data by timestamp for comparison
        timestamp_groups = defaultdict(lambda: defaultdict(list))
        
        for provider, data_points in provider_data.items():
            for point in data_points:
                if point.price and point.timestamp:
                    # Group by minute for comparison
                    minute_key = point.timestamp.replace(second=0, microsecond=0)
                    timestamp_groups[minute_key][provider].append(point)
        
        # Compare prices at each timestamp
        for timestamp, provider_points in timestamp_groups.items():
            if len(provider_points) >= 2:
                prices = {}
                for provider, points in provider_points.items():
                    if points:
                        # Use the most recent price in the minute
                        latest_point = max(points, key=lambda x: x.timestamp)
                        prices[provider] = latest_point.price
                
                if len(prices) >= 2:
                    issues.extend(self._compare_provider_prices(prices, timestamp))
        
        return issues
    
    def _compare_provider_prices(
        self, 
        prices: Dict[DataProvider, float], 
        timestamp: datetime
    ) -> List[ValidationIssue]:
        """Compare prices from different providers"""
        issues = []
        
        price_values = list(prices.values())
        if len(price_values) < 2:
            return issues
        
        # Calculate price spread
        min_price = min(price_values)
        max_price = max(price_values)
        
        if min_price > 0:
            spread_ratio = (max_price - min_price) / min_price
            
            if spread_ratio > self.tolerance_threshold:
                # Identify outlier providers
                median_price = statistics.median(price_values)
                
                for provider, price in prices.items():
                    deviation = abs(price - median_price) / median_price
                    
                    if deviation > self.tolerance_threshold:
                        severity = ValidationSeverity.WARNING
                        if deviation > self.tolerance_threshold * 3:
                            severity = ValidationSeverity.ERROR
                        
                        issues.append(ValidationIssue(
                            rule=ValidationRule.CROSS_PROVIDER_CONSISTENCY,
                            severity=severity,
                            message=f"Price deviation from median: {deviation:.2%}",
                            symbol="",  # Would need to be passed from context
                            timestamp=timestamp,
                            provider=provider,
                            data_point={'price': price, 'median_price': median_price, 'deviation': deviation},
                            suggested_fix=f"Verify {provider} data quality",
                            confidence_score=min(1.0, deviation / self.tolerance_threshold)
                        ))
        
        return issues
    
    def update_provider_reliability(self, provider: DataProvider, accuracy_score: float):
        """Update provider reliability score based on validation results"""
        # Use exponential weighted moving average
        alpha = 0.1  # Learning rate
        current_score = self.provider_reliability_scores[provider]
        self.provider_reliability_scores[provider] = alpha * accuracy_score + (1 - alpha) * current_score


class DataQualityValidator:
    """Comprehensive data quality validation system"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.validator")
        self.statistical_analyzer = StatisticalAnalyzer()
        self.cross_provider_validator = CrossProviderValidator()
        
        # Validation thresholds
        self.thresholds = {
            'min_price': 0.01,
            'max_price': 1000000.0,
            'min_volume': 0,
            'max_volume': 1e12,
            'max_price_change': 0.5,  # 50% max single-period change
            'max_volatility': 5.0,    # 500% annualized volatility
            'timestamp_gap_tolerance': timedelta(hours=24),  # Max gap between data points
            'ohlc_tolerance': 0.001   # 0.1% tolerance for OHLC consistency
        }
        
        # Historical data for context
        self.symbol_history = defaultdict(lambda: deque(maxlen=1000))
        self.validation_history = defaultdict(lambda: deque(maxlen=100))
    
    async def validate_market_data_point(
        self, 
        data_point: MarketDataPoint, 
        context_data: Optional[List[MarketDataPoint]] = None
    ) -> ValidationReport:
        """Validate a single market data point with context"""
        report = ValidationReport(
            symbol=data_point.symbol,
            validation_timestamp=datetime.utcnow(),
            total_data_points=1
        )
        
        # Basic validation
        report.issues.extend(self._validate_basic_constraints(data_point))
        
        # OHLC consistency validation
        if all([data_point.open_price, data_point.high_price, 
                data_point.low_price, data_point.price]):
            report.issues.extend(self._validate_ohlc_consistency(data_point))
        
        # Context-based validation
        if context_data:
            report.issues.extend(self._validate_with_context(data_point, context_data))
        
        # Statistical outlier detection
        historical_data = list(self.symbol_history[data_point.symbol])
        if len(historical_data) > 10:
            report.issues.extend(self._detect_statistical_outliers(data_point, historical_data))
        
        # Update symbol history
        self.symbol_history[data_point.symbol].append(data_point)
        
        # Calculate quality score
        metrics = report.calculate_quality_metrics()
        report.quality_score = metrics['overall_score']
        
        return report
    
    async def validate_historical_data(
        self, 
        historical_data: HistoricalData,
        cross_validate_providers: Optional[Dict[DataProvider, HistoricalData]] = None
    ) -> ValidationReport:
        """Validate historical data series"""
        report = ValidationReport(
            symbol=historical_data.symbol,
            validation_timestamp=datetime.utcnow(),
            total_data_points=len(historical_data.data_points)
        )
        
        if not historical_data.data_points:
            report.issues.append(ValidationIssue(
                rule=ValidationRule.DATA_COMPLETENESS,
                severity=ValidationSeverity.ERROR,
                message="No data points provided",
                symbol=historical_data.symbol,
                suggested_fix="Check data source and query parameters"
            ))
            return report
        
        # Validate individual data points
        for i, data_point in enumerate(historical_data.data_points):
            point_issues = self._validate_basic_constraints(data_point)
            for issue in point_issues:
                issue.data_point = {'index': i, 'data': data_point.dict() if hasattr(data_point, 'dict') else str(data_point)}
                report.issues.append(issue)
        
        # Validate time series continuity
        report.issues.extend(self._validate_time_series_continuity(historical_data))
        
        # Validate OHLC consistency for all points
        report.issues.extend(self._validate_series_ohlc_consistency(historical_data))
        
        # Statistical analysis
        report.issues.extend(self._perform_statistical_analysis(historical_data))
        
        # Cross-provider validation
        if cross_validate_providers:
            cross_validation_issues = await self._cross_validate_historical_data(
                historical_data, cross_validate_providers
            )
            report.issues.extend(cross_validation_issues)
            
            # Calculate provider scores
            for provider in cross_validate_providers.keys():
                provider_issues = [i for i in cross_validation_issues if i.provider == provider]
                error_count = len([i for i in provider_issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]])
                report.provider_scores[provider] = max(0.0, 1.0 - (error_count / max(1, len(historical_data.data_points))))
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)
        
        # Calculate final quality score
        metrics = report.calculate_quality_metrics()
        report.quality_score = metrics['overall_score']
        
        # Store validation history
        self.validation_history[historical_data.symbol].append(report)
        
        return report
    
    def _validate_basic_constraints(self, data_point: MarketDataPoint) -> List[ValidationIssue]:
        """Validate basic data constraints"""
        issues = []
        
        # Price validation
        if data_point.price is not None:
            if data_point.price <= self.thresholds['min_price']:
                issues.append(ValidationIssue(
                    rule=ValidationRule.PRICE_RANGE,
                    severity=ValidationSeverity.ERROR,
                    message=f"Price too low: {data_point.price}",
                    symbol=data_point.symbol,
                    timestamp=data_point.timestamp,
                    provider=data_point.provider,
                    suggested_fix="Check for stock splits or data errors"
                ))
            elif data_point.price > self.thresholds['max_price']:
                issues.append(ValidationIssue(
                    rule=ValidationRule.PRICE_RANGE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Price unusually high: {data_point.price}",
                    symbol=data_point.symbol,
                    timestamp=data_point.timestamp,
                    provider=data_point.provider,
                    suggested_fix="Verify price accuracy for high-value securities"
                ))
        else:
            issues.append(ValidationIssue(
                rule=ValidationRule.DATA_COMPLETENESS,
                severity=ValidationSeverity.ERROR,
                message="Missing price data",
                symbol=data_point.symbol,
                timestamp=data_point.timestamp,
                provider=data_point.provider,
                suggested_fix="Ensure price data is available from provider"
            ))
        
        # Volume validation
        if data_point.volume is not None:
            if data_point.volume < self.thresholds['min_volume']:
                issues.append(ValidationIssue(
                    rule=ValidationRule.VOLUME_RANGE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Volume is zero or negative: {data_point.volume}",
                    symbol=data_point.symbol,
                    timestamp=data_point.timestamp,
                    provider=data_point.provider,
                    suggested_fix="Check if market is open and trading is active"
                ))
            elif data_point.volume > self.thresholds['max_volume']:
                issues.append(ValidationIssue(
                    rule=ValidationRule.VOLUME_RANGE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Volume unusually high: {data_point.volume:,}",
                    symbol=data_point.symbol,
                    timestamp=data_point.timestamp,
                    provider=data_point.provider,
                    suggested_fix="Verify if high volume is due to corporate actions or news"
                ))
        
        # Bid-Ask validation
        if data_point.bid and data_point.ask:
            if data_point.bid >= data_point.ask:
                issues.append(ValidationIssue(
                    rule=ValidationRule.BUSINESS_LOGIC,
                    severity=ValidationSeverity.ERROR,
                    message=f"Bid ({data_point.bid}) >= Ask ({data_point.ask})",
                    symbol=data_point.symbol,
                    timestamp=data_point.timestamp,
                    provider=data_point.provider,
                    suggested_fix="Check quote data integrity"
                ))
        
        return issues
    
    def _validate_ohlc_consistency(self, data_point: MarketDataPoint) -> List[ValidationIssue]:
        """Validate OHLC price consistency"""
        issues = []
        
        o, h, l, c = data_point.open_price, data_point.high_price, data_point.low_price, data_point.price
        
        if not all([o, h, l, c]):
            return issues
        
        # High should be the highest price
        if h < max(o, c) * (1 - self.thresholds['ohlc_tolerance']):
            issues.append(ValidationIssue(
                rule=ValidationRule.OHLC_CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                message=f"High ({h}) is less than Open ({o}) or Close ({c})",
                symbol=data_point.symbol,
                timestamp=data_point.timestamp,
                provider=data_point.provider,
                suggested_fix="Verify OHLC data integrity"
            ))
        
        # Low should be the lowest price
        if l > min(o, c) * (1 + self.thresholds['ohlc_tolerance']):
            issues.append(ValidationIssue(
                rule=ValidationRule.OHLC_CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                message=f"Low ({l}) is greater than Open ({o}) or Close ({c})",
                symbol=data_point.symbol,
                timestamp=data_point.timestamp,
                provider=data_point.provider,
                suggested_fix="Verify OHLC data integrity"
            ))
        
        # High should be >= Low
        if h < l:
            issues.append(ValidationIssue(
                rule=ValidationRule.OHLC_CONSISTENCY,
                severity=ValidationSeverity.CRITICAL,
                message=f"High ({h}) is less than Low ({l})",
                symbol=data_point.symbol,
                timestamp=data_point.timestamp,
                provider=data_point.provider,
                suggested_fix="This is a critical data error that needs immediate attention"
            ))
        
        return issues
    
    def _validate_with_context(
        self, 
        data_point: MarketDataPoint, 
        context_data: List[MarketDataPoint]
    ) -> List[ValidationIssue]:
        """Validate data point against historical context"""
        issues = []
        
        if not context_data or not data_point.price:
            return issues
        
        # Get recent prices for comparison
        recent_prices = [dp.price for dp in context_data[-10:] if dp.price]
        
        if len(recent_prices) >= 3:
            avg_recent_price = statistics.mean(recent_prices)
            
            if avg_recent_price > 0:
                price_change = abs(data_point.price - avg_recent_price) / avg_recent_price
                
                if price_change > self.thresholds['max_price_change']:
                    severity = ValidationSeverity.WARNING
                    if price_change > self.thresholds['max_price_change'] * 2:
                        severity = ValidationSeverity.ERROR
                    
                    issues.append(ValidationIssue(
                        rule=ValidationRule.PRICE_VOLATILITY,
                        severity=severity,
                        message=f"Large price change: {price_change:.2%} from recent average",
                        symbol=data_point.symbol,
                        timestamp=data_point.timestamp,
                        provider=data_point.provider,
                        data_point={'current_price': data_point.price, 'avg_recent': avg_recent_price},
                        suggested_fix="Check for corporate actions or market events"
                    ))
        
        return issues
    
    def _detect_statistical_outliers(
        self, 
        data_point: MarketDataPoint, 
        historical_data: List[MarketDataPoint]
    ) -> List[ValidationIssue]:
        """Detect statistical outliers using historical data"""
        issues = []
        
        if not data_point.price or len(historical_data) < 20:
            return issues
        
        # Extract prices from historical data
        prices = [dp.price for dp in historical_data if dp.price]
        prices.append(data_point.price)
        
        # Detect outliers
        outlier_indices = self.statistical_analyzer.detect_price_outliers(prices, method='modified_zscore', threshold=3.0)
        
        # Check if current data point is an outlier
        if len(prices) - 1 in outlier_indices:  # Current point is last in array
            issues.append(ValidationIssue(
                rule=ValidationRule.STATISTICAL_OUTLIER,
                severity=ValidationSeverity.WARNING,
                message=f"Price identified as statistical outlier",
                symbol=data_point.symbol,
                timestamp=data_point.timestamp,
                provider=data_point.provider,
                suggested_fix="Review for data quality issues or genuine market events"
            ))
        
        return issues
    
    def _validate_time_series_continuity(self, historical_data: HistoricalData) -> List[ValidationIssue]:
        """Validate time series data continuity"""
        issues = []
        
        if len(historical_data.data_points) < 2:
            return issues
        
        # Sort by timestamp
        sorted_points = sorted(historical_data.data_points, key=lambda x: x.timestamp or datetime.min)
        
        for i in range(1, len(sorted_points)):
            current = sorted_points[i]
            previous = sorted_points[i-1]
            
            if current.timestamp and previous.timestamp:
                gap = current.timestamp - previous.timestamp
                
                if gap > self.thresholds['timestamp_gap_tolerance']:
                    issues.append(ValidationIssue(
                        rule=ValidationRule.TIMESTAMP_CONTINUITY,
                        severity=ValidationSeverity.WARNING,
                        message=f"Large time gap: {gap}",
                        symbol=historical_data.symbol,
                        timestamp=current.timestamp,
                        data_point={'gap_duration': str(gap), 'previous_timestamp': previous.timestamp.isoformat()},
                        suggested_fix="Check for missing data or market holidays"
                    ))
                
                # Check for duplicate timestamps
                if gap == timedelta(0):
                    issues.append(ValidationIssue(
                        rule=ValidationRule.TIMESTAMP_CONTINUITY,
                        severity=ValidationSeverity.WARNING,
                        message="Duplicate timestamp detected",
                        symbol=historical_data.symbol,
                        timestamp=current.timestamp,
                        suggested_fix="Remove or consolidate duplicate entries"
                    ))
        
        return issues
    
    def _validate_series_ohlc_consistency(self, historical_data: HistoricalData) -> List[ValidationIssue]:
        """Validate OHLC consistency across the entire series"""
        issues = []
        
        for i, data_point in enumerate(historical_data.data_points):
            ohlc_issues = self._validate_ohlc_consistency(data_point)
            for issue in ohlc_issues:
                issue.data_point = {'series_index': i}
                issues.append(issue)
        
        return issues
    
    def _perform_statistical_analysis(self, historical_data: HistoricalData) -> List[ValidationIssue]:
        """Perform comprehensive statistical analysis"""
        issues = []
        
        # Extract price and volume data
        prices = [dp.price for dp in historical_data.data_points if dp.price]
        volumes = [dp.volume for dp in historical_data.data_points if dp.volume]
        
        if len(prices) < 10:
            return issues
        
        # Price outlier detection
        price_outliers = self.statistical_analyzer.detect_price_outliers(prices)
        for idx in price_outliers:
            if idx < len(historical_data.data_points):
                data_point = historical_data.data_points[idx]
                issues.append(ValidationIssue(
                    rule=ValidationRule.STATISTICAL_OUTLIER,
                    severity=ValidationSeverity.INFO,
                    message=f"Price outlier detected: {data_point.price}",
                    symbol=historical_data.symbol,
                    timestamp=data_point.timestamp,
                    provider=data_point.provider,
                    suggested_fix="Investigate potential data quality issue or market event"
                ))
        
        # Volume anomaly detection
        if len(volumes) >= 20:
            volume_anomalies = self.statistical_analyzer.detect_volume_anomalies(volumes)
            for idx in volume_anomalies:
                if idx < len(historical_data.data_points):
                    data_point = historical_data.data_points[idx]
                    issues.append(ValidationIssue(
                        rule=ValidationRule.VOLUME_ANOMALY,
                        severity=ValidationSeverity.INFO,
                        message=f"Volume anomaly detected: {data_point.volume:,}",
                        symbol=historical_data.symbol,
                        timestamp=data_point.timestamp,
                        provider=data_point.provider,
                        suggested_fix="Check for corporate actions or unusual trading activity"
                    ))
        
        # Volatility analysis
        volatilities = self.statistical_analyzer.calculate_price_volatility(prices)
        if volatilities:
            max_volatility = max(volatilities)
            if max_volatility > self.thresholds['max_volatility']:
                issues.append(ValidationIssue(
                    rule=ValidationRule.PRICE_VOLATILITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Extremely high volatility detected: {max_volatility:.2f}",
                    symbol=historical_data.symbol,
                    data_point={'max_volatility': max_volatility},
                    suggested_fix="Review for data quality issues or market stress events"
                ))
        
        return issues
    
    async def _cross_validate_historical_data(
        self,
        primary_data: HistoricalData,
        provider_data: Dict[DataProvider, HistoricalData]
    ) -> List[ValidationIssue]:
        """Cross-validate historical data across providers"""
        issues = []
        
        # Prepare data for comparison
        comparison_data = {primary_data.provider: primary_data.data_points}
        comparison_data.update({provider: data.data_points for provider, data in provider_data.items()})
        
        # Use cross-provider validator
        cross_validation_issues = self.cross_provider_validator.validate_price_consistency(comparison_data)
        
        # Add symbol information to issues
        for issue in cross_validation_issues:
            issue.symbol = primary_data.symbol
            issues.append(issue)
        
        return issues
    
    def _generate_recommendations(self, report: ValidationReport) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        critical_issues = report.get_critical_issues()
        if critical_issues:
            recommendations.append("URGENT: Address critical data quality issues before using this data")
        
        # Count issues by type
        issue_counts = defaultdict(int)
        for issue in report.issues:
            issue_counts[issue.rule] += 1
        
        # Generate specific recommendations
        if issue_counts[ValidationRule.OHLC_CONSISTENCY] > 0:
            recommendations.append("Review OHLC data consistency with data provider")
        
        if issue_counts[ValidationRule.CROSS_PROVIDER_CONSISTENCY] > 0:
            recommendations.append("Consider using multiple data providers for better reliability")
        
        if issue_counts[ValidationRule.STATISTICAL_OUTLIER] > 5:
            recommendations.append("High number of statistical outliers detected - review data source quality")
        
        if issue_counts[ValidationRule.DATA_COMPLETENESS] > 0:
            recommendations.append("Ensure complete data coverage from your data providers")
        
        # Provider-specific recommendations
        for provider, score in report.provider_scores.items():
            if score < 0.8:
                recommendations.append(f"Consider alternative to {provider.value} due to low quality score ({score:.2f})")
        
        return recommendations
    
    def get_symbol_quality_history(self, symbol: str, limit: int = 10) -> List[ValidationReport]:
        """Get validation history for a symbol"""
        history = list(self.validation_history[symbol])
        return history[-limit:] if len(history) > limit else history
    
    def get_provider_reliability_scores(self) -> Dict[DataProvider, float]:
        """Get current provider reliability scores"""
        return dict(self.cross_provider_validator.provider_reliability_scores)
    
    def export_validation_report(self, report: ValidationReport) -> str:
        """Export validation report as JSON"""
        export_data = {
            'symbol': report.symbol,
            'validation_timestamp': report.validation_timestamp.isoformat(),
            'total_data_points': report.total_data_points,
            'quality_score': report.quality_score,
            'quality_metrics': report.calculate_quality_metrics(),
            'provider_scores': {k.value: v for k, v in report.provider_scores.items()},
            'issues': [issue.to_dict() for issue in report.issues],
            'recommendations': report.recommendations,
            'summary': {
                'total_issues': len(report.issues),
                'critical_issues': len(report.get_critical_issues()),
                'error_issues': len(report.get_issues_by_severity(ValidationSeverity.ERROR)),
                'warning_issues': len(report.get_issues_by_severity(ValidationSeverity.WARNING)),
                'info_issues': len(report.get_issues_by_severity(ValidationSeverity.INFO))
            }
        }
        
        return json.dumps(export_data, indent=2, default=str)


# Convenience function for quick validation
async def validate_market_data(
    data: Union[MarketDataPoint, HistoricalData],
    cross_provider_data: Optional[Dict[DataProvider, Any]] = None
) -> ValidationReport:
    """Quick validation function for market data"""
    validator = DataQualityValidator()
    
    if isinstance(data, MarketDataPoint):
        return await validator.validate_market_data_point(data)
    elif isinstance(data, HistoricalData):
        return await validator.validate_historical_data(data, cross_provider_data)
    else:
        raise ValueError("Data must be MarketDataPoint or HistoricalData instance")