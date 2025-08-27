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
    Markov regime-switching model for market states
    """
    
    def __init__(self):
        self.regimes = [MarketRegime.BULL, MarketRegime.BEAR, MarketRegime.VOLATILE]
        self.transition_matrix = None
        self.regime_params = {}
        self.current_regime = MarketRegime.BULL
        self.regime_history = []
        
    def estimate_parameters(self, returns: np.ndarray, window_size: int = 252) -> RegimeSwitchingParams:
        """
        Estimate regime-switching parameters using Expectation-Maximization
        """
        logger.info("Estimating regime-switching model parameters")
        
        # Use Gaussian Mixture Model as proxy for regime identification
        gmm = GaussianMixture(n_components=len(self.regimes), random_state=42)
        gmm.fit(returns.reshape(-1, 1))
        
        # Extract regime parameters
        regime_means = {}
        regime_volatilities = {}
        
        for i, regime in enumerate(self.regimes):
            regime_means[regime] = float(gmm.means_[i, 0])
            regime_volatilities[regime] = float(np.sqrt(gmm.covariances_[i, 0, 0]))
        
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
        
        return RegimeSwitchingParams(
            regimes=self.regimes,
            transition_matrix=transition_matrix,
            regime_means=regime_means,
            regime_volatilities=regime_volatilities,
            regime_duration_params=regime_duration_params
        )
    
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

class FatTailedDistribution:
    """
    Fat-tailed distribution modeling using t-distribution and skewed distributions
    """
    
    def __init__(self, distribution_type: str = "t"):
        self.distribution_type = distribution_type
        self.params = {}
    
    def fit_distribution(self, returns: np.ndarray) -> Dict[str, float]:
        """
        Fit fat-tailed distribution to return data
        """
        if self.distribution_type == "t":
            # Fit t-distribution
            df, loc, scale = stats.t.fit(returns)
            self.params = {
                'degrees_of_freedom': df,
                'location': loc,
                'scale': scale
            }
        elif self.distribution_type == "skewed_t":
            # Fit skewed t-distribution (approximation using skewnorm)
            a, loc, scale = stats.skewnorm.fit(returns)
            self.params = {
                'skewness': a,
                'location': loc,
                'scale': scale
            }
        else:
            raise ValueError(f"Unsupported distribution type: {self.distribution_type}")
        
        return self.params
    
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

class AdvancedMonteCarloEngine:
    """
    Advanced Monte Carlo simulation engine with regime-switching,
    fat-tailed distributions, and dynamic correlations
    """
    
    def __init__(self):
        self.regime_model = RegimeSwitchingModel()
        self.fat_tail_models = {}
        self.correlation_model = DynamicCorrelationModel()
        self.num_workers = mp.cpu_count()
        
    async def simulate_portfolio(self, 
                               assets: List[AssetParams],
                               weights: np.ndarray,
                               historical_returns: pd.DataFrame,
                               params: SimulationParams) -> SimulationResults:
        """
        Run comprehensive Monte Carlo simulation
        """
        logger.info(f"Starting Monte Carlo simulation with {params.num_simulations} paths")
        
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
        """Prepare statistical models for simulation"""
        
        # Estimate regime-switching parameters if enabled
        if params.regime_switching:
            # Use market index or first asset for regime detection
            market_returns = historical_returns.iloc[:, 0].values
            self.regime_params = self.regime_model.estimate_parameters(market_returns)
        
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
        """Run single-threaded simulation"""
        
        n_assets = len(assets)
        n_steps = params.time_horizon_years * params.time_steps_per_year
        dt = 1.0 / params.time_steps_per_year
        
        # Choose computation backend
        if params.use_gpu and GPU_AVAILABLE:
            xp = cp
            weights_gpu = cp.array(weights)
        else:
            xp = np
            weights_gpu = weights
        
        # Initialize result arrays
        final_values = xp.zeros(params.num_simulations)
        max_drawdowns = xp.zeros(params.num_simulations)
        time_to_recovery = xp.zeros(params.num_simulations)
        
        # Simulation loop
        for sim in range(params.num_simulations):
            portfolio_path = await self._simulate_single_path(
                assets, weights_gpu, n_steps, dt, params, xp
            )
            
            final_values[sim] = portfolio_path[-1]
            max_drawdowns[sim] = self._calculate_max_drawdown(portfolio_path)
            time_to_recovery[sim] = self._calculate_recovery_time(portfolio_path)
        
        # Convert back to numpy if using GPU
        if params.use_gpu and GPU_AVAILABLE:
            final_values = cp.asnumpy(final_values)
            max_drawdowns = cp.asnumpy(max_drawdowns)
            time_to_recovery = cp.asnumpy(time_to_recovery)
        
        # Calculate statistics
        return self._calculate_simulation_statistics(
            final_values, max_drawdowns, time_to_recovery, params
        )
    
    async def _simulate_single_path(self,
                                  assets: List[AssetParams],
                                  weights: Union[np.ndarray, 'cp.ndarray'],
                                  n_steps: int,
                                  dt: float,
                                  params: SimulationParams,
                                  xp) -> Union[np.ndarray, 'cp.ndarray']:
        """Simulate a single portfolio path"""
        
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
                
                if params.fat_tails and asset.symbol in self.fat_tail_models:
                    # Use fat-tailed distribution
                    shock = self.fat_tail_models[asset.symbol].sample(1, params.use_gpu)[0]
                    # Standardize and apply regime parameters
                    standardized_shock = (shock - self.fat_tail_models[asset.symbol].params['location']) / self.fat_tail_models[asset.symbol].params['scale']
                    asset_returns[i] = regime_mean * dt + regime_vol * xp.sqrt(dt) * standardized_shock
                else:
                    # Normal distribution with correlation
                    asset_returns[i] = regime_mean * dt + regime_vol * xp.sqrt(dt) * correlated_shocks[i]
            
            # Update portfolio value
            portfolio_return = xp.sum(weights * asset_returns)
            portfolio_value[t] = portfolio_value[t-1] * (1 + portfolio_return)
        
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
    
    def _calculate_simulation_statistics(self,
                                       final_values: np.ndarray,
                                       max_drawdowns: np.ndarray,
                                       time_to_recovery: np.ndarray,
                                       params: SimulationParams) -> SimulationResults:
        """Calculate comprehensive simulation statistics"""
        
        # Basic statistics
        mean_final_value = np.mean(final_values)
        std_final_value = np.std(final_values)
        
        # Percentiles
        percentiles = {}
        for conf_level in params.confidence_levels:
            percentiles[conf_level] = np.percentile(final_values, conf_level * 100)
        
        # Risk metrics
        var_95 = np.percentile(final_values, 5)
        var_99 = np.percentile(final_values, 1)
        expected_shortfall_95 = np.mean(final_values[final_values <= var_95])
        expected_shortfall_99 = np.mean(final_values[final_values <= var_99])
        
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
                'parametric_var_95': var_95,
                'parametric_var_99': var_99
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

# Example usage and testing functions
async def run_example_simulation():
    """Example of how to use the Monte Carlo engine"""
    
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
    
    # Run simulation
    engine = AdvancedMonteCarloEngine()
    results = await engine.simulate_portfolio(assets, weights, historical_returns, params)
    
    return results

if __name__ == "__main__":
    # Run example
    import asyncio
    results = asyncio.run(run_example_simulation())
    
    print("\n=== Monte Carlo Simulation Results ===")
    print(f"Mean final portfolio value: ${results.path_statistics['mean_final_value']:.2f}")
    print(f"Standard deviation: ${results.path_statistics['std_final_value']:.2f}")
    print(f"Annualized return: {results.path_statistics['annualized_return']:.2%}")
    print(f"Annualized volatility: {results.path_statistics['annualized_volatility']:.2%}")
    print(f"Sharpe ratio: {results.path_statistics['sharpe_ratio']:.3f}")
    print(f"VaR (95%): ${results.risk_metrics['var_95']:.2f}")
    print(f"VaR (99%): ${results.risk_metrics['var_99']:.2f}")
    print(f"Expected Shortfall (95%): ${results.expected_shortfall['es_95']:.2f}")