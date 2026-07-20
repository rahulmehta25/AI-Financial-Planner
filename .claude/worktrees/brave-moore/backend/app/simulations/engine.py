"""
High-Performance Monte Carlo Simulation Engine

Optimized Monte Carlo engine using Numba JIT compilation for fast simulation
of portfolio returns and retirement outcomes.
"""

import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import time

import numpy as np
import pandas as pd
from numba import jit, prange
from scipy.stats import multivariate_normal

from .market_assumptions import CapitalMarketAssumptions
from .logging_config import (
    SimulationLogger, performance_monitor, error_handler, 
    ValidationError, CalculationError, log_memory_usage,
    log_simulation_config, log_portfolio_allocation
)

# Initialize simulation logger
sim_logger = SimulationLogger("monte_carlo_engine")
logger = sim_logger.logger


@dataclass
class SimulationParameters:
    """Parameters for Monte Carlo simulation"""
    n_simulations: int = 50_000
    years_to_retirement: int = 30
    retirement_years: int = 25
    initial_portfolio_value: float = 100_000.0
    annual_contribution: float = 12_000.0
    contribution_growth_rate: float = 0.03  # 3% annual increase
    withdrawal_rate: float = 0.04  # 4% initial withdrawal rate
    rebalancing_frequency: int = 12  # Monthly rebalancing
    random_seed: Optional[int] = None


@dataclass
class PortfolioAllocation:
    """Portfolio allocation across asset classes"""
    allocations: Dict[str, float]  # Asset class -> allocation percentage
    
    def __post_init__(self):
        """Validate allocations sum to 1.0"""
        total = sum(self.allocations.values())
        if not np.isclose(total, 1.0, rtol=1e-3):
            raise ValueError(f"Portfolio allocations must sum to 1.0, got {total:.4f}")


@jit(nopython=True, parallel=True, cache=True)
def simulate_portfolio_paths_numba(
    expected_returns: np.ndarray,
    covariance_matrix: np.ndarray,
    portfolio_weights: np.ndarray,
    n_simulations: int,
    n_years: int,
    initial_value: float,
    monthly_contributions: np.ndarray,
    rebalance_frequency: int
) -> np.ndarray:
    """
    Numba-compiled Monte Carlo simulation for portfolio paths
    
    Args:
        expected_returns: Expected annual returns for each asset class
        covariance_matrix: Covariance matrix for asset classes
        portfolio_weights: Portfolio allocation weights
        n_simulations: Number of simulation paths
        n_years: Number of years to simulate
        initial_value: Initial portfolio value
        monthly_contributions: Monthly contribution amounts over time
        rebalance_frequency: Rebalancing frequency (1=annual, 12=monthly)
        
    Returns:
        Array of portfolio values with shape (n_simulations, n_months)
    """
    n_months = n_years * 12
    n_assets = len(expected_returns)
    
    # Convert annual parameters to monthly
    monthly_returns = expected_returns / 12.0
    monthly_covariance = covariance_matrix / 12.0
    
    # Initialize arrays
    portfolio_values = np.zeros((n_simulations, n_months))
    portfolio_values[:, 0] = initial_value
    
    # Pre-compute Cholesky decomposition for efficiency
    chol_cov = np.linalg.cholesky(monthly_covariance)
    
    # Generate all random numbers upfront for better performance
    random_normals = np.random.standard_normal((n_simulations, n_months - 1, n_assets))
    
    # Simulate each path
    for sim in prange(n_simulations):
        current_weights = portfolio_weights.copy()
        current_value = initial_value
        
        for month in range(1, n_months):
            # Generate correlated returns using Cholesky decomposition
            random_vec = random_normals[sim, month - 1, :]
            correlated_shocks = chol_cov @ random_vec
            monthly_asset_returns = monthly_returns + correlated_shocks
            
            # Calculate portfolio return
            portfolio_return = np.sum(current_weights * monthly_asset_returns)
            
            # Update portfolio value
            current_value *= (1.0 + portfolio_return)
            
            # Add contribution if within contribution period
            if month - 1 < len(monthly_contributions):
                current_value += monthly_contributions[month - 1]
            
            # Rebalance if needed (monthly or quarterly)
            if month % (12 // rebalance_frequency) == 0:
                current_weights = portfolio_weights.copy()
            
            portfolio_values[sim, month] = current_value
    
    return portfolio_values


@jit(nopython=True, parallel=True, cache=True)
def simulate_retirement_withdrawals_numba(
    portfolio_paths: np.ndarray,
    retirement_start_month: int,
    initial_withdrawal_rate: float,
    inflation_paths: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate retirement withdrawals with inflation adjustment
    
    Args:
        portfolio_paths: Portfolio value paths from accumulation phase
        retirement_start_month: Month when retirement begins
        initial_withdrawal_rate: Initial withdrawal rate (e.g., 0.04 for 4%)
        inflation_paths: Inflation rate paths for withdrawal adjustment
        
    Returns:
        Tuple of (final_balances, withdrawal_amounts)
    """
    n_simulations, n_months = portfolio_paths.shape
    retirement_months = n_months - retirement_start_month
    
    final_balances = np.zeros(n_simulations)
    withdrawal_amounts = np.zeros((n_simulations, retirement_months))
    
    for sim in prange(n_simulations):
        current_balance = portfolio_paths[sim, retirement_start_month]
        initial_withdrawal = current_balance * initial_withdrawal_rate
        
        for month in range(retirement_months):
            if month + retirement_start_month >= n_months:
                break
                
            # Adjust withdrawal for inflation
            if month < len(inflation_paths[sim]):
                cumulative_inflation = np.prod(1.0 + inflation_paths[sim, :month+1])
                current_withdrawal = initial_withdrawal * cumulative_inflation
            else:
                current_withdrawal = initial_withdrawal
            
            # Take withdrawal
            current_balance -= current_withdrawal
            withdrawal_amounts[sim, month] = current_withdrawal
            
            # Apply investment returns if balance is positive
            if current_balance > 0:
                # Use the simulated portfolio return for this month
                portfolio_return = (portfolio_paths[sim, retirement_start_month + month + 1] - 
                                  portfolio_paths[sim, retirement_start_month + month]) / portfolio_paths[sim, retirement_start_month + month]
                current_balance *= (1.0 + portfolio_return)
            else:
                current_balance = 0.0
                break
        
        final_balances[sim] = max(current_balance, 0.0)
    
    return final_balances, withdrawal_amounts


class MonteCarloEngine:
    """
    High-performance Monte Carlo simulation engine for retirement planning
    
    Features:
    - Numba JIT compilation for 10x+ performance improvement
    - Correlated asset class returns
    - Inflation modeling
    - Portfolio rebalancing
    - Configurable contribution and withdrawal patterns
    """
    
    def __init__(self, market_assumptions: Optional[CapitalMarketAssumptions] = None):
        """
        Initialize Monte Carlo engine
        
        Args:
            market_assumptions: Capital market assumptions, creates default if None
        """
        self.market_assumptions = market_assumptions or CapitalMarketAssumptions()
        self.last_simulation_time = None
        self.last_simulation_results = None
        
        logger.info("Monte Carlo engine initialized")
    
    def _validate_simulation_inputs(
        self, 
        portfolio_allocation: PortfolioAllocation, 
        parameters: SimulationParameters
    ) -> None:
        """Validate simulation inputs"""
        errors = []
        
        # Validate parameters
        if parameters.n_simulations <= 0:
            errors.append("Number of simulations must be positive")
        if parameters.n_simulations > 100_000:
            sim_logger.log_warning(f"Large number of simulations ({parameters.n_simulations:,}) may impact performance")
        
        if parameters.years_to_retirement <= 0:
            errors.append("Years to retirement must be positive")
        if parameters.retirement_years <= 0:
            errors.append("Retirement years must be positive")
        
        if parameters.initial_portfolio_value < 0:
            errors.append("Initial portfolio value cannot be negative")
        if parameters.annual_contribution < 0:
            errors.append("Annual contribution cannot be negative")
        
        if not 0.01 <= parameters.withdrawal_rate <= 0.20:
            errors.append("Withdrawal rate must be between 1% and 20%")
        
        if parameters.contribution_growth_rate < -0.10 or parameters.contribution_growth_rate > 0.20:
            errors.append("Contribution growth rate must be between -10% and 20%")
        
        # Validate portfolio allocation
        try:
            total_allocation = sum(portfolio_allocation.allocations.values())
            if not np.isclose(total_allocation, 1.0, rtol=1e-3):
                errors.append(f"Portfolio allocations must sum to 1.0, got {total_allocation:.4f}")
        except Exception as e:
            errors.append(f"Portfolio allocation validation error: {str(e)}")
        
        # Check for reasonable allocation ranges
        for asset, weight in portfolio_allocation.allocations.items():
            if weight < 0:
                errors.append(f"Negative allocation not allowed for {asset}: {weight:.1%}")
            if weight > 0.80:
                sim_logger.log_warning(f"High allocation to single asset {asset}: {weight:.1%}")
        
        if errors:
            raise ValidationError(f"Input validation failed: {'; '.join(errors)}")
    
    @performance_monitor(sim_logger)
    @error_handler(sim_logger, raise_on_error=True)
    def run_simulation(
        self, 
        portfolio_allocation: PortfolioAllocation,
        parameters: SimulationParameters
    ) -> Dict:
        """
        Run complete Monte Carlo simulation for retirement planning
        
        Args:
            portfolio_allocation: Target portfolio allocation
            parameters: Simulation parameters
            
        Returns:
            Dictionary containing simulation results and statistics
        """
        try:
            # Validate inputs
            self._validate_simulation_inputs(portfolio_allocation, parameters)
            
            # Log simulation configuration
            sim_config = {
                "n_simulations": parameters.n_simulations,
                "years_to_retirement": parameters.years_to_retirement,
                "retirement_years": parameters.retirement_years,
                "initial_value": parameters.initial_portfolio_value,
                "annual_contribution": parameters.annual_contribution,
                "withdrawal_rate": parameters.withdrawal_rate
            }
            log_simulation_config(sim_config)
            log_portfolio_allocation(portfolio_allocation.allocations)
            
            sim_logger.log_simulation_start(sim_config)
            
            # Set random seed for reproducibility
            if parameters.random_seed is not None:
                np.random.seed(parameters.random_seed)
                logger.debug(f"Random seed set to: {parameters.random_seed}")
            
            # Log memory usage at start
            log_memory_usage(sim_logger, "Simulation start")
            
            # Prepare market data
            with sim_logger.performance_timer("market_data_preparation"):
                market_data = self._prepare_market_data(portfolio_allocation)
            
            # Generate contribution schedule
            with sim_logger.performance_timer("contribution_schedule_generation"):
                contribution_schedule = self._generate_contribution_schedule(parameters)
            
            # Simulate accumulation phase
            with sim_logger.performance_timer("accumulation_phase_simulation"):
                accumulation_paths = self._simulate_accumulation_phase(
                    market_data, parameters, contribution_schedule
                )
            
            # Log memory usage after accumulation
            log_memory_usage(sim_logger, "After accumulation phase")
            
            # Simulate retirement phase
            with sim_logger.performance_timer("retirement_phase_simulation"):
                retirement_results = self._simulate_retirement_phase(
                    accumulation_paths, parameters
                )
            
            # Calculate performance statistics
            with sim_logger.performance_timer("results_calculation"):
                results = self._calculate_results(
                    accumulation_paths, retirement_results, parameters
                )
            
            self.last_simulation_time = time.time() - sim_logger.performance_metrics.get('simulation_start_time', time.time())
            self.last_simulation_results = results
            
            # Log success
            results_summary = {
                'success_probability': results.get('success_probability', 0),
                'median_balance': results.get('retirement_balance_stats', {}).get('median', 0)
            }
            sim_logger.log_simulation_end(True, results_summary)
            
            return results
            
        except Exception as e:
            sim_logger.log_simulation_end(False)
            raise CalculationError(f"Simulation failed: {str(e)}") from e
    
    def _prepare_market_data(self, portfolio_allocation: PortfolioAllocation) -> Dict:
        """Prepare market data for simulation"""
        
        # Get covariance matrix and asset names
        covariance_matrix, asset_names = self.market_assumptions.get_covariance_matrix()
        
        # Extract expected returns for allocated assets
        allocated_assets = list(portfolio_allocation.allocations.keys())
        
        # Validate all allocated assets exist in market assumptions
        missing_assets = set(allocated_assets) - set(asset_names)
        if missing_assets:
            raise ValueError(f"Unknown asset classes in portfolio: {missing_assets}")
        
        # Create asset index mapping
        asset_indices = {asset: i for i, asset in enumerate(asset_names)}
        portfolio_indices = [asset_indices[asset] for asset in allocated_assets]
        
        # Extract relevant market data
        expected_returns = np.array([
            self.market_assumptions.asset_classes[asset].expected_return 
            for asset in allocated_assets
        ])
        
        # Extract relevant covariance matrix
        relevant_covariance = covariance_matrix[np.ix_(portfolio_indices, portfolio_indices)]
        
        # Portfolio weights
        portfolio_weights = np.array([
            portfolio_allocation.allocations[asset] for asset in allocated_assets
        ])
        
        return {
            "expected_returns": expected_returns,
            "covariance_matrix": relevant_covariance,
            "portfolio_weights": portfolio_weights,
            "asset_names": allocated_assets
        }
    
    def _generate_contribution_schedule(self, parameters: SimulationParameters) -> np.ndarray:
        """Generate monthly contribution schedule with growth"""
        
        n_contribution_months = parameters.years_to_retirement * 12
        monthly_contribution = parameters.annual_contribution / 12.0
        growth_rate = parameters.contribution_growth_rate
        
        # Calculate monthly growth rate
        monthly_growth = (1 + growth_rate) ** (1/12) - 1
        
        # Generate contribution schedule
        contributions = np.zeros(n_contribution_months)
        current_contribution = monthly_contribution
        
        for month in range(n_contribution_months):
            contributions[month] = current_contribution
            
            # Increase contribution annually
            if month > 0 and month % 12 == 0:
                current_contribution *= (1 + growth_rate)
        
        return contributions
    
    def _simulate_accumulation_phase(
        self, 
        market_data: Dict, 
        parameters: SimulationParameters,
        contribution_schedule: np.ndarray
    ) -> np.ndarray:
        """Simulate the accumulation (pre-retirement) phase"""
        
        # Run Numba-compiled simulation
        portfolio_paths = simulate_portfolio_paths_numba(
            expected_returns=market_data["expected_returns"],
            covariance_matrix=market_data["covariance_matrix"],
            portfolio_weights=market_data["portfolio_weights"],
            n_simulations=parameters.n_simulations,
            n_years=parameters.years_to_retirement,
            initial_value=parameters.initial_portfolio_value,
            monthly_contributions=contribution_schedule,
            rebalance_frequency=parameters.rebalancing_frequency
        )
        
        return portfolio_paths
    
    def _simulate_retirement_phase(
        self,
        accumulation_paths: np.ndarray,
        parameters: SimulationParameters
    ) -> Dict:
        """Simulate the retirement (withdrawal) phase"""
        
        retirement_start_month = parameters.years_to_retirement * 12
        n_total_months = (parameters.years_to_retirement + parameters.retirement_years) * 12
        
        # Extend accumulation paths for retirement period
        extended_paths = np.zeros((parameters.n_simulations, n_total_months))
        extended_paths[:, :retirement_start_month] = accumulation_paths
        
        # Simulate continued investment returns during retirement
        # (This is a simplified approach - in practice, we'd want to continue the full simulation)
        for month in range(retirement_start_month, n_total_months):
            # Apply average expected portfolio return
            avg_portfolio_return = np.sum(
                self._prepare_market_data(
                    PortfolioAllocation({asset: 1.0/len(self.market_assumptions.asset_classes) 
                                       for asset in list(self.market_assumptions.asset_classes.keys())[:3]})
                )["expected_returns"][:3] / 3.0
            ) / 12.0  # Monthly return
            
            extended_paths[:, month] = extended_paths[:, month-1] * (1.0 + avg_portfolio_return * 0.5)  # Conservative estimate
        
        # Generate inflation paths
        inflation_paths = self.market_assumptions.simulate_inflation_path(
            years=parameters.retirement_years,
            n_simulations=parameters.n_simulations
        )
        
        # Simulate withdrawals
        final_balances, withdrawal_amounts = simulate_retirement_withdrawals_numba(
            portfolio_paths=extended_paths,
            retirement_start_month=retirement_start_month,
            initial_withdrawal_rate=parameters.withdrawal_rate,
            inflation_paths=inflation_paths
        )
        
        return {
            "final_balances": final_balances,
            "withdrawal_amounts": withdrawal_amounts,
            "inflation_paths": inflation_paths,
            "extended_paths": extended_paths
        }
    
    def _calculate_results(
        self,
        accumulation_paths: np.ndarray,
        retirement_results: Dict,
        parameters: SimulationParameters
    ) -> Dict:
        """Calculate comprehensive simulation results"""
        
        # Retirement balance at start of retirement
        retirement_balances = accumulation_paths[:, -1]
        final_balances = retirement_results["final_balances"]
        
        # Success rate (portfolio survives retirement)
        success_rate = np.mean(final_balances > 0)
        
        # Balance statistics
        retirement_stats = {
            "median": float(np.median(retirement_balances)),
            "percentile_10": float(np.percentile(retirement_balances, 10)),
            "percentile_25": float(np.percentile(retirement_balances, 25)),
            "percentile_75": float(np.percentile(retirement_balances, 75)),
            "percentile_90": float(np.percentile(retirement_balances, 90)),
            "mean": float(np.mean(retirement_balances)),
            "std": float(np.std(retirement_balances))
        }
        
        final_stats = {
            "median": float(np.median(final_balances)),
            "percentile_10": float(np.percentile(final_balances, 10)),
            "percentile_25": float(np.percentile(final_balances, 25)),
            "percentile_75": float(np.percentile(final_balances, 75)),
            "percentile_90": float(np.percentile(final_balances, 90)),
            "mean": float(np.mean(final_balances)),
            "std": float(np.std(final_balances))
        }
        
        # Shortfall analysis
        failed_simulations = final_balances <= 0
        if np.any(failed_simulations):
            years_depleted = []
            for sim_idx in np.where(failed_simulations)[0]:
                # Find when balance first reaches zero
                sim_path = retirement_results["extended_paths"][sim_idx]
                retirement_start = parameters.years_to_retirement * 12
                retirement_path = sim_path[retirement_start:]
                
                depletion_month = np.where(retirement_path <= 0)[0]
                if len(depletion_month) > 0:
                    years_depleted.append(depletion_month[0] / 12.0)
                else:
                    years_depleted.append(parameters.retirement_years)
            
            shortfall_stats = {
                "probability": float(1 - success_rate),
                "median_depletion_years": float(np.median(years_depleted)) if years_depleted else 0,
                "mean_depletion_years": float(np.mean(years_depleted)) if years_depleted else 0
            }
        else:
            shortfall_stats = {
                "probability": 0.0,
                "median_depletion_years": float(parameters.retirement_years),
                "mean_depletion_years": float(parameters.retirement_years)
            }
        
        # Calculate annualized returns
        total_years = parameters.years_to_retirement
        annualized_returns = (retirement_balances / parameters.initial_portfolio_value) ** (1/total_years) - 1
        
        return {
            "simulation_metadata": {
                "n_simulations": parameters.n_simulations,
                "years_to_retirement": parameters.years_to_retirement,
                "retirement_years": parameters.retirement_years,
                "simulation_time_seconds": self.last_simulation_time,
                "timestamp": datetime.now().isoformat()
            },
            "success_probability": float(success_rate),
            "retirement_balance_stats": retirement_stats,
            "final_balance_stats": final_stats,
            "shortfall_analysis": shortfall_stats,
            "annualized_returns": {
                "median": float(np.median(annualized_returns)),
                "percentile_10": float(np.percentile(annualized_returns, 10)),
                "percentile_90": float(np.percentile(annualized_returns, 90)),
                "mean": float(np.mean(annualized_returns)),
                "std": float(np.std(annualized_returns))
            },
            "raw_results": {
                "retirement_balances": retirement_balances.tolist(),
                "final_balances": final_balances.tolist(),
                "sample_paths": accumulation_paths[:min(100, parameters.n_simulations), ::12].tolist()  # Monthly snapshots for first 100 sims
            }
        }
    
    def run_stress_test(
        self,
        portfolio_allocation: PortfolioAllocation,
        parameters: SimulationParameters,
        stress_scenarios: List[str] = ["bear", "crisis"]
    ) -> Dict:
        """
        Run stress tests under different market regimes
        
        Args:
            portfolio_allocation: Target portfolio allocation
            parameters: Simulation parameters
            stress_scenarios: List of stress scenarios to test
            
        Returns:
            Dictionary containing stress test results
        """
        original_assumptions = self.market_assumptions
        stress_results = {}
        
        # Baseline simulation
        baseline_results = self.run_simulation(portfolio_allocation, parameters)
        stress_results["baseline"] = baseline_results
        
        for scenario in stress_scenarios:
            logger.info(f"Running stress test: {scenario}")
            
            # Create stressed market assumptions
            stressed_assumptions = CapitalMarketAssumptions()
            stressed_assumptions.update_assumptions(scenario)
            
            # Temporarily update assumptions
            self.market_assumptions = stressed_assumptions
            
            # Run simulation under stress
            scenario_results = self.run_simulation(portfolio_allocation, parameters)
            stress_results[scenario] = scenario_results
            
            logger.info(f"Stress test {scenario} completed - Success rate: {scenario_results['success_probability']:.1%}")
        
        # Restore original assumptions
        self.market_assumptions = original_assumptions
        
        return stress_results
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for the simulation engine"""
        
        if self.last_simulation_time is None:
            return {"status": "No simulations run yet"}
        
        return {
            "last_simulation_time_seconds": self.last_simulation_time,
            "simulations_per_second": int(50_000 / self.last_simulation_time) if self.last_simulation_time > 0 else 0,
            "performance_target_met": self.last_simulation_time < 30.0,  # Target: < 30 seconds
            "numba_compilation_status": "enabled",
            "parallel_execution": "enabled"
        }