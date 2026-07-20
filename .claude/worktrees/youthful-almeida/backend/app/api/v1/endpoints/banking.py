"""
Banking Integration API Endpoints

This module provides secure REST API endpoints for banking integration
with comprehensive security controls and validation.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator

from app.api.deps import (
    get_db, get_current_active_user, get_current_verified_user,
    audit_log_dependency
)
from app.database.models import User
from app.services.banking import (
    bank_aggregator, 
    PlaidService, 
    YodleeService,
    balance_monitor,
    transaction_categorizer,
    cash_flow_analyzer,
    spending_pattern_detector,
    banking_webhook_handler
)
from app.core.exceptions import ValidationError, BankingIntegrationError

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


# Pydantic Models for Request/Response
class LinkTokenRequest(BaseModel):
    """Request model for creating link token"""
    preferred_provider: Optional[str] = Field(None, description="Preferred banking provider")
    
    @validator('preferred_provider')
    def validate_provider(cls, v):
        if v and v not in ['plaid', 'yodlee']:
            raise ValueError('Provider must be plaid or yodlee')
        return v


class LinkTokenResponse(BaseModel):
    """Response model for link token"""
    link_token: Optional[str] = None
    providers: Optional[List[Dict[str, Any]]] = None
    provider: str
    success: bool
    message: Optional[str] = None


class ConnectAccountRequest(BaseModel):
    """Request model for connecting bank account"""
    provider: str = Field(..., description="Banking provider")
    connection_data: Dict[str, Any] = Field(..., description="Provider-specific connection data")
    
    @validator('provider')
    def validate_provider(cls, v):
        if v not in ['plaid', 'yodlee']:
            raise ValueError('Provider must be plaid or yodlee')
        return v


class ConnectAccountResponse(BaseModel):
    """Response model for account connection"""
    credential_id: str
    success: bool
    message: str
    accounts_connected: int = 0


class BankAccountInfo(BaseModel):
    """Bank account information"""
    account_id: str
    name: str
    type: str
    subtype: Optional[str]
    current_balance: Optional[float]
    available_balance: Optional[float]
    currency: str
    mask: Optional[str]
    provider: str


class TransactionInfo(BaseModel):
    """Transaction information"""
    transaction_id: str
    account_id: str
    amount: float
    date: datetime
    name: str
    merchant_name: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    pending: bool
    location: Optional[Dict[str, Any]]


class FinancialSummaryResponse(BaseModel):
    """Financial summary response"""
    user_id: str
    generated_at: datetime
    total_accounts: int
    total_balance: float
    monthly_income: float
    monthly_expenses: float
    net_cash_flow: float
    savings_rate: float
    financial_health_score: float
    top_spending_categories: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]


class CashFlowAnalysisRequest(BaseModel):
    """Cash flow analysis request"""
    lookback_days: int = Field(90, ge=30, le=365, description="Days of transaction history")
    analysis_period: str = Field("monthly", description="Analysis period")
    include_forecasting: bool = Field(True, description="Include cash flow forecasting")
    
    @validator('analysis_period')
    def validate_period(cls, v):
        if v not in ['monthly', 'quarterly', 'yearly']:
            raise ValueError('Period must be monthly, quarterly, or yearly')
        return v


class SpendingAnalysisRequest(BaseModel):
    """Spending pattern analysis request"""
    lookback_days: int = Field(90, ge=30, le=365, description="Days of transaction history")
    include_anomaly_detection: bool = Field(True, description="Include anomaly detection")
    confidence_threshold: float = Field(0.8, ge=0.1, le=1.0, description="Pattern confidence threshold")


class CategorizationFeedbackRequest(BaseModel):
    """Transaction categorization feedback"""
    transaction_id: str
    correct_category: str
    correct_subcategory: Optional[str]
    notes: Optional[str]


class AlertPreferencesRequest(BaseModel):
    """Alert preferences configuration"""
    enable_low_balance_alerts: bool = True
    low_balance_threshold: Optional[float] = Field(None, ge=0)
    enable_spending_alerts: bool = True
    spending_threshold_percentage: float = Field(20.0, ge=5.0, le=100.0)
    notification_methods: List[str] = Field(['in_app'], description="Notification methods")
    
    @validator('notification_methods')
    def validate_notification_methods(cls, v):
        valid_methods = ['in_app', 'email', 'sms', 'push']
        for method in v:
            if method not in valid_methods:
                raise ValueError(f'Invalid notification method: {method}')
        return v


# API Endpoints
@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    request: LinkTokenRequest,
    current_user: User = Depends(get_current_verified_user),
    audit_data: dict = Depends(lambda: audit_log_dependency("CREATE", "banking_link_token"))
):
    """
    Create a link token for banking account connection
    
    This endpoint creates a secure link token that can be used by the frontend
    to initialize the account linking process with supported banking providers.
    """
    try:
        preferred_provider = None
        if request.preferred_provider:
            if request.preferred_provider == 'plaid':
                from app.services.banking.bank_aggregator import BankingProvider
                preferred_provider = BankingProvider.PLAID
            elif request.preferred_provider == 'yodlee':
                from app.services.banking.bank_aggregator import BankingProvider
                preferred_provider = BankingProvider.YODLEE
        
        result = await bank_aggregator.create_link_token(
            str(current_user.id), 
            preferred_provider
        )
        
        logger.info(f"Created link token for user {current_user.id}")
        
        return LinkTokenResponse(
            link_token=result.get('link_token'),
            providers=result.get('providers'),
            provider=result['provider'],
            success=result['success'],
            message="Link token created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating link token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create link token: {str(e)}"
        )


@router.post("/connect", response_model=ConnectAccountResponse)
async def connect_bank_account(
    request: ConnectAccountRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    audit_data: dict = Depends(lambda: audit_log_dependency("CREATE", "banking_connection"))
):
    """
    Connect a bank account using provider credentials
    
    This endpoint securely connects a bank account through supported providers
    and starts monitoring for balance alerts and transaction updates.
    """
    try:
        # Validate connection data based on provider
        if request.provider == 'plaid':
            if 'public_token' not in request.connection_data:
                raise ValidationError("Missing public_token for Plaid connection")
        elif request.provider == 'yodlee':
            if 'provider_id' not in request.connection_data or 'credentials' not in request.connection_data:
                raise ValidationError("Missing provider_id or credentials for Yodlee connection")
        
        # Connect account
        from app.services.banking.bank_aggregator import BankingProvider
        provider = BankingProvider.PLAID if request.provider == 'plaid' else BankingProvider.YODLEE
        
        credential_id = await bank_aggregator.connect_bank_account(
            str(current_user.id),
            request.connection_data,
            provider,
            db
        )
        
        # Get account count
        connections = await bank_aggregator.get_user_connections(str(current_user.id), db)
        connected_connection = next((c for c in connections if c.credential_id == credential_id), None)
        accounts_connected = connected_connection.account_count if connected_connection else 0
        
        # Start background sync
        background_tasks.add_task(
            bank_aggregator.sync_all_accounts,
            str(current_user.id),
            db
        )
        
        logger.info(f"Connected bank account for user {current_user.id} via {request.provider}")
        
        return ConnectAccountResponse(
            credential_id=credential_id,
            success=True,
            message="Bank account connected successfully",
            accounts_connected=accounts_connected
        )
        
    except Exception as e:
        logger.error(f"Error connecting bank account: {str(e)}")
        raise HTTPException(
            status_code=400 if isinstance(e, ValidationError) else 500,
            detail=f"Failed to connect bank account: {str(e)}"
        )


@router.get("/accounts", response_model=List[BankAccountInfo])
async def get_bank_accounts(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("READ", "banking_accounts"))
):
    """
    Get all connected bank accounts for the user
    
    Returns a list of all bank accounts connected across all providers
    with current balance information and account details.
    """
    try:
        financial_data = await bank_aggregator.get_comprehensive_financial_data(
            str(current_user.id), db, include_analysis=False
        )
        
        accounts_info = []
        for account in financial_data.accounts:
            account_info = BankAccountInfo(
                account_id=account.account_id,
                name=account.name,
                type=account.type,
                subtype=account.subtype,
                current_balance=account.balance_current,
                available_balance=account.balance_available,
                currency=account.currency,
                mask=account.mask,
                provider=account.provider if hasattr(account, 'provider') else 'unknown'
            )
            accounts_info.append(account_info)
        
        logger.info(f"Retrieved {len(accounts_info)} accounts for user {current_user.id}")
        
        return accounts_info
        
    except Exception as e:
        logger.error(f"Error retrieving bank accounts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve bank accounts: {str(e)}"
        )


@router.get("/transactions")
async def get_transactions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    account_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Field(100, ge=1, le=1000),
    offset: int = Field(0, ge=0),
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("READ", "banking_transactions"))
):
    """
    Get bank transactions with filtering and pagination
    
    Returns bank transactions with optional filtering by date range,
    account, category, and other criteria.
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        financial_data = await bank_aggregator.get_comprehensive_financial_data(
            str(current_user.id), db, include_analysis=False, lookback_days=30
        )
        
        # Filter transactions
        filtered_transactions = []
        for i, transaction in enumerate(financial_data.transactions):
            # Apply filters
            if account_id and transaction.account_id != account_id:
                continue
            
            if start_date and transaction.date < start_date:
                continue
                
            if end_date and transaction.date > end_date:
                continue
            
            if category:
                transaction_category = None
                if i < len(financial_data.categorized_transactions):
                    transaction_category = financial_data.categorized_transactions[i].category
                if transaction_category != category:
                    continue
            
            # Convert to response format
            transaction_info = TransactionInfo(
                transaction_id=transaction.transaction_id,
                account_id=transaction.account_id,
                amount=transaction.amount,
                date=transaction.date,
                name=transaction.name,
                merchant_name=transaction.merchant_name,
                category=financial_data.categorized_transactions[i].category if i < len(financial_data.categorized_transactions) else None,
                subcategory=financial_data.categorized_transactions[i].subcategory if i < len(financial_data.categorized_transactions) else None,
                pending=transaction.pending,
                location=transaction.location
            )
            filtered_transactions.append(transaction_info)
        
        # Apply pagination
        paginated_transactions = filtered_transactions[offset:offset + limit]
        
        logger.info(f"Retrieved {len(paginated_transactions)} transactions for user {current_user.id}")
        
        return {
            "transactions": paginated_transactions,
            "total_count": len(filtered_transactions),
            "has_more": offset + limit < len(filtered_transactions)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving transactions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )


@router.get("/summary", response_model=FinancialSummaryResponse)
async def get_financial_summary(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("READ", "banking_summary"))
):
    """
    Get comprehensive financial summary
    
    Returns a high-level overview of the user's financial situation including
    account balances, cash flow, and financial health metrics.
    """
    try:
        financial_data = await bank_aggregator.get_comprehensive_financial_data(
            str(current_user.id), db, include_analysis=True
        )
        
        # Calculate summary metrics
        total_balance = sum(acc.balance_current or 0 for acc in financial_data.accounts)
        
        # Extract cash flow data
        cash_flow = financial_data.cash_flow_analysis
        monthly_income = 0
        monthly_expenses = 0
        net_cash_flow = 0
        savings_rate = 0
        financial_health_score = 0
        
        if cash_flow and cash_flow.get('period_analysis'):
            latest_period = cash_flow['period_analysis'][-1] if cash_flow['period_analysis'] else {}
            monthly_income = latest_period.get('total_income', 0)
            monthly_expenses = latest_period.get('total_expenses', 0)
            net_cash_flow = latest_period.get('net_cash_flow', 0)
        
        if cash_flow and cash_flow.get('financial_health'):
            health = cash_flow['financial_health']
            savings_rate = health.get('savings_rate', 0)
            financial_health_score = health.get('overall_score', 0)
        
        # Top spending categories
        top_categories = []
        if cash_flow and cash_flow.get('period_analysis'):
            latest_period = cash_flow['period_analysis'][-1] if cash_flow['period_analysis'] else {}
            expenses_by_cat = latest_period.get('expenses_by_category', {})
            sorted_categories = sorted(expenses_by_cat.items(), key=lambda x: x[1], reverse=True)
            top_categories = [{'category': cat, 'amount': amount} for cat, amount in sorted_categories[:5]]
        
        # Recent alerts
        recent_alerts = []
        if financial_data.balance_alerts:
            recent_alerts = financial_data.balance_alerts[:5]  # Top 5 most recent
        
        summary = FinancialSummaryResponse(
            user_id=str(current_user.id),
            generated_at=datetime.utcnow(),
            total_accounts=len(financial_data.accounts),
            total_balance=total_balance,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            net_cash_flow=net_cash_flow,
            savings_rate=savings_rate,
            financial_health_score=financial_health_score,
            top_spending_categories=top_categories,
            recent_alerts=recent_alerts
        )
        
        logger.info(f"Generated financial summary for user {current_user.id}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating financial summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate financial summary: {str(e)}"
        )


@router.post("/analysis/cash-flow")
async def analyze_cash_flow(
    request: CashFlowAnalysisRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("CREATE", "cash_flow_analysis"))
):
    """
    Perform comprehensive cash flow analysis
    
    Analyzes the user's income, expenses, and cash flow patterns
    with trend analysis and financial health scoring.
    """
    try:
        financial_data = await bank_aggregator.get_comprehensive_financial_data(
            str(current_user.id), db, include_analysis=False, lookback_days=request.lookback_days
        )
        
        if not financial_data.transactions:
            raise ValidationError("No transactions found for analysis")
        
        # Perform cash flow analysis
        analysis = await cash_flow_analyzer.analyze_cash_flow(
            financial_data.transactions,
            financial_data.accounts,
            analysis_period=request.analysis_period,
            user_id=str(current_user.id)
        )
        
        logger.info(f"Completed cash flow analysis for user {current_user.id}")
        
        return {
            "success": True,
            "analysis": analysis,
            "transactions_analyzed": len(financial_data.transactions),
            "analysis_period": request.analysis_period
        }
        
    except Exception as e:
        logger.error(f"Error in cash flow analysis: {str(e)}")
        raise HTTPException(
            status_code=400 if isinstance(e, ValidationError) else 500,
            detail=f"Cash flow analysis failed: {str(e)}"
        )


@router.post("/analysis/spending-patterns")
async def analyze_spending_patterns(
    request: SpendingAnalysisRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("CREATE", "spending_analysis"))
):
    """
    Analyze spending patterns and detect anomalies
    
    Performs advanced analysis of spending behavior including
    pattern recognition and anomaly detection for fraud prevention.
    """
    try:
        financial_data = await bank_aggregator.get_comprehensive_financial_data(
            str(current_user.id), db, include_analysis=False, lookback_days=request.lookback_days
        )
        
        if not financial_data.transactions:
            raise ValidationError("No transactions found for analysis")
        
        # Perform spending pattern analysis
        analysis = await spending_pattern_detector.analyze_spending_patterns(
            financial_data.transactions,
            user_id=str(current_user.id),
            lookback_days=request.lookback_days
        )
        
        logger.info(f"Completed spending pattern analysis for user {current_user.id}")
        
        return {
            "success": True,
            "analysis": analysis,
            "transactions_analyzed": len(financial_data.transactions),
            "anomaly_detection_enabled": request.include_anomaly_detection
        }
        
    except Exception as e:
        logger.error(f"Error in spending pattern analysis: {str(e)}")
        raise HTTPException(
            status_code=400 if isinstance(e, ValidationError) else 500,
            detail=f"Spending pattern analysis failed: {str(e)}"
        )


@router.post("/categorization/feedback")
async def submit_categorization_feedback(
    request: CategorizationFeedbackRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("UPDATE", "transaction_category"))
):
    """
    Submit feedback for transaction categorization
    
    Allows users to correct transaction categorization to improve
    the accuracy of the ML-based categorization engine.
    """
    try:
        # Find the transaction (this would need actual transaction lookup)
        # For now, we'll simulate finding the transaction
        transaction = None  # Would get from database
        
        if not transaction:
            raise ValidationError("Transaction not found")
        
        # Submit feedback to categorization engine
        await transaction_categorizer.learn_from_feedback(
            transaction,
            request.correct_category,
            request.correct_subcategory,
            str(current_user.id),
            db
        )
        
        logger.info(f"Received categorization feedback for transaction {request.transaction_id}")
        
        return {
            "success": True,
            "message": "Categorization feedback recorded successfully",
            "transaction_id": request.transaction_id
        }
        
    except Exception as e:
        logger.error(f"Error recording categorization feedback: {str(e)}")
        raise HTTPException(
            status_code=400 if isinstance(e, ValidationError) else 500,
            detail=f"Failed to record feedback: {str(e)}"
        )


@router.post("/alerts/preferences")
async def update_alert_preferences(
    request: AlertPreferencesRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("UPDATE", "alert_preferences"))
):
    """
    Update balance and spending alert preferences
    
    Configures alert thresholds and notification preferences
    for balance monitoring and spending alerts.
    """
    try:
        # Convert to threshold configurations
        from app.services.banking.balance_monitor import BalanceThreshold, AlertType
        
        thresholds = []
        
        if request.enable_low_balance_alerts and request.low_balance_threshold:
            threshold = BalanceThreshold(
                user_id=str(current_user.id),
                account_id="*",  # All accounts
                threshold_type=AlertType.LOW_BALANCE,
                threshold_value=request.low_balance_threshold,
                enabled=True,
                notification_methods=request.notification_methods,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            thresholds.append(threshold)
        
        # Update thresholds
        success = await balance_monitor.update_thresholds(
            str(current_user.id), thresholds, db
        )
        
        if not success:
            raise BankingIntegrationError("Failed to update alert preferences")
        
        logger.info(f"Updated alert preferences for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Alert preferences updated successfully",
            "thresholds_configured": len(thresholds)
        }
        
    except Exception as e:
        logger.error(f"Error updating alert preferences: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update alert preferences: {str(e)}"
        )


@router.post("/sync")
async def sync_all_accounts(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    audit_data: dict = Depends(lambda: audit_log_dependency("UPDATE", "banking_sync"))
):
    """
    Manually trigger synchronization of all bank accounts
    
    Forces a sync of all connected accounts to get the latest
    transactions and balance information.
    """
    try:
        # Start background sync
        background_tasks.add_task(
            bank_aggregator.sync_all_accounts,
            str(current_user.id),
            db
        )
        
        logger.info(f"Started manual sync for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Account synchronization started",
            "sync_initiated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting account sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start account sync: {str(e)}"
        )


@router.delete("/connections/{credential_id}")
async def disconnect_bank_account(
    credential_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    audit_data: dict = Depends(lambda: audit_log_dependency("DELETE", "banking_connection"))
):
    """
    Disconnect a bank account
    
    Removes a banking connection and stops monitoring for the account.
    This action cannot be undone and will require re-authentication.
    """
    try:
        success = await bank_aggregator.disconnect_bank_account(
            str(current_user.id), credential_id, db
        )
        
        if not success:
            raise ValidationError("Failed to disconnect account or account not found")
        
        logger.info(f"Disconnected bank account {credential_id} for user {current_user.id}")
        
        return {
            "success": True,
            "message": "Bank account disconnected successfully",
            "credential_id": credential_id
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting bank account: {str(e)}")
        raise HTTPException(
            status_code=400 if isinstance(e, ValidationError) else 500,
            detail=f"Failed to disconnect bank account: {str(e)}"
        )


# Webhook endpoints
@router.post("/webhooks/plaid")
async def plaid_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Plaid webhook events
    
    Secure endpoint for receiving real-time updates from Plaid
    about account changes, transactions, and other events.
    """
    try:
        result = await banking_webhook_handler.handle_plaid_webhook(request, db)
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling Plaid webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed"
        )


@router.post("/webhooks/yodlee")
async def yodlee_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Yodlee webhook events
    
    Secure endpoint for receiving real-time updates from Yodlee
    about account changes, transactions, and other events.
    """
    try:
        result = await banking_webhook_handler.handle_yodlee_webhook(request, db)
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling Yodlee webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed"
        )