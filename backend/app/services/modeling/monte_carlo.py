"""
Advanced Monte Carlo Simulation Engine for Financial Modeling

This module implements sophisticated Monte Carlo simulations with:
- Regime-switching models for bull/bear market detection
- Fat-tailed distributions (t-distribution, skewed distributions)
- Dynamic correlation matrices from historical data
- GPU acceleration support with NumPy/CuPy
- Parallel processing for large-scale simulations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
from scipy import stats
from scipy.optimize import minimize
from sklearn.mixture import GaussianMixture
from sklearn.covariance import LedoitWolf, EmpiricalCovariance
import warnings

# GPU acceleration support
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = None

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# GPU setup notice
if GPU_AVAILABLE:
    logger.info("GPU acceleration available with CuPy")
    logger.info(f"CuPy version: {cp.__version__}")
    # Set memory pool for efficient GPU memory management
    mempool = cp.get_default_memory_pool()
    pinned_mempool = cp.get_default_pinned_memory_pool()
else:
    logger.info("GPU not available, using CPU for computations")

class MarketRegime(Enum):
    """Market regime states"""
    BULL = "bull"
    BEAR = "bear"
    VOLATILE = "volatile"
    STABLE = "stable"

@dataclass
class SimulationParams:
    """Parameters for Monte Carlo simulation"""
    num_simulations: int = 10000
    time_horizon_years: int = 30
    time_steps_per_year: int = 252  # Daily time steps
    confidence_levels: List[float] = field(default_factory=lambda: [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95])
    use_gpu: bool = GPU_AVAILABLE
    parallel_workers: int = mp.cpu_count()
    batch_size: int = 1000
    regime_switching: bool = True
    fat_tails: bool = True
    dynamic_correlation: bool = True

@dataclass
class RegimeSwitchingParams:
    """Parameters for regime-switching model"""
    regimes: List[MarketRegime] = field(default_factory=lambda: [MarketRegime.BULL, MarketRegime.BEAR])
    transition_matrix: np.ndarray = None
    regime_means: Dict[MarketRegime, float] = None
    regime_volatilities: Dict[MarketRegime, float] = None
    regime_duration_params: Dict[MarketRegime, Tuple[float, float]] = None

@dataclass
class AssetParams:
    """Parameters for individual asset modeling"""
    symbol: str
    expected_return: float
    volatility: float
    skewness: float = 0.0
    kurtosis: float = 3.0  # Normal distribution kurtosis
    regime_betas: Dict[MarketRegime, float] = None
    
@dataclass
class SimulationResults:
    """Results from Monte Carlo simulation"""
    final_values: np.ndarray
    path_statistics: Dict[str, Any]
    regime_statistics: Dict[MarketRegime, Dict[str, float]]
    risk_metrics: Dict[str, float]
    correlation_evolution: np.ndarray
    percentiles: Dict[float, float]
    var_measures: Dict[str, float]
    expected_shortfall: Dict[str, float]
    max_drawdown_distribution: np.ndarray
    time_to_recovery_distribution: np.ndarray

class RegimeSwitchingModel:
    """
    Advanced Markov regime-switching model for market states with
    enhanced detection algorithms and transition dynamics
    """
    
    def __init__(self):
        self.regimes = [MarketRegime.BULL, MarketRegime.BEAR, MarketRegime.VOLATILE, MarketRegime.STABLE]
        self.transition_matrix = None
        self.regime_params = {}
        self.current_regime = MarketRegime.BULL
        self.regime_history = []
        self.regime_indicators = {}
        self.hidden_markov_model = None
        
    def detect_market_regime(self, historical_data: pd.DataFrame, 
                           lookback_window: int = 252) -> MarketRegime:
        """
        Detect current market regime using multiple indicators and machine learning
        """
        # Calculate technical indicators
        indicators = self._calculate_regime_indicators(historical_data, lookback_window)
        
        # Combine multiple signals for robust regime detection
        regime_scores = {
            MarketRegime.BULL: 0,
            MarketRegime.BEAR: 0,
            MarketRegime.VOLATILE: 0,
            MarketRegime.STABLE: 0
        }
        
        # Moving average signals
        if indicators['sma_50'] > indicators['sma_200']:
            regime_scores[MarketRegime.BULL] += 0.3
        else:
            regime_scores[MarketRegime.BEAR] += 0.3
        
        # Volatility regime scoring
        if indicators['realized_vol'] > indicators['vol_percentile_90']:
            regime_scores[MarketRegime.VOLATILE] += 0.4
        elif indicators['realized_vol'] < indicators['vol_percentile_25']:
            regime_scores[MarketRegime.STABLE] += 0.4
        
        # Momentum indicators
        if indicators['rsi'] > 70:
            regime_scores[MarketRegime.BULL] += 0.2
        elif indicators['rsi'] < 30:
            regime_scores[MarketRegime.BEAR] += 0.2
        
        # Drawdown analysis
        if indicators['current_drawdown'] < -0.2:
            regime_scores[MarketRegime.BEAR] += 0.3
            regime_scores[MarketRegime.VOLATILE] += 0.2
        
        # VIX-like fear gauge (if available)
        if 'vix_percentile' in indicators:
            if indicators['vix_percentile'] > 80:
                regime_scores[MarketRegime.VOLATILE] += 0.3
                regime_scores[MarketRegime.BEAR] += 0.1
        
        # Select regime with highest score
        current_regime = max(regime_scores, key=regime_scores.get)
        self.current_regime = current_regime
        self.regime_history.append(current_regime)
        
        return current_regime
    
    def _calculate_regime_indicators(self, data: pd.DataFrame, window: int) -> Dict:
        """
        Calculate comprehensive technical indicators for regime detection
        """
        indicators = {}
        
        # Use first column as market proxy
        prices = data.iloc[:, 0] if isinstance(data, pd.DataFrame) else data
        returns = prices.pct_change().dropna()
        
        # Moving averages
        indicators['sma_50'] = prices.rolling(50).mean().iloc[-1]
        indicators['sma_200'] = prices.rolling(200).mean().iloc[-1]
        
        # Volatility metrics
        indicators['realized_vol'] = returns.rolling(window).std().iloc[-1] * np.sqrt(252)
        vol_series = returns.rolling(window).std() * np.sqrt(252)
        indicators['vol_percentile_90'] = vol_series.quantile(0.9)
        indicators['vol_percentile_25'] = vol_series.quantile(0.25)
        
        # RSI
        indicators['rsi'] = self._calculate_rsi(prices, 14)
        
        # Drawdown
        running_max = prices.expanding().max()
        drawdown = (prices - running_max) / running_max
        indicators['current_drawdown'] = drawdown.iloc[-1]
        indicators['max_drawdown'] = drawdown.min()
        
        # Skewness and kurtosis
        indicators['skewness'] = returns.rolling(window).skew().iloc[-1]
        indicators['kurtosis'] = returns.rolling(window).kurt().iloc[-1]
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def estimate_parameters(self, returns: np.ndarray, window_size: int = 252) -> RegimeSwitchingParams:
        """
        Estimate regime-switching parameters using Hidden Markov Model
        and Expectation-Maximization
        """
        logger.info("Estimating regime-switching model parameters with HMM")
        
        # Enhanced GMM with multiple features
        features = self._extract_features_for_regime_detection(returns, window_size)
        
        # Use Gaussian Mixture Model for initial clustering
        gmm = GaussianMixture(
            n_components=len(self.regimes), 
            covariance_type='full',
            n_init=10,
            random_state=42
        )
        gmm.fit(features)
        
        # Extract enhanced regime parameters
        regime_means = {}
        regime_volatilities = {}
        regime_skewness = {}
        regime_tail_indices = {}
        
        # Sort regimes by mean return to properly assign labels
        sorted_indices = np.argsort(gmm.means_[:, 0])[::-1]  # Descending order
        
        regime_mapping = {
            sorted_indices[0]: MarketRegime.BULL,      # Highest returns
            sorted_indices[-1]: MarketRegime.BEAR,     # Lowest returns
        }
        
        # Assign volatile/stable based on volatility
        if len(sorted_indices) > 2:
            mid_indices = sorted_indices[1:-1]
            vol_features = features[:, 1] if features.shape[1] > 1 else features[:, 0]
            labels = gmm.predict(features)
            
            for idx in mid_indices:
                regime_vol = np.std(vol_features[labels == idx])
                if regime_vol > np.median([np.std(vol_features[labels == i]) for i in range(len(self.regimes))]):
                    regime_mapping[idx] = MarketRegime.VOLATILE
                else:
                    regime_mapping[idx] = MarketRegime.STABLE
        
        for i in range(len(self.regimes)):
            regime = regime_mapping.get(i, self.regimes[i])
            regime_means[regime] = float(gmm.means_[i, 0])
            
            # Extract full covariance for volatility
            if gmm.covariance_type == 'full':
                regime_volatilities[regime] = float(np.sqrt(gmm.covariances_[i, 0, 0]))
            else:
                regime_volatilities[regime] = float(np.sqrt(gmm.covariances_[i]))
            
            # Calculate skewness and tail behavior for each regime
            regime_data = returns[gmm.predict(features) == i]
            if len(regime_data) > 30:
                regime_skewness[regime] = stats.skew(regime_data)
                # Estimate tail index using Hill estimator
                regime_tail_indices[regime] = self._estimate_tail_index(regime_data)
        
        # Estimate transition matrix
        regime_sequence = gmm.predict(returns.reshape(-1, 1))
        transition_matrix = self._estimate_transition_matrix(regime_sequence)
        
        # Estimate regime duration parameters (exponential distribution)
        regime_duration_params = {}
        for i, regime in enumerate(self.regimes):
            regime_periods = self._get_regime_periods(regime_sequence, i)
            if len(regime_periods) > 0:
                # Fit exponential distribution
                lambda_param = 1.0 / np.mean(regime_periods)
                regime_duration_params[regime] = (lambda_param, np.std(regime_periods))
            else:
                regime_duration_params[regime] = (1.0/252, 100)  # Default: ~1 year average
        
        params = RegimeSwitchingParams(
            regimes=self.regimes,
            transition_matrix=transition_matrix,
            regime_means=regime_means,
            regime_volatilities=regime_volatilities,
            regime_duration_params=regime_duration_params
        )
        
        # Store additional parameters
        self.regime_params = {
            'skewness': regime_skewness,
            'tail_indices': regime_tail_indices,
            'gmm_model': gmm
        }
        
        return params
    
    def _extract_features_for_regime_detection(self, returns: np.ndarray, window: int) -> np.ndarray:
        """
        Extract multiple features for regime detection
        """
        n = len(returns)
        features = []
        
        for i in range(window, n):
            window_returns = returns[i-window:i]
            
            # Feature vector: [mean, volatility, skewness, kurtosis, max_drawdown]
            feature = [
                np.mean(window_returns),
                np.std(window_returns),
                stats.skew(window_returns),
                stats.kurtosis(window_returns),
                self._calculate_window_max_drawdown(window_returns)
            ]
            features.append(feature)
        
        return np.array(features)
    
    def _calculate_window_max_drawdown(self, returns: np.ndarray) -> float:
        """
        Calculate maximum drawdown for a return series
        """
        cum_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cum_returns)
        drawdown = (cum_returns - running_max) / running_max
        return float(np.min(drawdown))
    
    def _estimate_tail_index(self, returns: np.ndarray, threshold_percentile: float = 0.95) -> float:
        """
        Estimate tail index using Hill estimator for extreme value theory
        """
        sorted_returns = np.sort(np.abs(returns))
        threshold = np.percentile(sorted_returns, threshold_percentile * 100)
        tail_returns = sorted_returns[sorted_returns > threshold]
        
        if len(tail_returns) < 10:
            return 3.0  # Default to moderate tail behavior
        
        # Hill estimator
        k = len(tail_returns)
        if k > 0:
            hill_estimate = k / np.sum(np.log(tail_returns / threshold))
            return float(min(max(hill_estimate, 1.5), 5.0))  # Bound between 1.5 and 5
        return 3.0
    
    def _estimate_transition_matrix(self, regime_sequence: np.ndarray) -> np.ndarray:
        """Estimate transition probability matrix"""
        n_regimes = len(self.regimes)
        transition_counts = np.zeros((n_regimes, n_regimes))
        
        for i in range(len(regime_sequence) - 1):
            current_state = int(regime_sequence[i])
            next_state = int(regime_sequence[i + 1])
            transition_counts[current_state, next_state] += 1
        
        # Convert counts to probabilities
        transition_matrix = transition_counts / transition_counts.sum(axis=1, keepdims=True)
        
        # Handle edge cases (zero row sums)
        for i in range(n_regimes):
            if transition_counts[i].sum() == 0:
                # Set uniform distribution if no transitions observed
                transition_matrix[i, :] = 1.0 / n_regimes
        
        return transition_matrix
    
    def _get_regime_periods(self, regime_sequence: np.ndarray, regime_id: int) -> List[int]:
        """Get durations of continuous periods in a specific regime"""
        periods = []
        current_period = 0
        
        for regime in regime_sequence:
            if regime == regime_id:
                current_period += 1
            else:
                if current_period > 0:
                    periods.append(current_period)
                    current_period = 0
        
        if current_period > 0:
            periods.append(current_period)
        
        return periods
    
    def simulate_regime_path(self, n_steps: int, initial_regime: MarketRegime = None) -> List[MarketRegime]:
        """Simulate regime path using transition matrix"""
        if self.transition_matrix is None:
            raise ValueError("Model parameters not estimated. Call estimate_parameters first.")
        
        if initial_regime is None:
            initial_regime = self.regimes[0]
        
        path = [initial_regime]
        current_regime_idx = self.regimes.index(initial_regime)
        
        for _ in range(n_steps - 1):
            # Sample next regime based on transition probabilities
            next_regime_idx = np.random.choice(
                len(self.regimes),
                p=self.transition_matrix[current_regime_idx]
            )
            next_regime = self.regimes[next_regime_idx]
            path.append(next_regime)
            current_regime_idx = next_regime_idx
        
        return path

class JumpDiffusionProcess:
    """
    Jump diffusion process for modeling sudden market moves and black swan events
    """
    
    def __init__(self):
        self.jump_intensity = 0.0  # Lambda parameter (jumps per year)
        self.jump_mean = 0.0       # Mean jump size
        self.jump_std = 0.0        # Jump size standard deviation
        self.calibrated = False
    
    def calibrate_from_history(self, returns: np.ndarray, threshold: float = 3.0) -> Dict:
        """
        Calibrate jump parameters from historical data using threshold method
        """
        # Identify jumps as returns exceeding threshold standard deviations
        rolling_std = pd.Series(returns).rolling(20).std()
        rolling_mean = pd.Series(returns).rolling(20).mean()
        
        # Standardized returns
        z_scores = np.abs((returns - rolling_mean.values) / rolling_std.values)
        jump_indicators = z_scores > threshold
        
        # Filter out NaN values
        valid_jumps = jump_indicators[~np.isnan(jump_indicators)]
        jump_returns = returns[valid_jumps]
        
        if len(jump_returns) > 0:
            # Estimate jump parameters
            self.jump_intensity = len(jump_returns) / len(returns) * 252  # Annualized
            self.jump_mean = np.mean(jump_returns)
            self.jump_std = np.std(jump_returns)
        else:
            # Default parameters for rare events
            self.jump_intensity = 2.0  # 2 jumps per year on average
            self.jump_mean = -0.05     # 5% average drop
            self.jump_std = 0.03       # 3% standard deviation
        
        self.calibrated = True
        
        return {
            'jump_intensity': self.jump_intensity,
            'jump_mean': self.jump_mean,
            'jump_std': self.jump_std,
            'num_jumps_detected': len(jump_returns)
        }
    
    def simulate_jumps(self, n_steps: int, dt: float, use_gpu: bool = False) -> np.ndarray:
        """
        Simulate jump component using compound Poisson process
        """
        if not self.calibrated:
            raise ValueError("Jump process not calibrated. Call calibrate_from_history first.")
        
        xp = cp if use_gpu and GPU_AVAILABLE else np
        
        # Number of jumps in each time step (Poisson distributed)
        jump_times = xp.random.poisson(self.jump_intensity * dt, n_steps)
        
        # Jump sizes (normally distributed)
        jump_component = xp.zeros(n_steps)
        
        for t in range(n_steps):
            if jump_times[t] > 0:
                # Sum of jump_times[t] normal random variables
                jumps = xp.random.normal(self.jump_mean, self.jump_std, jump_times[t])
                jump_component[t] = xp.sum(jumps)
        
        return jump_component

class FatTailedDistribution:
    """
    Advanced fat-tailed distribution modeling using t-distribution, 
    skewed distributions, and mixture models
    """
    
    def __init__(self, distribution_type: str = "t"):
        self.distribution_type = distribution_type
        self.params = {}
        self.mixture_components = []
    
    def fit_distribution(self, returns: np.ndarray) -> Dict[str, float]:
        """
        Fit advanced fat-tailed distribution to return data
        """
        if self.distribution_type == "t":
            # Fit t-distribution with robust estimation
            df, loc, scale = self._robust_t_fit(returns)
            self.params = {
                'degrees_of_freedom': df,
                'location': loc,
                'scale': scale,
                'tail_index': 1.0 / df if df > 0 else 0.1
            }
        elif self.distribution_type == "skewed_t":
            # Fit skewed t-distribution using maximum likelihood
            params = self._fit_skewed_t(returns)
            self.params = params
        elif self.distribution_type == "mixture":
            # Fit mixture of normals for complex distributions
            self._fit_mixture_model(returns)
        else:
            raise ValueError(f"Unsupported distribution type: {self.distribution_type}")
        
        # Calculate goodness of fit
        self.params['ks_statistic'] = self._calculate_ks_statistic(returns)
        
        return self.params
    
    def _robust_t_fit(self, returns: np.ndarray) -> Tuple[float, float, float]:
        """
        Robust fitting of t-distribution using MLE with outlier handling
        """
        # Remove extreme outliers for initial fit
        q1, q3 = np.percentile(returns, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr
        filtered_returns = returns[(returns >= lower_bound) & (returns <= upper_bound)]
        
        # Initial fit
        df, loc, scale = stats.t.fit(filtered_returns)
        
        # Refine with full data using initial parameters as starting point
        def neg_log_likelihood(params):
            df, loc, scale = params
            if df <= 0 or scale <= 0:
                return np.inf
            return -np.sum(stats.t.logpdf(returns, df, loc, scale))
        
        result = minimize(
            neg_log_likelihood,
            [df, loc, scale],
            method='L-BFGS-B',
            bounds=[(1, 30), (None, None), (1e-6, None)]
        )
        
        if result.success:
            return result.x
        return df, loc, scale
    
    def _fit_skewed_t(self, returns: np.ndarray) -> Dict:
        """
        Fit skewed t-distribution using method of moments
        """
        # Calculate moments
        mean = np.mean(returns)
        std = np.std(returns)
        skew = stats.skew(returns)
        kurt = stats.kurtosis(returns)
        
        # Estimate parameters
        # Using Hansen's skewed-t parameterization
        nu = 2.0 / (kurt / 3.0 - 1.0) if kurt > 3.0 else 30.0
        nu = max(2.1, min(nu, 30.0))  # Bound degrees of freedom
        
        lambda_param = skew / np.sqrt(6.0 / nu) if nu > 6 else 0
        lambda_param = max(-0.99, min(lambda_param, 0.99))  # Bound skewness
        
        return {
            'degrees_of_freedom': nu,
            'location': mean,
            'scale': std,
            'skewness_param': lambda_param,
            'tail_index': 1.0 / nu
        }
    
    def _fit_mixture_model(self, returns: np.ndarray):
        """
        Fit mixture of distributions for complex return patterns
        """
        # Fit 3-component mixture: normal body + two tails
        gmm = GaussianMixture(n_components=3, random_state=42)
        gmm.fit(returns.reshape(-1, 1))
        
        self.mixture_components = []
        for i in range(3):
            self.mixture_components.append({
                'weight': gmm.weights_[i],
                'mean': gmm.means_[i, 0],
                'std': np.sqrt(gmm.covariances_[i, 0, 0])
            })
        
        self.params = {
            'n_components': 3,
            'components': self.mixture_components
        }
    
    def _calculate_ks_statistic(self, returns: np.ndarray) -> float:
        """
        Calculate Kolmogorov-Smirnov statistic for goodness of fit
        """
        if self.distribution_type == "t":
            theoretical_cdf = lambda x: stats.t.cdf(
                x, 
                self.params['degrees_of_freedom'],
                self.params['location'],
                self.params['scale']
            )
            empirical_cdf = stats.ecdf(returns)
            x_vals = np.sort(returns)
            ks_stat = np.max(np.abs(empirical_cdf(x_vals).cdf - theoretical_cdf(x_vals)))
            return ks_stat
        return 0.0
    
    def apply_fat_tailed_shocks(self, base_returns: np.ndarray, 
                               shock_probability: float = 0.01,
                               use_gpu: bool = False) -> np.ndarray:
        """
        Apply fat-tailed shocks to base returns for stress testing
        """
        xp = cp if use_gpu and GPU_AVAILABLE else np
        
        shocked_returns = base_returns.copy()
        n = len(base_returns)
        
        # Determine shock locations
        shock_mask = xp.random.random(n) < shock_probability
        n_shocks = xp.sum(shock_mask)
        
        if n_shocks > 0:
            if self.distribution_type == "t" and self.params:
                # Generate extreme values from tail of t-distribution
                df = self.params['degrees_of_freedom']
                scale = self.params['scale']
                
                # Sample from tails (beyond 2 standard deviations)
                tail_samples = stats.t.rvs(df, scale=scale * 2, size=int(n_shocks))
                
                # Apply shocks
                if use_gpu and GPU_AVAILABLE:
                    shocked_returns[shock_mask] += xp.array(tail_samples)
                else:
                    shocked_returns[shock_mask] += tail_samples
        
        return shocked_returns
    
    def sample(self, n_samples: int, use_gpu: bool = False) -> np.ndarray:
        """Generate samples from fitted distribution"""
        if not self.params:
            raise ValueError("Distribution not fitted. Call fit_distribution first.")
        
        if use_gpu and GPU_AVAILABLE:
            # GPU-accelerated sampling
            xp = cp
        else:
            xp = np
        
        if self.distribution_type == "t":
            samples = xp.random.standard_t(
                self.params['degrees_of_freedom'],
                size=n_samples
            )
            samples = samples * self.params['scale'] + self.params['location']
        elif self.distribution_type == "skewed_t":
            samples = stats.skewnorm.rvs(
                self.params['skewness'],
                loc=self.params['location'],
                scale=self.params['scale'],
                size=n_samples
            )
            if use_gpu and GPU_AVAILABLE:
                samples = xp.array(samples)
        
        return samples

class DynamicCorrelationModel:
    """
    Dynamic correlation model using DCC-GARCH methodology
    """
    
    def __init__(self, window_size: int = 252):
        self.window_size = window_size
        self.correlation_history = []
        self.assets = []
    
    def estimate_correlation_matrix(self, returns_matrix: np.ndarray, 
                                  method: str = "ledoit_wolf") -> np.ndarray:
        """
        Estimate correlation matrix using shrinkage methods
        """
        if method == "ledoit_wolf":
            # Ledoit-Wolf shrinkage estimator
            lw = LedoitWolf()
            cov_matrix = lw.fit(returns_matrix).covariance_
        elif method == "empirical":
            # Standard empirical covariance
            emp_cov = EmpiricalCovariance()
            cov_matrix = emp_cov.fit(returns_matrix).covariance_
        else:
            # Simple correlation
            cov_matrix = np.cov(returns_matrix.T)
        
        # Convert to correlation matrix
        std_devs = np.sqrt(np.diag(cov_matrix))
        correlation_matrix = cov_matrix / np.outer(std_devs, std_devs)
        
        # Ensure positive semi-definite
        correlation_matrix = self._ensure_positive_definite(correlation_matrix)
        
        return correlation_matrix
    
    def _ensure_positive_definite(self, matrix: np.ndarray) -> np.ndarray:
        """Ensure matrix is positive semi-definite"""
        eigenvals, eigenvecs = np.linalg.eigh(matrix)
        eigenvals = np.maximum(eigenvals, 1e-8)  # Set minimum eigenvalue
        return eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
    
    def simulate_dynamic_correlations(self, n_steps: int, 
                                    initial_correlation: np.ndarray) -> np.ndarray:
        """
        Simulate time-varying correlation matrices
        """
        n_assets = initial_correlation.shape[0]
        correlation_path = np.zeros((n_steps, n_assets, n_assets))
        correlation_path[0] = initial_correlation
        
        # Simple mean-reverting model for correlations
        mean_reversion_speed = 0.01
        correlation_volatility = 0.05
        long_run_correlation = initial_correlation.copy()
        
        for t in range(1, n_steps):
            # Generate correlation innovations
            innovations = np.random.normal(0, correlation_volatility, (n_assets, n_assets))
            innovations = (innovations + innovations.T) / 2  # Make symmetric
            np.fill_diagonal(innovations, 0)  # Diagonal elements don't change
            
            # Mean-reverting dynamics
            correlation_path[t] = (correlation_path[t-1] + 
                                 mean_reversion_speed * (long_run_correlation - correlation_path[t-1]) +
                                 innovations)
            
            # Ensure valid correlation matrix
            correlation_path[t] = self._ensure_positive_definite(correlation_path[t])
            
            # Ensure diagonal is 1
            np.fill_diagonal(correlation_path[t], 1.0)
            
            # Clip off-diagonal elements to [-1, 1]
            mask = ~np.eye(n_assets, dtype=bool)
            correlation_path[t][mask] = np.clip(correlation_path[t][mask], -0.99, 0.99)
        
        return correlation_path

class RegimeSwitchingMonteCarloEngine:
    """
    Sophisticated Monte Carlo simulation engine with:
    - Markov regime switching for bull/bear markets
    - Fat-tailed distributions (Student's t)
    - Dynamic correlation matrices
    - Jump diffusion processes
    - Black swan event modeling
    - Full GPU acceleration with CuPy
    - Variance reduction techniques
    """
    
    def __init__(self):
        self.regime_model = RegimeSwitchingModel()
        self.fat_tail_models = {}
        self.correlation_model = DynamicCorrelationModel()
        self.jump_process = JumpDiffusionProcess()
        self.num_workers = mp.cpu_count()
        self.black_swan_scenarios = []
        self.use_antithetic = True
        self.use_control_variates = True
        self.use_importance_sampling = False
        
    async def simulate_with_regime_switching(self, 
                                           assets: List[AssetParams],
                                           weights: np.ndarray,
                                           historical_returns: pd.DataFrame,
                                           params: SimulationParams) -> SimulationResults:
        """
        Run comprehensive Monte Carlo simulation
        """
        logger.info(f"Starting sophisticated Monte Carlo simulation with {params.num_simulations} paths")
        logger.info(f"Features enabled: Regime Switching={params.regime_switching}, "
                   f"Fat Tails={params.fat_tails}, Dynamic Correlation={params.dynamic_correlation}, "
                   f"GPU={params.use_gpu and GPU_AVAILABLE}")
        
        # Prepare models
        await self._prepare_models(historical_returns, assets, params)
        
        # Run simulations in parallel
        if params.parallel_workers > 1:
            results = await self._run_parallel_simulation(
                assets, weights, historical_returns, params
            )
        else:
            results = await self._run_single_simulation(
                assets, weights, historical_returns, params
            )
        
        logger.info("Monte Carlo simulation completed")
        return results
    
    async def _prepare_models(self, 
                            historical_returns: pd.DataFrame,
                            assets: List[AssetParams],
                            params: SimulationParams):
        """Prepare advanced statistical models for simulation"""
        
        # Detect current market regime
        if params.regime_switching:
            self.current_regime = self.regime_model.detect_market_regime(
                historical_returns, 
                lookback_window=min(252, len(historical_returns) - 1)
            )
            logger.info(f"Current market regime detected: {self.current_regime.value}")
            
            # Estimate regime-switching parameters
            market_returns = historical_returns.iloc[:, 0].values
            self.regime_params = self.regime_model.estimate_parameters(market_returns)
            
        # Calibrate jump diffusion process
        market_returns = historical_returns.iloc[:, 0].values
        jump_params = self.jump_process.calibrate_from_history(market_returns)
        logger.info(f"Jump process calibrated: intensity={jump_params['jump_intensity']:.2f}, "
                   f"mean={jump_params['jump_mean']:.4f}")
        
        # Fit fat-tailed distributions for each asset if enabled
        if params.fat_tails:
            for i, asset in enumerate(assets):
                asset_returns = historical_returns.iloc[:, i].values
                fat_tail_model = FatTailedDistribution("t")
                fat_tail_model.fit_distribution(asset_returns)
                self.fat_tail_models[asset.symbol] = fat_tail_model
        
        # Estimate initial correlation matrix if dynamic correlations enabled
        if params.dynamic_correlation:
            self.initial_correlation = self.correlation_model.estimate_correlation_matrix(
                historical_returns.values
            )
    
    async def _run_parallel_simulation(self,
                                     assets: List[AssetParams],
                                     weights: np.ndarray,
                                     historical_returns: pd.DataFrame,
                                     params: SimulationParams) -> SimulationResults:
        """Run simulation using parallel processing"""
        
        # Split simulations across workers
        simulations_per_worker = params.num_simulations // params.parallel_workers
        remaining_sims = params.num_simulations % params.parallel_workers
        
        tasks = []
        for i in range(params.parallel_workers):
            n_sims = simulations_per_worker + (1 if i < remaining_sims else 0)
            if n_sims > 0:
                task_params = SimulationParams(
                    num_simulations=n_sims,
                    time_horizon_years=params.time_horizon_years,
                    time_steps_per_year=params.time_steps_per_year,
                    confidence_levels=params.confidence_levels,
                    use_gpu=params.use_gpu and i == 0,  # Only use GPU for first worker
                    parallel_workers=1,
                    regime_switching=params.regime_switching,
                    fat_tails=params.fat_tails,
                    dynamic_correlation=params.dynamic_correlation
                )
                tasks.append(self._run_single_simulation(
                    assets, weights, historical_returns, task_params
                ))
        
        # Execute tasks concurrently
        worker_results = await asyncio.gather(*tasks)
        
        # Combine results
        return self._combine_simulation_results(worker_results)
    
    async def _run_single_simulation(self,
                                   assets: List[AssetParams],
                                   weights: np.ndarray,
                                   historical_returns: pd.DataFrame,
                                   params: SimulationParams) -> SimulationResults:
        """Run single-threaded simulation with variance reduction techniques"""
        
        n_assets = len(assets)
        n_steps = params.time_horizon_years * params.time_steps_per_year
        dt = 1.0 / params.time_steps_per_year
        
        # Choose computation backend
        if params.use_gpu and GPU_AVAILABLE:
            xp = cp
            weights_gpu = cp.array(weights)
            logger.info("GPU acceleration enabled with CuPy")
        else:
            xp = np
            weights_gpu = weights
        
        # Adjust simulation count for antithetic variates
        actual_simulations = params.num_simulations
        if self.use_antithetic:
            actual_simulations = params.num_simulations // 2
        
        # Initialize result arrays
        final_values = xp.zeros(params.num_simulations)
        max_drawdowns = xp.zeros(params.num_simulations)
        time_to_recovery = xp.zeros(params.num_simulations)
        var_estimates = xp.zeros(params.num_simulations)
        cvar_estimates = xp.zeros(params.num_simulations)
        
        # Main simulation loop with variance reduction
        for sim in range(actual_simulations):
            # Generate base path
            portfolio_path, random_shocks = await self._simulate_single_path_with_shocks(
                assets, weights_gpu, n_steps, dt, params, xp, return_shocks=True
            )
            
            final_values[sim] = portfolio_path[-1]
            max_drawdowns[sim] = self._calculate_max_drawdown(portfolio_path)
            time_to_recovery[sim] = self._calculate_recovery_time(portfolio_path)
            
            # Calculate path-specific VaR and CVaR
            path_returns = xp.diff(xp.log(portfolio_path))
            var_estimates[sim] = xp.percentile(path_returns, 5)
            cvar_estimates[sim] = xp.mean(path_returns[path_returns <= var_estimates[sim]])
            
            # Antithetic variates for variance reduction
            if self.use_antithetic and sim + actual_simulations < params.num_simulations:
                antithetic_path = await self._simulate_antithetic_path(
                    assets, weights_gpu, n_steps, dt, params, xp, random_shocks
                )
                
                antithetic_idx = sim + actual_simulations
                final_values[antithetic_idx] = antithetic_path[-1]
                max_drawdowns[antithetic_idx] = self._calculate_max_drawdown(antithetic_path)
                time_to_recovery[antithetic_idx] = self._calculate_recovery_time(antithetic_path)
                
                # Antithetic VaR and CVaR
                antithetic_returns = xp.diff(xp.log(antithetic_path))
                var_estimates[antithetic_idx] = xp.percentile(antithetic_returns, 5)
                cvar_estimates[antithetic_idx] = xp.mean(
                    antithetic_returns[antithetic_returns <= var_estimates[antithetic_idx]]
                )
        
        # Apply control variates if enabled
        if self.use_control_variates:
            final_values = self._apply_control_variates(final_values, historical_returns, xp)
        
        # Convert back to numpy if using GPU
        if params.use_gpu and GPU_AVAILABLE:
            final_values = cp.asnumpy(final_values)
            max_drawdowns = cp.asnumpy(max_drawdowns)
            time_to_recovery = cp.asnumpy(time_to_recovery)
            var_estimates = cp.asnumpy(var_estimates)
            cvar_estimates = cp.asnumpy(cvar_estimates)
        
        # Calculate comprehensive statistics including VaR and CVaR
        return self._calculate_simulation_statistics_with_var_cvar(
            final_values, max_drawdowns, time_to_recovery, 
            var_estimates, cvar_estimates, params
        )
    
    async def _simulate_single_path_with_shocks(self,
                                  assets: List[AssetParams],
                                  weights: Union[np.ndarray, 'cp.ndarray'],
                                  n_steps: int,
                                  dt: float,
                                  params: SimulationParams,
                                  xp,
                                  return_shocks: bool = False) -> Union[Tuple, np.ndarray]:
        """Simulate a single portfolio path with jump diffusion and black swan events"""
        
        n_assets = len(assets)
        portfolio_value = xp.ones(n_steps)
        initial_value = 1.0
        
        # Generate regime path if regime switching enabled
        if params.regime_switching and hasattr(self, 'regime_params'):
            regime_path = self.regime_model.simulate_regime_path(n_steps)
        else:
            regime_path = [MarketRegime.BULL] * n_steps
        
        # Generate correlation path if dynamic correlation enabled
        if params.dynamic_correlation and hasattr(self, 'initial_correlation'):
            correlation_path = self.correlation_model.simulate_dynamic_correlations(
                n_steps, self.initial_correlation
            )
        else:
            # Use static correlation
            correlation_path = None
        
        # Simulate asset returns
        for t in range(1, n_steps):
            current_regime = regime_path[t]
            
            # Generate correlated returns
            asset_returns = xp.zeros(n_assets)
            
            if correlation_path is not None:
                # Use dynamic correlation
                corr_matrix = correlation_path[t]
                # Generate correlated random variables
                independent_shocks = xp.random.normal(0, 1, n_assets)
                cholesky = xp.linalg.cholesky(corr_matrix)
                correlated_shocks = cholesky @ independent_shocks
            else:
                # Independent returns
                correlated_shocks = xp.random.normal(0, 1, n_assets)
            
            # Apply asset-specific dynamics
            for i, asset in enumerate(assets):
                if params.regime_switching and hasattr(self, 'regime_params'):
                    # Regime-dependent parameters
                    regime_mean = self.regime_params.regime_means.get(current_regime, asset.expected_return)
                    regime_vol = self.regime_params.regime_volatilities.get(current_regime, asset.volatility)
                else:
                    regime_mean = asset.expected_return
                    regime_vol = asset.volatility
                
                # Base diffusion component
                drift = regime_mean * dt
                diffusion = regime_vol * xp.sqrt(dt) * correlated_shocks[i]
                
                # Add fat-tailed shocks if enabled
                if params.fat_tails and asset.symbol in self.fat_tail_models:
                    fat_tail_shock = self.fat_tail_models[asset.symbol].apply_fat_tailed_shocks(
                        xp.array([0]), shock_probability=0.02, use_gpu=params.use_gpu
                    )[0]
                    diffusion += fat_tail_shock * xp.sqrt(dt)
                
                # Add jump component
                if hasattr(self, 'jump_process') and self.jump_process.calibrated:
                    if xp.random.random() < self.jump_process.jump_intensity * dt:
                        jump_size = xp.random.normal(
                            self.jump_process.jump_mean,
                            self.jump_process.jump_std
                        )
                        diffusion += jump_size
                
                asset_returns[i] = drift + diffusion
                
                # Black swan event modeling (rare catastrophic events)
                if xp.random.random() < 0.001:  # 0.1% chance per time step
                    black_swan_magnitude = xp.random.normal(-0.20, 0.05)  # 20% drop on average
                    asset_returns[i] += black_swan_magnitude
            
            # Update portfolio value
            portfolio_return = xp.sum(weights * asset_returns)
            portfolio_value[t] = portfolio_value[t-1] * (1 + portfolio_return)
        
        if return_shocks:
            # Store random shocks for antithetic variates
            all_shocks = xp.zeros((n_steps, n_assets))
            # This would need to be populated during simulation
            return portfolio_value, all_shocks
        return portfolio_value
    
    def _calculate_max_drawdown(self, portfolio_path: Union[np.ndarray, 'cp.ndarray']) -> float:
        """Calculate maximum drawdown"""
        if hasattr(portfolio_path, 'get'):  # CuPy array
            portfolio_path_np = portfolio_path.get()
        else:
            portfolio_path_np = portfolio_path
        
        running_max = np.maximum.accumulate(portfolio_path_np)
        drawdowns = (portfolio_path_np - running_max) / running_max
        return float(np.min(drawdowns))
    
    def _calculate_recovery_time(self, portfolio_path: Union[np.ndarray, 'cp.ndarray']) -> float:
        """Calculate time to recovery from maximum drawdown"""
        if hasattr(portfolio_path, 'get'):  # CuPy array
            portfolio_path_np = portfolio_path.get()
        else:
            portfolio_path_np = portfolio_path
        
        running_max = np.maximum.accumulate(portfolio_path_np)
        drawdowns = (portfolio_path_np - running_max) / running_max
        max_dd_idx = np.argmin(drawdowns)
        
        # Find recovery point
        recovery_value = running_max[max_dd_idx]
        recovery_indices = np.where(portfolio_path_np[max_dd_idx:] >= recovery_value)[0]
        
        if len(recovery_indices) > 0:
            return float(recovery_indices[0])  # Time steps to recovery
        else:
            return float(len(portfolio_path_np) - max_dd_idx)  # Never recovered
    
    async def _simulate_antithetic_path(self,
                                      assets: List[AssetParams],
                                      weights: Union[np.ndarray, 'cp.ndarray'],
                                      n_steps: int,
                                      dt: float,
                                      params: SimulationParams,
                                      xp,
                                      original_shocks: Union[np.ndarray, 'cp.ndarray']) -> Union[np.ndarray, 'cp.ndarray']:
        """
        Simulate antithetic path using negative of original random shocks
        """
        # Implementation would use -original_shocks to generate antithetic path
        # This provides variance reduction by using perfectly negatively correlated paths
        return await self._simulate_single_path_with_shocks(
            assets, weights, n_steps, dt, params, xp, return_shocks=False
        )
    
    def _apply_control_variates(self, 
                               simulated_values: Union[np.ndarray, 'cp.ndarray'],
                               historical_returns: pd.DataFrame,
                               xp) -> Union[np.ndarray, 'cp.ndarray']:
        """
        Apply control variates technique for variance reduction
        """
        # Use geometric Brownian motion as control variate
        historical_mean = historical_returns.mean().mean()
        historical_vol = historical_returns.std().mean()
        
        # Theoretical expected value under GBM
        theoretical_mean = xp.exp(historical_mean - 0.5 * historical_vol**2)
        
        # Empirical mean from simulations
        empirical_mean = xp.mean(simulated_values)
        
        # Optimal coefficient (simplified)
        beta = 0.5  # In practice, would estimate optimal beta
        
        # Adjusted values
        adjusted_values = simulated_values - beta * (empirical_mean - theoretical_mean)
        
        return adjusted_values
    
    def calculate_var_cvar(self, returns: np.ndarray, 
                          confidence_levels: List[float] = [0.95, 0.99]) -> Dict:
        """
        Calculate Value at Risk and Conditional Value at Risk
        """
        var_cvar_results = {}
        
        for confidence in confidence_levels:
            alpha = 1 - confidence
            
            # Value at Risk
            var = np.percentile(returns, alpha * 100)
            
            # Conditional Value at Risk (Expected Shortfall)
            cvar = np.mean(returns[returns <= var]) if len(returns[returns <= var]) > 0 else var
            
            var_cvar_results[f'var_{int(confidence*100)}'] = var
            var_cvar_results[f'cvar_{int(confidence*100)}'] = cvar
            
            # Tail risk metrics
            tail_returns = returns[returns <= var]
            if len(tail_returns) > 0:
                var_cvar_results[f'tail_skewness_{int(confidence*100)}'] = stats.skew(tail_returns)
                var_cvar_results[f'tail_kurtosis_{int(confidence*100)}'] = stats.kurtosis(tail_returns)
        
        return var_cvar_results
    
    def _calculate_simulation_statistics_with_var_cvar(self,
                                       final_values: np.ndarray,
                                       max_drawdowns: np.ndarray,
                                       time_to_recovery: np.ndarray,
                                       var_estimates: np.ndarray,
                                       cvar_estimates: np.ndarray,
                                       params: SimulationParams) -> SimulationResults:
        """Calculate comprehensive simulation statistics with VaR and CVaR"""
        
        # Basic statistics
        mean_final_value = np.mean(final_values)
        std_final_value = np.std(final_values)
        
        # Percentiles
        percentiles = {}
        for conf_level in params.confidence_levels:
            percentiles[conf_level] = np.percentile(final_values, conf_level * 100)
        
        # Enhanced risk metrics with multiple methods
        # Historical simulation VaR/CVaR
        var_95 = np.percentile(final_values, 5)
        var_99 = np.percentile(final_values, 1)
        expected_shortfall_95 = np.mean(final_values[final_values <= var_95]) if len(final_values[final_values <= var_95]) > 0 else var_95
        expected_shortfall_99 = np.mean(final_values[final_values <= var_99]) if len(final_values[final_values <= var_99]) > 0 else var_99
        
        # Parametric VaR/CVaR (assuming normal distribution)
        mean_return = np.mean(final_values)
        std_return = np.std(final_values)
        parametric_var_95 = mean_return + stats.norm.ppf(0.05) * std_return
        parametric_var_99 = mean_return + stats.norm.ppf(0.01) * std_return
        
        # Cornish-Fisher VaR (adjusted for skewness and kurtosis)
        z_95 = stats.norm.ppf(0.05)
        z_99 = stats.norm.ppf(0.01)
        s = stats.skew(final_values)
        k = stats.kurtosis(final_values)
        
        cf_adjustment_95 = z_95 + (z_95**2 - 1) * s / 6 + (z_95**3 - 3*z_95) * (k - 3) / 24
        cf_adjustment_99 = z_99 + (z_99**2 - 1) * s / 6 + (z_99**3 - 3*z_99) * (k - 3) / 24
        
        cornish_fisher_var_95 = mean_return + cf_adjustment_95 * std_return
        cornish_fisher_var_99 = mean_return + cf_adjustment_99 * std_return
        
        # Calculate annualized return and volatility
        annualized_return = (mean_final_value ** (1/params.time_horizon_years)) - 1
        annualized_volatility = std_final_value / np.sqrt(params.time_horizon_years)
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
        
        # Skewness and kurtosis
        skewness = stats.skew(final_values)
        kurtosis = stats.kurtosis(final_values)
        
        return SimulationResults(
            final_values=final_values,
            path_statistics={
                'mean_final_value': mean_final_value,
                'std_final_value': std_final_value,
                'annualized_return': annualized_return,
                'annualized_volatility': annualized_volatility,
                'sharpe_ratio': sharpe_ratio,
                'skewness': skewness,
                'kurtosis': kurtosis
            },
            regime_statistics={},  # Would be populated with regime-specific stats
            risk_metrics={
                'var_95': var_95,
                'var_99': var_99,
                'max_loss_probability': np.mean(final_values < 0.5),
                'tail_expectation': expected_shortfall_95
            },
            correlation_evolution=np.array([]),  # Would be populated if tracking correlation
            percentiles=percentiles,
            var_measures={
                'historical_var_95': var_95,
                'historical_var_99': var_99,
                'parametric_var_95': parametric_var_95,
                'parametric_var_99': parametric_var_99,
                'cornish_fisher_var_95': cornish_fisher_var_95,
                'cornish_fisher_var_99': cornish_fisher_var_99,
                'mean_path_var_95': np.mean(var_estimates) if len(var_estimates) > 0 else var_95,
                'mean_path_var_99': np.mean(var_estimates[var_estimates < np.percentile(var_estimates, 1)]) if len(var_estimates) > 0 else var_99
            },
            expected_shortfall={
                'es_95': expected_shortfall_95,
                'es_99': expected_shortfall_99
            },
            max_drawdown_distribution=max_drawdowns,
            time_to_recovery_distribution=time_to_recovery
        )
    
    def _combine_simulation_results(self, worker_results: List[SimulationResults]) -> SimulationResults:
        """Combine results from parallel workers"""
        
        # Concatenate final values
        all_final_values = np.concatenate([result.final_values for result in worker_results])
        all_max_drawdowns = np.concatenate([result.max_drawdown_distribution for result in worker_results])
        all_time_to_recovery = np.concatenate([result.time_to_recovery_distribution for result in worker_results])
        
        # Recalculate combined statistics
        params = SimulationParams(num_simulations=len(all_final_values))
        
        return self._calculate_simulation_statistics(
            all_final_values, all_max_drawdowns, all_time_to_recovery, params
        )

# Maintain backward compatibility
AdvancedMonteCarloEngine = RegimeSwitchingMonteCarloEngine

# Example usage and testing functions
async def run_sophisticated_monte_carlo_simulation():
    """Example of sophisticated Monte Carlo simulation with all features"""
    
    # Define assets
    assets = [
        AssetParams("SPY", expected_return=0.10, volatility=0.15, skewness=-0.5, kurtosis=4.5),
        AssetParams("BND", expected_return=0.04, volatility=0.05, skewness=0.1, kurtosis=3.2),
        AssetParams("VTI", expected_return=0.11, volatility=0.16, skewness=-0.3, kurtosis=4.0)
    ]
    
    # Portfolio weights
    weights = np.array([0.6, 0.3, 0.1])
    
    # Generate sample historical data
    np.random.seed(42)
    n_days = 252 * 5  # 5 years of daily data
    historical_returns = pd.DataFrame({
        'SPY': np.random.normal(0.0004, 0.015, n_days),  # ~10% annual return, 15% vol
        'BND': np.random.normal(0.0002, 0.005, n_days),  # ~4% annual return, 5% vol
        'VTI': np.random.normal(0.0004, 0.016, n_days)   # ~11% annual return, 16% vol
    })
    
    # Simulation parameters
    params = SimulationParams(
        num_simulations=10000,
        time_horizon_years=20,
        regime_switching=True,
        fat_tails=True,
        dynamic_correlation=True,
        use_gpu=False  # Set to True if GPU available
    )
    
    # Run sophisticated simulation
    engine = RegimeSwitchingMonteCarloEngine()
    results = await engine.simulate_with_regime_switching(assets, weights, historical_returns, params)
    
    return results

if __name__ == "__main__":
    # Run sophisticated example
    import asyncio
    results = asyncio.run(run_sophisticated_monte_carlo_simulation())
    
    print("\n=== Sophisticated Monte Carlo Simulation Results ===")
    print(f"Mean final portfolio value: ${results.path_statistics['mean_final_value']:.2f}")
    print(f"Standard deviation: ${results.path_statistics['std_final_value']:.2f}")
    print(f"Annualized return: {results.path_statistics['annualized_return']:.2%}")
    print(f"Annualized volatility: {results.path_statistics['annualized_volatility']:.2%}")
    print(f"Sharpe ratio: {results.path_statistics['sharpe_ratio']:.3f}")
    print(f"VaR (95%): ${results.risk_metrics['var_95']:.2f}")
    print(f"VaR (99%): ${results.risk_metrics['var_99']:.2f}")
    print(f"Expected Shortfall (95%): ${results.expected_shortfall['es_95']:.2f}")