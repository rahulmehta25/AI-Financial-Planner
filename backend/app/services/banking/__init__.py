"""
Banking Integration Services

This module provides secure banking integration capabilities including:
- Plaid API integration for account aggregation
- Yodlee fallback provider
- Secure credential vault with encryption
- Transaction categorization engine
- Automated cash flow analysis
- Spending pattern detection
- Account balance monitoring
- Secure webhook handlers
"""

from .plaid_service import PlaidService
from .yodlee_service import YodleeService
from .credential_vault import CredentialVault
from .transaction_categorizer import TransactionCategorizer
from .cash_flow_analyzer import CashFlowAnalyzer
from .spending_pattern_detector import SpendingPatternDetector
from .balance_monitor import BalanceMonitor
from .webhook_handler import BankingWebhookHandler
from .bank_aggregator import BankAggregator
from .error_handler import BankingErrorHandler, with_retry, with_plaid_retry, with_yodlee_retry

__all__ = [
    "PlaidService",
    "YodleeService", 
    "CredentialVault",
    "TransactionCategorizer",
    "CashFlowAnalyzer",
    "SpendingPatternDetector",
    "BalanceMonitor",
    "BankingWebhookHandler",
    "BankAggregator",
    "BankingErrorHandler",
    "with_retry",
    "with_plaid_retry", 
    "with_yodlee_retry"
]