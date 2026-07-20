"""
Advanced Investment Strategies Service

High-risk, high-reward wealth management strategies with comprehensive
risk warnings, educational components, and risk management tools.

WARNING: These strategies involve significant risk of loss and are suitable
only for experienced investors who can afford to lose their investment.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np
import pandas as pd
from dataclasses import dataclass
import math
from abc import ABC, abstractmethod


class RiskLevel(Enum):
    """Risk levels for investment strategies"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate" 
    AGGRESSIVE = "aggressive"
    SPECULATIVE = "speculative"
    EXTREME_RISK = "extreme_risk"


class StrategyType(Enum):
    """Types of investment strategies"""
    OPTIONS_TRADING = "options_trading"
    LEVERAGED_ETF = "leveraged_etf"
    SECTOR_ROTATION = "sector_rotation"
    MOMENTUM_TRADING = "momentum_trading"
    CRYPTOCURRENCY = "cryptocurrency"
    ALTERNATIVES = "alternatives"
    GROWTH_STOCKS = "growth_stocks"
    IPO_TRACKING = "ipo_tracking"
    SMALL_CAP_VALUE = "small_cap_value"
    EMERGING_MARKETS = "emerging_markets"
    THEMATIC_INVESTING = "thematic_investing"


@dataclass
class RiskWarning:
    """Risk warning structure"""
    title: str
    description: str
    risk_level: RiskLevel
    potential_loss: str
    time_horizon: str
    complexity: str
    required_knowledge: List[str]


@dataclass
class StrategyMetrics:
    """Strategy performance and risk metrics"""
    expected_return: float
    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    var_95: float  # Value at Risk at 95% confidence
    kelly_fraction: float
    required_capital: float


@dataclass
class EducationalContent:
    """Educational content for strategies"""
    title: str
    description: str
    prerequisites: List[str]
    key_concepts: List[str]
    resources: List[str]
    quiz_questions: List[Dict[str, Any]]


class AdvancedStrategy(ABC):
    """Abstract base class for advanced investment strategies"""
    
    def __init__(self, name: str, risk_level: RiskLevel):
        self.name = name
        self.risk_level = risk_level
        self.created_at = datetime.utcnow()
    
    @abstractmethod
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        """Calculate strategy performance metrics"""
        pass
    
    @abstractmethod
    def get_risk_warnings(self) -> List[RiskWarning]:
        """Get risk warnings for this strategy"""
        pass
    
    @abstractmethod
    def get_educational_content(self) -> EducationalContent:
        """Get educational content for this strategy"""
        pass


class RiskManagementService:
    """Advanced risk management calculations and tools"""
    
    @staticmethod
    def kelly_criterion(win_probability: float, win_amount: float, loss_amount: float) -> float:
        """
        Calculate Kelly Criterion for optimal position sizing
        
        Args:
            win_probability: Probability of winning trade (0-1)
            win_amount: Average win amount
            loss_amount: Average loss amount
            
        Returns:
            Optimal fraction of capital to risk
        """
        if win_probability <= 0 or win_probability >= 1:
            return 0.0
            
        b = win_amount / loss_amount  # Odds ratio
        q = 1 - win_probability  # Probability of loss
        
        kelly_fraction = (win_probability * b - q) / b
        
        # Cap at 25% for safety (fractional Kelly)
        return min(max(kelly_fraction, 0), 0.25)
    
    @staticmethod
    def value_at_risk(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) at given confidence level
        
        Args:
            returns: Historical returns
            confidence_level: Confidence level (default 95%)
            
        Returns:
            VaR value
        """
        if not returns:
            return 0.0
            
        returns_array = np.array(returns)
        return np.percentile(returns_array, (1 - confidence_level) * 100)
    
    @staticmethod
    def maximum_drawdown(prices: List[float]) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown from price series
        
        Args:
            prices: Historical price data
            
        Returns:
            (max_drawdown, start_index, end_index)
        """
        if len(prices) < 2:
            return 0.0, 0, 0
            
        prices_array = np.array(prices)
        peak = np.maximum.accumulate(prices_array)
        drawdown = (prices_array - peak) / peak
        
        max_dd_idx = np.argmin(drawdown)
        max_dd = drawdown[max_dd_idx]
        
        # Find start of drawdown
        start_idx = 0
        for i in range(max_dd_idx, -1, -1):
            if drawdown[i] == 0:
                start_idx = i
                break
        
        return abs(max_dd), start_idx, max_dd_idx
    
    @staticmethod
    def stress_test_scenarios() -> Dict[str, Dict]:
        """Historical crisis scenarios for stress testing"""
        return {
            "dot_com_crash_2000": {
                "name": "Dot-com Crash (2000-2002)",
                "market_decline": -0.49,  # NASDAQ declined 78%
                "duration_months": 31,
                "sector_impacts": {
                    "technology": -0.78,
                    "telecom": -0.65,
                    "financials": -0.25,
                    "utilities": -0.10
                }
            },
            "financial_crisis_2008": {
                "name": "Financial Crisis (2007-2009)",
                "market_decline": -0.57,  # S&P 500 declined 57%
                "duration_months": 17,
                "sector_impacts": {
                    "financials": -0.83,
                    "real_estate": -0.75,
                    "industrials": -0.60,
                    "energy": -0.55,
                    "consumer_discretionary": -0.55
                }
            },
            "covid_crash_2020": {
                "name": "COVID-19 Crash (2020)",
                "market_decline": -0.34,  # S&P 500 declined 34%
                "duration_months": 2,
                "sector_impacts": {
                    "travel": -0.70,
                    "energy": -0.65,
                    "financials": -0.45,
                    "industrials": -0.40,
                    "technology": -0.15  # Some tech stocks gained
                }
            },
            "inflation_shock_2022": {
                "name": "Inflation Shock (2022)",
                "market_decline": -0.28,  # NASDAQ declined 33%
                "duration_months": 10,
                "sector_impacts": {
                    "growth_stocks": -0.45,
                    "bonds": -0.13,
                    "real_estate": -0.35,
                    "commodities": 0.20  # Commodities gained
                }
            }
        }


class OptionsStrategy(AdvancedStrategy):
    """Options trading strategies"""
    
    def __init__(self):
        super().__init__("Options Trading", RiskLevel.SPECULATIVE)
    
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        """Calculate options strategy metrics"""
        # Example metrics for covered calls
        return StrategyMetrics(
            expected_return=0.12,  # 12% annually
            volatility=0.25,       # 25% volatility
            max_drawdown=0.35,     # 35% max drawdown
            sharpe_ratio=0.8,
            var_95=0.08,           # 8% VaR
            kelly_fraction=0.15,   # 15% position size
            required_capital=10000  # Minimum $10k
        )
    
    def get_risk_warnings(self) -> List[RiskWarning]:
        return [
            RiskWarning(
                title="OPTIONS TRADING - EXTREME RISK WARNING",
                description="Options trading can result in 100% loss of premium paid. Naked options writing can result in unlimited losses exceeding your initial investment.",
                risk_level=RiskLevel.SPECULATIVE,
                potential_loss="Up to 100% of premium (buyers) or UNLIMITED (naked sellers)",
                time_horizon="Short-term (days to months)",
                complexity="Advanced - requires deep understanding of Greeks, volatility, and time decay",
                required_knowledge=[
                    "Options pricing models (Black-Scholes)",
                    "Greeks (Delta, Gamma, Theta, Vega)",
                    "Implied volatility concepts",
                    "Time decay effects",
                    "Assignment and exercise risks",
                    "Margin requirements"
                ]
            )
        ]
    
    def get_educational_content(self) -> EducationalContent:
        return EducationalContent(
            title="Options Trading Fundamentals",
            description="Learn the basics of options trading, including covered calls and protective puts",
            prerequisites=[
                "Understanding of stock trading",
                "Basic knowledge of derivatives",
                "Risk tolerance assessment"
            ],
            key_concepts=[
                "Call and Put options",
                "Strike price and expiration",
                "Intrinsic vs. Extrinsic value",
                "The Greeks (Delta, Gamma, Theta, Vega)",
                "Covered calls strategy",
                "Protective puts strategy",
                "Assignment risk"
            ],
            resources=[
                "CBOE Options Education Center",
                "Options Strategies Quick Guide",
                "Risk Management for Options Traders"
            ],
            quiz_questions=[
                {
                    "question": "What is the maximum loss for a covered call strategy?",
                    "options": ["Premium received", "Strike price", "Unlimited", "Stock purchase price minus premium"],
                    "correct": 3,
                    "explanation": "Maximum loss is the stock purchase price minus the premium received from selling the call."
                }
            ]
        )
    
    def covered_call_analysis(self, stock_price: float, strike_price: float, 
                            premium: float, days_to_expiration: int) -> Dict:
        """Analyze covered call strategy"""
        
        max_profit = (strike_price - stock_price) + premium
        max_loss = stock_price - premium
        breakeven = stock_price - premium
        
        # Calculate annualized return if called away
        if days_to_expiration > 0:
            return_if_called = ((strike_price + premium) / stock_price - 1) * (365 / days_to_expiration)
        else:
            return_if_called = 0
            
        return {
            "strategy": "Covered Call",
            "max_profit": max_profit,
            "max_loss": max_loss,
            "breakeven": breakeven,
            "return_if_called_away": return_if_called,
            "days_to_expiration": days_to_expiration,
            "risk_reward_ratio": max_profit / max_loss if max_loss > 0 else 0
        }
    
    def protective_put_analysis(self, stock_price: float, put_strike: float, 
                              put_premium: float) -> Dict:
        """Analyze protective put strategy"""
        
        max_loss = stock_price - put_strike + put_premium
        breakeven = stock_price + put_premium
        
        return {
            "strategy": "Protective Put",
            "max_loss": max_loss,
            "breakeven": breakeven,
            "insurance_cost": put_premium,
            "protection_level": put_strike,
            "cost_as_percentage": (put_premium / stock_price) * 100
        }


class LeveragedETFStrategy(AdvancedStrategy):
    """Leveraged ETF strategies with decay warnings"""
    
    def __init__(self):
        super().__init__("Leveraged ETF Trading", RiskLevel.EXTREME_RISK)
    
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        return StrategyMetrics(
            expected_return=0.25,   # 25% annually (with high risk)
            volatility=0.50,        # 50% volatility
            max_drawdown=0.70,      # 70% max drawdown possible
            sharpe_ratio=0.5,
            var_95=0.15,           # 15% VaR
            kelly_fraction=0.05,    # 5% position size (very small due to high risk)
            required_capital=5000   # Minimum $5k
        )
    
    def get_risk_warnings(self) -> List[RiskWarning]:
        return [
            RiskWarning(
                title="LEVERAGED ETF - EXTREME VOLATILITY DECAY WARNING",
                description="Leveraged ETFs experience volatility decay over time. Daily rebalancing can cause significant losses even if the underlying index performs well over longer periods.",
                risk_level=RiskLevel.EXTREME_RISK,
                potential_loss="Can lose 80-100% in volatile markets even if underlying rises",
                time_horizon="SHORT-TERM ONLY (days to weeks, NOT buy-and-hold)",
                complexity="Advanced - requires understanding of daily rebalancing effects",
                required_knowledge=[
                    "Volatility decay mechanics",
                    "Daily rebalancing effects",
                    "Correlation breakdown",
                    "Path dependency",
                    "Optimal holding periods"
                ]
            )
        ]
    
    def get_educational_content(self) -> EducationalContent:
        return EducationalContent(
            title="Leveraged ETF Trading Strategy",
            description="Understanding the mechanics and risks of leveraged ETF trading",
            prerequisites=[
                "ETF trading experience",
                "Understanding of leverage",
                "Short-term trading focus"
            ],
            key_concepts=[
                "2x and 3x leverage mechanics",
                "Daily rebalancing effects",
                "Volatility decay",
                "Path dependency",
                "Optimal holding periods",
                "Market timing strategies"
            ],
            resources=[
                "SEC Leveraged ETF Warning",
                "Volatility Decay Analysis",
                "Leveraged ETF Performance Studies"
            ],
            quiz_questions=[
                {
                    "question": "Why do leveraged ETFs lose value over time even in sideways markets?",
                    "options": ["Management fees", "Volatility decay", "Tracking error", "All of the above"],
                    "correct": 3,
                    "explanation": "All factors contribute, but volatility decay is the primary reason due to daily rebalancing."
                }
            ]
        )
    
    def volatility_decay_analysis(self, daily_returns: List[float], 
                                leverage: float = 2.0) -> Dict:
        """Analyze volatility decay for leveraged ETF"""
        
        if not daily_returns:
            return {}
            
        returns_array = np.array(daily_returns)
        
        # Calculate cumulative returns for underlying and leveraged ETF
        underlying_cumulative = np.cumprod(1 + returns_array)
        leveraged_daily_returns = returns_array * leverage
        leveraged_cumulative = np.cumprod(1 + leveraged_daily_returns)
        
        # Calculate expected vs actual leveraged performance
        underlying_total_return = underlying_cumulative[-1] - 1
        expected_leveraged_return = underlying_total_return * leverage
        actual_leveraged_return = leveraged_cumulative[-1] - 1
        
        decay = expected_leveraged_return - actual_leveraged_return
        
        return {
            "underlying_return": underlying_total_return,
            "expected_leveraged_return": expected_leveraged_return,
            "actual_leveraged_return": actual_leveraged_return,
            "volatility_decay": decay,
            "decay_percentage": (decay / abs(expected_leveraged_return)) * 100 if expected_leveraged_return != 0 else 0,
            "daily_volatility": np.std(returns_array),
            "recommended_holding_period": "1-5 days" if np.std(returns_array) > 0.02 else "1-2 weeks"
        }


class SectorRotationStrategy(AdvancedStrategy):
    """Sector rotation based on economic cycles"""
    
    def __init__(self):
        super().__init__("Sector Rotation", RiskLevel.AGGRESSIVE)
    
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        return StrategyMetrics(
            expected_return=0.15,   # 15% annually
            volatility=0.20,        # 20% volatility
            max_drawdown=0.25,      # 25% max drawdown
            sharpe_ratio=0.75,
            var_95=0.06,           # 6% VaR
            kelly_fraction=0.20,    # 20% position size
            required_capital=25000  # $25k minimum for diversification
        )
    
    def get_risk_warnings(self) -> List[RiskWarning]:
        return [
            RiskWarning(
                title="SECTOR ROTATION - TIMING RISK",
                description="Sector rotation requires accurate market cycle timing. Incorrect timing can lead to significant underperformance versus broad market indices.",
                risk_level=RiskLevel.AGGRESSIVE,
                potential_loss="20-40% in bear markets or mistimed rotations",
                time_horizon="Medium-term (3-12 months per rotation)",
                complexity="Advanced - requires macroeconomic analysis",
                required_knowledge=[
                    "Economic cycle phases",
                    "Sector performance patterns",
                    "Macroeconomic indicators",
                    "Interest rate impacts",
                    "Momentum indicators"
                ]
            )
        ]
    
    def get_educational_content(self) -> EducationalContent:
        return EducationalContent(
            title="Sector Rotation Strategy",
            description="Learn to rotate investments across sectors based on economic cycles",
            prerequisites=[
                "Macroeconomic knowledge",
                "Sector ETF familiarity",
                "Technical analysis basics"
            ],
            key_concepts=[
                "Economic cycle phases",
                "Sector leadership patterns",
                "Relative strength analysis",
                "Momentum indicators",
                "Risk-on vs risk-off sentiment"
            ],
            resources=[
                "Economic Cycle Analysis Guide",
                "Sector Performance Studies",
                "Macroeconomic Indicator Dashboard"
            ],
            quiz_questions=[]
        )
    
    def get_cycle_recommendations(self, economic_phase: str) -> Dict:
        """Get sector recommendations based on economic cycle phase"""
        
        recommendations = {
            "early_cycle": {
                "favored_sectors": ["Technology", "Consumer Discretionary", "Industrials"],
                "avoid_sectors": ["Utilities", "Consumer Staples"],
                "reasoning": "Economic growth accelerating, risk appetite increasing"
            },
            "mid_cycle": {
                "favored_sectors": ["Industrials", "Materials", "Energy"],
                "avoid_sectors": ["Bonds", "Defensive sectors"],
                "reasoning": "Full economic expansion, commodity demand strong"
            },
            "late_cycle": {
                "favored_sectors": ["Energy", "Financials", "Real Estate"],
                "avoid_sectors": ["Technology", "Growth stocks"],
                "reasoning": "Inflation concerns, interest rates rising"
            },
            "recession": {
                "favored_sectors": ["Consumer Staples", "Healthcare", "Utilities"],
                "avoid_sectors": ["Consumer Discretionary", "Industrials"],
                "reasoning": "Defensive positioning, focus on necessity goods"
            }
        }
        
        return recommendations.get(economic_phase, {})


class CryptocurrencyStrategy(AdvancedStrategy):
    """Cryptocurrency allocation with volatility warnings"""
    
    def __init__(self):
        super().__init__("Cryptocurrency Investment", RiskLevel.EXTREME_RISK)
    
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        return StrategyMetrics(
            expected_return=0.30,   # 30% annually (highly speculative)
            volatility=0.80,        # 80% volatility
            max_drawdown=0.85,      # 85% max drawdown possible
            sharpe_ratio=0.375,
            var_95=0.25,           # 25% VaR
            kelly_fraction=0.02,    # 2% position size (very small)
            required_capital=1000   # $1k minimum
        )
    
    def get_risk_warnings(self) -> List[RiskWarning]:
        return [
            RiskWarning(
                title="CRYPTOCURRENCY - EXTREME VOLATILITY & REGULATORY RISK",
                description="Cryptocurrencies are highly speculative assets with extreme volatility. Prices can decline 50-90% rapidly. Regulatory changes could impact value significantly.",
                risk_level=RiskLevel.EXTREME_RISK,
                potential_loss="Total loss possible - cryptocurrencies can go to zero",
                time_horizon="Long-term (5+ years) or active trading",
                complexity="Advanced - requires understanding of blockchain technology",
                required_knowledge=[
                    "Blockchain technology basics",
                    "Cryptocurrency types and use cases",
                    "Wallet security",
                    "Exchange risks",
                    "Regulatory landscape",
                    "Market manipulation risks"
                ]
            )
        ]
    
    def get_educational_content(self) -> EducationalContent:
        return EducationalContent(
            title="Cryptocurrency Investment Strategy",
            description="Understanding cryptocurrency investment with proper risk management",
            prerequisites=[
                "High risk tolerance",
                "Technology understanding",
                "Speculative investment experience"
            ],
            key_concepts=[
                "Bitcoin vs. Altcoins",
                "Blockchain fundamentals",
                "DeFi protocols",
                "Staking and yield farming",
                "Security best practices",
                "Tax implications"
            ],
            resources=[
                "Cryptocurrency Security Guide",
                "DeFi Risk Assessment",
                "Tax Reporting for Crypto"
            ],
            quiz_questions=[]
        )
    
    def calculate_allocation_recommendation(self, portfolio_value: float, 
                                         risk_tolerance: str) -> Dict:
        """Calculate recommended crypto allocation"""
        
        allocations = {
            "conservative": 0.01,    # 1%
            "moderate": 0.02,        # 2%
            "aggressive": 0.05,      # 5%
            "speculative": 0.10      # 10%
        }
        
        max_allocation = allocations.get(risk_tolerance, 0.02)
        recommended_amount = portfolio_value * max_allocation
        
        return {
            "recommended_percentage": max_allocation * 100,
            "recommended_amount": recommended_amount,
            "warning": "Never invest more than you can afford to lose completely",
            "diversification_suggestion": {
                "bitcoin": 0.6,      # 60% in Bitcoin
                "ethereum": 0.25,    # 25% in Ethereum  
                "other_alts": 0.15   # 15% in other cryptocurrencies
            }
        }


class GrowthStockStrategy(AdvancedStrategy):
    """Growth stock screening and analysis"""
    
    def __init__(self):
        super().__init__("Growth Stock Screening", RiskLevel.AGGRESSIVE)
    
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        return StrategyMetrics(
            expected_return=0.18,   # 18% annually
            volatility=0.35,        # 35% volatility
            max_drawdown=0.45,      # 45% max drawdown
            sharpe_ratio=0.51,
            var_95=0.12,           # 12% VaR
            kelly_fraction=0.15,    # 15% position size
            required_capital=15000  # $15k minimum
        )
    
    def get_risk_warnings(self) -> List[RiskWarning]:
        return [
            RiskWarning(
                title="GROWTH STOCKS - HIGH VALUATION RISK",
                description="Growth stocks often trade at high valuations and can experience severe corrections during market downturns or when growth expectations are not met.",
                risk_level=RiskLevel.AGGRESSIVE,
                potential_loss="40-70% during market corrections or earnings disappointments",
                time_horizon="Long-term (3-7 years)",
                complexity="Moderate - requires financial analysis skills",
                required_knowledge=[
                    "Financial statement analysis",
                    "Valuation metrics (P/E, PEG, EV/Sales)",
                    "Industry dynamics",
                    "Competitive advantages",
                    "Management assessment"
                ]
            )
        ]
    
    def get_educational_content(self) -> EducationalContent:
        return EducationalContent(
            title="Growth Stock Investment Strategy",
            description="Learn to identify and invest in high-growth companies",
            prerequisites=[
                "Stock analysis basics",
                "Financial statement reading",
                "Industry research skills"
            ],
            key_concepts=[
                "Revenue growth trends",
                "Profit margin expansion",
                "Market opportunity sizing",
                "Competitive moats",
                "Management quality assessment",
                "Valuation methods"
            ],
            resources=[
                "Growth Stock Screening Guide",
                "Financial Analysis Fundamentals",
                "Industry Research Methods"
            ],
            quiz_questions=[]
        )
    
    def growth_stock_screener(self, criteria: Dict = None) -> Dict:
        """Screen for growth stocks based on criteria"""
        
        default_criteria = {
            "revenue_growth_3y": 0.20,      # 20%+ revenue growth
            "earnings_growth_3y": 0.25,     # 25%+ earnings growth
            "roe_min": 0.15,                # 15%+ ROE
            "debt_to_equity_max": 0.5,      # Max 50% debt/equity
            "peg_ratio_max": 2.0,           # PEG < 2.0
            "market_cap_min": 1000000000    # Min $1B market cap
        }
        
        screening_criteria = {**default_criteria, **(criteria or {})}
        
        # This would integrate with actual stock screening APIs
        sample_results = {
            "screening_criteria": screening_criteria,
            "total_matches": 156,
            "top_recommendations": [
                {
                    "symbol": "NVDA",
                    "company": "NVIDIA Corp",
                    "revenue_growth_3y": 0.45,
                    "earnings_growth_3y": 0.78,
                    "roe": 0.32,
                    "peg_ratio": 1.2,
                    "risk_score": "High"
                },
                {
                    "symbol": "AMZN", 
                    "company": "Amazon.com Inc",
                    "revenue_growth_3y": 0.22,
                    "earnings_growth_3y": 0.35,
                    "roe": 0.18,
                    "peg_ratio": 1.8,
                    "risk_score": "Medium-High"
                }
            ],
            "warning": "Past performance does not guarantee future results. Conduct thorough research before investing."
        }
        
        return sample_results


class IPOTrackingStrategy(AdvancedStrategy):
    """IPO investment tracking and analysis"""
    
    def __init__(self):
        super().__init__("IPO Investment Tracking", RiskLevel.SPECULATIVE)
    
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        return StrategyMetrics(
            expected_return=0.35,   # 35% annually (highly variable)
            volatility=0.60,        # 60% volatility
            max_drawdown=0.75,      # 75% max drawdown
            sharpe_ratio=0.58,
            var_95=0.20,           # 20% VaR
            kelly_fraction=0.08,    # 8% position size
            required_capital=5000   # $5k minimum
        )
    
    def get_risk_warnings(self) -> List[RiskWarning]:
        return [
            RiskWarning(
                title="IPO INVESTMENTS - EXTREME VOLATILITY & LIMITED HISTORY",
                description="IPOs lack trading history and can be extremely volatile. Many IPOs trade below their offering price within the first year.",
                risk_level=RiskLevel.SPECULATIVE,
                potential_loss="50-90% losses common in first year",
                time_horizon="Very long-term (5+ years) or short-term trading",
                complexity="Advanced - requires deep company analysis",
                required_knowledge=[
                    "S-1 filing analysis",
                    "IPO pricing mechanics",
                    "Lock-up period effects",
                    "Underwriter quality assessment",
                    "Market timing factors"
                ]
            )
        ]
    
    def get_educational_content(self) -> EducationalContent:
        return EducationalContent(
            title="IPO Investment Strategy",
            description="Understanding IPO investments and associated risks",
            prerequisites=[
                "Advanced stock analysis",
                "High risk tolerance",
                "Patient investment approach"
            ],
            key_concepts=[
                "IPO process and timeline",
                "S-1 prospectus analysis",
                "Valuation methods for new companies",
                "Lock-up periods and insider selling",
                "Market conditions impact"
            ],
            resources=[
                "IPO Analysis Framework",
                "S-1 Filing Guide",
                "IPO Performance Studies"
            ],
            quiz_questions=[]
        )
    
    def ipo_analysis_framework(self, company_data: Dict) -> Dict:
        """Analyze IPO investment opportunity"""
        
        # This would integrate with IPO data feeds
        analysis = {
            "company_fundamentals": {
                "revenue_growth": company_data.get("revenue_growth", 0),
                "profitability": company_data.get("profitable", False),
                "market_size": company_data.get("tam", "Unknown"),
                "competitive_position": company_data.get("moat", "Unknown")
            },
            "ipo_metrics": {
                "valuation_vs_peers": "Premium/Discount analysis needed",
                "underwriter_quality": "Tier 1/2/3 rating needed",
                "insider_ownership": company_data.get("insider_ownership", 0),
                "lockup_expiration": company_data.get("lockup_days", 180)
            },
            "risk_assessment": {
                "market_conditions": "Analyze current IPO market",
                "sector_sentiment": "Check sector performance",
                "company_specific_risks": ["Regulatory", "Competition", "Execution"]
            },
            "recommendation": "Wait for 6-month trading history and quarterly reports before investing"
        }
        
        return analysis


class SmallCapValueStrategy(AdvancedStrategy):
    """Small-cap value investment strategy"""
    
    def __init__(self):
        super().__init__("Small-Cap Value", RiskLevel.AGGRESSIVE)
    
    def calculate_metrics(self, market_data: Dict) -> StrategyMetrics:
        return StrategyMetrics(
            expected_return=0.16,   # 16% annually
            volatility=0.28,        # 28% volatility
            max_drawdown=0.40,      # 40% max drawdown
            sharpe_ratio=0.57,
            var_95=0.10,           # 10% VaR
            kelly_fraction=0.18,    # 18% position size
            required_capital=20000  # $20k for diversification
        )
    
    def get_risk_warnings(self) -> List[RiskWarning]:
        return [
            RiskWarning(
                title="SMALL-CAP VALUE - LIQUIDITY & BUSINESS RISK",
                description="Small-cap stocks have limited liquidity and higher business risk. Economic downturns can severely impact small companies.",
                risk_level=RiskLevel.AGGRESSIVE,
                potential_loss="30-50% in recessions, individual stocks can lose 70%+",
                time_horizon="Long-term (5-10 years)",
                complexity="Advanced - requires extensive research",
                required_knowledge=[
                    "Small company analysis",
                    "Liquidity considerations",
                    "Value investing principles",
                    "Economic cycle impacts",
                    "Diversification requirements"
                ]
            )
        ]
    
    def get_educational_content(self) -> EducationalContent:
        return EducationalContent(
            title="Small-Cap Value Investment",
            description="Investing in undervalued small-cap companies",
            prerequisites=[
                "Value investing knowledge",
                "Small business understanding",
                "Long-term perspective"
            ],
            key_concepts=[
                "Value metrics (P/B, P/E, EV/EBITDA)",
                "Small-cap market dynamics",
                "Liquidity considerations",
                "Management quality assessment",
                "Turnaround situations"
            ],
            resources=[
                "Small-Cap Research Guide",
                "Value Investing Principles",
                "Liquidity Risk Management"
            ],
            quiz_questions=[]
        )


class AdvancedStrategiesService:
    """Main service for advanced investment strategies"""
    
    def __init__(self):
        self.risk_management = RiskManagementService()
        self.strategies = {
            StrategyType.OPTIONS_TRADING: OptionsStrategy(),
            StrategyType.LEVERAGED_ETF: LeveragedETFStrategy(),
            StrategyType.SECTOR_ROTATION: SectorRotationStrategy(),
            StrategyType.CRYPTOCURRENCY: CryptocurrencyStrategy(),
            StrategyType.GROWTH_STOCKS: GrowthStockStrategy(),
            StrategyType.IPO_TRACKING: IPOTrackingStrategy(),
            StrategyType.SMALL_CAP_VALUE: SmallCapValueStrategy(),
        }
        self.user_acknowledgments = {}  # Track risk acknowledgments
    
    def get_risk_disclosure(self) -> Dict:
        """Get comprehensive risk disclosure"""
        return {
            "title": "HIGH-RISK INVESTMENT STRATEGIES - MANDATORY DISCLOSURE",
            "warnings": [
                "These strategies involve substantial risk of loss and are suitable only for experienced investors.",
                "You may lose more than your initial investment in some strategies.",
                "Past performance does not guarantee future results.",
                "High-risk strategies require active management and monitoring.",
                "Consider consulting with a qualified financial advisor.",
                "Only invest money you can afford to lose completely."
            ],
            "acknowledgment_required": True,
            "minimum_experience_required": "2+ years active investing",
            "recommended_portfolio_allocation": "Maximum 10-20% of total portfolio"
        }
    
    def require_risk_acknowledgment(self, user_id: str, strategy_type: StrategyType) -> bool:
        """Check if user has acknowledged risks for strategy"""
        key = f"{user_id}_{strategy_type.value}"
        return self.user_acknowledgments.get(key, False)
    
    def acknowledge_risks(self, user_id: str, strategy_type: StrategyType, 
                         quiz_score: float = 0) -> Dict:
        """Record user risk acknowledgment"""
        
        # Require minimum quiz score for high-risk strategies
        min_score_required = {
            StrategyType.OPTIONS_TRADING: 0.8,
            StrategyType.LEVERAGED_ETF: 0.8,
            StrategyType.CRYPTOCURRENCY: 0.7,
            StrategyType.SECTOR_ROTATION: 0.6
        }
        
        required_score = min_score_required.get(strategy_type, 0.6)
        
        if quiz_score < required_score:
            return {
                "acknowledged": False,
                "reason": f"Minimum quiz score of {required_score*100}% required",
                "current_score": quiz_score * 100,
                "recommendation": "Please review educational materials and retake quiz"
            }
        
        key = f"{user_id}_{strategy_type.value}"
        self.user_acknowledgments[key] = True
        
        return {
            "acknowledged": True,
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": strategy_type.value,
            "quiz_score": quiz_score * 100
        }
    
    def get_strategy_analysis(self, strategy_type: StrategyType, 
                            market_data: Dict = None) -> Dict:
        """Get comprehensive strategy analysis"""
        
        if strategy_type not in self.strategies:
            return {"error": "Strategy not implemented"}
        
        strategy = self.strategies[strategy_type]
        
        return {
            "strategy_name": strategy.name,
            "risk_level": strategy.risk_level.value,
            "metrics": strategy.calculate_metrics(market_data or {}).__dict__,
            "risk_warnings": [warning.__dict__ for warning in strategy.get_risk_warnings()],
            "educational_content": strategy.get_educational_content().__dict__,
            "implementation_date": datetime.utcnow().isoformat()
        }
    
    def portfolio_stress_test(self, portfolio_positions: List[Dict], 
                            scenario: str = "financial_crisis_2008") -> Dict:
        """Perform portfolio stress test using historical scenarios"""
        
        scenarios = self.risk_management.stress_test_scenarios()
        
        if scenario not in scenarios:
            return {"error": "Invalid stress test scenario"}
        
        test_scenario = scenarios[scenario]
        total_portfolio_value = sum(pos.get('value', 0) for pos in portfolio_positions)
        
        stressed_values = []
        for position in portfolio_positions:
            sector = position.get('sector', 'general')
            value = position.get('value', 0)
            
            # Apply sector-specific stress
            sector_impact = test_scenario['sector_impacts'].get(
                sector, test_scenario['market_decline']
            )
            
            stressed_value = value * (1 + sector_impact)
            stressed_values.append({
                'position': position.get('symbol', 'Unknown'),
                'original_value': value,
                'stressed_value': stressed_value,
                'impact': sector_impact * 100
            })
        
        total_stressed_value = sum(pos['stressed_value'] for pos in stressed_values)
        total_loss = total_portfolio_value - total_stressed_value
        loss_percentage = (total_loss / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0
        
        return {
            "scenario": test_scenario['name'],
            "duration_months": test_scenario['duration_months'],
            "portfolio_original_value": total_portfolio_value,
            "portfolio_stressed_value": total_stressed_value,
            "total_loss": total_loss,
            "loss_percentage": loss_percentage,
            "position_impacts": stressed_values,
            "recommendation": self._get_stress_test_recommendation(loss_percentage)
        }
    
    def _get_stress_test_recommendation(self, loss_percentage: float) -> str:
        """Get recommendation based on stress test results"""
        
        if loss_percentage > 50:
            return "CRITICAL: Portfolio too risky. Consider significant reduction in high-risk positions."
        elif loss_percentage > 30:
            return "HIGH RISK: Consider reducing position sizes and increasing diversification."
        elif loss_percentage > 20:
            return "MODERATE RISK: Portfolio within acceptable risk range but monitor closely."
        else:
            return "LOW RISK: Portfolio shows good resilience to stress scenarios."
    
    def calculate_optimal_position_size(self, strategy_type: StrategyType, 
                                      portfolio_value: float,
                                      historical_performance: Dict) -> Dict:
        """Calculate optimal position size using Kelly Criterion and risk metrics"""
        
        if strategy_type not in self.strategies:
            return {"error": "Strategy not implemented"}
        
        strategy = self.strategies[strategy_type]
        metrics = strategy.calculate_metrics({})
        
        # Use Kelly Criterion with performance data
        win_rate = historical_performance.get('win_rate', 0.55)
        avg_win = historical_performance.get('avg_win', 0.15)
        avg_loss = historical_performance.get('avg_loss', 0.08)
        
        kelly_fraction = self.risk_management.kelly_criterion(win_rate, avg_win, avg_loss)
        
        # Apply additional safety factors for high-risk strategies
        safety_factors = {
            RiskLevel.CONSERVATIVE: 1.0,
            RiskLevel.MODERATE: 0.8,
            RiskLevel.AGGRESSIVE: 0.6,
            RiskLevel.SPECULATIVE: 0.4,
            RiskLevel.EXTREME_RISK: 0.2
        }
        
        safety_factor = safety_factors[strategy.risk_level]
        adjusted_kelly = kelly_fraction * safety_factor
        
        # Cap position size based on strategy risk level
        max_positions = {
            RiskLevel.CONSERVATIVE: 0.25,
            RiskLevel.MODERATE: 0.20,
            RiskLevel.AGGRESSIVE: 0.15,
            RiskLevel.SPECULATIVE: 0.10,
            RiskLevel.EXTREME_RISK: 0.05
        }
        
        max_position = max_positions[strategy.risk_level]
        optimal_fraction = min(adjusted_kelly, max_position)
        optimal_amount = portfolio_value * optimal_fraction
        
        return {
            "strategy": strategy_type.value,
            "kelly_fraction": kelly_fraction,
            "safety_adjusted_fraction": adjusted_kelly,
            "optimal_fraction": optimal_fraction,
            "optimal_amount": optimal_amount,
            "max_recommended_fraction": max_position,
            "risk_level": strategy.risk_level.value,
            "rationale": f"Position sized for {strategy.risk_level.value} risk level with safety factor of {safety_factor}"
        }
    
    def get_thematic_investment_opportunities(self) -> Dict:
        """Get current thematic investment opportunities"""
        
        themes = {
            "artificial_intelligence": {
                "description": "AI and machine learning companies",
                "growth_potential": "Very High",
                "risk_level": "High",
                "key_sectors": ["Technology", "Healthcare", "Automotive"],
                "example_etfs": ["ROBO", "BOTZ", "IRBO"],
                "risks": ["Regulatory uncertainty", "Valuation concerns", "Competition"],
                "time_horizon": "5-10 years"
            },
            "clean_energy": {
                "description": "Renewable energy and clean technology",
                "growth_potential": "High",
                "risk_level": "Moderate-High",
                "key_sectors": ["Utilities", "Industrials", "Materials"],
                "example_etfs": ["ICLN", "QCLN", "PBW"],
                "risks": ["Policy changes", "Commodity prices", "Technology shifts"],
                "time_horizon": "3-7 years"
            },
            "biotechnology": {
                "description": "Biotech and pharmaceutical innovation",
                "growth_potential": "Very High",
                "risk_level": "Very High",
                "key_sectors": ["Healthcare", "Biotechnology"],
                "example_etfs": ["IBB", "XBI", "ARKG"],
                "risks": ["FDA approval", "Patent cliffs", "R&D failures"],
                "time_horizon": "5-15 years"
            },
            "cybersecurity": {
                "description": "Cybersecurity and data protection",
                "growth_potential": "High",
                "risk_level": "Moderate",
                "key_sectors": ["Technology", "Software"],
                "example_etfs": ["HACK", "CIBR", "BUG"],
                "risks": ["Competition", "Technology obsolescence"],
                "time_horizon": "3-5 years"
            }
        }
        
        return {
            "themes": themes,
            "recommendation": "Limit thematic investments to 5-10% of portfolio",
            "diversification_note": "Spread across multiple themes to reduce concentration risk"
        }


# Example usage and testing functions
def example_usage():
    """Example usage of the Advanced Strategies Service"""
    
    service = AdvancedStrategiesService()
    
    # Get risk disclosure
    disclosure = service.get_risk_disclosure()
    print("Risk Disclosure:", disclosure)
    
    # Analyze options strategy
    options_analysis = service.get_strategy_analysis(StrategyType.OPTIONS_TRADING)
    print("\nOptions Strategy Analysis:", options_analysis)
    
    # Stress test a sample portfolio
    sample_portfolio = [
        {"symbol": "AAPL", "value": 10000, "sector": "technology"},
        {"symbol": "JPM", "value": 8000, "sector": "financials"},
        {"symbol": "XLE", "value": 5000, "sector": "energy"}
    ]
    
    stress_test = service.portfolio_stress_test(sample_portfolio, "financial_crisis_2008")
    print("\nStress Test Results:", stress_test)


if __name__ == "__main__":
    example_usage()