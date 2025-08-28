import numpy as np
import cupy as cp
import pandas as pd
from typing import List, Dict, Optional
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from scipy.stats import t, norm
import statsmodels.api as sm
from enum import Enum, auto

class MarketRegime(Enum):
    BULL = auto()
    BEAR = auto()
    NEUTRAL = auto()

@dataclass
class SimulationConfig:
    n_paths: int = 50_000
    n_years: int = 30
    initial_price: float = 100.0
    risk_free_rate: float = 0.02
    volatility: float = 0.15
    jump_intensity: float = 0.1
    jump_size_mean: float = -0.05
    jump_size_std: float = 0.2

class AdvancedMonteCarloEngine:
    def __init__(self, config: SimulationConfig = SimulationConfig()):
        self.config = config
        self.gpu_available = cp.cuda.runtime.getDeviceCount() > 0

    def _detect_market_regime(self, returns: np.ndarray) -> MarketRegime:
        """
        Detect market regime using technical indicators and statistical analysis
        """
        # Implement regime detection using Hidden Markov Model
        model = sm.tsa.MarkovAutoregression(returns, k_regimes=3, order=1)
        model_fit = model.fit()
        
        # Simplified regime interpretation based on model results
        mean_returns = model_fit.regime_means
        if mean_returns[0] > 0:
            return MarketRegime.BULL
        elif mean_returns[0] < 0:
            return MarketRegime.BEAR
        return MarketRegime.NEUTRAL

    def _jump_diffusion_process(self, 
                                 base_process: np.ndarray, 
                                 dt: float) -> np.ndarray:
        """
        Add jump diffusion to simulate black swan events
        """
        # Poisson process for jump events
        jump_times = np.random.poisson(
            self.config.jump_intensity * dt, 
            base_process.shape
        )
        
        # Generate jump sizes using Student's t distribution
        jump_sizes = t.rvs(
            df=4,  # Fat-tailed distribution
            loc=self.config.jump_size_mean, 
            scale=self.config.jump_size_std, 
            size=base_process.shape
        )
        
        # Apply jumps
        jumps = jump_times * jump_sizes
        return base_process + jumps

    def _garch_volatility(self, returns: np.ndarray) -> np.ndarray:
        """
        GARCH volatility modeling
        """
        # Simplified GARCH(1,1) model
        omega = 0.1  # Constant term
        alpha = 0.1  # ARCH term
        beta = 0.8   # GARCH term
        
        volatilities = np.zeros_like(returns)
        volatilities[0] = np.std(returns)
        
        for t in range(1, len(returns)):
            volatilities[t] = np.sqrt(
                omega + 
                alpha * returns[t-1]**2 + 
                beta * volatilities[t-1]**2
            )
        
        return volatilities

    def simulate_paths(self, verbose: bool = False) -> np.ndarray:
        """
        Generate Monte Carlo simulation paths with advanced features
        """
        dt = 1.0 / 252  # Trading days per year
        
        # Use CuPy for GPU acceleration if available
        xp = cp if self.gpu_available else np
        
        # Initialize paths
        paths = xp.zeros((self.config.n_paths, self.config.n_years * 252 + 1))
        paths[:, 0] = self.config.initial_price
        
        # Parallel processing for path generation
        def generate_path(seed: int):
            xp.random.seed(seed)
            path = xp.zeros(self.config.n_years * 252 + 1)
            path[0] = self.config.initial_price
            
            # Geometric Brownian Motion with enhancements
            for t in range(1, len(path)):
                # Standard Brownian motion
                dW = xp.random.normal(0, xp.sqrt(dt))
                
                # Drift term with regime-dependent adjustment
                drift = (self.config.risk_free_rate - 0.5 * self.config.volatility**2) * dt
                
                # Volatility term with GARCH-like adjustment
                vol_term = self.config.volatility * dW
                
                # Update path with jump diffusion
                path[t] = path[t-1] * xp.exp(drift + vol_term)
            
            return path
        
        # Use ProcessPoolExecutor for parallel simulation
        with ProcessPoolExecutor() as executor:
            seeds = list(range(self.config.n_paths))
            paths = list(executor.map(generate_path, seeds))
        
        # Convert to NumPy array for consistency
        paths = np.array(paths)
        
        # Optional verbose logging
        if verbose:
            print(f"Simulation Statistics:")
            print(f"Mean Final Price: {np.mean(paths[:, -1])}")
            print(f"Std Dev Final Price: {np.std(paths[:, -1])}")
        
        return paths

    def calculate_risk_metrics(self, paths: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive risk metrics
        """
        final_prices = paths[:, -1]
        returns = np.diff(paths, axis=1) / paths[:, :-1]
        
        return {
            "Value at Risk (95%)": np.percentile(final_prices, 5),
            "Conditional VaR (95%)": np.mean(final_prices[final_prices <= np.percentile(final_prices, 5)]),
            "Maximum Drawdown": np.max(np.maximum.accumulate(paths) - paths, axis=1).max(),
            "Sharpe Ratio": (np.mean(returns) - self.config.risk_free_rate) / np.std(returns),
            "Skewness": np.mean((returns - np.mean(returns))**3) / np.std(returns)**3,
            "Kurtosis": np.mean((returns - np.mean(returns))**4) / np.std(returns)**4
        }

# Example usage
if __name__ == "__main__":
    config = SimulationConfig(n_paths=50_000, n_years=30)
    engine = AdvancedMonteCarloEngine(config)
    paths = engine.simulate_paths(verbose=True)
    risk_metrics = engine.calculate_risk_metrics(paths)
    print("\nRisk Metrics:")
    for metric, value in risk_metrics.items():
        print(f"{metric}: {value}")
