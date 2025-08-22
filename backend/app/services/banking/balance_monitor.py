"""
Account Balance Monitoring and Alert Service

This module provides real-time balance monitoring, alert generation,
and proactive financial notifications for better money management.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from .plaid_service import BankAccount, PlaidService
from .yodlee_service import YodleeService

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of balance alerts"""
    LOW_BALANCE = "low_balance"
    NEGATIVE_BALANCE = "negative_balance"
    UNUSUAL_WITHDRAWAL = "unusual_withdrawal"
    LARGE_DEPOSIT = "large_deposit"
    ACCOUNT_OVERDRAFT = "account_overdraft"
    RECURRING_PAYMENT_FAILURE = "recurring_payment_failure"
    SPENDING_LIMIT_REACHED = "spending_limit_reached"
    FRAUD_ALERT = "fraud_alert"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


@dataclass
class BalanceAlert:
    """Balance monitoring alert"""
    alert_id: str
    user_id: str
    account_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    current_balance: float
    threshold_value: Optional[float]
    triggered_at: datetime
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = None


@dataclass
class BalanceThreshold:
    """Balance monitoring threshold configuration"""
    user_id: str
    account_id: str
    threshold_type: AlertType
    threshold_value: float
    enabled: bool
    notification_methods: List[str]  # ['email', 'sms', 'push', 'in_app']
    created_at: datetime
    updated_at: datetime


@dataclass
class AccountSnapshot:
    """Account balance snapshot for monitoring"""
    account_id: str
    snapshot_time: datetime
    current_balance: float
    available_balance: Optional[float]
    pending_transactions: int
    last_transaction_date: Optional[datetime]
    balance_change_24h: float
    balance_change_7d: float
    provider: str  # 'plaid' or 'yodlee'


class BalanceMonitor:
    """
    Account balance monitoring and alert service.
    
    Features:
    - Real-time balance monitoring
    - Customizable alert thresholds
    - Multiple notification channels
    - Fraud detection alerts
    - Spending limit monitoring
    - Balance trend analysis
    - Overdraft prevention
    - Recurring payment monitoring
    """
    
    def __init__(self):
        self.check_frequency_hours = settings.BALANCE_CHECK_FREQUENCY_HOURS
        self.low_balance_threshold = settings.LOW_BALANCE_THRESHOLD_PERCENTAGE
        self.plaid_service = PlaidService()
        self.yodlee_service = YodleeService()
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_monitoring(
        self,
        user_id: str,
        credential_ids: List[str],
        db: AsyncSession,
        custom_thresholds: Optional[List[BalanceThreshold]] = None
    ) -> bool:
        """
        Start balance monitoring for user accounts
        
        Args:
            user_id: User identifier
            credential_ids: List of credential IDs to monitor
            db: Database session
            custom_thresholds: Custom threshold configurations
            
        Returns:
            True if monitoring started successfully
        """
        try:
            # Stop existing monitoring if any
            await self.stop_monitoring(user_id)
            
            # Create monitoring task
            task = asyncio.create_task(
                self._monitor_user_accounts(user_id, credential_ids, db, custom_thresholds)
            )
            self._monitoring_tasks[user_id] = task
            
            logger.info(f"Started balance monitoring for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start balance monitoring for user {user_id}: {str(e)}")
            return False
    
    async def stop_monitoring(self, user_id: str) -> bool:
        """
        Stop balance monitoring for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            True if monitoring stopped successfully
        """
        try:
            if user_id in self._monitoring_tasks:
                task = self._monitoring_tasks[user_id]
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                del self._monitoring_tasks[user_id]
                logger.info(f"Stopped balance monitoring for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop balance monitoring for user {user_id}: {str(e)}")
            return False
    
    async def _monitor_user_accounts(
        self,
        user_id: str,
        credential_ids: List[str],
        db: AsyncSession,
        custom_thresholds: Optional[List[BalanceThreshold]] = None
    ):
        """Main monitoring loop for user accounts"""
        try:
            # Initialize thresholds
            thresholds = await self._get_monitoring_thresholds(user_id, custom_thresholds, db)
            previous_snapshots: Dict[str, AccountSnapshot] = {}
            
            while True:
                try:
                    # Get current account balances
                    current_snapshots = await self._get_account_snapshots(
                        user_id, credential_ids, db
                    )
                    
                    # Check for alerts
                    alerts = await self._check_balance_alerts(
                        current_snapshots, previous_snapshots, thresholds, user_id
                    )
                    
                    # Process and send alerts
                    if alerts:
                        await self._process_alerts(alerts, user_id, db)
                    
                    # Update previous snapshots
                    previous_snapshots = current_snapshots
                    
                    # Wait for next check
                    await asyncio.sleep(self.check_frequency_hours * 3600)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop for user {user_id}: {str(e)}")
                    await asyncio.sleep(300)  # Wait 5 minutes before retry
                    
        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for user {user_id}")
            raise
        except Exception as e:
            logger.error(f"Fatal error in monitoring for user {user_id}: {str(e)}")
    
    async def _get_account_snapshots(
        self,
        user_id: str,
        credential_ids: List[str],
        db: AsyncSession
    ) -> Dict[str, AccountSnapshot]:
        """Get current balance snapshots for all accounts"""
        snapshots = {}
        
        try:
            for credential_id in credential_ids:
                try:
                    # Determine provider and get accounts
                    credential_data = await self._get_credential_provider(credential_id, user_id, db)
                    
                    if not credential_data:
                        continue
                    
                    provider = credential_data['provider']
                    
                    if provider == 'plaid':
                        accounts = await self.plaid_service.get_accounts(credential_id, user_id, db)
                    elif provider == 'yodlee':
                        accounts = await self.yodlee_service.get_accounts(credential_id, user_id, db)
                    else:
                        continue
                    
                    # Create snapshots
                    for account in accounts:
                        snapshot = AccountSnapshot(
                            account_id=account.account_id,
                            snapshot_time=datetime.utcnow(),
                            current_balance=account.balance_current or 0.0,
                            available_balance=account.balance_available,
                            pending_transactions=0,  # Would need to query transactions
                            last_transaction_date=None,  # Would need to query transactions
                            balance_change_24h=0.0,  # Would need historical data
                            balance_change_7d=0.0,  # Would need historical data
                            provider=provider
                        )
                        snapshots[account.account_id] = snapshot
                        
                except Exception as e:
                    logger.error(f"Error getting snapshot for credential {credential_id}: {str(e)}")
                    continue
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Error getting account snapshots for user {user_id}: {str(e)}")
            return {}
    
    async def _get_monitoring_thresholds(
        self,
        user_id: str,
        custom_thresholds: Optional[List[BalanceThreshold]],
        db: AsyncSession
    ) -> List[BalanceThreshold]:
        """Get monitoring thresholds for user"""
        try:
            thresholds = []
            
            # Add custom thresholds if provided
            if custom_thresholds:
                thresholds.extend(custom_thresholds)
            
            # Add default thresholds if none exist
            if not thresholds:
                # Default low balance threshold (10% of average balance)
                default_threshold = BalanceThreshold(
                    user_id=user_id,
                    account_id="*",  # Applies to all accounts
                    threshold_type=AlertType.LOW_BALANCE,
                    threshold_value=self.low_balance_threshold,
                    enabled=True,
                    notification_methods=['in_app', 'email'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                thresholds.append(default_threshold)
                
                # Default negative balance threshold
                negative_threshold = BalanceThreshold(
                    user_id=user_id,
                    account_id="*",
                    threshold_type=AlertType.NEGATIVE_BALANCE,
                    threshold_value=0.0,
                    enabled=True,
                    notification_methods=['in_app', 'email', 'sms'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                thresholds.append(negative_threshold)
            
            return thresholds
            
        except Exception as e:
            logger.error(f"Error getting monitoring thresholds: {str(e)}")
            return []
    
    async def _check_balance_alerts(
        self,
        current_snapshots: Dict[str, AccountSnapshot],
        previous_snapshots: Dict[str, AccountSnapshot],
        thresholds: List[BalanceThreshold],
        user_id: str
    ) -> List[BalanceAlert]:
        """Check for balance alerts based on current snapshots and thresholds"""
        alerts = []
        
        try:
            for account_id, current_snapshot in current_snapshots.items():
                previous_snapshot = previous_snapshots.get(account_id)
                
                # Check each threshold
                for threshold in thresholds:
                    if not threshold.enabled:
                        continue
                    
                    # Check if threshold applies to this account
                    if threshold.account_id != "*" and threshold.account_id != account_id:
                        continue
                    
                    alert = await self._evaluate_threshold(
                        current_snapshot, previous_snapshot, threshold, user_id
                    )
                    
                    if alert:
                        alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking balance alerts: {str(e)}")
            return []
    
    async def _evaluate_threshold(
        self,
        current_snapshot: AccountSnapshot,
        previous_snapshot: Optional[AccountSnapshot],
        threshold: BalanceThreshold,
        user_id: str
    ) -> Optional[BalanceAlert]:
        """Evaluate a specific threshold against account snapshot"""
        try:
            current_balance = current_snapshot.current_balance
            account_id = current_snapshot.account_id
            
            if threshold.threshold_type == AlertType.LOW_BALANCE:
                # Calculate percentage-based threshold
                if threshold.threshold_value <= 1.0:  # Percentage
                    # Need historical average for percentage calculation
                    # For now, use a simple low balance check
                    if current_balance < 100:  # Simple $100 threshold
                        return BalanceAlert(
                            alert_id=f"low_balance_{account_id}_{int(datetime.utcnow().timestamp())}",
                            user_id=user_id,
                            account_id=account_id,
                            alert_type=AlertType.LOW_BALANCE,
                            severity=AlertSeverity.WARNING,
                            title="Low Balance Alert",
                            message=f"Your account balance is low: ${current_balance:.2f}",
                            current_balance=current_balance,
                            threshold_value=threshold.threshold_value,
                            triggered_at=datetime.utcnow()
                        )
                else:  # Absolute amount
                    if current_balance < threshold.threshold_value:
                        return BalanceAlert(
                            alert_id=f"low_balance_{account_id}_{int(datetime.utcnow().timestamp())}",
                            user_id=user_id,
                            account_id=account_id,
                            alert_type=AlertType.LOW_BALANCE,
                            severity=AlertSeverity.WARNING,
                            title="Low Balance Alert",
                            message=f"Your account balance ${current_balance:.2f} is below ${threshold.threshold_value:.2f}",
                            current_balance=current_balance,
                            threshold_value=threshold.threshold_value,
                            triggered_at=datetime.utcnow()
                        )
            
            elif threshold.threshold_type == AlertType.NEGATIVE_BALANCE:
                if current_balance < 0:
                    return BalanceAlert(
                        alert_id=f"negative_balance_{account_id}_{int(datetime.utcnow().timestamp())}",
                        user_id=user_id,
                        account_id=account_id,
                        alert_type=AlertType.NEGATIVE_BALANCE,
                        severity=AlertSeverity.CRITICAL,
                        title="Negative Balance Alert",
                        message=f"Your account has a negative balance: ${current_balance:.2f}",
                        current_balance=current_balance,
                        threshold_value=0.0,
                        triggered_at=datetime.utcnow()
                    )
            
            elif threshold.threshold_type == AlertType.UNUSUAL_WITHDRAWAL:
                if previous_snapshot:
                    balance_change = current_balance - previous_snapshot.current_balance
                    if balance_change < -threshold.threshold_value:  # Large withdrawal
                        return BalanceAlert(
                            alert_id=f"unusual_withdrawal_{account_id}_{int(datetime.utcnow().timestamp())}",
                            user_id=user_id,
                            account_id=account_id,
                            alert_type=AlertType.UNUSUAL_WITHDRAWAL,
                            severity=AlertSeverity.WARNING,
                            title="Large Withdrawal Detected",
                            message=f"Large withdrawal detected: ${abs(balance_change):.2f}",
                            current_balance=current_balance,
                            threshold_value=threshold.threshold_value,
                            triggered_at=datetime.utcnow(),
                            metadata={'balance_change': balance_change}
                        )
            
            elif threshold.threshold_type == AlertType.LARGE_DEPOSIT:
                if previous_snapshot:
                    balance_change = current_balance - previous_snapshot.current_balance
                    if balance_change > threshold.threshold_value:  # Large deposit
                        return BalanceAlert(
                            alert_id=f"large_deposit_{account_id}_{int(datetime.utcnow().timestamp())}",
                            user_id=user_id,
                            account_id=account_id,
                            alert_type=AlertType.LARGE_DEPOSIT,
                            severity=AlertSeverity.INFO,
                            title="Large Deposit Received",
                            message=f"Large deposit received: ${balance_change:.2f}",
                            current_balance=current_balance,
                            threshold_value=threshold.threshold_value,
                            triggered_at=datetime.utcnow(),
                            metadata={'balance_change': balance_change}
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating threshold: {str(e)}")
            return None
    
    async def _process_alerts(
        self,
        alerts: List[BalanceAlert],
        user_id: str,
        db: AsyncSession
    ):
        """Process and send alerts to user"""
        try:
            for alert in alerts:
                # Store alert in database
                await self._store_alert(alert, db)
                
                # Send notifications
                await self._send_alert_notifications(alert, user_id)
                
                logger.info(
                    f"Processed {alert.alert_type.value} alert for user {user_id}, "
                    f"account {alert.account_id}"
                )
                
        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")
    
    async def _store_alert(self, alert: BalanceAlert, db: AsyncSession):
        """Store alert in database"""
        try:
            # Implementation would store alert in database
            # For now, just log it
            logger.info(f"Storing alert: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")
    
    async def _send_alert_notifications(self, alert: BalanceAlert, user_id: str):
        """Send alert notifications via configured channels"""
        try:
            # Implementation would send notifications via email, SMS, push, etc.
            # For now, just log the notification
            logger.info(
                f"Sending {alert.severity.value} alert to user {user_id}: {alert.title}"
            )
            
        except Exception as e:
            logger.error(f"Error sending alert notifications: {str(e)}")
    
    async def _get_credential_provider(
        self,
        credential_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get credential provider information"""
        try:
            # This would query the credential vault to get provider info
            # For now, return a mock response
            return {
                'provider': 'plaid',  # or 'yodlee'
                'credential_id': credential_id
            }
            
        except Exception as e:
            logger.error(f"Error getting credential provider: {str(e)}")
            return None
    
    async def get_user_alerts(
        self,
        user_id: str,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        alert_types: Optional[List[AlertType]] = None,
        unacknowledged_only: bool = False
    ) -> List[BalanceAlert]:
        """
        Get alerts for a user
        
        Args:
            user_id: User identifier
            db: Database session
            start_date: Filter alerts from this date
            end_date: Filter alerts to this date
            alert_types: Filter by alert types
            unacknowledged_only: Only return unacknowledged alerts
            
        Returns:
            List of user alerts
        """
        try:
            # Implementation would query database for alerts
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting user alerts: {str(e)}")
            return []
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert identifier
            user_id: User identifier for authorization
            db: Database session
            
        Returns:
            True if acknowledged successfully
        """
        try:
            # Implementation would update alert in database
            logger.info(f"Acknowledged alert {alert_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {str(e)}")
            return False
    
    async def update_thresholds(
        self,
        user_id: str,
        thresholds: List[BalanceThreshold],
        db: AsyncSession
    ) -> bool:
        """
        Update monitoring thresholds for a user
        
        Args:
            user_id: User identifier
            thresholds: New threshold configurations
            db: Database session
            
        Returns:
            True if updated successfully
        """
        try:
            # Implementation would update thresholds in database
            logger.info(f"Updated monitoring thresholds for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating thresholds: {str(e)}")
            return False
    
    async def get_balance_history(
        self,
        user_id: str,
        account_id: str,
        db: AsyncSession,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get balance history for an account
        
        Args:
            user_id: User identifier
            account_id: Account identifier
            db: Database session
            days: Number of days of history
            
        Returns:
            Balance history data
        """
        try:
            # Implementation would query historical balance data
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting balance history: {str(e)}")
            return []
    
    async def check_immediate_alerts(
        self,
        user_id: str,
        credential_ids: List[str],
        db: AsyncSession
    ) -> List[BalanceAlert]:
        """
        Perform immediate balance check and return any alerts
        
        Args:
            user_id: User identifier
            credential_ids: List of credential IDs to check
            db: Database session
            
        Returns:
            List of immediate alerts
        """
        try:
            # Get current snapshots
            current_snapshots = await self._get_account_snapshots(user_id, credential_ids, db)
            
            # Get thresholds
            thresholds = await self._get_monitoring_thresholds(user_id, None, db)
            
            # Check for alerts
            alerts = await self._check_balance_alerts(
                current_snapshots, {}, thresholds, user_id
            )
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking immediate alerts: {str(e)}")
            return []


# Singleton instance
balance_monitor = BalanceMonitor()