"""
Data Validator

Validates market data for consistency and anomalies before storage.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict

from ..models import MarketDataPoint, HistoricalData, DataProvider
from ..config import config


class DataValidator:
    """Validates market data for quality and consistency"""
    
    def __init__(self):
        self.logger = logging.getLogger("market_data.data_validator")
        
        # Validation statistics
        self.validations_performed = 0
        self.data_points_validated = 0
        self.anomalies_detected = 0
        self.validation_errors = 0
        
        # Anomaly tracking
        self.anomaly_history = defaultdict(list)
    
    def validate_market_data_point(self, data_point: MarketDataPoint) -> Tuple[bool, List[str]]:
        """Validate a single market data point"""
        self.validations_performed += 1
        self.data_points_validated += 1
        
        errors = []
        
        try:
            # Basic field validation
            errors.extend(self._validate_basic_fields(data_point))
            
            # Price validation
            errors.extend(self._validate_prices(data_point))
            
            # Volume validation
            errors.extend(self._validate_volume(data_point))
            
            # Timestamp validation
            errors.extend(self._validate_timestamp(data_point))
            
            # Cross-field validation
            errors.extend(self._validate_cross_fields(data_point))
            
            # Anomaly detection
            anomalies = self._detect_anomalies(data_point)
            if anomalies:
                self.anomalies_detected += len(anomalies)
                errors.extend(anomalies)
                
                # Log anomalies for tracking
                self.anomaly_history[data_point.symbol].extend(anomalies)
            
            is_valid = len(errors) == 0
            
            if not is_valid:
                self.logger.warning(f"Validation failed for {data_point.symbol}: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            self.validation_errors += 1
            self.logger.error(f"Error validating data point for {data_point.symbol}: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def validate_historical_data(self, historical_data: HistoricalData) -> Tuple[bool, List[str], List[MarketDataPoint]]:
        """Validate historical data and return valid data points"""
        self.validations_performed += 1
        
        errors = []
        valid_data_points = []
        
        try:
            # Validate the container
            if not historical_data.data_points:
                return False, ["No data points provided"], []
            
            if not historical_data.symbol:
                return False, ["Symbol is required"], []
            
            # Validate date range
            if historical_data.start_date > historical_data.end_date:
                errors.append("Start date cannot be after end date")
            
            # Validate each data point
            point_errors = []
            for i, data_point in enumerate(historical_data.data_points):
                self.data_points_validated += 1
                
                # Basic validation
                is_valid, data_errors = self.validate_market_data_point(data_point)
                
                if is_valid:
                    valid_data_points.append(data_point)
                else:
                    point_errors.extend([f"Point {i}: {error}" for error in data_errors])
            
            # Check data continuity
            continuity_errors = self._validate_data_continuity(valid_data_points)
            errors.extend(continuity_errors)
            
            # Check for duplicates
            duplicate_errors = self._check_duplicates(valid_data_points)
            errors.extend(duplicate_errors)
            
            # Check data ordering
            ordering_errors = self._validate_data_ordering(valid_data_points)
            errors.extend(ordering_errors)
            
            # Add point-level errors
            errors.extend(point_errors)
            
            # Consider validation successful if we have at least 80% valid data
            success_threshold = 0.8
            success_rate = len(valid_data_points) / len(historical_data.data_points)
            is_valid = success_rate >= success_threshold and len(errors) == 0
            
            if not is_valid:
                self.logger.warning(f"Historical data validation failed for {historical_data.symbol}: {len(errors)} errors")
            
            return is_valid, errors, valid_data_points
            
        except Exception as e:
            self.validation_errors += 1
            self.logger.error(f"Error validating historical data for {historical_data.symbol}: {e}")
            return False, [f"Validation error: {str(e)}"], []
    
    def _validate_basic_fields(self, data_point: MarketDataPoint) -> List[str]:
        """Validate basic required fields"""
        errors = []
        
        if not data_point.symbol or len(data_point.symbol.strip()) == 0:
            errors.append("Symbol is required")
        
        if not data_point.timestamp:
            errors.append("Timestamp is required")
        
        if not data_point.provider:
            errors.append("Provider is required")
        
        if not data_point.data_type:
            errors.append("Data type is required")
        
        return errors
    
    def _validate_prices(self, data_point: MarketDataPoint) -> List[str]:
        """Validate price fields"""
        errors = []
        
        # Check for negative prices
        price_fields = [
            ('current_price', data_point.current_price),
            ('open_price', data_point.open_price),
            ('high_price', data_point.high_price),
            ('low_price', data_point.low_price),
            ('close_price', data_point.close_price)
        ]
        
        for field_name, price in price_fields:
            if price is not None:
                if price < 0:
                    errors.append(f"{field_name} cannot be negative: {price}")
                elif price == 0 and field_name != 'price_change':
                    errors.append(f"{field_name} cannot be zero: {price}")
                elif price > Decimal('1000000'):  # Sanity check for extremely high prices
                    errors.append(f"{field_name} seems unreasonably high: {price}")
        
        # Validate price relationships (if all OHLC prices are present)
        if all(price is not None for price in [data_point.open_price, data_point.high_price, 
                                              data_point.low_price, data_point.close_price]):
            
            if data_point.high_price < data_point.low_price:
                errors.append(f"High price ({data_point.high_price}) cannot be less than low price ({data_point.low_price})")
            
            if data_point.high_price < max(data_point.open_price, data_point.close_price):
                errors.append("High price must be >= max(open, close)")
            
            if data_point.low_price > min(data_point.open_price, data_point.close_price):
                errors.append("Low price must be <= min(open, close)")
        
        return errors
    
    def _validate_volume(self, data_point: MarketDataPoint) -> List[str]:
        """Validate volume field"""
        errors = []
        
        if data_point.volume is not None:
            if data_point.volume < 0:
                errors.append(f"Volume cannot be negative: {data_point.volume}")
            elif data_point.volume > 10_000_000_000:  # 10 billion shares seems unreasonable
                errors.append(f"Volume seems unreasonably high: {data_point.volume:,}")
        
        return errors
    
    def _validate_timestamp(self, data_point: MarketDataPoint) -> List[str]:
        """Validate timestamp field"""
        errors = []
        
        if data_point.timestamp:
            now = datetime.utcnow()
            
            # Check if timestamp is too far in the future
            if data_point.timestamp > now + timedelta(hours=1):
                errors.append(f"Timestamp is too far in the future: {data_point.timestamp}")
            
            # Check if timestamp is too far in the past (e.g., before 1970)
            min_date = datetime(1970, 1, 1)
            if data_point.timestamp < min_date:
                errors.append(f"Timestamp is too far in the past: {data_point.timestamp}")
        
        return errors
    
    def _validate_cross_fields(self, data_point: MarketDataPoint) -> List[str]:
        """Validate relationships between fields"""
        errors = []
        
        # Validate price change calculations
        if (data_point.price_change is not None and 
            data_point.current_price is not None and 
            data_point.close_price is not None):
            
            expected_change = data_point.current_price - data_point.close_price
            actual_change = data_point.price_change
            
            # Allow small floating point differences
            if abs(expected_change - actual_change) > Decimal('0.01'):
                errors.append(f"Price change calculation mismatch: expected {expected_change}, got {actual_change}")
        
        # Validate percentage change calculations
        if (data_point.price_change_percent is not None and 
            data_point.price_change is not None and 
            data_point.close_price is not None and 
            data_point.close_price > 0):
            
            expected_percent = (data_point.price_change / data_point.close_price) * 100
            actual_percent = data_point.price_change_percent
            
            # Allow small floating point differences
            if abs(expected_percent - actual_percent) > Decimal('0.1'):
                errors.append(f"Price change percent calculation mismatch: expected {expected_percent:.2f}%, got {actual_percent:.2f}%")
        
        return errors
    
    def _detect_anomalies(self, data_point: MarketDataPoint) -> List[str]:
        """Detect anomalies in market data"""
        anomalies = []
        
        # Skip anomaly detection if validation is disabled
        if not config.validate_price_changes:
            return anomalies
        
        # Extreme price change detection
        if data_point.price_change_percent is not None:
            abs_change = abs(data_point.price_change_percent)
            if abs_change > config.max_price_change_percent:
                anomalies.append(f"Extreme price change detected: {data_point.price_change_percent:.2f}%")
        
        # Volume anomaly detection (if we have historical context)
        if data_point.volume is not None:
            # This would ideally compare against historical averages
            # For now, just check for extremely high volume
            if data_point.volume > 1_000_000_000:  # 1 billion shares
                anomalies.append(f"Extremely high volume detected: {data_point.volume:,}")
        
        # Gap detection (significant difference between consecutive prices)
        if (data_point.open_price is not None and 
            data_point.close_price is not None and 
            data_point.close_price > 0):
            
            gap_percent = abs((data_point.open_price - data_point.close_price) / data_point.close_price * 100)
            if gap_percent > 20:  # 20% gap
                anomalies.append(f"Large price gap detected: {gap_percent:.2f}%")
        
        return anomalies
    
    def _validate_data_continuity(self, data_points: List[MarketDataPoint]) -> List[str]:
        """Validate data continuity (no large gaps)"""
        errors = []
        
        if len(data_points) < 2:
            return errors
        
        # Sort by timestamp
        sorted_points = sorted(data_points, key=lambda x: x.timestamp)
        
        for i in range(1, len(sorted_points)):
            prev_point = sorted_points[i-1]
            curr_point = sorted_points[i]
            
            # Check for large time gaps (more than 7 days for daily data)
            time_diff = curr_point.timestamp - prev_point.timestamp
            if time_diff > timedelta(days=7):
                errors.append(f"Large time gap detected: {time_diff} between {prev_point.timestamp} and {curr_point.timestamp}")
        
        return errors
    
    def _check_duplicates(self, data_points: List[MarketDataPoint]) -> List[str]:
        """Check for duplicate data points"""
        errors = []
        
        seen_timestamps = set()
        
        for point in data_points:
            timestamp_key = point.timestamp.replace(microsecond=0)  # Ignore microseconds
            
            if timestamp_key in seen_timestamps:
                errors.append(f"Duplicate timestamp detected: {timestamp_key}")
            else:
                seen_timestamps.add(timestamp_key)
        
        return errors
    
    def _validate_data_ordering(self, data_points: List[MarketDataPoint]) -> List[str]:
        """Validate that data points are properly ordered"""
        errors = []
        
        if len(data_points) < 2:
            return errors
        
        # Check if timestamps are in order
        timestamps = [point.timestamp for point in data_points]
        sorted_timestamps = sorted(timestamps)
        
        if timestamps != sorted_timestamps:
            errors.append("Data points are not ordered by timestamp")
        
        return errors
    
    def validate_provider_consistency(self, data_points: List[MarketDataPoint]) -> List[str]:
        """Validate consistency across different providers"""
        errors = []
        
        # Group by symbol and timestamp
        grouped_data = defaultdict(list)
        
        for point in data_points:
            key = (point.symbol, point.timestamp.replace(microsecond=0))
            grouped_data[key].append(point)
        
        # Check for significant discrepancies between providers
        for key, points in grouped_data.items():
            if len(points) > 1:
                symbol, timestamp = key
                
                # Compare prices from different providers
                prices = [point.current_price for point in points if point.current_price]
                
                if len(prices) > 1:
                    min_price = min(prices)
                    max_price = max(prices)
                    
                    if min_price > 0:
                        price_diff_percent = ((max_price - min_price) / min_price) * 100
                        
                        if price_diff_percent > 5:  # 5% difference threshold
                            errors.append(f"Large price discrepancy for {symbol} at {timestamp}: {price_diff_percent:.2f}% difference between providers")
        
        return errors
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            "validations_performed": self.validations_performed,
            "data_points_validated": self.data_points_validated,
            "anomalies_detected": self.anomalies_detected,
            "validation_errors": self.validation_errors,
            "anomaly_rate": self.anomalies_detected / self.data_points_validated if self.data_points_validated > 0 else 0,
            "error_rate": self.validation_errors / self.validations_performed if self.validations_performed > 0 else 0,
            "symbols_with_anomalies": len(self.anomaly_history),
            "total_anomalies_by_symbol": {symbol: len(anomalies) for symbol, anomalies in self.anomaly_history.items()}
        }
    
    def get_symbol_anomalies(self, symbol: str, limit: int = 10) -> List[str]:
        """Get recent anomalies for a specific symbol"""
        anomalies = self.anomaly_history.get(symbol.upper(), [])
        return anomalies[-limit:] if limit else anomalies
    
    def reset_stats(self):
        """Reset validation statistics"""
        self.validations_performed = 0
        self.data_points_validated = 0
        self.anomalies_detected = 0
        self.validation_errors = 0
        self.anomaly_history.clear()
        self.logger.info("Validation statistics reset")