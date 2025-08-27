"""
Black-Litterman Model for Portfolio Optimization
Combines market equilibrium with investor views
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from scipy import linalg
import cvxpy as cp


@dataclass
class InvestorView:
    """Represents an investor's view on asset returns"""
    assets: List[int]  # Indices of assets in the view
    view_type: str  # 'absolute' or 'relative'
    expected_return: float  # Expected return for the view
    confidence: float  # Confidence level (0-1, higher = more confident)
    
@dataclass  
class MarketData:
    """Market data for Black-Litterman model"""
    market_cap: np.ndarray  # Market capitalizations
    covariance: np.ndarray  # Covariance matrix
    risk_aversion: float  # Market risk aversion coefficient
    risk_free_rate: float  # Risk-free rate

@dataclass
class BlackLittermanResult:
    """Results from Black-Litterman model"""
    equilibrium_returns: np.ndarray  # Market equilibrium returns
    posterior_returns: np.ndarray  # Combined returns after incorporating views
    posterior_covariance: np.ndarray  # Posterior covariance matrix
    optimal_weights: np.ndarray  # Optimal portfolio weights
    confidence_scores: Dict[str, float]  # Confidence in each asset


class BlackLittermanModel:
    """
    Implementation of the Black-Litterman model for combining
    market equilibrium with investor views
    """
    
    def __init__(
        self,
        tau: float = 0.05,
        risk_aversion: Optional[float] = None
    ):
        """
        Initialize Black-Litterman model
        
        Args:
            tau: Scaling factor for uncertainty in equilibrium returns (typically 0.01-0.1)
            risk_aversion: Risk aversion parameter (if None, will be calculated from market)
        """
        self.tau = tau
        self.risk_aversion = risk_aversion
        
    def calculate_equilibrium_returns(
        self,
        market_weights: np.ndarray,
        covariance_matrix: np.ndarray,
        risk_aversion: Optional[float] = None
    ) -> np.ndarray:
        """
        Calculate market equilibrium returns using reverse optimization
        
        The equilibrium returns are derived from the market portfolio weights
        assuming the market is in equilibrium.
        
        Args:
            market_weights: Market capitalization weights
            covariance_matrix: Asset covariance matrix
            risk_aversion: Risk aversion parameter
            
        Returns:
            Equilibrium expected returns
        """
        if risk_aversion is None:
            risk_aversion = self.risk_aversion if self.risk_aversion else 2.5
            
        # Equilibrium returns: π = λ * Σ * w_mkt
        equilibrium_returns = risk_aversion * covariance_matrix @ market_weights
        
        return equilibrium_returns
    
    def incorporate_views(
        self,
        equilibrium_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        views: List[InvestorView]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Incorporate investor views into equilibrium returns
        
        Args:
            equilibrium_returns: Market equilibrium returns
            covariance_matrix: Asset covariance matrix
            views: List of investor views
            
        Returns:
            Tuple of (posterior_returns, posterior_covariance)
        """
        if not views:
            # No views, return equilibrium
            return equilibrium_returns, covariance_matrix
            
        n_assets = len(equilibrium_returns)
        n_views = len(views)
        
        # Build the views matrix P and views vector Q
        P = np.zeros((n_views, n_assets))
        Q = np.zeros(n_views)
        
        # Build uncertainty matrix Omega (diagonal with view uncertainties)
        omega_diag = []
        
        for i, view in enumerate(views):
            if view.view_type == 'absolute':
                # Absolute view: return on specific asset(s)
                for asset_idx in view.assets:
                    P[i, asset_idx] = 1.0 / len(view.assets)
            else:  # relative
                # Relative view: asset A will outperform asset B
                if len(view.assets) == 2:
                    P[i, view.assets[0]] = 1.0
                    P[i, view.assets[1]] = -1.0
                else:
                    raise ValueError("Relative views require exactly 2 assets")
                    
            Q[i] = view.expected_return
            
            # View uncertainty based on confidence
            # Lower confidence = higher uncertainty
            view_variance = (1.0 - view.confidence) * 0.1  # Scale factor
            omega_diag.append(view_variance)
            
        # Omega matrix (uncertainty in views)
        # Can be diagonal or full matrix
        # Here we use: Omega = diag(P @ (tau * Sigma) @ P^T) scaled by confidence
        Omega = np.diag(omega_diag)
        
        # Alternative: Omega proportional to variance of view portfolios
        # Omega = self.tau * P @ covariance_matrix @ P.T
        # Then scale by confidence
        
        # Calculate posterior parameters using Bayes' rule
        # Prior precision
        prior_precision = np.linalg.inv(self.tau * covariance_matrix)
        
        # View precision
        try:
            omega_inv = np.linalg.inv(Omega)
        except np.linalg.LinAlgError:
            # Singular matrix, use pseudo-inverse
            omega_inv = np.linalg.pinv(Omega)
            
        # Posterior precision
        posterior_precision = prior_precision + P.T @ omega_inv @ P
        
        # Posterior covariance
        try:
            posterior_covariance = np.linalg.inv(posterior_precision)
        except np.linalg.LinAlgError:
            posterior_covariance = np.linalg.pinv(posterior_precision)
            
        # Posterior expected returns
        posterior_returns = posterior_covariance @ (
            prior_precision @ equilibrium_returns + P.T @ omega_inv @ Q
        )
        
        # Add back the original covariance (not scaled by tau) for portfolio optimization
        full_posterior_covariance = covariance_matrix + posterior_covariance
        
        return posterior_returns, full_posterior_covariance
    
    def optimize_portfolio(
        self,
        posterior_returns: np.ndarray,
        posterior_covariance: np.ndarray,
        risk_aversion: Optional[float] = None,
        constraints: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Optimize portfolio weights given posterior returns and covariance
        
        Args:
            posterior_returns: Posterior expected returns
            posterior_covariance: Posterior covariance matrix
            risk_aversion: Risk aversion parameter
            constraints: Optional constraints dictionary
            
        Returns:
            Optimal portfolio weights
        """
        if risk_aversion is None:
            risk_aversion = self.risk_aversion if self.risk_aversion else 2.5
            
        n_assets = len(posterior_returns)
        
        # Use CVXPY for optimization
        weights = cp.Variable(n_assets)
        
        # Expected portfolio return
        portfolio_return = posterior_returns @ weights
        
        # Portfolio variance
        portfolio_variance = cp.quad_form(weights, posterior_covariance)
        
        # Objective: maximize utility = return - (risk_aversion/2) * variance
        objective = cp.Maximize(
            portfolio_return - (risk_aversion / 2) * portfolio_variance
        )
        
        # Constraints
        constraints_list = [
            cp.sum(weights) == 1,  # Fully invested
            weights >= 0  # No short selling (can be changed)
        ]
        
        # Add custom constraints if provided
        if constraints:
            if 'max_weight' in constraints:
                constraints_list.append(weights <= constraints['max_weight'])
            if 'min_weight' in constraints:
                constraints_list.append(weights >= constraints['min_weight'])
            if 'sector_limits' in constraints:
                for sector, limit in constraints['sector_limits'].items():
                    # Assuming sector is provided as asset indices
                    sector_indices = constraints['sector_mapping'][sector]
                    constraints_list.append(
                        cp.sum(weights[sector_indices]) <= limit
                    )
                    
        # Solve
        problem = cp.Problem(objective, constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        return weights.value
    
    def full_black_litterman_optimization(
        self,
        market_data: MarketData,
        views: List[InvestorView],
        constraints: Optional[Dict] = None
    ) -> BlackLittermanResult:
        """
        Complete Black-Litterman optimization process
        
        Args:
            market_data: Market data including caps and covariance
            views: List of investor views
            constraints: Optional portfolio constraints
            
        Returns:
            Complete Black-Litterman results
        """
        # Calculate market weights from market caps
        total_market_cap = np.sum(market_data.market_cap)
        market_weights = market_data.market_cap / total_market_cap
        
        # Calculate equilibrium returns
        equilibrium_returns = self.calculate_equilibrium_returns(
            market_weights,
            market_data.covariance,
            market_data.risk_aversion
        )
        
        # Incorporate views
        posterior_returns, posterior_covariance = self.incorporate_views(
            equilibrium_returns,
            market_data.covariance,
            views
        )
        
        # Optimize portfolio
        optimal_weights = self.optimize_portfolio(
            posterior_returns,
            posterior_covariance,
            market_data.risk_aversion,
            constraints
        )
        
        # Calculate confidence scores for each asset
        confidence_scores = self._calculate_confidence_scores(
            views,
            optimal_weights,
            len(equilibrium_returns)
        )
        
        return BlackLittermanResult(
            equilibrium_returns=equilibrium_returns,
            posterior_returns=posterior_returns,
            posterior_covariance=posterior_covariance,
            optimal_weights=optimal_weights,
            confidence_scores=confidence_scores
        )
    
    def calculate_implied_returns(
        self,
        market_weights: np.ndarray,
        covariance_matrix: np.ndarray,
        risk_aversion: float = 2.5
    ) -> np.ndarray:
        """
        Calculate implied equilibrium returns from market weights
        
        This is useful for understanding what returns the market is implying
        given current market capitalizations.
        
        Args:
            market_weights: Current market capitalization weights
            covariance_matrix: Asset covariance matrix
            risk_aversion: Market risk aversion coefficient
            
        Returns:
            Implied equilibrium returns
        """
        return self.calculate_equilibrium_returns(
            market_weights,
            covariance_matrix, 
            risk_aversion
        )
    
    def tilt_weights_with_views(
        self,
        base_weights: np.ndarray,
        views: List[InvestorView],
        tilt_strength: float = 0.1
    ) -> np.ndarray:
        """
        Tilt existing portfolio weights based on views
        
        This is a simpler alternative to full Black-Litterman that
        adjusts existing weights based on views.
        
        Args:
            base_weights: Starting portfolio weights
            views: List of investor views
            tilt_strength: How much to tilt (0-1)
            
        Returns:
            Tilted portfolio weights
        """
        n_assets = len(base_weights)
        tilted_weights = base_weights.copy()
        
        for view in views:
            if view.view_type == 'absolute':
                # Increase weight for positive views, decrease for negative
                for asset_idx in view.assets:
                    if view.expected_return > 0:
                        # Positive view - increase weight
                        tilt = tilt_strength * view.confidence * view.expected_return
                        tilted_weights[asset_idx] *= (1 + tilt)
                    else:
                        # Negative view - decrease weight
                        tilt = tilt_strength * view.confidence * abs(view.expected_return)
                        tilted_weights[asset_idx] *= (1 - tilt)
                        
            elif view.view_type == 'relative':
                if len(view.assets) == 2:
                    # Asset 0 outperforms asset 1
                    tilt = tilt_strength * view.confidence * abs(view.expected_return)
                    tilted_weights[view.assets[0]] *= (1 + tilt)
                    tilted_weights[view.assets[1]] *= (1 - tilt)
                    
        # Renormalize to sum to 1
        tilted_weights = tilted_weights / np.sum(tilted_weights)
        
        return tilted_weights
    
    def estimate_view_confidence(
        self,
        historical_accuracy: Optional[Dict[str, float]] = None,
        view_source: str = 'analyst',
        time_horizon: int = 30
    ) -> float:
        """
        Estimate confidence level for a view based on historical accuracy
        
        Args:
            historical_accuracy: Past accuracy of views from this source
            view_source: Source of the view (analyst, model, etc.)
            time_horizon: Time horizon in days
            
        Returns:
            Estimated confidence level (0-1)
        """
        base_confidence = {
            'analyst': 0.6,
            'quantitative_model': 0.7,
            'machine_learning': 0.65,
            'fundamental': 0.5,
            'technical': 0.4
        }.get(view_source, 0.5)
        
        # Adjust based on historical accuracy if available
        if historical_accuracy and view_source in historical_accuracy:
            accuracy = historical_accuracy[view_source]
            base_confidence = 0.3 * base_confidence + 0.7 * accuracy
            
        # Adjust based on time horizon (shorter = less confidence)
        time_adjustment = min(1.0, time_horizon / 90)  # Max confidence at 90 days
        
        return base_confidence * time_adjustment
    
    def _calculate_confidence_scores(
        self,
        views: List[InvestorView],
        optimal_weights: np.ndarray,
        n_assets: int
    ) -> Dict[str, float]:
        """
        Calculate confidence scores for each asset based on views
        
        Args:
            views: List of investor views
            optimal_weights: Optimal portfolio weights
            n_assets: Number of assets
            
        Returns:
            Dictionary of confidence scores
        """
        confidence_scores = {}
        
        # Base confidence from optimal weights
        for i in range(n_assets):
            asset_confidence = 0.5  # Base confidence
            
            # Adjust based on views affecting this asset
            for view in views:
                if i in view.assets:
                    asset_confidence = max(asset_confidence, view.confidence)
                    
            # Weight influence
            if optimal_weights[i] > 0.01:  # Significant position
                asset_confidence *= (1 + optimal_weights[i])
                
            confidence_scores[f"asset_{i}"] = min(1.0, asset_confidence)
            
        return confidence_scores
    
    def sensitivity_analysis(
        self,
        market_data: MarketData,
        views: List[InvestorView],
        parameter: str = 'tau',
        range_values: Optional[List[float]] = None
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on Black-Litterman parameters
        
        Args:
            market_data: Market data
            views: Investor views
            parameter: Parameter to vary ('tau', 'risk_aversion', 'confidence')
            range_values: Values to test
            
        Returns:
            DataFrame with sensitivity results
        """
        if range_values is None:
            if parameter == 'tau':
                range_values = [0.01, 0.025, 0.05, 0.075, 0.1]
            elif parameter == 'risk_aversion':
                range_values = [1.5, 2.0, 2.5, 3.0, 3.5]
            elif parameter == 'confidence':
                range_values = [0.3, 0.5, 0.7, 0.9]
                
        results = []
        
        for value in range_values:
            # Update parameter
            if parameter == 'tau':
                original_tau = self.tau
                self.tau = value
            elif parameter == 'risk_aversion':
                original_ra = market_data.risk_aversion
                market_data.risk_aversion = value
            elif parameter == 'confidence':
                # Update all view confidences
                original_confidences = [v.confidence for v in views]
                for v in views:
                    v.confidence = value
                    
            # Run optimization
            result = self.full_black_litterman_optimization(market_data, views)
            
            # Store results
            results.append({
                parameter: value,
                'max_weight': np.max(result.optimal_weights),
                'min_weight': np.min(result.optimal_weights[result.optimal_weights > 0.001]),
                'concentration': np.sum(result.optimal_weights ** 2),  # Herfindahl index
                'expected_return': result.posterior_returns @ result.optimal_weights
            })
            
            # Reset parameter
            if parameter == 'tau':
                self.tau = original_tau
            elif parameter == 'risk_aversion':
                market_data.risk_aversion = original_ra
            elif parameter == 'confidence':
                for v, orig_conf in zip(views, original_confidences):
                    v.confidence = orig_conf
                    
        return pd.DataFrame(results)