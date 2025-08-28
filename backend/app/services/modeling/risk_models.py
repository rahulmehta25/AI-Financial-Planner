"""
Advanced Risk Models for Financial Portfolio Analysis

This module implements sophisticated risk modeling techniques:
- GARCH models for volatility clustering
- Jump diffusion processes for sudden market moves
- Extreme Value Theory for tail risk assessment
- Copula models for dependency structure
- Regime-dependent risk models
- Factor models for systemic risk
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy import stats, optimize
from scipy.special import gamma, digamma
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.covariance import LedoitWolf, EmpiricalCovariance
import warnings
warnings.filterwarnings('ignore')

# GPU acceleration support
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = None

logger = logging.getLogger(__name__)

class RiskModelType(Enum):
    """Types of risk models"""
    GARCH = "garch"
    EGARCH = "egarch"  
    GJRGARCH = "gjrgarch"
    JUMP_DIFFUSION = "jump_diffusion"
    STOCHASTIC_VOLATILITY = "stochastic_volatility"
    REGIME_SWITCHING = "regime_switching"

class TailRiskModel(Enum):
    """Tail risk modeling approaches"""
    GENERALIZED_PARETO = "gpd"
    GENERALIZED_EXTREME_VALUE = "gev"
    PEAKS_OVER_THRESHOLD = "pot"
    BLOCK_MAXIMA = "bm"

@dataclass
class GARCHParams:
    """GARCH model parameters"""
    omega: float = 0.0  # Constant term
    alpha: List[float] = field(default_factory=list)  # ARCH coefficients
    beta: List[float] = field(default_factory=list)   # GARCH coefficients
    gamma: float = 0.0  # Asymmetry parameter (for GJR-GARCH)
    nu: float = np.inf  # Degrees of freedom for t-distribution
    distribution: str = "normal"  # "normal", "t", "ged"
    
@dataclass 
class JumpDiffusionParams:
    """Jump diffusion model parameters"""
    mu: float = 0.0          # Drift parameter
    sigma: float = 0.0       # Diffusion volatility
    jump_intensity: float = 0.0  # Jump intensity (lambda)
    jump_mean: float = 0.0   # Mean jump size
    jump_std: float = 0.0    # Jump size volatility
    jump_distribution: str = "normal"  # Jump size distribution

@dataclass
class ExtremeValueParams:
    """Extreme value theory parameters"""
    threshold: float = 0.0
    shape_parameter: float = 0.0  # xi (tail index)
    scale_parameter: float = 0.0  # sigma
    location_parameter: float = 0.0  # mu (for GEV)
    
@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    var_estimates: Dict[str, float]
    cvar_estimates: Dict[str, float]
    tail_indices: Dict[str, float]
    maximum_drawdown: float
    volatility_clustering: float
    tail_dependence: Dict[str, float]
    correlation_breakdown: bool
    model_diagnostics: Dict[str, Any]

class GARCHModel:
    """
    Comprehensive GARCH model implementation supporting:
    - Standard GARCH(p,q)
    - EGARCH for asymmetric effects
    - GJR-GARCH for leverage effects
    - Multiple error distributions (Normal, t, GED)
    """
    
    def __init__(self, model_type: RiskModelType = RiskModelType.GARCH):
        self.model_type = model_type
        self.params = None
        self.fitted = False
        self.residuals = None
        self.conditional_volatility = None
        self.log_likelihood = None
        self.aic = None
        self.bic = None
        
    def fit(self, returns: np.ndarray, p: int = 1, q: int = 1, 
            distribution: str = "normal", max_iter: int = 1000) -> GARCHParams:
        """
        Fit GARCH model using Maximum Likelihood Estimation
        """
        logger.info(f"Fitting {self.model_type.value} model with p={p}, q={q}")
        
        # Prepare data
        returns = np.asarray(returns).flatten()
        T = len(returns)
        
        # Initial parameter estimates
        initial_params = self._get_initial_parameters(returns, p, q, distribution)
        
        # Define bounds for optimization
        bounds = self._get_parameter_bounds(p, q, distribution)
        
        # Log-likelihood function
        def negative_log_likelihood(params):
            try:
                ll = self._calculate_log_likelihood(params, returns, p, q, distribution)
                return -ll if not np.isnan(ll) else 1e10
            except:
                return 1e10
        
        # Optimize
        result = optimize.minimize(
            negative_log_likelihood,
            initial_params,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': max_iter, 'ftol': 1e-9}
        )
        
        if not result.success:
            logger.warning("GARCH optimization did not converge, trying alternative method")
            # Try different method
            result = optimize.minimize(
                negative_log_likelihood,
                initial_params,
                method='SLSQP',
                bounds=bounds,
                options={'maxiter': max_iter}
            )
        
        # Store results
        self.params = self._parse_parameters(result.x, p, q, distribution)
        self.log_likelihood = -result.fun
        self.fitted = True
        
        # Calculate fitted volatility and residuals
        self.conditional_volatility = self._calculate_conditional_volatility(
            self.params, returns, p, q
        )
        
        # Standardized residuals
        self.residuals = returns / self.conditional_volatility
        
        # Information criteria
        n_params = len(result.x)
        self.aic = 2 * n_params - 2 * self.log_likelihood
        self.bic = np.log(T) * n_params - 2 * self.log_likelihood
        
        logger.info(f"GARCH model fitted successfully. Log-likelihood: {self.log_likelihood:.4f}")
        return self.params
    
    def _get_initial_parameters(self, returns: np.ndarray, p: int, q: int, 
                              distribution: str) -> np.ndarray:
        """Get initial parameter estimates"""
        
        # Basic statistics
        var_returns = np.var(returns)
        
        # Initial GARCH parameters
        omega_init = var_returns * 0.1
        alpha_init = [0.1] * p
        beta_init = [0.8] * q
        
        params = [omega_init] + alpha_init + beta_init
        
        # Add asymmetry parameter for GJR-GARCH
        if self.model_type == RiskModelType.GJRGARCH:
            params.append(0.05)  # gamma
            
        # Add distribution parameters
        if distribution == "t":
            params.append(10.0)  # degrees of freedom
        elif distribution == "ged":
            params.append(1.5)   # shape parameter
            
        return np.array(params)
    
    def _get_parameter_bounds(self, p: int, q: int, distribution: str) -> List[Tuple]:
        """Define parameter bounds for optimization"""
        
        bounds = [(1e-6, 1)]  # omega > 0
        bounds.extend([(1e-6, 1)] * p)  # alpha_i > 0
        bounds.extend([(1e-6, 1)] * q)  # beta_i > 0
        
        # Add asymmetry parameter bounds
        if self.model_type == RiskModelType.GJRGARCH:
            bounds.append((0, 1))  # gamma >= 0
            
        # Distribution parameter bounds
        if distribution == "t":
            bounds.append((2.1, 100))  # degrees of freedom > 2
        elif distribution == "ged":
            bounds.append((0.5, 5))    # shape parameter
            
        return bounds
    
    def _calculate_log_likelihood(self, params: np.ndarray, returns: np.ndarray,
                                p: int, q: int, distribution: str) -> float:
        """Calculate log-likelihood for GARCH model"""
        
        T = len(returns)
        parsed_params = self._parse_parameters(params, p, q, distribution)
        
        # Calculate conditional variances
        h = np.zeros(T)
        h[0] = np.var(returns)  # Initial variance
        
        for t in range(1, T):
            h[t] = parsed_params.omega
            
            # ARCH terms
            for i in range(min(p, t)):
                h[t] += parsed_params.alpha[i] * returns[t-1-i]**2
                
            # GARCH terms  
            for j in range(min(q, t)):
                h[t] += parsed_params.beta[j] * h[t-1-j]
                
            # Asymmetry term for GJR-GARCH
            if self.model_type == RiskModelType.GJRGARCH and hasattr(parsed_params, 'gamma'):
                for i in range(min(p, t)):
                    if returns[t-1-i] < 0:
                        h[t] += parsed_params.gamma * returns[t-1-i]**2
        
        # Prevent numerical issues
        h = np.maximum(h, 1e-8)
        
        # Log-likelihood calculation
        if distribution == "normal":
            ll = -0.5 * np.sum(np.log(2 * np.pi * h) + returns**2 / h)
        elif distribution == "t":
            nu = parsed_params.nu
            ll = np.sum(
                np.log(gamma((nu + 1) / 2)) - np.log(gamma(nu / 2)) - 
                0.5 * np.log(np.pi * (nu - 2) * h) -
                ((nu + 1) / 2) * np.log(1 + returns**2 / ((nu - 2) * h))
            )
        elif distribution == "ged":
            # Generalized Error Distribution
            shape = parsed_params.shape_param if hasattr(parsed_params, 'shape_param') else 1.5
            lambda_param = np.sqrt(2**(-2/shape) * gamma(1/shape) / gamma(3/shape))
            ll = np.sum(
                np.log(shape) - np.log(lambda_param) - 0.5 * np.log(2 * h) -
                np.log(gamma(1/shape)) - 0.5 * (np.abs(returns) / (lambda_param * np.sqrt(h)))**shape
            )
        else:
            raise ValueError(f"Unknown distribution: {distribution}")
            
        return ll if not np.isnan(ll) else -1e10
    
    def _parse_parameters(self, params: np.ndarray, p: int, q: int, 
                         distribution: str) -> GARCHParams:
        """Parse parameter array into GARCHParams object"""
        
        idx = 0
        omega = params[idx]
        idx += 1
        
        alpha = params[idx:idx+p].tolist()
        idx += p
        
        beta = params[idx:idx+q].tolist()
        idx += q
        
        gamma = 0.0
        if self.model_type == RiskModelType.GJRGARCH:
            gamma = params[idx]
            idx += 1
            
        nu = np.inf
        shape_param = None
        if distribution == "t":
            nu = params[idx]
        elif distribution == "ged":
            shape_param = params[idx]
            
        garch_params = GARCHParams(
            omega=omega,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            nu=nu,
            distribution=distribution
        )
        
        if shape_param is not None:
            garch_params.shape_param = shape_param
            
        return garch_params
    
    def _calculate_conditional_volatility(self, params: GARCHParams, 
                                        returns: np.ndarray, p: int, q: int) -> np.ndarray:
        """Calculate conditional volatility series"""
        
        T = len(returns)
        h = np.zeros(T)
        h[0] = np.var(returns)
        
        for t in range(1, T):
            h[t] = params.omega
            
            # ARCH terms
            for i in range(min(p, t)):
                h[t] += params.alpha[i] * returns[t-1-i]**2
                
            # GARCH terms
            for j in range(min(q, t)):
                h[t] += params.beta[j] * h[t-1-j]
                
            # Asymmetry term for GJR-GARCH
            if self.model_type == RiskModelType.GJRGARCH:
                for i in range(min(p, t)):
                    if returns[t-1-i] < 0:
                        h[t] += params.gamma * returns[t-1-i]**2
        
        return np.sqrt(np.maximum(h, 1e-8))
    
    def forecast_volatility(self, steps: int = 1) -> np.ndarray:
        """Forecast conditional volatility"""
        if not self.fitted:
            raise ValueError("Model must be fitted before forecasting")
            
        # Multi-step ahead forecasting
        forecasts = np.zeros(steps)
        
        # Get recent data
        recent_returns = self.residuals[-10:] if len(self.residuals) >= 10 else self.residuals
        recent_volatility = self.conditional_volatility[-10:] if len(self.conditional_volatility) >= 10 else self.conditional_volatility
        
        # Simple approach: use long-run variance for multi-step
        long_run_variance = self.params.omega / (1 - sum(self.params.alpha) - sum(self.params.beta))
        
        for h in range(steps):
            if h == 0:
                # One-step ahead
                forecasts[h] = np.sqrt(long_run_variance)
            else:
                # Multi-step ahead (converges to long-run)
                weight = (sum(self.params.alpha) + sum(self.params.beta))**h
                forecasts[h] = np.sqrt(weight * forecasts[0]**2 + (1 - weight) * long_run_variance)
                
        return forecasts
    
    def get_model_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive model diagnostics"""
        if not self.fitted:
            raise ValueError("Model must be fitted before diagnostics")
            
        # Ljung-Box test for serial correlation
        def ljung_box_test(residuals, lags=10):
            n = len(residuals)
            acf = np.correlate(residuals, residuals, mode='full')
            acf = acf[n-1:]
            acf = acf[1:lags+1] / acf[0]
            
            lb_stat = n * (n + 2) * np.sum(acf**2 / (n - np.arange(1, lags+1)))
            p_value = 1 - stats.chi2.cdf(lb_stat, lags)
            return lb_stat, p_value
        
        # ARCH test for remaining heteroskedasticity
        def arch_lm_test(residuals, lags=5):
            n = len(residuals)
            squared_residuals = residuals**2
            
            # Create lagged variables
            X = np.column_stack([squared_residuals[i:n-lags+i] for i in range(lags)])
            y = squared_residuals[lags:]
            
            # OLS regression
            X_with_const = np.column_stack([np.ones(len(X)), X])
            try:
                beta = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
                y_pred = X_with_const @ beta
                ssr = np.sum((y - y_pred)**2)
                tss = np.sum((y - np.mean(y))**2)
                r_squared = 1 - ssr/tss
                
                lm_stat = len(y) * r_squared
                p_value = 1 - stats.chi2.cdf(lm_stat, lags)
                return lm_stat, p_value
            except:
                return np.nan, np.nan
        
        # Calculate diagnostics
        lb_stat, lb_pval = ljung_box_test(self.residuals)
        arch_stat, arch_pval = arch_lm_test(self.residuals)
        
        # Normality tests
        jb_stat, jb_pval = stats.jarque_bera(self.residuals)
        
        return {
            'log_likelihood': self.log_likelihood,
            'aic': self.aic,
            'bic': self.bic,
            'ljung_box_stat': lb_stat,
            'ljung_box_pvalue': lb_pval,
            'arch_lm_stat': arch_stat,
            'arch_lm_pvalue': arch_pval,
            'jarque_bera_stat': jb_stat,
            'jarque_bera_pvalue': jb_pval,
            'mean_residual': np.mean(self.residuals),
            'std_residual': np.std(self.residuals),
            'skewness_residual': stats.skew(self.residuals),
            'kurtosis_residual': stats.kurtosis(self.residuals)
        }

class JumpDiffusionRiskModel:
    """
    Advanced Jump Diffusion model for capturing sudden market moves
    Implements Merton's jump diffusion model with stochastic volatility
    """
    
    def __init__(self):
        self.params = None
        self.fitted = False
        self.jump_times = []
        self.jump_sizes = []
        
    def fit(self, returns: np.ndarray, method: str = "method_of_moments") -> JumpDiffusionParams:
        """
        Fit jump diffusion model using various estimation methods
        """
        logger.info("Fitting Jump Diffusion model")
        
        if method == "method_of_moments":
            params = self._fit_method_of_moments(returns)
        elif method == "maximum_likelihood":
            params = self._fit_maximum_likelihood(returns)
        elif method == "threshold_detection":
            params = self._fit_threshold_detection(returns)
        else:
            raise ValueError(f"Unknown fitting method: {method}")
            
        self.params = params
        self.fitted = True
        
        return params
    
    def _fit_method_of_moments(self, returns: np.ndarray) -> JumpDiffusionParams:
        """Fit using method of moments"""
        
        # Calculate sample moments
        mean_return = np.mean(returns)
        var_return = np.var(returns)
        skew_return = stats.skew(returns)
        kurt_return = stats.kurtosis(returns)
        
        # Initial guesses for iterative solution
        dt = 1/252  # Assuming daily data
        
        # Estimate jump parameters from higher moments
        # This is a simplified approach
        excess_kurtosis = kurt_return
        jump_intensity_est = excess_kurtosis / (3 * dt)
        jump_intensity_est = max(0, min(jump_intensity_est, 50))  # Reasonable bounds
        
        # Estimate jump size parameters
        if jump_intensity_est > 0:
            jump_var_est = var_return * 0.1  # Assume jumps contribute 10% to total variance
            jump_mean_est = skew_return * np.sqrt(jump_var_est) / 3
            jump_std_est = np.sqrt(jump_var_est)
        else:
            jump_mean_est = 0
            jump_std_est = 0
            
        # Estimate diffusion parameters
        diffusion_var = var_return - jump_intensity_est * (jump_mean_est**2 + jump_std_est**2) * dt
        diffusion_vol = np.sqrt(max(diffusion_var / dt, var_return * 0.5))
        
        mu_est = mean_return / dt - jump_intensity_est * jump_mean_est
        
        return JumpDiffusionParams(
            mu=mu_est,
            sigma=diffusion_vol,
            jump_intensity=jump_intensity_est,
            jump_mean=jump_mean_est,
            jump_std=jump_std_est,
            jump_distribution="normal"
        )
    
    def _fit_threshold_detection(self, returns: np.ndarray, threshold: float = 3.0) -> JumpDiffusionParams:
        """Fit using threshold-based jump detection"""
        
        # Calculate rolling statistics for jump detection
        window = 20
        rolling_mean = pd.Series(returns).rolling(window, center=True).mean()
        rolling_std = pd.Series(returns).rolling(window, center=True).std()
        
        # Detect jumps
        standardized_returns = (returns - rolling_mean) / rolling_std
        jump_indicators = np.abs(standardized_returns) > threshold
        
        # Remove NaN values
        valid_mask = ~np.isnan(jump_indicators)
        jump_indicators = jump_indicators[valid_mask]
        valid_returns = returns[valid_mask]
        
        # Extract jump information
        jump_returns = valid_returns[jump_indicators]
        self.jump_times = np.where(jump_indicators)[0]
        self.jump_sizes = jump_returns
        
        # Estimate parameters
        dt = 1/252
        T = len(valid_returns) * dt
        
        if len(jump_returns) > 0:
            jump_intensity = len(jump_returns) / T
            jump_mean = np.mean(jump_returns)
            jump_std = np.std(jump_returns)
        else:
            jump_intensity = 0
            jump_mean = 0
            jump_std = 0
            
        # Estimate diffusion parameters from non-jump periods
        non_jump_returns = valid_returns[~jump_indicators]
        if len(non_jump_returns) > 0:
            mu_est = np.mean(non_jump_returns) / dt
            sigma_est = np.std(non_jump_returns) / np.sqrt(dt)
        else:
            mu_est = np.mean(valid_returns) / dt
            sigma_est = np.std(valid_returns) / np.sqrt(dt)
            
        return JumpDiffusionParams(
            mu=mu_est,
            sigma=sigma_est,
            jump_intensity=jump_intensity,
            jump_mean=jump_mean,
            jump_std=jump_std,
            jump_distribution="normal"
        )
    
    def simulate_paths(self, n_paths: int, n_steps: int, dt: float, 
                      initial_value: float = 1.0) -> np.ndarray:
        """Simulate jump diffusion paths"""
        if not self.fitted:
            raise ValueError("Model must be fitted before simulation")
            
        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = initial_value
        
        for i in range(n_paths):
            for t in range(n_steps):
                # Brownian motion component
                dW = np.random.normal(0, np.sqrt(dt))
                drift = self.params.mu * dt
                diffusion = self.params.sigma * dW
                
                # Jump component
                jump = 0
                if np.random.random() < self.params.jump_intensity * dt:
                    if self.params.jump_distribution == "normal":
                        jump = np.random.normal(self.params.jump_mean, self.params.jump_std)
                    # Add other jump distributions as needed
                    
                # Update path
                paths[i, t+1] = paths[i, t] * np.exp(drift + diffusion + jump)
                
        return paths
    
    def calculate_jump_risk_measures(self) -> Dict[str, float]:
        """Calculate jump-specific risk measures"""
        if not self.fitted:
            raise ValueError("Model must be fitted before calculating risk measures")
            
        # Expected number of jumps per year
        jumps_per_year = self.params.jump_intensity
        
        # Expected jump impact
        expected_jump_return = self.params.jump_mean
        
        # Jump volatility contribution
        jump_variance_contribution = (self.params.jump_intensity * 
                                     (self.params.jump_mean**2 + self.params.jump_std**2))
        
        # Probability of extreme jumps
        if self.params.jump_std > 0:
            prob_large_negative_jump = stats.norm.cdf(-0.1, self.params.jump_mean, self.params.jump_std)
            prob_large_positive_jump = 1 - stats.norm.cdf(0.1, self.params.jump_mean, self.params.jump_std)
        else:
            prob_large_negative_jump = 0
            prob_large_positive_jump = 0
            
        return {
            'jumps_per_year': jumps_per_year,
            'expected_jump_return': expected_jump_return,
            'jump_variance_contribution': jump_variance_contribution,
            'prob_large_negative_jump': prob_large_negative_jump,
            'prob_large_positive_jump': prob_large_positive_jump,
            'diffusion_volatility': self.params.sigma,
            'total_expected_return': self.params.mu + self.params.jump_intensity * self.params.jump_mean
        }

class ExtremeValueRiskModel:
    """
    Extreme Value Theory implementation for tail risk modeling
    Supports GPD for Peaks-over-Threshold and GEV for Block Maxima
    """
    
    def __init__(self, model_type: TailRiskModel = TailRiskModel.GENERALIZED_PARETO):
        self.model_type = model_type
        self.params = None
        self.fitted = False
        self.threshold = None
        self.exceedances = None
        
    def fit(self, returns: np.ndarray, threshold_quantile: float = 0.95) -> ExtremeValueParams:
        """
        Fit extreme value model to tail data
        """
        logger.info(f"Fitting {self.model_type.value} extreme value model")
        
        if self.model_type == TailRiskModel.GENERALIZED_PARETO:
            params = self._fit_gpd(returns, threshold_quantile)
        elif self.model_type == TailRiskModel.GENERALIZED_EXTREME_VALUE:
            params = self._fit_gev(returns)
        else:
            raise ValueError(f"Unsupported tail risk model: {self.model_type}")
            
        self.params = params
        self.fitted = True
        
        return params
    
    def _fit_gpd(self, returns: np.ndarray, threshold_quantile: float) -> ExtremeValueParams:
        """Fit Generalized Pareto Distribution for Peaks-over-Threshold"""
        
        # Determine threshold
        self.threshold = np.percentile(np.abs(returns), threshold_quantile * 100)
        
        # Extract exceedances
        exceedances = np.abs(returns)[np.abs(returns) > self.threshold] - self.threshold
        self.exceedances = exceedances
        
        if len(exceedances) < 10:
            logger.warning("Insufficient exceedances for reliable GPD fitting")
            # Return default parameters
            return ExtremeValueParams(
                threshold=self.threshold,
                shape_parameter=0.1,
                scale_parameter=np.std(returns),
                location_parameter=0.0
            )
        
        # Method of moments for initial estimates
        sample_mean = np.mean(exceedances)
        sample_var = np.var(exceedances)
        
        # Initial parameter estimates
        if sample_var > 0:
            xi_init = 0.5 * (1 - (sample_mean**2 / sample_var))
            sigma_init = sample_mean * (1 - xi_init)
        else:
            xi_init = 0.1
            sigma_init = sample_mean
            
        # Maximum likelihood estimation
        def neg_log_likelihood(params):
            xi, sigma = params
            if sigma <= 0:
                return 1e10
                
            try:
                if abs(xi) < 1e-6:  # Exponential case
                    ll = -len(exceedances) * np.log(sigma) - np.sum(exceedances) / sigma
                else:
                    y = 1 + xi * exceedances / sigma
                    if np.any(y <= 0):
                        return 1e10
                    ll = (-len(exceedances) * np.log(sigma) - 
                          (1 + 1/xi) * np.sum(np.log(y)))
                return -ll
            except:
                return 1e10
        
        # Optimize
        bounds = [(-0.5, 0.5), (1e-6, None)]  # Bounds for xi and sigma
        result = optimize.minimize(
            neg_log_likelihood,
            [xi_init, sigma_init],
            method='L-BFGS-B',
            bounds=bounds
        )
        
        if result.success:
            xi_est, sigma_est = result.x
        else:
            xi_est, sigma_est = xi_init, sigma_init
            logger.warning("GPD optimization failed, using initial estimates")
        
        return ExtremeValueParams(
            threshold=self.threshold,
            shape_parameter=xi_est,
            scale_parameter=sigma_est,
            location_parameter=0.0
        )
    
    def _fit_gev(self, returns: np.ndarray, block_size: int = 22) -> ExtremeValueParams:
        """Fit Generalized Extreme Value Distribution using block maxima"""
        
        # Extract block maxima
        n_blocks = len(returns) // block_size
        block_maxima = []
        
        for i in range(n_blocks):
            block_data = returns[i*block_size:(i+1)*block_size]
            block_maxima.append(np.max(np.abs(block_data)))
            
        block_maxima = np.array(block_maxima)
        
        if len(block_maxima) < 10:
            logger.warning("Insufficient blocks for reliable GEV fitting")
            return ExtremeValueParams(
                threshold=0,
                shape_parameter=0.1,
                scale_parameter=np.std(returns),
                location_parameter=np.mean(block_maxima)
            )
        
        # Fit GEV using scipy.stats
        try:
            # Use scipy's built-in GEV fitting
            shape, loc, scale = stats.genextreme.fit(block_maxima)
            
            return ExtremeValueParams(
                threshold=0,
                shape_parameter=-shape,  # scipy uses negative convention
                scale_parameter=scale,
                location_parameter=loc
            )
        except:
            logger.warning("GEV fitting failed, using method of moments")
            return ExtremeValueParams(
                threshold=0,
                shape_parameter=0.1,
                scale_parameter=np.std(block_maxima),
                location_parameter=np.mean(block_maxima)
            )
    
    def calculate_tail_var_cvar(self, confidence_levels: List[float], 
                               n_observations: int) -> Dict[str, Dict[str, float]]:
        """Calculate tail-based VaR and CVaR estimates"""
        if not self.fitted:
            raise ValueError("Model must be fitted before calculating VaR/CVaR")
            
        results = {}
        
        for alpha in confidence_levels:
            var_cvar = {}
            
            if self.model_type == TailRiskModel.GENERALIZED_PARETO:
                # GPD-based VaR and CVaR
                n_exceedances = len(self.exceedances)
                Nu = n_exceedances / n_observations  # Exceedance probability
                
                xi = self.params.shape_parameter
                sigma = self.params.scale_parameter
                u = self.threshold
                
                # VaR calculation
                if abs(xi) < 1e-6:  # Exponential case
                    var = u + sigma * np.log(Nu / (1 - alpha))
                else:
                    var = u + (sigma / xi) * ((Nu / (1 - alpha))**xi - 1)
                
                # CVaR calculation
                if abs(xi) < 1e-6:
                    cvar = var + sigma
                else:
                    if xi < 1:
                        cvar = var / (1 - xi) + (sigma - xi * u) / ((1 - xi) * (1 - alpha))
                    else:
                        cvar = np.inf  # Heavy tail case
                        
                var_cvar['var'] = var
                var_cvar['cvar'] = cvar if cvar != np.inf else var * 2
                
            elif self.model_type == TailRiskModel.GENERALIZED_EXTREME_VALUE:
                # GEV-based VaR and CVaR
                xi = self.params.shape_parameter
                sigma = self.params.scale_parameter
                mu = self.params.location_parameter
                
                # VaR calculation
                if abs(xi) < 1e-6:
                    var = mu - sigma * np.log(-np.log(alpha))
                else:
                    var = mu + (sigma / xi) * ((-np.log(alpha))**(-xi) - 1)
                
                # CVaR calculation (simplified)
                # For exact calculation, would need numerical integration
                var_cvar['var'] = var
                var_cvar['cvar'] = var * 1.2  # Approximation
                
            results[f'alpha_{alpha:.3f}'] = var_cvar
            
        return results
    
    def estimate_tail_index(self) -> float:
        """Estimate tail index for heavy-tailed behavior assessment"""
        if not self.fitted:
            raise ValueError("Model must be fitted before estimating tail index")
            
        if self.params.shape_parameter > 0:
            # Heavy-tailed case
            tail_index = 1 / self.params.shape_parameter
        else:
            # Light-tailed case  
            tail_index = np.inf
            
        return float(tail_index)

class CopulaRiskModel:
    """
    Copula-based dependency modeling for multivariate risk assessment
    """
    
    def __init__(self, copula_type: str = "gaussian"):
        self.copula_type = copula_type  # "gaussian", "t", "clayton", "gumbel"
        self.params = {}
        self.fitted = False
        self.correlation_matrix = None
        self.marginal_distributions = []
        
    def fit(self, returns_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Fit copula model to multivariate returns
        """
        logger.info(f"Fitting {self.copula_type} copula model")
        
        n_assets = returns_matrix.shape[1]
        
        # Fit marginal distributions
        self.marginal_distributions = []
        uniform_data = np.zeros_like(returns_matrix)
        
        for i in range(n_assets):
            # Fit marginal distribution (using empirical CDF)
            marginal_data = returns_matrix[:, i]
            sorted_data = np.sort(marginal_data)
            
            # Store marginal parameters
            self.marginal_distributions.append({
                'data': sorted_data,
                'mean': np.mean(marginal_data),
                'std': np.std(marginal_data)
            })
            
            # Transform to uniform marginals
            uniform_data[:, i] = stats.rankdata(marginal_data) / (len(marginal_data) + 1)
        
        # Fit copula parameters
        if self.copula_type == "gaussian":
            self.params = self._fit_gaussian_copula(uniform_data)
        elif self.copula_type == "t":
            self.params = self._fit_t_copula(uniform_data)
        elif self.copula_type == "clayton":
            self.params = self._fit_archimedean_copula(uniform_data, "clayton")
        elif self.copula_type == "gumbel":
            self.params = self._fit_archimedean_copula(uniform_data, "gumbel")
        else:
            raise ValueError(f"Unsupported copula type: {self.copula_type}")
        
        self.fitted = True
        return self.params
    
    def _fit_gaussian_copula(self, uniform_data: np.ndarray) -> Dict[str, Any]:
        """Fit Gaussian copula"""
        # Transform to standard normal
        normal_data = stats.norm.ppf(uniform_data)
        
        # Estimate correlation matrix
        self.correlation_matrix = np.corrcoef(normal_data.T)
        
        # Ensure positive definite
        eigenvals, eigenvecs = np.linalg.eigh(self.correlation_matrix)
        eigenvals = np.maximum(eigenvals, 1e-8)
        self.correlation_matrix = eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
        
        return {
            'correlation_matrix': self.correlation_matrix,
            'type': 'gaussian'
        }
    
    def _fit_t_copula(self, uniform_data: np.ndarray) -> Dict[str, Any]:
        """Fit t-copula with estimated degrees of freedom"""
        from scipy.optimize import minimize_scalar
        
        def neg_log_likelihood(nu):
            try:
                # Transform to t-marginals
                t_data = stats.t.ppf(uniform_data, nu)
                if np.any(~np.isfinite(t_data)):
                    return 1e10
                
                # Estimate correlation
                corr_matrix = np.corrcoef(t_data.T)
                
                # Calculate log-likelihood (simplified)
                n = len(uniform_data)
                det_corr = np.linalg.det(corr_matrix)
                if det_corr <= 0:
                    return 1e10
                
                # Simplified likelihood calculation
                ll = -0.5 * n * np.log(det_corr)
                return -ll
            except:
                return 1e10
        
        # Optimize degrees of freedom
        result = minimize_scalar(neg_log_likelihood, bounds=(2.1, 30), method='bounded')
        
        if result.success:
            optimal_nu = result.x
        else:
            optimal_nu = 10.0  # Default value
        
        # Fit correlation with optimal nu
        t_data = stats.t.ppf(uniform_data, optimal_nu)
        self.correlation_matrix = np.corrcoef(t_data.T)
        
        return {
            'correlation_matrix': self.correlation_matrix,
            'degrees_of_freedom': optimal_nu,
            'type': 't'
        }
    
    def _fit_archimedean_copula(self, uniform_data: np.ndarray, 
                               copula_type: str) -> Dict[str, Any]:
        """Fit Archimedean copulas (Clayton, Gumbel)"""
        
        # For simplicity, implement bivariate case
        if uniform_data.shape[1] != 2:
            raise ValueError("Archimedean copulas currently only support bivariate case")
        
        u1, u2 = uniform_data[:, 0], uniform_data[:, 1]
        
        def neg_log_likelihood(theta):
            try:
                if copula_type == "clayton":
                    if theta <= 0:
                        return 1e10
                    # Clayton copula density
                    term1 = (1 + theta) * (u1 * u2)**(-1 - theta)
                    term2 = (u1**(-theta) + u2**(-theta) - 1)**(-1/theta - 2)
                    density = term1 * term2
                elif copula_type == "gumbel":
                    if theta < 1:
                        return 1e10
                    # Gumbel copula density (simplified)
                    a = (-np.log(u1))**theta + (-np.log(u2))**theta
                    c = np.exp(-a**(1/theta))
                    
                    term1 = c / (u1 * u2)
                    term2 = a**(-2 + 2/theta)
                    term3 = (np.log(u1) * np.log(u2))**(theta - 1)
                    term4 = (theta - 1) * a**(-1 + 1/theta) + a**(2/theta)
                    density = term1 * term2 * term3 * term4
                    
                density = np.maximum(density, 1e-10)  # Prevent log(0)
                ll = np.sum(np.log(density))
                return -ll
            except:
                return 1e10
        
        # Optimize parameter
        if copula_type == "clayton":
            bounds = (0.1, 20)
        else:  # gumbel
            bounds = (1.1, 20)
            
        result = minimize_scalar(neg_log_likelihood, bounds=bounds, method='bounded')
        
        if result.success:
            optimal_theta = result.x
        else:
            optimal_theta = 1.5 if copula_type == "gumbel" else 0.5
        
        return {
            'theta': optimal_theta,
            'type': copula_type
        }
    
    def calculate_tail_dependence(self) -> Dict[str, float]:
        """Calculate tail dependence coefficients"""
        if not self.fitted:
            raise ValueError("Model must be fitted before calculating tail dependence")
        
        if self.copula_type == "gaussian":
            # Gaussian copula has zero tail dependence
            return {'upper_tail': 0.0, 'lower_tail': 0.0}
        elif self.copula_type == "t":
            # t-copula has symmetric tail dependence
            nu = self.params['degrees_of_freedom']
            rho = self.correlation_matrix[0, 1] if self.correlation_matrix.shape[0] > 1 else 0
            
            tail_dep = 2 * stats.t.cdf(-np.sqrt((nu + 1) * (1 - rho) / (1 + rho)), nu + 1)
            return {'upper_tail': tail_dep, 'lower_tail': tail_dep}
        elif self.copula_type == "clayton":
            # Clayton copula
            theta = self.params['theta']
            lower_tail = 2**(-1/theta) if theta > 0 else 0
            return {'upper_tail': 0.0, 'lower_tail': lower_tail}
        elif self.copula_type == "gumbel":
            # Gumbel copula
            theta = self.params['theta']
            upper_tail = 2 - 2**(1/theta) if theta >= 1 else 0
            return {'upper_tail': upper_tail, 'lower_tail': 0.0}
        
        return {'upper_tail': 0.0, 'lower_tail': 0.0}

class FactorRiskModel:
    """
    Factor-based risk model for systematic risk decomposition
    """
    
    def __init__(self, n_factors: int = 3):
        self.n_factors = n_factors
        self.factor_loadings = None
        self.factor_returns = None
        self.idiosyncratic_risk = None
        self.fitted = False
        
    def fit(self, returns_matrix: np.ndarray, method: str = "pca") -> Dict[str, np.ndarray]:
        """
        Fit factor model using PCA or Factor Analysis
        """
        logger.info(f"Fitting factor risk model with {self.n_factors} factors using {method}")
        
        if method == "pca":
            model = PCA(n_components=self.n_factors)
        elif method == "factor_analysis":
            model = FactorAnalysis(n_components=self.n_factors, random_state=42)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Standardize returns
        scaler = StandardScaler()
        standardized_returns = scaler.fit_transform(returns_matrix)
        
        # Fit model
        factor_returns = model.fit_transform(standardized_returns)
        
        if method == "pca":
            factor_loadings = model.components_.T
            explained_variance = model.explained_variance_ratio_
        else:
            factor_loadings = model.components_.T
            explained_variance = np.var(factor_returns, axis=0) / np.sum(np.var(standardized_returns, axis=1))
        
        # Calculate idiosyncratic risk
        reconstructed_returns = factor_returns @ factor_loadings.T
        residuals = standardized_returns - reconstructed_returns
        idiosyncratic_risk = np.var(residuals, axis=0)
        
        self.factor_loadings = factor_loadings
        self.factor_returns = factor_returns
        self.idiosyncratic_risk = idiosyncratic_risk
        self.fitted = True
        
        return {
            'factor_loadings': factor_loadings,
            'factor_returns': factor_returns,
            'idiosyncratic_risk': idiosyncratic_risk,
            'explained_variance': explained_variance
        }
    
    def calculate_portfolio_risk_decomposition(self, weights: np.ndarray) -> Dict[str, float]:
        """Decompose portfolio risk into factor and idiosyncratic components"""
        if not self.fitted:
            raise ValueError("Model must be fitted before risk decomposition")
        
        # Factor contribution to portfolio variance
        portfolio_loadings = self.factor_loadings.T @ weights
        factor_covariance = np.cov(self.factor_returns.T)
        factor_contribution = portfolio_loadings.T @ factor_covariance @ portfolio_loadings
        
        # Idiosyncratic contribution
        idiosyncratic_contribution = np.sum((weights**2) * self.idiosyncratic_risk)
        
        # Total portfolio variance
        total_variance = factor_contribution + idiosyncratic_contribution
        
        return {
            'total_variance': total_variance,
            'factor_contribution': factor_contribution,
            'idiosyncratic_contribution': idiosyncratic_contribution,
            'factor_contribution_pct': factor_contribution / total_variance * 100,
            'idiosyncratic_contribution_pct': idiosyncratic_contribution / total_variance * 100,
            'total_volatility': np.sqrt(total_variance),
            'factor_volatility': np.sqrt(factor_contribution),
            'idiosyncratic_volatility': np.sqrt(idiosyncratic_contribution)
        }

class IntegratedRiskModelFramework:
    """
    Comprehensive risk modeling framework combining all risk models
    """
    
    def __init__(self):
        self.garch_model = None
        self.jump_model = None
        self.extreme_value_model = None
        self.copula_model = None
        self.factor_model = None
        self.fitted_models = {}
        
    def fit_comprehensive_risk_model(self, returns_matrix: np.ndarray) -> Dict[str, Any]:
        """Fit all risk models to the data"""
        
        logger.info("Fitting comprehensive risk model framework")
        results = {}
        
        # Fit GARCH models for each asset
        garch_results = {}
        for i in range(returns_matrix.shape[1]):
            asset_returns = returns_matrix[:, i]
            garch_model = GARCHModel()
            try:
                garch_params = garch_model.fit(asset_returns)
                garch_results[f'asset_{i}'] = {
                    'params': garch_params,
                    'diagnostics': garch_model.get_model_diagnostics()
                }
            except Exception as e:
                logger.warning(f"GARCH fitting failed for asset {i}: {e}")
                
        results['garch'] = garch_results
        
        # Fit Jump Diffusion model (on market proxy - first asset)
        try:
            jump_model = JumpDiffusionRiskModel()
            jump_params = jump_model.fit(returns_matrix[:, 0])
            results['jump_diffusion'] = {
                'params': jump_params,
                'risk_measures': jump_model.calculate_jump_risk_measures()
            }
        except Exception as e:
            logger.warning(f"Jump diffusion fitting failed: {e}")
        
        # Fit Extreme Value model
        try:
            evt_model = ExtremeValueRiskModel()
            evt_params = evt_model.fit(returns_matrix[:, 0])
            results['extreme_value'] = {
                'params': evt_params,
                'tail_var_cvar': evt_model.calculate_tail_var_cvar([0.95, 0.99], len(returns_matrix)),
                'tail_index': evt_model.estimate_tail_index()
            }
        except Exception as e:
            logger.warning(f"Extreme value fitting failed: {e}")
        
        # Fit Copula model (if multivariate)
        if returns_matrix.shape[1] > 1:
            try:
                copula_model = CopulaRiskModel()
                copula_params = copula_model.fit(returns_matrix)
                results['copula'] = {
                    'params': copula_params,
                    'tail_dependence': copula_model.calculate_tail_dependence()
                }
            except Exception as e:
                logger.warning(f"Copula fitting failed: {e}")
        
        # Fit Factor model
        if returns_matrix.shape[1] > 3:  # Need enough assets
            try:
                factor_model = FactorRiskModel(n_factors=min(3, returns_matrix.shape[1]-1))
                factor_results = factor_model.fit(returns_matrix)
                results['factor_model'] = factor_results
            except Exception as e:
                logger.warning(f"Factor model fitting failed: {e}")
        
        return results
    
    def calculate_integrated_risk_metrics(self, returns_matrix: np.ndarray, 
                                        weights: np.ndarray = None) -> RiskMetrics:
        """Calculate comprehensive risk metrics using all fitted models"""
        
        if weights is None:
            weights = np.ones(returns_matrix.shape[1]) / returns_matrix.shape[1]
        
        # Portfolio returns
        portfolio_returns = returns_matrix @ weights
        
        # Basic risk metrics
        var_95 = np.percentile(portfolio_returns, 5)
        var_99 = np.percentile(portfolio_returns, 1)
        cvar_95 = np.mean(portfolio_returns[portfolio_returns <= var_95])
        cvar_99 = np.mean(portfolio_returns[portfolio_returns <= var_99])
        
        # Maximum drawdown
        cumulative_returns = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # Volatility clustering (GARCH-based)
        volatility_clustering = 0.0
        if len(portfolio_returns) > 50:
            # Simple measure: correlation between squared returns
            squared_returns = portfolio_returns**2
            volatility_clustering = np.corrcoef(
                squared_returns[:-1], squared_returns[1:]
            )[0, 1]
        
        # Tail indices (placeholder - would use fitted EVT models)
        tail_indices = {'gpd_tail_index': 3.0}  # Default value
        
        # Tail dependence (placeholder - would use fitted copula models)
        tail_dependence = {'upper_tail': 0.1, 'lower_tail': 0.1}
        
        # Correlation breakdown detection
        correlation_breakdown = False
        if returns_matrix.shape[1] > 1:
            # Simple heuristic: check if correlations exceed historical levels
            recent_corr = np.corrcoef(returns_matrix[-50:].T) if len(returns_matrix) >= 50 else np.corrcoef(returns_matrix.T)
            historical_corr = np.corrcoef(returns_matrix.T)
            
            # Check if correlations increased significantly
            correlation_breakdown = np.mean(recent_corr - historical_corr) > 0.2
        
        return RiskMetrics(
            var_estimates={
                'var_95': var_95,
                'var_99': var_99,
                'historical_var_95': var_95,
                'parametric_var_95': var_95  # Placeholder
            },
            cvar_estimates={
                'cvar_95': cvar_95,
                'cvar_99': cvar_99
            },
            tail_indices=tail_indices,
            maximum_drawdown=max_drawdown,
            volatility_clustering=volatility_clustering,
            tail_dependence=tail_dependence,
            correlation_breakdown=correlation_breakdown,
            model_diagnostics={
                'portfolio_volatility': np.std(portfolio_returns),
                'portfolio_skewness': stats.skew(portfolio_returns),
                'portfolio_kurtosis': stats.kurtosis(portfolio_returns),
                'jarque_bera_pvalue': stats.jarque_bera(portfolio_returns)[1]
            }
        )

# Example usage and testing
def demo_risk_models():
    """Demonstrate all risk models with synthetic data"""
    
    # Generate synthetic return data
    np.random.seed(42)
    n_days = 1000
    n_assets = 3
    
    # Generate correlated returns with regime switching
    base_returns = np.random.multivariate_normal(
        [0.0005, 0.0003, 0.0004],  # Daily returns
        [[0.0004, 0.0001, 0.0002],
         [0.0001, 0.0001, 0.0001],
         [0.0002, 0.0001, 0.0003]],
        n_days
    )
    
    # Add jumps and regime switching
    for i in range(n_assets):
        # Add occasional jumps
        jump_times = np.random.poisson(0.05, n_days)  # 5% chance per day
        for t in range(n_days):
            if jump_times[t] > 0:
                base_returns[t, i] += np.random.normal(-0.02, 0.01)  # Negative jumps
    
    returns_matrix = base_returns
    
    # Initialize framework
    framework = IntegratedRiskModelFramework()
    
    # Fit all models
    print("Fitting comprehensive risk models...")
    model_results = framework.fit_comprehensive_risk_model(returns_matrix)
    
    # Print results
    print("\n=== Risk Model Results ===")
    
    if 'garch' in model_results:
        print(f"\nGARCH Models fitted for {len(model_results['garch'])} assets")
        
    if 'jump_diffusion' in model_results:
        jump_measures = model_results['jump_diffusion']['risk_measures']
        print(f"\nJump Diffusion Model:")
        print(f"  Expected jumps per year: {jump_measures['jumps_per_year']:.2f}")
        print(f"  Expected jump return: {jump_measures['expected_jump_return']:.4f}")
        
    if 'extreme_value' in model_results:
        tail_measures = model_results['extreme_value']['tail_var_cvar']
        print(f"\nExtreme Value Theory:")
        print(f"  Tail index: {model_results['extreme_value']['tail_index']:.2f}")
        for level, measures in tail_measures.items():
            print(f"  {level} - VaR: {measures['var']:.4f}, CVaR: {measures['cvar']:.4f}")
    
    # Calculate integrated risk metrics
    risk_metrics = framework.calculate_integrated_risk_metrics(returns_matrix)
    
    print(f"\n=== Integrated Risk Metrics ===")
    print(f"VaR (95%): {risk_metrics.var_estimates['var_95']:.4f}")
    print(f"CVaR (95%): {risk_metrics.cvar_estimates['cvar_95']:.4f}")
    print(f"Maximum Drawdown: {risk_metrics.maximum_drawdown:.4f}")
    print(f"Volatility Clustering: {risk_metrics.volatility_clustering:.3f}")
    print(f"Correlation Breakdown: {risk_metrics.correlation_breakdown}")
    print(f"Portfolio Volatility: {risk_metrics.model_diagnostics['portfolio_volatility']:.4f}")

if __name__ == "__main__":
    demo_risk_models()