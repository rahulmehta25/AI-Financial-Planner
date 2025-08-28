"""
Institutional Portfolio Manager - Advanced institutional investment management system
with liability-driven investing, asset-liability matching, and large order execution.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from scipy import optimize
from scipy.stats import norm, t
from scipy.linalg import sqrtm
import json

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

class InstitutionType(Enum):
    """Types of institutional investors"""
    PENSION_FUND = "pension_fund"
    INSURANCE_COMPANY = "insurance_company"
    ENDOWMENT = "endowment"
    FOUNDATION = "foundation"
    SOVEREIGN_WEALTH = "sovereign_wealth"
    CENTRAL_BANK = "central_bank"
    ASSET_MANAGER = "asset_manager"

class LiabilityType(Enum):
    """Types of institutional liabilities"""
    DEFINED_BENEFIT = "defined_benefit"
    DEFINED_CONTRIBUTION = "defined_contribution"
    INSURANCE_CLAIMS = "insurance_claims"
    SPENDING_COMMITMENT = "spending_commitment"
    REGULATORY_CAPITAL = "regulatory_capital"

class ExecutionAlgorithm(Enum):
    """Large order execution algorithms"""
    VWAP = "vwap"  # Volume Weighted Average Price
    TWAP = "twap"  # Time Weighted Average Price
    POV = "pov"    # Percentage of Volume
    IS = "is"      # Implementation Shortfall
    ARRIVAL_PRICE = "arrival_price"
    CLOSE_TARGET = "close_target"
    LIQUIDITY_SEEKING = "liquidity_seeking"
    DARK_POOL = "dark_pool"

class RiskBudgetType(Enum):
    """Risk budget allocation methods"""
    EQUAL_RISK = "equal_risk"
    RISK_PARITY = "risk_parity"
    MAXIMUM_DIVERSIFICATION = "maximum_diversification"
    FACTOR_BASED = "factor_based"
    VOLATILITY_TARGET = "volatility_target"

@dataclass
class Liability:
    """Institutional liability structure"""
    liability_id: str
    type: LiabilityType
    nominal_value: float
    present_value: float
    duration: float  # Modified duration
    convexity: float
    payment_schedule: List[Dict[str, float]]  # {date: amount}
    inflation_linked: bool = False
    discount_rate: float = 0.03
    confidence_level: float = 0.95

@dataclass
class AssetClass:
    """Institutional asset class definition"""
    name: str
    allocation: float  # Current allocation percentage
    target_allocation: float
    min_allocation: float
    max_allocation: float
    expected_return: float
    volatility: float
    duration: float = 0.0  # For fixed income
    liquidity_score: float = 1.0  # 0-1 scale
    correlation_matrix: Optional[np.ndarray] = None

@dataclass
class FundingRatio:
    """Pension funding ratio metrics"""
    assets: float
    liabilities: float
    ratio: float
    surplus_deficit: float
    required_return: float
    funding_gap_years: Optional[float] = None
    stress_scenarios: Dict[str, float] = field(default_factory=dict)

@dataclass
class ExecutionOrder:
    """Large order execution parameters"""
    symbol: str
    quantity: float
    side: str  # "buy" or "sell"
    algorithm: ExecutionAlgorithm
    urgency: float  # 0-1 scale
    risk_aversion: float  # 0-1 scale
    start_time: datetime
    end_time: datetime
    participation_rate: float = 0.20  # Target % of market volume
    limit_price: Optional[float] = None
    benchmark: str = "arrival"  # arrival, vwap, twap, close

@dataclass
class TransactionCost:
    """Transaction cost analysis components"""
    spread_cost: float
    market_impact: float
    delay_cost: float
    opportunity_cost: float
    total_cost: float
    cost_basis_points: float
    implementation_shortfall: float
    execution_price: float
    benchmark_price: float
    side: str

@dataclass
class OverlayStrategy:
    """Overlay strategy parameters"""
    strategy_type: str  # duration, currency, equity, credit
    notional_exposure: float
    hedge_ratio: float
    instruments: List[str]  # derivatives used
    cost_basis_points: float
    effectiveness: float  # hedge effectiveness
    rebalance_frequency: str  # daily, weekly, monthly
    margin_requirement: float

# ============================================================================
# MAIN INSTITUTIONAL PORTFOLIO MANAGER
# ============================================================================

class InstitutionalPortfolioManager:
    """
    Comprehensive institutional portfolio management system with advanced
    liability-driven investing, execution algorithms, and risk management.
    """
    
    def __init__(self):
        self.liabilities: Dict[str, Liability] = {}
        self.asset_classes: Dict[str, AssetClass] = {}
        self.overlay_strategies: List[OverlayStrategy] = []
        self.execution_history: List[TransactionCost] = []
        self.risk_budgets: Dict[str, float] = {}
        
        # Market data cache
        self.market_data = {
            'risk_free_rate': 0.045,
            'inflation_rate': 0.025,
            'credit_spreads': {},
            'volatility_surface': {},
            'correlation_matrix': None
        }
        
        # Execution parameters
        self.execution_params = {
            'max_participation': 0.25,
            'min_block_size': 1000,
            'dark_pool_threshold': 50000,
            'urgency_multiplier': 1.5
        }
        
        logger.info("Institutional Portfolio Manager initialized")
    
    # ========================================================================
    # LIABILITY-DRIVEN INVESTING (LDI)
    # ========================================================================
    
    async def implement_ldi_strategy(
        self,
        liabilities: List[Liability],
        assets: Dict[str, float],
        target_funding_ratio: float = 1.05
    ) -> Dict[str, Any]:
        """
        Implement liability-driven investing strategy for pension funds.
        
        Args:
            liabilities: List of institutional liabilities
            assets: Current asset allocations
            target_funding_ratio: Target assets/liabilities ratio
            
        Returns:
            LDI strategy with asset allocation and hedging recommendations
        """
        try:
            # Calculate aggregate liability metrics
            total_liabilities = sum(l.present_value for l in liabilities)
            weighted_duration = sum(
                l.present_value * l.duration for l in liabilities
            ) / total_liabilities
            weighted_convexity = sum(
                l.present_value * l.convexity for l in liabilities
            ) / total_liabilities
            
            # Calculate required return to meet liabilities
            total_assets = sum(assets.values())
            funding_ratio = total_assets / total_liabilities
            funding_gap = max(0, target_funding_ratio * total_liabilities - total_assets)
            
            # Duration matching for interest rate hedging
            liability_duration = weighted_duration
            asset_duration = self._calculate_portfolio_duration(assets)
            duration_gap = liability_duration - asset_duration
            
            # Calculate hedging requirements
            hedge_notional = total_liabilities * duration_gap * 0.01  # 1% rate move
            
            # Determine asset allocation strategy
            if funding_ratio < 0.8:
                # Severely underfunded - growth focus
                strategy_type = "growth_oriented"
                equity_target = 0.60
                fixed_income_target = 0.30
                alternatives_target = 0.10
            elif funding_ratio < 1.0:
                # Underfunded - balanced approach
                strategy_type = "balanced_growth"
                equity_target = 0.45
                fixed_income_target = 0.40
                alternatives_target = 0.15
            elif funding_ratio < target_funding_ratio:
                # Near fully funded - de-risking
                strategy_type = "de_risking"
                equity_target = 0.35
                fixed_income_target = 0.50
                alternatives_target = 0.15
            else:
                # Fully funded - liability matching
                strategy_type = "liability_matching"
                equity_target = 0.25
                fixed_income_target = 0.65
                alternatives_target = 0.10
            
            # Create glide path for de-risking
            glide_path = self._create_glide_path(
                current_funding=funding_ratio,
                target_funding=target_funding_ratio,
                years=10
            )
            
            # Calculate cash flow matching portfolio
            cf_matching = await self._cash_flow_matching(liabilities, assets)
            
            # Stress test the strategy
            stress_results = self._stress_test_ldi(
                assets=total_assets,
                liabilities=total_liabilities,
                duration_gap=duration_gap
            )
            
            return {
                'strategy_type': strategy_type,
                'funding_metrics': {
                    'current_ratio': funding_ratio,
                    'target_ratio': target_funding_ratio,
                    'funding_gap': funding_gap,
                    'required_return': self._calculate_required_return(
                        funding_gap, total_assets, years=7
                    )
                },
                'liability_metrics': {
                    'total_pv': total_liabilities,
                    'duration': weighted_duration,
                    'convexity': weighted_convexity,
                    'inflation_sensitivity': sum(
                        l.present_value for l in liabilities if l.inflation_linked
                    ) / total_liabilities
                },
                'asset_allocation': {
                    'equity': equity_target,
                    'fixed_income': fixed_income_target,
                    'alternatives': alternatives_target,
                    'rebalancing_threshold': 0.05
                },
                'hedging_strategy': {
                    'duration_gap': duration_gap,
                    'hedge_notional': hedge_notional,
                    'recommended_instruments': self._get_hedging_instruments(
                        duration_gap, hedge_notional
                    )
                },
                'glide_path': glide_path,
                'cash_flow_matching': cf_matching,
                'stress_test_results': stress_results,
                'implementation_priority': self._prioritize_actions(
                    funding_ratio, duration_gap
                )
            }
            
        except Exception as e:
            logger.error(f"LDI strategy implementation failed: {str(e)}")
            raise
    
    # ========================================================================
    # ASSET-LIABILITY MATCHING (ALM)
    # ========================================================================
    
    async def optimize_alm(
        self,
        assets: Dict[str, AssetClass],
        liabilities: List[Liability],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize asset-liability matching using stochastic programming.
        
        Args:
            assets: Available asset classes
            liabilities: Institutional liabilities
            constraints: Investment constraints
            
        Returns:
            Optimal ALM strategy with allocation and risk metrics
        """
        try:
            # Prepare optimization inputs
            n_assets = len(assets)
            returns = np.array([a.expected_return for a in assets.values()])
            volatilities = np.array([a.volatility for a in assets.values()])
            
            # Build correlation matrix
            correlations = self._build_correlation_matrix(assets)
            cov_matrix = np.outer(volatilities, volatilities) * correlations
            
            # Calculate liability-driven constraints
            liability_pv = sum(l.present_value for l in liabilities)
            liability_duration = sum(
                l.present_value * l.duration for l in liabilities
            ) / liability_pv
            
            # Define optimization objective (minimize ALM risk)
            def alm_objective(weights):
                portfolio_return = np.dot(weights, returns)
                portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
                
                # Duration matching penalty
                asset_duration = sum(
                    w * a.duration for w, a in zip(weights, assets.values())
                )
                duration_penalty = 10 * (asset_duration - liability_duration) ** 2
                
                # Funding ratio volatility
                funding_volatility = np.sqrt(portfolio_variance) * liability_pv
                
                # Combined objective
                return -portfolio_return + 0.5 * portfolio_variance + duration_penalty
            
            # Set up constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
            ]
            
            # Add custom constraints
            if constraints:
                if 'min_funding_return' in constraints:
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda x: np.dot(x, returns) - constraints['min_funding_return']
                    })
                
                if 'max_tracking_error' in constraints:
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda x: constraints['max_tracking_error'] - 
                                        np.sqrt(np.dot(x, np.dot(cov_matrix, x)))
                    })
            
            # Set bounds for each asset
            bounds = [(a.min_allocation, a.max_allocation) for a in assets.values()]
            
            # Run optimization
            initial_weights = np.array([a.allocation for a in assets.values()])
            result = optimize.minimize(
                alm_objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list,
                options={'maxiter': 1000}
            )
            
            optimal_weights = result.x
            
            # Calculate ALM metrics
            optimal_return = np.dot(optimal_weights, returns)
            optimal_risk = np.sqrt(np.dot(optimal_weights, np.dot(cov_matrix, optimal_weights)))
            optimal_duration = sum(
                w * a.duration for w, a in zip(optimal_weights, assets.values())
            )
            
            # Monte Carlo simulation for ALM outcomes
            alm_simulation = await self._simulate_alm_outcomes(
                weights=optimal_weights,
                assets=assets,
                liabilities=liabilities,
                n_scenarios=10000
            )
            
            # Calculate surplus risk metrics
            surplus_risk = self._calculate_surplus_risk(
                optimal_weights, assets, liabilities, cov_matrix
            )
            
            return {
                'optimal_allocation': {
                    name: weight for name, weight in zip(assets.keys(), optimal_weights)
                },
                'portfolio_metrics': {
                    'expected_return': optimal_return,
                    'volatility': optimal_risk,
                    'duration': optimal_duration,
                    'sharpe_ratio': (optimal_return - self.market_data['risk_free_rate']) / optimal_risk
                },
                'alm_metrics': {
                    'duration_match': optimal_duration - liability_duration,
                    'funding_ratio_volatility': optimal_risk * liability_pv,
                    'surplus_at_risk': surplus_risk['surplus_at_risk'],
                    'conditional_surplus_at_risk': surplus_risk['conditional_surplus_at_risk']
                },
                'simulation_results': alm_simulation,
                'rebalancing_triggers': {
                    'duration_threshold': 0.5,
                    'allocation_threshold': 0.05,
                    'funding_ratio_threshold': 0.03
                },
                'implementation_costs': self._estimate_rebalancing_costs(
                    current_weights=initial_weights,
                    target_weights=optimal_weights,
                    assets=assets
                )
            }
            
        except Exception as e:
            logger.error(f"ALM optimization failed: {str(e)}")
            raise
    
    # ========================================================================
    # GLIDE PATH OPTIMIZATION
    # ========================================================================
    
    def optimize_glide_path(
        self,
        current_age: int,
        retirement_age: int,
        life_expectancy: int,
        risk_tolerance: float,
        funding_status: float
    ) -> Dict[str, Any]:
        """
        Optimize glide path for pension funds and target-date strategies.
        
        Args:
            current_age: Current participant age
            retirement_age: Target retirement age
            life_expectancy: Expected lifespan
            risk_tolerance: Risk tolerance (0-1)
            funding_status: Current funding ratio
            
        Returns:
            Optimized glide path with age-based allocations
        """
        try:
            years_to_retirement = retirement_age - current_age
            years_in_retirement = life_expectancy - retirement_age
            
            # Create age buckets
            ages = list(range(current_age, life_expectancy + 1))
            
            # Initialize glide path allocations
            glide_path = {}
            
            for age in ages:
                if age < retirement_age:
                    # Accumulation phase
                    years_remaining = retirement_age - age
                    
                    # Equity allocation decreases as retirement approaches
                    base_equity = 0.9 - (0.6 * (1 - years_remaining / years_to_retirement))
                    
                    # Adjust for funding status
                    if funding_status < 0.8:
                        equity_adjustment = 0.1  # More aggressive if underfunded
                    elif funding_status > 1.2:
                        equity_adjustment = -0.1  # More conservative if overfunded
                    else:
                        equity_adjustment = 0
                    
                    # Adjust for risk tolerance
                    risk_adjustment = (risk_tolerance - 0.5) * 0.2
                    
                    equity_allocation = np.clip(
                        base_equity + equity_adjustment + risk_adjustment,
                        0.2, 0.95
                    )
                    
                    # Fixed income allocation
                    fixed_income = 0.7 * (1 - equity_allocation)
                    
                    # Alternatives allocation
                    alternatives = 0.3 * (1 - equity_allocation)
                    
                else:
                    # Retirement phase
                    years_in = age - retirement_age
                    
                    # More conservative allocation in retirement
                    equity_allocation = max(
                        0.2,
                        0.4 - (0.2 * years_in / years_in_retirement)
                    )
                    
                    # Higher fixed income for income generation
                    fixed_income = 0.7 + (0.1 * years_in / years_in_retirement)
                    
                    # Reduced alternatives
                    alternatives = 1 - equity_allocation - fixed_income
                
                glide_path[age] = {
                    'equity': round(equity_allocation, 3),
                    'fixed_income': round(fixed_income, 3),
                    'alternatives': round(max(0, alternatives), 3),
                    'cash': round(max(0, 1 - equity_allocation - fixed_income - alternatives), 3)
                }
            
            # Calculate risk metrics along glide path
            risk_profile = self._calculate_glide_path_risk(glide_path)
            
            # Optimize transition points
            transition_points = self._optimize_transitions(glide_path, funding_status)
            
            return {
                'glide_path': glide_path,
                'current_allocation': glide_path[current_age],
                'retirement_allocation': glide_path[retirement_age],
                'risk_profile': risk_profile,
                'transition_points': transition_points,
                'expected_outcomes': {
                    'median_wealth_at_retirement': self._project_wealth(
                        glide_path, current_age, retirement_age, percentile=50
                    ),
                    'lower_quartile': self._project_wealth(
                        glide_path, current_age, retirement_age, percentile=25
                    ),
                    'upper_quartile': self._project_wealth(
                        glide_path, current_age, retirement_age, percentile=75
                    )
                },
                'rebalancing_schedule': 'quarterly',
                'de_risking_triggers': {
                    'funding_ratio': 1.1,
                    'years_to_retirement': 10,
                    'market_volatility': 0.25
                }
            }
            
        except Exception as e:
            logger.error(f"Glide path optimization failed: {str(e)}")
            raise
    
    # ========================================================================
    # RISK BUDGETING
    # ========================================================================
    
    def implement_risk_budgeting(
        self,
        assets: Dict[str, AssetClass],
        risk_budget_type: RiskBudgetType,
        total_risk_budget: float = 0.15
    ) -> Dict[str, Any]:
        """
        Implement risk budgeting framework for institutional portfolios.
        
        Args:
            assets: Asset classes with characteristics
            risk_budget_type: Type of risk budgeting approach
            total_risk_budget: Total portfolio risk budget
            
        Returns:
            Risk budget allocations and portfolio construction
        """
        try:
            n_assets = len(assets)
            
            # Build covariance matrix
            returns = np.array([a.expected_return for a in assets.values()])
            volatilities = np.array([a.volatility for a in assets.values()])
            correlations = self._build_correlation_matrix(assets)
            cov_matrix = np.outer(volatilities, volatilities) * correlations
            
            if risk_budget_type == RiskBudgetType.EQUAL_RISK:
                # Equal risk contribution
                risk_budgets = np.ones(n_assets) / n_assets
                weights = self._solve_risk_parity(cov_matrix, risk_budgets)
                
            elif risk_budget_type == RiskBudgetType.RISK_PARITY:
                # Risk parity - inverse volatility weighted
                inv_vols = 1 / volatilities
                weights = inv_vols / np.sum(inv_vols)
                weights = self._solve_risk_parity(cov_matrix, weights)
                
            elif risk_budget_type == RiskBudgetType.MAXIMUM_DIVERSIFICATION:
                # Maximum diversification ratio
                weights = self._maximize_diversification(cov_matrix, volatilities)
                
            elif risk_budget_type == RiskBudgetType.FACTOR_BASED:
                # Factor-based risk budgeting
                factor_exposures = self._get_factor_exposures(assets)
                weights = self._factor_risk_budgeting(
                    cov_matrix, factor_exposures, total_risk_budget
                )
                
            else:  # VOLATILITY_TARGET
                # Target volatility optimization
                weights = self._volatility_targeting(
                    returns, cov_matrix, total_risk_budget
                )
            
            # Scale to meet total risk budget
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            if portfolio_vol > total_risk_budget:
                leverage = total_risk_budget / portfolio_vol
                weights = weights * leverage
                cash_weight = 1 - np.sum(weights)
            else:
                cash_weight = 0
            
            # Calculate risk contributions
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            risk_contributions = weights * marginal_contrib
            
            # Calculate risk metrics
            portfolio_return = np.dot(weights, returns)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            
            # Diversification metrics
            weighted_avg_vol = np.dot(weights, volatilities)
            diversification_ratio = weighted_avg_vol / portfolio_vol
            
            # Concentration metrics
            effective_n = 1 / np.sum(weights ** 2)
            max_weight = np.max(weights)
            
            return {
                'risk_budget_allocation': {
                    name: {
                        'weight': float(w),
                        'risk_contribution': float(rc),
                        'risk_budget': float(rc / np.sum(risk_contributions))
                    }
                    for name, w, rc in zip(assets.keys(), weights, risk_contributions)
                },
                'portfolio_metrics': {
                    'expected_return': float(portfolio_return),
                    'volatility': float(portfolio_vol),
                    'sharpe_ratio': float(
                        (portfolio_return - self.market_data['risk_free_rate']) / portfolio_vol
                    ),
                    'cash_allocation': float(cash_weight)
                },
                'risk_metrics': {
                    'total_risk_used': float(portfolio_vol),
                    'risk_budget_remaining': float(max(0, total_risk_budget - portfolio_vol)),
                    'diversification_ratio': float(diversification_ratio),
                    'effective_number_of_bets': float(effective_n),
                    'max_concentration': float(max_weight)
                },
                'implementation': {
                    'rebalancing_frequency': 'monthly',
                    'risk_budget_tolerance': 0.02,
                    'tracking_error_limit': 0.03,
                    'leverage_required': float(1 / (1 - cash_weight)) if cash_weight > 0 else 1.0
                },
                'stress_test': self._stress_test_risk_budget(
                    weights, cov_matrix, total_risk_budget
                )
            }
            
        except Exception as e:
            logger.error(f"Risk budgeting implementation failed: {str(e)}")
            raise
    
    # ========================================================================
    # OVERLAY STRATEGIES
    # ========================================================================
    
    async def design_overlay_strategy(
        self,
        base_portfolio: Dict[str, float],
        overlay_objectives: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Design overlay strategies for duration, currency, and risk management.
        
        Args:
            base_portfolio: Current portfolio allocations
            overlay_objectives: List of overlay objectives
            constraints: Overlay constraints
            
        Returns:
            Comprehensive overlay strategy design
        """
        try:
            overlay_strategies = []
            total_cost = 0
            margin_requirement = 0
            
            for objective in overlay_objectives:
                if objective == "duration_matching":
                    strategy = await self._duration_overlay(base_portfolio, constraints)
                    overlay_strategies.append(strategy)
                    
                elif objective == "currency_hedging":
                    strategy = await self._currency_overlay(base_portfolio, constraints)
                    overlay_strategies.append(strategy)
                    
                elif objective == "tail_risk_hedging":
                    strategy = await self._tail_risk_overlay(base_portfolio, constraints)
                    overlay_strategies.append(strategy)
                    
                elif objective == "equity_beta_management":
                    strategy = await self._equity_overlay(base_portfolio, constraints)
                    overlay_strategies.append(strategy)
                    
                elif objective == "credit_spread_hedging":
                    strategy = await self._credit_overlay(base_portfolio, constraints)
                    overlay_strategies.append(strategy)
                    
                elif objective == "inflation_protection":
                    strategy = await self._inflation_overlay(base_portfolio, constraints)
                    overlay_strategies.append(strategy)
                
                if strategy:
                    total_cost += strategy.cost_basis_points
                    margin_requirement += strategy.margin_requirement
            
            # Optimize overlay combination
            optimized_overlays = self._optimize_overlay_combination(
                overlay_strategies, base_portfolio, constraints
            )
            
            # Calculate aggregate impact
            aggregate_impact = self._calculate_overlay_impact(
                base_portfolio, optimized_overlays
            )
            
            return {
                'overlay_strategies': [
                    {
                        'type': s.strategy_type,
                        'notional': s.notional_exposure,
                        'hedge_ratio': s.hedge_ratio,
                        'instruments': s.instruments,
                        'cost_bps': s.cost_basis_points,
                        'effectiveness': s.effectiveness,
                        'rebalance_frequency': s.rebalance_frequency
                    }
                    for s in optimized_overlays
                ],
                'aggregate_metrics': {
                    'total_cost_bps': total_cost,
                    'total_margin': margin_requirement,
                    'margin_efficiency': self._calculate_margin_efficiency(
                        optimized_overlays, aggregate_impact
                    )
                },
                'risk_impact': aggregate_impact,
                'implementation_plan': {
                    'execution_timeline': self._create_overlay_timeline(optimized_overlays),
                    'monitoring_framework': self._design_monitoring_framework(optimized_overlays),
                    'trigger_levels': self._set_overlay_triggers(optimized_overlays)
                },
                'stress_scenarios': await self._stress_test_overlays(
                    base_portfolio, optimized_overlays
                ),
                'regulatory_considerations': self._check_regulatory_compliance(
                    optimized_overlays, margin_requirement
                )
            }
            
        except Exception as e:
            logger.error(f"Overlay strategy design failed: {str(e)}")
            raise
    
    # ========================================================================
    # LARGE ORDER EXECUTION
    # ========================================================================
    
    async def execute_large_order(
        self,
        order: ExecutionOrder,
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute large institutional orders using advanced algorithms.
        
        Args:
            order: Execution order parameters
            market_conditions: Current market conditions
            
        Returns:
            Execution results with transaction cost analysis
        """
        try:
            # Select execution algorithm
            if order.algorithm == ExecutionAlgorithm.VWAP:
                execution_result = await self._execute_vwap(order, market_conditions)
            elif order.algorithm == ExecutionAlgorithm.TWAP:
                execution_result = await self._execute_twap(order, market_conditions)
            elif order.algorithm == ExecutionAlgorithm.IS:
                execution_result = await self._execute_implementation_shortfall(
                    order, market_conditions
                )
            elif order.algorithm == ExecutionAlgorithm.POV:
                execution_result = await self._execute_pov(order, market_conditions)
            elif order.algorithm == ExecutionAlgorithm.ARRIVAL_PRICE:
                execution_result = await self._execute_arrival_price(order, market_conditions)
            else:
                execution_result = await self._execute_adaptive(order, market_conditions)
            
            # Calculate transaction costs
            tca = self._calculate_transaction_costs(
                order, execution_result, market_conditions
            )
            
            # Store execution history
            self.execution_history.append(tca)
            
            # Generate execution report
            report = {
                'execution_summary': {
                    'symbol': order.symbol,
                    'quantity': order.quantity,
                    'side': order.side,
                    'algorithm': order.algorithm.value,
                    'avg_price': execution_result['average_price'],
                    'total_cost': tca.total_cost,
                    'cost_bps': tca.cost_basis_points
                },
                'transaction_cost_analysis': {
                    'spread_cost': tca.spread_cost,
                    'market_impact': tca.market_impact,
                    'delay_cost': tca.delay_cost,
                    'opportunity_cost': tca.opportunity_cost,
                    'implementation_shortfall': tca.implementation_shortfall
                },
                'execution_details': execution_result,
                'market_conditions': market_conditions,
                'performance_metrics': {
                    'participation_rate': execution_result.get('actual_participation', 0),
                    'fill_rate': execution_result.get('fill_rate', 0),
                    'passive_fill_ratio': execution_result.get('passive_fills', 0),
                    'venue_analysis': execution_result.get('venue_breakdown', {})
                },
                'best_execution_analysis': self._analyze_best_execution(
                    order, execution_result, tca
                )
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Large order execution failed: {str(e)}")
            raise
    
    # ========================================================================
    # TRANSACTION COST ANALYSIS
    # ========================================================================
    
    def analyze_transaction_costs(
        self,
        trades: List[Dict[str, Any]],
        benchmark: str = "arrival"
    ) -> Dict[str, Any]:
        """
        Comprehensive transaction cost analysis for institutional trades.
        
        Args:
            trades: List of executed trades
            benchmark: Benchmark for cost measurement
            
        Returns:
            Detailed TCA report with cost breakdown and analytics
        """
        try:
            total_costs = {
                'spread_cost': 0,
                'market_impact': 0,
                'delay_cost': 0,
                'opportunity_cost': 0,
                'total_cost': 0
            }
            
            trade_analytics = []
            
            for trade in trades:
                # Calculate individual trade costs
                spread_cost = self._calculate_spread_cost(trade)
                market_impact = self._calculate_market_impact(trade)
                delay_cost = self._calculate_delay_cost(trade, benchmark)
                opportunity_cost = self._calculate_opportunity_cost(trade)
                
                total_trade_cost = spread_cost + market_impact + delay_cost + opportunity_cost
                
                # Store analytics
                trade_analytics.append({
                    'symbol': trade['symbol'],
                    'quantity': trade['quantity'],
                    'notional': trade['quantity'] * trade['execution_price'],
                    'spread_cost_bps': spread_cost * 10000 / (trade['quantity'] * trade['execution_price']),
                    'impact_bps': market_impact * 10000 / (trade['quantity'] * trade['execution_price']),
                    'delay_bps': delay_cost * 10000 / (trade['quantity'] * trade['execution_price']),
                    'total_cost_bps': total_trade_cost * 10000 / (trade['quantity'] * trade['execution_price'])
                })
                
                # Aggregate costs
                total_costs['spread_cost'] += spread_cost
                total_costs['market_impact'] += market_impact
                total_costs['delay_cost'] += delay_cost
                total_costs['opportunity_cost'] += opportunity_cost
                total_costs['total_cost'] += total_trade_cost
            
            # Calculate statistics
            cost_bps = [t['total_cost_bps'] for t in trade_analytics]
            
            return {
                'aggregate_costs': total_costs,
                'cost_breakdown': {
                    'spread_percentage': total_costs['spread_cost'] / total_costs['total_cost'] * 100,
                    'impact_percentage': total_costs['market_impact'] / total_costs['total_cost'] * 100,
                    'delay_percentage': total_costs['delay_cost'] / total_costs['total_cost'] * 100,
                    'opportunity_percentage': total_costs['opportunity_cost'] / total_costs['total_cost'] * 100
                },
                'trade_level_analytics': trade_analytics,
                'statistical_summary': {
                    'mean_cost_bps': np.mean(cost_bps),
                    'median_cost_bps': np.median(cost_bps),
                    'std_cost_bps': np.std(cost_bps),
                    'percentile_95': np.percentile(cost_bps, 95),
                    'percentile_5': np.percentile(cost_bps, 5)
                },
                'algorithm_performance': self._analyze_algorithm_performance(trades),
                'venue_analysis': self._analyze_venue_performance(trades),
                'time_of_day_analysis': self._analyze_time_patterns(trades),
                'recommendations': self._generate_tca_recommendations(trade_analytics)
            }
            
        except Exception as e:
            logger.error(f"Transaction cost analysis failed: {str(e)}")
            raise
    
    # ========================================================================
    # STRESS TESTING
    # ========================================================================
    
    async def stress_test_portfolio(
        self,
        portfolio: Dict[str, float],
        scenarios: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive stress testing for institutional portfolios.
        
        Args:
            portfolio: Current portfolio allocations
            scenarios: Specific stress scenarios to test
            
        Returns:
            Stress test results with impact analysis
        """
        try:
            if scenarios is None:
                scenarios = [
                    "equity_crash_2008",
                    "bond_tantrum_2013", 
                    "covid_pandemic_2020",
                    "inflation_surge_2022",
                    "banking_crisis_2023",
                    "geopolitical_conflict",
                    "stagflation",
                    "deflation_spiral"
                ]
            
            results = {}
            
            for scenario in scenarios:
                # Get scenario parameters
                scenario_params = self._get_scenario_parameters(scenario)
                
                # Apply shocks to portfolio
                shocked_portfolio = self._apply_scenario_shocks(
                    portfolio, scenario_params
                )
                
                # Calculate impact metrics
                impact = {
                    'portfolio_loss': shocked_portfolio['total_loss'],
                    'funding_ratio_impact': shocked_portfolio['funding_impact'],
                    'duration_mismatch': shocked_portfolio['duration_impact'],
                    'liquidity_impact': shocked_portfolio['liquidity_impact'],
                    'margin_calls': shocked_portfolio['margin_requirement'],
                    'recovery_time_estimate': shocked_portfolio['recovery_months']
                }
                
                results[scenario] = impact
            
            # Calculate aggregate risk metrics
            worst_case = min(r['portfolio_loss'] for r in results.values())
            expected_shortfall = np.mean([
                r['portfolio_loss'] for r in results.values() 
                if r['portfolio_loss'] < np.percentile(
                    [r['portfolio_loss'] for r in results.values()], 5
                )
            ])
            
            # Generate recommendations
            recommendations = self._generate_stress_recommendations(results)
            
            return {
                'scenario_results': results,
                'risk_metrics': {
                    'worst_case_loss': worst_case,
                    'expected_shortfall_95': expected_shortfall,
                    'max_funding_ratio_decline': min(
                        r['funding_ratio_impact'] for r in results.values()
                    ),
                    'liquidity_coverage_ratio': self._calculate_lcr(
                        portfolio, results
                    )
                },
                'vulnerable_positions': self._identify_vulnerable_positions(
                    portfolio, results
                ),
                'hedging_recommendations': recommendations['hedging'],
                'rebalancing_suggestions': recommendations['rebalancing'],
                'contingency_plans': self._create_contingency_plans(results)
            }
            
        except Exception as e:
            logger.error(f"Portfolio stress testing failed: {str(e)}")
            raise
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_portfolio_duration(self, assets: Dict[str, float]) -> float:
        """Calculate weighted average duration of portfolio"""
        total_value = sum(assets.values())
        if total_value == 0:
            return 0
        
        weighted_duration = 0
        for asset_name, value in assets.items():
            if asset_name in self.asset_classes:
                asset = self.asset_classes[asset_name]
                weighted_duration += (value / total_value) * asset.duration
        
        return weighted_duration
    
    def _create_glide_path(
        self, 
        current_funding: float,
        target_funding: float,
        years: int
    ) -> List[Dict[str, float]]:
        """Create de-risking glide path"""
        glide_path = []
        
        for year in range(years + 1):
            progress = year / years
            
            # Funding ratio projection
            projected_funding = current_funding + (target_funding - current_funding) * progress
            
            # Risk allocation based on funding
            if projected_funding < 0.9:
                equity_weight = 0.6
            elif projected_funding < 1.0:
                equity_weight = 0.5 - 0.2 * (projected_funding - 0.9) / 0.1
            else:
                equity_weight = 0.3 - 0.1 * min((projected_funding - 1.0) / 0.1, 1)
            
            glide_path.append({
                'year': year,
                'funding_ratio': projected_funding,
                'equity': equity_weight,
                'fixed_income': 1 - equity_weight - 0.1,
                'alternatives': 0.1
            })
        
        return glide_path
    
    async def _cash_flow_matching(
        self,
        liabilities: List[Liability],
        assets: Dict[str, float]
    ) -> Dict[str, Any]:
        """Match asset cash flows to liability payments"""
        # Aggregate liability cash flows
        cash_flow_schedule = {}
        for liability in liabilities:
            for date_str, amount in liability.payment_schedule:
                if date_str in cash_flow_schedule:
                    cash_flow_schedule[date_str] += amount
                else:
                    cash_flow_schedule[date_str] = amount
        
        # Sort by date
        sorted_dates = sorted(cash_flow_schedule.keys())
        
        # Calculate required bond ladder
        bond_ladder = []
        cumulative_cost = 0
        
        for date in sorted_dates:
            required_payment = cash_flow_schedule[date]
            # Find appropriate bond/asset
            maturity_years = (datetime.fromisoformat(date) - datetime.now()).days / 365
            
            # Calculate present value
            discount_rate = self.market_data['risk_free_rate'] + 0.01  # Add spread
            pv = required_payment / (1 + discount_rate) ** maturity_years
            
            bond_ladder.append({
                'maturity_date': date,
                'face_value': required_payment,
                'present_value': pv,
                'duration': maturity_years,
                'yield': discount_rate
            })
            
            cumulative_cost += pv
        
        return {
            'bond_ladder': bond_ladder,
            'total_cost': cumulative_cost,
            'cash_flow_schedule': cash_flow_schedule,
            'funding_gap': cumulative_cost - sum(assets.values()),
            'implementation': 'Use zero-coupon bonds or strips for precise matching'
        }
    
    def _stress_test_ldi(
        self,
        assets: float,
        liabilities: float,
        duration_gap: float
    ) -> Dict[str, float]:
        """Stress test LDI strategy"""
        scenarios = {
            'rates_up_100bps': {
                'asset_change': -duration_gap * 0.01 * assets,
                'liability_change': -duration_gap * 0.01 * liabilities
            },
            'rates_down_100bps': {
                'asset_change': duration_gap * 0.01 * assets,
                'liability_change': duration_gap * 0.01 * liabilities
            },
            'equity_down_20pct': {
                'asset_change': -0.20 * assets * 0.4,  # Assuming 40% equity
                'liability_change': 0
            },
            'credit_spread_widening': {
                'asset_change': -0.05 * assets * 0.3,  # Assuming 30% credit
                'liability_change': 0
            }
        }
        
        results = {}
        for scenario, impacts in scenarios.items():
            new_assets = assets + impacts['asset_change']
            new_liabilities = liabilities + impacts['liability_change']
            results[scenario] = new_assets / new_liabilities
        
        return results
    
    def _calculate_required_return(
        self,
        funding_gap: float,
        assets: float,
        years: int
    ) -> float:
        """Calculate required return to close funding gap"""
        if funding_gap <= 0:
            return self.market_data['risk_free_rate']
        
        target_value = assets + funding_gap
        required_return = (target_value / assets) ** (1 / years) - 1
        
        return required_return
    
    def _get_hedging_instruments(
        self,
        duration_gap: float,
        notional: float
    ) -> List[str]:
        """Recommend appropriate hedging instruments"""
        instruments = []
        
        if abs(duration_gap) > 2:
            instruments.append("Interest rate swaps")
            instruments.append("Treasury futures")
        
        if abs(duration_gap) > 5:
            instruments.append("Swaptions for convexity management")
        
        if notional > 100_000_000:
            instruments.append("Structured notes")
            instruments.append("Total return swaps")
        
        return instruments
    
    def _prioritize_actions(
        self,
        funding_ratio: float,
        duration_gap: float
    ) -> List[str]:
        """Prioritize implementation actions"""
        actions = []
        
        if funding_ratio < 0.8:
            actions.append("1. Increase return-seeking assets")
            actions.append("2. Consider liability restructuring")
        
        if abs(duration_gap) > 2:
            actions.append("3. Implement duration hedging immediately")
        
        if funding_ratio > 1.1:
            actions.append("4. Begin de-risking process")
            actions.append("5. Lock in funding gains")
        
        return actions
    
    def _build_correlation_matrix(self, assets: Dict[str, AssetClass]) -> np.ndarray:
        """Build correlation matrix for assets"""
        n = len(assets)
        corr_matrix = np.eye(n)
        
        # Default correlations (simplified)
        asset_list = list(assets.values())
        for i in range(n):
            for j in range(i+1, n):
                # Simple correlation model
                if 'equity' in asset_list[i].name.lower() and 'equity' in asset_list[j].name.lower():
                    corr_matrix[i, j] = corr_matrix[j, i] = 0.8
                elif 'bond' in asset_list[i].name.lower() and 'bond' in asset_list[j].name.lower():
                    corr_matrix[i, j] = corr_matrix[j, i] = 0.6
                elif 'equity' in asset_list[i].name.lower() and 'bond' in asset_list[j].name.lower():
                    corr_matrix[i, j] = corr_matrix[j, i] = -0.2
                else:
                    corr_matrix[i, j] = corr_matrix[j, i] = 0.3
        
        return corr_matrix
    
    def _solve_risk_parity(
        self,
        cov_matrix: np.ndarray,
        risk_budgets: np.ndarray
    ) -> np.ndarray:
        """Solve for risk parity weights"""
        n = len(risk_budgets)
        
        def objective(weights):
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            risk_contrib = weights * marginal_contrib
            
            # Minimize squared deviations from target risk budgets
            return np.sum((risk_contrib - risk_budgets * portfolio_vol) ** 2)
        
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}]
        bounds = [(0.01, 0.5) for _ in range(n)]
        
        result = optimize.minimize(
            objective,
            np.ones(n) / n,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return result.x
    
    async def _execute_vwap(
        self,
        order: ExecutionOrder,
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute using VWAP algorithm"""
        # Simulate VWAP execution
        volume_profile = market_conditions.get('intraday_volume', self._default_volume_profile())
        
        # Slice order based on historical volume
        slices = []
        remaining = order.quantity
        
        for hour, volume_pct in volume_profile.items():
            slice_size = min(remaining, order.quantity * volume_pct)
            slices.append({
                'time': hour,
                'quantity': slice_size,
                'target_participation': min(order.participation_rate, 0.25)
            })
            remaining -= slice_size
        
        # Simulate execution
        executed_slices = []
        total_cost = 0
        
        for slice_data in slices:
            # Add market impact
            impact = self._calculate_slice_impact(slice_data, market_conditions)
            execution_price = market_conditions.get('current_price', 100) * (1 + impact)
            
            executed_slices.append({
                'time': slice_data['time'],
                'quantity': slice_data['quantity'],
                'price': execution_price
            })
            
            total_cost += slice_data['quantity'] * execution_price
        
        return {
            'algorithm': 'VWAP',
            'average_price': total_cost / order.quantity,
            'slices': executed_slices,
            'actual_participation': order.participation_rate,
            'fill_rate': 1.0
        }
    
    def _calculate_transaction_costs(
        self,
        order: ExecutionOrder,
        execution_result: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> TransactionCost:
        """Calculate detailed transaction costs"""
        
        benchmark_price = market_conditions.get('arrival_price', 100)
        execution_price = execution_result['average_price']
        
        # Spread cost (half spread)
        spread = market_conditions.get('spread', 0.01)
        spread_cost = order.quantity * benchmark_price * spread / 2
        
        # Market impact (temporary + permanent)
        volatility = market_conditions.get('volatility', 0.20)
        daily_volume = market_conditions.get('daily_volume', 1000000)
        
        # Simplified Almgren-Chriss model
        participation = order.quantity / daily_volume
        temp_impact = 0.1 * volatility * np.sqrt(participation)
        perm_impact = 0.01 * participation
        
        market_impact = order.quantity * benchmark_price * (temp_impact + perm_impact)
        
        # Delay cost
        time_to_start = (order.start_time - datetime.now()).seconds / 3600
        drift = market_conditions.get('drift', 0.08) / 252 / 8  # Hourly drift
        delay_cost = order.quantity * benchmark_price * drift * time_to_start
        
        # Opportunity cost (unfilled portion)
        fill_rate = execution_result.get('fill_rate', 1.0)
        if order.side == 'buy':
            opp_cost = (1 - fill_rate) * order.quantity * max(0, market_conditions.get('close_price', 100) - benchmark_price)
        else:
            opp_cost = (1 - fill_rate) * order.quantity * max(0, benchmark_price - market_conditions.get('close_price', 100))
        
        total_cost = spread_cost + market_impact + delay_cost + opp_cost
        
        return TransactionCost(
            spread_cost=spread_cost,
            market_impact=market_impact,
            delay_cost=delay_cost,
            opportunity_cost=opp_cost,
            total_cost=total_cost,
            cost_basis_points=total_cost / (order.quantity * benchmark_price) * 10000,
            implementation_shortfall=(execution_price - benchmark_price) * order.quantity,
            execution_price=execution_price,
            benchmark_price=benchmark_price,
            side=order.side
        )
    
    def _default_volume_profile(self) -> Dict[int, float]:
        """Default intraday volume profile"""
        return {
            9: 0.15,   # 9:30-10:30
            10: 0.12,  # 10:30-11:30
            11: 0.10,  # 11:30-12:30
            12: 0.08,  # 12:30-13:30
            13: 0.10,  # 13:30-14:30
            14: 0.15,  # 14:30-15:30
            15: 0.30   # 15:30-16:00 (close)
        }
    
    def _calculate_slice_impact(
        self,
        slice_data: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> float:
        """Calculate market impact for order slice"""
        # Simplified square-root model
        participation = slice_data['target_participation']
        volatility = market_conditions.get('volatility', 0.20)
        
        # Temporary impact
        temp_impact = 0.1 * volatility * np.sqrt(participation)
        
        # Permanent impact
        perm_impact = 0.05 * participation
        
        return temp_impact + perm_impact


# ============================================================================
# PENSION FUND MANAGER
# ============================================================================

class PensionFundManager:
    """
    Specialized manager for defined benefit pension funds with funding ratio
    projections and regulatory compliance.
    """
    
    def __init__(self, portfolio_manager: InstitutionalPortfolioManager):
        self.portfolio_manager = portfolio_manager
        self.regulatory_requirements = {
            'min_funding_ratio': 0.80,
            'target_funding_ratio': 1.05,
            'pbgc_premium_threshold': 0.80,
            'erisa_compliance': True
        }
        logger.info("Pension Fund Manager initialized")
    
    async def project_funding_ratio(
        self,
        current_assets: float,
        current_liabilities: float,
        participant_data: Dict[str, Any],
        economic_assumptions: Dict[str, float],
        years: int = 30
    ) -> Dict[str, Any]:
        """
        Project pension funding ratio with stochastic modeling.
        
        Args:
            current_assets: Current plan assets
            current_liabilities: Current PBO (Projected Benefit Obligation)
            participant_data: Demographics and benefit information
            economic_assumptions: Discount rate, salary growth, etc.
            years: Projection period
            
        Returns:
            Funding ratio projections with confidence intervals
        """
        try:
            # Initialize projection arrays
            n_scenarios = 10000
            asset_paths = np.zeros((n_scenarios, years + 1))
            liability_paths = np.zeros((n_scenarios, years + 1))
            
            # Set initial values
            asset_paths[:, 0] = current_assets
            liability_paths[:, 0] = current_liabilities
            
            # Economic parameters
            expected_return = economic_assumptions.get('expected_return', 0.07)
            volatility = economic_assumptions.get('volatility', 0.15)
            discount_rate = economic_assumptions.get('discount_rate', 0.045)
            salary_growth = economic_assumptions.get('salary_growth', 0.03)
            
            # Simulate paths
            for year in range(1, years + 1):
                # Asset returns (geometric Brownian motion)
                returns = np.random.normal(expected_return, volatility, n_scenarios)
                asset_paths[:, year] = asset_paths[:, year-1] * (1 + returns)
                
                # Add contributions
                contributions = self._calculate_contributions(
                    participant_data, year, salary_growth
                )
                asset_paths[:, year] += contributions
                
                # Subtract benefit payments
                benefits = self._calculate_benefits(participant_data, year)
                asset_paths[:, year] -= benefits
                
                # Liability growth
                liability_growth = discount_rate + self._calculate_service_cost(
                    participant_data, year, salary_growth
                )
                liability_paths[:, year] = liability_paths[:, year-1] * (1 + liability_growth)
                liability_paths[:, year] -= benefits  # Reduce for payments
            
            # Calculate funding ratios
            funding_ratios = asset_paths / liability_paths
            
            # Statistical analysis
            percentiles = [5, 25, 50, 75, 95]
            ratio_percentiles = np.percentile(funding_ratios, percentiles, axis=0)
            
            # Find probability of underfunding
            prob_underfunded = np.mean(funding_ratios < 0.80, axis=0)
            
            # Required contributions analysis
            required_contributions = self._calculate_required_contributions(
                funding_ratios, liability_paths, self.regulatory_requirements['target_funding_ratio']
            )
            
            return {
                'projection_years': list(range(years + 1)),
                'funding_ratio_percentiles': {
                    f'p{p}': ratio_percentiles[i].tolist()
                    for i, p in enumerate(percentiles)
                },
                'expected_funding_ratio': np.mean(funding_ratios, axis=0).tolist(),
                'probability_underfunded': prob_underfunded.tolist(),
                'required_annual_contribution': required_contributions,
                'regulatory_compliance': {
                    'meets_minimum': np.all(np.mean(funding_ratios, axis=0) >= self.regulatory_requirements['min_funding_ratio']),
                    'pbgc_variable_premium': self._calculate_pbgc_premium(funding_ratios[-1]),
                    'erisa_funding_notice_required': np.any(funding_ratios[-1] < 0.80)
                },
                'risk_metrics': {
                    'funding_ratio_volatility': np.std(funding_ratios[-1]),
                    'worst_case_scenario': np.percentile(funding_ratios[-1], 1),
                    'tail_risk': np.mean(funding_ratios[-1][funding_ratios[-1] < np.percentile(funding_ratios[-1], 5)])
                },
                'recommendations': self._generate_funding_recommendations(
                    funding_ratios, asset_paths, liability_paths
                )
            }
            
        except Exception as e:
            logger.error(f"Funding ratio projection failed: {str(e)}")
            raise
    
    def _calculate_contributions(
        self,
        participant_data: Dict[str, Any],
        year: int,
        salary_growth: float
    ) -> float:
        """Calculate expected contributions"""
        active_participants = participant_data.get('active_count', 10000)
        avg_salary = participant_data.get('avg_salary', 75000) * (1 + salary_growth) ** year
        contribution_rate = participant_data.get('contribution_rate', 0.10)
        
        return active_participants * avg_salary * contribution_rate
    
    def _calculate_benefits(
        self,
        participant_data: Dict[str, Any],
        year: int
    ) -> float:
        """Calculate expected benefit payments"""
        retirees = participant_data.get('retiree_count', 5000)
        avg_benefit = participant_data.get('avg_benefit', 30000)
        cola = participant_data.get('cola', 0.02)
        
        return retirees * avg_benefit * (1 + cola) ** year
    
    def _calculate_service_cost(
        self,
        participant_data: Dict[str, Any],
        year: int,
        salary_growth: float
    ) -> float:
        """Calculate service cost as percentage of liabilities"""
        active_participants = participant_data.get('active_count', 10000)
        avg_service_cost_rate = 0.015  # 1.5% of liabilities
        
        # Adjust for workforce changes
        workforce_growth = participant_data.get('workforce_growth', 0)
        adjusted_participants = active_participants * (1 + workforce_growth) ** year
        
        return avg_service_cost_rate * (adjusted_participants / active_participants)
    
    def _calculate_required_contributions(
        self,
        funding_ratios: np.ndarray,
        liability_paths: np.ndarray,
        target_ratio: float
    ) -> Dict[str, float]:
        """Calculate required contributions to meet target funding"""
        years_analyzed = [1, 3, 5, 7, 10]
        required = {}
        
        for year in years_analyzed:
            if year < len(funding_ratios[0]):
                current_ratio = np.mean(funding_ratios[:, year])
                if current_ratio < target_ratio:
                    gap = (target_ratio - current_ratio) * np.mean(liability_paths[:, year])
                    annual_contribution = gap / year
                    required[f'year_{year}'] = annual_contribution
                else:
                    required[f'year_{year}'] = 0
        
        return required
    
    def _calculate_pbgc_premium(self, final_funding_ratios: np.ndarray) -> float:
        """Calculate PBGC variable rate premium"""
        avg_funding = np.mean(final_funding_ratios)
        
        if avg_funding >= 1.0:
            return 0
        
        # Simplified PBGC calculation
        unfunded_per_participant = max(0, (1 - avg_funding) * 500000)  # Assume $500k per participant
        variable_rate = 0.052  # 5.2% for 2024
        
        return unfunded_per_participant * variable_rate
    
    def _generate_funding_recommendations(
        self,
        funding_ratios: np.ndarray,
        asset_paths: np.ndarray,
        liability_paths: np.ndarray
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        current_ratio = funding_ratios[:, 0].mean()
        final_ratio = funding_ratios[:, -1].mean()
        
        if current_ratio < 0.80:
            recommendations.append("URGENT: Implement recovery plan - funding below 80%")
            recommendations.append("Consider pension risk transfer for select participants")
            recommendations.append("Evaluate lump sum windows to reduce liabilities")
        
        if final_ratio < current_ratio:
            recommendations.append("Funding deteriorating - increase contributions or adjust strategy")
        
        volatility = np.std(funding_ratios[:, -1])
        if volatility > 0.15:
            recommendations.append("High funding volatility - implement LDI strategy")
            recommendations.append("Consider longevity hedging instruments")
        
        if current_ratio > 1.10:
            recommendations.append("Well-funded status - begin de-risking glide path")
            recommendations.append("Lock in gains with duration-matched bonds")
        
        return recommendations