"""
Comprehensive unit tests for banking integration services.

This test suite covers:
- Plaid API integration
- Yodlee API integration
- Bank account aggregation
- Transaction processing
- Security and credential management
- Error handling and retries
- Webhook processing
- Data validation
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.banking.plaid_service import PlaidService
from app.services.banking.yodlee_service import YodleeService
from app.services.banking.bank_aggregator import BankAggregator
from app.services.banking.transaction_categorizer import TransactionCategorizer
from app.services.banking.spending_pattern_detector import SpendingPatternDetector
from app.services.banking.cash_flow_analyzer import CashFlowAnalyzer
from app.services.banking.balance_monitor import BalanceMonitor
from app.services.banking.credential_vault import CredentialVault
from app.services.banking.webhook_handler import WebhookHandler
from app.services.banking.error_handler import BankingErrorHandler
from app.database.banking_models import BankAccount, Transaction, TransactionCategory


class TestPlaidService:
    """Test suite for Plaid API integration."""
    
    @pytest.fixture
    def plaid_service(self):
        """Create Plaid service instance."""
        return PlaidService()
    
    @pytest.fixture
    def mock_plaid_client(self):
        """Mock Plaid client."""
        return Mock()
    
    @pytest.fixture
    def sample_plaid_accounts(self):
        """Sample Plaid accounts response."""
        return {
            'accounts': [
                {
                    'account_id': 'account_1',
                    'name': 'Checking Account',
                    'type': 'depository',
                    'subtype': 'checking',
                    'balances': {
                        'available': 1500.50,
                        'current': 1500.50,
                        'limit': None,
                        'iso_currency_code': 'USD'
                    }
                },
                {
                    'account_id': 'account_2',
                    'name': 'Savings Account',
                    'type': 'depository',
                    'subtype': 'savings',
                    'balances': {
                        'available': 5000.00,
                        'current': 5000.00,
                        'limit': None,
                        'iso_currency_code': 'USD'
                    }
                },
                {
                    'account_id': 'account_3',
                    'name': 'Credit Card',
                    'type': 'credit',
                    'subtype': 'credit_card',
                    'balances': {
                        'available': 2500.00,
                        'current': -750.00,
                        'limit': 3000.00,
                        'iso_currency_code': 'USD'
                    }
                }
            ],
            'request_id': 'request_123'
        }
    
    @pytest.fixture
    def sample_plaid_transactions(self):
        """Sample Plaid transactions response."""
        return {
            'transactions': [
                {
                    'transaction_id': 'txn_1',
                    'account_id': 'account_1',
                    'amount': 12.99,
                    'date': '2024-01-15',
                    'name': 'Netflix Subscription',
                    'category': ['Service', 'Subscription'],
                    'category_id': '12345',
                    'merchant_name': 'Netflix',
                    'pending': False
                },
                {
                    'transaction_id': 'txn_2',
                    'account_id': 'account_1',
                    'amount': -2500.00,
                    'date': '2024-01-01',
                    'name': 'Paycheck Deposit',
                    'category': ['Deposit'],
                    'category_id': '67890',
                    'merchant_name': None,
                    'pending': False
                },
                {
                    'transaction_id': 'txn_3',
                    'account_id': 'account_1',
                    'amount': 85.67,
                    'date': '2024-01-10',
                    'name': 'Grocery Store',
                    'category': ['Shops', 'Food and Drink', 'Groceries'],
                    'category_id': '11111',
                    'merchant_name': 'Safeway',
                    'pending': False
                }
            ],
            'total_transactions': 3,
            'request_id': 'request_456'
        }
    
    @pytest.mark.asyncio
    async def test_create_link_token(self, plaid_service, mock_plaid_client):
        """Test Plaid Link token creation."""
        
        mock_response = {
            'link_token': 'link-sandbox-12345',
            'expiration': '2024-01-01T12:00:00Z',
            'request_id': 'request_123'
        }
        
        mock_plaid_client.link_token_create.return_value = mock_response
        
        with patch.object(plaid_service, '_client', mock_plaid_client):
            token_response = await plaid_service.create_link_token(
                user_id='user_123',
                client_name='AI Financial Planner'
            )
        
        assert token_response['link_token'] == 'link-sandbox-12345'
        assert 'expiration' in token_response
        
        # Verify API call
        mock_plaid_client.link_token_create.assert_called_once()
        call_args = mock_plaid_client.link_token_create.call_args[0][0]
        assert call_args['user']['client_user_id'] == 'user_123'
        assert call_args['client_name'] == 'AI Financial Planner'
    
    @pytest.mark.asyncio
    async def test_exchange_public_token(self, plaid_service, mock_plaid_client):
        """Test public token exchange for access token."""
        
        mock_response = {
            'access_token': 'access-sandbox-12345',
            'item_id': 'item_123',
            'request_id': 'request_456'
        }
        
        mock_plaid_client.item_public_token_exchange.return_value = mock_response
        
        with patch.object(plaid_service, '_client', mock_plaid_client):
            token_response = await plaid_service.exchange_public_token('public-sandbox-token')
        
        assert token_response['access_token'] == 'access-sandbox-12345'
        assert token_response['item_id'] == 'item_123'
        
        # Verify API call
        mock_plaid_client.item_public_token_exchange.assert_called_once_with({
            'public_token': 'public-sandbox-token'
        })
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, plaid_service, mock_plaid_client, sample_plaid_accounts):
        """Test fetching bank accounts."""
        
        mock_plaid_client.accounts_get.return_value = sample_plaid_accounts
        
        with patch.object(plaid_service, '_client', mock_plaid_client):
            accounts = await plaid_service.get_accounts('access-token-123')
        
        assert len(accounts) == 3
        assert accounts[0]['account_id'] == 'account_1'
        assert accounts[0]['name'] == 'Checking Account'
        assert accounts[0]['type'] == 'depository'
        assert accounts[0]['subtype'] == 'checking'
        
        # Check balance parsing
        assert accounts[0]['balance']['available'] == 1500.50
        assert accounts[0]['balance']['current'] == 1500.50
        
        # Credit card should have negative current balance
        credit_card = next(acc for acc in accounts if acc['type'] == 'credit')
        assert credit_card['balance']['current'] == -750.00
        assert credit_card['balance']['limit'] == 3000.00
    
    @pytest.mark.asyncio
    async def test_get_transactions(self, plaid_service, mock_plaid_client, sample_plaid_transactions):
        """Test fetching transactions."""
        
        mock_plaid_client.transactions_get.return_value = sample_plaid_transactions
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        with patch.object(plaid_service, '_client', mock_plaid_client):
            transactions = await plaid_service.get_transactions(
                'access-token-123', start_date, end_date
            )
        
        assert len(transactions) == 3
        assert transactions[0]['transaction_id'] == 'txn_1'
        assert transactions[0]['amount'] == 12.99
        assert transactions[0]['name'] == 'Netflix Subscription'
        assert transactions[0]['category'] == ['Service', 'Subscription']
        
        # Check date parsing
        assert isinstance(transactions[0]['date'], datetime)
        
        # Verify API call with date range
        mock_plaid_client.transactions_get.assert_called_once()
        call_args = mock_plaid_client.transactions_get.call_args[0][0]
        assert call_args['access_token'] == 'access-token-123'
        assert 'start_date' in call_args
        assert 'end_date' in call_args
    
    @pytest.mark.asyncio
    async def test_get_account_balance(self, plaid_service, mock_plaid_client, sample_plaid_accounts):
        """Test getting specific account balance."""
        
        mock_plaid_client.accounts_get.return_value = sample_plaid_accounts
        
        with patch.object(plaid_service, '_client', mock_plaid_client):
            balance = await plaid_service.get_account_balance(
                'access-token-123', 'account_1'
            )
        
        assert balance['available'] == 1500.50
        assert balance['current'] == 1500.50
        assert balance['currency'] == 'USD'
    
    @pytest.mark.asyncio
    async def test_error_handling(self, plaid_service, mock_plaid_client):
        """Test error handling for Plaid API errors."""
        
        from plaid.errors import PlaidError
        
        # Test invalid access token
        mock_plaid_client.accounts_get.side_effect = PlaidError({
            'error_type': 'INVALID_INPUT',
            'error_code': 'INVALID_ACCESS_TOKEN',
            'display_message': 'The access token is invalid.'
        })
        
        with patch.object(plaid_service, '_client', mock_plaid_client):
            with pytest.raises(Exception) as exc_info:
                await plaid_service.get_accounts('invalid-token')
            
            assert 'invalid' in str(exc_info.value).lower()
        
        # Test rate limiting
        mock_plaid_client.accounts_get.side_effect = PlaidError({
            'error_type': 'RATE_LIMIT_EXCEEDED',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'display_message': 'Rate limit exceeded.'
        })
        
        with patch.object(plaid_service, '_client', mock_plaid_client):
            with pytest.raises(Exception) as exc_info:
                await plaid_service.get_accounts('access-token-123')
            
            assert 'rate limit' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_webhook_verification(self, plaid_service):
        """Test webhook signature verification."""
        
        webhook_body = json.dumps({
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'DEFAULT_UPDATE',
            'item_id': 'item_123'
        })
        
        # Test with valid signature
        with patch.object(plaid_service, '_verify_webhook_signature', return_value=True):
            is_valid = plaid_service.verify_webhook(webhook_body, 'test-signature')
            assert is_valid
        
        # Test with invalid signature
        with patch.object(plaid_service, '_verify_webhook_signature', return_value=False):
            is_valid = plaid_service.verify_webhook(webhook_body, 'invalid-signature')
            assert not is_valid


class TestYodleeService:
    """Test suite for Yodlee API integration."""
    
    @pytest.fixture
    def yodlee_service(self):
        """Create Yodlee service instance."""
        return YodleeService()
    
    @pytest.fixture
    def mock_yodlee_client(self):
        """Mock Yodlee client."""
        return Mock()
    
    @pytest.fixture
    def sample_yodlee_accounts(self):
        """Sample Yodlee accounts response."""
        return {
            'account': [
                {
                    'id': 123456,
                    'accountName': 'Primary Checking',
                    'accountType': 'CHECKING',
                    'accountStatus': 'ACTIVE',
                    'balance': {
                        'amount': 2500.75,
                        'currency': 'USD'
                    },
                    'providerId': 16441,
                    'providerName': 'Chase Bank'
                },
                {
                    'id': 123457,
                    'accountName': 'High Yield Savings',
                    'accountType': 'SAVINGS',
                    'accountStatus': 'ACTIVE',
                    'balance': {
                        'amount': 15000.00,
                        'currency': 'USD'
                    },
                    'providerId': 16441,
                    'providerName': 'Chase Bank'
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self, yodlee_service, mock_yodlee_client):
        """Test Yodlee user authentication."""
        
        mock_response = {
            'user': {
                'id': 10123456,
                'loginName': 'testuser123',
                'session': {
                    'userSession': 'session-token-12345'
                }
            }
        }
        
        mock_yodlee_client.authenticate.return_value = mock_response
        
        with patch.object(yodlee_service, '_client', mock_yodlee_client):
            auth_response = await yodlee_service.authenticate_user(
                'testuser123', 'password123'
            )
        
        assert auth_response['user_id'] == 10123456
        assert auth_response['session_token'] == 'session-token-12345'
    
    @pytest.mark.asyncio
    async def test_add_provider_account(self, yodlee_service, mock_yodlee_client):
        """Test adding a provider account."""
        
        mock_response = {
            'providerAccount': [
                {
                    'id': 789012,
                    'providerId': 16441,
                    'isManual': False,
                    'status': 'SUCCESS',
                    'dataset': [
                        {
                            'name': 'BASIC_AGG_DATA',
                            'additionalStatus': 'AVAILABLE_DATA_RETRIEVED'
                        }
                    ]
                }
            ]
        }
        
        mock_yodlee_client.add_provider_account.return_value = mock_response
        
        credentials = {
            'LOGIN': 'user123',
            'PASSWORD': 'pass123'
        }
        
        with patch.object(yodlee_service, '_client', mock_yodlee_client):
            provider_response = await yodlee_service.add_provider_account(
                provider_id=16441,
                credentials=credentials
            )
        
        assert provider_response['provider_account_id'] == 789012
        assert provider_response['status'] == 'SUCCESS'
        assert provider_response['provider_id'] == 16441
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, yodlee_service, mock_yodlee_client, sample_yodlee_accounts):
        """Test fetching accounts from Yodlee."""
        
        mock_yodlee_client.get_accounts.return_value = sample_yodlee_accounts
        
        with patch.object(yodlee_service, '_client', mock_yodlee_client):
            accounts = await yodlee_service.get_accounts()
        
        assert len(accounts) == 2
        assert accounts[0]['id'] == 123456
        assert accounts[0]['name'] == 'Primary Checking'
        assert accounts[0]['type'] == 'CHECKING'
        assert accounts[0]['balance']['amount'] == 2500.75
        assert accounts[0]['balance']['currency'] == 'USD'
    
    @pytest.mark.asyncio
    async def test_refresh_provider_account(self, yodlee_service, mock_yodlee_client):
        """Test refreshing provider account data."""
        
        mock_response = {
            'providerAccount': [
                {
                    'id': 789012,
                    'refreshInfo': {
                        'status': 'SUCCESS',
                        'statusCode': 0,
                        'statusMessage': 'OK',
                        'lastRefreshed': '2024-01-15T10:30:00Z'
                    }
                }
            ]
        }
        
        mock_yodlee_client.refresh_provider_account.return_value = mock_response
        
        with patch.object(yodlee_service, '_client', mock_yodlee_client):
            refresh_response = await yodlee_service.refresh_provider_account(789012)
        
        assert refresh_response['status'] == 'SUCCESS'
        assert 'last_refreshed' in refresh_response


class TestBankAggregator:
    """Test suite for bank account aggregation service."""
    
    @pytest.fixture
    def bank_aggregator(self):
        """Create bank aggregator instance."""
        return BankAggregator()
    
    @pytest.fixture
    def mock_plaid_service(self):
        """Mock Plaid service."""
        return Mock()
    
    @pytest.fixture
    def mock_yodlee_service(self):
        """Mock Yodlee service."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_aggregate_accounts_multiple_providers(self, bank_aggregator, 
                                                        mock_plaid_service, mock_yodlee_service):
        """Test aggregating accounts from multiple providers."""
        
        # Mock Plaid response
        plaid_accounts = [
            {
                'account_id': 'plaid_acc_1',
                'name': 'Chase Checking',
                'type': 'depository',
                'subtype': 'checking',
                'balance': {'current': 1500.00, 'available': 1500.00},
                'provider': 'plaid'
            }
        ]
        mock_plaid_service.get_accounts.return_value = plaid_accounts
        
        # Mock Yodlee response
        yodlee_accounts = [
            {
                'id': 'yodlee_acc_1',
                'name': 'Wells Fargo Savings',
                'type': 'SAVINGS',
                'balance': {'amount': 5000.00, 'currency': 'USD'},
                'provider': 'yodlee'
            }
        ]
        mock_yodlee_service.get_accounts.return_value = yodlee_accounts
        
        with patch.object(bank_aggregator, '_plaid_service', mock_plaid_service), \
             patch.object(bank_aggregator, '_yodlee_service', mock_yodlee_service):
            
            aggregated_accounts = await bank_aggregator.get_all_accounts('user_123')
        
        assert len(aggregated_accounts) == 2
        
        # Check Plaid account normalization
        plaid_account = next(acc for acc in aggregated_accounts if acc['provider'] == 'plaid')
        assert plaid_account['id'] == 'plaid_acc_1'
        assert plaid_account['normalized_type'] == 'checking'
        assert plaid_account['balance'] == 1500.00
        
        # Check Yodlee account normalization
        yodlee_account = next(acc for acc in aggregated_accounts if acc['provider'] == 'yodlee')
        assert yodlee_account['id'] == 'yodlee_acc_1'
        assert yodlee_account['normalized_type'] == 'savings'
        assert yodlee_account['balance'] == 5000.00
    
    @pytest.mark.asyncio
    async def test_account_deduplication(self, bank_aggregator, mock_plaid_service, mock_yodlee_service):
        """Test deduplication of accounts across providers."""
        
        # Mock identical accounts from different providers
        plaid_accounts = [
            {
                'account_id': 'plaid_acc_1',
                'name': 'Chase Checking ****1234',
                'type': 'depository',
                'subtype': 'checking',
                'balance': {'current': 1500.00},
                'provider': 'plaid'
            }
        ]
        
        yodlee_accounts = [
            {
                'id': 'yodlee_acc_1',
                'name': 'Chase Checking ending in 1234',
                'type': 'CHECKING',
                'balance': {'amount': 1500.00, 'currency': 'USD'},
                'provider': 'yodlee'
            }
        ]
        
        mock_plaid_service.get_accounts.return_value = plaid_accounts
        mock_yodlee_service.get_accounts.return_value = yodlee_accounts
        
        with patch.object(bank_aggregator, '_plaid_service', mock_plaid_service), \
             patch.object(bank_aggregator, '_yodlee_service', mock_yodlee_service):
            
            aggregated_accounts = await bank_aggregator.get_all_accounts(
                'user_123', deduplicate=True
            )
        
        # Should only return one account after deduplication
        assert len(aggregated_accounts) == 1
        
        # Should prefer the provider with more complete data
        remaining_account = aggregated_accounts[0]
        assert remaining_account['id'] in ['plaid_acc_1', 'yodlee_acc_1']
    
    @pytest.mark.asyncio
    async def test_account_categorization(self, bank_aggregator):
        """Test categorization of account types."""
        
        test_accounts = [
            {'type': 'depository', 'subtype': 'checking', 'name': 'Checking Account'},
            {'type': 'depository', 'subtype': 'savings', 'name': 'Savings Account'},
            {'type': 'credit', 'subtype': 'credit_card', 'name': 'Credit Card'},
            {'type': 'investment', 'subtype': '401k', 'name': '401k Account'},
            {'type': 'loan', 'subtype': 'mortgage', 'name': 'Home Mortgage'}
        ]
        
        categorized = bank_aggregator.categorize_accounts(test_accounts)
        
        assert 'liquid_assets' in categorized
        assert 'investment_accounts' in categorized
        assert 'credit_accounts' in categorized
        assert 'loan_accounts' in categorized
        
        # Check categorization
        assert len(categorized['liquid_assets']) == 2  # checking + savings
        assert len(categorized['credit_accounts']) == 1  # credit card
        assert len(categorized['investment_accounts']) == 1  # 401k
        assert len(categorized['loan_accounts']) == 1  # mortgage
    
    @pytest.mark.asyncio
    async def test_balance_calculation(self, bank_aggregator):
        """Test net worth and balance calculations."""
        
        accounts = [
            {'type': 'checking', 'balance': 1500.00},
            {'type': 'savings', 'balance': 5000.00},
            {'type': 'credit_card', 'balance': -750.00},  # Credit card debt
            {'type': '401k', 'balance': 25000.00},
            {'type': 'mortgage', 'balance': -250000.00}  # Mortgage debt
        ]
        
        balance_summary = bank_aggregator.calculate_balance_summary(accounts)
        
        assert balance_summary['total_assets'] == 31500.00  # 1500 + 5000 + 25000
        assert balance_summary['total_liabilities'] == 250750.00  # 750 + 250000
        assert balance_summary['net_worth'] == -219250.00  # assets - liabilities
        assert balance_summary['liquid_assets'] == 6500.00  # checking + savings
        assert balance_summary['investment_assets'] == 25000.00  # 401k


class TestTransactionCategorizer:
    """Test suite for transaction categorization."""
    
    @pytest.fixture
    def categorizer(self):
        """Create transaction categorizer instance."""
        return TransactionCategorizer()
    
    @pytest.fixture
    def sample_transactions(self):
        """Sample transactions for categorization testing."""
        return [
            {
                'id': 'txn_1',
                'description': 'NETFLIX.COM',
                'amount': 15.99,
                'merchant': 'Netflix'
            },
            {
                'id': 'txn_2',
                'description': 'SAFEWAY GROCERY',
                'amount': 87.45,
                'merchant': 'Safeway'
            },
            {
                'id': 'txn_3',
                'description': 'SHELL STATION',
                'amount': 45.20,
                'merchant': 'Shell'
            },
            {
                'id': 'txn_4',
                'description': 'PAYCHECK DEPOSIT',
                'amount': -2500.00,
                'merchant': None
            },
            {
                'id': 'txn_5',
                'description': 'RENT PAYMENT',
                'amount': 1200.00,
                'merchant': 'Property Management Co'
            }
        ]
    
    def test_rule_based_categorization(self, categorizer, sample_transactions):
        """Test rule-based transaction categorization."""
        
        categorized = categorizer.categorize_transactions(sample_transactions)
        
        # Check specific categorizations
        netflix_txn = next(txn for txn in categorized if txn['id'] == 'txn_1')
        assert netflix_txn['category'] == 'Entertainment'
        assert netflix_txn['subcategory'] == 'Streaming Services'
        
        grocery_txn = next(txn for txn in categorized if txn['id'] == 'txn_2')
        assert grocery_txn['category'] == 'Food & Dining'
        assert grocery_txn['subcategory'] == 'Groceries'
        
        gas_txn = next(txn for txn in categorized if txn['id'] == 'txn_3')
        assert gas_txn['category'] == 'Transportation'
        assert gas_txn['subcategory'] == 'Gas & Fuel'
        
        paycheck_txn = next(txn for txn in categorized if txn['id'] == 'txn_4')
        assert paycheck_txn['category'] == 'Income'
        assert paycheck_txn['subcategory'] == 'Salary'
        
        rent_txn = next(txn for txn in categorized if txn['id'] == 'txn_5')
        assert rent_txn['category'] == 'Housing'
        assert rent_txn['subcategory'] == 'Rent'
    
    @pytest.mark.asyncio
    async def test_ml_based_categorization(self, categorizer):
        """Test ML-based transaction categorization."""
        
        # Mock ML model prediction
        with patch.object(categorizer, '_ml_model') as mock_model:
            mock_model.predict.return_value = ['Food & Dining', 'Transportation', 'Shopping']
            
            transactions = [
                {'description': 'Unknown Restaurant XYZ', 'amount': 25.50},
                {'description': 'Unknown Gas Station ABC', 'amount': 30.00},
                {'description': 'Unknown Store 123', 'amount': 15.75}
            ]
            
            categorized = await categorizer.categorize_with_ml(transactions)
            
            assert categorized[0]['predicted_category'] == 'Food & Dining'
            assert categorized[1]['predicted_category'] == 'Transportation'
            assert categorized[2]['predicted_category'] == 'Shopping'
            
            # Verify model was called with transaction features
            mock_model.predict.assert_called_once()
    
    def test_confidence_scoring(self, categorizer):
        """Test confidence scoring for categorizations."""
        
        # High confidence transactions (clear merchant names)
        high_confidence_txn = {
            'description': 'STARBUCKS COFFEE',
            'merchant': 'Starbucks'
        }
        
        confidence = categorizer.calculate_confidence(high_confidence_txn, 'Food & Dining')
        assert confidence > 0.8
        
        # Low confidence transactions (ambiguous descriptions)
        low_confidence_txn = {
            'description': 'PAYMENT THANK YOU',
            'merchant': None
        }
        
        confidence = categorizer.calculate_confidence(low_confidence_txn, 'Other')
        assert confidence < 0.5
    
    def test_custom_rules_addition(self, categorizer):
        """Test adding custom categorization rules."""
        
        # Add custom rule
        custom_rule = {
            'pattern': r'VENMO.*',
            'category': 'Transfer',
            'subcategory': 'Peer-to-Peer',
            'confidence': 0.9
        }
        
        categorizer.add_custom_rule(custom_rule)
        
        # Test transaction matching custom rule
        venmo_txn = {
            'id': 'txn_venmo',
            'description': 'VENMO PAYMENT TO FRIEND',
            'amount': 50.00
        }
        
        categorized = categorizer.categorize_transactions([venmo_txn])
        
        assert categorized[0]['category'] == 'Transfer'
        assert categorized[0]['subcategory'] == 'Peer-to-Peer'
        assert categorized[0]['confidence'] == 0.9
    
    def test_category_statistics(self, categorizer, sample_transactions):
        """Test calculation of spending statistics by category."""
        
        categorized = categorizer.categorize_transactions(sample_transactions)
        stats = categorizer.calculate_category_statistics(categorized)
        
        assert 'total_spending' in stats
        assert 'category_totals' in stats
        assert 'category_percentages' in stats
        
        # Check that percentages sum to approximately 100% (excluding income)
        spending_txns = [txn for txn in categorized if txn['amount'] > 0]
        total_spending = sum(txn['amount'] for txn in spending_txns)
        
        assert abs(stats['total_spending'] - total_spending) < 0.01


class TestSpendingPatternDetector:
    """Test suite for spending pattern detection."""
    
    @pytest.fixture
    def pattern_detector(self):
        """Create spending pattern detector instance."""
        return SpendingPatternDetector()
    
    @pytest.fixture
    def sample_transaction_history(self):
        """Sample transaction history for pattern analysis."""
        transactions = []
        base_date = datetime.now() - timedelta(days=90)
        
        # Generate recurring Netflix subscription
        for i in range(3):
            transactions.append({
                'id': f'netflix_{i}',
                'description': 'NETFLIX.COM',
                'amount': 15.99,
                'date': base_date + timedelta(days=30*i),
                'category': 'Entertainment'
            })
        
        # Generate weekly grocery shopping
        for week in range(12):
            transactions.append({
                'id': f'grocery_{week}',
                'description': 'SAFEWAY GROCERY',
                'amount': 85.50 + (week * 2),  # Slightly increasing amounts
                'date': base_date + timedelta(days=7*week),
                'category': 'Food & Dining'
            })
        
        # Generate monthly rent
        for month in range(3):
            transactions.append({
                'id': f'rent_{month}',
                'description': 'RENT PAYMENT',
                'amount': 1200.00,
                'date': base_date + timedelta(days=30*month),
                'category': 'Housing'
            })
        
        return transactions
    
    def test_recurring_transaction_detection(self, pattern_detector, sample_transaction_history):
        """Test detection of recurring transactions."""
        
        recurring_patterns = pattern_detector.detect_recurring_transactions(
            sample_transaction_history
        )
        
        # Should detect 3 recurring patterns: Netflix, Groceries, Rent
        assert len(recurring_patterns) >= 3
        
        # Check Netflix pattern
        netflix_pattern = next(
            (p for p in recurring_patterns if 'netflix' in p['merchant'].lower()), None
        )
        assert netflix_pattern is not None
        assert netflix_pattern['frequency'] == 'monthly'
        assert abs(netflix_pattern['average_amount'] - 15.99) < 0.01
        
        # Check grocery pattern
        grocery_pattern = next(
            (p for p in recurring_patterns if 'safeway' in p['merchant'].lower()), None
        )
        assert grocery_pattern is not None
        assert grocery_pattern['frequency'] == 'weekly'
        
        # Check rent pattern
        rent_pattern = next(
            (p for p in recurring_patterns if 'rent' in p['description'].lower()), None
        )
        assert rent_pattern is not None
        assert rent_pattern['frequency'] == 'monthly'
        assert rent_pattern['average_amount'] == 1200.00
    
    def test_spending_trend_analysis(self, pattern_detector, sample_transaction_history):
        """Test analysis of spending trends over time."""
        
        trends = pattern_detector.analyze_spending_trends(
            sample_transaction_history, period='monthly'
        )
        
        assert 'overall_trend' in trends
        assert 'category_trends' in trends
        assert 'period_comparisons' in trends
        
        # Check that trends include direction and magnitude
        overall_trend = trends['overall_trend']
        assert 'direction' in overall_trend  # 'increasing', 'decreasing', 'stable'
        assert 'percentage_change' in overall_trend
        assert 'confidence' in overall_trend
    
    def test_anomaly_detection(self, pattern_detector):
        """Test detection of spending anomalies."""
        
        # Create normal spending pattern with one anomaly
        normal_transactions = [
            {'id': f'normal_{i}', 'amount': 50.0 + (i % 3), 'category': 'Food', 
             'date': datetime.now() - timedelta(days=i)}
            for i in range(30)
        ]
        
        # Add anomalous transaction
        anomaly_transaction = {
            'id': 'anomaly_1',
            'amount': 500.0,  # Much higher than normal
            'category': 'Food',
            'date': datetime.now() - timedelta(days=1)
        }
        
        all_transactions = normal_transactions + [anomaly_transaction]
        
        anomalies = pattern_detector.detect_anomalies(all_transactions)
        
        assert len(anomalies) >= 1
        anomaly = anomalies[0]
        assert anomaly['transaction_id'] == 'anomaly_1'
        assert anomaly['anomaly_score'] > 0.7  # High anomaly score
        assert anomaly['reason'] == 'amount_outlier'
    
    def test_seasonal_pattern_detection(self, pattern_detector):
        """Test detection of seasonal spending patterns."""
        
        # Generate transactions with seasonal pattern (higher spending in December)
        transactions = []
        for month in range(1, 13):
            base_amount = 100.0
            if month == 12:  # December - holiday spending
                seasonal_multiplier = 2.5
            elif month in [6, 7, 8]:  # Summer vacation spending
                seasonal_multiplier = 1.5
            else:
                seasonal_multiplier = 1.0
            
            for day in range(5):  # 5 transactions per month
                transactions.append({
                    'id': f'txn_{month}_{day}',
                    'amount': base_amount * seasonal_multiplier,
                    'category': 'Shopping',
                    'date': datetime(2024, month, day + 1)
                })
        
        seasonal_patterns = pattern_detector.detect_seasonal_patterns(transactions)
        
        assert 'monthly_patterns' in seasonal_patterns
        assert 'seasonal_categories' in seasonal_patterns
        
        # December should show high spending
        december_pattern = seasonal_patterns['monthly_patterns'].get(12)
        if december_pattern:
            assert december_pattern['spending_multiplier'] > 2.0
    
    def test_budget_variance_analysis(self, pattern_detector):
        """Test analysis of actual vs budgeted spending."""
        
        budget = {
            'Food & Dining': 400.00,
            'Transportation': 200.00,
            'Entertainment': 100.00,
            'Shopping': 300.00
        }
        
        actual_transactions = [
            {'category': 'Food & Dining', 'amount': 450.00},
            {'category': 'Transportation', 'amount': 180.00},
            {'category': 'Entertainment', 'amount': 120.00},
            {'category': 'Shopping', 'amount': 350.00}
        ]
        
        variance_analysis = pattern_detector.analyze_budget_variance(
            actual_transactions, budget
        )
        
        assert 'category_variances' in variance_analysis
        assert 'total_variance' in variance_analysis
        assert 'categories_over_budget' in variance_analysis
        
        # Food & Dining should be over budget
        food_variance = variance_analysis['category_variances']['Food & Dining']
        assert food_variance['variance_amount'] == 50.00
        assert food_variance['variance_percentage'] > 0
        
        # Transportation should be under budget
        transport_variance = variance_analysis['category_variances']['Transportation']
        assert transport_variance['variance_amount'] == -20.00
        assert transport_variance['variance_percentage'] < 0


class TestCashFlowAnalyzer:
    """Test suite for cash flow analysis."""
    
    @pytest.fixture
    def cash_flow_analyzer(self):
        """Create cash flow analyzer instance."""
        return CashFlowAnalyzer()
    
    def test_cash_flow_calculation(self, cash_flow_analyzer):
        """Test basic cash flow calculation."""
        
        transactions = [
            {'amount': -2500.00, 'category': 'Income', 'type': 'credit'},  # Salary
            {'amount': 1200.00, 'category': 'Housing', 'type': 'debit'},   # Rent
            {'amount': 400.00, 'category': 'Food', 'type': 'debit'},       # Food
            {'amount': 200.00, 'category': 'Transportation', 'type': 'debit'}, # Gas
            {'amount': 100.00, 'category': 'Entertainment', 'type': 'debit'},  # Entertainment
        ]
        
        cash_flow = cash_flow_analyzer.calculate_cash_flow(transactions)
        
        assert cash_flow['total_income'] == 2500.00
        assert cash_flow['total_expenses'] == 1900.00
        assert cash_flow['net_cash_flow'] == 600.00
        assert cash_flow['savings_rate'] == 0.24  # 600/2500
    
    def test_monthly_cash_flow_projection(self, cash_flow_analyzer):
        """Test monthly cash flow projection."""
        
        historical_data = {
            'average_monthly_income': 2500.00,
            'average_monthly_expenses': 1900.00,
            'expense_categories': {
                'Housing': 1200.00,
                'Food': 400.00,
                'Transportation': 200.00,
                'Entertainment': 100.00
            }
        }
        
        projection = cash_flow_analyzer.project_monthly_cash_flow(
            historical_data, months=6
        )
        
        assert len(projection['monthly_projections']) == 6
        
        for month_data in projection['monthly_projections']:
            assert 'projected_income' in month_data
            assert 'projected_expenses' in month_data
            assert 'projected_net_flow' in month_data
            assert 'cumulative_savings' in month_data
        
        # Cumulative savings should increase over time (assuming positive cash flow)
        if projection['monthly_projections'][0]['projected_net_flow'] > 0:
            assert (projection['monthly_projections'][-1]['cumulative_savings'] > 
                   projection['monthly_projections'][0]['cumulative_savings'])
    
    def test_cash_flow_stress_testing(self, cash_flow_analyzer):
        """Test cash flow under different scenarios."""
        
        base_cash_flow = {
            'monthly_income': 2500.00,
            'monthly_expenses': 1900.00,
            'emergency_fund': 5000.00
        }
        
        scenarios = [
            {'name': 'job_loss', 'income_reduction': 1.0, 'duration_months': 3},
            {'name': 'medical_emergency', 'expense_increase': 2000.00, 'duration_months': 1},
            {'name': 'economic_downturn', 'income_reduction': 0.2, 'expense_increase': 200.00, 'duration_months': 12}
        ]
        
        stress_test_results = cash_flow_analyzer.stress_test_cash_flow(
            base_cash_flow, scenarios
        )
        
        assert len(stress_test_results) == 3
        
        for scenario_result in stress_test_results:
            assert 'scenario_name' in scenario_result
            assert 'months_until_depletion' in scenario_result
            assert 'total_shortfall' in scenario_result
            assert 'recommendations' in scenario_result
        
        # Job loss scenario should show fastest depletion
        job_loss_result = next(r for r in stress_test_results if r['scenario_name'] == 'job_loss')
        assert job_loss_result['months_until_depletion'] is not None
    
    def test_cash_flow_optimization_suggestions(self, cash_flow_analyzer):
        """Test generation of cash flow optimization suggestions."""
        
        cash_flow_data = {
            'monthly_income': 2500.00,
            'monthly_expenses': 2400.00,  # Very little savings
            'expense_breakdown': {
                'Housing': 1200.00,
                'Food': 600.00,  # High food spending
                'Transportation': 400.00,  # High transportation costs
                'Entertainment': 200.00   # High entertainment spending
            },
            'debt_payments': 300.00,
            'savings_rate': 0.04  # Only 4% savings rate
        }
        
        suggestions = cash_flow_analyzer.generate_optimization_suggestions(cash_flow_data)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Should suggest reducing high spending categories
        suggestion_texts = [s['description'].lower() for s in suggestions]
        assert any('food' in text for text in suggestion_texts)
        assert any('entertainment' in text for text in suggestion_texts)
        
        # Should suggest increasing savings rate
        assert any('savings' in text for text in suggestion_texts)
        
        # Each suggestion should have priority and estimated impact
        for suggestion in suggestions:
            assert 'priority' in suggestion
            assert 'estimated_monthly_savings' in suggestion
            assert 'difficulty' in suggestion


class TestCredentialVault:
    """Test suite for secure credential storage."""
    
    @pytest.fixture
    def credential_vault(self):
        """Create credential vault instance."""
        return CredentialVault()
    
    def test_credential_encryption(self, credential_vault):
        """Test encryption and decryption of credentials."""
        
        credentials = {
            'username': 'testuser123',
            'password': 'secretpassword456',
            'account_id': 'acc_789012'
        }
        
        # Encrypt credentials
        encrypted_data = credential_vault.encrypt_credentials(credentials)
        
        assert encrypted_data != credentials
        assert isinstance(encrypted_data, str)  # Should be base64 encoded
        
        # Decrypt credentials
        decrypted_data = credential_vault.decrypt_credentials(encrypted_data)
        
        assert decrypted_data == credentials
    
    @pytest.mark.asyncio
    async def test_credential_storage_retrieval(self, credential_vault):
        """Test storing and retrieving credentials."""
        
        user_id = 'user_123'
        provider = 'plaid'
        credentials = {
            'access_token': 'access-sandbox-token-123',
            'item_id': 'item_456',
            'institution_id': 'ins_789'
        }
        
        # Store credentials
        credential_id = await credential_vault.store_credentials(
            user_id, provider, credentials
        )
        
        assert credential_id is not None
        assert isinstance(credential_id, str)
        
        # Retrieve credentials
        retrieved_credentials = await credential_vault.get_credentials(
            user_id, provider
        )
        
        assert retrieved_credentials == credentials
    
    @pytest.mark.asyncio
    async def test_credential_rotation(self, credential_vault):
        """Test credential rotation functionality."""
        
        user_id = 'user_123'
        provider = 'yodlee'
        
        # Store initial credentials
        initial_credentials = {'session_token': 'token_123'}
        credential_id = await credential_vault.store_credentials(
            user_id, provider, initial_credentials
        )
        
        # Rotate credentials
        new_credentials = {'session_token': 'token_456'}
        await credential_vault.rotate_credentials(
            credential_id, new_credentials
        )
        
        # Retrieve updated credentials
        retrieved_credentials = await credential_vault.get_credentials(
            user_id, provider
        )
        
        assert retrieved_credentials == new_credentials
        assert retrieved_credentials != initial_credentials
    
    def test_credential_expiration(self, credential_vault):
        """Test credential expiration handling."""
        
        # Create credentials with short expiration
        credentials = {
            'access_token': 'token_123',
            'expires_at': datetime.now() + timedelta(minutes=1)
        }
        
        # Should not be expired initially
        assert not credential_vault.is_expired(credentials)
        
        # Mock time passage
        with patch('app.services.banking.credential_vault.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=2)
            
            # Should be expired now
            assert credential_vault.is_expired(credentials)
    
    @pytest.mark.asyncio
    async def test_credential_audit_logging(self, credential_vault):
        """Test audit logging for credential operations."""
        
        with patch.object(credential_vault, '_audit_logger') as mock_audit:
            user_id = 'user_123'
            provider = 'plaid'
            credentials = {'access_token': 'token_123'}
            
            await credential_vault.store_credentials(user_id, provider, credentials)
            
            # Should log credential storage
            mock_audit.log_event.assert_called()
            call_args = mock_audit.log_event.call_args[1]
            assert call_args['event_type'] == 'credential_stored'
            assert call_args['user_id'] == user_id
            assert call_args['provider'] == provider


class TestWebhookHandler:
    """Test suite for webhook handling."""
    
    @pytest.fixture
    def webhook_handler(self):
        """Create webhook handler instance."""
        return WebhookHandler()
    
    @pytest.mark.asyncio
    async def test_plaid_webhook_processing(self, webhook_handler):
        """Test processing of Plaid webhooks."""
        
        webhook_data = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'DEFAULT_UPDATE',
            'item_id': 'item_123',
            'new_transactions': 5,
            'removed_transactions': ['txn_removed_1']
        }
        
        with patch.object(webhook_handler, '_plaid_service') as mock_plaid:
            mock_plaid.get_transactions.return_value = [
                {'transaction_id': 'new_txn_1', 'amount': 25.50},
                {'transaction_id': 'new_txn_2', 'amount': 12.99}
            ]
            
            result = await webhook_handler.process_plaid_webhook(webhook_data)
            
            assert result['status'] == 'processed'
            assert result['new_transactions_processed'] == 5
            
            # Should fetch new transactions
            mock_plaid.get_transactions.assert_called()
    
    @pytest.mark.asyncio
    async def test_yodlee_webhook_processing(self, webhook_handler):
        """Test processing of Yodlee webhooks."""
        
        webhook_data = {
            'event': 'REFRESH',
            'data': {
                'providerAccountId': 789012,
                'status': 'SUCCESS',
                'dataset': ['BASIC_AGG_DATA']
            }
        }
        
        with patch.object(webhook_handler, '_yodlee_service') as mock_yodlee:
            mock_yodlee.get_accounts.return_value = [
                {'id': 123456, 'balance': {'amount': 1500.00}}
            ]
            
            result = await webhook_handler.process_yodlee_webhook(webhook_data)
            
            assert result['status'] == 'processed'
            assert result['provider_account_id'] == 789012
            
            # Should refresh account data
            mock_yodlee.get_accounts.assert_called()
    
    @pytest.mark.asyncio
    async def test_webhook_signature_validation(self, webhook_handler):
        """Test webhook signature validation."""
        
        webhook_body = json.dumps({'test': 'data'})
        valid_signature = 'valid_signature_123'
        invalid_signature = 'invalid_signature_456'
        
        with patch.object(webhook_handler, '_validate_signature') as mock_validate:
            # Test valid signature
            mock_validate.return_value = True
            is_valid = webhook_handler.validate_webhook_signature(
                webhook_body, valid_signature, 'plaid'
            )
            assert is_valid
            
            # Test invalid signature
            mock_validate.return_value = False
            is_valid = webhook_handler.validate_webhook_signature(
                webhook_body, invalid_signature, 'plaid'
            )
            assert not is_valid
    
    @pytest.mark.asyncio
    async def test_webhook_error_handling(self, webhook_handler):
        """Test error handling in webhook processing."""
        
        webhook_data = {
            'webhook_type': 'TRANSACTIONS',
            'webhook_code': 'DEFAULT_UPDATE',
            'item_id': 'item_123'
        }
        
        # Mock service failure
        with patch.object(webhook_handler, '_plaid_service') as mock_plaid:
            mock_plaid.get_transactions.side_effect = Exception('API Error')
            
            result = await webhook_handler.process_plaid_webhook(webhook_data)
            
            assert result['status'] == 'error'
            assert 'error_message' in result
            assert 'API Error' in result['error_message']
    
    @pytest.mark.asyncio
    async def test_webhook_retry_mechanism(self, webhook_handler):
        """Test retry mechanism for failed webhooks."""
        
        webhook_data = {'item_id': 'item_123'}
        
        with patch.object(webhook_handler, '_plaid_service') as mock_plaid:
            # Fail first two attempts, succeed on third
            mock_plaid.get_transactions.side_effect = [
                Exception('Temporary error'),
                Exception('Temporary error'),
                [{'transaction_id': 'success_txn'}]
            ]
            
            result = await webhook_handler.process_plaid_webhook(
                webhook_data, max_retries=3
            )
            
            assert result['status'] == 'processed'
            assert result['retry_count'] == 2
            
            # Should have been called 3 times
            assert mock_plaid.get_transactions.call_count == 3