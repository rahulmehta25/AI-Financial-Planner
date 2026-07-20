"""
Results Calculator for Monte Carlo Simulations

Advanced statistical analysis and probability calculations for retirement planning
simulation results with comprehensive outcome metrics.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)


@dataclass
class OutcomeMetrics:
    """Comprehensive outcome metrics from simulation results"""
    success_probability: float
    median_balance: float
    percentile_10_balance: float
    percentile_90_balance: float
    expected_shortfall: float
    median_years_funded: float
    worst_case_scenario: float
    best_case_scenario: float
    confidence_interval_95: Tuple[float, float]


@dataclass
class RiskMetrics:
    """Risk analysis metrics"""
    value_at_risk_5: float      # 5% VaR
    conditional_var_5: float    # Expected shortfall beyond 5% VaR
    maximum_drawdown: float
    volatility: float
    downside_deviation: float
    sortino_ratio: float


@dataclass
class ReturnMetrics:
    """Return analysis metrics"""
    annualized_return: float
    real_return: float
    sharpe_ratio: float
    calmar_ratio: float
    information_ratio: float
    tracking_error: float


class ResultsCalculator:
    """
    Advanced calculator for Monte Carlo simulation results
    
    Provides comprehensive analysis including:
    - Probability of success/failure
    - Percentile-based outcome analysis
    - Risk metrics (VaR, CVaR, drawdowns)
    - Return metrics (Sharpe, Sortino, Calmar ratios)
    - Scenario analysis and stress testing
    """
    
    def __init__(self):
        """Initialize results calculator"""
        logger.info("Results calculator initialized")
    
    def calculate_comprehensive_results(
        self, 
        simulation_results: Dict,
        target_value: Optional[float] = None,
        confidence_levels: List[float] = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive results from Monte Carlo simulation
        
        Args:
            simulation_results: Raw simulation results from MonteCarloEngine
            target_value: Target portfolio value for success calculation
            confidence_levels: Confidence levels for percentile analysis
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            # Extract key data from simulation results
            retirement_balances = np.array(simulation_results["raw_results"]["retirement_balances"])
            final_balances = np.array(simulation_results["raw_results"]["final_balances"])
            
            # Calculate outcome metrics
            outcome_metrics = self._calculate_outcome_metrics(
                retirement_balances, final_balances, target_value, confidence_levels
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                retirement_balances, final_balances, simulation_results
            )
            
            # Calculate return metrics
            return_metrics = self._calculate_return_metrics(
                retirement_balances, simulation_results
            )
            
            # Calculate withdrawal sustainability
            withdrawal_analysis = self._calculate_withdrawal_analysis(
                final_balances, simulation_results
            )
            
            # Calculate scenario analysis
            scenario_analysis = self._calculate_scenario_analysis(
                retirement_balances, final_balances
            )
            
            # Calculate goal achievement probabilities
            goal_probabilities = self._calculate_goal_probabilities(
                retirement_balances, final_balances
            )
            
            return {
                "outcome_metrics": outcome_metrics,
                "risk_metrics": risk_metrics,
                "return_metrics": return_metrics,
                "withdrawal_analysis": withdrawal_analysis,
                "scenario_analysis": scenario_analysis,
                "goal_probabilities": goal_probabilities,
                "statistical_tests": self._run_statistical_tests(retirement_balances),
                "metadata": {
                    "calculation_timestamp": datetime.now().isoformat(),
                    "n_simulations": len(retirement_balances),
                    "confidence_levels": confidence_levels
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive results: {str(e)}")
            raise
    
    def _calculate_outcome_metrics(
        self,
        retirement_balances: np.ndarray,
        final_balances: np.ndarray,
        target_value: Optional[float],
        confidence_levels: List[float]
    ) -> Dict[str, Any]:
        """Calculate outcome-based metrics"""
        
        # Basic success probability (portfolio survives retirement)
        success_probability = np.mean(final_balances > 0)
        
        # Percentile calculations
        percentiles = {}
        for level in confidence_levels:
            percentiles[f"percentile_{int(level*100)}"] = float(np.percentile(retirement_balances, level*100))
        
        # Target achievement probability
        target_achievement_prob = None
        if target_value is not None:
            target_achievement_prob = float(np.mean(retirement_balances >= target_value))
        
        # Expected shortfall (average shortfall when target is missed)
        if target_value is not None:
            shortfall_scenarios = retirement_balances < target_value
            if np.any(shortfall_scenarios):
                expected_shortfall = float(np.mean(target_value - retirement_balances[shortfall_scenarios]))
            else:
                expected_shortfall = 0.0
        else:
            # Use median as target if not specified
            median_balance = np.median(retirement_balances)
            shortfall_scenarios = retirement_balances < median_balance
            expected_shortfall = float(np.mean(median_balance - retirement_balances[shortfall_scenarios])) if np.any(shortfall_scenarios) else 0.0
        
        # Years funded analysis (simplified - assumes 4% withdrawal rate)
        withdrawal_rate = 0.04
        years_funded = retirement_balances / (retirement_balances * withdrawal_rate)  # Simplified calculation
        years_funded = np.minimum(years_funded, 40)  # Cap at 40 years
        
        # Confidence intervals
        ci_95 = (
            float(np.percentile(retirement_balances, 2.5)),
            float(np.percentile(retirement_balances, 97.5))
        )
        
        return {
            "success_probability": float(success_probability),
            "target_achievement_probability": target_achievement_prob,
            "percentiles": percentiles,
            "expected_shortfall": expected_shortfall,
            "median_years_funded": float(np.median(years_funded)),
            "worst_case_scenario": float(np.min(retirement_balances)),
            "best_case_scenario": float(np.max(retirement_balances)),
            "confidence_interval_95": ci_95,
            "mean_balance": float(np.mean(retirement_balances)),
            "std_deviation": float(np.std(retirement_balances)),
            "coefficient_of_variation": float(np.std(retirement_balances) / np.mean(retirement_balances))
        }
    
    def _calculate_risk_metrics(
        self,
        retirement_balances: np.ndarray,
        final_balances: np.ndarray,
        simulation_results: Dict
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        
        # Value at Risk (VaR) calculations
        var_5 = float(np.percentile(retirement_balances, 5))
        var_1 = float(np.percentile(retirement_balances, 1))
        
        # Conditional Value at Risk (Expected Shortfall)
        cvar_5 = float(np.mean(retirement_balances[retirement_balances <= var_5]))
        
        # Volatility measures
        returns = np.log(retirement_balances / simulation_results["simulation_metadata"]["initial_portfolio_value"] if "initial_portfolio_value" in simulation_results["simulation_metadata"] else 100000)
        volatility = float(np.std(returns))
        
        # Downside deviation (volatility of negative returns)
        mean_return = np.mean(returns)
        downside_returns = returns[returns < mean_return]
        downside_deviation = float(np.std(downside_returns)) if len(downside_returns) > 0 else 0.0
        
        # Sortino ratio (return/downside deviation)
        sortino_ratio = float(mean_return / downside_deviation) if downside_deviation > 0 else 0.0
        
        # Maximum drawdown (simplified calculation)
        # This would ideally use path data, but we'll approximate using percentiles
        max_drawdown = float((np.percentile(retirement_balances, 90) - var_5) / np.percentile(retirement_balances, 90))
        
        # Skewness and kurtosis
        skewness = float(stats.skew(retirement_balances))
        kurtosis = float(stats.kurtosis(retirement_balances))
        
        return {
            "value_at_risk_5": var_5,
            "value_at_risk_1": var_1,
            "conditional_var_5": cvar_5,
            "volatility": volatility,
            "downside_deviation": downside_deviation,
            "sortino_ratio": sortino_ratio,
            "maximum_drawdown": max_drawdown,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "risk_adjusted_return": float(mean_return / volatility) if volatility > 0 else 0.0
        }
    
    def _calculate_return_metrics(
        self,
        retirement_balances: np.ndarray,
        simulation_results: Dict
    ) -> Dict[str, Any]:
        """Calculate return-based metrics"""
        
        # Extract parameters
        years_to_retirement = simulation_results["simulation_metadata"]["years_to_retirement"]
        initial_value = 100000  # Default if not available
        
        # Calculate annualized returns
        total_returns = retirement_balances / initial_value
        annualized_returns = total_returns ** (1/years_to_retirement) - 1
        
        # Basic return statistics
        mean_return = float(np.mean(annualized_returns))
        median_return = float(np.median(annualized_returns))
        std_return = float(np.std(annualized_returns))
        
        # Sharpe ratio (assuming risk-free rate of 3%)
        risk_free_rate = 0.03
        sharpe_ratio = float((mean_return - risk_free_rate) / std_return) if std_return > 0 else 0.0
        
        # Real returns (assuming 2.5% inflation)
        inflation_rate = 0.025
        real_return = float(mean_return - inflation_rate)
        
        # Return percentiles
        return_percentiles = {
            "percentile_10": float(np.percentile(annualized_returns, 10)),
            "percentile_25": float(np.percentile(annualized_returns, 25)),
            "percentile_75": float(np.percentile(annualized_returns, 75)),
            "percentile_90": float(np.percentile(annualized_returns, 90))
        }
        
        return {
            "mean_annualized_return": mean_return,
            "median_annualized_return": median_return,
            "real_return": real_return,
            "sharpe_ratio": sharpe_ratio,
            "return_volatility": std_return,
            "return_percentiles": return_percentiles,
            "positive_return_probability": float(np.mean(annualized_returns > 0)),
            "target_return_probability": float(np.mean(annualized_returns > 0.07))  # 7% target
        }
    
    def _calculate_withdrawal_analysis(
        self,
        final_balances: np.ndarray,
        simulation_results: Dict
    ) -> Dict[str, Any]:
        """Analyze withdrawal sustainability"""
        
        # Safe withdrawal rates analysis
        withdrawal_rates = [0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06]
        
        # Get retirement balances for withdrawal rate calculation
        retirement_balances = np.array(simulation_results["raw_results"]["retirement_balances"])
        
        withdrawal_success_rates = {}
        for rate in withdrawal_rates:
            # Simple approximation: portfolio lasts if balance > 25x annual withdrawal
            required_balance = (1/rate) * (retirement_balances * rate)
            success_rate = float(np.mean(final_balances > 0))  # Simplified
            withdrawal_success_rates[f"rate_{rate:.1%}"] = success_rate
        
        # Calculate optimal withdrawal rate (rate with 90% success probability)
        optimal_rate = 0.04  # Default
        for rate in sorted(withdrawal_rates, reverse=True):
            if withdrawal_success_rates[f"rate_{rate:.1%}"] >= 0.90:
                optimal_rate = rate
                break
        
        # Withdrawal amount distributions
        retirement_median = np.median(retirement_balances)
        withdrawal_distributions = {}
        for rate in withdrawal_rates:
            annual_withdrawal = retirement_median * rate
            withdrawal_distributions[f"rate_{rate:.1%}"] = {
                "annual_amount": float(annual_withdrawal),
                "monthly_amount": float(annual_withdrawal / 12)
            }
        
        return {
            "withdrawal_success_rates": withdrawal_success_rates,
            "optimal_withdrawal_rate": optimal_rate,
            "withdrawal_distributions": withdrawal_distributions,
            "sustainable_withdrawal_probability": float(np.mean(final_balances > retirement_balances * 0.5)),
            "depletion_risk": float(np.mean(final_balances <= 0))
        }
    
    def _calculate_scenario_analysis(
        self,
        retirement_balances: np.ndarray,
        final_balances: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate scenario-based analysis"""
        
        # Define scenarios based on percentiles
        scenarios = {
            "worst_case": np.percentile(retirement_balances, 5),
            "pessimistic": np.percentile(retirement_balances, 25),
            "median": np.percentile(retirement_balances, 50),
            "optimistic": np.percentile(retirement_balances, 75),
            "best_case": np.percentile(retirement_balances, 95)
        }
        
        # Calculate probabilities for different outcome ranges
        balance_ranges = {
            "below_500k": float(np.mean(retirement_balances < 500_000)),
            "500k_to_1m": float(np.mean((retirement_balances >= 500_000) & (retirement_balances < 1_000_000))),
            "1m_to_2m": float(np.mean((retirement_balances >= 1_000_000) & (retirement_balances < 2_000_000))),
            "2m_to_5m": float(np.mean((retirement_balances >= 2_000_000) & (retirement_balances < 5_000_000))),
            "above_5m": float(np.mean(retirement_balances >= 5_000_000))
        }
        
        # Tail risk analysis
        tail_risk = {
            "left_tail_5": float(np.percentile(retirement_balances, 5)),
            "left_tail_1": float(np.percentile(retirement_balances, 1)),
            "right_tail_95": float(np.percentile(retirement_balances, 95)),
            "right_tail_99": float(np.percentile(retirement_balances, 99)),
            "tail_ratio": float(np.percentile(retirement_balances, 95) / np.percentile(retirement_balances, 5))
        }
        
        return {
            "scenarios": {k: float(v) for k, v in scenarios.items()},
            "balance_ranges": balance_ranges,
            "tail_risk": tail_risk,
            "interquartile_range": float(np.percentile(retirement_balances, 75) - np.percentile(retirement_balances, 25)),
            "range_width": float(np.max(retirement_balances) - np.min(retirement_balances))
        }
    
    def _calculate_goal_probabilities(
        self,
        retirement_balances: np.ndarray,
        final_balances: np.ndarray
    ) -> Dict[str, float]:
        """Calculate probabilities of achieving various financial goals"""
        
        goals = {
            "basic_retirement": 500_000,
            "comfortable_retirement": 1_000_000,
            "luxury_retirement": 2_000_000,
            "legacy_planning": 5_000_000
        }
        
        goal_probabilities = {}
        for goal_name, goal_amount in goals.items():
            probability = float(np.mean(retirement_balances >= goal_amount))
            goal_probabilities[goal_name] = probability
        
        # Time to goal achievement (simplified)
        median_balance = np.median(retirement_balances)
        time_to_goals = {}
        for goal_name, goal_amount in goals.items():
            if median_balance >= goal_amount:
                time_to_goals[goal_name] = 0  # Already achieved
            else:
                # Assume 7% growth rate for estimation
                years_needed = np.log(goal_amount / median_balance) / np.log(1.07)
                time_to_goals[goal_name] = float(max(0, years_needed))
        
        return {
            "goal_achievement_probabilities": goal_probabilities,
            "estimated_years_to_goals": time_to_goals,
            "probability_millionaire": goal_probabilities["comfortable_retirement"],
            "probability_multi_millionaire": goal_probabilities["luxury_retirement"]
        }
    
    def _run_statistical_tests(self, retirement_balances: np.ndarray) -> Dict[str, Any]:
        """Run statistical tests on simulation results"""
        
        try:
            # Normality test
            shapiro_stat, shapiro_p = stats.shapiro(retirement_balances[:5000])  # Limit sample size
            
            # Log-normality test
            log_balances = np.log(retirement_balances[retirement_balances > 0])
            log_shapiro_stat, log_shapiro_p = stats.shapiro(log_balances[:5000])
            
            # Anderson-Darling test for normality
            anderson_result = stats.anderson(retirement_balances, dist='norm')
            
            # Jarque-Bera test
            jb_stat, jb_p = stats.jarque_bera(retirement_balances)
            
            return {
                "normality_tests": {
                    "shapiro_wilk": {"statistic": float(shapiro_stat), "p_value": float(shapiro_p)},
                    "log_normal_shapiro": {"statistic": float(log_shapiro_stat), "p_value": float(log_shapiro_p)},
                    "anderson_darling": {"statistic": float(anderson_result.statistic), "critical_values": anderson_result.critical_values.tolist()},
                    "jarque_bera": {"statistic": float(jb_stat), "p_value": float(jb_p)}
                },
                "distribution_fit": {
                    "best_fit_distribution": self._find_best_distribution(retirement_balances),
                    "is_approximately_normal": float(shapiro_p) > 0.05,
                    "is_approximately_lognormal": float(log_shapiro_p) > 0.05
                }
            }
            
        except Exception as e:
            logger.warning(f"Error in statistical tests: {str(e)}")
            return {"error": str(e)}
    
    def _find_best_distribution(self, data: np.ndarray) -> str:
        """Find best-fitting distribution for the data"""
        
        distributions = [
            stats.norm, stats.lognorm, stats.gamma, stats.beta, 
            stats.weibull_min, stats.expon
        ]
        
        best_dist = "normal"
        best_aic = float('inf')
        
        for dist in distributions:
            try:
                params = dist.fit(data)
                ll = np.sum(dist.logpdf(data, *params))
                aic = -2 * ll + 2 * len(params)
                
                if aic < best_aic:
                    best_aic = aic
                    best_dist = dist.name
                    
            except Exception:
                continue
        
        return best_dist
    
    def compare_scenarios(
        self, 
        baseline_results: Dict, 
        alternative_results: Dict,
        scenario_name: str = "Alternative"
    ) -> Dict[str, Any]:
        """
        Compare two sets of simulation results
        
        Args:
            baseline_results: Baseline simulation results
            alternative_results: Alternative scenario results
            scenario_name: Name for the alternative scenario
            
        Returns:
            Comparison analysis
        """
        
        baseline_balances = np.array(baseline_results["raw_results"]["retirement_balances"])
        alternative_balances = np.array(alternative_results["raw_results"]["retirement_balances"])
        
        # Statistical comparison
        t_stat, t_p = stats.ttest_ind(baseline_balances, alternative_balances)
        mann_whitney = stats.mannwhitneyu(baseline_balances, alternative_balances, alternative='two-sided')
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(baseline_balances) - 1) * np.var(baseline_balances) + 
                             (len(alternative_balances) - 1) * np.var(alternative_balances)) / 
                            (len(baseline_balances) + len(alternative_balances) - 2))
        cohens_d = (np.mean(alternative_balances) - np.mean(baseline_balances)) / pooled_std
        
        # Percentage improvements
        median_improvement = (np.median(alternative_balances) - np.median(baseline_balances)) / np.median(baseline_balances) * 100
        mean_improvement = (np.mean(alternative_balances) - np.mean(baseline_balances)) / np.mean(baseline_balances) * 100
        
        # Success rate improvement
        baseline_success = baseline_results["success_probability"]
        alternative_success = alternative_results["success_probability"]
        success_improvement = alternative_success - baseline_success
        
        return {
            "scenario_name": scenario_name,
            "statistical_significance": {
                "t_test": {"statistic": float(t_stat), "p_value": float(t_p)},
                "mann_whitney": {"statistic": float(mann_whitney.statistic), "p_value": float(mann_whitney.pvalue)},
                "effect_size_cohens_d": float(cohens_d),
                "is_significantly_different": float(t_p) < 0.05
            },
            "improvement_metrics": {
                "median_balance_improvement_pct": float(median_improvement),
                "mean_balance_improvement_pct": float(mean_improvement),
                "success_rate_improvement": float(success_improvement),
                "percentile_10_improvement": float((np.percentile(alternative_balances, 10) - np.percentile(baseline_balances, 10)) / np.percentile(baseline_balances, 10) * 100)
            },
            "relative_performance": {
                "probability_alternative_better": float(np.mean(alternative_balances > baseline_balances)),
                "median_ratio": float(np.median(alternative_balances) / np.median(baseline_balances)),
                "volatility_ratio": float(np.std(alternative_balances) / np.std(baseline_balances))
            }
        }
    
    def generate_summary_report(self, comprehensive_results: Dict) -> str:
        """
        Generate a human-readable summary report
        
        Args:
            comprehensive_results: Results from calculate_comprehensive_results
            
        Returns:
            Formatted summary report
        """
        
        outcome = comprehensive_results["outcome_metrics"]
        risk = comprehensive_results["risk_metrics"]
        returns = comprehensive_results["return_metrics"]
        
        report = f"""
MONTE CARLO SIMULATION SUMMARY REPORT
=====================================

SUCCESS PROBABILITY: {outcome['success_probability']:.1%}
The probability that your portfolio will successfully fund your retirement.

EXPECTED OUTCOMES:
- Median Portfolio Value: ${outcome['percentiles']['percentile_50']:,.0f}
- 90% Confidence Range: ${outcome['confidence_interval_95'][0]:,.0f} - ${outcome['confidence_interval_95'][1]:,.0f}
- 10th Percentile (Pessimistic): ${outcome['percentiles']['percentile_10']:,.0f}
- 90th Percentile (Optimistic): ${outcome['percentiles']['percentile_90']:,.0f}

RISK ANALYSIS:
- Portfolio Volatility: {risk['volatility']:.1%}
- Value at Risk (5%): ${risk['value_at_risk_5']:,.0f}
- Maximum Expected Shortfall: ${risk['conditional_var_5']:,.0f}
- Downside Deviation: {risk['downside_deviation']:.1%}

RETURN EXPECTATIONS:
- Expected Annual Return: {returns['mean_annualized_return']:.1%}
- Real Return (After Inflation): {returns['real_return']:.1%}
- Risk-Adjusted Return (Sharpe): {returns['sharpe_ratio']:.2f}

WITHDRAWAL SUSTAINABILITY:
- Optimal Withdrawal Rate: {comprehensive_results['withdrawal_analysis']['optimal_withdrawal_rate']:.1%}
- Depletion Risk: {comprehensive_results['withdrawal_analysis']['depletion_risk']:.1%}

GOAL ACHIEVEMENT PROBABILITIES:
- Basic Retirement ($500K): {comprehensive_results['goal_probabilities']['goal_achievement_probabilities']['basic_retirement']:.1%}
- Comfortable Retirement ($1M): {comprehensive_results['goal_probabilities']['goal_achievement_probabilities']['comfortable_retirement']:.1%}
- Luxury Retirement ($2M): {comprehensive_results['goal_probabilities']['goal_achievement_probabilities']['luxury_retirement']:.1%}

Generated on: {comprehensive_results['metadata']['calculation_timestamp']}
Based on {comprehensive_results['metadata']['n_simulations']:,} simulations
"""
        
        return report.strip()