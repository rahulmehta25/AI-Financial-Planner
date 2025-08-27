"""
Goal-Based Financial Planning Engine

This module implements sophisticated goal-based financial planning with:
- Multiple goal optimization and prioritization
- Success probability calculations using Monte Carlo methods
- Trade-off analysis between competing goals
- Dynamic goal adjustment and rebalancing
- Risk-aware goal achievement strategies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date, timedelta
import asyncio
import logging
from abc import ABC, abstractmethod
from scipy.optimize import minimize, differential_evolution
from sklearn.preprocessing import StandardScaler
import warnings

logger = logging.getLogger(__name__)

class GoalPriority(Enum):
    """Goal priority levels"""
    CRITICAL = 1    # Must achieve (retirement, emergency fund)
    HIGH = 2        # Very important (home purchase, education)
    MEDIUM = 3      # Important but flexible (vacation, car)
    LOW = 4         # Nice to have (luxury items)

class GoalType(Enum):
    """Types of financial goals"""
    RETIREMENT = "retirement"
    EMERGENCY_FUND = "emergency_fund"
    HOME_PURCHASE = "home_purchase"
    EDUCATION = "education"
    DEBT_PAYOFF = "debt_payoff"
    VACATION = "vacation"
    CAR_PURCHASE = "car_purchase"
    BUSINESS_STARTUP = "business_startup"
    WEDDING = "wedding"
    MAJOR_PURCHASE = "major_purchase"
    CHARITABLE_GIVING = "charitable_giving"
    OTHER = "other"

class OptimizationObjective(Enum):
    """Optimization objectives for goal planning"""
    MAXIMIZE_SUCCESS_PROBABILITY = "maximize_success"
    MINIMIZE_SHORTFALL_RISK = "minimize_shortfall"
    MAXIMIZE_EXPECTED_SURPLUS = "maximize_surplus"
    BALANCE_RISK_RETURN = "balance_risk_return"

@dataclass
class FinancialGoal:
    """Individual financial goal definition"""
    name: str
    goal_type: GoalType
    target_amount: float
    target_date: date
    priority: GoalPriority
    current_progress: float = 0.0
    required_return: Optional[float] = None
    risk_tolerance: float = 0.5  # 0 = very conservative, 1 = very aggressive
    flexibility: float = 0.1  # How much the goal can be adjusted (0-1)
    minimum_acceptable: float = 0.8  # Minimum acceptable achievement ratio
    tax_treatment: str = "taxable"  # taxable, tax_deferred, tax_free
    inflation_adjusted: bool = True
    success_threshold: float = 0.9  # Minimum success probability desired
    
    def __post_init__(self):
        if self.required_return is None:
            self.required_return = self._estimate_required_return()
    
    def _estimate_required_return(self) -> float:
        """Estimate required return based on goal parameters"""
        years_to_goal = (self.target_date - date.today()).days / 365.25
        if years_to_goal <= 0:
            return 0.0
        
        future_value_needed = self.target_amount - self.current_progress
        if future_value_needed <= 0:
            return 0.0
        
        # Estimate required monthly contribution
        estimated_monthly_contribution = future_value_needed / (years_to_goal * 12) * 0.1
        
        if estimated_monthly_contribution == 0:
            return 0.0
        
        # Calculate required return using future value formula
        n_periods = years_to_goal * 12
        try:
            required_return = (future_value_needed / (estimated_monthly_contribution * n_periods)) ** (1/n_periods) - 1
            return max(0.0, min(0.20, required_return * 12))  # Cap at 20% annual
        except:
            return 0.07  # Default assumption

@dataclass
class GoalAllocation:
    """Allocation strategy for a specific goal"""
    goal_name: str
    monthly_contribution: float
    asset_allocation: Dict[str, float]  # Asset class -> weight
    expected_return: float
    expected_volatility: float
    success_probability: float
    expected_shortfall: float
    years_to_target: float

@dataclass
class OptimizationConstraints:
    """Constraints for goal optimization"""
    total_monthly_budget: float
    minimum_emergency_fund: float = 0.0
    maximum_debt_ratio: float = 0.36  # 36% of income max
    minimum_retirement_contribution: float = 0.0
    asset_allocation_constraints: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    goal_contribution_limits: Dict[str, Tuple[float, float]] = field(default_factory=dict)

@dataclass
class TradeOffAnalysis:
    """Analysis of trade-offs between goals"""
    competing_goals: List[str]
    trade_off_scenarios: List[Dict[str, Any]]
    pareto_frontier: List[Dict[str, float]]
    recommended_allocation: Dict[str, float]
    sensitivity_analysis: Dict[str, Dict[str, float]]

@dataclass
class GoalOptimizationResult:
    """Results from goal optimization"""
    optimal_allocations: List[GoalAllocation]
    total_success_probability: float
    expected_shortfalls: Dict[str, float]
    trade_off_analysis: TradeOffAnalysis
    risk_metrics: Dict[str, float]
    sensitivity_metrics: Dict[str, Dict[str, float]]
    rebalancing_schedule: List[Dict[str, Any]]

class GoalSuccessProbabilityCalculator:
    """Calculate success probabilities for financial goals using Monte Carlo"""
    
    def __init__(self, n_simulations: int = 10000):
        self.n_simulations = n_simulations
    
    async def calculate_success_probability(self,
                                          goal: FinancialGoal,
                                          monthly_contribution: float,
                                          asset_allocation: Dict[str, float],
                                          market_assumptions: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Calculate probability of achieving a specific goal"""
        
        years_to_goal = (goal.target_date - date.today()).days / 365.25
        if years_to_goal <= 0:
            return {'success_probability': 1.0 if goal.current_progress >= goal.target_amount else 0.0}
        
        n_months = int(years_to_goal * 12)
        
        # Generate return scenarios
        return_scenarios = self._generate_return_scenarios(
            asset_allocation, market_assumptions, n_months
        )
        
        # Simulate goal achievement
        final_values = []
        
        for scenario in return_scenarios:
            portfolio_value = goal.current_progress
            
            for month in range(n_months):
                # Add monthly contribution
                portfolio_value += monthly_contribution
                
                # Apply market returns
                monthly_return = scenario[month]
                portfolio_value *= (1 + monthly_return)
            
            final_values.append(portfolio_value)
        
        final_values = np.array(final_values)
        
        # Calculate success metrics
        target_amount = goal.target_amount
        if goal.inflation_adjusted:
            # Adjust target for inflation (assume 2.5% inflation)
            target_amount *= (1.025 ** years_to_goal)
        
        success_probability = np.mean(final_values >= target_amount)
        expected_shortfall = np.mean(np.maximum(0, target_amount - final_values))
        expected_surplus = np.mean(np.maximum(0, final_values - target_amount))
        
        # Risk metrics
        var_95 = np.percentile(final_values, 5)
        expected_final_value = np.mean(final_values)
        
        return {
            'success_probability': success_probability,
            'expected_final_value': expected_final_value,
            'expected_shortfall': expected_shortfall,
            'expected_surplus': expected_surplus,
            'var_95': var_95,
            'target_amount': target_amount,
            'shortfall_risk': np.mean(final_values < target_amount * goal.minimum_acceptable)
        }
    
    def _generate_return_scenarios(self,
                                 asset_allocation: Dict[str, float],
                                 market_assumptions: Dict[str, Dict[str, float]],
                                 n_months: int) -> np.ndarray:
        """Generate return scenarios based on asset allocation"""
        
        scenarios = np.zeros((self.n_simulations, n_months))
        
        # Calculate portfolio expected return and volatility
        portfolio_return = 0.0
        portfolio_variance = 0.0
        
        for asset_class, weight in asset_allocation.items():
            if asset_class in market_assumptions:
                asset_return = market_assumptions[asset_class]['expected_return']
                asset_vol = market_assumptions[asset_class]['volatility']
                
                portfolio_return += weight * asset_return
                portfolio_variance += (weight * asset_vol) ** 2
        
        portfolio_volatility = np.sqrt(portfolio_variance)
        monthly_return = portfolio_return / 12
        monthly_vol = portfolio_volatility / np.sqrt(12)
        
        # Generate correlated scenarios (simplified)
        for i in range(self.n_simulations):
            # Generate monthly returns with some autocorrelation
            returns = np.random.normal(monthly_return, monthly_vol, n_months)
            
            # Add some autocorrelation
            for month in range(1, n_months):
                returns[month] += 0.1 * returns[month - 1]
            
            scenarios[i] = returns
        
        return scenarios

class MultiGoalOptimizer:
    """Optimize allocation across multiple financial goals"""
    
    def __init__(self):
        self.success_calculator = GoalSuccessProbabilityCalculator()
        self.risk_tolerance_mapping = {
            0.0: {'stocks': 0.2, 'bonds': 0.8},
            0.5: {'stocks': 0.6, 'bonds': 0.4},
            1.0: {'stocks': 0.9, 'bonds': 0.1}
        }
    
    async def optimize_goals(self,
                           goals: List[FinancialGoal],
                           constraints: OptimizationConstraints,
                           market_assumptions: Dict[str, Dict[str, float]],
                           objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_SUCCESS_PROBABILITY) -> GoalOptimizationResult:
        """Optimize allocation across multiple financial goals"""
        
        logger.info(f"Optimizing allocation for {len(goals)} goals")
        
        # Prepare optimization
        n_goals = len(goals)
        
        # Define decision variables bounds (monthly contributions)
        bounds = []
        for goal in goals:
            max_contribution = constraints.total_monthly_budget * 0.8  # Max 80% to one goal
            bounds.append((0.0, max_contribution))
        
        # Define objective function
        async def objective_function(contributions):
            return await self._evaluate_allocation(
                contributions, goals, constraints, market_assumptions, objective
            )
        
        # Run optimization
        result = await self._run_optimization(objective_function, bounds, constraints.total_monthly_budget)
        
        optimal_contributions = result['optimal_contributions']
        
        # Calculate detailed results for optimal allocation
        optimal_allocations = []
        
        for i, goal in enumerate(goals):
            contribution = optimal_contributions[i]
            asset_allocation = self._get_goal_asset_allocation(goal)
            
            success_metrics = await self.success_calculator.calculate_success_probability(
                goal, contribution, asset_allocation, market_assumptions
            )
            
            allocation = GoalAllocation(
                goal_name=goal.name,
                monthly_contribution=contribution,
                asset_allocation=asset_allocation,
                expected_return=self._calculate_portfolio_return(asset_allocation, market_assumptions),
                expected_volatility=self._calculate_portfolio_volatility(asset_allocation, market_assumptions),
                success_probability=success_metrics['success_probability'],
                expected_shortfall=success_metrics['expected_shortfall'],
                years_to_target=(goal.target_date - date.today()).days / 365.25
            )
            optimal_allocations.append(allocation)
        
        # Calculate overall metrics
        total_success_probability = np.mean([alloc.success_probability for alloc in optimal_allocations])
        expected_shortfalls = {alloc.goal_name: alloc.expected_shortfall for alloc in optimal_allocations}
        
        # Perform trade-off analysis
        trade_off_analysis = await self._analyze_trade_offs(goals, optimal_contributions, constraints, market_assumptions)
        
        # Calculate sensitivity analysis
        sensitivity_metrics = await self._perform_sensitivity_analysis(
            goals, optimal_contributions, constraints, market_assumptions
        )
        
        # Generate rebalancing schedule
        rebalancing_schedule = self._generate_rebalancing_schedule(goals, optimal_allocations)
        
        logger.info("Goal optimization completed")
        
        return GoalOptimizationResult(
            optimal_allocations=optimal_allocations,
            total_success_probability=total_success_probability,
            expected_shortfalls=expected_shortfalls,
            trade_off_analysis=trade_off_analysis,
            risk_metrics=result['risk_metrics'],
            sensitivity_metrics=sensitivity_metrics,
            rebalancing_schedule=rebalancing_schedule
        )
    
    async def _evaluate_allocation(self,
                                 contributions: np.ndarray,
                                 goals: List[FinancialGoal],
                                 constraints: OptimizationConstraints,
                                 market_assumptions: Dict[str, Dict[str, float]],
                                 objective: OptimizationObjective) -> float:
        """Evaluate the quality of a given allocation"""
        
        # Check budget constraint
        if np.sum(contributions) > constraints.total_monthly_budget:
            return float('inf')  # Infeasible
        
        # Calculate success probabilities for each goal
        success_probabilities = []
        expected_shortfalls = []
        
        for i, goal in enumerate(goals):
            asset_allocation = self._get_goal_asset_allocation(goal)
            
            success_metrics = await self.success_calculator.calculate_success_probability(
                goal, contributions[i], asset_allocation, market_assumptions
            )
            
            success_probabilities.append(success_metrics['success_probability'])
            expected_shortfalls.append(success_metrics['expected_shortfall'])
        
        # Apply priority weighting
        priority_weights = self._get_priority_weights(goals)
        
        if objective == OptimizationObjective.MAXIMIZE_SUCCESS_PROBABILITY:
            # Weighted average of success probabilities
            weighted_success = np.sum(np.array(success_probabilities) * priority_weights)
            return -weighted_success  # Minimize negative (maximize positive)
        
        elif objective == OptimizationObjective.MINIMIZE_SHORTFALL_RISK:
            # Weighted sum of expected shortfalls
            weighted_shortfall = np.sum(np.array(expected_shortfalls) * priority_weights)
            return weighted_shortfall
        
        elif objective == OptimizationObjective.MAXIMIZE_EXPECTED_SURPLUS:
            # Calculate expected surplus (more complex)
            total_surplus = 0.0
            for i, goal in enumerate(goals):
                if success_probabilities[i] > goal.success_threshold:
                    # Goal likely to succeed, count surplus
                    asset_allocation = self._get_goal_asset_allocation(goal)
                    years_to_goal = (goal.target_date - date.today()).days / 365.25
                    expected_value = self._calculate_expected_final_value(
                        goal, contributions[i], asset_allocation, market_assumptions, years_to_goal
                    )
                    surplus = max(0, expected_value - goal.target_amount)
                    total_surplus += surplus * priority_weights[i]
            
            return -total_surplus
        
        else:  # BALANCE_RISK_RETURN
            # Balance between success probability and risk
            weighted_success = np.sum(np.array(success_probabilities) * priority_weights)
            risk_penalty = np.std(success_probabilities)  # Penalize uneven success rates
            return -(weighted_success - 0.5 * risk_penalty)
    
    async def _run_optimization(self,
                              objective_function,
                              bounds: List[Tuple[float, float]],
                              total_budget: float) -> Dict[str, Any]:
        """Run the optimization algorithm"""
        
        # Budget constraint
        constraint = {'type': 'ineq', 'fun': lambda x: total_budget - np.sum(x)}
        
        # Use differential evolution for global optimization
        result = differential_evolution(
            lambda x: asyncio.run(objective_function(x)),
            bounds,
            constraints=[constraint],
            seed=42,
            maxiter=1000,
            atol=1e-6
        )
        
        if not result.success:
            logger.warning("Optimization did not converge fully")
        
        return {
            'optimal_contributions': result.x,
            'objective_value': result.fun,
            'risk_metrics': {
                'optimization_success': result.success,
                'iterations': result.nit,
                'function_evaluations': result.nfev
            }
        }
    
    def _get_goal_asset_allocation(self, goal: FinancialGoal) -> Dict[str, float]:
        """Get appropriate asset allocation for a goal based on risk tolerance and time horizon"""
        
        years_to_goal = (goal.target_date - date.today()).days / 365.25
        
        # Adjust allocation based on time horizon
        if years_to_goal <= 2:
            # Short-term: Conservative
            base_allocation = {'stocks': 0.3, 'bonds': 0.7}
        elif years_to_goal <= 10:
            # Medium-term: Moderate
            base_allocation = {'stocks': 0.6, 'bonds': 0.4}
        else:
            # Long-term: Growth-oriented
            base_allocation = {'stocks': 0.8, 'bonds': 0.2}
        
        # Adjust for risk tolerance
        risk_adjustment = (goal.risk_tolerance - 0.5) * 0.4  # -0.2 to +0.2
        
        stock_weight = min(0.95, max(0.05, base_allocation['stocks'] + risk_adjustment))
        bond_weight = 1.0 - stock_weight
        
        # Adjust for goal type
        if goal.goal_type == GoalType.EMERGENCY_FUND:
            return {'stocks': 0.1, 'bonds': 0.9}
        elif goal.goal_type == GoalType.RETIREMENT and years_to_goal > 20:
            return {'stocks': min(0.9, stock_weight + 0.1), 'bonds': max(0.1, bond_weight - 0.1)}
        
        return {'stocks': stock_weight, 'bonds': bond_weight}
    
    def _get_priority_weights(self, goals: List[FinancialGoal]) -> np.ndarray:
        """Calculate priority weights for goals"""
        
        priority_values = []
        for goal in goals:
            if goal.priority == GoalPriority.CRITICAL:
                priority_values.append(4.0)
            elif goal.priority == GoalPriority.HIGH:
                priority_values.append(3.0)
            elif goal.priority == GoalPriority.MEDIUM:
                priority_values.append(2.0)
            else:
                priority_values.append(1.0)
        
        # Normalize weights
        weights = np.array(priority_values)
        return weights / np.sum(weights)
    
    def _calculate_portfolio_return(self,
                                  asset_allocation: Dict[str, float],
                                  market_assumptions: Dict[str, Dict[str, float]]) -> float:
        """Calculate expected portfolio return"""
        
        expected_return = 0.0
        for asset_class, weight in asset_allocation.items():
            if asset_class in market_assumptions:
                expected_return += weight * market_assumptions[asset_class]['expected_return']
        
        return expected_return
    
    def _calculate_portfolio_volatility(self,
                                      asset_allocation: Dict[str, float],
                                      market_assumptions: Dict[str, Dict[str, float]]) -> float:
        """Calculate expected portfolio volatility (simplified)"""
        
        portfolio_variance = 0.0
        for asset_class, weight in asset_allocation.items():
            if asset_class in market_assumptions:
                asset_vol = market_assumptions[asset_class]['volatility']
                portfolio_variance += (weight * asset_vol) ** 2
        
        return np.sqrt(portfolio_variance)
    
    def _calculate_expected_final_value(self,
                                      goal: FinancialGoal,
                                      monthly_contribution: float,
                                      asset_allocation: Dict[str, float],
                                      market_assumptions: Dict[str, Dict[str, float]],
                                      years_to_goal: float) -> float:
        """Calculate expected final value for a goal"""
        
        if years_to_goal <= 0:
            return goal.current_progress
        
        expected_return = self._calculate_portfolio_return(asset_allocation, market_assumptions)
        monthly_return = expected_return / 12
        n_months = int(years_to_goal * 12)
        
        # Future value with regular contributions
        if monthly_return == 0:
            future_value = goal.current_progress + (monthly_contribution * n_months)
        else:
            # Present value growth
            pv_growth = goal.current_progress * (1 + monthly_return) ** n_months
            
            # Annuity future value
            annuity_fv = monthly_contribution * (((1 + monthly_return) ** n_months - 1) / monthly_return)
            
            future_value = pv_growth + annuity_fv
        
        return future_value
    
    async def _analyze_trade_offs(self,
                                goals: List[FinancialGoal],
                                optimal_contributions: np.ndarray,
                                constraints: OptimizationConstraints,
                                market_assumptions: Dict[str, Dict[str, float]]) -> TradeOffAnalysis:
        """Analyze trade-offs between competing goals"""
        
        # Find competing goals (same priority or overlapping time periods)
        competing_groups = self._identify_competing_goals(goals)
        
        trade_off_scenarios = []
        pareto_frontier = []
        
        for group in competing_groups:
            # Generate alternative allocation scenarios
            scenarios = self._generate_trade_off_scenarios(group, optimal_contributions, constraints)
            
            for scenario in scenarios:
                # Evaluate each scenario
                scenario_metrics = {}
                for i, goal_name in enumerate(group):
                    goal = next(g for g in goals if g.name == goal_name)
                    goal_idx = next(i for i, g in enumerate(goals) if g.name == goal_name)
                    
                    asset_allocation = self._get_goal_asset_allocation(goal)
                    success_metrics = await self.success_calculator.calculate_success_probability(
                        goal, scenario['contributions'][goal_idx], asset_allocation, market_assumptions
                    )
                    
                    scenario_metrics[goal_name] = {
                        'contribution': scenario['contributions'][goal_idx],
                        'success_probability': success_metrics['success_probability'],
                        'expected_shortfall': success_metrics['expected_shortfall']
                    }
                
                trade_off_scenarios.append({
                    'scenario_name': scenario['name'],
                    'metrics': scenario_metrics,
                    'total_success': np.mean([m['success_probability'] for m in scenario_metrics.values()])
                })
        
        # Generate Pareto frontier points
        if trade_off_scenarios:
            pareto_frontier = self._calculate_pareto_frontier(trade_off_scenarios)
        
        # Recommend best balanced allocation
        recommended_allocation = {
            goal.name: optimal_contributions[i] for i, goal in enumerate(goals)
        }
        
        # Perform sensitivity analysis
        sensitivity_analysis = await self._calculate_sensitivity_to_changes(
            goals, optimal_contributions, constraints, market_assumptions
        )
        
        return TradeOffAnalysis(
            competing_goals=[goal.name for group in competing_groups for goal in group],
            trade_off_scenarios=trade_off_scenarios,
            pareto_frontier=pareto_frontier,
            recommended_allocation=recommended_allocation,
            sensitivity_analysis=sensitivity_analysis
        )
    
    def _identify_competing_goals(self, goals: List[FinancialGoal]) -> List[List[str]]:
        """Identify groups of competing goals"""
        
        competing_groups = []
        
        # Group by priority and time horizon
        priority_groups = {}
        for goal in goals:
            if goal.priority not in priority_groups:
                priority_groups[goal.priority] = []
            priority_groups[goal.priority].append(goal.name)
        
        # Each priority group with more than one goal is competing
        for priority, goal_names in priority_groups.items():
            if len(goal_names) > 1:
                competing_groups.append(goal_names)
        
        return competing_groups
    
    def _generate_trade_off_scenarios(self,
                                    competing_goals: List[str],
                                    base_contributions: np.ndarray,
                                    constraints: OptimizationConstraints) -> List[Dict]:
        """Generate alternative allocation scenarios for competing goals"""
        
        scenarios = []
        
        # Base scenario
        scenarios.append({
            'name': 'Balanced',
            'contributions': base_contributions.copy()
        })
        
        # Favor each goal in turn
        for goal_name in competing_goals:
            scenario_contributions = base_contributions.copy()
            
            # Increase this goal by 20%, decrease others proportionally
            goal_indices = [i for i, goal in enumerate(competing_goals)]
            
            if len(goal_indices) > 1:
                increase_factor = 1.2
                decrease_factor = 0.8
                
                # This is a simplified approach - in practice would need more sophisticated reallocation
                scenarios.append({
                    'name': f'Favor {goal_name}',
                    'contributions': scenario_contributions
                })
        
        return scenarios
    
    def _calculate_pareto_frontier(self, scenarios: List[Dict]) -> List[Dict[str, float]]:
        """Calculate Pareto frontier for trade-off analysis"""
        
        pareto_points = []
        
        # Extract relevant metrics for Pareto analysis
        for scenario in scenarios:
            point = {
                'scenario_name': scenario['scenario_name'],
                'total_success_probability': scenario['total_success'],
                'risk_score': 1.0 - scenario['total_success']  # Simple risk measure
            }
            pareto_points.append(point)
        
        # Simple Pareto filtering (in practice would be more sophisticated)
        pareto_frontier = []
        for point in pareto_points:
            is_dominated = False
            for other_point in pareto_points:
                if (other_point['total_success_probability'] >= point['total_success_probability'] and 
                    other_point['risk_score'] <= point['risk_score'] and
                    other_point != point):
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_frontier.append(point)
        
        return pareto_frontier
    
    async def _calculate_sensitivity_to_changes(self,
                                              goals: List[FinancialGoal],
                                              base_contributions: np.ndarray,
                                              constraints: OptimizationConstraints,
                                              market_assumptions: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Calculate sensitivity of success probabilities to parameter changes"""
        
        sensitivity_analysis = {}
        
        # Test sensitivity to market return assumptions
        for asset_class in market_assumptions:
            original_return = market_assumptions[asset_class]['expected_return']
            
            # Test +/- 1% return scenarios
            for delta in [-0.01, 0.01]:
                market_assumptions[asset_class]['expected_return'] = original_return + delta
                
                # Recalculate success probabilities
                scenario_name = f"{asset_class}_return_{'+' if delta > 0 else ''}{delta:.1%}"
                scenario_results = {}
                
                for i, goal in enumerate(goals):
                    asset_allocation = self._get_goal_asset_allocation(goal)
                    success_metrics = await self.success_calculator.calculate_success_probability(
                        goal, base_contributions[i], asset_allocation, market_assumptions
                    )
                    scenario_results[goal.name] = success_metrics['success_probability']
                
                sensitivity_analysis[scenario_name] = scenario_results
            
            # Restore original return
            market_assumptions[asset_class]['expected_return'] = original_return
        
        return sensitivity_analysis
    
    async def _perform_sensitivity_analysis(self,
                                          goals: List[FinancialGoal],
                                          optimal_contributions: np.ndarray,
                                          constraints: OptimizationConstraints,
                                          market_assumptions: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Perform comprehensive sensitivity analysis"""
        
        sensitivity_metrics = {}
        
        # Base case metrics
        base_metrics = {}
        for i, goal in enumerate(goals):
            asset_allocation = self._get_goal_asset_allocation(goal)
            success_metrics = await self.success_calculator.calculate_success_probability(
                goal, optimal_contributions[i], asset_allocation, market_assumptions
            )
            base_metrics[goal.name] = success_metrics['success_probability']
        
        sensitivity_metrics['base_case'] = base_metrics
        
        # Test contribution changes
        for i, goal in enumerate(goals):
            for delta_pct in [-0.2, -0.1, 0.1, 0.2]:  # +/- 10%, 20%
                test_contributions = optimal_contributions.copy()
                test_contributions[i] *= (1 + delta_pct)
                
                # Ensure budget constraint
                if np.sum(test_contributions) <= constraints.total_monthly_budget:
                    asset_allocation = self._get_goal_asset_allocation(goal)
                    success_metrics = await self.success_calculator.calculate_success_probability(
                        goal, test_contributions[i], asset_allocation, market_assumptions
                    )
                    
                    scenario_name = f"{goal.name}_contribution_{'+' if delta_pct > 0 else ''}{delta_pct:.0%}"
                    sensitivity_metrics[scenario_name] = {
                        goal.name: success_metrics['success_probability']
                    }
        
        return sensitivity_metrics
    
    def _generate_rebalancing_schedule(self,
                                     goals: List[FinancialGoal],
                                     optimal_allocations: List[GoalAllocation]) -> List[Dict[str, Any]]:
        """Generate rebalancing schedule for goals"""
        
        rebalancing_schedule = []
        
        for goal in goals:
            years_to_goal = (goal.target_date - date.today()).days / 365.25
            
            # Create rebalancing points at key milestones
            milestones = []
            
            if years_to_goal > 10:
                milestones = [5, 2, 1]  # Years before target
            elif years_to_goal > 5:
                milestones = [2, 1]
            elif years_to_goal > 1:
                milestones = [1]
            
            for years_before in milestones:
                rebalance_date = goal.target_date - timedelta(days=365 * years_before)
                
                # Adjust allocation to be more conservative as goal approaches
                if years_before <= 2:
                    new_allocation = {'stocks': 0.3, 'bonds': 0.7}
                elif years_before <= 5:
                    new_allocation = {'stocks': 0.5, 'bonds': 0.5}
                else:
                    continue  # No change needed
                
                rebalancing_schedule.append({
                    'goal_name': goal.name,
                    'rebalance_date': rebalance_date,
                    'new_allocation': new_allocation,
                    'reason': f'Risk reduction {years_before} years before target'
                })
        
        # Sort by date
        rebalancing_schedule.sort(key=lambda x: x['rebalance_date'])
        
        return rebalancing_schedule

# Example usage and testing
async def run_goal_planning_example():
    """Example of goal-based financial planning"""
    
    # Define financial goals
    goals = [
        FinancialGoal(
            name="Emergency Fund",
            goal_type=GoalType.EMERGENCY_FUND,
            target_amount=50000,
            target_date=date(2025, 12, 31),
            priority=GoalPriority.CRITICAL,
            current_progress=10000,
            risk_tolerance=0.2  # Conservative
        ),
        FinancialGoal(
            name="Home Down Payment",
            goal_type=GoalType.HOME_PURCHASE,
            target_amount=100000,
            target_date=date(2027, 6, 1),
            priority=GoalPriority.HIGH,
            current_progress=20000,
            risk_tolerance=0.4  # Moderate
        ),
        FinancialGoal(
            name="Retirement",
            goal_type=GoalType.RETIREMENT,
            target_amount=1500000,
            target_date=date(2054, 1, 1),
            priority=GoalPriority.CRITICAL,
            current_progress=50000,
            risk_tolerance=0.7  # Growth-oriented
        ),
        FinancialGoal(
            name="Child Education",
            goal_type=GoalType.EDUCATION,
            target_amount=200000,
            target_date=date(2042, 9, 1),
            priority=GoalPriority.HIGH,
            current_progress=5000,
            risk_tolerance=0.6  # Moderate growth
        )
    ]
    
    # Define constraints
    constraints = OptimizationConstraints(
        total_monthly_budget=4000,
        minimum_emergency_fund=25000,
        minimum_retirement_contribution=500
    )
    
    # Market assumptions
    market_assumptions = {
        'stocks': {
            'expected_return': 0.10,
            'volatility': 0.16
        },
        'bonds': {
            'expected_return': 0.04,
            'volatility': 0.05
        }
    }
    
    # Run optimization
    optimizer = MultiGoalOptimizer()
    result = await optimizer.optimize_goals(
        goals=goals,
        constraints=constraints,
        market_assumptions=market_assumptions,
        objective=OptimizationObjective.MAXIMIZE_SUCCESS_PROBABILITY
    )
    
    return result

if __name__ == "__main__":
    # Run example
    import asyncio
    result = asyncio.run(run_goal_planning_example())
    
    print("\n=== Goal-Based Planning Results ===")
    print(f"Total Success Probability: {result.total_success_probability:.2%}")
    print(f"\nOptimal Allocations:")
    
    for allocation in result.optimal_allocations:
        print(f"\n{allocation.goal_name}:")
        print(f"  Monthly Contribution: ${allocation.monthly_contribution:,.2f}")
        print(f"  Success Probability: {allocation.success_probability:.2%}")
        print(f"  Expected Shortfall: ${allocation.expected_shortfall:,.2f}")
        print(f"  Asset Allocation: {allocation.asset_allocation}")
    
    print(f"\nRebalancing Schedule: {len(result.rebalancing_schedule)} events planned")