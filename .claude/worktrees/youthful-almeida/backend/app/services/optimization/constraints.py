"""
Advanced Portfolio Constraints Management
Handles complex constraints for portfolio optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import cvxpy as cp
from datetime import datetime


class ConstraintType(Enum):
    """Types of portfolio constraints"""
    LINEAR = "linear"
    QUADRATIC = "quadratic"
    CONIC = "conic"
    INTEGER = "integer"
    LOGICAL = "logical"
    CUSTOM = "custom"


class ConstraintPriority(Enum):
    """Priority levels for constraint satisfaction"""
    HARD = 1  # Must be satisfied
    SOFT = 2  # Should be satisfied if possible
    PREFERENCE = 3  # Nice to have


@dataclass
class RegulatoryConstraints:
    """Regulatory and compliance constraints"""
    ucits_compliant: bool = False  # UCITS diversification rules
    erisa_compliant: bool = False  # ERISA prudent investor rules
    mifid_compliant: bool = False  # MiFID suitability rules
    
    # Concentration limits
    single_issuer_limit: float = 0.1  # 10% single issuer limit
    five_percent_basket_limit: float = 0.4  # 40% in 5%+ positions (5/10/40 rule)
    
    # Derivatives and leverage
    max_derivatives_exposure: float = 0.1
    max_leverage: float = 1.0
    
    # Liquidity requirements
    min_liquid_assets: float = 0.85  # 85% in liquid assets
    max_illiquid_assets: float = 0.15
    

@dataclass
class LiquidityConstraints:
    """Liquidity-related constraints"""
    min_daily_volume: float = 1000000  # Minimum daily trading volume
    max_position_vs_adv: float = 0.1  # Max position as % of ADV
    max_market_impact: float = 0.01  # Max acceptable market impact
    min_liquidity_score: float = 0.7
    liquidation_horizon: int = 10  # Days to liquidate position
    

@dataclass
class RiskConstraints:
    """Risk-related constraints"""
    # Volatility constraints
    max_volatility: float = 0.15  # 15% annual volatility
    min_volatility: Optional[float] = None
    
    # Drawdown constraints
    max_drawdown: float = 0.2  # 20% maximum drawdown
    max_consecutive_losses: int = 5
    
    # Value at Risk
    max_var_95: float = 0.05  # 5% VaR at 95% confidence
    max_cvar_95: float = 0.075  # 7.5% CVaR at 95% confidence
    
    # Beta and correlation
    max_beta: float = 1.2
    min_beta: Optional[float] = None
    max_correlation_to_benchmark: float = 0.95
    
    # Tracking error
    max_tracking_error: float = 0.05
    
    # Factor exposures
    factor_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    

@dataclass
class ESGConstraints:
    """Environmental, Social, and Governance constraints"""
    min_esg_score: float = 0.5
    exclude_sectors: List[str] = field(default_factory=list)  # e.g., ['tobacco', 'weapons']
    exclude_countries: List[str] = field(default_factory=list)
    
    # Carbon footprint
    max_carbon_intensity: Optional[float] = None
    
    # Social factors
    min_diversity_score: Optional[float] = None
    exclude_child_labor: bool = True
    
    # Governance
    min_governance_score: Optional[float] = None
    require_independent_board: bool = False
    

@dataclass
class TaxConstraints:
    """Tax-related constraints"""
    max_turnover: float = 0.5  # Maximum annual turnover
    min_holding_period: int = 365  # Days for long-term capital gains
    max_realized_gains: Optional[float] = None
    harvest_losses: bool = True
    max_wash_sale_risk: float = 0.1
    

@dataclass
class CustomConstraint:
    """Custom user-defined constraint"""
    name: str
    constraint_function: Callable
    priority: ConstraintPriority = ConstraintPriority.HARD
    parameters: Dict[str, Any] = field(default_factory=dict)


class ConstraintManager:
    """
    Manages and validates portfolio constraints
    """
    
    def __init__(self):
        self.constraints = []
        self.soft_constraints = []
        self.validation_errors = []
        
    def add_regulatory_constraints(
        self,
        regulatory: RegulatoryConstraints
    ) -> None:
        """Add regulatory compliance constraints"""
        if regulatory.ucits_compliant:
            self._add_ucits_constraints()
        if regulatory.erisa_compliant:
            self._add_erisa_constraints()
        if regulatory.mifid_compliant:
            self._add_mifid_constraints()
            
        # Concentration limits
        self.constraints.append({
            'type': 'concentration',
            'single_issuer_limit': regulatory.single_issuer_limit,
            'five_percent_basket_limit': regulatory.five_percent_basket_limit
        })
        
    def add_liquidity_constraints(
        self,
        liquidity: LiquidityConstraints,
        market_data: pd.DataFrame
    ) -> None:
        """Add liquidity constraints"""
        # Filter assets by minimum daily volume
        liquid_assets = market_data[
            market_data['daily_volume'] >= liquidity.min_daily_volume
        ].index.tolist()
        
        self.constraints.append({
            'type': 'liquidity',
            'eligible_assets': liquid_assets,
            'max_position_vs_adv': liquidity.max_position_vs_adv,
            'liquidation_horizon': liquidity.liquidation_horizon
        })
        
    def add_risk_constraints(
        self,
        risk: RiskConstraints,
        covariance_matrix: np.ndarray,
        factor_loadings: Optional[pd.DataFrame] = None
    ) -> None:
        """Add risk management constraints"""
        # Volatility constraint
        if risk.max_volatility:
            self.constraints.append({
                'type': 'volatility',
                'max': risk.max_volatility,
                'covariance': covariance_matrix
            })
            
        # VaR and CVaR constraints
        if risk.max_var_95:
            self.constraints.append({
                'type': 'var',
                'confidence_level': 0.95,
                'max_var': risk.max_var_95
            })
            
        # Factor exposure constraints
        if factor_loadings is not None and risk.factor_limits:
            for factor, (min_exp, max_exp) in risk.factor_limits.items():
                if factor in factor_loadings.columns:
                    self.constraints.append({
                        'type': 'factor_exposure',
                        'factor': factor,
                        'loadings': factor_loadings[factor].values,
                        'min': min_exp,
                        'max': max_exp
                    })
                    
    def add_esg_constraints(
        self,
        esg: ESGConstraints,
        asset_data: pd.DataFrame
    ) -> None:
        """Add ESG constraints"""
        # ESG score constraint
        if esg.min_esg_score and 'esg_score' in asset_data.columns:
            self.constraints.append({
                'type': 'esg_score',
                'scores': asset_data['esg_score'].values,
                'min_score': esg.min_esg_score
            })
            
        # Sector exclusions
        if esg.exclude_sectors:
            excluded_assets = asset_data[
                asset_data['sector'].isin(esg.exclude_sectors)
            ].index.tolist()
            
            self.constraints.append({
                'type': 'exclusion',
                'excluded_assets': excluded_assets
            })
            
        # Carbon intensity constraint
        if esg.max_carbon_intensity and 'carbon_intensity' in asset_data.columns:
            self.constraints.append({
                'type': 'carbon',
                'intensities': asset_data['carbon_intensity'].values,
                'max_intensity': esg.max_carbon_intensity
            })
            
    def add_custom_constraint(
        self,
        constraint: CustomConstraint
    ) -> None:
        """Add custom constraint"""
        if constraint.priority == ConstraintPriority.HARD:
            self.constraints.append({
                'type': 'custom',
                'name': constraint.name,
                'function': constraint.constraint_function,
                'parameters': constraint.parameters
            })
        else:
            self.soft_constraints.append({
                'type': 'custom',
                'name': constraint.name,
                'function': constraint.constraint_function,
                'parameters': constraint.parameters,
                'priority': constraint.priority
            })
            
    def build_cvxpy_constraints(
        self,
        weights: cp.Variable,
        n_assets: int
    ) -> Tuple[List, List]:
        """
        Build CVXPY constraint objects
        
        Returns:
            Tuple of (hard_constraints, soft_constraints)
        """
        hard_constraints = []
        soft_constraints = []
        
        for constraint in self.constraints:
            cvxpy_constraint = self._convert_to_cvxpy(constraint, weights, n_assets)
            if cvxpy_constraint:
                hard_constraints.extend(cvxpy_constraint)
                
        for constraint in self.soft_constraints:
            cvxpy_constraint = self._convert_to_cvxpy(constraint, weights, n_assets)
            if cvxpy_constraint:
                soft_constraints.extend(cvxpy_constraint)
                
        return hard_constraints, soft_constraints
    
    def validate_portfolio(
        self,
        weights: np.ndarray,
        asset_data: pd.DataFrame,
        returns_data: Optional[pd.DataFrame] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate portfolio against all constraints
        
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        for constraint in self.constraints:
            is_satisfied, violation_msg = self._check_constraint(
                constraint, weights, asset_data, returns_data
            )
            if not is_satisfied:
                violations.append(violation_msg)
                
        return len(violations) == 0, violations
    
    def get_feasible_region(
        self,
        n_assets: int,
        granularity: int = 100
    ) -> np.ndarray:
        """
        Estimate the feasible region for portfolio weights
        
        Returns:
            Array of feasible weight combinations
        """
        # This is a simplified version - actual implementation would be more complex
        feasible_weights = []
        
        # Generate grid of weights
        for i in range(granularity):
            weights = np.random.dirichlet(np.ones(n_assets))
            
            # Check if weights satisfy constraints
            is_valid = True
            for constraint in self.constraints:
                if constraint['type'] == 'concentration':
                    if np.max(weights) > constraint['single_issuer_limit']:
                        is_valid = False
                        break
                        
            if is_valid:
                feasible_weights.append(weights)
                
        return np.array(feasible_weights)
    
    def relax_constraints(
        self,
        infeasible_constraints: List[str],
        relaxation_factor: float = 0.1
    ) -> None:
        """
        Relax constraints that make problem infeasible
        
        Args:
            infeasible_constraints: List of constraint names to relax
            relaxation_factor: How much to relax (0-1)
        """
        for constraint in self.constraints:
            if constraint.get('name') in infeasible_constraints:
                # Relax based on type
                if constraint['type'] == 'volatility':
                    constraint['max'] *= (1 + relaxation_factor)
                elif constraint['type'] == 'concentration':
                    constraint['single_issuer_limit'] *= (1 + relaxation_factor)
                elif constraint['type'] == 'esg_score':
                    constraint['min_score'] *= (1 - relaxation_factor)
                    
    def _add_ucits_constraints(self) -> None:
        """Add UCITS diversification rules"""
        # 5/10/40 rule
        self.constraints.append({
            'type': 'ucits_5_10_40',
            'name': 'UCITS 5/10/40 Rule',
            'max_single_position': 0.1,  # 10% max single position
            'max_large_positions': 0.4,  # 40% max in 5%+ positions
            'large_position_threshold': 0.05
        })
        
        # Minimum diversification
        self.constraints.append({
            'type': 'min_positions',
            'name': 'UCITS Minimum Diversification',
            'min_positions': 16  # Implied by 5/10/40 rule
        })
        
    def _add_erisa_constraints(self) -> None:
        """Add ERISA prudent investor rules"""
        self.constraints.append({
            'type': 'diversification',
            'name': 'ERISA Prudent Diversification',
            'max_sector_concentration': 0.25,
            'max_single_stock': 0.05
        })
        
    def _add_mifid_constraints(self) -> None:
        """Add MiFID suitability rules"""
        self.constraints.append({
            'type': 'suitability',
            'name': 'MiFID Suitability',
            'require_liquidity_assessment': True,
            'require_risk_assessment': True
        })
        
    def _convert_to_cvxpy(
        self,
        constraint: Dict,
        weights: cp.Variable,
        n_assets: int
    ) -> List:
        """Convert constraint to CVXPY format"""
        cvxpy_constraints = []
        
        if constraint['type'] == 'concentration':
            cvxpy_constraints.append(
                weights <= constraint['single_issuer_limit']
            )
            
        elif constraint['type'] == 'volatility':
            portfolio_variance = cp.quad_form(weights, constraint['covariance'])
            cvxpy_constraints.append(
                portfolio_variance <= constraint['max'] ** 2
            )
            
        elif constraint['type'] == 'esg_score':
            portfolio_esg = constraint['scores'] @ weights
            cvxpy_constraints.append(
                portfolio_esg >= constraint['min_score']
            )
            
        elif constraint['type'] == 'exclusion':
            for excluded_idx in constraint['excluded_assets']:
                if excluded_idx < n_assets:
                    cvxpy_constraints.append(weights[excluded_idx] == 0)
                    
        elif constraint['type'] == 'factor_exposure':
            factor_exposure = constraint['loadings'] @ weights
            cvxpy_constraints.append(factor_exposure >= constraint['min'])
            cvxpy_constraints.append(factor_exposure <= constraint['max'])
            
        elif constraint['type'] == 'custom':
            # Custom constraints need special handling
            custom_constraint = constraint['function'](
                weights, **constraint['parameters']
            )
            if custom_constraint is not None:
                cvxpy_constraints.append(custom_constraint)
                
        return cvxpy_constraints
    
    def _check_constraint(
        self,
        constraint: Dict,
        weights: np.ndarray,
        asset_data: pd.DataFrame,
        returns_data: Optional[pd.DataFrame]
    ) -> Tuple[bool, str]:
        """Check if constraint is satisfied"""
        
        if constraint['type'] == 'concentration':
            max_weight = np.max(weights)
            if max_weight > constraint['single_issuer_limit']:
                return False, f"Position size {max_weight:.2%} exceeds limit {constraint['single_issuer_limit']:.2%}"
                
        elif constraint['type'] == 'volatility':
            portfolio_variance = weights @ constraint['covariance'] @ weights
            portfolio_vol = np.sqrt(portfolio_variance)
            if portfolio_vol > constraint['max']:
                return False, f"Portfolio volatility {portfolio_vol:.2%} exceeds limit {constraint['max']:.2%}"
                
        elif constraint['type'] == 'esg_score':
            portfolio_esg = np.sum(weights * constraint['scores'])
            if portfolio_esg < constraint['min_score']:
                return False, f"Portfolio ESG score {portfolio_esg:.2f} below minimum {constraint['min_score']:.2f}"
                
        return True, ""


class ConstraintSensitivityAnalyzer:
    """
    Analyze sensitivity of optimal portfolio to constraint changes
    """
    
    def __init__(self, optimizer):
        self.optimizer = optimizer
        
    def analyze_constraint_sensitivity(
        self,
        base_constraints: Dict,
        constraint_name: str,
        perturbation_range: np.ndarray,
        asset_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Analyze how portfolio changes with constraint perturbation
        
        Returns:
            DataFrame with sensitivity analysis results
        """
        results = []
        
        for perturbation in perturbation_range:
            # Modify constraint
            modified_constraints = base_constraints.copy()
            modified_constraints[constraint_name] *= (1 + perturbation)
            
            # Re-optimize
            try:
                optimal_weights = self.optimizer.optimize(
                    asset_data, 
                    constraints=modified_constraints
                )
                
                # Calculate metrics
                results.append({
                    'perturbation': perturbation,
                    'constraint_value': modified_constraints[constraint_name],
                    'portfolio_return': self._calculate_return(optimal_weights, asset_data),
                    'portfolio_risk': self._calculate_risk(optimal_weights, asset_data),
                    'max_weight': np.max(optimal_weights),
                    'effective_assets': np.sum(optimal_weights > 0.01)
                })
            except:
                # Constraint made problem infeasible
                results.append({
                    'perturbation': perturbation,
                    'constraint_value': modified_constraints[constraint_name],
                    'feasible': False
                })
                
        return pd.DataFrame(results)
    
    def find_binding_constraints(
        self,
        optimal_weights: np.ndarray,
        constraints: List[Dict],
        tolerance: float = 1e-6
    ) -> List[str]:
        """
        Identify which constraints are binding at the optimal solution
        
        Returns:
            List of binding constraint names
        """
        binding_constraints = []
        
        for constraint in constraints:
            # Check if constraint is active (at the boundary)
            if self._is_constraint_binding(
                constraint, 
                optimal_weights, 
                tolerance
            ):
                binding_constraints.append(
                    constraint.get('name', constraint['type'])
                )
                
        return binding_constraints
    
    def calculate_shadow_prices(
        self,
        optimal_weights: np.ndarray,
        constraints: List[Dict],
        asset_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate shadow prices (marginal value) of constraints
        
        Returns:
            Dictionary of constraint names to shadow prices
        """
        shadow_prices = {}
        epsilon = 1e-4
        
        base_objective = self._calculate_objective(optimal_weights, asset_data)
        
        for constraint in constraints:
            if self._is_constraint_binding(constraint, optimal_weights):
                # Relax constraint slightly and re-optimize
                relaxed_constraint = constraint.copy()
                relaxed_constraint['value'] *= (1 + epsilon)
                
                # Re-optimize with relaxed constraint
                relaxed_weights = self.optimizer.optimize(
                    asset_data,
                    constraints=[relaxed_constraint] + [c for c in constraints if c != constraint]
                )
                
                relaxed_objective = self._calculate_objective(relaxed_weights, asset_data)
                
                # Shadow price is change in objective per unit change in constraint
                shadow_price = (relaxed_objective - base_objective) / (epsilon * constraint['value'])
                shadow_prices[constraint.get('name', constraint['type'])] = shadow_price
                
        return shadow_prices
    
    def _calculate_return(self, weights: np.ndarray, asset_data: pd.DataFrame) -> float:
        """Calculate portfolio return"""
        return np.sum(weights * asset_data['expected_return'].values)
    
    def _calculate_risk(self, weights: np.ndarray, asset_data: pd.DataFrame) -> float:
        """Calculate portfolio risk"""
        cov_matrix = asset_data[['returns']].cov().values
        return np.sqrt(weights @ cov_matrix @ weights)
    
    def _calculate_objective(self, weights: np.ndarray, asset_data: pd.DataFrame) -> float:
        """Calculate objective value (e.g., Sharpe ratio)"""
        return_val = self._calculate_return(weights, asset_data)
        risk_val = self._calculate_risk(weights, asset_data)
        return (return_val - 0.02) / risk_val  # Sharpe ratio with 2% risk-free rate
    
    def _is_constraint_binding(
        self,
        constraint: Dict,
        weights: np.ndarray,
        tolerance: float = 1e-6
    ) -> bool:
        """Check if constraint is binding"""
        if constraint['type'] == 'concentration':
            return abs(np.max(weights) - constraint['single_issuer_limit']) < tolerance
        elif constraint['type'] == 'volatility':
            portfolio_vol = np.sqrt(weights @ constraint['covariance'] @ weights)
            return abs(portfolio_vol - constraint['max']) < tolerance
        return False