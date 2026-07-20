"""
Advanced CUDA-Accelerated Monte Carlo Simulation with CuPy

Implements highly optimized GPU kernels for financial simulations with:
- Custom CUDA kernels for maximum performance
- GPU memory management and pooling
- Multi-GPU support for large simulations
- CPU/GPU hybrid execution
- Performance benchmarking and profiling
"""

import logging
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import asyncio

# GPU acceleration imports
try:
    import cupy as cp
    from cupy import cuda
    from cupyx.profiler import benchmark
    GPU_AVAILABLE = cuda.is_available()
    
    # Custom CUDA kernels
    if GPU_AVAILABLE:
        # Portfolio simulation kernel with optimizations
        cuda_portfolio_kernel = cp.RawKernel(r'''
        extern "C" __global__
        void simulate_portfolio(
            float* portfolio_values,
            const float* random_normals,
            const float* chol_cov,
            const float* monthly_returns,
            const float* weights,
            const float* contributions,
            const int n_simulations,
            const int n_months,
            const int n_assets,
            const int rebalance_freq,
            const float initial_value
        ) {
            int sim_idx = blockIdx.x * blockDim.x + threadIdx.x;
            if (sim_idx >= n_simulations) return;
            
            extern __shared__ float shared_mem[];
            float* asset_values = shared_mem + threadIdx.x * n_assets;
            
            // Initialize portfolio
            portfolio_values[sim_idx * n_months] = initial_value;
            
            // Initialize asset values
            for (int i = 0; i < n_assets; i++) {
                asset_values[i] = initial_value * weights[i];
            }
            
            // Simulate each month
            for (int month = 1; month < n_months; month++) {
                float total_value = 0.0f;
                
                // Generate correlated returns
                for (int i = 0; i < n_assets; i++) {
                    float corr_return = 0.0f;
                    for (int j = 0; j < n_assets; j++) {
                        int rand_idx = sim_idx * (n_months - 1) * n_assets + 
                                     (month - 1) * n_assets + j;
                        corr_return += random_normals[rand_idx] * 
                                     chol_cov[i * n_assets + j];
                    }
                    
                    // Update asset value
                    float asset_return = monthly_returns[i] + corr_return;
                    asset_values[i] *= (1.0f + asset_return);
                    
                    // Add contribution
                    int contrib_idx = min(month - 1, n_months - 1);
                    asset_values[i] += contributions[contrib_idx] * weights[i];
                    
                    total_value += asset_values[i];
                }
                
                // Rebalance if needed
                if (month % rebalance_freq == 0) {
                    for (int i = 0; i < n_assets; i++) {
                        asset_values[i] = total_value * weights[i];
                    }
                }
                
                // Store portfolio value
                portfolio_values[sim_idx * n_months + month] = total_value;
            }
        }
        ''', 'simulate_portfolio')
        
        # Risk metrics calculation kernel
        cuda_risk_kernel = cp.RawKernel(r'''
        extern "C" __global__
        void calculate_risk_metrics(
            const float* portfolio_values,
            float* var_values,
            float* cvar_values,
            float* max_drawdowns,
            const int n_simulations,
            const int n_months,
            const float confidence_level
        ) {
            int sim_idx = blockIdx.x * blockDim.x + threadIdx.x;
            if (sim_idx >= n_simulations) return;
            
            float max_value = 0.0f;
            float max_dd = 0.0f;
            float final_value = portfolio_values[sim_idx * n_months + n_months - 1];
            
            // Calculate maximum drawdown
            for (int month = 0; month < n_months; month++) {
                float value = portfolio_values[sim_idx * n_months + month];
                if (value > max_value) {
                    max_value = value;
                }
                float drawdown = (max_value - value) / max_value;
                if (drawdown > max_dd) {
                    max_dd = drawdown;
                }
            }
            
            max_drawdowns[sim_idx] = max_dd;
            
            // Store final values for VaR/CVaR calculation
            var_values[sim_idx] = final_value;
        }
        ''', 'calculate_risk_metrics')
        
except ImportError:
    GPU_AVAILABLE = False
    cp = np

logger = logging.getLogger(__name__)


@dataclass
class GPUSimulationConfig:
    """Configuration for GPU simulation"""
    batch_size: int = 10000
    block_size: int = 256
    shared_memory_size: int = 49152  # 48KB shared memory
    memory_pool_size: int = 8 * 1024**3  # 8GB
    use_multiple_gpus: bool = True
    enable_profiling: bool = False
    precision: str = "float32"  # float32 or float64


class AdvancedGPUMonteCarloEngine:
    """
    Advanced GPU-accelerated Monte Carlo engine with CUDA optimizations
    """
    
    def __init__(self, config: GPUSimulationConfig = None):
        """
        Initialize advanced GPU Monte Carlo engine
        
        Args:
            config: GPU simulation configuration
        """
        self.config = config or GPUSimulationConfig()
        self.gpu_available = GPU_AVAILABLE
        
        if self.gpu_available:
            self._initialize_gpu()
        else:
            logger.warning("GPU not available, using CPU fallback")
        
        # Performance metrics
        self.performance_metrics = {
            'kernel_time': 0,
            'memory_transfer_time': 0,
            'total_simulations': 0,
            'gpu_memory_used': 0
        }
    
    def _initialize_gpu(self):
        """Initialize GPU resources"""
        # Set up memory pool
        mempool = cp.get_default_memory_pool()
        pinned_mempool = cp.get_default_pinned_memory_pool()
        mempool.set_limit(size=self.config.memory_pool_size)
        
        # Get GPU information
        self.gpu_count = cuda.runtime.getDeviceCount()
        self.gpu_devices = []
        
        for i in range(self.gpu_count):
            with cuda.Device(i):
                device_props = cuda.runtime.getDeviceProperties(i)
                self.gpu_devices.append({
                    'id': i,
                    'name': device_props['name'].decode(),
                    'compute_capability': f"{device_props['major']}.{device_props['minor']}",
                    'total_memory': device_props['totalGlobalMem'] / (1024**3),
                    'multiprocessors': device_props['multiProcessorCount'],
                    'max_threads_per_block': device_props['maxThreadsPerBlock'],
                    'max_shared_memory': device_props['sharedMemPerBlock']
                })
        
        logger.info(f"Initialized {self.gpu_count} GPU(s): {self.gpu_devices}")
    
    async def simulate_portfolio_advanced(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        portfolio_weights: np.ndarray,
        n_simulations: int,
        n_years: int,
        initial_value: float,
        monthly_contributions: np.ndarray,
        rebalance_frequency: int = 12,
        calculate_risk_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Run advanced GPU-accelerated portfolio simulation
        
        Args:
            expected_returns: Expected annual returns
            covariance_matrix: Asset covariance matrix
            portfolio_weights: Portfolio weights
            n_simulations: Number of simulation paths
            n_years: Simulation horizon
            initial_value: Initial portfolio value
            monthly_contributions: Monthly contributions
            rebalance_frequency: Rebalancing frequency (months)
            calculate_risk_metrics: Whether to calculate risk metrics
            
        Returns:
            Dictionary with simulation results and metrics
        """
        start_time = time.perf_counter()
        n_months = n_years * 12
        n_assets = len(expected_returns)
        
        # Choose precision
        dtype = cp.float32 if self.config.precision == "float32" else cp.float64
        
        # Transfer data to GPU
        transfer_start = time.perf_counter()
        
        if self.gpu_available:
            expected_returns_gpu = cp.asarray(expected_returns, dtype=dtype)
            covariance_gpu = cp.asarray(covariance_matrix, dtype=dtype)
            weights_gpu = cp.asarray(portfolio_weights, dtype=dtype)
            contributions_gpu = cp.asarray(monthly_contributions, dtype=dtype)
            
            # Prepare for simulation
            monthly_returns = expected_returns_gpu / 12.0
            monthly_covariance = covariance_gpu / 12.0
            chol_cov = cp.linalg.cholesky(monthly_covariance)
        else:
            # CPU fallback
            monthly_returns = expected_returns / 12.0
            monthly_covariance = covariance_matrix / 12.0
            chol_cov = np.linalg.cholesky(monthly_covariance)
        
        self.performance_metrics['memory_transfer_time'] += time.perf_counter() - transfer_start
        
        # Determine execution strategy
        if n_simulations > 100000 and self.gpu_count > 1 and self.config.use_multiple_gpus:
            # Use multiple GPUs for large simulations
            results = await self._multi_gpu_simulation(
                n_simulations, n_months, n_assets,
                chol_cov, monthly_returns, weights_gpu,
                contributions_gpu, initial_value, rebalance_frequency
            )
        else:
            # Single GPU execution
            results = await self._single_gpu_simulation(
                n_simulations, n_months, n_assets,
                chol_cov, monthly_returns, weights_gpu if self.gpu_available else portfolio_weights,
                contributions_gpu if self.gpu_available else monthly_contributions,
                initial_value, rebalance_frequency
            )
        
        # Calculate risk metrics if requested
        if calculate_risk_metrics:
            risk_metrics = self._calculate_risk_metrics(results['portfolio_values'])
            results['risk_metrics'] = risk_metrics
        
        # Calculate statistics
        results['statistics'] = self._calculate_statistics(results['portfolio_values'])
        
        # Performance metrics
        total_time = time.perf_counter() - start_time
        results['performance'] = {
            'total_time': total_time,
            'simulations_per_second': n_simulations / total_time,
            'kernel_time': self.performance_metrics['kernel_time'],
            'memory_transfer_time': self.performance_metrics['memory_transfer_time'],
            'gpu_memory_used': self._get_gpu_memory_usage() if self.gpu_available else 0
        }
        
        self.performance_metrics['total_simulations'] += n_simulations
        
        return results
    
    async def _single_gpu_simulation(
        self,
        n_simulations: int,
        n_months: int,
        n_assets: int,
        chol_cov: Union[np.ndarray, 'cp.ndarray'],
        monthly_returns: Union[np.ndarray, 'cp.ndarray'],
        weights: Union[np.ndarray, 'cp.ndarray'],
        contributions: Union[np.ndarray, 'cp.ndarray'],
        initial_value: float,
        rebalance_frequency: int
    ) -> Dict[str, Any]:
        """Execute simulation on single GPU"""
        
        if self.gpu_available:
            # Allocate memory for results
            portfolio_values = cp.zeros((n_simulations, n_months), dtype=cp.float32)
            
            # Generate random numbers on GPU
            random_normals = cp.random.standard_normal(
                (n_simulations, n_months - 1, n_assets),
                dtype=cp.float32
            )
            
            # Flatten arrays for kernel
            random_normals_flat = random_normals.reshape(-1)
            chol_cov_flat = chol_cov.astype(cp.float32).reshape(-1)
            monthly_returns_flat = monthly_returns.astype(cp.float32)
            weights_flat = weights.astype(cp.float32)
            contributions_flat = contributions.astype(cp.float32)
            
            # Configure kernel launch parameters
            threads_per_block = self.config.block_size
            blocks_per_grid = (n_simulations + threads_per_block - 1) // threads_per_block
            shared_mem_size = threads_per_block * n_assets * 4  # float32 size
            
            # Launch CUDA kernel
            kernel_start = time.perf_counter()
            
            cuda_portfolio_kernel(
                (blocks_per_grid,), (threads_per_block,),
                (
                    portfolio_values,
                    random_normals_flat,
                    chol_cov_flat,
                    monthly_returns_flat,
                    weights_flat,
                    contributions_flat,
                    n_simulations,
                    n_months,
                    n_assets,
                    rebalance_frequency,
                    initial_value
                ),
                shared_mem=shared_mem_size
            )
            
            # Synchronize
            cuda.stream.get_current_stream().synchronize()
            
            self.performance_metrics['kernel_time'] += time.perf_counter() - kernel_start
            
            # Transfer results back to CPU
            portfolio_values_cpu = cp.asnumpy(portfolio_values)
            
        else:
            # CPU fallback implementation
            portfolio_values_cpu = self._cpu_simulation(
                n_simulations, n_months, n_assets,
                chol_cov, monthly_returns, weights,
                contributions, initial_value, rebalance_frequency
            )
        
        return {
            'portfolio_values': portfolio_values_cpu,
            'n_simulations': n_simulations,
            'n_months': n_months
        }
    
    async def _multi_gpu_simulation(
        self,
        n_simulations: int,
        n_months: int,
        n_assets: int,
        chol_cov: 'cp.ndarray',
        monthly_returns: 'cp.ndarray',
        weights: 'cp.ndarray',
        contributions: 'cp.ndarray',
        initial_value: float,
        rebalance_frequency: int
    ) -> Dict[str, Any]:
        """Execute simulation across multiple GPUs"""
        
        # Divide simulations among GPUs
        sims_per_gpu = n_simulations // self.gpu_count
        remainder = n_simulations % self.gpu_count
        
        async def run_on_gpu(gpu_id: int, n_sims: int) -> np.ndarray:
            with cuda.Device(gpu_id):
                # Create local copies on this GPU
                local_chol = cp.asarray(chol_cov)
                local_returns = cp.asarray(monthly_returns)
                local_weights = cp.asarray(weights)
                local_contributions = cp.asarray(contributions)
                
                # Run simulation on this GPU
                result = await self._single_gpu_simulation(
                    n_sims, n_months, n_assets,
                    local_chol, local_returns, local_weights,
                    local_contributions, initial_value, rebalance_frequency
                )
                
                return result['portfolio_values']
        
        # Launch simulations on all GPUs
        tasks = []
        for gpu_id in range(self.gpu_count):
            n_sims = sims_per_gpu + (1 if gpu_id < remainder else 0)
            if n_sims > 0:
                tasks.append(run_on_gpu(gpu_id, n_sims))
        
        # Wait for all GPUs to complete
        results = await asyncio.gather(*tasks)
        
        # Combine results
        portfolio_values = np.vstack(results)
        
        return {
            'portfolio_values': portfolio_values,
            'n_simulations': n_simulations,
            'n_months': n_months
        }
    
    def _cpu_simulation(
        self,
        n_simulations: int,
        n_months: int,
        n_assets: int,
        chol_cov: np.ndarray,
        monthly_returns: np.ndarray,
        weights: np.ndarray,
        contributions: np.ndarray,
        initial_value: float,
        rebalance_frequency: int
    ) -> np.ndarray:
        """CPU fallback for simulation"""
        
        portfolio_values = np.zeros((n_simulations, n_months))
        portfolio_values[:, 0] = initial_value
        
        for sim in range(n_simulations):
            asset_values = initial_value * weights
            
            for month in range(1, n_months):
                # Generate returns
                random_normals = np.random.standard_normal(n_assets)
                correlated_returns = np.dot(chol_cov, random_normals)
                asset_returns = monthly_returns + correlated_returns
                
                # Update values
                asset_values *= (1 + asset_returns)
                
                # Add contributions
                contrib_idx = min(month - 1, len(contributions) - 1)
                asset_values += contributions[contrib_idx] * weights
                
                # Rebalance if needed
                if month % rebalance_frequency == 0:
                    total_value = np.sum(asset_values)
                    asset_values = total_value * weights
                
                portfolio_values[sim, month] = np.sum(asset_values)
        
        return portfolio_values
    
    def _calculate_risk_metrics(self, portfolio_values: np.ndarray) -> Dict[str, float]:
        """Calculate risk metrics from simulation results"""
        
        if self.gpu_available:
            values_gpu = cp.asarray(portfolio_values)
            
            # Calculate returns
            final_values = values_gpu[:, -1]
            initial_values = values_gpu[:, 0]
            returns = (final_values - initial_values) / initial_values
            
            # Calculate metrics on GPU
            metrics = {
                'mean_return': float(cp.mean(returns)),
                'std_return': float(cp.std(returns)),
                'var_95': float(cp.percentile(returns, 5)),
                'cvar_95': float(cp.mean(returns[returns <= cp.percentile(returns, 5)])),
                'max_drawdown': float(self._calculate_max_drawdown_gpu(values_gpu)),
                'sharpe_ratio': float(cp.mean(returns) / cp.std(returns)) if cp.std(returns) > 0 else 0
            }
            
        else:
            # CPU calculation
            final_values = portfolio_values[:, -1]
            initial_values = portfolio_values[:, 0]
            returns = (final_values - initial_values) / initial_values
            
            metrics = {
                'mean_return': float(np.mean(returns)),
                'std_return': float(np.std(returns)),
                'var_95': float(np.percentile(returns, 5)),
                'cvar_95': float(np.mean(returns[returns <= np.percentile(returns, 5)])),
                'max_drawdown': float(self._calculate_max_drawdown_cpu(portfolio_values)),
                'sharpe_ratio': float(np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0
            }
        
        return metrics
    
    def _calculate_max_drawdown_gpu(self, values: 'cp.ndarray') -> float:
        """Calculate maximum drawdown on GPU"""
        n_simulations, n_months = values.shape
        
        # Calculate running maximum
        running_max = cp.maximum.accumulate(values, axis=1)
        
        # Calculate drawdowns
        drawdowns = (running_max - values) / running_max
        
        # Get maximum drawdown for each simulation
        max_drawdowns = cp.max(drawdowns, axis=1)
        
        # Return average maximum drawdown
        return cp.mean(max_drawdowns)
    
    def _calculate_max_drawdown_cpu(self, values: np.ndarray) -> float:
        """Calculate maximum drawdown on CPU"""
        n_simulations, n_months = values.shape
        
        max_drawdowns = []
        for sim in range(n_simulations):
            running_max = 0
            max_dd = 0
            
            for value in values[sim]:
                running_max = max(running_max, value)
                drawdown = (running_max - value) / running_max if running_max > 0 else 0
                max_dd = max(max_dd, drawdown)
            
            max_drawdowns.append(max_dd)
        
        return np.mean(max_drawdowns)
    
    def _calculate_statistics(self, portfolio_values: np.ndarray) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        
        if self.gpu_available:
            values_gpu = cp.asarray(portfolio_values)
            
            stats = {
                'mean': cp.asnumpy(cp.mean(values_gpu, axis=0)),
                'std': cp.asnumpy(cp.std(values_gpu, axis=0)),
                'min': cp.asnumpy(cp.min(values_gpu, axis=0)),
                'max': cp.asnumpy(cp.max(values_gpu, axis=0)),
                'percentiles': {}
            }
            
            for p in percentiles:
                stats['percentiles'][p] = cp.asnumpy(cp.percentile(values_gpu, p, axis=0))
                
        else:
            stats = {
                'mean': np.mean(portfolio_values, axis=0),
                'std': np.std(portfolio_values, axis=0),
                'min': np.min(portfolio_values, axis=0),
                'max': np.max(portfolio_values, axis=0),
                'percentiles': {}
            }
            
            for p in percentiles:
                stats['percentiles'][p] = np.percentile(portfolio_values, p, axis=0)
        
        return stats
    
    def _get_gpu_memory_usage(self) -> Dict[str, float]:
        """Get current GPU memory usage"""
        if not self.gpu_available:
            return {}
        
        mempool = cp.get_default_memory_pool()
        used_bytes = mempool.used_bytes()
        total_bytes = mempool.total_bytes()
        
        return {
            'used_gb': used_bytes / (1024**3),
            'total_gb': total_bytes / (1024**3),
            'percentage': (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
        }
    
    def benchmark_performance(
        self,
        simulation_sizes: List[int] = [1000, 10000, 100000],
        n_years: int = 30,
        n_assets: int = 5
    ) -> Dict[str, Any]:
        """
        Benchmark GPU performance with different simulation sizes
        
        Args:
            simulation_sizes: List of simulation counts to benchmark
            n_years: Number of years to simulate
            n_assets: Number of assets in portfolio
            
        Returns:
            Benchmark results
        """
        results = {}
        
        # Generate test data
        expected_returns = np.random.uniform(0.05, 0.15, n_assets)
        covariance = np.random.uniform(0.01, 0.05, (n_assets, n_assets))
        covariance = np.dot(covariance, covariance.T)  # Make positive definite
        weights = np.ones(n_assets) / n_assets
        contributions = np.ones(n_years * 12) * 1000
        
        for n_simulations in simulation_sizes:
            logger.info(f"Benchmarking {n_simulations} simulations...")
            
            if self.gpu_available:
                # GPU benchmark
                gpu_start = time.perf_counter()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                gpu_result = loop.run_until_complete(
                    self.simulate_portfolio_advanced(
                        expected_returns, covariance, weights,
                        n_simulations, n_years, 100000,
                        contributions, calculate_risk_metrics=False
                    )
                )
                
                gpu_time = time.perf_counter() - gpu_start
                
                # CPU benchmark for comparison
                self.gpu_available = False
                cpu_start = time.perf_counter()
                
                cpu_result = loop.run_until_complete(
                    self.simulate_portfolio_advanced(
                        expected_returns, covariance, weights,
                        min(n_simulations, 1000), n_years, 100000,
                        contributions, calculate_risk_metrics=False
                    )
                )
                
                cpu_time = (time.perf_counter() - cpu_start) * (n_simulations / min(n_simulations, 1000))
                self.gpu_available = True
                
                results[n_simulations] = {
                    'gpu_time': gpu_time,
                    'cpu_time_estimated': cpu_time,
                    'speedup': cpu_time / gpu_time,
                    'gpu_simulations_per_second': n_simulations / gpu_time,
                    'gpu_memory_used': gpu_result['performance']['gpu_memory_used']
                }
                
            else:
                # CPU only benchmark
                cpu_start = time.perf_counter()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                cpu_result = loop.run_until_complete(
                    self.simulate_portfolio_advanced(
                        expected_returns, covariance, weights,
                        n_simulations, n_years, 100000,
                        contributions, calculate_risk_metrics=False
                    )
                )
                
                cpu_time = time.perf_counter() - cpu_start
                
                results[n_simulations] = {
                    'cpu_time': cpu_time,
                    'cpu_simulations_per_second': n_simulations / cpu_time
                }
        
        return results
    
    def cleanup(self):
        """Clean up GPU resources"""
        if self.gpu_available:
            mempool = cp.get_default_memory_pool()
            pinned_mempool = cp.get_default_pinned_memory_pool()
            
            mempool.free_all_blocks()
            pinned_mempool.free_all_blocks()
            
            logger.info("GPU resources cleaned up")