"""
Unit tests for banking service and transaction processing.

Tests Plaid integration, transaction categorization, and account aggregation.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta

from app.services.banking.plaid_service import PlaidService
from app.services.banking.transaction_categorizer import TransactionCategorizer
from app.services.banking.cash_flow_analyzer import CashFlowAnalyzer
from app.services.banking.spending_pattern_detector import SpendingPatternDetector
from tests.factories import UserFactory


class TestPlaidService:
    """Test cases for Plaid banking service integration."""
    
    @pytest.fixture
    def plaid_service(self, mock_plaid_client):
        """Create PlaidService with mocked client."""
        service = PlaidService()
        service.client = mock_plaid_client
        return service
    
    @pytest.fixture
    def mock_plaid_accounts_response(self):
        """Mock Plaid accounts response."""
        return {
            'accounts': [
                {
                    'account_id': 'account_1',
                    'name': 'Checking Account',
                    'type': 'depository',
                    'subtype': 'checking',
                    'balances': {
                        'available': 2500.50,
                        'current': 2500.50,
                        'iso_currency_code': 'USD'
                    }
                },
                {
                    'account_id': 'account_2',
                    'name': 'Savings Account',
                    'type': 'depository',
                    'subtype': 'savings',
                    'balances': {
                        'available': 15000.00,
                        'current': 15000.00,
                        'iso_currency_code': 'USD'
                    }
                }
            ]
        }
    
    @pytest.fixture
    def mock_plaid_transactions_response(self):
        """Mock Plaid transactions response."""
        return {
            'transactions': [
                {
                    'transaction_id': 'txn_1',
                    'account_id': 'account_1',
                    'amount': 85.50,
                    'date': '2023-11-15',
                    'name': 'Whole Foods Market',
                    'category': ['Shops', 'Food and Drink', 'Groceries'],
                    'category_id': '13005013',
                    'merchant_name': 'Whole Foods'
                },
                {
                    'transaction_id': 'txn_2',
                    'account_id': 'account_1',
                    'amount': -2500.00,
                    'date': '2023-11-01',
                    'name': 'Payroll Deposit',
                    'category': ['Deposit'],
                    'category_id': '21006000'
                }
            ],
            'total_transactions': 2
        }
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, plaid_service, mock_plaid_accounts_response):
        """Test retrieving user accounts from Plaid."""
        # Arrange
        access_token = "test_access_token"
        plaid_service.client.accounts_get.return_value = mock_plaid_accounts_response
        
        # Act
        accounts = await plaid_service.get_accounts(access_token)
        
        # Assert
        assert len(accounts) == 2
        assert accounts[0]['name'] == 'Checking Account'
        assert accounts[0]['balance'] == 2500.50
        assert accounts[1]['name'] == 'Savings Account'
        assert accounts[1]['balance'] == 15000.00
        plaid_service.client.accounts_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_transactions(self, plaid_service, mock_plaid_transactions_response):
        """Test retrieving transactions from Plaid."""
        # Arrange
        access_token = "test_access_token"
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date()
        plaid_service.client.transactions_get.return_value = mock_plaid_transactions_response
        
        # Act
        transactions = await plaid_service.get_transactions(access_token, start_date, end_date)
        
        # Assert
        assert len(transactions) == 2
        assert transactions[0]['amount'] == 85.50
        assert transactions[0]['merchant_name'] == 'Whole Foods'
        assert transactions[1]['amount'] == -2500.00  # Negative for income
        plaid_service.client.transactions_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_link_token(self, plaid_service):
        """Test creating Plaid link token."""
        # Arrange
        user_id = "test_user_id"
        mock_response = {
            'link_token': 'link-sandbox-12345',
            'expiration': '2023-12-01T10:00:00Z'
        }
        plaid_service.client.link_token_create.return_value = mock_response
        
        # Act
        link_token = await plaid_service.create_link_token(user_id)
        
        # Assert
        assert link_token == 'link-sandbox-12345'
        plaid_service.client.link_token_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exchange_public_token(self, plaid_service):
        """Test exchanging public token for access token."""
        # Arrange
        public_token = "public-sandbox-12345"
        mock_response = {
            'access_token': 'access-sandbox-67890',
            'item_id': 'item-123'
        }
        plaid_service.client.item_public_token_exchange.return_value = mock_response
        
        # Act
        access_token = await plaid_service.exchange_public_token(public_token)
        
        # Assert
        assert access_token == 'access-sandbox-67890'
        plaid_service.client.item_public_token_exchange.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_plaid_error_handling(self, plaid_service):
        """Test error handling for Plaid API errors."""
        # Arrange
        from plaid.exceptions import PlaidError
        access_token = "invalid_token"
        plaid_service.client.accounts_get.side_effect = PlaidError({
            'error_code': 'INVALID_ACCESS_TOKEN',
            'error_message': 'Invalid access token'
        })
        
        # Act & Assert
        with pytest.raises(PlaidError):
            await plaid_service.get_accounts(access_token)


class TestTransactionCategorizer:
    """Test cases for transaction categorization."""
    
    @pytest.fixture
    def categorizer(self):
        """Create transaction categorizer."""
        return TransactionCategorizer()
    
    @pytest.fixture
    def sample_transactions(self):
        """Sample transactions for testing."""
        return [
            {
                'name': 'Whole Foods Market',
                'amount': 85.50,
                'category': ['Shops', 'Food and Drink', 'Groceries'],
                'merchant_name': 'Whole Foods'
            },
            {
                'name': 'Shell Gas Station',
                'amount': 45.20,
                'category': ['Transportation', 'Gas Stations'],
                'merchant_name': 'Shell'
            },
            {
                'name': 'Netflix Subscription',
                'amount': 15.99,
                'category': ['Recreation', 'Entertainment'],
                'merchant_name': 'Netflix'
            },
            {
                'name': 'Payroll Deposit',
                'amount': -3000.00,
                'category': ['Deposit'],
                'merchant_name': None
            }
        ]
    
    def test_categorize_transaction(self, categorizer, sample_transactions):
        """Test individual transaction categorization."""
        # Test grocery transaction
        grocery_txn = sample_transactions[0]
        category = categorizer.categorize_transaction(grocery_txn)
        assert category == 'Food & Dining'
        
        # Test gas transaction
        gas_txn = sample_transactions[1]
        category = categorizer.categorize_transaction(gas_txn)
        assert category == 'Transportation'
        
        # Test entertainment transaction
        entertainment_txn = sample_transactions[2]
        category = categorizer.categorize_transaction(entertainment_txn)
        assert category == 'Entertainment'
        
        # Test income transaction
        income_txn = sample_transactions[3]
        category = categorizer.categorize_transaction(income_txn)
        assert category == 'Income'
    
    def test_categorize_batch(self, categorizer, sample_transactions):
        """Test batch categorization of transactions."""
        # Act
        categorized = categorizer.categorize_batch(sample_transactions)
        
        # Assert
        assert len(categorized) == 4
        assert categorized[0]['category'] == 'Food & Dining'
        assert categorized[1]['category'] == 'Transportation'
        assert categorized[2]['category'] == 'Entertainment'
        assert categorized[3]['category'] == 'Income'
    
    def test_custom_rules(self, categorizer):
        """Test custom categorization rules."""
        # Add custom rule
        categorizer.add_custom_rule(
            merchant_pattern="AMAZON",
            category="Shopping"
        )
        
        # Test transaction matching custom rule
        amazon_txn = {
            'name': 'AMAZON MARKETPLACE',
            'amount': 29.99,
            'category': ['Shops'],
            'merchant_name': 'Amazon'
        }
        
        category = categorizer.categorize_transaction(amazon_txn)
        assert category == 'Shopping'
    
    def test_confidence_scoring(self, categorizer, sample_transactions):
        """Test confidence scoring for categorization."""
        grocery_txn = sample_transactions[0]
        result = categorizer.categorize_with_confidence(grocery_txn)
        
        assert 'category' in result
        assert 'confidence' in result
        assert result['category'] == 'Food & Dining'
        assert 0 <= result['confidence'] <= 1
        assert result['confidence'] > 0.8  # High confidence for clear category


class TestCashFlowAnalyzer:
    """Test cases for cash flow analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create cash flow analyzer."""
        return CashFlowAnalyzer()
    
    @pytest.fixture
    def monthly_transactions(self):
        """Sample monthly transactions."""
        return [
            # Income
            {'amount': -3000.00, 'category': 'Income', 'date': '2023-11-01'},
            {'amount': -500.00, 'category': 'Income', 'date': '2023-11-15'},  # Bonus
            
            # Expenses
            {'amount': 1200.00, 'category': 'Housing', 'date': '2023-11-01'},  # Rent
            {'amount': 400.00, 'category': 'Food & Dining', 'date': '2023-11-03'},
            {'amount': 150.00, 'category': 'Transportation', 'date': '2023-11-05'},
            {'amount': 200.00, 'category': 'Utilities', 'date': '2023-11-08'},
            {'amount': 100.00, 'category': 'Entertainment', 'date': '2023-11-10'},
            {'amount': 75.00, 'category': 'Shopping', 'date': '2023-11-12'}
        ]
    
    def test_calculate_monthly_cash_flow(self, analyzer, monthly_transactions):
        """Test monthly cash flow calculation."""
        # Act
        cash_flow = analyzer.calculate_monthly_cash_flow(monthly_transactions)
        
        # Assert
        assert 'total_income' in cash_flow
        assert 'total_expenses' in cash_flow
        assert 'net_cash_flow' in cash_flow
        assert 'expense_categories' in cash_flow
        
        assert cash_flow['total_income'] == 3500.00
        assert cash_flow['total_expenses'] == 2125.00
        assert cash_flow['net_cash_flow'] == 1375.00
        assert cash_flow['expense_categories']['Housing'] == 1200.00
    
    def test_trend_analysis(self, analyzer):
        """Test cash flow trend analysis over multiple months."""
        # Arrange
        monthly_data = [
            {'month': '2023-09', 'income': 3000, 'expenses': 2200, 'net': 800},
            {'month': '2023-10', 'income': 3200, 'expenses': 2100, 'net': 1100},
            {'month': '2023-11', 'income': 3500, 'expenses': 2125, 'net': 1375}
        ]
        
        # Act
        trends = analyzer.analyze_trends(monthly_data)
        
        # Assert
        assert 'income_trend' in trends
        assert 'expense_trend' in trends
        assert 'savings_rate_trend' in trends
        assert trends['income_trend'] == 'increasing'
        assert trends['savings_rate_trend'] == 'improving'
    
    def test_budget_variance_analysis(self, analyzer, monthly_transactions):
        """Test budget vs actual spending analysis."""
        # Arrange
        budget = {
            'Housing': 1200,
            'Food & Dining': 500,
            'Transportation': 200,
            'Utilities': 150,
            'Entertainment': 100,
            'Shopping': 100
        }
        
        # Act
        variance = analyzer.analyze_budget_variance(monthly_transactions, budget)
        
        # Assert
        assert 'category_variances' in variance
        assert 'total_variance' in variance
        assert 'over_budget_categories' in variance
        
        # Food & Dining was under budget (400 vs 500)
        assert variance['category_variances']['Food & Dining'] == -100
        # Utilities was over budget (200 vs 150)  
        assert variance['category_variances']['Utilities'] == 50


class TestSpendingPatternDetector:
    """Test cases for spending pattern detection."""
    
    @pytest.fixture
    def detector(self):
        """Create spending pattern detector."""
        return SpendingPatternDetector()
    
    @pytest.fixture
    def historical_transactions(self):
        """Historical transactions for pattern detection."""
        transactions = []
        # Generate 6 months of sample data
        for month in range(6):
            base_date = datetime.now().date() - timedelta(days=30*month)
            
            # Regular patterns
            transactions.extend([
                {'amount': 1200, 'category': 'Housing', 'date': base_date, 'merchant': 'Rent'},
                {'amount': 150, 'category': 'Utilities', 'date': base_date + timedelta(days=5)},
                {'amount': 300, 'category': 'Food & Dining', 'date': base_date + timedelta(days=10)},
                {'amount': 100, 'category': 'Transportation', 'date': base_date + timedelta(days=15)}
            ])
            
            # Occasional larger expenses
            if month % 2 == 0:
                transactions.append({
                    'amount': 500, 'category': 'Shopping', 
                    'date': base_date + timedelta(days=20)
                })
        
        return transactions
    
    def test_detect_recurring_transactions(self, detector, historical_transactions):
        """Test detection of recurring transactions."""
        # Act
        recurring = detector.detect_recurring_transactions(historical_transactions)
        
        # Assert
        assert len(recurring) > 0
        
        # Should detect rent as highly recurring
        rent_pattern = next((r for r in recurring if r['merchant'] == 'Rent'), None)
        assert rent_pattern is not None
        assert rent_pattern['frequency'] == 'monthly'
        assert rent_pattern['confidence'] > 0.9
        assert rent_pattern['amount'] == 1200
    
    def test_detect_seasonal_patterns(self, detector):
        """Test detection of seasonal spending patterns."""
        # Arrange - simulate holiday season spending
        transactions = []
        for year in [2022, 2023]:
            for month in range(1, 13):
                base_amount = 100
                # Increase spending in November/December (holiday season)
                if month in [11, 12]:
                    base_amount *= 3
                
                transactions.append({
                    'amount': base_amount,
                    'category': 'Shopping',
                    'date': f'{year}-{month:02d}-15',
                    'merchant': 'Various'
                })
        
        # Act
        seasonal = detector.detect_seasonal_patterns(transactions)
        
        # Assert
        assert 'Shopping' in seasonal
        shopping_pattern = seasonal['Shopping']
        assert 'peak_months' in shopping_pattern
        assert 11 in shopping_pattern['peak_months']
        assert 12 in shopping_pattern['peak_months']
    
    def test_detect_anomalies(self, detector, historical_transactions):
        """Test detection of spending anomalies."""
        # Add an anomalous transaction
        anomaly_txn = {
            'amount': 5000,  # Much larger than usual
            'category': 'Shopping',
            'date': datetime.now().date(),
            'merchant': 'Expensive Store'
        }
        historical_transactions.append(anomaly_txn)
        
        # Act
        anomalies = detector.detect_anomalies(historical_transactions)
        
        # Assert
        assert len(anomalies) > 0
        found_anomaly = any(a['amount'] == 5000 for a in anomalies)
        assert found_anomaly
    
    def test_spending_insights(self, detector, historical_transactions):
        """Test generation of spending insights."""
        # Act
        insights = detector.generate_insights(historical_transactions)
        
        # Assert
        assert 'top_categories' in insights
        assert 'spending_velocity' in insights
        assert 'monthly_average' in insights
        assert 'recommendations' in insights
        
        # Housing should be top category
        assert insights['top_categories'][0]['category'] == 'Housing'
        assert len(insights['recommendations']) > 0
    
    @pytest.mark.benchmark
    def test_pattern_detection_performance(self, detector, benchmark):
        """Benchmark pattern detection performance."""
        # Generate large dataset
        large_dataset = []
        for i in range(10000):
            large_dataset.append({
                'amount': 50 + (i % 100),
                'category': ['Food', 'Transport', 'Shopping'][i % 3],
                'date': datetime.now().date() - timedelta(days=i % 365),
                'merchant': f'Merchant_{i % 50}'
            })
        
        # Benchmark should complete within reasonable time
        result = benchmark(detector.detect_recurring_transactions, large_dataset)
        assert result is not None