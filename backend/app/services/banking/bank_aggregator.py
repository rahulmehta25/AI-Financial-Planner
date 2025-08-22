"""
Bank Aggregator Service

This module provides a unified interface for banking integration,
orchestrating all banking services and providing a single point of access.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BankingIntegrationError, ValidationError
from .plaid_service import PlaidService, BankAccount, Transaction
from .yodlee_service import YodleeService
from .credential_vault import credential_vault
from .transaction_categorizer import transaction_categorizer, CategoryPrediction
from .cash_flow_analyzer import cash_flow_analyzer
from .spending_pattern_detector import spending_pattern_detector
from .balance_monitor import balance_monitor

logger = logging.getLogger(__name__)


class BankingProvider(Enum):
    """Supported banking providers"""
    PLAID = "plaid"
    YODLEE = "yodlee"


@dataclass
class BankingConnection:
    """Banking connection information"""
    credential_id: str
    provider: BankingProvider
    institution_id: str
    institution_name: str
    connected_at: datetime
    last_sync: Optional[datetime]
    status: str  # 'active', 'error', 'expired'
    account_count: int


@dataclass
class ComprehensiveFinancialData:
    """Complete financial data for a user"""
    user_id: str
    generated_at: datetime
    connections: List[BankingConnection]
    accounts: List[BankAccount]
    transactions: List[Transaction]
    categorized_transactions: List[CategoryPrediction]
    cash_flow_analysis: Dict[str, Any]
    spending_patterns: Dict[str, Any]
    balance_alerts: List[Dict[str, Any]]
    financial_insights: List[str]
    recommendations: List[str]


class BankAggregator:
    """
    Unified bank aggregation service.
    
    Features:
    - Multi-provider support (Plaid, Yodlee)
    - Automatic failover between providers
    - Comprehensive financial analysis
    - Real-time monitoring and alerts
    - Secure credential management
    - Intelligent transaction categorization
    - Advanced analytics and insights
    """
    
    def __init__(self):
        self.plaid_service = PlaidService()
        self.yodlee_service = YodleeService()
        self._provider_priority = [BankingProvider.PLAID, BankingProvider.YODLEE]
    
    async def create_link_token(
        self,
        user_id: str,
        preferred_provider: Optional[BankingProvider] = None
    ) -> Dict[str, Any]:
        """
        Create a link token for account connection
        
        Args:
            user_id: User identifier
            preferred_provider: Preferred banking provider
            
        Returns:
            Link token and provider information
        """
        try:
            # Try preferred provider first, then fallback
            providers_to_try = [preferred_provider] if preferred_provider else self._provider_priority
            
            for provider in providers_to_try:
                try:
                    if provider == BankingProvider.PLAID:
                        link_token = await self.plaid_service.create_link_token(user_id)
                        return {
                            "link_token": link_token,
                            "provider": "plaid",
                            "success": True
                        }
                    
                    elif provider == BankingProvider.YODLEE:
                        # Yodlee requires different setup
                        providers = await self.yodlee_service.get_providers()
                        return {
                            "providers": providers[:50],  # Limit to 50 providers
                            "provider": "yodlee",
                            "success": True
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to create link token with {provider.value}: {str(e)}")
                    continue
            
            raise BankingIntegrationError("No banking providers available")
            
        except Exception as e:
            logger.error(f"Error creating link token: {str(e)}")
            raise BankingIntegrationError("Failed to create banking link token")
    
    async def connect_bank_account(
        self,
        user_id: str,
        connection_data: Dict[str, Any],
        provider: BankingProvider,
        db: AsyncSession
    ) -> str:
        """
        Connect a bank account using the specified provider
        
        Args:
            user_id: User identifier
            connection_data: Provider-specific connection data
            provider: Banking provider to use
            db: Database session
            
        Returns:
            Credential ID for the connected account
        """
        try:
            if provider == BankingProvider.PLAID:
                public_token = connection_data.get('public_token')
                if not public_token:
                    raise ValidationError("Missing public_token for Plaid connection")
                
                credential_id = await self.plaid_service.exchange_public_token(
                    public_token, user_id, db
                )
                
            elif provider == BankingProvider.YODLEE:
                provider_id = connection_data.get('provider_id')
                credentials = connection_data.get('credentials', {})
                
                if not provider_id or not credentials:
                    raise ValidationError("Missing provider_id or credentials for Yodlee connection")
                
                # Create Yodlee user if needed
                user_data = connection_data.get('user_data', {})
                yodlee_login = await self.yodlee_service.create_user(user_id, user_data)
                
                # Get user access token
                password = credentials.get('password', f'TempPass123!{user_id}')
                user_access_token = await self.yodlee_service.get_user_access_token(
                    yodlee_login, password
                )
                
                # Add account
                credential_id = await self.yodlee_service.add_account(
                    user_access_token, provider_id, credentials, user_id, db
                )
                
            else:
                raise ValidationError(f"Unsupported provider: {provider}")
            
            # Start balance monitoring
            await balance_monitor.start_monitoring(user_id, [credential_id], db)
            
            logger.info(f"Connected bank account for user {user_id} via {provider.value}")
            return credential_id
            
        except Exception as e:
            logger.error(f"Error connecting bank account: {str(e)}")
            raise BankingIntegrationError("Failed to connect bank account")
    
    async def get_user_connections(
        self,
        user_id: str,
        db: AsyncSession
    ) -> List[BankingConnection]:
        """
        Get all banking connections for a user
        
        Args:
            user_id: User identifier
            db: Database session
            
        Returns:
            List of banking connections
        """
        try:
            connections = []
            
            # Get credentials from vault
            credentials_list = await credential_vault.list_user_credentials(user_id, db)
            
            for cred_metadata in credentials_list:
                # Get detailed credential data
                credential_data = await credential_vault.retrieve_credentials(
                    cred_metadata['credential_id'], user_id, db
                )
                
                if credential_data:
                    provider = BankingProvider(credential_data['provider'])
                    
                    # Get account count
                    try:
                        if provider == BankingProvider.PLAID:
                            accounts = await self.plaid_service.get_accounts(
                                cred_metadata['credential_id'], user_id, db
                            )
                        else:
                            accounts = await self.yodlee_service.get_accounts(
                                cred_metadata['credential_id'], user_id, db
                            )
                        account_count = len(accounts)
                        status = 'active'
                    except Exception:
                        account_count = 0
                        status = 'error'
                    
                    connection = BankingConnection(
                        credential_id=cred_metadata['credential_id'],
                        provider=provider,
                        institution_id=credential_data['institution_id'],
                        institution_name=credential_data['institution_id'],  # Would need institution name lookup
                        connected_at=datetime.fromisoformat(credential_data['created_at']),
                        last_sync=None,  # Would need to track sync times
                        status=status,
                        account_count=account_count
                    )
                    connections.append(connection)
            
            return connections
            
        except Exception as e:
            logger.error(f"Error getting user connections: {str(e)}")
            return []
    
    async def sync_all_accounts(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Sync all bank accounts for a user
        
        Args:
            user_id: User identifier
            db: Database session
            
        Returns:
            Sync results for all accounts
        """
        try:
            connections = await self.get_user_connections(user_id, db)
            sync_results = []
            total_accounts = 0
            total_transactions = 0
            
            for connection in connections:
                try:
                    if connection.provider == BankingProvider.PLAID:
                        result = await self.plaid_service.sync_account_data(
                            connection.credential_id, user_id, db
                        )
                    else:
                        result = await self.yodlee_service.sync_account_data(
                            connection.credential_id, user_id, db
                        )
                    
                    sync_results.append({
                        "credential_id": connection.credential_id,
                        "provider": connection.provider.value,
                        "status": "success",
                        "accounts_count": result.get('accounts_count', 0),
                        "transactions_count": result.get('transactions_count', 0)
                    })
                    
                    total_accounts += result.get('accounts_count', 0)
                    total_transactions += result.get('transactions_count', 0)
                    
                except Exception as e:
                    logger.error(f"Failed to sync {connection.credential_id}: {str(e)}")
                    sync_results.append({
                        "credential_id": connection.credential_id,
                        "provider": connection.provider.value,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "user_id": user_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "total_connections": len(connections),
                "total_accounts": total_accounts,
                "total_transactions": total_transactions,
                "sync_results": sync_results
            }
            
        except Exception as e:
            logger.error(f"Error syncing all accounts: {str(e)}")
            raise BankingIntegrationError("Failed to sync accounts")
    
    async def get_comprehensive_financial_data(
        self,
        user_id: str,
        db: AsyncSession,
        include_analysis: bool = True,
        lookback_days: int = 90
    ) -> ComprehensiveFinancialData:
        """
        Get comprehensive financial data and analysis for a user
        
        Args:
            user_id: User identifier
            db: Database session
            include_analysis: Whether to include advanced analysis
            lookback_days: Days of transaction history to analyze
            
        Returns:
            Complete financial data with analysis
        """
        try:
            # Get connections
            connections = await self.get_user_connections(user_id, db)
            
            # Collect all accounts and transactions
            all_accounts = []
            all_transactions = []
            
            for connection in connections:
                try:
                    if connection.provider == BankingProvider.PLAID:
                        accounts = await self.plaid_service.get_accounts(
                            connection.credential_id, user_id, db
                        )
                        transactions = await self.plaid_service.get_transactions(
                            connection.credential_id, user_id, db,
                            start_date=datetime.utcnow() - timedelta(days=lookback_days)
                        )
                    else:
                        accounts = await self.yodlee_service.get_accounts(
                            connection.credential_id, user_id, db
                        )
                        transactions = await self.yodlee_service.get_transactions(
                            connection.credential_id, user_id, db,
                            start_date=datetime.utcnow() - timedelta(days=lookback_days)
                        )
                    
                    all_accounts.extend(accounts)
                    all_transactions.extend(transactions)
                    
                except Exception as e:
                    logger.error(f"Error getting data for {connection.credential_id}: {str(e)}")
                    continue
            
            # Initialize analysis variables
            categorized_transactions = []
            cash_flow_analysis = {}
            spending_patterns = {}
            balance_alerts = []
            financial_insights = []
            recommendations = []
            
            if include_analysis and all_transactions:
                # Categorize transactions
                categorized_transactions = await transaction_categorizer.categorize_transactions_batch(
                    all_transactions, user_id
                )
                
                # Cash flow analysis
                cash_flow_analysis = await cash_flow_analyzer.analyze_cash_flow(
                    all_transactions, all_accounts, categorized_transactions, user_id
                )
                
                # Spending pattern analysis
                spending_patterns = await spending_pattern_detector.analyze_spending_patterns(
                    all_transactions, categorized_transactions, user_id, lookback_days
                )
                
                # Get balance alerts
                credential_ids = [conn.credential_id for conn in connections]
                balance_alerts_objects = await balance_monitor.check_immediate_alerts(
                    user_id, credential_ids, db
                )
                balance_alerts = [alert.__dict__ for alert in balance_alerts_objects]
                
                # Generate insights
                financial_insights = self._generate_financial_insights(
                    cash_flow_analysis, spending_patterns, balance_alerts
                )
                
                # Generate recommendations
                recommendations = self._generate_recommendations(
                    cash_flow_analysis, spending_patterns, financial_insights
                )
            
            return ComprehensiveFinancialData(
                user_id=user_id,
                generated_at=datetime.utcnow(),
                connections=connections,
                accounts=all_accounts,
                transactions=all_transactions,
                categorized_transactions=categorized_transactions,
                cash_flow_analysis=cash_flow_analysis,
                spending_patterns=spending_patterns,
                balance_alerts=balance_alerts,
                financial_insights=financial_insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error getting comprehensive financial data: {str(e)}")
            raise BankingIntegrationError("Failed to get financial data")
    
    async def disconnect_bank_account(
        self,
        user_id: str,
        credential_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Disconnect a bank account
        
        Args:
            user_id: User identifier
            credential_id: Credential ID to disconnect
            db: Database session
            
        Returns:
            True if disconnected successfully
        """
        try:
            # Get credential data to determine provider
            credential_data = await credential_vault.retrieve_credentials(
                credential_id, user_id, db
            )
            
            if not credential_data:
                return False
            
            provider = BankingProvider(credential_data['provider'])
            
            # Remove from provider
            if provider == BankingProvider.PLAID:
                await self.plaid_service.remove_item(credential_id, user_id, db)
            else:
                await self.yodlee_service.remove_account(credential_id, user_id, db)
            
            # Stop monitoring
            await balance_monitor.stop_monitoring(user_id)
            
            logger.info(f"Disconnected bank account {credential_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting bank account: {str(e)}")
            return False
    
    def _generate_financial_insights(
        self,
        cash_flow_analysis: Dict[str, Any],
        spending_patterns: Dict[str, Any],
        balance_alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate financial insights from analysis data"""
        insights = []
        
        try:
            # Cash flow insights
            if cash_flow_analysis.get('financial_health'):
                health_score = cash_flow_analysis['financial_health']['overall_score']
                if health_score >= 80:
                    insights.append("Your financial health is excellent! Keep up the good work.")
                elif health_score >= 60:
                    insights.append("Your financial health is good with room for improvement.")
                else:
                    insights.append("Focus on improving your financial fundamentals.")
            
            # Spending pattern insights
            if spending_patterns.get('insights'):
                pattern_insights = spending_patterns['insights']
                for insight in pattern_insights[:3]:  # Top 3 insights
                    if isinstance(insight, dict):
                        insights.append(insight.get('description', ''))
                    else:
                        insights.append(str(insight))
            
            # Alert insights
            if balance_alerts:
                critical_alerts = [a for a in balance_alerts if a.get('severity') == 'critical']
                if critical_alerts:
                    insights.append(f"You have {len(critical_alerts)} critical account alerts that need attention.")
            
            return insights[:10]  # Limit to 10 insights
            
        except Exception as e:
            logger.error(f"Error generating financial insights: {str(e)}")
            return ["Unable to generate financial insights from current data"]
    
    def _generate_recommendations(
        self,
        cash_flow_analysis: Dict[str, Any],
        spending_patterns: Dict[str, Any],
        financial_insights: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        try:
            # Cash flow recommendations
            if cash_flow_analysis.get('recommendations'):
                recommendations.extend(cash_flow_analysis['recommendations'][:3])
            
            # Spending pattern recommendations
            if spending_patterns.get('recommendations'):
                recommendations.extend(spending_patterns['recommendations'][:3])
            
            # General recommendations
            general_recommendations = [
                "Review your spending patterns monthly for better budgeting",
                "Set up automatic savings to build wealth consistently",
                "Monitor account balances regularly to avoid overdrafts",
                "Consider setting spending limits for major expense categories",
                "Build an emergency fund covering 3-6 months of expenses"
            ]
            
            # Add general recommendations if we don't have enough specific ones
            while len(recommendations) < 5:
                for rec in general_recommendations:
                    if rec not in recommendations:
                        recommendations.append(rec)
                        break
                else:
                    break
            
            return recommendations[:10]  # Limit to 10 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Regular financial review and budgeting is recommended"]


# Singleton instance
bank_aggregator = BankAggregator()