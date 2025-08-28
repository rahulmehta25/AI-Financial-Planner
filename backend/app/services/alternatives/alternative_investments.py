"""
Alternative Investment Integration Module

Comprehensive implementation for alternative investment strategies including:
- Cryptocurrency portfolio optimization with DeFi opportunities
- Real estate investment analysis (REITs, crowdfunding, tokenized)
- Private equity evaluation (accredited investors)
- Commodities allocation for inflation hedging
- Institutional-grade risk analysis and portfolio impact
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm, t as student_t
import asyncio
import logging
from decimal import Decimal
import hashlib
import json

logger = logging.getLogger(__name__)


class InvestorAccreditation(Enum):
    """Investor accreditation status levels"""
    NON_ACCREDITED = "non_accredited"
    ACCREDITED = "accredited"
    QUALIFIED_PURCHASER = "qualified_purchaser"
    INSTITUTIONAL = "institutional"


class CryptoAsset(Enum):
    """Supported cryptocurrency assets"""
    BTC = "bitcoin"
    ETH = "ethereum"
    SOL = "solana"
    MATIC = "polygon"
    LINK = "chainlink"
    ADA = "cardano"
    DOT = "polkadot"
    AVAX = "avalanche"
    UNI = "uniswap"
    AAVE = "aave"
    # Additional DeFi and Layer 2 tokens
    ARB = "arbitrum"
    OP = "optimism"
    COMP = "compound"
    MKR = "maker"
    CRV = "curve"
    SNX = "synthetix"
    SUSHI = "sushi"
    YFI = "yearn"
    BAL = "balancer"
    LDO = "lido"


class RealEstateType(Enum):
    """Real estate investment types"""
    REIT = "reit"
    CROWDFUNDING = "crowdfunding"
    DIRECT_OWNERSHIP = "direct"
    SYNDICATION = "syndication"
    REAL_ESTATE_FUND = "fund"
    TOKENIZED_REAL_ESTATE = "tokenized"
    FRACTIONAL_OWNERSHIP = "fractional"
    OPPORTUNITY_ZONES = "opportunity_zones"
    PRIVATE_REIT = "private_reit"


class CommodityType(Enum):
    """Commodity investment types"""
    GOLD = "gold"
    SILVER = "silver"
    OIL = "oil"
    NATURAL_GAS = "natural_gas"
    AGRICULTURAL = "agricultural"
    INDUSTRIAL_METALS = "industrial_metals"


@dataclass
class UserProfile:
    """User investment profile"""
    user_id: str
    total_assets: float
    liquid_assets: float
    annual_income: float
    risk_tolerance: float  # 0-1 scale
    investment_horizon_years: int
    accreditation_status: InvestorAccreditation
    crypto_experience: bool = False
    real_estate_experience: bool = False
    private_equity_experience: bool = False
    inflation_concern: float = 0.5  # 0-1 scale
    liquidity_needs: float = 0.3  # percentage of portfolio needed liquid
    geographic_preferences: List[str] = field(default_factory=list)
    crypto_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Portfolio:
    """Current portfolio holdings"""
    total_value: float
    stocks: float
    bonds: float
    cash: float
    alternatives: float = 0.0
    real_estate: float = 0.0
    crypto: float = 0.0
    commodities: float = 0.0
    private_equity: float = 0.0


@dataclass
class CryptoAllocation:
    """Cryptocurrency allocation recommendation"""
    allocations: Dict[str, float]  # symbol -> amount
    total_amount: float
    risk_score: float
    expected_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    defi_opportunities: Optional[List[Dict]] = None
    staking_recommendations: Optional[List[Dict]] = None
    yield_farming_opportunities: Optional[List[Dict]] = None
    liquidity_pools: Optional[List[Dict]] = None
    lending_protocols: Optional[List[Dict]] = None
    derivatives_strategies: Optional[List[Dict]] = None


@dataclass
class RealEstateAllocation:
    """Real estate allocation recommendation"""
    allocations: Dict[str, float]  # type -> amount
    total_amount: float
    expected_yield: float
    geographic_diversification: Dict[str, float]
    recommended_reits: List[Dict]
    crowdfunding_opportunities: List[Dict]


@dataclass
class PrivateEquityAllocation:
    """Private equity allocation recommendation"""
    allocations: Dict[str, float]  # fund -> amount
    total_commitment: float
    expected_irr: float
    lock_up_period_years: int
    capital_call_schedule: List[Dict]
    recommended_funds: List[Dict]


@dataclass
class CommoditiesAllocation:
    """Commodities allocation recommendation"""
    allocations: Dict[str, float]  # commodity -> amount
    total_amount: float
    inflation_hedge_effectiveness: float
    expected_return: float
    recommended_etfs: List[Dict]


@dataclass
class AlternativeAllocationPlan:
    """Complete alternative investment allocation plan"""
    recommendations: Dict[str, Any]
    total_alternative_allocation: float
    impact_analysis: Dict[str, float]
    implementation_strategy: Dict[str, Any]
    risk_metrics: Dict[str, float]
    rebalancing_schedule: List[Dict]


class AlternativeInvestmentManager:
    """
    Manages alternative investment allocation and optimization.
    Provides sophisticated strategies for crypto, real estate, 
    private equity, and commodities.
    """
    
    def __init__(self):
        # Risk parameters for different asset classes
        self.crypto_risk_params = {
            'max_single_asset': 0.4,
            'min_market_cap': 1e9,
            'max_volatility': 1.5,
            'min_liquidity': 1e6
        }
        
        self.real_estate_params = {
            'max_single_property': 0.3,
            'min_yield': 0.04,
            'max_leverage': 0.7
        }
        
        self.pe_params = {
            'min_commitment': 50000,
            'max_allocation': 0.2,
            'min_track_record_years': 5
        }
        
        self.commodity_params = {
            'max_single_commodity': 0.3,
            'inflation_hedge_weight': 0.6
        }
        
        # Market data (would be fetched from market data service in production)
        self._initialize_market_data()
    
    def _initialize_market_data(self):
        """Initialize market data for simulations"""
        # Crypto market data (mock data for demonstration)
        self.crypto_market_data = {
            'BTC': {
                'price': 65000,
                'market_cap': 1.3e12,
                'volume_24h': 30e9,
                'volatility_30d': 0.65,
                'btc_correlation': 1.0,
                'expected_return': 0.25
            },
            'ETH': {
                'price': 3500,
                'market_cap': 420e9,
                'volume_24h': 15e9,
                'volatility_30d': 0.75,
                'btc_correlation': 0.85,
                'expected_return': 0.30
            },
            'SOL': {
                'price': 150,
                'market_cap': 70e9,
                'volume_24h': 2e9,
                'volatility_30d': 0.95,
                'btc_correlation': 0.75,
                'expected_return': 0.40
            },
            'MATIC': {
                'price': 1.2,
                'market_cap': 11e9,
                'volume_24h': 500e6,
                'volatility_30d': 0.85,
                'btc_correlation': 0.70,
                'expected_return': 0.35
            },
            'LINK': {
                'price': 15,
                'market_cap': 9e9,
                'volume_24h': 400e6,
                'volatility_30d': 0.80,
                'btc_correlation': 0.72,
                'expected_return': 0.32
            }
        }
        
        # Real estate market data
        self.real_estate_data = {
            'residential_reits': {
                'avg_yield': 0.045,
                'volatility': 0.15,
                'expected_return': 0.08
            },
            'commercial_reits': {
                'avg_yield': 0.055,
                'volatility': 0.18,
                'expected_return': 0.09
            },
            'industrial_reits': {
                'avg_yield': 0.04,
                'volatility': 0.14,
                'expected_return': 0.085
            }
        }
        
        # Commodity data
        self.commodity_data = {
            'GOLD': {
                'price': 2050,
                'volatility': 0.16,
                'inflation_beta': 0.8,
                'expected_return': 0.05
            },
            'SILVER': {
                'price': 24,
                'volatility': 0.25,
                'inflation_beta': 0.7,
                'expected_return': 0.06
            },
            'OIL': {
                'price': 85,
                'volatility': 0.35,
                'inflation_beta': 0.6,
                'expected_return': 0.07
            }
        }
    
    async def analyze_alternative_allocation(
        self,
        user_profile: UserProfile,
        portfolio: Portfolio,
        risk_tolerance: Optional[float] = None
    ) -> AlternativeAllocationPlan:
        """
        Analyze and recommend alternative investment allocation.
        
        This is the main entry point for alternative investment analysis.
        """
        # Use provided risk tolerance or from user profile
        risk_tolerance = risk_tolerance or user_profile.risk_tolerance
        
        # Verify accreditation status
        is_accredited = await self._verify_accreditation(user_profile)
        
        # Calculate maximum alternative allocation based on profile
        max_alternatives = self._calculate_max_alternatives(
            portfolio.total_value,
            risk_tolerance,
            is_accredited
        )
        
        logger.info(f"Maximum alternative allocation: ${max_alternatives:,.2f}")
        
        recommendations = {}
        
        # Crypto allocation (higher risk tolerance required)
        if risk_tolerance > 0.4 and user_profile.crypto_experience:
            crypto_allocation = await self._optimize_crypto_allocation(
                max_allocation=min(max_alternatives * 0.3, portfolio.total_value * 0.1),
                user_preferences=user_profile.crypto_preferences
            )
            if crypto_allocation.total_amount > 0:
                recommendations['crypto'] = crypto_allocation
                logger.info(f"Crypto allocation: ${crypto_allocation.total_amount:,.2f}")
        
        # Real estate allocation (moderate risk)
        if portfolio.total_value > 50000:
            real_estate_allocation = await self._optimize_real_estate(
                max_allocation=max_alternatives * 0.4,
                geographic_preferences=user_profile.geographic_preferences,
                investment_type=RealEstateType.REIT if portfolio.total_value < 250000 else RealEstateType.CROWDFUNDING
            )
            if real_estate_allocation.total_amount > 0:
                recommendations['real_estate'] = real_estate_allocation
                logger.info(f"Real estate allocation: ${real_estate_allocation.total_amount:,.2f}")
        
        # Private equity (accredited investors only)
        if is_accredited and portfolio.total_value > 500000:
            pe_allocation = await self._evaluate_private_equity(
                max_allocation=min(max_alternatives * 0.2, portfolio.total_value * 0.15),
                minimum_commitment=50000,
                lock_up_tolerance=user_profile.liquidity_needs
            )
            if pe_allocation and pe_allocation.total_commitment > 0:
                recommendations['private_equity'] = pe_allocation
                logger.info(f"Private equity allocation: ${pe_allocation.total_commitment:,.2f}")
        
        # Commodities for inflation hedging
        if user_profile.inflation_concern > 0.5:
            commodities_allocation = await self._optimize_commodities(
                max_allocation=max_alternatives * 0.1,
                inflation_hedge_priority=user_profile.inflation_concern
            )
            if commodities_allocation.total_amount > 0:
                recommendations['commodities'] = commodities_allocation
                logger.info(f"Commodities allocation: ${commodities_allocation.total_amount:,.2f}")
        
        # Calculate portfolio impact
        impact_analysis = await self._analyze_alternative_impact(
            current_portfolio=portfolio,
            proposed_alternatives=recommendations
        )
        
        # Create implementation strategy
        implementation_strategy = self._create_implementation_strategy(
            recommendations,
            user_profile
        )
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(recommendations, portfolio)
        
        # Create rebalancing schedule
        rebalancing_schedule = self._create_rebalancing_schedule(
            recommendations,
            user_profile.investment_horizon_years
        )
        
        total_allocation = sum(
            self._get_allocation_amount(alloc) 
            for alloc in recommendations.values()
        )
        
        return AlternativeAllocationPlan(
            recommendations=recommendations,
            total_alternative_allocation=total_allocation,
            impact_analysis=impact_analysis,
            implementation_strategy=implementation_strategy,
            risk_metrics=risk_metrics,
            rebalancing_schedule=rebalancing_schedule
        )
    
    async def _optimize_crypto_allocation(
        self,
        max_allocation: float,
        user_preferences: Dict
    ) -> CryptoAllocation:
        """
        Optimize cryptocurrency allocation using modern portfolio theory.
        Includes DeFi opportunities and staking recommendations.
        """
        # Filter cryptos based on preferences and risk parameters
        eligible_cryptos = self._filter_eligible_cryptos(user_preferences)
        
        if not eligible_cryptos:
            return CryptoAllocation(
                allocations={},
                total_amount=0,
                risk_score=0,
                expected_return=0,
                volatility=0,
                sharpe_ratio=0,
                max_drawdown=0
            )
        
        # Calculate risk scores for each crypto
        risk_scores = {}
        expected_returns = {}
        volatilities = {}
        
        for symbol in eligible_cryptos:
            data = self.crypto_market_data[symbol]
            risk_scores[symbol] = self._calculate_crypto_risk(
                volatility=data['volatility_30d'],
                market_cap=data['market_cap'],
                volume=data['volume_24h'],
                correlation_to_btc=data['btc_correlation']
            )
            expected_returns[symbol] = data['expected_return']
            volatilities[symbol] = data['volatility_30d']
        
        # Build correlation matrix (simplified - would use historical data in production)
        correlation_matrix = self._build_crypto_correlation_matrix(eligible_cryptos)
        
        # Optimize allocation using mean-variance optimization
        allocation = self._optimize_crypto_portfolio(
            eligible_cryptos,
            expected_returns,
            volatilities,
            correlation_matrix,
            max_allocation,
            risk_scores
        )
        
        # Calculate portfolio metrics
        portfolio_return = sum(
            allocation[symbol] / max_allocation * expected_returns[symbol]
            for symbol in allocation if allocation[symbol] > 0
        )
        
        portfolio_volatility = self._calculate_portfolio_volatility(
            allocation,
            volatilities,
            correlation_matrix,
            max_allocation
        )
        
        portfolio_risk_score = np.mean([
            risk_scores[symbol] for symbol in allocation if allocation[symbol] > 0
        ])
        
        # Identify DeFi opportunities if user is interested
        defi_opportunities = None
        if user_preferences.get('defi_interest', False):
            defi_opportunities = self._identify_defi_opportunities(
                allocation,
                max_allocation * 0.2  # Max 20% in DeFi
            )
        
        # Identify staking opportunities
        staking_recommendations = self._identify_staking_opportunities(allocation)
        
        # Additional advanced strategies
        yield_farming = self._identify_yield_farming_opportunities(allocation, max_allocation * 0.15)
        liquidity_pools = self._identify_liquidity_pool_opportunities(allocation, max_allocation * 0.2)
        lending_protocols = self._identify_lending_opportunities(allocation, max_allocation * 0.25)
        derivatives = self._identify_derivatives_strategies(allocation, max_allocation * 0.1)
        
        # Calculate Sharpe ratio
        risk_free_rate = 0.04
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Estimate maximum drawdown using historical simulation
        max_drawdown = self._estimate_max_drawdown(allocation, volatilities, correlation_matrix)
        
        return CryptoAllocation(
            allocations=allocation,
            total_amount=sum(allocation.values()),
            risk_score=portfolio_risk_score,
            expected_return=portfolio_return,
            volatility=portfolio_volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            defi_opportunities=defi_opportunities,
            staking_recommendations=staking_recommendations,
            yield_farming_opportunities=yield_farming,
            liquidity_pools=liquidity_pools,
            lending_protocols=lending_protocols,
            derivatives_strategies=derivatives
        )
    
    def _filter_eligible_cryptos(self, user_preferences: Dict) -> List[str]:
        """Filter cryptocurrencies based on user preferences and risk parameters"""
        eligible = []
        
        # Always include BTC and ETH for stability
        if self.crypto_market_data['BTC']['market_cap'] >= self.crypto_risk_params['min_market_cap']:
            eligible.append('BTC')
        if self.crypto_market_data['ETH']['market_cap'] >= self.crypto_risk_params['min_market_cap']:
            eligible.append('ETH')
        
        # Add other cryptos based on preferences
        exclude_list = user_preferences.get('exclude', [])
        include_list = user_preferences.get('include', [])
        
        for symbol, data in self.crypto_market_data.items():
            if symbol in exclude_list:
                continue
            if symbol in include_list or (
                data['market_cap'] >= self.crypto_risk_params['min_market_cap'] and
                data['volume_24h'] >= self.crypto_risk_params['min_liquidity'] and
                data['volatility_30d'] <= self.crypto_risk_params['max_volatility']
            ):
                if symbol not in eligible:
                    eligible.append(symbol)
        
        return eligible
    
    def _calculate_crypto_risk(
        self,
        volatility: float,
        market_cap: float,
        volume: float,
        correlation_to_btc: float
    ) -> float:
        """
        Calculate risk score for a cryptocurrency.
        Lower score = lower risk.
        """
        # Normalize metrics
        volatility_score = min(volatility / 1.0, 1.0)  # Cap at 100% volatility
        
        # Market cap score (log scale, higher is better)
        market_cap_score = 1.0 - min(np.log10(market_cap) / 12, 1.0)  # $1T = 12
        
        # Liquidity score (volume/market cap ratio)
        liquidity_ratio = volume / market_cap
        liquidity_score = 1.0 - min(liquidity_ratio / 0.1, 1.0)  # 10% daily volume is excellent
        
        # Correlation score (high correlation to BTC = lower independent risk)
        correlation_score = 1.0 - correlation_to_btc
        
        # Weighted risk score
        risk_score = (
            volatility_score * 0.35 +
            market_cap_score * 0.25 +
            liquidity_score * 0.25 +
            correlation_score * 0.15
        )
        
        return risk_score
    
    def _build_crypto_correlation_matrix(self, symbols: List[str]) -> np.ndarray:
        """Build correlation matrix for crypto assets"""
        n = len(symbols)
        correlation_matrix = np.eye(n)
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i != j:
                    # Use BTC correlation as proxy
                    corr1 = self.crypto_market_data[symbol1]['btc_correlation']
                    corr2 = self.crypto_market_data[symbol2]['btc_correlation']
                    # Estimate correlation between assets
                    correlation_matrix[i, j] = corr1 * corr2 * 0.9  # Slight decorrelation
        
        return correlation_matrix
    
    def _optimize_crypto_portfolio(
        self,
        symbols: List[str],
        expected_returns: Dict[str, float],
        volatilities: Dict[str, float],
        correlation_matrix: np.ndarray,
        max_allocation: float,
        risk_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Optimize crypto portfolio using mean-variance optimization"""
        n = len(symbols)
        
        # Convert to arrays for optimization
        returns = np.array([expected_returns[s] for s in symbols])
        vols = np.array([volatilities[s] for s in symbols])
        
        # Covariance matrix
        cov_matrix = np.outer(vols, vols) * correlation_matrix
        
        # Objective function (maximize Sharpe ratio)
        def objective(weights):
            portfolio_return = np.dot(weights, returns)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            sharpe_ratio = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
            return -sharpe_ratio  # Minimize negative Sharpe
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        ]
        
        # Bounds (0 to max_single_asset percentage)
        bounds = tuple((0, self.crypto_risk_params['max_single_asset']) for _ in range(n))
        
        # Initial guess (equal weight)
        x0 = np.array([1.0/n] * n)
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        # Convert to dollar allocations
        allocations = {}
        if result.success:
            for i, symbol in enumerate(symbols):
                amount = result.x[i] * max_allocation
                if amount > 100:  # Minimum $100 per position
                    allocations[symbol] = round(amount, 2)
        
        return allocations
    
    def _calculate_portfolio_volatility(
        self,
        allocation: Dict[str, float],
        volatilities: Dict[str, float],
        correlation_matrix: np.ndarray,
        total_value: float
    ) -> float:
        """Calculate portfolio volatility"""
        if not allocation or total_value == 0:
            return 0
        
        symbols = list(allocation.keys())
        weights = np.array([allocation[s] / total_value for s in symbols])
        vols = np.array([volatilities[s] for s in symbols])
        
        # Build correlation matrix for allocated assets
        n = len(symbols)
        corr = np.eye(n)
        for i in range(n):
            for j in range(n):
                if i != j:
                    corr[i, j] = self.crypto_market_data[symbols[i]]['btc_correlation'] * \
                                self.crypto_market_data[symbols[j]]['btc_correlation'] * 0.9
        
        cov_matrix = np.outer(vols, vols) * corr
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        
        return np.sqrt(portfolio_variance)
    
    def _identify_defi_opportunities(
        self,
        crypto_allocation: Dict[str, float],
        max_defi_allocation: float
    ) -> List[Dict]:
        """Identify comprehensive DeFi opportunities for yield generation"""
        opportunities = []
        
        # Tier 1: Low-risk lending protocols
        if max_defi_allocation > 1000:
            opportunities.extend([
                {
                    'protocol': 'Aave V3',
                    'type': 'lending',
                    'asset': 'USDC',
                    'apy': 0.052,
                    'risk_level': 'low',
                    'recommended_amount': min(max_defi_allocation * 0.25, 25000),
                    'insurance_available': True,
                    'audit_score': 9.5,
                    'tvl': 5.2e9
                },
                {
                    'protocol': 'Compound V3',
                    'type': 'lending',
                    'asset': 'USDT',
                    'apy': 0.048,
                    'risk_level': 'low',
                    'recommended_amount': min(max_defi_allocation * 0.2, 20000),
                    'insurance_available': True,
                    'audit_score': 9.3,
                    'tvl': 3.8e9
                }
            ])
        
        # Tier 2: Liquid staking derivatives
        if 'ETH' in crypto_allocation and crypto_allocation['ETH'] > 1000:
            opportunities.extend([
                {
                    'protocol': 'Lido',
                    'type': 'liquid_staking',
                    'asset': 'ETH',
                    'apy': 0.041,
                    'risk_level': 'low',
                    'recommended_amount': crypto_allocation['ETH'] * 0.6,
                    'derivative_token': 'stETH',
                    'additional_yield_options': ['Curve', 'Yearn'],
                    'audit_score': 9.7,
                    'tvl': 32e9
                },
                {
                    'protocol': 'Rocket Pool',
                    'type': 'liquid_staking',
                    'asset': 'ETH',
                    'apy': 0.039,
                    'risk_level': 'low-medium',
                    'recommended_amount': crypto_allocation['ETH'] * 0.3,
                    'derivative_token': 'rETH',
                    'decentralized': True,
                    'audit_score': 9.2,
                    'tvl': 1.8e9
                }
            ])
        
        # Tier 3: Concentrated liquidity provision
        if max_defi_allocation > 5000:
            opportunities.extend([
                {
                    'protocol': 'Uniswap V3',
                    'type': 'concentrated_liquidity',
                    'pair': 'ETH/USDC',
                    'estimated_apy': 0.18,
                    'risk_level': 'medium',
                    'recommended_amount': min(max_defi_allocation * 0.15, 30000),
                    'range_strategy': 'narrow',
                    'impermanent_loss_risk': 'moderate-high',
                    'rebalancing_frequency': 'weekly',
                    'gas_optimization': 'L2 recommended',
                    'audit_score': 9.8,
                    'tvl': 4.2e9
                },
                {
                    'protocol': 'Curve',
                    'type': 'stable_liquidity',
                    'pool': '3pool',
                    'estimated_apy': 0.08,
                    'risk_level': 'low-medium',
                    'recommended_amount': min(max_defi_allocation * 0.2, 40000),
                    'impermanent_loss_risk': 'low',
                    'gauge_rewards': True,
                    'audit_score': 9.6,
                    'tvl': 3.5e9
                }
            ])
        
        # Tier 4: Advanced yield strategies
        if max_defi_allocation > 10000:
            opportunities.extend([
                {
                    'protocol': 'Yearn Finance',
                    'type': 'yield_aggregator',
                    'vault': 'ETH Vault',
                    'estimated_apy': 0.095,
                    'risk_level': 'medium',
                    'recommended_amount': min(max_defi_allocation * 0.1, 25000),
                    'strategy_complexity': 'high',
                    'auto_compounding': True,
                    'audit_score': 9.1,
                    'tvl': 450e6
                },
                {
                    'protocol': 'Convex Finance',
                    'type': 'yield_booster',
                    'underlying': 'Curve LP',
                    'boosted_apy': 0.14,
                    'risk_level': 'medium',
                    'recommended_amount': min(max_defi_allocation * 0.1, 20000),
                    'lock_period': 'none',
                    'audit_score': 8.9,
                    'tvl': 3.1e9
                }
            ])
        
        # Tier 5: Options and derivatives
        if max_defi_allocation > 25000:
            opportunities.extend([
                {
                    'protocol': 'Ribbon Finance',
                    'type': 'options_vault',
                    'strategy': 'covered_call',
                    'asset': 'ETH',
                    'estimated_apy': 0.22,
                    'risk_level': 'medium-high',
                    'recommended_amount': min(max_defi_allocation * 0.05, 15000),
                    'weekly_expiry': True,
                    'principal_protection': False,
                    'audit_score': 8.7,
                    'tvl': 250e6
                },
                {
                    'protocol': 'GMX',
                    'type': 'perpetuals_liquidity',
                    'asset': 'GLP',
                    'estimated_apy': 0.28,
                    'risk_level': 'high',
                    'recommended_amount': min(max_defi_allocation * 0.05, 10000),
                    'exposure': 'multi-asset',
                    'audit_score': 8.5,
                    'tvl': 650e6
                }
            ])
        
        # Add risk scoring and filtering
        for opp in opportunities:
            opp['risk_score'] = self._calculate_defi_risk_score(opp)
            opp['gas_estimate_monthly'] = self._estimate_gas_costs(opp)
            opp['net_apy'] = opp.get('apy', opp.get('estimated_apy', 0)) - opp['gas_estimate_monthly']
        
        # Sort by risk-adjusted returns
        opportunities.sort(key=lambda x: x['net_apy'] / (1 + x['risk_score']), reverse=True)
        
        return opportunities[:10]  # Return top 10 opportunities
    
    def _identify_staking_opportunities(self, allocation: Dict[str, float]) -> List[Dict]:
        """Identify comprehensive staking opportunities for allocated cryptocurrencies"""
        opportunities = []
        
        # Enhanced staking data with multiple providers
        staking_data = {
            'ETH': [
                {
                    'provider': 'Lido',
                    'apy': 0.041,
                    'min_amount': 0,
                    'lock_period': 'liquid',
                    'derivative': 'stETH',
                    'fee': 0.10,
                    'insurance': True
                },
                {
                    'provider': 'Rocket Pool',
                    'apy': 0.039,
                    'min_amount': 0.01,
                    'lock_period': 'liquid',
                    'derivative': 'rETH',
                    'fee': 0.15,
                    'decentralized': True
                },
                {
                    'provider': 'Coinbase',
                    'apy': 0.035,
                    'min_amount': 0,
                    'lock_period': 'liquid',
                    'derivative': 'cbETH',
                    'fee': 0.25,
                    'regulated': True
                }
            ],
            'SOL': [
                {
                    'provider': 'Marinade',
                    'apy': 0.068,
                    'min_amount': 0,
                    'lock_period': 'liquid',
                    'derivative': 'mSOL',
                    'fee': 0.06,
                    'auto_compound': True
                },
                {
                    'provider': 'Native',
                    'apy': 0.072,
                    'min_amount': 1,
                    'lock_period': '2-3 days',
                    'derivative': None,
                    'fee': 0,
                    'validator_selection': True
                }
            ],
            'MATIC': [
                {
                    'provider': 'Lido',
                    'apy': 0.049,
                    'min_amount': 0,
                    'lock_period': 'liquid',
                    'derivative': 'stMATIC',
                    'fee': 0.10,
                    'chain': 'Ethereum'
                },
                {
                    'provider': 'Native',
                    'apy': 0.052,
                    'min_amount': 1,
                    'lock_period': '3-4 days',
                    'derivative': None,
                    'fee': 0,
                    'chain': 'Polygon'
                }
            ],
            'DOT': [
                {
                    'provider': 'Native',
                    'apy': 0.14,
                    'min_amount': 120,
                    'lock_period': '28 days',
                    'derivative': None,
                    'fee': 0,
                    'nomination_pools': True
                },
                {
                    'provider': 'Parallel Finance',
                    'apy': 0.125,
                    'min_amount': 1,
                    'lock_period': 'liquid',
                    'derivative': 'sDOT',
                    'fee': 0.10,
                    'defi_composable': True
                }
            ],
            'ADA': [
                {
                    'provider': 'Native',
                    'apy': 0.045,
                    'min_amount': 10,
                    'lock_period': 'flexible',
                    'derivative': None,
                    'fee': 0.02,
                    'delegation': True
                }
            ],
            'AVAX': [
                {
                    'provider': 'Native',
                    'apy': 0.089,
                    'min_amount': 25,
                    'lock_period': '14 days',
                    'derivative': None,
                    'fee': 0.02,
                    'validator_required': True
                },
                {
                    'provider': 'Benqi',
                    'apy': 0.078,
                    'min_amount': 0,
                    'lock_period': 'liquid',
                    'derivative': 'sAVAX',
                    'fee': 0.10,
                    'defi_integration': True
                }
            ]
        }
        
        for symbol, amount in allocation.items():
            if symbol in staking_data:
                providers = staking_data[symbol]
                
                for provider_data in providers:
                    # Calculate net returns after fees
                    gross_apy = provider_data['apy']
                    fee = provider_data.get('fee', 0)
                    net_apy = gross_apy * (1 - fee)
                    
                    # Check minimum requirements
                    min_amount = provider_data['min_amount']
                    if amount < min_amount:
                        continue
                    
                    opportunity = {
                        'asset': symbol,
                        'provider': provider_data['provider'],
                        'amount': amount,
                        'gross_apy': gross_apy,
                        'fee': fee,
                        'net_apy': net_apy,
                        'annual_income': amount * net_apy,
                        'min_amount': min_amount,
                        'lock_period': provider_data['lock_period'],
                        'liquid': provider_data['lock_period'] in ['liquid', 'flexible'],
                        'derivative_token': provider_data.get('derivative'),
                        'recommended_percentage': 0.8 if provider_data.get('derivative') else 0.6,
                        'risk_factors': self._assess_staking_risks(provider_data),
                        'additional_features': self._get_staking_features(provider_data)
                    }
                    
                    # Calculate risk-adjusted score
                    opportunity['risk_adjusted_apy'] = self._calculate_risk_adjusted_staking_return(
                        net_apy,
                        opportunity['risk_factors']
                    )
                    
                    opportunities.append(opportunity)
        
        # Sort by risk-adjusted returns
        opportunities.sort(key=lambda x: x['risk_adjusted_apy'], reverse=True)
        
        # Group by asset and select best option per asset
        best_by_asset = {}
        for opp in opportunities:
            asset = opp['asset']
            if asset not in best_by_asset or opp['risk_adjusted_apy'] > best_by_asset[asset]['risk_adjusted_apy']:
                best_by_asset[asset] = opp
        
        return list(best_by_asset.values())
    
    async def _optimize_real_estate(
        self,
        max_allocation: float,
        geographic_preferences: List[str],
        investment_type: RealEstateType
    ) -> RealEstateAllocation:
        """
        Optimize real estate allocation across REITs, crowdfunding, and direct investment.
        """
        allocations = {}
        recommended_reits = []
        crowdfunding_opportunities = []
        
        # REIT allocation
        if investment_type in [RealEstateType.REIT, RealEstateType.REAL_ESTATE_FUND]:
            reit_allocation = self._optimize_reit_allocation(
                max_allocation * 0.6,
                geographic_preferences
            )
            allocations.update(reit_allocation['allocations'])
            recommended_reits = reit_allocation['recommendations']
        
        # Crowdfunding opportunities
        if investment_type == RealEstateType.CROWDFUNDING and max_allocation > 10000:
            crowdfunding = self._identify_crowdfunding_opportunities(
                max_allocation * 0.4,
                geographic_preferences
            )
            crowdfunding_opportunities = crowdfunding
            for opp in crowdfunding:
                allocations[f"crowdfunding_{opp['id']}"] = opp['min_investment']
        
        # Calculate geographic diversification
        geographic_div = self._calculate_geographic_diversification(
            allocations,
            recommended_reits,
            crowdfunding_opportunities
        )
        
        # Calculate expected yield
        expected_yield = self._calculate_real_estate_yield(
            allocations,
            recommended_reits,
            crowdfunding_opportunities
        )
        
        total_amount = sum(allocations.values())
        
        return RealEstateAllocation(
            allocations=allocations,
            total_amount=total_amount,
            expected_yield=expected_yield,
            geographic_diversification=geographic_div,
            recommended_reits=recommended_reits,
            crowdfunding_opportunities=crowdfunding_opportunities
        )
    
    def _optimize_reit_allocation(
        self,
        max_allocation: float,
        geographic_preferences: List[str]
    ) -> Dict:
        """Optimize REIT allocation across sectors and geographies"""
        # Sample REIT recommendations
        reits = [
            {
                'symbol': 'VNQ',
                'name': 'Vanguard Real Estate ETF',
                'type': 'diversified',
                'yield': 0.032,
                'expense_ratio': 0.0012,
                'geography': 'US',
                'market_cap': 80e9
            },
            {
                'symbol': 'O',
                'name': 'Realty Income',
                'type': 'retail',
                'yield': 0.045,
                'expense_ratio': 0,
                'geography': 'US',
                'market_cap': 45e9
            },
            {
                'symbol': 'PLD',
                'name': 'Prologis',
                'type': 'industrial',
                'yield': 0.028,
                'expense_ratio': 0,
                'geography': 'Global',
                'market_cap': 120e9
            },
            {
                'symbol': 'AMT',
                'name': 'American Tower',
                'type': 'infrastructure',
                'yield': 0.03,
                'expense_ratio': 0,
                'geography': 'Global',
                'market_cap': 100e9
            },
            {
                'symbol': 'SPG',
                'name': 'Simon Property Group',
                'type': 'retail',
                'yield': 0.055,
                'expense_ratio': 0,
                'geography': 'US',
                'market_cap': 50e9
            }
        ]
        
        # Filter based on preferences
        if geographic_preferences:
            reits = [r for r in reits if r['geography'] in geographic_preferences or r['geography'] == 'Global']
        
        # Optimize allocation (simplified - equal weight to top yielding)
        sorted_reits = sorted(reits, key=lambda x: x['yield'], reverse=True)[:3]
        
        allocations = {}
        per_reit = max_allocation / len(sorted_reits)
        
        for reit in sorted_reits:
            allocations[reit['symbol']] = round(per_reit, 2)
        
        return {
            'allocations': allocations,
            'recommendations': sorted_reits
        }
    
    def _identify_crowdfunding_opportunities(
        self,
        max_allocation: float,
        geographic_preferences: List[str]
    ) -> List[Dict]:
        """Identify real estate crowdfunding opportunities"""
        opportunities = [
            {
                'id': 'cf_001',
                'platform': 'Fundrise',
                'property_type': 'Mixed Portfolio',
                'location': 'US Diversified',
                'target_return': 0.089,
                'min_investment': 500,
                'term_years': 5,
                'risk_level': 'moderate'
            },
            {
                'id': 'cf_002',
                'platform': 'RealtyMogul',
                'property_type': 'Commercial Office',
                'location': 'Major US Cities',
                'target_return': 0.105,
                'min_investment': 5000,
                'term_years': 7,
                'risk_level': 'moderate-high'
            },
            {
                'id': 'cf_003',
                'platform': 'YieldStreet',
                'property_type': 'Multifamily Residential',
                'location': 'Southeast US',
                'target_return': 0.095,
                'min_investment': 1000,
                'term_years': 3,
                'risk_level': 'moderate'
            }
        ]
        
        # Filter based on allocation size
        viable_opportunities = [
            opp for opp in opportunities 
            if opp['min_investment'] <= max_allocation * 0.5
        ]
        
        return viable_opportunities[:2]  # Return top 2 opportunities
    
    def _calculate_geographic_diversification(
        self,
        allocations: Dict,
        reits: List[Dict],
        crowdfunding: List[Dict]
    ) -> Dict[str, float]:
        """Calculate geographic diversification of real estate investments"""
        geographic_allocation = {
            'US': 0,
            'International': 0,
            'Global': 0
        }
        
        total = sum(allocations.values())
        if total == 0:
            return geographic_allocation
        
        for reit in reits:
            if reit['symbol'] in allocations:
                amount = allocations[reit['symbol']]
                if reit['geography'] == 'Global':
                    geographic_allocation['Global'] += amount
                elif reit['geography'] == 'US':
                    geographic_allocation['US'] += amount
                else:
                    geographic_allocation['International'] += amount
        
        # Normalize to percentages
        for key in geographic_allocation:
            geographic_allocation[key] = geographic_allocation[key] / total if total > 0 else 0
        
        return geographic_allocation
    
    def _calculate_real_estate_yield(
        self,
        allocations: Dict,
        reits: List[Dict],
        crowdfunding: List[Dict]
    ) -> float:
        """Calculate weighted average yield for real estate allocation"""
        total_yield = 0
        total_allocation = sum(allocations.values())
        
        if total_allocation == 0:
            return 0
        
        for reit in reits:
            if reit['symbol'] in allocations:
                weight = allocations[reit['symbol']] / total_allocation
                total_yield += reit['yield'] * weight
        
        for cf in crowdfunding:
            cf_key = f"crowdfunding_{cf['id']}"
            if cf_key in allocations:
                weight = allocations[cf_key] / total_allocation
                total_yield += cf['target_return'] * weight
        
        return total_yield
    
    async def _evaluate_private_equity(
        self,
        max_allocation: float,
        minimum_commitment: float,
        lock_up_tolerance: float
    ) -> Optional[PrivateEquityAllocation]:
        """
        Evaluate private equity opportunities for accredited investors.
        """
        if max_allocation < minimum_commitment:
            return None
        
        # Sample PE funds (in production, would fetch from database)
        pe_funds = [
            {
                'name': 'Growth Equity Fund III',
                'strategy': 'Growth Equity',
                'target_irr': 0.18,
                'minimum': 100000,
                'lock_up_years': 7,
                'management_fee': 0.02,
                'carried_interest': 0.20,
                'track_record_years': 15
            },
            {
                'name': 'Technology Ventures Fund',
                'strategy': 'Venture Capital',
                'target_irr': 0.25,
                'minimum': 50000,
                'lock_up_years': 10,
                'management_fee': 0.025,
                'carried_interest': 0.20,
                'track_record_years': 10
            },
            {
                'name': 'Real Estate Opportunity Fund',
                'strategy': 'Real Estate',
                'target_irr': 0.15,
                'minimum': 50000,
                'lock_up_years': 5,
                'management_fee': 0.015,
                'carried_interest': 0.15,
                'track_record_years': 20
            }
        ]
        
        # Filter funds based on minimum commitment and lock-up tolerance
        max_lock_up = 10 * (1 - lock_up_tolerance)  # Higher liquidity need = shorter lock-up
        
        eligible_funds = [
            fund for fund in pe_funds
            if fund['minimum'] <= max_allocation and
            fund['lock_up_years'] <= max_lock_up and
            fund['track_record_years'] >= self.pe_params['min_track_record_years']
        ]
        
        if not eligible_funds:
            return None
        
        # Select best fund based on risk-adjusted returns
        best_fund = max(eligible_funds, key=lambda x: x['target_irr'] / x['lock_up_years'])
        
        # Create capital call schedule
        capital_call_schedule = self._create_capital_call_schedule(
            best_fund['minimum'],
            best_fund['lock_up_years']
        )
        
        return PrivateEquityAllocation(
            allocations={best_fund['name']: best_fund['minimum']},
            total_commitment=best_fund['minimum'],
            expected_irr=best_fund['target_irr'],
            lock_up_period_years=best_fund['lock_up_years'],
            capital_call_schedule=capital_call_schedule,
            recommended_funds=[best_fund]
        )
    
    def _create_capital_call_schedule(
        self,
        total_commitment: float,
        years: int
    ) -> List[Dict]:
        """Create capital call schedule for PE investment"""
        schedule = []
        
        # Typical PE capital call schedule
        call_percentages = [0.25, 0.25, 0.25, 0.15, 0.10]  # Front-loaded
        
        for i, pct in enumerate(call_percentages[:min(years, 5)]):
            schedule.append({
                'year': i + 1,
                'quarter': 'Q1',
                'amount': total_commitment * pct,
                'cumulative': sum(call_percentages[:i+1]) * total_commitment
            })
        
        return schedule
    
    async def _optimize_commodities(
        self,
        max_allocation: float,
        inflation_hedge_priority: float
    ) -> CommoditiesAllocation:
        """
        Optimize commodity allocation for inflation hedging.
        """
        # Commodity ETFs and their characteristics
        commodity_etfs = [
            {
                'symbol': 'GLD',
                'name': 'SPDR Gold Shares',
                'commodity': 'GOLD',
                'expense_ratio': 0.004,
                'inflation_beta': 0.8,
                'volatility': 0.16,
                'expected_return': 0.05
            },
            {
                'symbol': 'SLV',
                'name': 'iShares Silver Trust',
                'commodity': 'SILVER',
                'expense_ratio': 0.005,
                'inflation_beta': 0.7,
                'volatility': 0.25,
                'expected_return': 0.06
            },
            {
                'symbol': 'USO',
                'name': 'United States Oil Fund',
                'commodity': 'OIL',
                'expense_ratio': 0.0079,
                'inflation_beta': 0.6,
                'volatility': 0.35,
                'expected_return': 0.07
            },
            {
                'symbol': 'DBA',
                'name': 'Invesco DB Agriculture Fund',
                'commodity': 'AGRICULTURAL',
                'expense_ratio': 0.0085,
                'inflation_beta': 0.5,
                'volatility': 0.20,
                'expected_return': 0.045
            }
        ]
        
        # Weight by inflation hedge effectiveness
        total_beta = sum(etf['inflation_beta'] for etf in commodity_etfs)
        
        allocations = {}
        for etf in commodity_etfs:
            # Allocate proportionally to inflation beta, adjusted by priority
            weight = (etf['inflation_beta'] / total_beta) * inflation_hedge_priority
            allocation = max_allocation * weight
            
            # Apply minimum position size
            if allocation > 500:
                allocations[etf['symbol']] = round(allocation, 2)
        
        # Calculate portfolio metrics
        total_amount = sum(allocations.values())
        
        if total_amount > 0:
            inflation_effectiveness = sum(
                allocations.get(etf['symbol'], 0) / total_amount * etf['inflation_beta']
                for etf in commodity_etfs
            )
            
            expected_return = sum(
                allocations.get(etf['symbol'], 0) / total_amount * etf['expected_return']
                for etf in commodity_etfs
            )
        else:
            inflation_effectiveness = 0
            expected_return = 0
        
        return CommoditiesAllocation(
            allocations=allocations,
            total_amount=total_amount,
            inflation_hedge_effectiveness=inflation_effectiveness,
            expected_return=expected_return,
            recommended_etfs=[etf for etf in commodity_etfs if etf['symbol'] in allocations]
        )
    
    async def _verify_accreditation(self, user_profile: UserProfile) -> bool:
        """Verify if user meets accredited investor requirements"""
        # SEC accredited investor criteria
        income_threshold = 200000  # $200k individual or $300k joint
        net_worth_threshold = 1000000  # $1M excluding primary residence
        
        meets_income = user_profile.annual_income >= income_threshold
        meets_net_worth = user_profile.total_assets >= net_worth_threshold
        
        is_accredited = (
            user_profile.accreditation_status in [
                InvestorAccreditation.ACCREDITED,
                InvestorAccreditation.QUALIFIED_PURCHASER,
                InvestorAccreditation.INSTITUTIONAL
            ] or
            meets_income or
            meets_net_worth
        )
        
        return is_accredited
    
    def _calculate_max_alternatives(
        self,
        portfolio_value: float,
        risk_tolerance: float,
        is_accredited: bool
    ) -> float:
        """Calculate maximum allocation to alternatives based on profile"""
        # Base allocation percentage
        base_allocation = 0.05  # 5% minimum
        
        # Risk adjustment (0-20% additional based on risk tolerance)
        risk_adjustment = risk_tolerance * 0.20
        
        # Accreditation adjustment
        accreditation_bonus = 0.10 if is_accredited else 0
        
        # Portfolio size adjustment
        if portfolio_value > 1000000:
            size_bonus = 0.10
        elif portfolio_value > 500000:
            size_bonus = 0.05
        else:
            size_bonus = 0
        
        max_percentage = min(
            base_allocation + risk_adjustment + accreditation_bonus + size_bonus,
            0.40  # Cap at 40% of portfolio
        )
        
        return portfolio_value * max_percentage
    
    async def _analyze_alternative_impact(
        self,
        current_portfolio: Portfolio,
        proposed_alternatives: Dict
    ) -> Dict[str, float]:
        """Analyze impact of alternative investments on portfolio"""
        total_alternatives = sum(
            self._get_allocation_amount(alloc)
            for alloc in proposed_alternatives.values()
        )
        
        new_total = current_portfolio.total_value + total_alternatives
        
        # Calculate new allocations
        impact = {
            'total_portfolio_value': new_total,
            'alternatives_percentage': total_alternatives / new_total if new_total > 0 else 0,
            'traditional_percentage': current_portfolio.total_value / new_total if new_total > 0 else 0,
            'expected_return_improvement': self._calculate_return_improvement(proposed_alternatives),
            'risk_increase': self._calculate_risk_increase(proposed_alternatives),
            'diversification_benefit': self._calculate_diversification_benefit(proposed_alternatives)
        }
        
        return impact
    
    def _get_allocation_amount(self, allocation: Any) -> float:
        """Extract allocation amount from different allocation types"""
        if hasattr(allocation, 'total_amount'):
            return allocation.total_amount
        elif hasattr(allocation, 'total_commitment'):
            return allocation.total_commitment
        elif isinstance(allocation, dict):
            return allocation.get('amount', 0)
        return 0
    
    def _calculate_return_improvement(self, alternatives: Dict) -> float:
        """Calculate expected return improvement from alternatives"""
        improvement = 0
        
        for key, allocation in alternatives.items():
            if hasattr(allocation, 'expected_return'):
                # Weight by allocation size
                improvement += allocation.expected_return * 0.2  # Conservative estimate
        
        return improvement / len(alternatives) if alternatives else 0
    
    def _calculate_risk_increase(self, alternatives: Dict) -> float:
        """Calculate risk increase from adding alternatives"""
        risk_scores = []
        
        for key, allocation in alternatives.items():
            if key == 'crypto' and hasattr(allocation, 'volatility'):
                risk_scores.append(allocation.volatility)
            elif key == 'commodities':
                risk_scores.append(0.20)  # Moderate volatility
            elif key == 'real_estate':
                risk_scores.append(0.15)  # Lower volatility
            elif key == 'private_equity':
                risk_scores.append(0.25)  # Higher risk due to illiquidity
        
        return np.mean(risk_scores) if risk_scores else 0
    
    def _calculate_diversification_benefit(self, alternatives: Dict) -> float:
        """Calculate diversification benefit score (0-1)"""
        # More asset classes = better diversification
        num_classes = len(alternatives)
        
        # Maximum benefit at 4 alternative asset classes
        diversification_score = min(num_classes / 4, 1.0)
        
        # Adjust for correlation (alternatives typically have low correlation to traditional assets)
        correlation_benefit = 0.3  # Assume 30% reduction in portfolio volatility
        
        return diversification_score * (1 + correlation_benefit)
    
    def _create_implementation_strategy(
        self,
        recommendations: Dict,
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """Create implementation strategy for alternative investments"""
        strategy = {
            'phases': [],
            'timeline_months': 0,
            'priority_order': [],
            'platform_recommendations': []
        }
        
        # Phase 1: Liquid alternatives (REITs, Commodities)
        phase1 = {
            'phase': 1,
            'duration_months': 1,
            'investments': []
        }
        
        if 'real_estate' in recommendations:
            phase1['investments'].append('REITs')
            strategy['platform_recommendations'].append({
                'type': 'REIT',
                'platforms': ['Vanguard', 'Fidelity', 'Charles Schwab']
            })
        
        if 'commodities' in recommendations:
            phase1['investments'].append('Commodity ETFs')
            strategy['platform_recommendations'].append({
                'type': 'Commodities',
                'platforms': ['Interactive Brokers', 'TD Ameritrade']
            })
        
        if phase1['investments']:
            strategy['phases'].append(phase1)
            strategy['timeline_months'] += 1
        
        # Phase 2: Cryptocurrency
        if 'crypto' in recommendations:
            phase2 = {
                'phase': 2,
                'duration_months': 2,
                'investments': ['Cryptocurrency'],
                'steps': [
                    'Open account with regulated exchange',
                    'Complete KYC verification',
                    'Set up hardware wallet for large holdings',
                    'Implement dollar-cost averaging strategy'
                ]
            }
            strategy['phases'].append(phase2)
            strategy['timeline_months'] += 2
            strategy['platform_recommendations'].append({
                'type': 'Crypto',
                'platforms': ['Coinbase Pro', 'Kraken', 'Gemini']
            })
        
        # Phase 3: Private investments
        if 'private_equity' in recommendations:
            phase3 = {
                'phase': 3,
                'duration_months': 3,
                'investments': ['Private Equity'],
                'steps': [
                    'Complete accreditation verification',
                    'Review fund documents and terms',
                    'Consult with tax advisor',
                    'Complete subscription documents'
                ]
            }
            strategy['phases'].append(phase3)
            strategy['timeline_months'] += 3
        
        # Set priority order based on liquidity and complexity
        priority_map = {
            'commodities': 1,
            'real_estate': 2,
            'crypto': 3,
            'private_equity': 4
        }
        
        strategy['priority_order'] = sorted(
            recommendations.keys(),
            key=lambda x: priority_map.get(x, 5)
        )
        
        return strategy
    
    def _create_rebalancing_schedule(
        self,
        recommendations: Dict,
        investment_horizon_years: int
    ) -> List[Dict]:
        """Create rebalancing schedule for alternative investments"""
        schedule = []
        
        # Quarterly rebalancing for first year
        for quarter in range(1, 5):
            schedule.append({
                'period': f'Year 1, Q{quarter}',
                'actions': [
                    'Review crypto allocation and rebalance if >5% deviation',
                    'Assess commodity performance vs inflation',
                    'Monitor REIT distributions'
                ],
                'threshold': 0.05  # 5% deviation triggers rebalancing
            })
        
        # Semi-annual for subsequent years
        for year in range(2, min(investment_horizon_years + 1, 6)):
            for half in [1, 2]:
                schedule.append({
                    'period': f'Year {year}, H{half}',
                    'actions': [
                        'Comprehensive portfolio review',
                        'Rebalance if any allocation >10% deviation',
                        'Evaluate new opportunities',
                        'Tax loss harvesting review'
                    ],
                    'threshold': 0.10  # 10% deviation triggers rebalancing
                })
        
        return schedule
    
    def _calculate_risk_metrics(
        self,
        recommendations: Dict,
        portfolio: Portfolio
    ) -> Dict[str, float]:
        """Calculate comprehensive risk metrics for alternative allocation"""
        metrics = {}
        
        # Calculate total alternatives
        total_alts = sum(
            self._get_allocation_amount(alloc)
            for alloc in recommendations.values()
        )
        
        # Concentration risk
        largest_position = max(
            (self._get_allocation_amount(alloc) for alloc in recommendations.values()),
            default=0
        )
        metrics['concentration_risk'] = (
            largest_position / total_alts if total_alts > 0 else 0
        )
        
        # Liquidity risk (percentage in illiquid investments)
        illiquid = 0
        if 'private_equity' in recommendations:
            illiquid += self._get_allocation_amount(recommendations['private_equity'])
        if 'real_estate' in recommendations:
            # Assume 50% of real estate is illiquid
            illiquid += self._get_allocation_amount(recommendations['real_estate']) * 0.5
        
        metrics['liquidity_risk'] = illiquid / total_alts if total_alts > 0 else 0
        
        # Volatility estimate
        vol_contributions = []
        if 'crypto' in recommendations and hasattr(recommendations['crypto'], 'volatility'):
            vol_contributions.append(recommendations['crypto'].volatility)
        if 'commodities' in recommendations:
            vol_contributions.append(0.20)
        if 'real_estate' in recommendations:
            vol_contributions.append(0.15)
        
        metrics['estimated_volatility'] = np.mean(vol_contributions) if vol_contributions else 0
        
        # Maximum drawdown estimate
        metrics['estimated_max_drawdown'] = metrics['estimated_volatility'] * 2.5
        
        # Sharpe ratio estimate
        risk_free_rate = 0.04
        expected_return = self._calculate_return_improvement(recommendations)
        metrics['estimated_sharpe'] = (
            (expected_return - risk_free_rate) / metrics['estimated_volatility']
            if metrics['estimated_volatility'] > 0 else 0
        )
        
        return metrics
    
    def _calculate_defi_risk_score(self, opportunity: Dict) -> float:
        """Calculate risk score for DeFi opportunity"""
        base_risk = {
            'low': 0.2,
            'low-medium': 0.35,
            'medium': 0.5,
            'medium-high': 0.65,
            'high': 0.8
        }.get(opportunity.get('risk_level', 'medium'), 0.5)
        
        # Adjust for audit score
        audit_score = opportunity.get('audit_score', 7) / 10
        audit_adjustment = (1 - audit_score) * 0.2
        
        # Adjust for TVL (higher TVL = lower risk)
        tvl = opportunity.get('tvl', 1e6)
        tvl_adjustment = max(0, 0.1 - np.log10(tvl) / 100)
        
        # Insurance reduces risk
        insurance_adjustment = -0.1 if opportunity.get('insurance_available') else 0
        
        return min(1.0, max(0, base_risk + audit_adjustment + tvl_adjustment + insurance_adjustment))
    
    def _estimate_gas_costs(self, opportunity: Dict) -> float:
        """Estimate monthly gas costs as percentage of APY"""
        # Base gas estimates by protocol type
        gas_intensity = {
            'lending': 0.002,  # 0.2% APY
            'liquid_staking': 0.001,  # 0.1% APY
            'concentrated_liquidity': 0.015,  # 1.5% APY (requires rebalancing)
            'stable_liquidity': 0.003,  # 0.3% APY
            'yield_aggregator': 0.005,  # 0.5% APY
            'yield_booster': 0.004,  # 0.4% APY
            'options_vault': 0.008,  # 0.8% APY
            'perpetuals_liquidity': 0.006  # 0.6% APY
        }.get(opportunity.get('type'), 0.005)
        
        # Adjust for L2 optimization
        if 'L2' in opportunity.get('gas_optimization', ''):
            gas_intensity *= 0.1  # 90% reduction on L2
        
        return gas_intensity
    
    def _identify_yield_farming_opportunities(
        self,
        allocation: Dict[str, float],
        max_farming_allocation: float
    ) -> List[Dict]:
        """Identify yield farming opportunities"""
        opportunities = []
        
        if max_farming_allocation < 2000:
            return opportunities
        
        # Multi-protocol strategies
        opportunities.extend([
            {
                'protocol': 'Curve + Convex',
                'strategy': 'Stablecoin farming',
                'pools': ['3pool', 'fraxbp'],
                'base_apy': 0.04,
                'boost_apy': 0.08,
                'crv_rewards': True,
                'cvx_rewards': True,
                'risk_level': 'low-medium',
                'recommended_allocation': min(max_farming_allocation * 0.4, 20000),
                'auto_compound': True
            },
            {
                'protocol': 'Balancer',
                'strategy': 'Weighted pools',
                'pools': ['wstETH/WETH', 'rETH/WETH'],
                'base_apy': 0.06,
                'bal_rewards': 0.04,
                'total_apy': 0.10,
                'risk_level': 'medium',
                'recommended_allocation': min(max_farming_allocation * 0.3, 15000),
                'veBAL_boost': True
            }
        ])
        
        if 'ETH' in allocation and allocation['ETH'] > 5000:
            opportunities.append({
                'protocol': 'Pendle',
                'strategy': 'Yield tokenization',
                'asset': 'stETH',
                'fixed_yield': 0.045,
                'variable_yield': '3-8%',
                'maturity': '6 months',
                'risk_level': 'medium',
                'recommended_allocation': min(allocation['ETH'] * 0.3, 10000),
                'principal_protected': True
            })
        
        return opportunities
    
    def _identify_liquidity_pool_opportunities(
        self,
        allocation: Dict[str, float],
        max_lp_allocation: float
    ) -> List[Dict]:
        """Identify liquidity pool opportunities"""
        opportunities = []
        
        if max_lp_allocation < 3000:
            return opportunities
        
        # Concentrated liquidity opportunities
        if 'ETH' in allocation and 'USDC' in allocation:
            opportunities.append({
                'protocol': 'Uniswap V3',
                'pair': 'ETH/USDC',
                'fee_tier': 0.05,  # 0.05% fee tier
                'range': '±10%',
                'estimated_apy': 0.25,
                'capital_efficiency': '4x',
                'risk_level': 'medium-high',
                'recommended_allocation': min(max_lp_allocation * 0.3, 25000),
                'management_tool': 'Arrakis Finance'
            })
        
        # Stable pairs
        opportunities.append({
            'protocol': 'Curve',
            'pool': 'TriCrypto',
            'assets': ['USDT', 'WBTC', 'WETH'],
            'estimated_apy': 0.12,
            'impermanent_loss': 'moderate',
            'risk_level': 'medium',
            'recommended_allocation': min(max_lp_allocation * 0.4, 30000),
            'gauge_eligible': True
        })
        
        return opportunities
    
    def _identify_lending_opportunities(
        self,
        allocation: Dict[str, float],
        max_lending_allocation: float
    ) -> List[Dict]:
        """Identify lending protocol opportunities"""
        opportunities = []
        
        lending_protocols = [
            {
                'protocol': 'Aave V3',
                'chain': 'Ethereum',
                'assets': ['USDC', 'USDT', 'DAI', 'WETH', 'WBTC'],
                'supply_apy': {'USDC': 0.052, 'WETH': 0.018, 'WBTC': 0.008},
                'borrow_enabled': True,
                'efficiency_mode': True,
                'risk_level': 'low'
            },
            {
                'protocol': 'Compound V3',
                'chain': 'Ethereum',
                'base_asset': 'USDC',
                'supply_apy': 0.048,
                'comp_rewards': 0.012,
                'total_apy': 0.060,
                'risk_level': 'low'
            },
            {
                'protocol': 'Morpho',
                'chain': 'Ethereum',
                'type': 'P2P matching',
                'improved_rates': '15-30%',
                'underlying': 'Aave/Compound',
                'risk_level': 'low-medium'
            }
        ]
        
        for protocol in lending_protocols:
            if max_lending_allocation > 5000:
                opportunities.append({
                    **protocol,
                    'recommended_allocation': min(max_lending_allocation * 0.3, 20000),
                    'strategy': 'Supply and borrow stablecoins for additional yield'
                })
        
        return opportunities
    
    def _identify_derivatives_strategies(
        self,
        allocation: Dict[str, float],
        max_derivatives_allocation: float
    ) -> List[Dict]:
        """Identify derivatives and structured product strategies"""
        strategies = []
        
        if max_derivatives_allocation < 5000:
            return strategies
        
        if 'ETH' in allocation and allocation['ETH'] > 10000:
            strategies.extend([
                {
                    'protocol': 'Ribbon Finance',
                    'product': 'ETH Covered Call Vault',
                    'strategy': 'Sell weekly OTM calls',
                    'strike': '10% OTM',
                    'estimated_apy': 0.20,
                    'principal_risk': 'capped upside',
                    'risk_level': 'medium',
                    'recommended_allocation': min(allocation['ETH'] * 0.2, 15000)
                },
                {
                    'protocol': 'Dopex',
                    'product': 'Atlantic Straddles',
                    'strategy': 'Volatility harvesting',
                    'estimated_apy': 0.30,
                    'principal_risk': 'moderate',
                    'risk_level': 'medium-high',
                    'recommended_allocation': min(max_derivatives_allocation * 0.2, 10000)
                }
            ])
        
        if 'BTC' in allocation and allocation['BTC'] > 10000:
            strategies.append({
                'protocol': 'Squeeth',
                'product': 'Power Perpetuals',
                'strategy': 'Squared exposure to ETH',
                'use_case': 'Hedging or speculation',
                'funding_rate': 'variable',
                'risk_level': 'high',
                'recommended_allocation': min(max_derivatives_allocation * 0.1, 5000)
            })
        
        return strategies
    
    def _assess_staking_risks(self, provider_data: Dict) -> Dict[str, float]:
        """Assess risks associated with staking provider"""
        risks = {
            'slashing_risk': 0.01 if not provider_data.get('derivative') else 0,
            'liquidity_risk': 0 if provider_data.get('lock_period') == 'liquid' else 0.1,
            'smart_contract_risk': 0.05 if provider_data.get('derivative') else 0.02,
            'regulatory_risk': 0.03,
            'validator_risk': 0.02 if provider_data.get('validator_selection') else 0.01
        }
        return risks
    
    def _get_staking_features(self, provider_data: Dict) -> List[str]:
        """Get additional features of staking provider"""
        features = []
        
        if provider_data.get('derivative'):
            features.append(f"Liquid staking token: {provider_data['derivative']}")
        if provider_data.get('auto_compound'):
            features.append("Auto-compounding rewards")
        if provider_data.get('insurance'):
            features.append("Slashing insurance available")
        if provider_data.get('decentralized'):
            features.append("Decentralized validator set")
        if provider_data.get('regulated'):
            features.append("Regulated provider")
        if provider_data.get('defi_composable'):
            features.append("DeFi composable derivative")
        
        return features
    
    def _calculate_risk_adjusted_staking_return(
        self,
        net_apy: float,
        risk_factors: Dict[str, float]
    ) -> float:
        """Calculate risk-adjusted staking returns"""
        total_risk = sum(risk_factors.values())
        risk_adjustment = 1 - total_risk
        return net_apy * risk_adjustment
    
    def _estimate_max_drawdown(
        self,
        allocation: Dict[str, float],
        volatilities: Dict[str, float],
        correlation_matrix: np.ndarray
    ) -> float:
        """Estimate maximum drawdown using Monte Carlo simulation"""
        if not allocation:
            return 0
        
        # Simplified estimation: 2.5 standard deviations
        portfolio_vol = self._calculate_portfolio_volatility(
            allocation,
            volatilities,
            correlation_matrix,
            sum(allocation.values())
        )
        
        # Crypto markets can have severe drawdowns
        max_drawdown = min(0.95, portfolio_vol * 2.5)
        
        return max_drawdown


# Support classes for initialization
@dataclass
class CryptoService:
    """Mock crypto service for demonstration"""
    async def get_market_data(self, symbols: List[str]) -> Dict:
        # In production, this would fetch real market data
        return {}


@dataclass
class RealEstateService:
    """Mock real estate service for demonstration"""
    pass


@dataclass
class PrivateEquityService:
    """Mock private equity service for demonstration"""
    pass


@dataclass
class CommoditiesService:
    """Mock commodities service for demonstration"""
    pass


@dataclass
class NFTService:
    """Mock NFT service for demonstration"""
    pass


class CryptoPortfolioOptimizer:
    """Dedicated optimizer for cryptocurrency portfolios"""
    
    async def optimize(
        self,
        available_cryptos: List[str],
        risk_scores: Dict[str, float],
        max_allocation: float,
        constraints: Dict
    ) -> Dict:
        # Simplified optimization logic
        return {
            'remaining_capital': 0
        }