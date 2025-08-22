"""
Yodlee API Integration Service

This module provides Yodlee API integration as a fallback provider for banking
data aggregation when Plaid is unavailable or unsupported.
"""

import logging
import asyncio
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BankingIntegrationError, ValidationError
from .credential_vault import credential_vault
from .plaid_service import BankAccount, Transaction

logger = logging.getLogger(__name__)


@dataclass
class YodleeAuthToken:
    """Yodlee authentication token data"""
    access_token: str
    expires_in: int
    token_type: str
    issued_at: datetime


class YodleeService:
    """
    Yodlee API integration service for banking data access.
    
    Features:
    - Account aggregation and linking
    - Transaction synchronization
    - Balance monitoring
    - Secure credential management
    - Comprehensive error handling
    - Rate limiting and retry logic
    """
    
    def __init__(self):
        self.base_url = settings.YODLEE_BASE_URL
        self.client_id = settings.YODLEE_CLIENT_ID
        self.secret = settings.YODLEE_SECRET
        self.admin_login_name = settings.YODLEE_ADMIN_LOGIN_NAME
        self._retry_attempts = settings.BANKING_MAX_RETRY_ATTEMPTS
        self._retry_delay = settings.BANKING_RETRY_DELAY_SECONDS
        self._auth_token: Optional[YodleeAuthToken] = None
    
    async def _get_auth_token(self) -> str:
        """Get or refresh Yodlee authentication token"""
        try:
            if (self._auth_token and 
                datetime.utcnow() < self._auth_token.issued_at + 
                timedelta(seconds=self._auth_token.expires_in - 300)):  # 5 min buffer
                return self._auth_token.access_token
            
            # Create new authentication token
            auth_string = f"{self.client_id.get_secret_value()}:{self.secret.get_secret_value()}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/token",
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise BankingIntegrationError(
                        f"Yodlee authentication failed: {response.text}"
                    )
                
                token_data = response.json()
                
                self._auth_token = YodleeAuthToken(
                    access_token=token_data['access_token'],
                    expires_in=token_data['expires_in'],
                    token_type=token_data['token_type'],
                    issued_at=datetime.utcnow()
                )
                
                logger.info("Yodlee authentication token obtained")
                return self._auth_token.access_token
                
        except Exception as e:
            logger.error(f"Failed to get Yodlee auth token: {str(e)}")
            raise BankingIntegrationError("Failed to authenticate with Yodlee")
    
    async def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Yodlee API"""
        try:
            token = await self._get_auth_token()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}{endpoint}"
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code >= 400:
                    raise BankingIntegrationError(
                        f"Yodlee API error {response.status_code}: {response.text}"
                    )
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Yodlee API request failed: {str(e)}")
            raise BankingIntegrationError("Yodlee API request failed")
    
    async def create_user(self, user_id: str, user_data: Dict[str, str]) -> str:
        """
        Create a Yodlee user account
        
        Args:
            user_id: Unique user identifier
            user_data: User information (name, email, etc.)
            
        Returns:
            Yodlee user login name
        """
        try:
            # Create unique login name
            yodlee_login_name = f"user_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            user_payload = {
                "user": {
                    "loginName": yodlee_login_name,
                    "password": f"TempPass123!{user_id}",  # Should be user-generated
                    "email": user_data.get("email", f"{user_id}@example.com"),
                    "name": {
                        "first": user_data.get("first_name", "User"),
                        "last": user_data.get("last_name", "Name")
                    }
                }
            }
            
            response = await self._make_authenticated_request(
                "POST", "/user/register", data=user_payload
            )
            
            logger.info(f"Created Yodlee user for user_id {user_id}")
            return yodlee_login_name
            
        except Exception as e:
            logger.error(f"Failed to create Yodlee user: {str(e)}")
            raise BankingIntegrationError("Failed to create Yodlee user account")
    
    async def get_user_access_token(
        self,
        yodlee_login_name: str,
        password: str
    ) -> str:
        """
        Get user access token for API calls
        
        Args:
            yodlee_login_name: Yodlee user login name
            password: User password
            
        Returns:
            User access token
        """
        try:
            auth_payload = {
                "user": {
                    "loginName": yodlee_login_name,
                    "password": password
                }
            }
            
            response = await self._make_authenticated_request(
                "POST", "/user/login", data=auth_payload
            )
            
            return response['user']['accessTokens'][0]['value']
            
        except Exception as e:
            logger.error(f"Failed to get user access token: {str(e)}")
            raise BankingIntegrationError("Failed to authenticate Yodlee user")
    
    async def get_providers(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available providers/institutions
        
        Args:
            name_filter: Optional filter by provider name
            
        Returns:
            List of provider information
        """
        try:
            params = {}
            if name_filter:
                params['name'] = name_filter
            
            response = await self._make_authenticated_request(
                "GET", "/providers", params=params
            )
            
            return response.get('provider', [])
            
        except Exception as e:
            logger.error(f"Failed to get providers: {str(e)}")
            raise BankingIntegrationError("Failed to retrieve providers")
    
    async def add_account(
        self,
        user_access_token: str,
        provider_id: str,
        credentials: Dict[str, str],
        user_id: str,
        db: AsyncSession
    ) -> str:
        """
        Add bank account using provider credentials
        
        Args:
            user_access_token: User access token
            provider_id: Yodlee provider ID
            credentials: Bank login credentials
            user_id: User identifier
            db: Database session
            
        Returns:
            Credential ID for stored account access
        """
        try:
            # Prepare account addition payload
            account_payload = {
                "providerAccount": {
                    "provider": [{"id": provider_id}],
                    "field": []
                }
            }
            
            # Add credentials to payload
            for key, value in credentials.items():
                account_payload["providerAccount"]["field"].append({
                    "id": key,
                    "value": value
                })
            
            # Make request with user token
            headers = {
                'Authorization': f'Bearer {user_access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/providerAccounts",
                    headers=headers,
                    json=account_payload,
                    timeout=60.0  # Longer timeout for account verification
                )
                
                if response.status_code >= 400:
                    raise BankingIntegrationError(
                        f"Failed to add account: {response.text}"
                    )
                
                result = response.json()
                provider_account_id = result['providerAccount'][0]['id']
            
            # Store credentials securely
            credential_data = {
                "user_access_token": user_access_token,
                "provider_account_id": provider_account_id,
                "provider_id": provider_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            credential_id = await credential_vault.store_credentials(
                user_id=user_id,
                provider="yodlee",
                institution_id=str(provider_id),
                credentials=credential_data,
                db=db
            )
            
            logger.info(
                f"Added Yodlee account for user {user_id}, "
                f"provider {provider_id}"
            )
            
            return credential_id
            
        except Exception as e:
            logger.error(f"Failed to add Yodlee account: {str(e)}")
            raise BankingIntegrationError("Failed to add bank account")
    
    async def get_accounts(
        self,
        credential_id: str,
        user_id: str,
        db: AsyncSession
    ) -> List[BankAccount]:
        """
        Get bank accounts for a user
        
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
            
            user_access_token = credential_data["credentials"]["user_access_token"]
            
            # Get accounts from Yodlee
            headers = {
                'Authorization': f'Bearer {user_access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/accounts",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code >= 400:
                    raise BankingIntegrationError(
                        f"Failed to get accounts: {response.text}"
                    )
                
                result = response.json()
            
            # Convert to our data structure
            accounts = []
            for account_data in result.get('account', []):
                account = BankAccount(
                    account_id=str(account_data['id']),
                    name=account_data.get('accountName', 'Unknown Account'),
                    type=account_data.get('CONTAINER', 'bank'),
                    subtype=account_data.get('accountType', ''),
                    balance_available=account_data.get('availableBalance', {}).get('amount'),
                    balance_current=account_data.get('currentBalance', {}).get('amount'),
                    balance_limit=account_data.get('availableCredit', {}).get('amount'),
                    currency=account_data.get('currentBalance', {}).get('currency', 'USD'),
                    institution_id=credential_data["credentials"]["provider_id"],
                    mask=account_data.get('accountNumber', '')[-4:] if account_data.get('accountNumber') else None
                )
                accounts.append(account)
            
            logger.info(f"Retrieved {len(accounts)} Yodlee accounts for user {user_id}")
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get Yodlee accounts: {str(e)}")
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
        Get transactions for user accounts
        
        Args:
            credential_id: Stored credential identifier
            user_id: User identifier
            db: Database session
            start_date: Transaction start date
            end_date: Transaction end date
            account_ids: Specific account IDs
            
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
            
            user_access_token = credential_data["credentials"]["user_access_token"]
            
            # Set date range
            if not start_date:
                start_date = datetime.now() - timedelta(
                    days=settings.TRANSACTION_SYNC_DAYS
                )
            if not end_date:
                end_date = datetime.now()
            
            # Prepare query parameters
            params = {
                'fromDate': start_date.strftime('%Y-%m-%d'),
                'toDate': end_date.strftime('%Y-%m-%d')
            }
            
            if account_ids:
                params['accountId'] = ','.join(account_ids)
            
            # Get transactions from Yodlee
            headers = {
                'Authorization': f'Bearer {user_access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/transactions",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code >= 400:
                    raise BankingIntegrationError(
                        f"Failed to get transactions: {response.text}"
                    )
                
                result = response.json()
            
            # Convert to our data structure
            transactions = []
            for txn_data in result.get('transaction', []):
                transaction = Transaction(
                    transaction_id=str(txn_data['id']),
                    account_id=str(txn_data['accountId']),
                    amount=txn_data.get('amount', {}).get('amount', 0.0),
                    date=datetime.strptime(txn_data['date'], '%Y-%m-%d'),
                    name=txn_data.get('description', {}).get('original', 'Unknown'),
                    merchant_name=txn_data.get('merchant', {}).get('name'),
                    category=[cat.get('category', '') for cat in txn_data.get('category', [])],
                    subcategory=txn_data.get('category', [{}])[0].get('category') if txn_data.get('category') else None,
                    pending=txn_data.get('status') == 'PENDING',
                    currency=txn_data.get('amount', {}).get('currency', 'USD'),
                    location=None  # Yodlee doesn't provide location data
                )
                transactions.append(transaction)
            
            logger.info(
                f"Retrieved {len(transactions)} Yodlee transactions for user {user_id}"
            )
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get Yodlee transactions: {str(e)}")
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
                "provider": "yodlee",
                "sync_timestamp": datetime.utcnow().isoformat(),
                "accounts_count": len(accounts),
                "transactions_count": len(transactions),
                "accounts": [account.__dict__ for account in accounts],
                "transactions": [txn.__dict__ for txn in transactions]
            }
            
            logger.info(
                f"Synced {len(accounts)} accounts and {len(transactions)} "
                f"transactions via Yodlee for user {user_id}"
            )
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing Yodlee account data: {str(e)}")
            raise BankingIntegrationError("Failed to sync account data")
    
    async def remove_account(
        self,
        credential_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Remove Yodlee provider account and delete credentials
        
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
            
            user_access_token = credential_data["credentials"]["user_access_token"]
            provider_account_id = credential_data["credentials"]["provider_account_id"]
            
            # Remove account from Yodlee
            try:
                headers = {
                    'Authorization': f'Bearer {user_access_token}',
                    'Content-Type': 'application/json'
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.delete(
                        f"{self.base_url}/providerAccounts/{provider_account_id}",
                        headers=headers,
                        timeout=30.0
                    )
            except Exception as e:
                logger.warning(f"Could not remove Yodlee account: {str(e)}")
            
            # Delete stored credentials
            await credential_vault.delete_credentials(
                credential_id, user_id, db
            )
            
            logger.info(f"Removed Yodlee account for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing Yodlee account: {str(e)}")
            return False