"""
Trade-Off Analysis Engine

Analyzes the impact of various financial planning decisions including:
- Increasing savings rates
- Delaying retirement
- Reducing retirement spending
- Portfolio allocation changes
- Contribution timing and frequency
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from copy import deepcopy

import numpy as np

from .engine import MonteCarloEngine, SimulationParameters, PortfolioAllocation
from .results_calculator import ResultsCalculator
from .market_assumptions import CapitalMarketAssumptions

logger = logging.getLogger(__name__)


@dataclass
class TradeOffScenario:
    """Defines a trade-off scenario to analyze"""
    name: str
    description: str
    parameter_changes: Dict[str, Any]
    expected_impact: str  # "positive", "negative", "mixed"


@dataclass
class TradeOffResult:
    """Results of a trade-off analysis"""
    scenario_name: str
    baseline_success_rate: float
    scenario_success_rate: float
    improvement: float
    cost_benefit_ratio: Optional[float]
    implementation_difficulty: str
    recommendation: str


class TradeOffAnalyzer:
    """
    Analyzes trade-offs in financial planning decisions
    
    Features:
    - Savings rate impact analysis
    - Retirement timing optimization
    - Spending adjustment scenarios
    - Portfolio allocation trade-offs
    - Multi-dimensional optimization
    - Cost-benefit analysis
    """
    
    def __init__(self, 
                 monte_carlo_engine: Optional[MonteCarloEngine] = None,
                 results_calculator: Optional[ResultsCalculator] = None):
        """
        Initialize trade-off analyzer
        
        Args:
            monte_carlo_engine: Monte Carlo simulation engine
            results_calculator: Results calculator for analysis
        """
        self.engine = monte_carlo_engine or MonteCarloEngine()
        self.results_calc = results_calculator or ResultsCalculator()
        self.last_analysis_results = None
        
        # Pre-defined trade-off scenarios
        self._initialize_scenario_templates()
        
        logger.info("Trade-off analyzer initialized")
    
    def _initialize_scenario_templates(self):
        """Initialize common trade-off scenario templates"""
        
        self.scenario_templates = {
            "increase_savings_3pct": TradeOffScenario(
                name="Increase Savings by 3%",
                description="Increase annual contribution by 3 percentage points of income",
                parameter_changes={"contribution_multiplier": 1.3},
                expected_impact="positive"
            ),
            
            "delay_retirement_2yr": TradeOffScenario(
                name="Delay Retirement by 2 Years",
                description="Work 2 additional years before retirement",
                parameter_changes={"years_to_retirement": 2, "retirement_years": -2},
                expected_impact="positive"
            ),
            
            "reduce_spending_10pct": TradeOffScenario(
                name="Reduce Retirement Spending by 10%",
                description="Reduce retirement spending needs by 10%",
                parameter_changes={"withdrawal_rate": -0.004},  # Reduce from 4% to 3.6%
                expected_impact="positive"
            ),
            
            "increase_risk_allocation": TradeOffScenario(
                name="Increase Equity Allocation",
                description="Shift 10% allocation from bonds to stocks",
                parameter_changes={"portfolio_adjustment": "more_aggressive"},
                expected_impact="mixed"
            ),
            
            "early_retirement_5yr": TradeOffScenario(
                name="Early Retirement (5 Years)",
                description="Retire 5 years earlier than planned",
                parameter_changes={"years_to_retirement": -5, "retirement_years": 5},
                expected_impact="negative"
            ),
            
            "increase_spending_20pct": TradeOffScenario(
                name="Increase Retirement Spending by 20%",
                description="Increase retirement lifestyle spending by 20%",
                parameter_changes={"withdrawal_rate": 0.008},  # Increase from 4% to 4.8%
                expected_impact="negative"
            )
        }
    
    def run_comprehensive_tradeoff_analysis(
        self,
        baseline_portfolio: PortfolioAllocation,
        baseline_parameters: SimulationParameters,
        scenarios_to_analyze: Optional[List[str]] = None,
        custom_scenarios: Optional[List[TradeOffScenario]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive trade-off analysis comparing multiple scenarios
        
        Args:
            baseline_portfolio: Baseline portfolio allocation
            baseline_parameters: Baseline simulation parameters
            scenarios_to_analyze: List of scenario names to analyze
            custom_scenarios: Custom scenarios to include in analysis
            
        Returns:
            Comprehensive trade-off analysis results
        """
        logger.info("Starting comprehensive trade-off analysis")
        
        # Run baseline simulation
        baseline_results = self.engine.run_simulation(baseline_portfolio, baseline_parameters)
        baseline_analysis = self.results_calc.calculate_comprehensive_results(baseline_results)
        
        # Determine scenarios to run
        if scenarios_to_analyze is None:
            scenarios_to_analyze = ["increase_savings_3pct", "delay_retirement_2yr", "reduce_spending_10pct"]
        
        scenarios = []
        for scenario_name in scenarios_to_analyze:
            if scenario_name in self.scenario_templates:
                scenarios.append(self.scenario_templates[scenario_name])
        
        if custom_scenarios:
            scenarios.extend(custom_scenarios)
        
        # Run scenario analysis
        scenario_results = {}
        trade_off_comparisons = {}
        
        for scenario in scenarios:
            logger.info(f"Analyzing scenario: {scenario.name}")
            
            # Create modified parameters for scenario
            modified_portfolio, modified_parameters = self._apply_scenario_changes(
                baseline_portfolio, baseline_parameters, scenario
            )
            
            # Run simulation for scenario
            scenario_sim_results = self.engine.run_simulation(modified_portfolio, modified_parameters)
            scenario_analysis = self.results_calc.calculate_comprehensive_results(scenario_sim_results)
            
            scenario_results[scenario.name] = {
                "scenario": scenario,
                "simulation_results": scenario_sim_results,
                "analysis_results": scenario_analysis
            }
            
            # Compare to baseline
            comparison = self.results_calc.compare_scenarios(
                baseline_results, scenario_sim_results, scenario.name
            )
            trade_off_comparisons[scenario.name] = comparison
        
        # Calculate trade-off metrics
        trade_off_summary = self._calculate_tradeoff_summary(
            baseline_analysis, scenario_results, trade_off_comparisons
        )
        
        # Generate recommendations
        recommendations = self._generate_tradeoff_recommendations(
            trade_off_summary, scenarios
        )
        
        self.last_analysis_results = {
            "baseline_results": baseline_analysis,
            "scenario_results": scenario_results,
            "trade_off_comparisons": trade_off_comparisons,
            "trade_off_summary": trade_off_summary,
            "recommendations": recommendations,
            "meta_analysis": self._perform_meta_analysis(scenario_results, baseline_analysis)
        }
        
        logger.info(f"Trade-off analysis completed for {len(scenarios)} scenarios")
        return self.last_analysis_results
    
    def _apply_scenario_changes(
        self,
        baseline_portfolio: PortfolioAllocation,
        baseline_parameters: SimulationParameters,
        scenario: TradeOffScenario
    ) -> Tuple[PortfolioAllocation, SimulationParameters]:
        """Apply scenario changes to baseline portfolio and parameters"""
        
        # Deep copy to avoid modifying originals
        modified_portfolio = deepcopy(baseline_portfolio)
        modified_parameters = deepcopy(baseline_parameters)
        
        for param_name, change_value in scenario.parameter_changes.items():
            
            if param_name == "contribution_multiplier":
                # Increase annual contribution by multiplier
                modified_parameters.annual_contribution *= change_value
                
            elif param_name == "years_to_retirement":
                # Adjust years to retirement (can be positive or negative)
                modified_parameters.years_to_retirement = max(1, modified_parameters.years_to_retirement + change_value)
                
            elif param_name == "retirement_years":
                # Adjust retirement duration
                modified_parameters.retirement_years = max(5, modified_parameters.retirement_years + change_value)
                
            elif param_name == "withdrawal_rate":
                # Adjust withdrawal rate
                modified_parameters.withdrawal_rate = max(0.01, modified_parameters.withdrawal_rate + change_value)
                
            elif param_name == "portfolio_adjustment":
                # Apply portfolio adjustments
                if change_value == "more_aggressive":
                    modified_portfolio = self._make_portfolio_more_aggressive(modified_portfolio)
                elif change_value == "more_conservative":
                    modified_portfolio = self._make_portfolio_more_conservative(modified_portfolio)
                    
            elif param_name == "contribution_growth_rate":
                # Adjust contribution growth rate
                modified_parameters.contribution_growth_rate = max(0, modified_parameters.contribution_growth_rate + change_value)
                
            elif param_name == "initial_portfolio_value":
                # Adjust initial value
                modified_parameters.initial_portfolio_value *= change_value
        
        return modified_portfolio, modified_parameters
    
    def _make_portfolio_more_aggressive(self, portfolio: PortfolioAllocation) -> PortfolioAllocation:
        """Shift portfolio allocation to be more aggressive (higher equity allocation)"""
        
        allocations = portfolio.allocations.copy()
        
        # Identify equity and bond assets
        equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
        bond_assets = ["US_TREASURY_LONG", "US_TREASURY_INTERMEDIATE", "CORPORATE_BONDS", "HIGH_YIELD_BONDS"]
        
        # Calculate current equity and bond allocations
        current_equity = sum(allocations.get(asset, 0) for asset in equity_assets)
        current_bonds = sum(allocations.get(asset, 0) for asset in bond_assets)
        
        if current_bonds > 0.05:  # Only adjust if we have bonds to shift
            # Shift 10% from bonds to equity
            shift_amount = min(0.10, current_bonds * 0.5)  # Don't shift more than half of bonds
            
            # Reduce bond allocations proportionally
            bond_reduction_factor = (current_bonds - shift_amount) / current_bonds
            for asset in bond_assets:
                if asset in allocations:
                    allocations[asset] *= bond_reduction_factor
            
            # Increase equity allocations proportionally
            if current_equity > 0:
                equity_increase_factor = (current_equity + shift_amount) / current_equity
                for asset in equity_assets:
                    if asset in allocations:
                        allocations[asset] *= equity_increase_factor
            else:
                # Add to US large cap if no current equity
                allocations["US_LARGE_CAP"] = shift_amount
        
        return PortfolioAllocation(allocations)
    
    def _make_portfolio_more_conservative(self, portfolio: PortfolioAllocation) -> PortfolioAllocation:
        """Shift portfolio allocation to be more conservative (higher bond allocation)"""
        
        allocations = portfolio.allocations.copy()
        
        # Identify equity and bond assets
        equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
        bond_assets = ["US_TREASURY_LONG", "US_TREASURY_INTERMEDIATE", "CORPORATE_BONDS"]
        
        # Calculate current allocations
        current_equity = sum(allocations.get(asset, 0) for asset in equity_assets)
        current_bonds = sum(allocations.get(asset, 0) for asset in bond_assets)
        
        if current_equity > 0.10:  # Only adjust if we have significant equity
            # Shift 10% from equity to bonds
            shift_amount = min(0.10, current_equity * 0.2)  # Don't shift more than 20% of equity
            
            # Reduce equity allocations proportionally
            equity_reduction_factor = (current_equity - shift_amount) / current_equity
            for asset in equity_assets:
                if asset in allocations:
                    allocations[asset] *= equity_reduction_factor
            
            # Increase bond allocations or add intermediate treasuries
            if current_bonds > 0:
                bond_increase_factor = (current_bonds + shift_amount) / current_bonds
                for asset in bond_assets:
                    if asset in allocations:
                        allocations[asset] *= bond_increase_factor
            else:
                # Add to intermediate treasuries if no current bonds
                allocations["US_TREASURY_INTERMEDIATE"] = shift_amount
        
        return PortfolioAllocation(allocations)
    
    def _calculate_tradeoff_summary(
        self,
        baseline_analysis: Dict,
        scenario_results: Dict,
        comparisons: Dict
    ) -> Dict[str, Any]:
        """Calculate summary metrics for trade-off analysis"""
        
        baseline_success = baseline_analysis["outcome_metrics"]["success_probability"]
        baseline_median = baseline_analysis["outcome_metrics"]["percentiles"]["percentile_50"]
        
        summary = {
            "baseline_metrics": {
                "success_probability": baseline_success,
                "median_balance": baseline_median,
                "expected_return": baseline_analysis["return_metrics"]["mean_annualized_return"],
                "risk_level": baseline_analysis["risk_metrics"]["volatility"]
            },
            "scenario_impacts": {},
            "ranked_scenarios": []
        }
        
        # Calculate impacts for each scenario
        for scenario_name, results in scenario_results.items():
            scenario_success = results["analysis_results"]["outcome_metrics"]["success_probability"]
            scenario_median = results["analysis_results"]["outcome_metrics"]["percentiles"]["percentile_50"]
            
            success_improvement = scenario_success - baseline_success
            median_improvement_pct = (scenario_median - baseline_median) / baseline_median * 100
            
            # Calculate implementation difficulty score
            difficulty_score = self._calculate_implementation_difficulty(scenario_name, results["scenario"])
            
            # Calculate cost-benefit ratio
            cost_benefit = self._calculate_cost_benefit_ratio(scenario_name, results["scenario"], success_improvement)
            
            impact = {
                "success_rate_change": success_improvement,
                "median_balance_change_pct": median_improvement_pct,
                "implementation_difficulty": difficulty_score,
                "cost_benefit_ratio": cost_benefit,
                "net_benefit_score": success_improvement * 100 - difficulty_score,  # Simple scoring
                "recommendation_tier": self._get_recommendation_tier(success_improvement, difficulty_score, cost_benefit)
            }
            
            summary["scenario_impacts"][scenario_name] = impact
        
        # Rank scenarios by net benefit
        ranked = sorted(
            summary["scenario_impacts"].items(),
            key=lambda x: x[1]["net_benefit_score"],
            reverse=True
        )
        summary["ranked_scenarios"] = [{"name": name, **metrics} for name, metrics in ranked]
        
        return summary
    
    def _calculate_implementation_difficulty(self, scenario_name: str, scenario: TradeOffScenario) -> float:
        """Calculate implementation difficulty score (0-10, where 10 is most difficult)"""
        
        difficulty_map = {
            "increase_savings_3pct": 6.0,  # Requires lifestyle changes
            "delay_retirement_2yr": 7.0,   # Major life decision
            "reduce_spending_10pct": 5.0,  # Lifestyle adjustment
            "increase_risk_allocation": 3.0,  # Simple portfolio change
            "early_retirement_5yr": 8.0,   # Major life change with risks
            "increase_spending_20pct": 2.0  # Easy but negative impact
        }
        
        return difficulty_map.get(scenario_name, 5.0)  # Default medium difficulty
    
    def _calculate_cost_benefit_ratio(self, scenario_name: str, scenario: TradeOffScenario, improvement: float) -> Optional[float]:
        """Calculate cost-benefit ratio for scenario"""
        
        # Simplified cost estimation (would be more sophisticated in practice)
        cost_map = {
            "increase_savings_3pct": 0.03,  # 3% of income opportunity cost
            "delay_retirement_2yr": 0.10,   # High personal cost
            "reduce_spending_10pct": 0.10,  # 10% lifestyle reduction
            "increase_risk_allocation": 0.01,  # Minimal cost
            "early_retirement_5yr": -0.20,  # Negative cost (gain years)
            "increase_spending_20pct": -0.20  # Increased enjoyment
        }
        
        cost = cost_map.get(scenario_name, 0.05)
        
        if cost != 0 and improvement != 0:
            return improvement / abs(cost)
        return None
    
    def _get_recommendation_tier(self, improvement: float, difficulty: float, cost_benefit: Optional[float]) -> str:
        """Get recommendation tier based on improvement and difficulty"""
        
        if improvement > 0.05 and difficulty < 6:  # High improvement, low difficulty
            return "Highly Recommended"
        elif improvement > 0.02 and difficulty < 7:  # Good improvement, moderate difficulty
            return "Recommended"
        elif improvement > 0:  # Some improvement
            return "Consider"
        else:  # No improvement or negative
            return "Not Recommended"
    
    def _generate_tradeoff_recommendations(
        self,
        trade_off_summary: Dict,
        scenarios: List[TradeOffScenario]
    ) -> Dict[str, Any]:
        """Generate actionable recommendations based on trade-off analysis"""
        
        ranked_scenarios = trade_off_summary["ranked_scenarios"]
        
        recommendations = {
            "top_recommendations": [],
            "quick_wins": [],
            "major_decisions": [],
            "avoid": [],
            "implementation_plan": []
        }
        
        for scenario_data in ranked_scenarios:
            scenario_name = scenario_data["name"]
            tier = scenario_data["recommendation_tier"]
            difficulty = scenario_data["implementation_difficulty"]
            improvement = scenario_data["success_rate_change"]
            
            if tier == "Highly Recommended":
                recommendations["top_recommendations"].append({
                    "name": scenario_name,
                    "improvement": f"{improvement:.1%}",
                    "difficulty": difficulty,
                    "priority": "High"
                })
                
                if difficulty < 5:
                    recommendations["quick_wins"].append(scenario_name)
                else:
                    recommendations["major_decisions"].append(scenario_name)
                    
            elif tier == "Recommended":
                if difficulty < 5:
                    recommendations["quick_wins"].append(scenario_name)
                else:
                    recommendations["major_decisions"].append(scenario_name)
                    
            elif improvement <= 0:
                recommendations["avoid"].append({
                    "name": scenario_name,
                    "reason": "Negative or no improvement"
                })
        
        # Create implementation plan
        plan_steps = []
        
        # Quick wins first
        for scenario_name in recommendations["quick_wins"]:
            plan_steps.append({
                "step": len(plan_steps) + 1,
                "action": scenario_name,
                "timeline": "Immediate (0-3 months)",
                "effort": "Low to Medium"
            })
        
        # Major decisions second
        for scenario_name in recommendations["major_decisions"]:
            plan_steps.append({
                "step": len(plan_steps) + 1,
                "action": scenario_name,
                "timeline": "Medium-term (3-12 months)",
                "effort": "High"
            })
        
        recommendations["implementation_plan"] = plan_steps
        
        return recommendations
    
    def _perform_meta_analysis(self, scenario_results: Dict, baseline_analysis: Dict) -> Dict[str, Any]:
        """Perform meta-analysis across all scenarios"""
        
        # Extract key metrics from all scenarios
        success_rates = [baseline_analysis["outcome_metrics"]["success_probability"]]
        median_balances = [baseline_analysis["outcome_metrics"]["percentiles"]["percentile_50"]]
        volatilities = [baseline_analysis["risk_metrics"]["volatility"]]
        
        for scenario_name, results in scenario_results.items():
            analysis = results["analysis_results"]
            success_rates.append(analysis["outcome_metrics"]["success_probability"])
            median_balances.append(analysis["outcome_metrics"]["percentiles"]["percentile_50"])
            volatilities.append(analysis["risk_metrics"]["volatility"])
        
        # Calculate meta statistics
        meta_analysis = {
            "sensitivity_analysis": {
                "success_rate_range": float(np.max(success_rates) - np.min(success_rates)),
                "median_balance_range_pct": float((np.max(median_balances) - np.min(median_balances)) / np.min(median_balances) * 100),
                "volatility_range": float(np.max(volatilities) - np.min(volatilities))
            },
            "correlation_analysis": {
                "risk_return_correlation": float(np.corrcoef(success_rates, volatilities)[0, 1]) if len(success_rates) > 1 else 0.0,
                "balance_success_correlation": float(np.corrcoef(median_balances, success_rates)[0, 1]) if len(success_rates) > 1 else 0.0
            },
            "optimization_potential": {
                "max_improvement_possible": float(np.max(success_rates) - success_rates[0]),
                "efficiency_frontier": self._calculate_efficiency_frontier(success_rates, volatilities),
                "pareto_optimal_scenarios": self._identify_pareto_optimal_scenarios(scenario_results)
            }
        }
        
        return meta_analysis
    
    def _calculate_efficiency_frontier(self, success_rates: List[float], volatilities: List[float]) -> List[Dict]:
        """Calculate efficient frontier points"""
        
        if len(success_rates) < 2:
            return []
        
        # Simple efficiency calculation - in practice would use more sophisticated optimization
        frontier_points = []
        for i, (success, vol) in enumerate(zip(success_rates, volatilities)):
            is_efficient = True
            for j, (other_success, other_vol) in enumerate(zip(success_rates, volatilities)):
                if i != j and other_success >= success and other_vol <= vol and (other_success > success or other_vol < vol):
                    is_efficient = False
                    break
            
            if is_efficient:
                frontier_points.append({
                    "success_rate": success,
                    "volatility": vol,
                    "sharpe_like_ratio": success / vol if vol > 0 else 0
                })
        
        return sorted(frontier_points, key=lambda x: x["volatility"])
    
    def _identify_pareto_optimal_scenarios(self, scenario_results: Dict) -> List[str]:
        """Identify Pareto optimal scenarios"""
        
        pareto_optimal = []
        
        for scenario1, results1 in scenario_results.items():
            analysis1 = results1["analysis_results"]
            success1 = analysis1["outcome_metrics"]["success_probability"]
            median1 = analysis1["outcome_metrics"]["percentiles"]["percentile_50"]
            
            is_pareto_optimal = True
            
            for scenario2, results2 in scenario_results.items():
                if scenario1 == scenario2:
                    continue
                    
                analysis2 = results2["analysis_results"]
                success2 = analysis2["outcome_metrics"]["success_probability"]
                median2 = analysis2["outcome_metrics"]["percentiles"]["percentile_50"]
                
                # If scenario2 dominates scenario1 in both metrics
                if success2 >= success1 and median2 >= median1 and (success2 > success1 or median2 > median1):
                    is_pareto_optimal = False
                    break
            
            if is_pareto_optimal:
                pareto_optimal.append(scenario1)
        
        return pareto_optimal
    
    def analyze_specific_tradeoff(
        self,
        baseline_portfolio: PortfolioAllocation,
        baseline_parameters: SimulationParameters,
        custom_scenario: TradeOffScenario
    ) -> Dict[str, Any]:
        """
        Analyze a specific custom trade-off scenario
        
        Args:
            baseline_portfolio: Baseline portfolio allocation
            baseline_parameters: Baseline simulation parameters
            custom_scenario: Custom scenario to analyze
            
        Returns:
            Detailed analysis of the specific trade-off
        """
        logger.info(f"Analyzing specific trade-off: {custom_scenario.name}")
        
        # Run baseline
        baseline_results = self.engine.run_simulation(baseline_portfolio, baseline_parameters)
        baseline_analysis = self.results_calc.calculate_comprehensive_results(baseline_results)
        
        # Apply scenario changes
        modified_portfolio, modified_parameters = self._apply_scenario_changes(
            baseline_portfolio, baseline_parameters, custom_scenario
        )
        
        # Run scenario simulation
        scenario_results = self.engine.run_simulation(modified_portfolio, modified_parameters)
        scenario_analysis = self.results_calc.calculate_comprehensive_results(scenario_results)
        
        # Compare results
        comparison = self.results_calc.compare_scenarios(
            baseline_results, scenario_results, custom_scenario.name
        )
        
        # Calculate detailed trade-off metrics
        detailed_analysis = {
            "scenario_details": {
                "name": custom_scenario.name,
                "description": custom_scenario.description,
                "parameter_changes": custom_scenario.parameter_changes
            },
            "baseline_results": baseline_analysis,
            "scenario_results": scenario_analysis,
            "comparison": comparison,
            "trade_off_metrics": self._calculate_detailed_tradeoff_metrics(
                baseline_analysis, scenario_analysis, custom_scenario
            ),
            "recommendation": self._generate_single_scenario_recommendation(
                comparison, custom_scenario
            )
        }
        
        return detailed_analysis
    
    def _calculate_detailed_tradeoff_metrics(
        self,
        baseline_analysis: Dict,
        scenario_analysis: Dict,
        scenario: TradeOffScenario
    ) -> Dict[str, Any]:
        """Calculate detailed metrics for a single trade-off"""
        
        baseline_success = baseline_analysis["outcome_metrics"]["success_probability"]
        scenario_success = scenario_analysis["outcome_metrics"]["success_probability"]
        
        baseline_median = baseline_analysis["outcome_metrics"]["percentiles"]["percentile_50"]
        scenario_median = scenario_analysis["outcome_metrics"]["percentiles"]["percentile_50"]
        
        return {
            "success_rate_impact": {
                "baseline": baseline_success,
                "scenario": scenario_success,
                "absolute_change": scenario_success - baseline_success,
                "relative_change_pct": (scenario_success - baseline_success) / baseline_success * 100 if baseline_success > 0 else 0
            },
            "wealth_impact": {
                "baseline_median": baseline_median,
                "scenario_median": scenario_median,
                "absolute_change": scenario_median - baseline_median,
                "relative_change_pct": (scenario_median - baseline_median) / baseline_median * 100
            },
            "risk_impact": {
                "baseline_volatility": baseline_analysis["risk_metrics"]["volatility"],
                "scenario_volatility": scenario_analysis["risk_metrics"]["volatility"],
                "volatility_change": scenario_analysis["risk_metrics"]["volatility"] - baseline_analysis["risk_metrics"]["volatility"]
            },
            "implementation_assessment": {
                "difficulty_score": self._calculate_implementation_difficulty(scenario.name, scenario),
                "expected_impact": scenario.expected_impact,
                "cost_benefit_ratio": self._calculate_cost_benefit_ratio(scenario.name, scenario, scenario_success - baseline_success)
            }
        }
    
    def _generate_single_scenario_recommendation(self, comparison: Dict, scenario: TradeOffScenario) -> Dict[str, Any]:
        """Generate recommendation for a single scenario"""
        
        improvement = comparison["improvement_metrics"]["success_rate_improvement"]
        median_improvement = comparison["improvement_metrics"]["median_balance_improvement_pct"]
        
        if improvement > 0.05:
            recommendation_level = "Highly Recommended"
            reason = "Significant improvement in success probability"
        elif improvement > 0.02:
            recommendation_level = "Recommended"
            reason = "Moderate improvement in outcomes"
        elif improvement > 0:
            recommendation_level = "Consider"
            reason = "Small positive improvement"
        else:
            recommendation_level = "Not Recommended"
            reason = "No improvement or negative impact"
        
        return {
            "recommendation_level": recommendation_level,
            "primary_reason": reason,
            "success_rate_improvement": f"{improvement:.1%}",
            "wealth_improvement": f"{median_improvement:.1%}",
            "key_benefits": self._identify_key_benefits(comparison),
            "key_risks": self._identify_key_risks(comparison),
            "implementation_priority": "High" if improvement > 0.03 else "Medium" if improvement > 0.01 else "Low"
        }
    
    def _identify_key_benefits(self, comparison: Dict) -> List[str]:
        """Identify key benefits of a scenario"""
        
        benefits = []
        
        if comparison["improvement_metrics"]["success_rate_improvement"] > 0.02:
            benefits.append("Significantly improves retirement funding probability")
        
        if comparison["improvement_metrics"]["median_balance_improvement_pct"] > 5:
            benefits.append("Increases expected retirement wealth")
        
        if comparison["improvement_metrics"]["percentile_10_improvement"] > 5:
            benefits.append("Reduces downside risk")
        
        return benefits
    
    def _identify_key_risks(self, comparison: Dict) -> List[str]:
        """Identify key risks of a scenario"""
        
        risks = []
        
        if comparison["improvement_metrics"]["success_rate_improvement"] < 0:
            risks.append("Reduces retirement funding probability")
        
        if comparison["relative_performance"]["volatility_ratio"] > 1.1:
            risks.append("Increases portfolio volatility")
        
        return risks
    
    def get_optimization_recommendations(self) -> Optional[Dict[str, Any]]:
        """Get optimization recommendations based on last analysis"""
        
        if self.last_analysis_results is None:
            return None
        
        recommendations = self.last_analysis_results["recommendations"]
        trade_off_summary = self.last_analysis_results["trade_off_summary"]
        
        return {
            "summary": "Based on the trade-off analysis, here are the optimal strategies:",
            "top_priority_actions": recommendations["top_recommendations"][:3],
            "quick_wins": recommendations["quick_wins"],
            "implementation_roadmap": recommendations["implementation_plan"],
            "expected_improvement": {
                "best_case_success_rate": max([
                    scenario["success_rate_change"] for scenario in trade_off_summary["ranked_scenarios"]
                ]) + trade_off_summary["baseline_metrics"]["success_probability"],
                "combined_strategy_potential": "Multiple strategies can be combined for greater impact"
            }
        }