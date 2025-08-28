"""
Database models for the AI Financial Planning System
"""

# Legacy models
from .user import User
from .financial_profile import FinancialProfile
from .goal import Goal
from .investment import Investment
from .simulation_result import SimulationResult
from .market_data import MarketData
from .auth import (
    TokenBlacklist,
    UserSession, 
    LoginAttempt,
    PasswordResetToken,
    TwoFactorAuth,
    SecurityEvent,
    TrustedDevice,
    MFASecret
)

# Enhanced models with comprehensive fields
from .enhanced_models import (
    User as EnhancedUser,
    Portfolio as EnhancedPortfolio,
    Account as EnhancedAccount,
    Transaction as EnhancedTransaction,
    EnhancedMarketData,
    UserActivityLog,
    RegulatoryReport,
)

# Time-series models
from .timeseries import (
    MarketData as MarketDataLegacy,
    PortfolioPerformanceTimeseries,
    SimulationResultTimeseries,
    EconomicIndicatorTimeseries,
    MarketRegimeTimeseries,
    HourlyMarketSummaryView,
    DailyPortfolioSummaryView
)

__all__ = [
    # Legacy models
    "User",
    "FinancialProfile", 
    "Goal",
    "Investment",
    "SimulationResult",
    "MarketData",
    "TokenBlacklist",
    "UserSession",
    "LoginAttempt",
    "PasswordResetToken",
    "TwoFactorAuth",
    "SecurityEvent",
    "TrustedDevice",
    "MFASecret",
    
    # Enhanced models with comprehensive fields
    "EnhancedUser",
    "EnhancedPortfolio", 
    "EnhancedAccount",
    "EnhancedTransaction",
    "EnhancedMarketData",
    "UserActivityLog",
    "RegulatoryReport",
    
    # Time-series models
    "MarketDataLegacy",
    "PortfolioPerformanceTimeseries",
    "SimulationResultTimeseries",
    "EconomicIndicatorTimeseries",
    "MarketRegimeTimeseries",
    "HourlyMarketSummaryView",
    "DailyPortfolioSummaryView"
]