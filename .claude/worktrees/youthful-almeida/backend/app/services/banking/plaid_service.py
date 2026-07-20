"""
Plaid API Integration Service

This module provides comprehensive Plaid API integration for secure banking
data aggregation with account linking, transaction sync, and balance monitoring.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.exceptions import ApiException

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import BankingIntegrationError, ValidationError
from .credential_vault import credential_vault

logger = logging.getLogger(__name__)


@dataclass
class BankAccount:
    """Bank account data structure"""
    account_id: str
    name: str
    type: str
    subtype: str
    balance_available: Optional[float]
    balance_current: Optional[float]
    balance_limit: Optional[float]
    currency: str
    institution_id: str
    mask: Optional[str]


@dataclass
class Transaction:
    """Transaction data structure"""
    transaction_id: str
    account_id: str
    amount: float
    date: datetime
    name: str
    merchant_name: Optional[str]
    category: List[str]
    subcategory: Optional[str]
    pending: bool
    currency: str
    location: Optional[Dict[str, Any]]


class PlaidService:
    """
    Plaid API integration service for secure banking data access.
    
    Features:
    - Account aggregation and linking
    - Real-time transaction sync
    - Balance monitoring
    - Secure credential management
    - Comprehensive error handling
    - Rate limiting and retry logic
    """
    
    def __init__(self):
        self._setup_plaid_client()
        self._retry_attempts = settings.BANKING_MAX_RETRY_ATTEMPTS
        self._retry_delay = settings.BANKING_RETRY_DELAY_SECONDS
    
    def _setup_plaid_client(self):
        """Initialize Plaid API client with configuration"""
        try:
            # Determine environment
            environment_map = {
                "sandbox": plaid.Environment.sandbox,
                "development": plaid.Environment.development,
                "production": plaid.Environment.production
            }
            
            environment = environment_map.get(
                settings.PLAID_ENVIRONMENT,
                plaid.Environment.sandbox
            )
            
            # Configure Plaid client
            configuration = Configuration(
                host=environment,
                api_key={
                    'clientId': settings.PLAID_CLIENT_ID.get_secret_value(),
                    'secret': settings.PLAID_SECRET.get_secret_value(),
                }
            )
            
            api_client = ApiClient(configuration)
            self.client = plaid_api.PlaidApi(api_client)
            
            logger.info(f"Plaid client initialized for {settings.PLAID_ENVIRONMENT} environment")
            
        except Exception as e:
            logger.error(f"Failed to initialize Plaid client: {str(e)}")
            raise BankingIntegrationError("Failed to initialize Plaid service")
    
    async def create_link_token(
        self,
        user_id: str,
        client_name: str = "Financial Planning App"
    ) -> str:
        """
        Create a link token for Plaid Link initialization
        
        Args:
            user_id: Unique user identifier
            client_name: Application name for display
            
        Returns:
            Link token for frontend integration
        """
        try:
            request = LinkTokenCreateRequest(
                products=[Products('transactions')],
                client_name=client_name,
                country_codes=[CountryCode('US')],
                language='en',
                user=LinkTokenCreateRequestUser(client_user_id=user_id)
            )
            
            response = self.client.link_token_create(request)
            link_token = response['link_token']
            
            logger.info(f"Created link token for user {user_id}")
            return link_token
            
        except ApiException as e:
            logger.error(f"Plaid API error creating link token: {str(e)}")
            raise BankingIntegrationError("Failed to create account link token")
        except Exception as e:
            logger.error(f"Unexpected error creating link token: {str(e)}")
            raise BankingIntegrationError("Failed to create account link token")
    
    async def exchange_public_token(
        self,
        public_token: str,
        user_id: str,
        db: AsyncSession
    ) -> str:
        """
        Exchange public token for access token and store securely
        
        Args:
            public_token: Public token from Plaid Link
            user_id: User identifier
            db: Database session
            
        Returns:
            Credential ID for the stored access token
        """
        try:
            # Exchange public token for access token
            request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            
            response = self.client.item_public_token_exchange(request)
            access_token = response['access_token']
            item_id = response['item_id']
            
            # Get institution information
            institution_info = await self._get_institution_info(access_token)
            institution_id = institution_info.get('institution_id', 'unknown')
            
            # Store credentials securely
            credentials = {
                "access_token": access_token,
                "item_id": item_id,
                "institution_id": institution_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            credential_id = await credential_vault.store_credentials(
                user_id=user_id,
                provider="plaid",
                institution_id=institution_id,
                credentials=credentials,
                db=db
            )
            
            logger.info(
                f"Exchanged public token and stored credentials for user {user_id}, "
                f"institution {institution_id}"
            )
            
            return credential_id
            
        except ApiException as e:
            logger.error(f"Plaid API error exchanging public token: {str(e)}")
            raise BankingIntegrationError("Failed to link bank account")
        except Exception as e:
            logger.error(f"Unexpected error exchanging public token: {str(e)}")
            raise BankingIntegrationError("Failed to link bank account")
    
    async def get_accounts(
        self,
        credential_id: str,
        user_id: str,
        db: AsyncSession
    ) -> List[BankAccount]:
        """
        Retrieve bank accounts for a user
        
        Args:
            credential_id: Stored credential identifier
            user_id: User identifier
            db: Database session
            
        Returns:
            List of bank accounts
        """
        try:
            # Retrieve credentials
            credential_data = await credential_vault.retrieve_credentials(
                credential_id, user_id, db
            )
            
            if not credential_data:
                raise BankingIntegrationError("Banking credentials not found")
            
            access_token = credential_data["credentials"]["access_token"]
            
            # Get accounts from Plaid
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            # Convert to our data structure
            accounts = []
            for account_data in response['accounts']:
                account = BankAccount(
                    account_id=account_data['account_id'],
                    name=account_data['name'],
                    type=account_data['type'],
                    subtype=account_data.get('subtype', ''),
                    balance_available=account_data['balances'].get('available'),
                    balance_current=account_data['balances'].get('current'),
                    balance_limit=account_data['balances'].get('limit'),
                    currency=account_data['balances']['iso_currency_code'] or 'USD',
                    institution_id=credential_data["credentials"]["institution_id"],
                    mask=account_data.get('mask')
                )
                accounts.append(account)
            
            logger.info(f"Retrieved {len(accounts)} accounts for user {user_id}")
            return accounts
            
        except ApiException as e:
            logger.error(f"Plaid API error getting accounts: {str(e)}")
            raise BankingIntegrationError("Failed to retrieve bank accounts")
        except Exception as e:
            logger.error(f"Unexpected error getting accounts: {str(e)}")
            raise BankingIntegrationError("Failed to retrieve bank accounts")
    
    async def get_transactions(
        self,
        credential_id: str,
        user_id: str,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_ids: Optional[List[str]] = None
    ) -> List[Transaction]:
        """
        Retrieve transactions for user accounts
        
        Args:
            credential_id: Stored credential identifier
            user_id: User identifier
            db: Database session
            start_date: Transaction start date (default: 30 days ago)
            end_date: Transaction end date (default: today)
            account_ids: Specific account IDs to sync
            
        Returns:
            List of transactions
        """
        try:
            # Retrieve credentials
            credential_data = await credential_vault.retrieve_credentials(
                credential_id, user_id, db
            )
            
            if not credential_data:
                raise BankingIntegrationError("Banking credentials not found")
            
            access_token = credential_data["credentials"]["access_token"]
            
            # Set date range
            if not start_date:
                start_date = datetime.now() - timedelta(
                    days=settings.TRANSACTION_SYNC_DAYS
                )
            if not end_date:
                end_date = datetime.now()
            
            # Get transactions from Plaid
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                account_ids=account_ids
            )
            
            response = self.client.transactions_get(request)
            
            # Convert to our data structure
            transactions = []
            for txn_data in response['transactions']:
                transaction = Transaction(
                    transaction_id=txn_data['transaction_id'],
                    account_id=txn_data['account_id'],
                    amount=txn_data['amount'],
                    date=datetime.strptime(txn_data['date'], '%Y-%m-%d'),
                    name=txn_data['name'],
                    merchant_name=txn_data.get('merchant_name'),
                    category=txn_data.get('category', []),
                    subcategory=txn_data.get('category', [])[-1] if txn_data.get('category') else None,
                    pending=txn_data.get('pending', False),
                    currency=txn_data.get('iso_currency_code', 'USD'),
                    location=txn_data.get('location')
                )
                transactions.append(transaction)
            
            logger.info(
                f"Retrieved {len(transactions)} transactions for user {user_id} "
                f"from {start_date.date()} to {end_date.date()}"
            )
            
            return transactions
            
        except ApiException as e:
            logger.error(f"Plaid API error getting transactions: {str(e)}")
            raise BankingIntegrationError("Failed to retrieve transactions")
        except Exception as e:
            logger.error(f"Unexpected error getting transactions: {str(e)}")
            raise BankingIntegrationError("Failed to retrieve transactions")
    
    async def sync_account_data(
        self,
        credential_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Comprehensive account data synchronization
        
        Args:
            credential_id: Stored credential identifier
            user_id: User identifier
            db: Database session
            
        Returns:
            Sync results with accounts and transactions
        """
        try:
            # Get accounts and transactions concurrently
            accounts_task = self.get_accounts(credential_id, user_id, db)
            transactions_task = self.get_transactions(credential_id, user_id, db)
            
            accounts, transactions = await asyncio.gather(
                accounts_task, transactions_task
            )
            
            sync_result = {
                "user_id": user_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "accounts_count": len(accounts),
                "transactions_count": len(transactions),
                "accounts": [account.__dict__ for account in accounts],
                "transactions": [txn.__dict__ for txn in transactions]
            }
            
            logger.info(
                f"Synced {len(accounts)} accounts and {len(transactions)} "
                f"transactions for user {user_id}"
            )
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing account data: {str(e)}")
            raise BankingIntegrationError("Failed to sync account data")
    
    async def _get_institution_info(self, access_token: str) -> Dict[str, Any]:
        """Get institution information for an access token"""
        try:
            request = ItemGetRequest(access_token=access_token)
            response = self.client.item_get(request)
            
            return {
                "institution_id": response['item']['institution_id'],
                "item_id": response['item']['item_id']
            }
            
        except Exception as e:
            logger.warning(f"Could not get institution info: {str(e)}")
            return {"institution_id": "unknown", "item_id": "unknown"}
    
    async def remove_item(
        self,
        credential_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Remove Plaid item and delete stored credentials
        
        Args:
            credential_id: Stored credential identifier
            user_id: User identifier
            db: Database session
            
        Returns:
            True if removed successfully
        """
        try:
            # Retrieve credentials
            credential_data = await credential_vault.retrieve_credentials(
                credential_id, user_id, db
            )
            
            if not credential_data:
                return False
            
            access_token = credential_data["credentials"]["access_token"]
            
            # Remove item from Plaid (optional - for cleanup)
            try:
                from plaid.model.item_remove_request import ItemRemoveRequest
                request = ItemRemoveRequest(access_token=access_token)
                self.client.item_remove(request)
            except Exception as e:
                logger.warning(f"Could not remove Plaid item: {str(e)}")
            
            # Delete stored credentials
            await credential_vault.delete_credentials(
                credential_id, user_id, db
            )
            
            logger.info(f"Removed Plaid item for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing Plaid item: {str(e)}")
            return False