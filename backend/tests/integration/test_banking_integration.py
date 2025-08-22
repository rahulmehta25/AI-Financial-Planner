"""
Banking Integration with Transaction Sync Tests

This module tests comprehensive banking integration functionality:
- Account connection and authentication
- Real-time transaction synchronization
- Account balance monitoring
- Transaction categorization and analysis
- Banking data security and encryption
- Multi-bank aggregation
- Webhook handling for bank updates
- Error handling and retry mechanisms
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.base import FullStackIntegrationTest, integration_test_context
from tests.factories import UserFactory, create_complete_user_scenario
from app.models.user import User


class TestBankingIntegrationComplete(FullStackIntegrationTest):
    """Test complete banking integration with multiple providers."""
    
    def __init__(self):
        super().__init__()
        self.mock_plaid_client = None
        self.mock_yodlee_client = None
        self.transaction_sync_tracking = []
        self.webhook_events = []
    
    async def setup_test_environment(self) -> Dict[str, Any]:
        """Set up banking integration testing environment."""
        config = await super().setup_test_environment()
        
        # Set up banking service mocks
        await self._setup_banking_mocks()
        
        config.update({
            'banking_testing': True,
            'mock_banking_providers': True,
            'webhook_testing_url': 'http://test/webhooks/banking'
        })
        
        return config
    
    async def _setup_banking_mocks(self):
        """Set up mocks for banking service providers."""
        # Plaid client mock
        self.mock_plaid_client = AsyncMock()
        self.mock_plaid_client.link_token_create.return_value = {
            'link_token': 'link-development-token-123',
            'expiration': (datetime.now() + timedelta(hours=4)).isoformat()
        }
        
        self.mock_plaid_client.item_public_token_exchange.return_value = {
            'access_token': 'access-development-token-456',
            'item_id': 'item-development-id-789'
        }
        
        self.mock_plaid_client.accounts_get.return_value = {
            'accounts': [
                {
                    'account_id': 'checking_account_123',
                    'name': 'Test Checking Account',
                    'type': 'depository',
                    'subtype': 'checking',
                    'balances': {
                        'available': 5432.10,
                        'current': 5432.10,
                        'limit': None,
                        'iso_currency_code': 'USD'
                    },
                    'mask': '0000'
                },
                {
                    'account_id': 'savings_account_456',
                    'name': 'Test Savings Account',
                    'type': 'depository',
                    'subtype': 'savings',
                    'balances': {
                        'available': 12345.67,
                        'current': 12345.67,
                        'limit': None,
                        'iso_currency_code': 'USD'
                    },
                    'mask': '1111'
                }
            ],
            'item': {
                'item_id': 'item-development-id-789',
                'institution_id': 'ins_109508',
                'webhook': 'http://test/webhooks/banking/plaid'
            }
        }
        
        self.mock_plaid_client.transactions_get.return_value = {
            'transactions': [
                {
                    'transaction_id': 'txn_001',
                    'account_id': 'checking_account_123',
                    'amount': 25.99,
                    'date': (datetime.now() - timedelta(days=1)).date(),
                    'name': 'Starbucks Coffee',
                    'merchant_name': 'Starbucks',
                    'category': ['Food and Drink', 'Coffee Shop'],
                    'category_id': '13005043',
                    'transaction_type': 'place',
                    'pending': False,
                    'iso_currency_code': 'USD'
                },
                {
                    'transaction_id': 'txn_002',
                    'account_id': 'checking_account_123',
                    'amount': -2500.00,  # Negative = income/deposit
                    'date': (datetime.now() - timedelta(days=2)).date(),
                    'name': 'Salary Deposit',
                    'category': ['Deposit', 'Payroll'],
                    'transaction_type': 'special',
                    'pending': False,
                    'iso_currency_code': 'USD'
                }
            ],
            'total_transactions': 2
        }
        
        # Yodlee client mock
        self.mock_yodlee_client = AsyncMock()
        self.mock_yodlee_client.get_accounts.return_value = {
            'account': [
                {
                    'id': 'yodlee_account_123',
                    'accountName': 'Yodlee Test Account',
                    'accountType': 'CHECKING',
                    'balance': {
                        'amount': 3456.78,
                        'currency': 'USD'
                    },
                    'providerId': 'yodlee_provider_456'
                }
            ]
        }
    
    async def test_complete_banking_connection_flow(self):
        """Test complete banking connection flow from link creation to data sync."""
        async with integration_test_context(self) as config:
            
            # Create test user
            user_data = await self._create_test_user()
            
            # Step 1: Initialize Plaid Link
            await self.measure_operation(
                lambda: self._test_plaid_link_initialization(user_data),
                "plaid_link_initialization"
            )
            
            # Step 2: Exchange public token
            await self.measure_operation(
                lambda: self._test_public_token_exchange(user_data),
                "public_token_exchange"
            )
            
            # Step 3: Fetch and store accounts
            await self.measure_operation(
                lambda: self._test_account_fetching_and_storage(user_data),
                "account_fetching_storage"
            )
            
            # Step 4: Initial transaction sync
            await self.measure_operation(
                lambda: self._test_initial_transaction_sync(user_data),
                "initial_transaction_sync"
            )
            
            # Step 5: Transaction categorization
            await self.measure_operation(
                lambda: self._test_transaction_categorization(user_data),
                "transaction_categorization"
            )
            
            # Step 6: Balance monitoring setup
            await self.measure_operation(
                lambda: self._test_balance_monitoring_setup(user_data),
                "balance_monitoring_setup"
            )
            
            # Verify complete integration
            await self._verify_complete_banking_integration(user_data)
    
    async def test_multi_bank_aggregation(self):
        """Test aggregation of accounts from multiple banking providers."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            
            # Connect to Plaid
            await self._connect_plaid_account(user_data)
            
            # Connect to Yodlee
            await self._connect_yodlee_account(user_data)
            
            # Test aggregated account view
            await self.measure_operation(
                lambda: self._test_aggregated_account_view(user_data),
                "aggregated_account_view"
            )
            
            # Test consolidated transaction history
            await self.measure_operation(
                lambda: self._test_consolidated_transaction_history(user_data),
                "consolidated_transaction_history"
            )
            
            # Test net worth calculation
            await self.measure_operation(
                lambda: self._test_net_worth_calculation(user_data),
                "net_worth_calculation"
            )
    
    async def test_real_time_transaction_sync(self):
        """Test real-time transaction synchronization via webhooks."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            await self._connect_plaid_account(user_data)
            
            # Test webhook reception and processing
            await self.measure_operation(
                lambda: self._test_webhook_transaction_update(user_data),
                "webhook_transaction_update"
            )
            
            # Test real-time balance updates
            await self.measure_operation(
                lambda: self._test_real_time_balance_update(user_data),
                "real_time_balance_update"
            )
            
            # Test notification triggers
            await self.measure_operation(
                lambda: self._test_transaction_notification_triggers(user_data),
                "transaction_notification_triggers"
            )
    
    async def test_transaction_categorization_and_analysis(self):
        """Test transaction categorization and spending analysis."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            await self._connect_plaid_account(user_data)
            
            # Generate diverse transaction data
            await self._generate_test_transactions(user_data)
            
            # Test automatic categorization
            await self.measure_operation(
                lambda: self._test_automatic_categorization(user_data),
                "automatic_categorization"
            )
            
            # Test spending pattern analysis
            await self.measure_operation(
                lambda: self._test_spending_pattern_analysis(user_data),
                "spending_pattern_analysis"
            )
            
            # Test budget tracking
            await self.measure_operation(
                lambda: self._test_budget_tracking_integration(user_data),
                "budget_tracking_integration"
            )
            
            # Test cash flow analysis
            await self.measure_operation(
                lambda: self._test_cash_flow_analysis(user_data),
                "cash_flow_analysis"
            )
    
    async def test_banking_security_and_encryption(self):
        """Test banking data security and encryption measures."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            
            # Test access token encryption
            await self.measure_operation(
                lambda: self._test_access_token_encryption(user_data),
                "access_token_encryption"
            )
            
            # Test data encryption at rest
            await self.measure_operation(
                lambda: self._test_data_encryption_at_rest(user_data),
                "data_encryption_at_rest"
            )
            
            # Test API security headers
            await self.measure_operation(
                lambda: self._test_banking_api_security(user_data),
                "banking_api_security"
            )
            
            # Test credential vault integration
            await self.measure_operation(
                lambda: self._test_credential_vault_integration(user_data),
                "credential_vault_integration"
            )
    
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            
            # Test API failure handling
            await self.measure_operation(
                lambda: self._test_api_failure_handling(user_data),
                "api_failure_handling"
            )
            
            # Test connection timeout handling
            await self.measure_operation(
                lambda: self._test_connection_timeout_handling(user_data),
                "connection_timeout_handling"
            )
            
            # Test account reauth flow
            await self.measure_operation(
                lambda: self._test_account_reauth_flow(user_data),
                "account_reauth_flow"
            )
            
            # Test data sync recovery
            await self.measure_operation(
                lambda: self._test_data_sync_recovery(user_data),
                "data_sync_recovery"
            )
    
    async def test_compliance_and_audit_logging(self):
        """Test compliance features and audit logging for banking data."""
        async with integration_test_context(self) as config:
            
            user_data = await self._create_test_user()
            await self._connect_plaid_account(user_data)
            
            # Test data access logging
            await self.measure_operation(
                lambda: self._test_data_access_logging(user_data),
                "data_access_logging"
            )
            
            # Test PCI compliance measures
            await self.measure_operation(
                lambda: self._test_pci_compliance_measures(user_data),
                "pci_compliance_measures"
            )
            
            # Test data retention policies
            await self.measure_operation(
                lambda: self._test_data_retention_policies(user_data),
                "data_retention_policies"
            )
            
            # Test consent management
            await self.measure_operation(
                lambda: self._test_banking_consent_management(user_data),
                "banking_consent_management"
            )
    
    # Helper methods for banking integration testing
    
    async def _create_test_user(self) -> Dict[str, Any]:
        """Create test user for banking integration."""
        user_data = {
            "email": "banking@example.com",
            "password": "BankingTest123!",
            "first_name": "Banking",
            "last_name": "Tester"
        }
        
        response = await self.client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Authenticate
        login_data = {"username": user_data["email"], "password": user_data["password"]}
        response = await self.client.post("/api/v1/auth/login", data=login_data)
        token_data = response.json()
        
        user_data['id'] = response.json()['id']
        user_data['auth_token'] = token_data["access_token"]
        
        return user_data
    
    async def _test_plaid_link_initialization(self, user_data: Dict[str, Any]):
        """Test Plaid Link token creation."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.banking.plaid_service.PlaidService.create_link_token') as mock_create:
            mock_create.return_value = self.mock_plaid_client.link_token_create.return_value
            
            response = await self.client.post(
                "/api/v1/banking/plaid/link-token",
                headers=headers
            )
            assert response.status_code == 200
            
            link_data = response.json()
            assert 'link_token' in link_data
            assert 'expiration' in link_data
            
            # Store for later use
            user_data['link_token'] = link_data['link_token']
            
            return link_data
    
    async def _test_public_token_exchange(self, user_data: Dict[str, Any]):
        """Test exchanging public token for access token."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.banking.plaid_service.PlaidService.exchange_public_token') as mock_exchange:
            mock_exchange.return_value = self.mock_plaid_client.item_public_token_exchange.return_value
            
            exchange_data = {
                'public_token': 'public-development-token-123',
                'institution_id': 'ins_109508',
                'accounts': ['checking_account_123', 'savings_account_456']
            }
            
            response = await self.client.post(
                "/api/v1/banking/plaid/exchange-token",
                json=exchange_data,
                headers=headers
            )
            assert response.status_code == 201
            
            result = response.json()
            assert 'access_token' in result
            assert 'item_id' in result
            assert result['status'] == 'connected'
            
            user_data['access_token'] = result['access_token']
            user_data['item_id'] = result['item_id']
            
            return result
    
    async def _test_account_fetching_and_storage(self, user_data: Dict[str, Any]):
        """Test fetching and storing account information."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.banking.plaid_service.PlaidService.get_accounts') as mock_get_accounts:
            mock_get_accounts.return_value = self.mock_plaid_client.accounts_get.return_value
            
            response = await self.client.post(
                f"/api/v1/banking/accounts/sync",
                headers=headers
            )
            assert response.status_code == 200
            
            sync_result = response.json()
            assert sync_result['accounts_synced'] > 0
            
            # Verify accounts were stored
            response = await self.client.get(
                "/api/v1/banking/accounts/",
                headers=headers
            )
            assert response.status_code == 200
            
            accounts = response.json()
            assert len(accounts) >= 2  # Should have checking and savings
            
            checking_account = next((acc for acc in accounts if acc['subtype'] == 'checking'), None)
            assert checking_account is not None
            assert checking_account['balance'] > 0
            
            user_data['accounts'] = accounts
            
            return accounts
    
    async def _test_initial_transaction_sync(self, user_data: Dict[str, Any]):
        """Test initial transaction synchronization."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.banking.plaid_service.PlaidService.get_transactions') as mock_get_transactions:
            mock_get_transactions.return_value = self.mock_plaid_client.transactions_get.return_value
            
            # Trigger initial transaction sync
            sync_data = {
                'start_date': (datetime.now() - timedelta(days=30)).date().isoformat(),
                'end_date': datetime.now().date().isoformat()
            }
            
            response = await self.client.post(
                "/api/v1/banking/transactions/sync",
                json=sync_data,
                headers=headers
            )
            assert response.status_code == 200
            
            sync_result = response.json()
            assert sync_result['transactions_synced'] > 0
            
            # Verify transactions were stored
            response = await self.client.get(
                "/api/v1/banking/transactions/",
                headers=headers
            )
            assert response.status_code == 200
            
            transactions = response.json()
            assert len(transactions) >= 2
            
            # Verify transaction details
            coffee_transaction = next((txn for txn in transactions if 'Starbucks' in txn['name']), None)
            assert coffee_transaction is not None
            assert coffee_transaction['amount'] > 0  # Expense
            assert 'Food and Drink' in coffee_transaction['category']
            
            self.transaction_sync_tracking.append({
                'user_id': user_data['id'],
                'transactions_count': len(transactions),
                'sync_timestamp': time.time()
            })
            
            return transactions
    
    async def _test_transaction_categorization(self, user_data: Dict[str, Any]):
        """Test automatic transaction categorization."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Get transactions
        response = await self.client.get(
            "/api/v1/banking/transactions/",
            headers=headers
        )
        transactions = response.json()
        
        # Test categorization endpoint
        response = await self.client.post(
            "/api/v1/banking/transactions/categorize",
            headers=headers
        )
        assert response.status_code == 200
        
        categorization_result = response.json()
        assert 'categorized_count' in categorization_result
        
        # Test category analysis
        response = await self.client.get(
            "/api/v1/banking/spending/categories",
            headers=headers
        )
        assert response.status_code == 200
        
        category_analysis = response.json()
        assert 'categories' in category_analysis
        assert len(category_analysis['categories']) > 0
        
        # Should have food and drink category
        food_category = next((cat for cat in category_analysis['categories'] if 'Food' in cat['name']), None)
        assert food_category is not None
        assert food_category['amount'] > 0
        
        return category_analysis
    
    async def _test_balance_monitoring_setup(self, user_data: Dict[str, Any]):
        """Test balance monitoring and alerts setup."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Set up balance monitoring
        monitoring_config = {
            'low_balance_threshold': 500.0,
            'high_spending_threshold': 1000.0,
            'unusual_activity_detection': True,
            'notification_preferences': {
                'email': True,
                'push': True,
                'sms': False
            }
        }
        
        response = await self.client.post(
            "/api/v1/banking/monitoring/configure",
            json=monitoring_config,
            headers=headers
        )
        assert response.status_code == 200
        
        # Test balance check
        response = await self.client.get(
            "/api/v1/banking/balance/current",
            headers=headers
        )
        assert response.status_code == 200
        
        balance_data = response.json()
        assert 'total_balance' in balance_data
        assert 'accounts' in balance_data
        assert balance_data['total_balance'] > 0
        
        return balance_data
    
    async def _connect_plaid_account(self, user_data: Dict[str, Any]):
        """Helper to connect Plaid account."""
        await self._test_plaid_link_initialization(user_data)
        await self._test_public_token_exchange(user_data)
        await self._test_account_fetching_and_storage(user_data)
    
    async def _connect_yodlee_account(self, user_data: Dict[str, Any]):
        """Helper to connect Yodlee account."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.banking.yodlee_service.YodleeService.get_accounts') as mock_get_accounts:
            mock_get_accounts.return_value = self.mock_yodlee_client.get_accounts.return_value
            
            yodlee_connection_data = {
                'provider_id': 'yodlee_provider_456',
                'login_form': {
                    'username': 'test_username',
                    'password': 'test_password'
                }
            }
            
            response = await self.client.post(
                "/api/v1/banking/yodlee/connect",
                json=yodlee_connection_data,
                headers=headers
            )
            assert response.status_code == 201
    
    async def _test_aggregated_account_view(self, user_data: Dict[str, Any]):
        """Test aggregated view of accounts from multiple providers."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/accounts/aggregated",
            headers=headers
        )
        assert response.status_code == 200
        
        aggregated_data = response.json()
        assert 'total_balance' in aggregated_data
        assert 'accounts_by_provider' in aggregated_data
        assert 'account_types_summary' in aggregated_data
        
        # Should have accounts from both providers
        providers = list(aggregated_data['accounts_by_provider'].keys())
        assert 'plaid' in providers or 'yodlee' in providers
        
        return aggregated_data
    
    async def _test_consolidated_transaction_history(self, user_data: Dict[str, Any]):
        """Test consolidated transaction history across providers."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/transactions/consolidated",
            headers=headers
        )
        assert response.status_code == 200
        
        consolidated_data = response.json()
        assert 'transactions' in consolidated_data
        assert 'total_count' in consolidated_data
        assert 'providers' in consolidated_data
        
        # Transactions should include provider source
        if consolidated_data['transactions']:
            transaction = consolidated_data['transactions'][0]
            assert 'provider' in transaction
            assert 'account_id' in transaction
        
        return consolidated_data
    
    async def _test_net_worth_calculation(self, user_data: Dict[str, Any]):
        """Test net worth calculation across all accounts."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/net-worth",
            headers=headers
        )
        assert response.status_code == 200
        
        net_worth_data = response.json()
        assert 'net_worth' in net_worth_data
        assert 'assets' in net_worth_data
        assert 'liabilities' in net_worth_data
        assert 'breakdown_by_account' in net_worth_data
        
        # Net worth should be positive for test data
        assert net_worth_data['net_worth'] > 0
        
        return net_worth_data
    
    async def _test_webhook_transaction_update(self, user_data: Dict[str, Any]):
        """Test webhook-based transaction updates."""
        # Simulate webhook from Plaid
        webhook_data = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'DEFAULT_UPDATE',
            'item_id': user_data.get('item_id', 'item-development-id-789'),
            'new_transactions': 5,
            'environment': 'development'
        }
        
        # Process webhook
        response = await self.client.post(
            "/api/v1/banking/webhooks/plaid",
            json=webhook_data
        )
        assert response.status_code == 200
        
        # Verify webhook was processed
        self.webhook_events.append({
            'type': 'transaction_update',
            'provider': 'plaid',
            'timestamp': time.time(),
            'data': webhook_data
        })
        
        # Check that transactions were updated
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        response = await self.client.get(
            "/api/v1/banking/transactions/recent",
            headers=headers
        )
        assert response.status_code == 200
        
        return True
    
    async def _test_real_time_balance_update(self, user_data: Dict[str, Any]):
        """Test real-time balance updates."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Get initial balance
        response = await self.client.get(
            "/api/v1/banking/balance/current",
            headers=headers
        )
        initial_balance = response.json()
        
        # Simulate balance update webhook
        balance_webhook = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'DEFAULT_UPDATE',
            'item_id': user_data.get('item_id'),
            'account_id': 'checking_account_123',
            'new_balance': initial_balance['total_balance'] + 100.0
        }
        
        response = await self.client.post(
            "/api/v1/banking/webhooks/balance-update",
            json=balance_webhook
        )
        assert response.status_code == 200
        
        # Verify balance was updated
        response = await self.client.get(
            "/api/v1/banking/balance/current",
            headers=headers
        )
        updated_balance = response.json()
        
        # Balance should have changed
        assert updated_balance['total_balance'] != initial_balance['total_balance']
        
        return updated_balance
    
    async def _test_transaction_notification_triggers(self, user_data: Dict[str, Any]):
        """Test transaction-based notification triggers."""
        # Simulate large transaction that should trigger notification
        large_transaction_webhook = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'DEFAULT_UPDATE',
            'item_id': user_data.get('item_id'),
            'transactions': [
                {
                    'transaction_id': 'large_txn_001',
                    'account_id': 'checking_account_123',
                    'amount': 1500.00,  # Large amount should trigger alert
                    'name': 'Large Purchase',
                    'category': ['Shopping', 'General Merchandise']
                }
            ]
        }
        
        response = await self.client.post(
            "/api/v1/banking/webhooks/plaid",
            json=large_transaction_webhook
        )
        assert response.status_code == 200
        
        # Check if notification was triggered
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        response = await self.client.get(
            "/api/v1/notifications/recent",
            headers=headers
        )
        assert response.status_code == 200
        
        notifications = response.json()
        large_purchase_notifications = [n for n in notifications if 'large' in n.get('content', '').lower()]
        
        # Should have triggered a large purchase notification
        assert len(large_purchase_notifications) > 0
        
        return True
    
    async def _generate_test_transactions(self, user_data: Dict[str, Any]):
        """Generate diverse test transactions for analysis."""
        # This would typically be done by syncing with bank APIs
        # For testing, we'll create mock transactions
        
        test_transactions = [
            {
                'name': 'Grocery Store',
                'amount': 85.43,
                'category': ['Food and Drink', 'Groceries'],
                'date': (datetime.now() - timedelta(days=1)).date().isoformat()
            },
            {
                'name': 'Gas Station',
                'amount': 45.67,
                'category': ['Transportation', 'Gas Stations'],
                'date': (datetime.now() - timedelta(days=2)).date().isoformat()
            },
            {
                'name': 'Netflix',
                'amount': 15.99,
                'category': ['Recreation', 'Entertainment'],
                'date': (datetime.now() - timedelta(days=3)).date().isoformat()
            }
        ]
        
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        for transaction in test_transactions:
            response = await self.client.post(
                "/api/v1/banking/transactions/manual",
                json=transaction,
                headers=headers
            )
            assert response.status_code == 201
    
    async def _test_automatic_categorization(self, user_data: Dict[str, Any]):
        """Test automatic transaction categorization."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Trigger categorization
        response = await self.client.post(
            "/api/v1/banking/transactions/auto-categorize",
            headers=headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert 'categorized_count' in result
        assert result['categorized_count'] > 0
        
        # Verify categories were assigned correctly
        response = await self.client.get(
            "/api/v1/banking/transactions/",
            headers=headers
        )
        transactions = response.json()
        
        categorized_transactions = [t for t in transactions if t.get('category')]
        assert len(categorized_transactions) > 0
        
        return result
    
    async def _test_spending_pattern_analysis(self, user_data: Dict[str, Any]):
        """Test spending pattern analysis."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/analysis/spending-patterns",
            headers=headers
        )
        assert response.status_code == 200
        
        analysis = response.json()
        assert 'monthly_spending' in analysis
        assert 'category_breakdown' in analysis
        assert 'trends' in analysis
        
        # Should identify spending trends
        if analysis['trends']:
            assert 'direction' in analysis['trends']
            assert 'categories' in analysis['trends']
        
        return analysis
    
    async def _test_budget_tracking_integration(self, user_data: Dict[str, Any]):
        """Test integration with budget tracking."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Create a budget
        budget_data = {
            'name': 'Monthly Budget',
            'period': 'monthly',
            'categories': {
                'Food and Drink': 400.0,
                'Transportation': 200.0,
                'Entertainment': 100.0
            }
        }
        
        response = await self.client.post(
            "/api/v1/banking/budgets/",
            json=budget_data,
            headers=headers
        )
        assert response.status_code == 201
        
        budget = response.json()
        
        # Check budget vs. actual spending
        response = await self.client.get(
            f"/api/v1/banking/budgets/{budget['id']}/progress",
            headers=headers
        )
        assert response.status_code == 200
        
        progress = response.json()
        assert 'budget_id' in progress
        assert 'categories' in progress
        assert 'overall_progress' in progress
        
        return progress
    
    async def _test_cash_flow_analysis(self, user_data: Dict[str, Any]):
        """Test cash flow analysis."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/analysis/cash-flow",
            headers=headers
        )
        assert response.status_code == 200
        
        cash_flow = response.json()
        assert 'income' in cash_flow
        assert 'expenses' in cash_flow
        assert 'net_cash_flow' in cash_flow
        assert 'monthly_trends' in cash_flow
        
        # Should have positive cash flow for test data
        assert cash_flow['net_cash_flow'] != 0
        
        return cash_flow
    
    async def _test_access_token_encryption(self, user_data: Dict[str, Any]):
        """Test that access tokens are properly encrypted."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Connect account first
        await self._connect_plaid_account(user_data)
        
        # Check that tokens are encrypted in storage
        response = await self.client.get(
            "/api/v1/banking/connections/security-info",
            headers=headers
        )
        assert response.status_code == 200
        
        security_info = response.json()
        assert 'encryption_status' in security_info
        assert security_info['encryption_status'] == 'encrypted'
        assert 'access_tokens_encrypted' in security_info
        assert security_info['access_tokens_encrypted'] == True
        
        return security_info
    
    async def _test_data_encryption_at_rest(self, user_data: Dict[str, Any]):
        """Test data encryption at rest."""
        # This would typically involve checking database encryption
        # For testing, we'll verify that sensitive data fields are encrypted
        
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/encryption/status",
            headers=headers
        )
        assert response.status_code == 200
        
        encryption_status = response.json()
        assert 'database_encryption' in encryption_status
        assert 'field_level_encryption' in encryption_status
        assert encryption_status['database_encryption'] == 'enabled'
        
        return encryption_status
    
    async def _test_banking_api_security(self, user_data: Dict[str, Any]):
        """Test banking API security measures."""
        # Test without authentication
        response = await self.client.get("/api/v1/banking/accounts/")
        assert response.status_code == 401
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await self.client.get(
            "/api/v1/banking/accounts/",
            headers=invalid_headers
        )
        assert response.status_code == 401
        
        # Test rate limiting
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        rate_limit_hit = False
        for i in range(100):  # Try many requests rapidly
            response = await self.client.get(
                "/api/v1/banking/balance/current",
                headers=headers
            )
            if response.status_code == 429:  # Too Many Requests
                rate_limit_hit = True
                break
        
        assert rate_limit_hit, "Banking API rate limiting not working"
        
        return True
    
    async def _test_credential_vault_integration(self, user_data: Dict[str, Any]):
        """Test credential vault integration."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Test storing credentials in vault
        vault_data = {
            'provider': 'test_bank',
            'credentials': {
                'username': 'test_user',
                'password': 'test_password'
            },
            'encryption_key_id': 'vault_key_123'
        }
        
        response = await self.client.post(
            "/api/v1/banking/vault/store",
            json=vault_data,
            headers=headers
        )
        assert response.status_code == 201
        
        vault_result = response.json()
        assert 'credential_id' in vault_result
        assert 'encrypted' in vault_result
        assert vault_result['encrypted'] == True
        
        # Test retrieving credentials
        credential_id = vault_result['credential_id']
        response = await self.client.get(
            f"/api/v1/banking/vault/{credential_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        retrieved_creds = response.json()
        assert 'provider' in retrieved_creds
        assert 'credentials' not in retrieved_creds  # Should not return raw credentials
        
        return vault_result
    
    async def _test_api_failure_handling(self, user_data: Dict[str, Any]):
        """Test API failure handling."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.banking.plaid_service.PlaidService.get_accounts') as mock_get_accounts:
            # Simulate API failure
            mock_get_accounts.side_effect = Exception("Plaid API temporarily unavailable")
            
            response = await self.client.post(
                "/api/v1/banking/accounts/sync",
                headers=headers
            )
            
            # Should handle gracefully
            assert response.status_code in [503, 502]  # Service unavailable or bad gateway
            
            error_response = response.json()
            assert 'error' in error_response
            assert 'retry_after' in error_response
        
        return True
    
    async def _test_connection_timeout_handling(self, user_data: Dict[str, Any]):
        """Test connection timeout handling."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.banking.plaid_service.PlaidService.get_transactions') as mock_get_transactions:
            # Simulate timeout
            mock_get_transactions.side_effect = asyncio.TimeoutError("Request timed out")
            
            response = await self.client.post(
                "/api/v1/banking/transactions/sync",
                headers=headers
            )
            
            # Should handle timeout gracefully
            assert response.status_code == 408  # Request Timeout
            
            timeout_response = response.json()
            assert 'error' in timeout_response
            assert 'timeout' in timeout_response['error'].lower()
        
        return True
    
    async def _test_account_reauth_flow(self, user_data: Dict[str, Any]):
        """Test account re-authentication flow."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Simulate account that needs re-authentication
        reauth_data = {
            'item_id': user_data.get('item_id', 'item-development-id-789'),
            'error_code': 'ITEM_LOGIN_REQUIRED'
        }
        
        response = await self.client.post(
            "/api/v1/banking/reauth/initiate",
            json=reauth_data,
            headers=headers
        )
        assert response.status_code == 200
        
        reauth_result = response.json()
        assert 'link_token' in reauth_result
        assert 'reauth_required' in reauth_result
        assert reauth_result['reauth_required'] == True
        
        return reauth_result
    
    async def _test_data_sync_recovery(self, user_data: Dict[str, Any]):
        """Test data synchronization recovery."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Test recovery from failed sync
        response = await self.client.post(
            "/api/v1/banking/sync/recover",
            headers=headers
        )
        assert response.status_code == 200
        
        recovery_result = response.json()
        assert 'recovery_status' in recovery_result
        assert 'actions_taken' in recovery_result
        
        return recovery_result
    
    async def _test_data_access_logging(self, user_data: Dict[str, Any]):
        """Test data access audit logging."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Access banking data (should be logged)
        response = await self.client.get(
            "/api/v1/banking/accounts/",
            headers=headers
        )
        assert response.status_code == 200
        
        # Check audit logs
        response = await self.client.get(
            "/api/v1/banking/audit/access-logs",
            headers=headers
        )
        assert response.status_code == 200
        
        audit_logs = response.json()
        assert 'logs' in audit_logs
        assert len(audit_logs['logs']) > 0
        
        # Should have logged the account access
        account_access_logs = [log for log in audit_logs['logs'] if 'accounts' in log['endpoint']]
        assert len(account_access_logs) > 0
        
        return audit_logs
    
    async def _test_pci_compliance_measures(self, user_data: Dict[str, Any]):
        """Test PCI compliance measures."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/compliance/pci-status",
            headers=headers
        )
        assert response.status_code == 200
        
        pci_status = response.json()
        assert 'compliance_level' in pci_status
        assert 'security_measures' in pci_status
        assert 'last_assessment' in pci_status
        
        # Should be PCI compliant
        assert pci_status['compliance_level'] in ['Level 1', 'Level 2', 'Level 3', 'Level 4']
        
        return pci_status
    
    async def _test_data_retention_policies(self, user_data: Dict[str, Any]):
        """Test data retention policies."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        response = await self.client.get(
            "/api/v1/banking/compliance/retention-policy",
            headers=headers
        )
        assert response.status_code == 200
        
        retention_policy = response.json()
        assert 'transaction_retention_days' in retention_policy
        assert 'account_data_retention_days' in retention_policy
        assert 'audit_log_retention_days' in retention_policy
        
        # Should have reasonable retention periods
        assert retention_policy['transaction_retention_days'] >= 2555  # 7 years minimum
        assert retention_policy['audit_log_retention_days'] >= 2555
        
        return retention_policy
    
    async def _test_banking_consent_management(self, user_data: Dict[str, Any]):
        """Test banking data consent management."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Get current consent status
        response = await self.client.get(
            "/api/v1/banking/consent/status",
            headers=headers
        )
        assert response.status_code == 200
        
        consent_status = response.json()
        assert 'consents' in consent_status
        assert 'permissions' in consent_status
        
        # Test consent withdrawal
        consent_data = {
            'consent_type': 'transaction_access',
            'action': 'withdraw'
        }
        
        response = await self.client.post(
            "/api/v1/banking/consent/manage",
            json=consent_data,
            headers=headers
        )
        assert response.status_code == 200
        
        # Test that access is restricted after consent withdrawal
        response = await self.client.get(
            "/api/v1/banking/transactions/",
            headers=headers
        )
        assert response.status_code == 403  # Forbidden due to withdrawn consent
        
        return True
    
    async def _verify_complete_banking_integration(self, user_data: Dict[str, Any]):
        """Verify complete banking integration was successful."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Verify accounts are connected
        response = await self.client.get(
            "/api/v1/banking/accounts/",
            headers=headers
        )
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) > 0
        
        # Verify transactions are synced
        response = await self.client.get(
            "/api/v1/banking/transactions/",
            headers=headers
        )
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) > 0
        
        # Verify categorization is working
        categorized_transactions = [t for t in transactions if t.get('category')]
        assert len(categorized_transactions) > 0
        
        # Verify balance monitoring is active
        response = await self.client.get(
            "/api/v1/banking/monitoring/status",
            headers=headers
        )
        assert response.status_code == 200
        monitoring_status = response.json()
        assert monitoring_status['active'] == True
        
        # Verify security measures are in place
        response = await self.client.get(
            "/api/v1/banking/security/status",
            headers=headers
        )
        assert response.status_code == 200
        security_status = response.json()
        assert security_status['encryption_enabled'] == True
        
        return True


@pytest.mark.asyncio
@pytest.mark.integration
class TestBankingIntegrationPerformance:
    """Test banking integration performance and scalability."""
    
    async def test_transaction_sync_performance(self):
        """Test transaction synchronization performance."""
        test = TestBankingIntegrationComplete()
        
        async with integration_test_context(test) as config:
            user_data = await test._create_test_user()
            await test._connect_plaid_account(user_data)
            
            # Test large transaction sync
            start_time = time.time()
            
            # Simulate syncing 1000 transactions
            large_sync_data = {
                'start_date': (datetime.now() - timedelta(days=365)).date().isoformat(),
                'end_date': datetime.now().date().isoformat(),
                'expected_count': 1000
            }
            
            headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
            response = await test.client.post(
                "/api/v1/banking/transactions/sync",
                json=large_sync_data,
                headers=headers
            )
            
            end_time = time.time()
            sync_duration = end_time - start_time
            
            assert response.status_code == 200
            assert sync_duration < 30  # Should complete within 30 seconds
            
            sync_result = response.json()
            transactions_per_second = sync_result.get('transactions_synced', 0) / sync_duration
            assert transactions_per_second > 10  # Should process at least 10 transactions/second
    
    async def test_concurrent_banking_operations(self):
        """Test concurrent banking operations."""
        test = TestBankingIntegrationComplete()
        
        async with integration_test_context(test) as config:
            
            # Create multiple users with banking connections
            users = []
            for i in range(10):
                user_data = await test._create_test_user()
                await test._connect_plaid_account(user_data)
                users.append(user_data)
            
            # Perform concurrent operations
            start_time = time.time()
            
            tasks = []
            for user in users:
                # Concurrent balance checks
                task = asyncio.create_task(
                    test._perform_banking_operations(user)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # All operations should succeed
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == len(users)
            
            # Should complete within reasonable time
            assert total_duration < 60  # All concurrent operations within 60 seconds
    
    async def _perform_banking_operations(self, user_data: Dict[str, Any]):
        """Perform various banking operations for performance testing."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        operations = [
            self.client.get("/api/v1/banking/accounts/", headers=headers),
            self.client.get("/api/v1/banking/balance/current", headers=headers),
            self.client.get("/api/v1/banking/transactions/recent", headers=headers),
            self.client.get("/api/v1/banking/spending/categories", headers=headers)
        ]
        
        results = await asyncio.gather(*operations)
        
        # All operations should succeed
        for result in results:
            assert result.status_code == 200
        
        return True