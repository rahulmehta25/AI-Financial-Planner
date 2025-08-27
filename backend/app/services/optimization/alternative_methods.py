"""
Alternative Portfolio Optimization Methods
Implements advanced and alternative optimization strategies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from scipy import stats, optimize, special
from scipy.stats import norm, t, multivariate_normal
from scipy.optimize import differential_evolution, basinhopping
import cvxpy as cp
from sklearn.covariance import LedoitWolf, MinCovDet, OAS
import warnings


@dataclass
class KellyResult:
    """Result from Kelly Criterion optimization"""
    full_kelly_weights: np.ndarray
    fractional_kelly_weights: np.ndarray
    kelly_fraction: float
    expected_growth_rate: float
    volatility: float
    max_drawdown_estimate: float
    

@dataclass
class EntropyResult:
    """Result from Maximum Entropy optimization"""
    weights: np.ndarray
    entropy: float
    expected_return: float
    volatility: float
    diversification_ratio: float


class KellyCriterion:
    """
    Kelly Criterion optimization for maximum growth rate
    """
    
    def __init__(self, kelly_fraction: float = 0.25):
        """
        Initialize Kelly optimizer
        
        Args:
            kelly_fraction: Fraction of full Kelly to use (for safety)
        """
        self.kelly_fraction = kelly_fraction
        
    def optimize(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Optional[Dict] = None
    ) -> KellyResult:
        """
        Optimize portfolio using Kelly Criterion
        
        The Kelly Criterion maximizes expected logarithmic wealth growth:
        f* = argmax E[log(1 + f'R)]
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix
            constraints: Optional constraints
            
        Returns:
            Kelly optimization result
        """
        n_assets = len(expected_returns)
        
        # Full Kelly solution (analytical for unconstrained case)
        # f* = Σ^(-1) * μ
        try:
            cov_inv = np.linalg.inv(covariance_matrix)
            full_kelly = cov_inv @ expected_returns
        except np.linalg.LinAlgError:
            # Use pseudo-inverse if singular
            cov_inv = np.linalg.pinv(covariance_matrix)
            full_kelly = cov_inv @ expected_returns
            
        # Normalize to sum to 1 (for fully invested constraint)
        full_kelly_normalized = full_kelly / np.sum(np.abs(full_kelly))
        
        # Apply Kelly fraction for safety
        fractional_kelly = self.kelly_fraction * full_kelly_normalized
        
        # If constraints provided, optimize with constraints
        if constraints:
            fractional_kelly = self._constrained_kelly(
                expected_returns,
                covariance_matrix,
                constraints
            )
            
        # Calculate expected growth rate
        growth_rate = self._calculate_growth_rate(
            fractional_kelly,
            expected_returns,
            covariance_matrix
        )
        
        # Calculate risk metrics
        portfolio_vol = np.sqrt(
            fractional_kelly @ covariance_matrix @ fractional_kelly
        )
        
        # Estimate maximum drawdown (approximation)
        max_dd_estimate = self._estimate_max_drawdown(
            fractional_kelly,
            expected_returns,
            covariance_matrix
        )
        
        return KellyResult(
            full_kelly_weights=full_kelly_normalized,
            fractional_kelly_weights=fractional_kelly,
            kelly_fraction=self.kelly_fraction,
            expected_growth_rate=growth_rate,
            volatility=portfolio_vol,
            max_drawdown_estimate=max_dd_estimate
        )
    
    def optimize_with_parameter_uncertainty(
        self,
        returns_samples: np.ndarray,
        num_bootstrap: int = 1000,
        confidence_level: float = 0.95
    ) -> KellyResult:
        """
        Kelly optimization with parameter uncertainty using bootstrap
        
        Args:
            returns_samples: Historical returns (T x N array)
            num_bootstrap: Number of bootstrap samples
            confidence_level: Confidence level for robust estimates
            
        Returns:
            Robust Kelly result
        """
        n_samples, n_assets = returns_samples.shape
        kelly_weights_samples = []
        
        for _ in range(num_bootstrap):
            # Bootstrap sample
            idx = np.random.choice(n_samples, n_samples, replace=True)
            bootstrap_returns = returns_samples[idx]
            
            # Calculate statistics
            mean_returns = np.mean(bootstrap_returns, axis=0)
            cov_matrix = np.cov(bootstrap_returns, rowvar=False)
            
            # Calculate Kelly weights
            try:
                cov_inv = np.linalg.inv(cov_matrix)
                kelly_weights = cov_inv @ mean_returns
                kelly_weights = kelly_weights / np.sum(np.abs(kelly_weights))
                kelly_weights_samples.append(kelly_weights)
            except:
                continue
                
        # Use robust estimate (e.g., median or trimmed mean)
        kelly_weights_samples = np.array(kelly_weights_samples)
        
        # Calculate confidence intervals
        lower_percentile = (1 - confidence_level) / 2
        upper_percentile = 1 - lower_percentile
        
        robust_kelly = np.median(kelly_weights_samples, axis=0)
        
        # Apply Kelly fraction
        fractional_kelly = self.kelly_fraction * robust_kelly
        
        # Calculate metrics using original data
        mean_returns = np.mean(returns_samples, axis=0)
        cov_matrix = np.cov(returns_samples, rowvar=False)
        
        growth_rate = self._calculate_growth_rate(
            fractional_kelly,
            mean_returns,
            cov_matrix
        )
        
        portfolio_vol = np.sqrt(
            fractional_kelly @ cov_matrix @ fractional_kelly
        )
        
        max_dd_estimate = self._estimate_max_drawdown(
            fractional_kelly,
            mean_returns,
            cov_matrix
        )
        
        return KellyResult(
            full_kelly_weights=robust_kelly,
            fractional_kelly_weights=fractional_kelly,
            kelly_fraction=self.kelly_fraction,
            expected_growth_rate=growth_rate,
            volatility=portfolio_vol,
            max_drawdown_estimate=max_dd_estimate
        )
    
    def _constrained_kelly(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Dict
    ) -> np.ndarray:
        """Kelly optimization with constraints"""
        n_assets = len(expected_returns)
        
        def negative_growth_rate(weights):
            """Negative growth rate for minimization"""
            portfolio_return = weights @ expected_returns
            portfolio_variance = weights @ covariance_matrix @ weights
            # Kelly growth rate approximation
            growth = portfolio_return - 0.5 * portfolio_variance
            return -self.kelly_fraction * growth
        
        # Constraints
        scipy_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        if 'max_position' in constraints:
            scipy_constraints.append({
                'type': 'ineq',
                'fun': lambda x: constraints['max_position'] - np.max(np.abs(x))
            })
            
        # Bounds
        if constraints.get('long_only', True):
            bounds = [(0, 1) for _ in range(n_assets)]
        else:
            max_leverage = constraints.get('max_leverage', 2.0)
            bounds = [(-max_leverage, max_leverage) for _ in range(n_assets)]
            
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = optimize.minimize(
            negative_growth_rate,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints,
            options={'maxiter': 1000}
        )
        
        return result.x
    
    def _calculate_growth_rate(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray
    ) -> float:
        """Calculate expected logarithmic growth rate"""
        portfolio_return = weights @ expected_returns
        portfolio_variance = weights @ covariance_matrix @ weights
        
        # Approximation: g ≈ μ - σ²/2
        growth_rate = portfolio_return - 0.5 * portfolio_variance
        
        return growth_rate
    
    def _estimate_max_drawdown(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        time_horizon: int = 252
    ) -> float:
        """
        Estimate maximum drawdown using probabilistic approach
        
        This is an approximation based on the expected maximum drawdown
        for a geometric Brownian motion process
        """
        portfolio_return = weights @ expected_returns
        portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
        
        # Approximate expected maximum drawdown
        # For GBM: E[MDD] ≈ 0.5 * σ * sqrt(T)
        expected_mdd = 0.5 * portfolio_vol * np.sqrt(time_horizon / 252)
        
        # Adjust for drift
        sharpe = portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
        if sharpe > 0:
            expected_mdd *= (1 - 0.2 * min(sharpe, 2))  # Reduce MDD for positive Sharpe
            
        return expected_mdd


class MaximumEntropy:
    """
    Maximum Entropy portfolio optimization
    Maximizes portfolio entropy (diversification) subject to constraints
    """
    
    def optimize(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        target_return: Optional[float] = None,
        target_risk: Optional[float] = None
    ) -> EntropyResult:
        """
        Maximum entropy optimization
        
        Maximizes: H(w) = -Σ w_i * log(w_i)
        
        Args:
            expected_returns: Expected returns
            covariance_matrix: Covariance matrix
            target_return: Target portfolio return
            target_risk: Target portfolio risk
            
        Returns:
            Maximum entropy portfolio
        """
        n_assets = len(expected_returns)
        
        # Use CVXPY with entropy maximization
        weights = cp.Variable(n_assets)
        
        # Entropy (use negative for maximization)
        # Note: cp.entr computes -x*log(x), so sum gives entropy
        entropy = cp.sum(cp.entr(weights))
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0.001  # Small positive value for log
        ]
        
        if target_return is not None:
            portfolio_return = expected_returns @ weights
            constraints.append(portfolio_return >= target_return)
            
        if target_risk is not None:
            portfolio_variance = cp.quad_form(weights, covariance_matrix)
            constraints.append(portfolio_variance <= target_risk ** 2)
            
        # Objective: maximize entropy
        objective = cp.Maximize(entropy)
        
        # Solve
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        optimal_weights = weights.value
        
        # Calculate metrics
        portfolio_return = optimal_weights @ expected_returns
        portfolio_vol = np.sqrt(optimal_weights @ covariance_matrix @ optimal_weights)
        
        # Diversification ratio
        weighted_vol = optimal_weights @ np.sqrt(np.diag(covariance_matrix))
        div_ratio = weighted_vol / portfolio_vol if portfolio_vol > 0 else 1
        
        # Calculate actual entropy
        actual_entropy = -np.sum(
            optimal_weights * np.log(optimal_weights + 1e-10)
        )
        
        return EntropyResult(
            weights=optimal_weights,
            entropy=actual_entropy,
            expected_return=portfolio_return,
            volatility=portfolio_vol,
            diversification_ratio=div_ratio
        )


class RobustOptimization:
    """
    Robust portfolio optimization with uncertainty sets
    """
    
    def __init__(self, uncertainty_method: str = 'ellipsoidal'):
        """
        Initialize robust optimizer
        
        Args:
            uncertainty_method: 'box', 'ellipsoidal', or 'polytopic'
        """
        self.uncertainty_method = uncertainty_method
        
    def worst_case_optimization(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        return_uncertainty: float = 0.1,
        covariance_uncertainty: float = 0.05
    ) -> Dict:
        """
        Worst-case robust optimization
        
        Args:
            expected_returns: Nominal expected returns
            covariance_matrix: Nominal covariance matrix
            return_uncertainty: Size of uncertainty set for returns
            covariance_uncertainty: Size of uncertainty set for covariance
            
        Returns:
            Robust optimal portfolio
        """
        n_assets = len(expected_returns)
        
        if self.uncertainty_method == 'box':
            return self._box_uncertainty_optimization(
                expected_returns,
                covariance_matrix,
                return_uncertainty,
                covariance_uncertainty
            )
        elif self.uncertainty_method == 'ellipsoidal':
            return self._ellipsoidal_uncertainty_optimization(
                expected_returns,
                covariance_matrix,
                return_uncertainty,
                covariance_uncertainty
            )
        else:
            raise ValueError(f"Unknown uncertainty method: {self.uncertainty_method}")
            
    def _box_uncertainty_optimization(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        return_uncertainty: float,
        covariance_uncertainty: float
    ) -> Dict:
        """Box uncertainty set optimization"""
        n_assets = len(expected_returns)
        
        # Decision variables
        weights = cp.Variable(n_assets)
        t = cp.Variable()  # Auxiliary variable for worst-case return
        
        # Worst-case returns (box uncertainty)
        return_lower = expected_returns - return_uncertainty * np.abs(expected_returns)
        return_upper = expected_returns + return_uncertainty * np.abs(expected_returns)
        
        # Worst-case covariance (scaled)
        worst_case_cov = covariance_matrix * (1 + covariance_uncertainty)
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0,
            return_lower @ weights >= t  # Worst-case return constraint
        ]
        
        # Objective: maximize worst-case Sharpe ratio approximation
        worst_case_risk = cp.quad_form(weights, worst_case_cov)
        
        # We want to maximize t/sqrt(risk), but this is non-convex
        # Instead, we can fix risk level and maximize return, or vice versa
        target_risk = 0.15  # Target 15% volatility
        constraints.append(worst_case_risk <= target_risk ** 2)
        
        objective = cp.Maximize(t)
        
        # Solve
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        return {
            'weights': weights.value,
            'worst_case_return': t.value,
            'worst_case_risk': np.sqrt(worst_case_risk.value),
            'method': 'box_uncertainty'
        }
    
    def _ellipsoidal_uncertainty_optimization(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        return_uncertainty: float,
        covariance_uncertainty: float
    ) -> Dict:
        """Ellipsoidal uncertainty set optimization"""
        n_assets = len(expected_returns)
        
        # Estimate uncertainty ellipsoid from data or use scaled identity
        return_cov_uncertainty = np.eye(n_assets) * (return_uncertainty ** 2)
        
        # Decision variables
        weights = cp.Variable(n_assets)
        
        # Robust return (with ellipsoidal uncertainty)
        # min μ'w - κ * sqrt(w' Σ_μ w)
        kappa = norm.ppf(0.95)  # 95% confidence
        robust_return = (
            expected_returns @ weights - 
            kappa * cp.sqrt(cp.quad_form(weights, return_cov_uncertainty))
        )
        
        # Robust risk (worst-case covariance)
        worst_case_cov = covariance_matrix * (1 + covariance_uncertainty)
        robust_risk = cp.quad_form(weights, worst_case_cov)
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0
        ]
        
        # Objective: maximize robust Sharpe ratio approximation
        # We use mean-variance utility with risk aversion
        risk_aversion = 3.0
        objective = cp.Maximize(
            robust_return - (risk_aversion / 2) * robust_risk
        )
        
        # Solve
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        return {
            'weights': weights.value,
            'robust_return': float(robust_return.value),
            'robust_risk': float(np.sqrt(robust_risk.value)),
            'method': 'ellipsoidal_uncertainty'
        }


class DistributionallyRobust:
    """
    Distributionally robust optimization using Wasserstein distance
    """
    
    def optimize_wasserstein(
        self,
        returns_data: np.ndarray,
        epsilon: float = 0.1,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Distributionally robust optimization with Wasserstein ball
        
        Args:
            returns_data: Historical returns (T x N)
            epsilon: Radius of Wasserstein ball
            confidence_level: Confidence level for CVaR
            
        Returns:
            Distributionally robust portfolio
        """
        n_samples, n_assets = returns_data.shape
        
        # Decision variables
        weights = cp.Variable(n_assets)
        lambda_var = cp.Variable(nonneg=True)  # Dual variable
        s = cp.Variable(n_samples)  # Auxiliary variables
        
        # Empirical distribution
        probs = np.ones(n_samples) / n_samples
        
        # Portfolio returns for each scenario
        portfolio_returns = returns_data @ weights
        
        # Wasserstein DRO formulation for CVaR
        # min_w sup_P∈B(P̂,ε) CVaR_α(w'R)
        
        alpha = 1 - confidence_level
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0,
            s >= -portfolio_returns - lambda_var,
            s >= 0
        ]
        
        # Objective (dual formulation)
        objective = cp.Minimize(
            lambda_var * epsilon + 
            (1 / n_samples) * cp.sum(s)
        )
        
        # Solve
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        optimal_weights = weights.value
        
        # Calculate metrics
        expected_return = np.mean(returns_data @ optimal_weights)
        portfolio_vol = np.std(returns_data @ optimal_weights) * np.sqrt(252)
        
        return {
            'weights': optimal_weights,
            'expected_return': expected_return,
            'volatility': portfolio_vol,
            'worst_case_cvar': problem.value,
            'method': 'wasserstein_dro'
        }


class StochasticProgramming:
    """
    Multi-stage stochastic programming for dynamic portfolios
    """
    
    def multi_stage_optimization(
        self,
        scenarios: Dict[int, np.ndarray],
        probabilities: Dict[int, float],
        stages: int = 3,
        rebalance_cost: float = 0.001
    ) -> Dict:
        """
        Multi-stage stochastic portfolio optimization
        
        Args:
            scenarios: Dictionary of stage -> scenario returns
            probabilities: Scenario probabilities
            stages: Number of stages
            rebalance_cost: Transaction cost for rebalancing
            
        Returns:
            Optimal policy for each stage
        """
        n_assets = scenarios[0].shape[1]
        n_scenarios = len(probabilities)
        
        # Decision variables for each stage and scenario
        weights = {}
        trades = {}
        
        for t in range(stages):
            weights[t] = cp.Variable((n_scenarios, n_assets))
            if t > 0:
                trades[t] = cp.Variable((n_scenarios, n_assets))
                
        # Objective: maximize expected terminal wealth minus costs
        objective_value = 0
        
        for s in range(n_scenarios):
            terminal_wealth = 1.0
            total_cost = 0
            
            for t in range(stages):
                if t == 0:
                    # Initial allocation
                    terminal_wealth *= (1 + scenarios[t][s] @ weights[t][s])
                else:
                    # Rebalancing
                    terminal_wealth *= (1 + scenarios[t][s] @ weights[t][s])
                    total_cost += rebalance_cost * cp.sum(cp.abs(trades[t][s]))
                    
            objective_value += probabilities[s] * (terminal_wealth - total_cost)
            
        objective = cp.Maximize(objective_value)
        
        # Constraints
        constraints = []
        
        for t in range(stages):
            for s in range(n_scenarios):
                # Budget constraint
                constraints.append(cp.sum(weights[t][s]) == 1)
                constraints.append(weights[t][s] >= 0)
                
                if t > 0:
                    # Non-anticipativity (decisions depend only on observed history)
                    # Simplified version - would be more complex in practice
                    constraints.append(
                        weights[t][s] == weights[t-1][s] + trades[t][s]
                    )
                    
        # Solve
        problem = cp.Problem(objective, constraints)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            raise ValueError(f"Optimization failed: {problem.status}")
            
        # Extract optimal policies
        optimal_policies = {}
        for t in range(stages):
            optimal_policies[t] = weights[t].value
            
        return {
            'policies': optimal_policies,
            'expected_wealth': objective_value.value,
            'method': 'multi_stage_stochastic'
        }


class CovarianceEstimators:
    """
    Advanced covariance estimation methods for portfolio optimization
    """
    
    @staticmethod
    def ledoit_wolf_shrinkage(returns: np.ndarray) -> np.ndarray:
        """
        Ledoit-Wolf shrinkage estimator
        
        Shrinks sample covariance towards structured target
        """
        lw = LedoitWolf()
        cov_shrunk, _ = lw.fit(returns).covariance_, lw.shrinkage_
        return cov_shrunk
    
    @staticmethod
    def minimum_covariance_determinant(
        returns: np.ndarray,
        support_fraction: float = 0.75
    ) -> np.ndarray:
        """
        Robust covariance estimation using MCD
        
        Resistant to outliers
        """
        mcd = MinCovDet(support_fraction=support_fraction)
        mcd.fit(returns)
        return mcd.covariance_
    
    @staticmethod
    def oracle_approximating_shrinkage(returns: np.ndarray) -> np.ndarray:
        """
        Oracle Approximating Shrinkage estimator
        """
        oas = OAS()
        cov_oas, _ = oas.fit(returns).covariance_, oas.shrinkage_
        return cov_oas
    
    @staticmethod
    def gerber_statistic_covariance(
        returns: np.ndarray,
        threshold: float = 0.5
    ) -> np.ndarray:
        """
        Gerber statistic for robust correlation estimation
        
        Uses co-movements beyond threshold to estimate correlation
        """
        n_samples, n_assets = returns.shape
        
        # Standardize returns
        returns_std = (returns - np.mean(returns, axis=0)) / np.std(returns, axis=0)
        
        # Calculate Gerber correlation matrix
        gerber_corr = np.zeros((n_assets, n_assets))
        
        for i in range(n_assets):
            for j in range(n_assets):
                # Count co-movements beyond threshold
                co_movements = np.sum(
                    (np.abs(returns_std[:, i]) > threshold) & 
                    (np.abs(returns_std[:, j]) > threshold) &
                    (np.sign(returns_std[:, i]) == np.sign(returns_std[:, j]))
                )
                
                total_movements = np.sum(
                    (np.abs(returns_std[:, i]) > threshold) | 
                    (np.abs(returns_std[:, j]) > threshold)
                )
                
                if total_movements > 0:
                    gerber_corr[i, j] = (2 * co_movements / total_movements) - 1
                else:
                    gerber_corr[i, j] = 0 if i != j else 1
                    
        # Convert correlation to covariance
        std_devs = np.std(returns, axis=0)
        gerber_cov = np.outer(std_devs, std_devs) * gerber_corr
        
        return gerber_cov


class MetaHeuristics:
    """
    Meta-heuristic optimization methods for complex portfolio problems
    """
    
    def genetic_algorithm_optimization(
        self,
        fitness_function: Callable,
        n_assets: int,
        population_size: int = 100,
        generations: int = 500,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7
    ) -> Dict:
        """
        Genetic algorithm for portfolio optimization
        
        Args:
            fitness_function: Function to evaluate portfolio fitness
            n_assets: Number of assets
            population_size: Size of population
            generations: Number of generations
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            
        Returns:
            Best portfolio found
        """
        # Initialize population
        population = np.random.dirichlet(
            np.ones(n_assets), 
            size=population_size
        )
        
        best_individual = None
        best_fitness = -np.inf
        
        for gen in range(generations):
            # Evaluate fitness
            fitness = np.array([fitness_function(ind) for ind in population])
            
            # Track best
            gen_best_idx = np.argmax(fitness)
            if fitness[gen_best_idx] > best_fitness:
                best_fitness = fitness[gen_best_idx]
                best_individual = population[gen_best_idx].copy()
                
            # Selection (tournament)
            new_population = []
            for _ in range(population_size):
                tournament = np.random.choice(
                    population_size, 
                    size=5, 
                    replace=False
                )
                winner_idx = tournament[np.argmax(fitness[tournament])]
                new_population.append(population[winner_idx])
                
            population = np.array(new_population)
            
            # Crossover
            for i in range(0, population_size - 1, 2):
                if np.random.rand() < crossover_rate:
                    # Uniform crossover
                    mask = np.random.rand(n_assets) < 0.5
                    child1 = population[i].copy()
                    child2 = population[i + 1].copy()
                    
                    child1[mask] = population[i + 1][mask]
                    child2[mask] = population[i][mask]
                    
                    # Renormalize
                    child1 /= child1.sum()
                    child2 /= child2.sum()
                    
                    population[i] = child1
                    population[i + 1] = child2
                    
            # Mutation
            for i in range(population_size):
                if np.random.rand() < mutation_rate:
                    # Add noise and renormalize
                    noise = np.random.randn(n_assets) * 0.01
                    population[i] += noise
                    population[i] = np.maximum(population[i], 0)
                    population[i] /= population[i].sum()
                    
        return {
            'weights': best_individual,
            'fitness': best_fitness,
            'method': 'genetic_algorithm'
        }
    
    def particle_swarm_optimization(
        self,
        objective_function: Callable,
        n_assets: int,
        n_particles: int = 50,
        iterations: int = 200,
        w: float = 0.7,  # Inertia weight
        c1: float = 1.5,  # Cognitive parameter
        c2: float = 1.5   # Social parameter
    ) -> Dict:
        """
        Particle swarm optimization for portfolio optimization
        
        Returns:
            Best portfolio found
        """
        # Initialize particles
        positions = np.random.dirichlet(np.ones(n_assets), size=n_particles)
        velocities = np.random.randn(n_particles, n_assets) * 0.1
        
        # Personal best
        personal_best_positions = positions.copy()
        personal_best_scores = np.array([
            objective_function(p) for p in positions
        ])
        
        # Global best
        global_best_idx = np.argmax(personal_best_scores)
        global_best_position = personal_best_positions[global_best_idx].copy()
        global_best_score = personal_best_scores[global_best_idx]
        
        for iteration in range(iterations):
            # Update velocities and positions
            for i in range(n_particles):
                # Random factors
                r1 = np.random.rand(n_assets)
                r2 = np.random.rand(n_assets)
                
                # Update velocity
                velocities[i] = (
                    w * velocities[i] +
                    c1 * r1 * (personal_best_positions[i] - positions[i]) +
                    c2 * r2 * (global_best_position - positions[i])
                )
                
                # Update position
                positions[i] += velocities[i]
                
                # Enforce constraints (simplex)
                positions[i] = np.maximum(positions[i], 0)
                positions[i] /= positions[i].sum()
                
                # Evaluate
                score = objective_function(positions[i])
                
                # Update personal best
                if score > personal_best_scores[i]:
                    personal_best_scores[i] = score
                    personal_best_positions[i] = positions[i].copy()
                    
                    # Update global best
                    if score > global_best_score:
                        global_best_score = score
                        global_best_position = positions[i].copy()
                        
            # Adaptive inertia weight
            w *= 0.99
            
        return {
            'weights': global_best_position,
            'objective_value': global_best_score,
            'method': 'particle_swarm'
        }