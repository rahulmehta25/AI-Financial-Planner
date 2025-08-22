"""
GPU-Accelerated Monte Carlo Simulation Engine using CUDA

This module provides high-performance Monte Carlo simulations using GPU acceleration
through CuPy/CUDA for massive speedups in financial simulations.
"""

import logging
import time
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import numpy as np

# GPU acceleration imports with fallback
try:
    import cupy as cp
    from cupy import cuda
    GPU_AVAILABLE = cuda.is_available()
except ImportError:
    GPU_AVAILABLE = False
    cp = np  # Fallback to NumPy if CuPy not available

# Performance monitoring
from ..simulations.logging_config import performance_monitor

logger = logging.getLogger(__name__)


class GPUMonteCarloEngine:
    """
    GPU-accelerated Monte Carlo simulation engine for financial portfolios
    
    Features:
    - CUDA kernel optimization for parallel processing
    - Memory pooling for efficient GPU memory management
    - Batch processing for large simulations
    - Automatic CPU fallback if GPU unavailable
    """
    
    def __init__(self, use_gpu: bool = True):
        """
        Initialize the GPU Monte Carlo engine
        
        Args:
            use_gpu: Whether to use GPU acceleration if available
        """
        self.use_gpu = use_gpu and GPU_AVAILABLE
        self.xp = cp if self.use_gpu else np
        
        if self.use_gpu:
            # Set up memory pool for efficient allocation
            mempool = cp.get_default_memory_pool()
            pinned_mempool = cp.get_default_pinned_memory_pool()
            
            # Configure memory limits (8GB GPU memory)
            mempool.set_limit(size=8 * 1024**3)
            
            logger.info(f"GPU Monte Carlo initialized - Device: {cp.cuda.Device().name}")
        else:
            logger.info("GPU not available, using CPU fallback")
    
    @performance_monitor
    def simulate_portfolio_gpu(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        portfolio_weights: np.ndarray,
        n_simulations: int,
        n_years: int,
        initial_value: float,
        monthly_contributions: np.ndarray,
        rebalance_frequency: int = 12,
        batch_size: int = 10000
    ) -> np.ndarray:
        """
        Run Monte Carlo simulation on GPU
        
        Args:
            expected_returns: Expected annual returns for each asset class
            covariance_matrix: Covariance matrix for asset classes
            portfolio_weights: Portfolio allocation weights
            n_simulations: Number of simulation paths
            n_years: Number of years to simulate
            initial_value: Initial portfolio value
            monthly_contributions: Monthly contribution amounts
            rebalance_frequency: Rebalancing frequency (months)
            batch_size: Batch size for GPU processing
            
        Returns:
            Array of portfolio values with shape (n_simulations, n_months)
        """
        n_months = n_years * 12
        n_assets = len(expected_returns)
        
        # Transfer data to GPU
        if self.use_gpu:
            expected_returns_gpu = cp.asarray(expected_returns)
            covariance_gpu = cp.asarray(covariance_matrix)
            weights_gpu = cp.asarray(portfolio_weights)
            contributions_gpu = cp.asarray(monthly_contributions)
        else:
            expected_returns_gpu = expected_returns
            covariance_gpu = covariance_matrix
            weights_gpu = portfolio_weights
            contributions_gpu = monthly_contributions
        
        # Convert to monthly parameters
        monthly_returns = expected_returns_gpu / 12.0
        monthly_covariance = covariance_gpu / 12.0
        
        # Cholesky decomposition for correlated returns
        chol_cov = self.xp.linalg.cholesky(monthly_covariance)
        
        # Initialize portfolio values array
        portfolio_values = self.xp.zeros((n_simulations, n_months))
        portfolio_values[:, 0] = initial_value
        
        # Process in batches to manage GPU memory
        for batch_start in range(0, n_simulations, batch_size):
            batch_end = min(batch_start + batch_size, n_simulations)
            batch_simulations = batch_end - batch_start
            
            # Generate random returns for batch
            random_normals = self.xp.random.standard_normal(
                (batch_simulations, n_months - 1, n_assets)
            )
            
            # Simulate portfolio paths for batch
            self._simulate_batch(
                portfolio_values[batch_start:batch_end],
                random_normals,
                chol_cov,
                monthly_returns,
                weights_gpu,
                contributions_gpu,
                rebalance_frequency,
                n_months
            )
        
        # Transfer results back to CPU if using GPU
        if self.use_gpu:
            portfolio_values = cp.asnumpy(portfolio_values)
            # Clear GPU memory
            mempool = cp.get_default_memory_pool()
            mempool.free_all_blocks()
        
        return portfolio_values
    
    def _simulate_batch(
        self,
        batch_values: Union[np.ndarray, 'cp.ndarray'],
        random_normals: Union[np.ndarray, 'cp.ndarray'],
        chol_cov: Union[np.ndarray, 'cp.ndarray'],
        monthly_returns: Union[np.ndarray, 'cp.ndarray'],
        weights: Union[np.ndarray, 'cp.ndarray'],
        contributions: Union[np.ndarray, 'cp.ndarray'],
        rebalance_frequency: int,
        n_months: int
    ):
        """
        Simulate a batch of portfolio paths
        
        This method uses vectorized operations optimized for GPU
        """
        batch_size = batch_values.shape[0]
        n_assets = len(weights)
        
        # Initialize asset values for each simulation
        asset_values = self.xp.zeros((batch_size, n_assets))
        for i in range(n_assets):
            asset_values[:, i] = batch_values[:, 0] * weights[i]
        
        # Simulate each month
        for month in range(1, n_months):
            # Generate correlated returns
            correlated_randoms = self.xp.dot(random_normals[:, month-1], chol_cov.T)
            asset_returns = monthly_returns + correlated_randoms
            
            # Update asset values
            asset_values *= (1 + asset_returns)
            
            # Add contributions
            contribution = contributions[min(month-1, len(contributions)-1)]
            for i in range(n_assets):
                asset_values[:, i] += contribution * weights[i]
            
            # Rebalance if needed
            if month % rebalance_frequency == 0:
                total_value = self.xp.sum(asset_values, axis=1, keepdims=True)
                for i in range(n_assets):
                    asset_values[:, i] = total_value[:, 0] * weights[i]
            
            # Store total portfolio value
            batch_values[:, month] = self.xp.sum(asset_values, axis=1)
    
    @performance_monitor
    def calculate_statistics_gpu(
        self,
        simulation_results: np.ndarray,
        percentiles: List[float] = [5, 25, 50, 75, 95]
    ) -> Dict[str, Union[float, np.ndarray]]:
        """
        Calculate statistics from simulation results using GPU
        
        Args:
            simulation_results: Simulation results array
            percentiles: List of percentiles to calculate
            
        Returns:
            Dictionary of statistics
        """
        if self.use_gpu:
            results_gpu = cp.asarray(simulation_results)
        else:
            results_gpu = simulation_results
        
        # Calculate statistics on GPU
        stats = {
            'mean': self.xp.mean(results_gpu, axis=0),
            'std': self.xp.std(results_gpu, axis=0),
            'min': self.xp.min(results_gpu, axis=0),
            'max': self.xp.max(results_gpu, axis=0),
            'percentiles': {}
        }
        
        # Calculate percentiles
        for p in percentiles:
            stats['percentiles'][p] = self.xp.percentile(results_gpu, p, axis=0)
        
        # Transfer back to CPU if using GPU
        if self.use_gpu:
            stats = {
                k: cp.asnumpy(v) if isinstance(v, cp.ndarray) else v
                for k, v in stats.items()
            }
            if 'percentiles' in stats:
                stats['percentiles'] = {
                    k: cp.asnumpy(v) if isinstance(v, cp.ndarray) else v
                    for k, v in stats['percentiles'].items()
                }
        
        return stats
    
    def get_device_info(self) -> Dict[str, any]:
        """Get information about the GPU device"""
        if not self.use_gpu:
            return {"device": "CPU", "gpu_available": False}
        
        device = cp.cuda.Device()
        return {
            "device": device.name.decode(),
            "gpu_available": True,
            "compute_capability": device.compute_capability,
            "total_memory": device.mem_info[1] / (1024**3),  # GB
            "free_memory": device.mem_info[0] / (1024**3),  # GB
        }


# CUDA kernel for advanced operations (if needed)
if GPU_AVAILABLE:
    # Custom CUDA kernel for portfolio simulation
    portfolio_kernel = cp.ElementwiseKernel(
        'float64 value, float64 return_rate, float64 contribution',
        'float64 new_value',
        'new_value = (value * (1 + return_rate)) + contribution',
        'portfolio_update'
    )
    
    # Kernel for risk metric calculation
    risk_kernel = cp.ReductionKernel(
        'float64 x',
        'float64 y',
        'x',
        'a + b',
        'y = sqrt(a / _in_ind.size())',
        '0',
        'risk_calculation'
    )