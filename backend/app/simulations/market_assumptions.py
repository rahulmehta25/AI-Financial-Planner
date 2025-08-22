"""
Capital Market Assumptions (CMA) for Monte Carlo Simulations

Forward-looking expected returns, volatilities, and correlations for major asset classes
based on current market conditions and long-term economic projections.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class AssetClassAssumptions:
    """Assumptions for a single asset class"""
    name: str
    expected_return: float  # Annualized expected return
    volatility: float       # Annualized volatility
    sharpe_ratio: float     # Expected Sharpe ratio
    description: str


class CapitalMarketAssumptions:
    """
    Forward-looking Capital Market Assumptions for portfolio simulation.
    
    Based on current market conditions, economic outlook, and historical patterns.
    Updated quarterly to reflect changing market dynamics.
    """
    
    def __init__(self, base_date: Optional[datetime] = None):
        self.base_date = base_date or datetime.now()
        self.last_updated = self.base_date
        
        # Initialize asset class assumptions (as of Q3 2024)
        self._initialize_asset_assumptions()
        self._initialize_correlation_matrix()
        self._initialize_inflation_assumptions()
        
        logger.info(f"CMA initialized with {len(self.asset_classes)} asset classes")
    
    def _initialize_asset_assumptions(self):
        """Initialize forward-looking assumptions for major asset classes"""
        
        self.asset_classes = {
            # Equity Asset Classes
            "US_LARGE_CAP": AssetClassAssumptions(
                name="US Large Cap Equities",
                expected_return=0.085,  # 8.5% - reduced from historical due to high valuations
                volatility=0.16,        # 16% - elevated due to market uncertainty
                sharpe_ratio=0.35,
                description="S&P 500 and similar broad US large-cap indices"
            ),
            
            "US_SMALL_CAP": AssetClassAssumptions(
                name="US Small Cap Equities", 
                expected_return=0.095,  # 9.5% - small cap premium
                volatility=0.22,        # 22% - higher volatility
                sharpe_ratio=0.32,
                description="Russell 2000 and small-cap growth indices"
            ),
            
            "INTERNATIONAL_DEVELOPED": AssetClassAssumptions(
                name="International Developed Equities",
                expected_return=0.078,  # 7.8% - lower due to slower growth
                volatility=0.18,        # 18% - currency and political risks
                sharpe_ratio=0.28,
                description="MSCI EAFE and developed international markets"
            ),
            
            "EMERGING_MARKETS": AssetClassAssumptions(
                name="Emerging Market Equities",
                expected_return=0.095,  # 9.5% - higher growth potential
                volatility=0.25,        # 25% - high volatility
                sharpe_ratio=0.26,
                description="MSCI Emerging Markets and frontier markets"
            ),
            
            # Fixed Income Asset Classes
            "US_TREASURY_LONG": AssetClassAssumptions(
                name="US Long-Term Treasury Bonds",
                expected_return=0.042,  # 4.2% - higher yields environment
                volatility=0.08,        # 8% - duration risk
                sharpe_ratio=0.15,
                description="20+ year US Treasury bonds"
            ),
            
            "US_TREASURY_INTERMEDIATE": AssetClassAssumptions(
                name="US Intermediate Treasury Bonds", 
                expected_return=0.038,  # 3.8%
                volatility=0.045,       # 4.5% - lower duration risk
                sharpe_ratio=0.22,
                description="7-10 year US Treasury bonds"
            ),
            
            "CORPORATE_BONDS": AssetClassAssumptions(
                name="US Investment Grade Corporate Bonds",
                expected_return=0.045,  # 4.5% - credit spread premium
                volatility=0.055,       # 5.5% - credit and duration risk
                sharpe_ratio=0.27,
                description="Investment grade corporate bond indices"
            ),
            
            "HIGH_YIELD_BONDS": AssetClassAssumptions(
                name="US High Yield Corporate Bonds",
                expected_return=0.065,  # 6.5% - higher yield for credit risk
                volatility=0.095,       # 9.5% - significant credit risk
                sharpe_ratio=0.32,
                description="Below investment grade corporate bonds"
            ),
            
            # Alternative Asset Classes
            "REITS": AssetClassAssumptions(
                name="Real Estate Investment Trusts",
                expected_return=0.075,  # 7.5% - real estate exposure
                volatility=0.19,        # 19% - real estate volatility
                sharpe_ratio=0.26,
                description="Publicly traded REITs and real estate indices"
            ),
            
            "COMMODITIES": AssetClassAssumptions(
                name="Broad Commodities",
                expected_return=0.035,  # 3.5% - inflation hedge
                volatility=0.21,        # 21% - high commodity volatility
                sharpe_ratio=0.05,
                description="Broad commodity indices including energy, metals, agriculture"
            ),
            
            # Cash and Cash Equivalents
            "CASH": AssetClassAssumptions(
                name="Cash and Money Market",
                expected_return=0.045,  # 4.5% - higher short rates
                volatility=0.005,       # 0.5% - minimal volatility
                sharpe_ratio=0.00,
                description="3-month Treasury bills and money market funds"
            )
        }
    
    def _initialize_correlation_matrix(self):
        """Initialize correlation matrix between asset classes"""
        
        assets = list(self.asset_classes.keys())
        n_assets = len(assets)
        
        # Initialize with empirical correlations (updated for current environment)
        correlations = np.eye(n_assets)  # Start with identity matrix
        
        # Asset class correlation mapping
        corr_data = {
            # Equity correlations (higher in risk-off periods)
            ("US_LARGE_CAP", "US_SMALL_CAP"): 0.85,
            ("US_LARGE_CAP", "INTERNATIONAL_DEVELOPED"): 0.75,
            ("US_LARGE_CAP", "EMERGING_MARKETS"): 0.65,
            ("US_SMALL_CAP", "INTERNATIONAL_DEVELOPED"): 0.70,
            ("US_SMALL_CAP", "EMERGING_MARKETS"): 0.68,
            ("INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"): 0.80,
            
            # Equity-Bond correlations (more negative in recent environment)
            ("US_LARGE_CAP", "US_TREASURY_LONG"): -0.15,
            ("US_LARGE_CAP", "US_TREASURY_INTERMEDIATE"): -0.10,
            ("US_LARGE_CAP", "CORPORATE_BONDS"): 0.25,
            ("US_LARGE_CAP", "HIGH_YIELD_BONDS"): 0.65,
            
            # Bond correlations
            ("US_TREASURY_LONG", "US_TREASURY_INTERMEDIATE"): 0.85,
            ("US_TREASURY_LONG", "CORPORATE_BONDS"): 0.60,
            ("US_TREASURY_INTERMEDIATE", "CORPORATE_BONDS"): 0.75,
            ("CORPORATE_BONDS", "HIGH_YIELD_BONDS"): 0.70,
            
            # Alternative asset correlations
            ("US_LARGE_CAP", "REITS"): 0.60,
            ("US_LARGE_CAP", "COMMODITIES"): 0.25,
            ("REITS", "COMMODITIES"): 0.15,
            
            # Cash correlations (near zero with most assets)
            ("CASH", "US_TREASURY_INTERMEDIATE"): 0.30,
        }
        
        # Fill correlation matrix
        for i, asset_i in enumerate(assets):
            for j, asset_j in enumerate(assets):
                if i != j:
                    # Check both directions for correlation
                    key1 = (asset_i, asset_j)
                    key2 = (asset_j, asset_i)
                    
                    if key1 in corr_data:
                        correlations[i, j] = corr_data[key1]
                    elif key2 in corr_data:
                        correlations[i, j] = corr_data[key2]
                    else:
                        # Default correlation for unspecified pairs
                        correlations[i, j] = 0.05
        
        # Ensure matrix is positive definite
        self.correlation_matrix = self._ensure_positive_definite(correlations)
        self.asset_names = assets
        
        logger.info("Correlation matrix initialized with %d x %d assets", n_assets, n_assets)
    
    def _ensure_positive_definite(self, matrix: np.ndarray, min_eigenval: float = 0.01) -> np.ndarray:
        """Ensure correlation matrix is positive definite for Cholesky decomposition"""
        
        # Check if already positive definite
        eigenvals = np.linalg.eigvals(matrix)
        if np.all(eigenvals > 0):
            return matrix
        
        # Fix negative eigenvalues
        eigenvals, eigenvecs = np.linalg.eigh(matrix)
        eigenvals = np.maximum(eigenvals, min_eigenval)
        
        # Reconstruct matrix
        fixed_matrix = eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
        
        # Ensure diagonal is 1.0 (correlation matrix property)
        np.fill_diagonal(fixed_matrix, 1.0)
        
        logger.warning("Correlation matrix adjusted to ensure positive definiteness")
        return fixed_matrix
    
    def _initialize_inflation_assumptions(self):
        """Initialize inflation modeling assumptions"""
        
        self.inflation_assumptions = {
            "long_term_target": 0.025,    # 2.5% long-term inflation target
            "current_level": 0.032,       # Current elevated inflation
            "volatility": 0.008,          # Inflation volatility
            "mean_reversion_speed": 0.3,  # Speed of reversion to target
            "correlation_with_bonds": -0.6, # Negative correlation with bonds
            "correlation_with_equities": -0.2, # Slight negative correlation with equities
        }
    
    def get_asset_assumptions(self, asset_class: str) -> AssetClassAssumptions:
        """Get assumptions for a specific asset class"""
        if asset_class not in self.asset_classes:
            raise ValueError(f"Unknown asset class: {asset_class}")
        return self.asset_classes[asset_class]
    
    def get_correlation(self, asset1: str, asset2: str) -> float:
        """Get correlation between two asset classes"""
        try:
            idx1 = self.asset_names.index(asset1)
            idx2 = self.asset_names.index(asset2)
            return self.correlation_matrix[idx1, idx2]
        except ValueError:
            raise ValueError(f"Unknown asset class: {asset1} or {asset2}")
    
    def get_covariance_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """
        Get covariance matrix for all asset classes
        
        Returns:
            Tuple of (covariance_matrix, asset_names)
        """
        volatilities = np.array([
            self.asset_classes[asset].volatility 
            for asset in self.asset_names
        ])
        
        # Convert correlation to covariance: Cov = Corr * vol_i * vol_j
        vol_matrix = np.outer(volatilities, volatilities)
        covariance_matrix = self.correlation_matrix * vol_matrix
        
        return covariance_matrix, self.asset_names
    
    def simulate_inflation_path(self, years: int, n_simulations: int = 1) -> np.ndarray:
        """
        Simulate inflation paths using mean-reverting process
        
        Args:
            years: Number of years to simulate
            n_simulations: Number of simulation paths
            
        Returns:
            Array of shape (n_simulations, years * 12) with monthly inflation rates
        """
        n_months = years * 12
        dt = 1/12  # Monthly time step
        
        current_inflation = self.inflation_assumptions["current_level"]
        target_inflation = self.inflation_assumptions["long_term_target"]
        volatility = self.inflation_assumptions["volatility"]
        mean_reversion = self.inflation_assumptions["mean_reversion_speed"]
        
        # Initialize array
        inflation_paths = np.zeros((n_simulations, n_months))
        inflation_paths[:, 0] = current_inflation
        
        # Generate random shocks
        random_shocks = np.random.normal(0, 1, size=(n_simulations, n_months - 1))
        
        # Simulate mean-reverting process: dr = speed * (target - r) * dt + vol * sqrt(dt) * dW
        for t in range(1, n_months):
            prev_inflation = inflation_paths[:, t-1]
            drift = mean_reversion * (target_inflation - prev_inflation) * dt
            shock = volatility * np.sqrt(dt) * random_shocks[:, t-1]
            inflation_paths[:, t] = prev_inflation + drift + shock
        
        # Ensure inflation stays positive
        inflation_paths = np.maximum(inflation_paths, 0.001)  # Minimum 0.1% inflation
        
        return inflation_paths
    
    def get_real_returns(self, asset_returns: np.ndarray, inflation_rates: np.ndarray) -> np.ndarray:
        """
        Convert nominal returns to real returns
        
        Args:
            asset_returns: Nominal returns array
            inflation_rates: Inflation rates array
            
        Returns:
            Real returns adjusted for inflation
        """
        # Real return = (1 + nominal) / (1 + inflation) - 1
        return (1 + asset_returns) / (1 + inflation_rates) - 1
    
    def stress_test_correlations(self, stress_factor: float = 1.5) -> np.ndarray:
        """
        Apply stress testing to correlations (increase during market stress)
        
        Args:
            stress_factor: Factor to increase correlations during stress periods
            
        Returns:
            Stressed correlation matrix
        """
        stressed_corr = self.correlation_matrix.copy()
        
        # Increase off-diagonal correlations during stress
        mask = ~np.eye(stressed_corr.shape[0], dtype=bool)
        stressed_corr[mask] = np.minimum(stressed_corr[mask] * stress_factor, 0.95)
        
        return self._ensure_positive_definite(stressed_corr)
    
    def update_assumptions(self, market_regime: str = "normal"):
        """
        Update market assumptions based on current regime
        
        Args:
            market_regime: One of "bull", "bear", "normal", "crisis"
        """
        regime_adjustments = {
            "bull": {"return_multiplier": 1.2, "vol_multiplier": 0.8, "correlation_increase": 0.1},
            "bear": {"return_multiplier": 0.7, "vol_multiplier": 1.4, "correlation_increase": 0.3},
            "normal": {"return_multiplier": 1.0, "vol_multiplier": 1.0, "correlation_increase": 0.0},
            "crisis": {"return_multiplier": 0.5, "vol_multiplier": 2.0, "correlation_increase": 0.5},
        }
        
        if market_regime not in regime_adjustments:
            raise ValueError(f"Unknown market regime: {market_regime}")
        
        adjustments = regime_adjustments[market_regime]
        
        # Adjust asset class assumptions
        for asset_class in self.asset_classes.values():
            asset_class.expected_return *= adjustments["return_multiplier"]
            asset_class.volatility *= adjustments["vol_multiplier"]
        
        # Adjust correlations
        if adjustments["correlation_increase"] > 0:
            mask = ~np.eye(self.correlation_matrix.shape[0], dtype=bool)
            self.correlation_matrix[mask] += adjustments["correlation_increase"]
            self.correlation_matrix = np.minimum(self.correlation_matrix, 0.95)
            self.correlation_matrix = self._ensure_positive_definite(self.correlation_matrix)
        
        self.last_updated = datetime.now()
        logger.info(f"Market assumptions updated for {market_regime} regime")
    
    def get_summary_statistics(self) -> Dict:
        """Get summary statistics of current market assumptions"""
        
        returns = [asset.expected_return for asset in self.asset_classes.values()]
        volatilities = [asset.volatility for asset in self.asset_classes.values()]
        sharpe_ratios = [asset.sharpe_ratio for asset in self.asset_classes.values()]
        
        return {
            "asset_classes": len(self.asset_classes),
            "expected_returns": {
                "min": min(returns),
                "max": max(returns), 
                "mean": np.mean(returns),
                "median": np.median(returns)
            },
            "volatilities": {
                "min": min(volatilities),
                "max": max(volatilities),
                "mean": np.mean(volatilities),
                "median": np.median(volatilities)
            },
            "correlations": {
                "min": np.min(self.correlation_matrix[~np.eye(len(self.asset_names), dtype=bool)]),
                "max": np.max(self.correlation_matrix[~np.eye(len(self.asset_names), dtype=bool)]),
                "mean": np.mean(self.correlation_matrix[~np.eye(len(self.asset_names), dtype=bool)])
            },
            "last_updated": self.last_updated.isoformat()
        }