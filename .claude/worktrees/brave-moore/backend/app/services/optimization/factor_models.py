"""
Factor-Based Portfolio Optimization
Implements Fama-French and custom factor models for portfolio construction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import cvxpy as cp
from sklearn.linear_model import LinearRegression
from scipy import stats
import warnings


@dataclass
class FactorExposure:
    """Factor exposure for an asset"""
    asset_id: str
    factor_loadings: Dict[str, float]  # Factor name -> loading
    r_squared: float  # Model R-squared
    residual_volatility: float  # Idiosyncratic risk
    
@dataclass
class FactorModel:
    """Factor model specification"""
    factors: List[str]  # Factor names
    factor_returns: pd.DataFrame  # Historical factor returns
    factor_covariance: np.ndarray  # Factor covariance matrix
    risk_premia: Dict[str, float]  # Expected factor risk premia
    
@dataclass
class FactorPortfolio:
    """Factor-optimized portfolio"""
    weights: np.ndarray
    factor_exposures: Dict[str, float]  # Portfolio factor exposures
    factor_risk_contribution: Dict[str, float]  # Risk from each factor
    idiosyncratic_risk: float  # Residual risk
    expected_return: float
    total_risk: float


class FactorBasedOptimization:
    """
    Factor-based portfolio optimization using various factor models
    """
    
    def __init__(self):
        self.factor_models = {
            'fama_french_3': ['MKT-RF', 'SMB', 'HML'],
            'fama_french_5': ['MKT-RF', 'SMB', 'HML', 'RMW', 'CMA'],
            'carhart_4': ['MKT-RF', 'SMB', 'HML', 'UMD'],
            'custom': []  # User-defined factors
        }
        self.factor_data_cache = {}
        
    def estimate_factor_exposures(
        self,
        asset_returns: pd.DataFrame,
        factor_returns: pd.DataFrame,
        min_history: int = 36
    ) -> Dict[str, FactorExposure]:
        """
        Estimate factor exposures for assets using regression
        
        Args:
            asset_returns: DataFrame of asset returns
            factor_returns: DataFrame of factor returns
            min_history: Minimum months of history required
            
        Returns:
            Dictionary of asset ID -> FactorExposure
        """
        exposures = {}
        
        # Align dates
        common_dates = asset_returns.index.intersection(factor_returns.index)
        if len(common_dates) < min_history:
            raise ValueError(f"Insufficient history: {len(common_dates)} < {min_history}")
            
        asset_returns_aligned = asset_returns.loc[common_dates]
        factor_returns_aligned = factor_returns.loc[common_dates]
        
        for asset in asset_returns.columns:
            # Run factor regression
            y = asset_returns_aligned[asset].values
            X = factor_returns_aligned.values
            
            # Add constant for alpha
            X_with_const = np.column_stack([np.ones(len(X)), X])
            
            # Regression
            model = LinearRegression(fit_intercept=False)
            model.fit(X_with_const, y)
            
            # Extract results
            alpha = model.coef_[0]
            betas = model.coef_[1:]
            
            # Calculate R-squared
            y_pred = model.predict(X_with_const)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Residual volatility
            residuals = y - y_pred
            residual_vol = np.std(residuals) * np.sqrt(252)  # Annualized
            
            # Store exposures
            factor_loadings = {'alpha': alpha}
            for i, factor_name in enumerate(factor_returns.columns):
                factor_loadings[factor_name] = betas[i]
                
            exposures[asset] = FactorExposure(
                asset_id=asset,
                factor_loadings=factor_loadings,
                r_squared=r_squared,
                residual_volatility=residual_vol
            )
            
        return exposures
    
    def build_fama_french_model(
        self,
        model_type: str = 'fama_french_5',
        data_source: str = 'kenneth_french'
    ) -> FactorModel:
        """
        Build Fama-French factor model
        
        Args:
            model_type: Type of model ('fama_french_3', 'fama_french_5', 'carhart_4')
            data_source: Data source for factors
            
        Returns:
            FactorModel object
        """
        # In production, this would fetch real factor data
        # Here we simulate it
        factors = self.factor_models[model_type]
        
        # Simulated factor returns (monthly)
        n_months = 120
        factor_returns = pd.DataFrame(
            np.random.randn(n_months, len(factors)) * 0.02,  # 2% monthly vol
            columns=factors
        )
        
        # Add realistic factor premia (annualized)
        risk_premia = {
            'MKT-RF': 0.08,  # Market premium
            'SMB': 0.02,     # Size premium
            'HML': 0.04,     # Value premium
            'RMW': 0.03,     # Profitability premium
            'CMA': 0.03,     # Investment premium
            'UMD': 0.06      # Momentum premium
        }
        
        # Calculate factor covariance
        factor_cov = factor_returns.cov().values * 12  # Annualized
        
        return FactorModel(
            factors=factors,
            factor_returns=factor_returns,
            factor_covariance=factor_cov,
            risk_premia={f: risk_premia.get(f, 0.0) for f in factors}
        )
    
    def optimize_factor_portfolio(
        self,
        factor_exposures: Dict[str, FactorExposure],
        factor_model: FactorModel,
        target_factor_exposures: Optional[Dict[str, float]] = None,
        risk_budget: Optional[Dict[str, float]] = None,
        constraints: Optional[Dict] = None
    ) -> FactorPortfolio:
        """
        Optimize portfolio based on factor exposures
        
        Args:
            factor_exposures: Asset factor exposures
            factor_model: Factor model specification
            target_factor_exposures: Target exposures to factors
            risk_budget: Risk budget for each factor
            constraints: Portfolio constraints
            
        Returns:
            Optimized factor portfolio
        """
        assets = list(factor_exposures.keys())
        n_assets = len(assets)
        n_factors = len(factor_model.factors)
        
        # Build factor loading matrix
        B = np.zeros((n_factors, n_assets))
        specific_vars = np.zeros(n_assets)
        
        for i, asset in enumerate(assets):
            exposure = factor_exposures[asset]
            for j, factor in enumerate(factor_model.factors):
                if factor in exposure.factor_loadings:
                    B[j, i] = exposure.factor_loadings[factor]
            specific_vars[i] = exposure.residual_volatility ** 2
            
        # Factor covariance matrix
        F = factor_model.factor_covariance
        
        # Total covariance: Σ = B'FB + D where D is diagonal specific variance
        D = np.diag(specific_vars)
        total_cov = B.T @ F @ B + D
        
        # Expected returns from factor model
        factor_premia = np.array([
            factor_model.risk_premia.get(f, 0) for f in factor_model.factors
        ])
        expected_returns = B.T @ factor_premia
        
        # Add alpha if available
        for i, asset in enumerate(assets):
            if 'alpha' in factor_exposures[asset].factor_loadings:
                expected_returns[i] += factor_exposures[asset].factor_loadings['alpha']
                
        # Optimization
        weights = cp.Variable(n_assets)
        
        # Portfolio factor exposures
        portfolio_factor_exposures = B @ weights
        
        # Objective depends on whether we have targets or risk budgets
        if target_factor_exposures:
            # Minimize tracking error to target exposures
            target_exp = np.array([
                target_factor_exposures.get(f, 0) for f in factor_model.factors
            ])
            tracking_error = cp.norm(portfolio_factor_exposures - target_exp)
            objective = cp.Minimize(tracking_error)
            
        elif risk_budget:
            # Risk parity across factors
            factor_risks = []
            for j in range(n_factors):
                factor_risk = cp.abs(portfolio_factor_exposures[j]) * np.sqrt(F[j, j])
                factor_risks.append(factor_risk)
                
            # Minimize deviation from risk budget
            total_risk = cp.sum(factor_risks)
            risk_contributions = [fr / total_risk for fr in factor_risks]
            
            target_risk_contrib = np.array([
                risk_budget.get(factor_model.factors[j], 1.0/n_factors)
                for j in range(n_factors)
            ])
            
            risk_parity_error = cp.sum([
                cp.square(risk_contributions[j] - target_risk_contrib[j])
                for j in range(n_factors)
            ])
            objective = cp.Minimize(risk_parity_error)
            
        else:
            # Maximize Sharpe ratio (approximation)
            portfolio_return = expected_returns @ weights
            portfolio_risk = cp.quad_form(weights, total_cov)
            objective = cp.Maximize(portfolio_return - 2.0 * portfolio_risk)
            
        # Constraints
        constraints_list = [
            cp.sum(weights) == 1,
            weights >= 0  # Long-only by default
        ]
        
        if constraints:
            if 'max_weight' in constraints:
                constraints_list.append(weights <= constraints['max_weight'])
            if 'min_weight' in constraints:
                constraints_list.append(weights >= constraints['min_weight'])
            if 'factor_limits' in constraints:
                for factor, (min_exp, max_exp) in constraints['factor_limits'].items():
                    factor_idx = factor_model.factors.index(factor)
                    constraints_list.append(
                        portfolio_factor_exposures[factor_idx] >= min_exp
                    )
                    constraints_list.append(
                        portfolio_factor_exposures[factor_idx] <= max_exp
                    )
                    
        # Solve
        problem = cp.Problem(objective, constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        # Calculate portfolio metrics
        opt_weights = weights.value
        port_factor_exp = B @ opt_weights
        
        # Factor risk contributions
        factor_cov_contribution = B.T @ F @ B
        portfolio_variance = opt_weights @ total_cov @ opt_weights
        
        factor_risk_contrib = {}
        for j, factor in enumerate(factor_model.factors):
            # Marginal contribution to risk from factor j
            factor_contribution = opt_weights @ factor_cov_contribution[j, :] @ opt_weights
            factor_risk_contrib[factor] = factor_contribution / portfolio_variance
            
        # Idiosyncratic risk
        idio_variance = opt_weights @ D @ opt_weights
        idio_risk = np.sqrt(idio_variance)
        
        # Total risk
        total_risk = np.sqrt(portfolio_variance)
        
        # Expected return
        expected_return = opt_weights @ expected_returns
        
        return FactorPortfolio(
            weights=opt_weights,
            factor_exposures={
                f: port_factor_exp[i] for i, f in enumerate(factor_model.factors)
            },
            factor_risk_contribution=factor_risk_contrib,
            idiosyncratic_risk=idio_risk,
            expected_return=expected_return,
            total_risk=total_risk
        )
    
    def create_factor_mimicking_portfolio(
        self,
        target_factor: str,
        factor_exposures: Dict[str, FactorExposure],
        factor_model: FactorModel,
        orthogonal_to: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Create a portfolio that mimics a specific factor
        
        Args:
            target_factor: Factor to mimic
            factor_exposures: Asset factor exposures
            factor_model: Factor model
            orthogonal_to: List of factors to be orthogonal to
            
        Returns:
            Portfolio weights
        """
        if target_factor not in factor_model.factors:
            raise ValueError(f"Factor {target_factor} not in model")
            
        assets = list(factor_exposures.keys())
        n_assets = len(assets)
        
        # Build factor loading matrix
        B = np.zeros((len(factor_model.factors), n_assets))
        for i, asset in enumerate(assets):
            exposure = factor_exposures[asset]
            for j, factor in enumerate(factor_model.factors):
                if factor in exposure.factor_loadings:
                    B[j, i] = exposure.factor_loadings[factor]
                    
        # Optimization
        weights = cp.Variable(n_assets)
        
        # Portfolio factor exposures
        portfolio_exposures = B @ weights
        
        # Target factor index
        target_idx = factor_model.factors.index(target_factor)
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            portfolio_exposures[target_idx] == 1  # Unit exposure to target
        ]
        
        # Orthogonality constraints
        if orthogonal_to:
            for factor in orthogonal_to:
                if factor in factor_model.factors:
                    factor_idx = factor_model.factors.index(factor)
                    constraints.append(portfolio_exposures[factor_idx] == 0)
                    
        # Minimize portfolio variance
        specific_vars = np.array([
            factor_exposures[asset].residual_volatility ** 2 for asset in assets
        ])
        D = np.diag(specific_vars)
        F = factor_model.factor_covariance
        total_cov = B.T @ F @ B + D
        
        objective = cp.Minimize(cp.quad_form(weights, total_cov))
        
        # Solve
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Failed to create factor mimicking portfolio: {problem.status}")
            
        return weights.value
    
    def tilt_portfolio_on_factors(
        self,
        base_weights: np.ndarray,
        factor_exposures: Dict[str, FactorExposure],
        factor_tilts: Dict[str, float],
        tilt_strength: float = 0.1
    ) -> np.ndarray:
        """
        Tilt portfolio weights based on factor preferences
        
        Args:
            base_weights: Starting portfolio weights
            factor_exposures: Asset factor exposures
            factor_tilts: Desired factor tilts (factor -> tilt amount)
            tilt_strength: Overall tilt strength (0-1)
            
        Returns:
            Tilted portfolio weights
        """
        assets = list(factor_exposures.keys())
        n_assets = len(assets)
        
        if len(base_weights) != n_assets:
            raise ValueError("Weight dimension mismatch")
            
        # Calculate tilt scores for each asset
        tilt_scores = np.zeros(n_assets)
        
        for i, asset in enumerate(assets):
            exposure = factor_exposures[asset]
            score = 0
            
            for factor, tilt in factor_tilts.items():
                if factor in exposure.factor_loadings:
                    # Asset's exposure to factor * desired tilt
                    score += exposure.factor_loadings[factor] * tilt
                    
            tilt_scores[i] = score
            
        # Normalize scores
        if np.std(tilt_scores) > 0:
            tilt_scores = (tilt_scores - np.mean(tilt_scores)) / np.std(tilt_scores)
            
        # Apply tilts to weights
        tilted_weights = base_weights * (1 + tilt_strength * tilt_scores)
        
        # Handle negative weights
        tilted_weights = np.maximum(tilted_weights, 0)
        
        # Renormalize
        if np.sum(tilted_weights) > 0:
            tilted_weights = tilted_weights / np.sum(tilted_weights)
        else:
            tilted_weights = base_weights  # Fallback to original
            
        return tilted_weights
    
    def calculate_factor_attribution(
        self,
        portfolio_returns: pd.Series,
        portfolio_weights: pd.DataFrame,
        factor_exposures: Dict[str, FactorExposure],
        factor_model: FactorModel
    ) -> pd.DataFrame:
        """
        Attribute portfolio returns to factor exposures
        
        Args:
            portfolio_returns: Time series of portfolio returns
            portfolio_weights: Time series of portfolio weights
            factor_exposures: Asset factor exposures
            factor_model: Factor model
            
        Returns:
            DataFrame with factor attribution
        """
        attribution_results = []
        
        for date in portfolio_returns.index:
            if date not in portfolio_weights.index:
                continue
                
            weights = portfolio_weights.loc[date]
            
            # Calculate portfolio factor exposures
            port_factor_exp = {}
            for factor in factor_model.factors:
                exposure = sum(
                    weights[asset] * factor_exposures[asset].factor_loadings.get(factor, 0)
                    for asset in weights.index if asset in factor_exposures
                )
                port_factor_exp[factor] = exposure
                
            # Get factor returns for this period
            if date in factor_model.factor_returns.index:
                factor_rets = factor_model.factor_returns.loc[date]
                
                # Calculate factor contributions
                factor_contrib = {}
                for factor in factor_model.factors:
                    if factor in factor_rets:
                        factor_contrib[factor] = (
                            port_factor_exp[factor] * factor_rets[factor]
                        )
                        
                # Alpha (residual)
                total_factor_return = sum(factor_contrib.values())
                alpha = portfolio_returns[date] - total_factor_return
                
                attribution_results.append({
                    'date': date,
                    'portfolio_return': portfolio_returns[date],
                    **factor_contrib,
                    'alpha': alpha
                })
                
        return pd.DataFrame(attribution_results)
    
    def momentum_factor_strategy(
        self,
        returns_data: pd.DataFrame,
        lookback_period: int = 12,
        holding_period: int = 1,
        n_long: int = 10,
        n_short: int = 10
    ) -> pd.DataFrame:
        """
        Implement momentum factor strategy
        
        Args:
            returns_data: Historical returns for assets
            lookback_period: Months to calculate momentum
            holding_period: Months to hold positions
            n_long: Number of long positions
            n_short: Number of short positions
            
        Returns:
            DataFrame with strategy positions over time
        """
        positions = []
        
        for i in range(lookback_period, len(returns_data), holding_period):
            # Calculate momentum scores
            period_returns = returns_data.iloc[i-lookback_period:i]
            momentum_scores = (1 + period_returns).prod() - 1
            
            # Rank assets
            ranked = momentum_scores.sort_values(ascending=False)
            
            # Select long and short positions
            long_assets = ranked.head(n_long).index
            short_assets = ranked.tail(n_short).index
            
            # Create position weights
            position_date = returns_data.index[i]
            weights = pd.Series(0.0, index=returns_data.columns)
            
            # Long positions (equal weight)
            for asset in long_assets:
                weights[asset] = 1.0 / n_long
                
            # Short positions (if allowed)
            if n_short > 0:
                for asset in short_assets:
                    weights[asset] = -1.0 / n_short
                    
            positions.append({
                'date': position_date,
                'weights': weights
            })
            
        return pd.DataFrame(positions)
    
    def value_factor_strategy(
        self,
        fundamental_data: pd.DataFrame,
        metric: str = 'book_to_market',
        n_long: int = 10,
        n_short: int = 0
    ) -> np.ndarray:
        """
        Implement value factor strategy
        
        Args:
            fundamental_data: Fundamental data for assets
            metric: Value metric to use
            n_long: Number of long positions
            n_short: Number of short positions
            
        Returns:
            Portfolio weights
        """
        # Get value scores
        if metric not in fundamental_data.columns:
            raise ValueError(f"Metric {metric} not found")
            
        value_scores = fundamental_data[metric]
        
        # Rank by value (higher is better for most metrics)
        ranked = value_scores.sort_values(ascending=False)
        
        # Initialize weights
        weights = np.zeros(len(fundamental_data))
        asset_indices = {asset: i for i, asset in enumerate(fundamental_data.index)}
        
        # Long positions
        long_assets = ranked.head(n_long).index
        for asset in long_assets:
            weights[asset_indices[asset]] = 1.0 / n_long
            
        # Short positions (if any)
        if n_short > 0:
            short_assets = ranked.tail(n_short).index
            for asset in short_assets:
                weights[asset_indices[asset]] = -1.0 / n_short
                
        return weights
    
    def smart_beta_portfolio(
        self,
        factor_exposures: Dict[str, FactorExposure],
        target_factors: Dict[str, float],
        risk_budget: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Create smart beta portfolio with targeted factor exposures
        
        Args:
            factor_exposures: Asset factor exposures
            target_factors: Target exposure to each factor
            risk_budget: Risk budget per factor
            
        Returns:
            Smart beta portfolio weights
        """
        assets = list(factor_exposures.keys())
        n_assets = len(assets)
        
        # Build factor loading matrix
        factors = list(target_factors.keys())
        B = np.zeros((len(factors), n_assets))
        
        for i, asset in enumerate(assets):
            exposure = factor_exposures[asset]
            for j, factor in enumerate(factors):
                if factor in exposure.factor_loadings:
                    B[j, i] = exposure.factor_loadings[factor]
                    
        # Optimization for smart beta
        weights = cp.Variable(n_assets)
        portfolio_exposures = B @ weights
        
        # Tracking error to target exposures
        target_exp = np.array([target_factors[f] for f in factors])
        tracking_error = cp.norm(portfolio_exposures - target_exp)
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0,
            weights <= 0.1  # Max 10% per asset
        ]
        
        # Risk budget constraints if specified
        if risk_budget:
            for j, factor in enumerate(factors):
                if factor in risk_budget:
                    constraints.append(
                        cp.abs(portfolio_exposures[j]) <= risk_budget[factor]
                    )
                    
        # Minimize tracking error
        objective = cp.Minimize(tracking_error)
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Smart beta optimization failed: {problem.status}")
            
        return weights.value
    
    def factor_timing_strategy(
        self,
        factor_returns: pd.DataFrame,
        lookback_window: int = 60,
        rebalance_freq: int = 12
    ) -> pd.DataFrame:
        """
        Dynamic factor timing strategy based on momentum and mean reversion
        
        Args:
            factor_returns: Historical factor returns
            lookback_window: Window for signal calculation
            rebalance_freq: Rebalancing frequency in months
            
        Returns:
            Time series of factor allocations
        """
        allocations = []
        
        for i in range(lookback_window, len(factor_returns), rebalance_freq):
            window = factor_returns.iloc[i-lookback_window:i]
            
            # Calculate factor signals
            signals = {}
            for factor in window.columns:
                # Momentum signal
                momentum = window[factor].rolling(12).mean().iloc[-1]
                
                # Mean reversion signal
                z_score = (window[factor].iloc[-1] - window[factor].mean()) / window[factor].std()
                mean_reversion = -z_score if abs(z_score) > 2 else 0
                
                # Combined signal
                signals[factor] = 0.7 * momentum + 0.3 * mean_reversion
                
            # Convert signals to weights
            total_signal = sum(abs(s) for s in signals.values())
            if total_signal > 0:
                weights = {f: abs(signals[f]) / total_signal for f in signals}
            else:
                weights = {f: 1.0 / len(signals) for f in signals}
                
            allocations.append({
                'date': factor_returns.index[i],
                **weights
            })
            
        return pd.DataFrame(allocations)
    
    def multi_factor_risk_model(
        self,
        returns_data: pd.DataFrame,
        factor_data: pd.DataFrame,
        n_factors: int = 5
    ) -> Dict[str, Any]:
        """
        Build multi-factor risk model with PCA augmentation
        
        Args:
            returns_data: Asset returns
            factor_data: Known factor returns
            n_factors: Number of statistical factors to extract
            
        Returns:
            Complete factor risk model
        """
        from sklearn.decomposition import PCA
        
        # Regress returns on known factors
        residuals = returns_data.copy()
        factor_exposures = {}
        
        for asset in returns_data.columns:
            y = returns_data[asset].values
            X = factor_data.values
            
            # Add intercept
            X_with_const = np.column_stack([np.ones(len(X)), X])
            
            # OLS regression
            coef = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
            factor_exposures[asset] = coef[1:]  # Exclude intercept
            
            # Calculate residuals
            fitted = X @ coef[1:] + coef[0]
            residuals[asset] = y - fitted
            
        # PCA on residuals to find statistical factors
        pca = PCA(n_components=n_factors)
        stat_factors = pca.fit_transform(residuals)
        stat_factor_exposures = pca.components_.T
        
        # Combine fundamental and statistical factors
        combined_exposures = np.hstack([
            np.array(list(factor_exposures.values())),
            stat_factor_exposures
        ])
        
        # Factor covariance
        all_factors = np.hstack([factor_data.values, stat_factors])
        factor_cov = np.cov(all_factors.T)
        
        # Specific risk (residual variance after all factors)
        final_residuals = residuals - stat_factors @ stat_factor_exposures.T
        specific_risk = np.diag(np.var(final_residuals, axis=0))
        
        return {
            'factor_exposures': combined_exposures,
            'factor_covariance': factor_cov,
            'specific_risk': specific_risk,
            'explained_variance': pca.explained_variance_ratio_,
            'n_fundamental_factors': len(factor_data.columns),
            'n_statistical_factors': n_factors
        }