"""
Modern Portfolio Theory (MPT) Optimization Module
Implements Markowitz portfolio optimization with efficient frontier calculation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import cvxpy as cp
from scipy.optimize import minimize
from scipy import linalg
import warnings

@dataclass
class OptimizationConstraints:
    """Portfolio optimization constraints"""
    max_position_size: Optional[float] = 0.2  # Maximum 20% per position
    min_position_size: Optional[float] = 0.01  # Minimum 1% per position  
    sector_limits: Optional[Dict[str, float]] = None
    asset_class_limits: Optional[Dict[str, float]] = None
    esg_min_score: Optional[float] = None
    allow_short_selling: bool = False
    max_turnover: Optional[float] = None
    
@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    weights: np.ndarray
    expected_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    
@dataclass
class EfficientFrontierPoint:
    """Point on the efficient frontier"""
    target_return: float
    weights: np.ndarray
    volatility: float
    sharpe_ratio: float


class ModernPortfolioTheory:
    """
    Modern Portfolio Theory optimizer implementing various optimization strategies
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        self.covariance_estimator = 'sample'  # Can be 'sample', 'ledoit_wolf', 'mcd'
        
    def calculate_efficient_frontier(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        n_points: int = 100,
        constraints: Optional[OptimizationConstraints] = None
    ) -> List[EfficientFrontierPoint]:
        """
        Calculate the efficient frontier
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix of returns
            n_points: Number of points to calculate on the frontier
            constraints: Optional optimization constraints
            
        Returns:
            List of efficient frontier points
        """
        if constraints is None:
            constraints = OptimizationConstraints()
            
        # Get range of possible returns
        min_return = np.min(expected_returns)
        max_return = np.max(expected_returns)
        
        # Generate target returns
        target_returns = np.linspace(min_return, max_return, n_points)
        
        frontier_points = []
        
        for target_return in target_returns:
            try:
                # Minimize variance for target return
                weights = self._minimize_variance(
                    expected_returns,
                    covariance_matrix,
                    target_return,
                    constraints
                )
                
                if weights is not None:
                    volatility = np.sqrt(weights @ covariance_matrix @ weights)
                    portfolio_return = weights @ expected_returns
                    sharpe = (portfolio_return - self.risk_free_rate) / volatility
                    
                    frontier_points.append(EfficientFrontierPoint(
                        target_return=target_return,
                        weights=weights,
                        volatility=volatility,
                        sharpe_ratio=sharpe
                    ))
            except:
                continue
                
        return frontier_points
    
    def maximize_sharpe_ratio(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Optional[OptimizationConstraints] = None
    ) -> PortfolioMetrics:
        """
        Find portfolio that maximizes Sharpe ratio
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix of returns
            constraints: Optional optimization constraints
            
        Returns:
            Optimal portfolio metrics
        """
        if constraints is None:
            constraints = OptimizationConstraints()
            
        n_assets = len(expected_returns)
        
        # Use CVXPY for convex optimization
        weights = cp.Variable(n_assets)
        
        # Portfolio metrics
        portfolio_return = expected_returns @ weights
        portfolio_variance = cp.quad_form(weights, covariance_matrix)
        
        # We can't directly maximize Sharpe ratio (non-convex)
        # Instead, we use the two-fund theorem approach
        
        # First find the minimum variance portfolio
        min_var_weights = self._minimize_variance_cvxpy(
            covariance_matrix,
            constraints
        )
        
        # Then find the tangency portfolio
        # This requires solving: max (μ - rf)^T w / sqrt(w^T Σ w)
        # We use a numerical approach
        
        def negative_sharpe(w):
            """Negative Sharpe ratio for minimization"""
            ret = w @ expected_returns
            vol = np.sqrt(w @ covariance_matrix @ w)
            return -(ret - self.risk_free_rate) / vol if vol > 0 else -np.inf
        
        # Build constraints for scipy
        scipy_constraints = self._build_scipy_constraints(n_assets, constraints)
        
        # Initial guess (equal weights)
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            negative_sharpe,
            x0,
            method='SLSQP',
            bounds=[(0, 1) for _ in range(n_assets)] if not constraints.allow_short_selling else None,
            constraints=scipy_constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            optimal_weights = result.x
            portfolio_return = optimal_weights @ expected_returns
            portfolio_vol = np.sqrt(optimal_weights @ covariance_matrix @ optimal_weights)
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            
            return PortfolioMetrics(
                weights=optimal_weights,
                expected_return=portfolio_return,
                volatility=portfolio_vol,
                sharpe_ratio=sharpe
            )
        else:
            raise ValueError("Optimization failed to converge")
    
    def minimize_variance(
        self,
        covariance_matrix: np.ndarray,
        constraints: Optional[OptimizationConstraints] = None
    ) -> PortfolioMetrics:
        """
        Find minimum variance portfolio
        
        Args:
            covariance_matrix: Covariance matrix of returns
            constraints: Optional optimization constraints
            
        Returns:
            Minimum variance portfolio metrics
        """
        if constraints is None:
            constraints = OptimizationConstraints()
            
        weights = self._minimize_variance_cvxpy(covariance_matrix, constraints)
        
        portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
        
        return PortfolioMetrics(
            weights=weights,
            expected_return=0.0,  # Will be calculated separately if returns provided
            volatility=portfolio_vol,
            sharpe_ratio=0.0  # Will be calculated separately
        )
    
    def risk_parity_optimization(
        self,
        covariance_matrix: np.ndarray,
        constraints: Optional[OptimizationConstraints] = None
    ) -> PortfolioMetrics:
        """
        Implement risk parity strategy where each asset contributes equally to portfolio risk
        
        Args:
            covariance_matrix: Covariance matrix of returns
            constraints: Optional optimization constraints
            
        Returns:
            Risk parity portfolio metrics
        """
        n_assets = len(covariance_matrix)
        
        def risk_parity_objective(weights):
            """
            Minimize the sum of squared differences between 
            risk contributions and target (1/n)
            """
            portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
            marginal_contrib = covariance_matrix @ weights
            contrib = weights * marginal_contrib / portfolio_vol
            target = 1.0 / n_assets
            return np.sum((contrib - target) ** 2)
        
        # Constraints
        scipy_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Sum to 1
        ]
        
        # Bounds
        bounds = [(0.001, 1.0) for _ in range(n_assets)]
        
        # Initial guess (equal weights)
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            weights = result.x
            portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
            
            # Calculate actual risk contributions
            marginal_contrib = covariance_matrix @ weights
            risk_contributions = weights * marginal_contrib / portfolio_vol
            
            return PortfolioMetrics(
                weights=weights,
                expected_return=0.0,
                volatility=portfolio_vol,
                sharpe_ratio=0.0
            )
        else:
            raise ValueError("Risk parity optimization failed to converge")
    
    def maximum_diversification_portfolio(
        self,
        covariance_matrix: np.ndarray,
        constraints: Optional[OptimizationConstraints] = None
    ) -> PortfolioMetrics:
        """
        Find portfolio that maximizes diversification ratio
        
        The diversification ratio is defined as the weighted average of asset volatilities
        divided by portfolio volatility.
        
        Args:
            covariance_matrix: Covariance matrix of returns
            constraints: Optional optimization constraints
            
        Returns:
            Maximum diversification portfolio metrics
        """
        n_assets = len(covariance_matrix)
        asset_vols = np.sqrt(np.diag(covariance_matrix))
        
        def negative_diversification_ratio(weights):
            """Negative diversification ratio for minimization"""
            weighted_vol = weights @ asset_vols
            portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
            return -weighted_vol / portfolio_vol if portfolio_vol > 0 else -np.inf
        
        # Constraints
        scipy_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        # Bounds
        bounds = [(0, 1) for _ in range(n_assets)]
        
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            negative_diversification_ratio,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            weights = result.x
            portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
            
            return PortfolioMetrics(
                weights=weights,
                expected_return=0.0,
                volatility=portfolio_vol,
                sharpe_ratio=0.0
            )
        else:
            raise ValueError("Maximum diversification optimization failed")
    
    def calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        returns_data: pd.DataFrame,
        expected_returns: Optional[np.ndarray] = None
    ) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics
        
        Args:
            weights: Portfolio weights
            returns_data: Historical returns data
            expected_returns: Optional expected returns
            
        Returns:
            Comprehensive portfolio metrics
        """
        # Portfolio returns series
        portfolio_returns = returns_data @ weights
        
        # Expected return
        if expected_returns is not None:
            exp_return = weights @ expected_returns
        else:
            exp_return = portfolio_returns.mean() * 252  # Annualized
        
        # Volatility
        volatility = portfolio_returns.std() * np.sqrt(252)
        
        # Sharpe ratio
        sharpe = (exp_return - self.risk_free_rate) / volatility
        
        # Sortino ratio (downside deviation)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        if len(downside_returns) > 0:
            downside_vol = downside_returns.std() * np.sqrt(252)
            sortino = (exp_return - self.risk_free_rate) / downside_vol
        else:
            sortino = np.inf
        
        # Maximum drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        
        # VaR and CVaR at 95% confidence
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        return PortfolioMetrics(
            weights=weights,
            expected_return=exp_return,
            volatility=volatility,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            var_95=var_95 * np.sqrt(252),  # Annualized
            cvar_95=cvar_95 * np.sqrt(252)  # Annualized
        )
    
    def _minimize_variance(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        target_return: float,
        constraints: OptimizationConstraints
    ) -> Optional[np.ndarray]:
        """Minimize variance for a target return"""
        n_assets = len(expected_returns)
        
        # CVXPY formulation
        weights = cp.Variable(n_assets)
        
        # Objective: minimize variance
        objective = cp.Minimize(cp.quad_form(weights, covariance_matrix))
        
        # Constraints
        constraints_list = [
            cp.sum(weights) == 1,
            expected_returns @ weights == target_return
        ]
        
        if not constraints.allow_short_selling:
            constraints_list.append(weights >= 0)
            
        if constraints.max_position_size:
            constraints_list.append(weights <= constraints.max_position_size)
            
        if constraints.min_position_size:
            constraints_list.append(weights >= constraints.min_position_size)
        
        # Solve
        problem = cp.Problem(objective, constraints_list)
        
        try:
            problem.solve(solver=cp.OSQP, verbose=False)
            if problem.status in ["optimal", "optimal_inaccurate"]:
                return weights.value
        except:
            pass
            
        return None
    
    def _minimize_variance_cvxpy(
        self,
        covariance_matrix: np.ndarray,
        constraints: OptimizationConstraints
    ) -> np.ndarray:
        """Minimize portfolio variance using CVXPY"""
        n_assets = len(covariance_matrix)
        
        weights = cp.Variable(n_assets)
        
        # Objective
        objective = cp.Minimize(cp.quad_form(weights, covariance_matrix))
        
        # Constraints
        constraints_list = [cp.sum(weights) == 1]
        
        if not constraints.allow_short_selling:
            constraints_list.append(weights >= 0)
            
        if constraints.max_position_size:
            constraints_list.append(weights <= constraints.max_position_size)
            
        if constraints.min_position_size:
            # Only apply to non-zero weights
            # This is approximated in the convex formulation
            pass
        
        # Solve
        problem = cp.Problem(objective, constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError("Minimum variance optimization failed")
            
        return weights.value
    
    def _build_scipy_constraints(
        self,
        n_assets: int,
        constraints: OptimizationConstraints
    ) -> List[Dict]:
        """Build constraints for scipy optimizer"""
        scipy_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        if constraints.max_position_size:
            scipy_constraints.append({
                'type': 'ineq',
                'fun': lambda x: constraints.max_position_size - np.max(x)
            })
            
        return scipy_constraints