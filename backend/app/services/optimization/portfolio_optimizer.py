"""
Comprehensive Portfolio Optimization Engine
Integrates multiple optimization strategies with real-world constraints
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
import cvxpy as cp
from scipy import stats, optimize
from scipy.cluster.hierarchy import linkage, fcluster
from datetime import datetime, timedelta
import warnings
from enum import Enum

# Import other optimization modules
from .mpt import ModernPortfolioTheory, OptimizationConstraints, PortfolioMetrics
from .black_litterman import BlackLittermanModel, InvestorView, MarketData
from .rebalancing import TaxAwareRebalancer, TransactionCost, TaxRates, Holding


class OptimizationMethod(Enum):
    """Available optimization methods"""
    MEAN_VARIANCE = "mean_variance"
    MAX_SHARPE = "max_sharpe"
    MIN_VARIANCE = "min_variance"
    RISK_PARITY = "risk_parity"
    BLACK_LITTERMAN = "black_litterman"
    KELLY_CRITERION = "kelly_criterion"
    HRP = "hierarchical_risk_parity"
    MAX_DIVERSIFICATION = "max_diversification"
    CVaR = "conditional_value_at_risk"
    ROBUST = "robust_optimization"


@dataclass
class AssetData:
    """Comprehensive asset data structure"""
    symbol: str
    returns: pd.Series
    expected_return: float
    volatility: float
    sector: Optional[str] = None
    geography: Optional[str] = None
    asset_class: Optional[str] = None
    esg_score: Optional[float] = None
    liquidity_score: Optional[float] = None
    market_cap: Optional[float] = None
    

@dataclass
class PortfolioConstraints:
    """Extended portfolio constraints"""
    # Position limits
    max_position_size: float = 0.25
    min_position_size: float = 0.01
    max_positions: Optional[int] = None
    
    # Sector/Geography limits
    sector_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    geography_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    asset_class_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # ESG constraints
    min_esg_score: Optional[float] = None
    esg_tilt: float = 0.0  # ESG tilt factor (0-1)
    
    # Liquidity constraints
    min_liquidity_score: Optional[float] = None
    max_illiquid_allocation: float = 0.2
    
    # Risk constraints
    max_volatility: Optional[float] = None
    max_var_95: Optional[float] = None
    max_cvar_95: Optional[float] = None
    max_tracking_error: Optional[float] = None
    
    # Trading constraints
    max_turnover: float = 0.5
    min_trade_size: float = 100
    round_lots: bool = False
    
    # Other constraints
    allow_short_selling: bool = False
    leverage_limit: float = 1.0
    benchmark_weights: Optional[np.ndarray] = None


@dataclass
class OptimizationResult:
    """Comprehensive optimization result"""
    method: OptimizationMethod
    weights: Dict[str, float]
    metrics: PortfolioMetrics
    constraints_satisfied: bool
    optimization_info: Dict[str, Any]
    backtesting_metrics: Optional[Dict] = None
    risk_decomposition: Optional[Dict] = None
    factor_exposures: Optional[Dict] = None


class PortfolioOptimizer:
    """
    Master portfolio optimization engine combining multiple strategies
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.02,
        confidence_level: float = 0.95,
        estimation_window: int = 252
    ):
        self.risk_free_rate = risk_free_rate
        self.confidence_level = confidence_level
        self.estimation_window = estimation_window
        
        # Initialize sub-optimizers
        self.mpt_optimizer = ModernPortfolioTheory(risk_free_rate)
        self.black_litterman = BlackLittermanModel()
        self.rebalancer = TaxAwareRebalancer()
        
    def optimize(
        self,
        assets: List[AssetData],
        method: OptimizationMethod,
        constraints: Optional[PortfolioConstraints] = None,
        views: Optional[List[InvestorView]] = None,
        **kwargs
    ) -> OptimizationResult:
        """
        Main optimization interface
        
        Args:
            assets: List of asset data
            method: Optimization method to use
            constraints: Portfolio constraints
            views: Investor views for Black-Litterman
            **kwargs: Additional method-specific parameters
            
        Returns:
            Optimization result with weights and metrics
        """
        if constraints is None:
            constraints = PortfolioConstraints()
            
        # Prepare data
        returns_matrix, expected_returns, cov_matrix = self._prepare_data(assets)
        
        # Route to appropriate optimizer
        if method == OptimizationMethod.MEAN_VARIANCE:
            result = self._optimize_mean_variance(
                expected_returns, cov_matrix, constraints
            )
        elif method == OptimizationMethod.MAX_SHARPE:
            result = self._optimize_max_sharpe(
                expected_returns, cov_matrix, constraints
            )
        elif method == OptimizationMethod.MIN_VARIANCE:
            result = self._optimize_min_variance(cov_matrix, constraints)
        elif method == OptimizationMethod.RISK_PARITY:
            result = self._optimize_risk_parity(cov_matrix, constraints)
        elif method == OptimizationMethod.BLACK_LITTERMAN:
            result = self._optimize_black_litterman(
                assets, expected_returns, cov_matrix, views, constraints
            )
        elif method == OptimizationMethod.KELLY_CRITERION:
            result = self._optimize_kelly(
                expected_returns, cov_matrix, constraints, **kwargs
            )
        elif method == OptimizationMethod.HRP:
            result = self._optimize_hrp(returns_matrix, cov_matrix, constraints)
        elif method == OptimizationMethod.MAX_DIVERSIFICATION:
            result = self._optimize_max_diversification(cov_matrix, constraints)
        elif method == OptimizationMethod.CVaR:
            result = self._optimize_cvar(
                returns_matrix, constraints, **kwargs
            )
        elif method == OptimizationMethod.ROBUST:
            result = self._optimize_robust(
                expected_returns, cov_matrix, constraints, **kwargs
            )
        else:
            raise ValueError(f"Unknown optimization method: {method}")
            
        # Post-process results
        result = self._post_process_result(result, assets, returns_matrix)
        
        # Validate constraints
        result.constraints_satisfied = self._validate_constraints(
            result.weights, assets, constraints
        )
        
        return result
    
    def optimize_multi_objective(
        self,
        assets: List[AssetData],
        objectives: List[Tuple[str, float]],
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Multi-objective portfolio optimization
        
        Args:
            assets: List of asset data
            objectives: List of (objective, weight) tuples
            constraints: Portfolio constraints
            
        Returns:
            Pareto-optimal portfolio
        """
        if constraints is None:
            constraints = PortfolioConstraints()
            
        returns_matrix, expected_returns, cov_matrix = self._prepare_data(assets)
        n_assets = len(assets)
        
        # Decision variables
        weights = cp.Variable(n_assets)
        
        # Build composite objective
        objective_value = 0
        
        for obj_name, obj_weight in objectives:
            if obj_name == "return":
                objective_value += obj_weight * (expected_returns @ weights)
            elif obj_name == "risk":
                objective_value -= obj_weight * cp.quad_form(weights, cov_matrix)
            elif obj_name == "diversification":
                # Maximize effective number of assets
                objective_value += obj_weight * (-cp.sum(cp.square(weights)))
            elif obj_name == "esg":
                esg_scores = np.array([a.esg_score or 0 for a in assets])
                objective_value += obj_weight * (esg_scores @ weights)
            elif obj_name == "liquidity":
                liquidity_scores = np.array([a.liquidity_score or 1 for a in assets])
                objective_value += obj_weight * (liquidity_scores @ weights)
                
        # Constraints
        constraints_list = self._build_cvxpy_constraints(
            weights, assets, constraints
        )
        
        # Solve
        problem = cp.Problem(cp.Maximize(objective_value), constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        # Build result
        weight_dict = {
            asset.symbol: weights.value[i] 
            for i, asset in enumerate(assets)
            if weights.value[i] > 1e-6
        }
        
        metrics = self.mpt_optimizer.calculate_portfolio_metrics(
            weights.value, 
            pd.DataFrame(returns_matrix, columns=[a.symbol for a in assets]),
            expected_returns
        )
        
        return OptimizationResult(
            method=OptimizationMethod.MEAN_VARIANCE,
            weights=weight_dict,
            metrics=metrics,
            constraints_satisfied=True,
            optimization_info={"objectives": objectives}
        )
    
    def _optimize_mean_variance(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        """Mean-variance optimization"""
        n_assets = len(expected_returns)
        
        # Use CVXPY
        weights = cp.Variable(n_assets)
        
        # Target return (can be parameterized)
        target_return = np.mean(expected_returns)
        
        # Objective: minimize variance
        objective = cp.Minimize(cp.quad_form(weights, cov_matrix))
        
        # Constraints
        constraints_list = [
            cp.sum(weights) == 1,
            expected_returns @ weights >= target_return
        ]
        
        if not constraints.allow_short_selling:
            constraints_list.append(weights >= 0)
            
        if constraints.max_position_size:
            constraints_list.append(weights <= constraints.max_position_size)
            
        # Solve
        problem = cp.Problem(objective, constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        return self._create_result(
            OptimizationMethod.MEAN_VARIANCE,
            weights.value,
            expected_returns,
            cov_matrix
        )
    
    def _optimize_kelly(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints,
        kelly_fraction: float = 0.25
    ) -> OptimizationResult:
        """
        Kelly Criterion optimization
        
        The Kelly Criterion maximizes the expected log return of the portfolio
        """
        n_assets = len(expected_returns)
        
        def negative_log_utility(weights):
            """Negative expected log utility for minimization"""
            portfolio_return = weights @ expected_returns
            portfolio_variance = weights @ cov_matrix @ weights
            
            # Kelly utility: E[log(1 + R)] ≈ μ - σ²/2
            # Apply Kelly fraction for more conservative allocation
            utility = kelly_fraction * (
                portfolio_return - 0.5 * portfolio_variance
            )
            return -utility
        
        # Constraints for scipy
        scipy_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        if constraints.max_position_size:
            scipy_constraints.append({
                'type': 'ineq',
                'fun': lambda x: constraints.max_position_size - np.max(x)
            })
            
        # Bounds
        bounds = [(0, 1) for _ in range(n_assets)]
        if constraints.allow_short_selling:
            bounds = [(-1, 1) for _ in range(n_assets)]
            
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = optimize.minimize(
            negative_log_utility,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            warnings.warn("Kelly optimization did not converge")
            
        return self._create_result(
            OptimizationMethod.KELLY_CRITERION,
            result.x,
            expected_returns,
            cov_matrix,
            {"kelly_fraction": kelly_fraction}
        )
    
    def _optimize_hrp(
        self,
        returns_matrix: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        """
        Hierarchical Risk Parity optimization
        
        HRP uses hierarchical clustering to build a diversified portfolio
        without requiring expected returns estimation
        """
        n_assets = len(cov_matrix)
        
        # Step 1: Correlation matrix from covariance
        std_devs = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)
        
        # Step 2: Distance matrix
        distance_matrix = np.sqrt(0.5 * (1 - corr_matrix))
        
        # Step 3: Hierarchical clustering
        condensed_distance = distance_matrix[np.triu_indices(n_assets, k=1)]
        linkage_matrix = linkage(condensed_distance, method='single')
        
        # Step 4: Quasi-diagonalization (reorder correlation matrix)
        def get_quasi_diag_order(linkage_matrix):
            """Get quasi-diagonal ordering from linkage matrix"""
            n = linkage_matrix.shape[0] + 1
            order = []
            
            def recursive_order(node, linkage_matrix):
                if node < n:
                    return [node]
                else:
                    left = int(linkage_matrix[node - n, 0])
                    right = int(linkage_matrix[node - n, 1])
                    return recursive_order(left, linkage_matrix) + \
                           recursive_order(right, linkage_matrix)
            
            return recursive_order(2 * n - 2, linkage_matrix)
        
        ordered_indices = get_quasi_diag_order(linkage_matrix)
        
        # Step 5: Recursive bisection for weight allocation
        def recursive_bisection(covariance, indices):
            """Allocate weights using recursive bisection"""
            weights = pd.Series(1.0, index=indices)
            clusters = [indices]
            
            while len(clusters) > 0:
                # Pop a cluster
                cluster = clusters.pop()
                if len(cluster) > 1:
                    # Split into two sub-clusters
                    n_cluster = len(cluster)
                    sub_cov = covariance.loc[cluster, cluster]
                    
                    # Use inverse variance for initial allocation
                    inv_var = 1 / np.diag(sub_cov.values)
                    parity = inv_var / inv_var.sum()
                    
                    # Split at midpoint
                    split_idx = n_cluster // 2
                    left_cluster = cluster[:split_idx]
                    right_cluster = cluster[split_idx:]
                    
                    # Calculate cluster variances
                    left_var = self._get_cluster_variance(
                        covariance, left_cluster
                    )
                    right_var = self._get_cluster_variance(
                        covariance, right_cluster
                    )
                    
                    # Allocate between clusters inversely to variance
                    alpha = 1 / left_var
                    alpha /= (1 / left_var + 1 / right_var)
                    
                    # Update weights
                    weights[left_cluster] *= alpha
                    weights[right_cluster] *= (1 - alpha)
                    
                    # Add sub-clusters for further processing
                    if len(left_cluster) > 1:
                        clusters.append(left_cluster)
                    if len(right_cluster) > 1:
                        clusters.append(right_cluster)
                        
            return weights / weights.sum()
        
        # Apply recursive bisection
        cov_df = pd.DataFrame(
            cov_matrix,
            index=list(range(n_assets)),
            columns=list(range(n_assets))
        )
        
        weights = recursive_bisection(cov_df, ordered_indices)
        weights = weights.sort_index().values
        
        # Apply constraints if needed
        if constraints.max_position_size:
            weights = np.minimum(weights, constraints.max_position_size)
            weights /= weights.sum()
            
        return self._create_result(
            OptimizationMethod.HRP,
            weights,
            None,
            cov_matrix,
            {"linkage_matrix": linkage_matrix, "order": ordered_indices}
        )
    
    def _optimize_cvar(
        self,
        returns_matrix: np.ndarray,
        constraints: PortfolioConstraints,
        alpha: float = 0.05,
        target_return: Optional[float] = None
    ) -> OptimizationResult:
        """
        Conditional Value at Risk (CVaR) optimization
        
        Minimizes the expected loss beyond VaR threshold
        """
        n_assets = returns_matrix.shape[1]
        n_scenarios = returns_matrix.shape[0]
        
        # Decision variables
        weights = cp.Variable(n_assets)
        z = cp.Variable(n_scenarios)  # Auxiliary variables for CVaR
        gamma = cp.Variable()  # VaR threshold
        
        # Portfolio returns for each scenario
        portfolio_returns = returns_matrix @ weights
        
        # CVaR formulation
        cvar = gamma + (1 / (n_scenarios * alpha)) * cp.sum(z)
        
        # Constraints
        constraints_list = [
            cp.sum(weights) == 1,
            z >= 0,
            z >= -portfolio_returns - gamma
        ]
        
        if not constraints.allow_short_selling:
            constraints_list.append(weights >= 0)
            
        if constraints.max_position_size:
            constraints_list.append(weights <= constraints.max_position_size)
            
        if target_return is not None:
            expected_return = np.mean(returns_matrix, axis=0) @ weights
            constraints_list.append(expected_return >= target_return)
            
        # Objective: minimize CVaR
        objective = cp.Minimize(cvar)
        
        # Solve
        problem = cp.Problem(objective, constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"CVaR optimization failed: {problem.status}")
            
        # Calculate metrics
        expected_returns = np.mean(returns_matrix, axis=0)
        cov_matrix = np.cov(returns_matrix, rowvar=False)
        
        return self._create_result(
            OptimizationMethod.CVaR,
            weights.value,
            expected_returns,
            cov_matrix,
            {"cvar": cvar.value, "var": gamma.value, "alpha": alpha}
        )
    
    def _optimize_robust(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints,
        uncertainty_set_size: float = 0.1,
        confidence_level: float = 0.95
    ) -> OptimizationResult:
        """
        Robust optimization with uncertainty in parameters
        
        Accounts for estimation error in expected returns and covariance
        """
        n_assets = len(expected_returns)
        
        # Uncertainty sets for returns and covariance
        return_uncertainty = uncertainty_set_size * np.abs(expected_returns)
        
        # Robust covariance (inflate by uncertainty factor)
        robust_cov = cov_matrix * (1 + uncertainty_set_size)
        
        # Decision variables
        weights = cp.Variable(n_assets)
        
        # Worst-case return (box uncertainty set)
        worst_case_return = (expected_returns - return_uncertainty) @ weights
        
        # Worst-case risk
        worst_case_risk = cp.quad_form(weights, robust_cov)
        
        # Robust Sharpe ratio approximation
        objective = cp.Maximize(
            worst_case_return - 
            confidence_level * cp.sqrt(worst_case_risk)
        )
        
        # Constraints
        constraints_list = [
            cp.sum(weights) == 1,
            weights >= 0
        ]
        
        if constraints.max_position_size:
            constraints_list.append(weights <= constraints.max_position_size)
            
        # Solve
        problem = cp.Problem(objective, constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Robust optimization failed: {problem.status}")
            
        return self._create_result(
            OptimizationMethod.ROBUST,
            weights.value,
            expected_returns,
            cov_matrix,
            {
                "uncertainty_set_size": uncertainty_set_size,
                "confidence_level": confidence_level,
                "worst_case_return": float(worst_case_return.value)
            }
        )
    
    def _get_cluster_variance(
        self,
        covariance: pd.DataFrame,
        cluster_indices: List[int]
    ) -> float:
        """Calculate variance of a cluster (equal-weighted)"""
        cluster_cov = covariance.loc[cluster_indices, cluster_indices]
        weights = np.ones(len(cluster_indices)) / len(cluster_indices)
        return weights @ cluster_cov.values @ weights
    
    def _optimize_max_sharpe(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        """Maximize Sharpe ratio"""
        mpt_constraints = self._convert_constraints(constraints)
        metrics = self.mpt_optimizer.maximize_sharpe_ratio(
            expected_returns, cov_matrix, mpt_constraints
        )
        return self._create_result(
            OptimizationMethod.MAX_SHARPE,
            metrics.weights,
            expected_returns,
            cov_matrix
        )
    
    def _optimize_min_variance(
        self,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        """Minimize portfolio variance"""
        mpt_constraints = self._convert_constraints(constraints)
        metrics = self.mpt_optimizer.minimize_variance(
            cov_matrix, mpt_constraints
        )
        return self._create_result(
            OptimizationMethod.MIN_VARIANCE,
            metrics.weights,
            None,
            cov_matrix
        )
    
    def _optimize_risk_parity(
        self,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        """Risk parity optimization"""
        mpt_constraints = self._convert_constraints(constraints)
        metrics = self.mpt_optimizer.risk_parity_optimization(
            cov_matrix, mpt_constraints
        )
        return self._create_result(
            OptimizationMethod.RISK_PARITY,
            metrics.weights,
            None,
            cov_matrix
        )
    
    def _optimize_max_diversification(
        self,
        cov_matrix: np.ndarray,
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        """Maximum diversification optimization"""
        mpt_constraints = self._convert_constraints(constraints)
        metrics = self.mpt_optimizer.maximum_diversification_portfolio(
            cov_matrix, mpt_constraints
        )
        return self._create_result(
            OptimizationMethod.MAX_DIVERSIFICATION,
            metrics.weights,
            None,
            cov_matrix
        )
    
    def _optimize_black_litterman(
        self,
        assets: List[AssetData],
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        views: Optional[List[InvestorView]],
        constraints: PortfolioConstraints
    ) -> OptimizationResult:
        """Black-Litterman optimization"""
        # Prepare market data
        market_caps = np.array([a.market_cap or 1e9 for a in assets])
        market_data = MarketData(
            market_cap=market_caps,
            covariance=cov_matrix,
            risk_aversion=2.5,
            risk_free_rate=self.risk_free_rate
        )
        
        # Run Black-Litterman
        bl_result = self.black_litterman.full_black_litterman_optimization(
            market_data, views or [], self._convert_bl_constraints(constraints)
        )
        
        return self._create_result(
            OptimizationMethod.BLACK_LITTERMAN,
            bl_result.optimal_weights,
            bl_result.posterior_returns,
            bl_result.posterior_covariance,
            {"confidence_scores": bl_result.confidence_scores}
        )
    
    def _prepare_data(
        self,
        assets: List[AssetData]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prepare returns matrix and statistics"""
        # Align all returns to same dates
        returns_df = pd.DataFrame({
            asset.symbol: asset.returns for asset in assets
        })
        
        # Handle missing data
        returns_df = returns_df.fillna(method='ffill').fillna(0)
        
        # Calculate statistics
        returns_matrix = returns_df.values
        expected_returns = np.array([asset.expected_return for asset in assets])
        cov_matrix = returns_df.cov().values
        
        # Regularize covariance if needed
        cov_matrix = self._regularize_covariance(cov_matrix)
        
        return returns_matrix, expected_returns, cov_matrix
    
    def _regularize_covariance(
        self,
        cov_matrix: np.ndarray,
        epsilon: float = 1e-8
    ) -> np.ndarray:
        """Regularize covariance matrix to ensure positive definiteness"""
        # Check eigenvalues
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        
        if np.min(eigenvalues) < epsilon:
            # Add small value to diagonal
            cov_matrix = cov_matrix + epsilon * np.eye(len(cov_matrix))
            
        return cov_matrix
    
    def _build_cvxpy_constraints(
        self,
        weights: cp.Variable,
        assets: List[AssetData],
        constraints: PortfolioConstraints
    ) -> List:
        """Build CVXPY constraints from PortfolioConstraints"""
        constraints_list = [cp.sum(weights) == 1]
        
        if not constraints.allow_short_selling:
            constraints_list.append(weights >= 0)
            
        if constraints.max_position_size:
            constraints_list.append(weights <= constraints.max_position_size)
            
        if constraints.min_position_size:
            # Only for non-zero weights (approximation)
            pass
            
        # Sector constraints
        for sector, (min_w, max_w) in constraints.sector_limits.items():
            sector_indices = [
                i for i, a in enumerate(assets) if a.sector == sector
            ]
            if sector_indices:
                sector_weight = cp.sum(weights[sector_indices])
                constraints_list.append(sector_weight >= min_w)
                constraints_list.append(sector_weight <= max_w)
                
        # ESG constraints
        if constraints.min_esg_score:
            esg_scores = np.array([a.esg_score or 0 for a in assets])
            portfolio_esg = esg_scores @ weights
            constraints_list.append(portfolio_esg >= constraints.min_esg_score)
            
        return constraints_list
    
    def _convert_constraints(
        self,
        constraints: PortfolioConstraints
    ) -> OptimizationConstraints:
        """Convert to MPT constraints format"""
        return OptimizationConstraints(
            max_position_size=constraints.max_position_size,
            min_position_size=constraints.min_position_size,
            sector_limits=dict(constraints.sector_limits),
            esg_min_score=constraints.min_esg_score,
            allow_short_selling=constraints.allow_short_selling,
            max_turnover=constraints.max_turnover
        )
    
    def _convert_bl_constraints(
        self,
        constraints: PortfolioConstraints
    ) -> Dict:
        """Convert to Black-Litterman constraints format"""
        bl_constraints = {}
        
        if constraints.max_position_size:
            bl_constraints['max_weight'] = constraints.max_position_size
            
        if constraints.min_position_size:
            bl_constraints['min_weight'] = constraints.min_position_size
            
        if constraints.sector_limits:
            bl_constraints['sector_limits'] = constraints.sector_limits
            
        return bl_constraints
    
    def _create_result(
        self,
        method: OptimizationMethod,
        weights: np.ndarray,
        expected_returns: Optional[np.ndarray],
        cov_matrix: np.ndarray,
        info: Optional[Dict] = None
    ) -> OptimizationResult:
        """Create optimization result"""
        # Calculate portfolio metrics
        if expected_returns is not None:
            portfolio_return = weights @ expected_returns
            portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            
            metrics = PortfolioMetrics(
                weights=weights,
                expected_return=portfolio_return,
                volatility=portfolio_vol,
                sharpe_ratio=sharpe
            )
        else:
            portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
            metrics = PortfolioMetrics(
                weights=weights,
                expected_return=0,
                volatility=portfolio_vol,
                sharpe_ratio=0
            )
            
        weight_dict = {f"asset_{i}": w for i, w in enumerate(weights) if w > 1e-6}
        
        return OptimizationResult(
            method=method,
            weights=weight_dict,
            metrics=metrics,
            constraints_satisfied=True,
            optimization_info=info or {}
        )
    
    def _post_process_result(
        self,
        result: OptimizationResult,
        assets: List[AssetData],
        returns_matrix: np.ndarray
    ) -> OptimizationResult:
        """Post-process optimization result with additional analytics"""
        # Update weight dictionary with actual symbols
        symbol_weights = {}
        for i, asset in enumerate(assets):
            key = f"asset_{i}"
            if key in result.weights:
                symbol_weights[asset.symbol] = result.weights[key]
        result.weights = symbol_weights
        
        # Risk decomposition
        result.risk_decomposition = self._calculate_risk_decomposition(
            result.metrics.weights, returns_matrix
        )
        
        return result
    
    def _calculate_risk_decomposition(
        self,
        weights: np.ndarray,
        returns_matrix: np.ndarray
    ) -> Dict:
        """Calculate risk contribution by asset"""
        cov_matrix = np.cov(returns_matrix, rowvar=False)
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        
        marginal_contrib = cov_matrix @ weights
        contrib = weights * marginal_contrib / portfolio_vol
        
        return {
            f"asset_{i}": contrib[i] 
            for i in range(len(weights))
        }
    
    def _validate_constraints(
        self,
        weights: Dict[str, float],
        assets: List[AssetData],
        constraints: PortfolioConstraints
    ) -> bool:
        """Validate that portfolio satisfies all constraints"""
        # Position size constraints
        for symbol, weight in weights.items():
            if weight > constraints.max_position_size:
                return False
            if weight > 0 and weight < constraints.min_position_size:
                return False
                
        # Sector constraints
        for sector, (min_w, max_w) in constraints.sector_limits.items():
            sector_weight = sum(
                weights.get(a.symbol, 0) 
                for a in assets if a.sector == sector
            )
            if sector_weight < min_w or sector_weight > max_w:
                return False
                
        return True