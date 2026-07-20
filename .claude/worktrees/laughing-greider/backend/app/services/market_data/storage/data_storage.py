"""
Data Storage

Historical market data storage and retrieval system with validation.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict

from sqlalchemy import text, select, insert, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MarketDataPoint, HistoricalData, CompanyInfo, DataProvider
from ..config import config
from .data_validator import DataValidator
from ...database.models import MarketDataModel


class DataStorage:
    """Storage system for historical market data"""
    
    def __init__(self, db_session_factory, validator: DataValidator = None):
        self.db_session_factory = db_session_factory
        self.validator = validator or DataValidator()
        self.logger = logging.getLogger("market_data.data_storage")
        
        # Storage statistics
        self.data_points_stored = 0
        self.storage_errors = 0
        self.duplicate_points = 0
        self.validation_failures = 0
        
        # Performance tracking
        self.storage_times = []
        self.batch_sizes = []
    
    async def store_market_data_point(self, data_point: MarketDataPoint, validate: bool = True) -> bool:
        """Store a single market data point"""
        try:
            # Validate data if requested
            if validate:
                is_valid, errors = self.validator.validate_market_data_point(data_point)
                if not is_valid:
                    self.validation_failures += 1
                    self.logger.warning(f"Validation failed for {data_point.symbol}: {errors}")
                    return False
            
            # Store in database
            async with self.db_session_factory() as session:
                # Check for existing data point
                existing = await self._get_existing_data_point(session, data_point)
                
                if existing:
                    # Update existing point
                    success = await self._update_data_point(session, existing, data_point)
                else:
                    # Insert new point
                    success = await self._insert_data_point(session, data_point)
                
                if success:
                    await session.commit()
                    self.data_points_stored += 1
                    return True
                else:
                    await session.rollback()
                    return False
        
        except Exception as e:
            self.storage_errors += 1
            self.logger.error(f"Error storing data point for {data_point.symbol}: {e}")
            return False
    
    async def store_historical_data(self, historical_data: HistoricalData, validate: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """Store historical market data"""
        start_time = datetime.utcnow()
        results = {
            "total_points": len(historical_data.data_points),
            "stored_points": 0,
            "updated_points": 0,
            "duplicate_points": 0,
            "validation_failures": 0,
            "errors": []
        }
        
        try:
            # Validate historical data if requested
            if validate:
                is_valid, errors, valid_points = self.validator.validate_historical_data(historical_data)
                if errors:
                    results["errors"].extend(errors)
                
                if not valid_points:
                    self.validation_failures += len(historical_data.data_points)
                    return False, results
                
                # Use only valid points
                data_points = valid_points
                results["validation_failures"] = len(historical_data.data_points) - len(valid_points)
            else:
                data_points = historical_data.data_points
            
            # Store data points in batches
            batch_size = 100
            for i in range(0, len(data_points), batch_size):
                batch = data_points[i:i + batch_size]
                batch_results = await self._store_data_batch(batch)
                
                results["stored_points"] += batch_results["stored"]
                results["updated_points"] += batch_results["updated"]
                results["duplicate_points"] += batch_results["duplicates"]
                results["errors"].extend(batch_results["errors"])
            
            # Track performance
            storage_time = (datetime.utcnow() - start_time).total_seconds()
            self.storage_times.append(storage_time)
            self.batch_sizes.append(len(data_points))
            
            # Keep only recent performance data
            if len(self.storage_times) > 100:
                self.storage_times = self.storage_times[-50:]
                self.batch_sizes = self.batch_sizes[-50:]
            
            success = results["stored_points"] + results["updated_points"] > 0
            
            self.logger.info(f"Stored historical data for {historical_data.symbol}: "
                           f"{results['stored_points']} new, {results['updated_points']} updated, "
                           f"{results['duplicate_points']} duplicates in {storage_time:.2f}s")
            
            return success, results
        
        except Exception as e:
            self.storage_errors += 1
            self.logger.error(f"Error storing historical data for {historical_data.symbol}: {e}")
            results["errors"].append(str(e))
            return False, results
    
    async def _store_data_batch(self, data_points: List[MarketDataPoint]) -> Dict[str, Any]:
        """Store a batch of data points efficiently"""
        results = {
            "stored": 0,
            "updated": 0,
            "duplicates": 0,
            "errors": []
        }
        
        try:
            async with self.db_session_factory() as session:
                for data_point in data_points:
                    try:
                        # Check for existing data point
                        existing = await self._get_existing_data_point(session, data_point)
                        
                        if existing:
                            # Check if update is needed
                            if self._needs_update(existing, data_point):
                                success = await self._update_data_point(session, existing, data_point)
                                if success:
                                    results["updated"] += 1
                                else:
                                    results["errors"].append(f"Failed to update {data_point.symbol}")
                            else:
                                results["duplicates"] += 1
                        else:
                            # Insert new point
                            success = await self._insert_data_point(session, data_point)
                            if success:
                                results["stored"] += 1
                            else:
                                results["errors"].append(f"Failed to insert {data_point.symbol}")
                    
                    except Exception as e:
                        results["errors"].append(f"Error processing {data_point.symbol}: {str(e)}")
                
                await session.commit()
        
        except Exception as e:
            results["errors"].append(f"Batch storage error: {str(e)}")
        
        return results
    
    async def _get_existing_data_point(self, session: AsyncSession, data_point: MarketDataPoint) -> Optional[Any]:
        """Check if data point already exists"""
        try:
            # Create query to find existing data point
            # This would use your MarketDataModel from the database models
            query = select(MarketDataModel).where(
                and_(
                    MarketDataModel.symbol == data_point.symbol.upper(),
                    MarketDataModel.timestamp == data_point.timestamp,
                    MarketDataModel.provider == data_point.provider.value
                )
            )
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
        
        except Exception as e:
            self.logger.error(f"Error checking existing data point: {e}")
            return None
    
    async def _insert_data_point(self, session: AsyncSession, data_point: MarketDataPoint) -> bool:
        """Insert new data point"""
        try:
            # Convert data point to database model
            db_model = self._to_db_model(data_point)
            
            session.add(db_model)
            return True
        
        except Exception as e:
            self.logger.error(f"Error inserting data point: {e}")
            return False
    
    async def _update_data_point(self, session: AsyncSession, existing: Any, data_point: MarketDataPoint) -> bool:
        """Update existing data point"""
        try:
            # Update relevant fields
            existing.current_price = data_point.current_price
            existing.open_price = data_point.open_price
            existing.high_price = data_point.high_price
            existing.low_price = data_point.low_price
            existing.close_price = data_point.close_price
            existing.volume = data_point.volume
            existing.market_cap = data_point.market_cap
            existing.price_change = data_point.price_change
            existing.price_change_percent = data_point.price_change_percent
            existing.is_real_time = data_point.is_real_time
            existing.additional_data = data_point.additional_data
            existing.updated_at = datetime.utcnow()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error updating data point: {e}")
            return False
    
    def _needs_update(self, existing: Any, new_point: MarketDataPoint) -> bool:
        """Check if existing data point needs update"""
        # Update if the new data is more recent or has different values
        if hasattr(existing, 'updated_at') and existing.updated_at:
            time_diff = datetime.utcnow() - existing.updated_at
            if time_diff < timedelta(minutes=1):  # Don't update if recently updated
                return False
        
        # Check if values are different
        return (
            existing.current_price != new_point.current_price or
            existing.volume != new_point.volume or
            existing.is_real_time != new_point.is_real_time
        )
    
    def _to_db_model(self, data_point: MarketDataPoint) -> Any:
        """Convert MarketDataPoint to database model"""
        # This would create an instance of your MarketDataModel
        return MarketDataModel(
            symbol=data_point.symbol.upper(),
            timestamp=data_point.timestamp,
            open_price=data_point.open_price,
            high_price=data_point.high_price,
            low_price=data_point.low_price,
            close_price=data_point.close_price,
            current_price=data_point.current_price,
            volume=data_point.volume,
            market_cap=data_point.market_cap,
            price_change=data_point.price_change,
            price_change_percent=data_point.price_change_percent,
            data_type=data_point.data_type.value,
            provider=data_point.provider.value,
            is_real_time=data_point.is_real_time,
            additional_data=data_point.additional_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def retrieve_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        interval: str = "1d",
        provider: Optional[DataProvider] = None
    ) -> Optional[HistoricalData]:
        """Retrieve historical data from storage"""
        try:
            async with self.db_session_factory() as session:
                # Build query
                query = select(MarketDataModel).where(
                    and_(
                        MarketDataModel.symbol == symbol.upper(),
                        MarketDataModel.timestamp >= datetime.combine(start_date, datetime.min.time()),
                        MarketDataModel.timestamp <= datetime.combine(end_date, datetime.max.time())
                    )
                )
                
                if provider:
                    query = query.where(MarketDataModel.provider == provider.value)
                
                # Order by timestamp
                query = query.order_by(MarketDataModel.timestamp)
                
                result = await session.execute(query)
                db_records = result.scalars().all()
                
                if not db_records:
                    return None
                
                # Convert to MarketDataPoint objects
                data_points = []
                for record in db_records:
                    point = self._from_db_model(record)
                    if point:
                        data_points.append(point)
                
                return HistoricalData(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    data_points=data_points,
                    provider=provider or DataProvider.YAHOO_FINANCE
                )
        
        except Exception as e:
            self.logger.error(f"Error retrieving historical data for {symbol}: {e}")
            return None
    
    def _from_db_model(self, db_record: Any) -> Optional[MarketDataPoint]:
        """Convert database model to MarketDataPoint"""
        try:
            return MarketDataPoint(
                symbol=db_record.symbol,
                timestamp=db_record.timestamp,
                open_price=db_record.open_price,
                high_price=db_record.high_price,
                low_price=db_record.low_price,
                close_price=db_record.close_price,
                current_price=db_record.current_price,
                volume=db_record.volume,
                market_cap=db_record.market_cap,
                price_change=db_record.price_change,
                price_change_percent=db_record.price_change_percent,
                data_type=db_record.data_type,
                provider=db_record.provider,
                is_real_time=db_record.is_real_time,
                additional_data=db_record.additional_data or {}
            )
        except Exception as e:
            self.logger.error(f"Error converting database record: {e}")
            return None
    
    async def get_latest_data_point(self, symbol: str, provider: Optional[DataProvider] = None) -> Optional[MarketDataPoint]:
        """Get the latest data point for a symbol"""
        try:
            async with self.db_session_factory() as session:
                query = select(MarketDataModel).where(
                    MarketDataModel.symbol == symbol.upper()
                )
                
                if provider:
                    query = query.where(MarketDataModel.provider == provider.value)
                
                query = query.order_by(MarketDataModel.timestamp.desc()).limit(1)
                
                result = await session.execute(query)
                db_record = result.scalar_one_or_none()
                
                if db_record:
                    return self._from_db_model(db_record)
                
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting latest data point for {symbol}: {e}")
            return None
    
    async def get_symbol_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get statistics for a symbol"""
        try:
            async with self.db_session_factory() as session:
                # Count total data points
                count_query = select(text("COUNT(*)")).select_from(MarketDataModel).where(
                    MarketDataModel.symbol == symbol.upper()
                )
                count_result = await session.execute(count_query)
                total_points = count_result.scalar()
                
                # Get date range
                date_query = select(
                    text("MIN(timestamp) as min_date, MAX(timestamp) as max_date")
                ).select_from(MarketDataModel).where(
                    MarketDataModel.symbol == symbol.upper()
                )
                date_result = await session.execute(date_query)
                date_row = date_result.first()
                
                # Get provider breakdown
                provider_query = select(
                    MarketDataModel.provider,
                    text("COUNT(*) as count")
                ).where(
                    MarketDataModel.symbol == symbol.upper()
                ).group_by(MarketDataModel.provider)
                
                provider_result = await session.execute(provider_query)
                provider_counts = {row.provider: row.count for row in provider_result}
                
                return {
                    "symbol": symbol,
                    "total_data_points": total_points,
                    "date_range": {
                        "min_date": date_row.min_date if date_row else None,
                        "max_date": date_row.max_date if date_row else None
                    },
                    "provider_breakdown": provider_counts
                }
        
        except Exception as e:
            self.logger.error(f"Error getting statistics for {symbol}: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = None) -> Dict[str, Any]:
        """Clean up old market data"""
        days_to_keep = days_to_keep or config.max_historical_days
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            async with self.db_session_factory() as session:
                # Count records to be deleted
                count_query = select(text("COUNT(*)")).select_from(MarketDataModel).where(
                    MarketDataModel.timestamp < cutoff_date
                )
                count_result = await session.execute(count_query)
                records_to_delete = count_result.scalar()
                
                # Delete old records
                delete_query = delete(MarketDataModel).where(
                    MarketDataModel.timestamp < cutoff_date
                )
                
                await session.execute(delete_query)
                await session.commit()
                
                self.logger.info(f"Cleaned up {records_to_delete} old data records (older than {days_to_keep} days)")
                
                return {
                    "records_deleted": records_to_delete,
                    "cutoff_date": cutoff_date.isoformat(),
                    "days_kept": days_to_keep
                }
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
            return {"error": str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage system statistics"""
        avg_storage_time = sum(self.storage_times) / len(self.storage_times) if self.storage_times else 0
        avg_batch_size = sum(self.batch_sizes) / len(self.batch_sizes) if self.batch_sizes else 0
        
        return {
            "data_points_stored": self.data_points_stored,
            "storage_errors": self.storage_errors,
            "duplicate_points": self.duplicate_points,
            "validation_failures": self.validation_failures,
            "performance": {
                "average_storage_time": avg_storage_time,
                "average_batch_size": avg_batch_size,
                "recent_operations": len(self.storage_times)
            },
            "error_rate": self.storage_errors / (self.storage_errors + self.data_points_stored) if (self.storage_errors + self.data_points_stored) > 0 else 0,
            "validation_stats": self.validator.get_validation_stats()
        }
    
    def reset_stats(self):
        """Reset storage statistics"""
        self.data_points_stored = 0
        self.storage_errors = 0
        self.duplicate_points = 0
        self.validation_failures = 0
        self.storage_times.clear()
        self.batch_sizes.clear()
        self.validator.reset_stats()
        self.logger.info("Storage statistics reset")