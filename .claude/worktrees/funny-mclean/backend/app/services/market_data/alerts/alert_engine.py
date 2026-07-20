"""
Alert Engine

Core alert processing engine that monitors market data and triggers alerts.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

from ..models import (
    MarketDataPoint, AlertConfig, PriceAlert, AlertType, AlertStatus,
    DataProvider
)
from ..config import config
from .notification_service import NotificationService


class AlertEngine:
    """Market data alert processing engine"""
    
    def __init__(self, notification_service: NotificationService = None):
        self.notification_service = notification_service or NotificationService()
        self.logger = logging.getLogger("market_data.alert_engine")
        
        # Alert storage
        self.active_alerts: Dict[str, AlertConfig] = {}
        self.user_alerts: Dict[str, Set[str]] = defaultdict(set)  # user_id -> alert_ids
        self.symbol_alerts: Dict[str, Set[str]] = defaultdict(set)  # symbol -> alert_ids
        
        # Alert history and state
        self.triggered_alerts: Dict[str, PriceAlert] = {}
        self.alert_states: Dict[str, Dict[str, Any]] = {}  # alert_id -> state data
        
        # Price history for calculations
        self.price_history: Dict[str, List[MarketDataPoint]] = defaultdict(list)
        
        # Processing control
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self.alerts_processed = 0
        self.alerts_triggered = 0
        self.processing_errors = 0
    
    async def start(self):
        """Start the alert engine"""
        if self._running:
            return
        
        self.logger.info("Starting alert engine")
        self._running = True
        
        # Start background processing
        self._processing_task = asyncio.create_task(self._processing_loop())
        
        # Initialize notification service
        await self.notification_service.initialize()
        
        self.logger.info("Alert engine started")
    
    async def stop(self):
        """Stop the alert engine"""
        if not self._running:
            return
        
        self.logger.info("Stopping alert engine")
        self._running = False
        
        # Cancel processing task
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown notification service
        await self.notification_service.shutdown()
        
        self.logger.info("Alert engine stopped")
    
    async def add_alert(self, alert_config: AlertConfig) -> bool:
        """Add a new alert configuration"""
        try:
            # Validate alert
            if not self._validate_alert_config(alert_config):
                return False
            
            # Check user alert limits
            user_alert_count = len(self.user_alerts.get(alert_config.user_id, set()))
            if user_alert_count >= config.max_alerts_per_user:
                self.logger.warning(f"User {alert_config.user_id} has reached alert limit")
                return False
            
            # Store alert
            self.active_alerts[alert_config.id] = alert_config
            self.user_alerts[alert_config.user_id].add(alert_config.id)
            self.symbol_alerts[alert_config.symbol.upper()].add(alert_config.id)
            
            # Initialize alert state
            self.alert_states[alert_config.id] = {
                "created_at": datetime.utcnow(),
                "last_checked": None,
                "check_count": 0,
                "previous_values": {}
            }
            
            self.logger.info(f"Added alert {alert_config.id} for user {alert_config.user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding alert {alert_config.id}: {e}")
            return False
    
    async def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert configuration"""
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return False
            
            # Remove from indexes
            self.user_alerts[alert.user_id].discard(alert_id)
            self.symbol_alerts[alert.symbol.upper()].discard(alert_id)
            
            # Remove main record
            del self.active_alerts[alert_id]
            
            # Clean up state
            if alert_id in self.alert_states:
                del self.alert_states[alert_id]
            
            self.logger.info(f"Removed alert {alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing alert {alert_id}: {e}")
            return False
    
    async def process_market_data(self, market_data: MarketDataPoint):
        """Process incoming market data for alert triggers"""
        try:
            symbol = market_data.symbol.upper()
            
            # Update price history
            self._update_price_history(symbol, market_data)
            
            # Get alerts for this symbol
            alert_ids = self.symbol_alerts.get(symbol, set())
            if not alert_ids:
                return
            
            # Check each alert
            for alert_id in alert_ids.copy():  # Copy to avoid modification during iteration
                alert = self.active_alerts.get(alert_id)
                if not alert or not alert.is_active:
                    continue
                
                # Check if alert should be triggered
                triggered = await self._check_alert(alert, market_data)
                if triggered:
                    await self._trigger_alert(alert, market_data)
            
            self.alerts_processed += len(alert_ids)
            
        except Exception as e:
            self.processing_errors += 1
            self.logger.error(f"Error processing market data for alerts: {e}")
    
    def _update_price_history(self, symbol: str, market_data: MarketDataPoint):
        """Update price history for calculations"""
        history = self.price_history[symbol]
        history.append(market_data)
        
        # Keep only recent history (last 100 points)
        if len(history) > 100:
            self.price_history[symbol] = history[-50:]
    
    async def _check_alert(self, alert: AlertConfig, market_data: MarketDataPoint) -> bool:
        """Check if an alert should be triggered"""
        try:
            current_price = market_data.current_price
            if not current_price:
                return False
            
            alert_state = self.alert_states[alert.id]
            alert_state["last_checked"] = datetime.utcnow()
            alert_state["check_count"] += 1
            
            # Check alert type
            if alert.alert_type == AlertType.PRICE_ABOVE:
                return current_price >= alert.threshold_value
            
            elif alert.alert_type == AlertType.PRICE_BELOW:
                return current_price <= alert.threshold_value
            
            elif alert.alert_type == AlertType.PRICE_CHANGE_PERCENT:
                return self._check_price_change_percent(alert, market_data)
            
            elif alert.alert_type == AlertType.VOLUME_SPIKE:
                return self._check_volume_spike(alert, market_data)
            
            elif alert.alert_type == AlertType.MOVING_AVERAGE_CROSS:
                return self._check_moving_average_cross(alert, market_data)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking alert {alert.id}: {e}")
            return False
    
    def _check_price_change_percent(self, alert: AlertConfig, market_data: MarketDataPoint) -> bool:
        """Check price change percentage alert"""
        if not market_data.price_change_percent:
            return False
        
        change_percent = abs(market_data.price_change_percent)
        return change_percent >= alert.percentage_threshold
    
    def _check_volume_spike(self, alert: AlertConfig, market_data: MarketDataPoint) -> bool:
        """Check volume spike alert"""
        if not market_data.volume:
            return False
        
        # Get historical volume data
        symbol = market_data.symbol.upper()
        history = self.price_history.get(symbol, [])
        
        if len(history) < 10:  # Need at least 10 data points
            return False
        
        # Calculate average volume (last 20 periods)
        recent_volumes = [point.volume for point in history[-20:] if point.volume]
        if not recent_volumes:
            return False
        
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        # Check if current volume is significantly higher
        volume_ratio = market_data.volume / avg_volume
        threshold = alert.threshold_value or Decimal("2.0")  # Default 2x spike
        
        return volume_ratio >= threshold
    
    def _check_moving_average_cross(self, alert: AlertConfig, market_data: MarketDataPoint) -> bool:
        """Check moving average crossover alert"""
        symbol = market_data.symbol.upper()
        history = self.price_history.get(symbol, [])
        
        if len(history) < 50:  # Need enough data for moving averages
            return False
        
        # Calculate short and long moving averages
        short_period = 20  # 20-period MA
        long_period = 50   # 50-period MA
        
        short_prices = [point.current_price for point in history[-short_period:] if point.current_price]
        long_prices = [point.current_price for point in history[-long_period:] if point.current_price]
        
        if len(short_prices) < short_period or len(long_prices) < long_period:
            return False
        
        short_ma = sum(short_prices) / len(short_prices)
        long_ma = sum(long_prices) / len(long_prices)
        
        # Check for crossover
        alert_state = self.alert_states[alert.id]
        previous_short_ma = alert_state["previous_values"].get("short_ma")
        previous_long_ma = alert_state["previous_values"].get("long_ma")
        
        # Store current values for next check
        alert_state["previous_values"]["short_ma"] = short_ma
        alert_state["previous_values"]["long_ma"] = long_ma
        
        if previous_short_ma is None or previous_long_ma is None:
            return False
        
        # Bullish crossover: short MA crosses above long MA
        bullish_cross = (previous_short_ma <= previous_long_ma and short_ma > long_ma)
        
        # Bearish crossover: short MA crosses below long MA
        bearish_cross = (previous_short_ma >= previous_long_ma and short_ma < long_ma)
        
        return bullish_cross or bearish_cross
    
    async def _trigger_alert(self, alert: AlertConfig, market_data: MarketDataPoint):
        """Trigger an alert and send notifications"""
        try:
            # Create alert instance
            alert_instance = PriceAlert(
                alert_config_id=alert.id,
                user_id=alert.user_id,
                symbol=alert.symbol,
                alert_type=alert.alert_type,
                trigger_price=market_data.current_price,
                trigger_value=self._get_trigger_value(alert, market_data),
                message=self._generate_alert_message(alert, market_data)
            )
            
            # Store triggered alert
            self.triggered_alerts[alert_instance.id] = alert_instance
            self.alerts_triggered += 1
            
            # Send notifications
            await self._send_notifications(alert, alert_instance)
            
            # Deactivate or modify alert based on configuration
            await self._handle_post_trigger(alert)
            
            self.logger.info(f"Triggered alert {alert.id} for {alert.symbol} at {market_data.current_price}")
            
        except Exception as e:
            self.logger.error(f"Error triggering alert {alert.id}: {e}")
    
    def _get_trigger_value(self, alert: AlertConfig, market_data: MarketDataPoint) -> Optional[Decimal]:
        """Get the value that triggered the alert"""
        if alert.alert_type == AlertType.PRICE_CHANGE_PERCENT:
            return market_data.price_change_percent
        elif alert.alert_type == AlertType.VOLUME_SPIKE:
            return Decimal(str(market_data.volume)) if market_data.volume else None
        else:
            return market_data.current_price
    
    def _generate_alert_message(self, alert: AlertConfig, market_data: MarketDataPoint) -> str:
        """Generate alert message"""
        if alert.custom_message:
            return alert.custom_message
        
        symbol = alert.symbol
        price = market_data.current_price
        
        if alert.alert_type == AlertType.PRICE_ABOVE:
            return f"{symbol} price ${price} is above threshold ${alert.threshold_value}"
        elif alert.alert_type == AlertType.PRICE_BELOW:
            return f"{symbol} price ${price} is below threshold ${alert.threshold_value}"
        elif alert.alert_type == AlertType.PRICE_CHANGE_PERCENT:
            change = market_data.price_change_percent
            return f"{symbol} price changed {change}% (threshold: {alert.percentage_threshold}%)"
        elif alert.alert_type == AlertType.VOLUME_SPIKE:
            volume = market_data.volume
            return f"{symbol} volume spike detected: {volume:,} shares"
        elif alert.alert_type == AlertType.MOVING_AVERAGE_CROSS:
            return f"{symbol} moving average crossover detected at ${price}"
        else:
            return f"{symbol} alert triggered at ${price}"
    
    async def _send_notifications(self, alert: AlertConfig, alert_instance: PriceAlert):
        """Send notifications for triggered alert"""
        try:
            # Email notification
            if alert.email_notification:
                success = await self.notification_service.send_email_alert(alert, alert_instance)
                alert_instance.email_sent = success
            
            # Push notification
            if alert.push_notification:
                success = await self.notification_service.send_push_alert(alert, alert_instance)
                alert_instance.push_sent = success
            
            # Webhook notification
            if alert.webhook_url:
                success = await self.notification_service.send_webhook_alert(alert, alert_instance)
                alert_instance.webhook_sent = success
                
        except Exception as e:
            self.logger.error(f"Error sending notifications for alert {alert.id}: {e}")
    
    async def _handle_post_trigger(self, alert: AlertConfig):
        """Handle alert after it's triggered"""
        # For one-time alerts, deactivate after triggering
        if alert.alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_BELOW]:
            alert.is_active = False
            self.logger.info(f"Deactivated one-time alert {alert.id}")
        
        # Check expiration
        if alert.expires_at and datetime.utcnow() >= alert.expires_at:
            await self.remove_alert(alert.id)
            self.logger.info(f"Removed expired alert {alert.id}")
    
    async def _processing_loop(self):
        """Background processing loop"""
        while self._running:
            try:
                await asyncio.sleep(config.alert_check_interval)
                
                # Clean up expired alerts
                await self._cleanup_expired_alerts()
                
                # Clean up old price history
                self._cleanup_price_history()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in alert processing loop: {e}")
    
    async def _cleanup_expired_alerts(self):
        """Remove expired alerts"""
        now = datetime.utcnow()
        expired_alerts = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.expires_at and now >= alert.expires_at:
                expired_alerts.append(alert_id)
        
        for alert_id in expired_alerts:
            await self.remove_alert(alert_id)
            self.logger.info(f"Removed expired alert {alert_id}")
    
    def _cleanup_price_history(self):
        """Clean up old price history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for symbol in list(self.price_history.keys()):
            history = self.price_history[symbol]
            
            # Remove old data points
            recent_history = [
                point for point in history 
                if point.timestamp >= cutoff_time
            ]
            
            if recent_history:
                self.price_history[symbol] = recent_history
            else:
                del self.price_history[symbol]
    
    def _validate_alert_config(self, alert: AlertConfig) -> bool:
        """Validate alert configuration"""
        if not alert.symbol or not alert.user_id:
            return False
        
        if alert.alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_BELOW]:
            if not alert.threshold_value or alert.threshold_value <= 0:
                return False
        
        if alert.alert_type == AlertType.PRICE_CHANGE_PERCENT:
            if not alert.percentage_threshold or alert.percentage_threshold <= 0:
                return False
        
        return True
    
    def get_user_alerts(self, user_id: str) -> List[AlertConfig]:
        """Get all alerts for a user"""
        alert_ids = self.user_alerts.get(user_id, set())
        return [self.active_alerts[alert_id] for alert_id in alert_ids if alert_id in self.active_alerts]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert engine statistics"""
        active_by_type = defaultdict(int)
        active_by_symbol = defaultdict(int)
        
        for alert in self.active_alerts.values():
            if alert.is_active:
                active_by_type[alert.alert_type.value] += 1
                active_by_symbol[alert.symbol] += 1
        
        return {
            "running": self._running,
            "total_active_alerts": len(self.active_alerts),
            "total_users": len(self.user_alerts),
            "alerts_by_type": dict(active_by_type),
            "alerts_by_symbol": dict(active_by_symbol),
            "performance": {
                "alerts_processed": self.alerts_processed,
                "alerts_triggered": self.alerts_triggered,
                "processing_errors": self.processing_errors
            },
            "triggered_alerts_count": len(self.triggered_alerts)
        }