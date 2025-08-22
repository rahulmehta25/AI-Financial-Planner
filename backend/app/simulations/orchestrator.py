"""
Monte Carlo Simulation Orchestrator

Main orchestrator class that coordinates all simulation components and provides
a high-level interface for running comprehensive retirement planning simulations.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import json

from .market_assumptions import CapitalMarketAssumptions
from .engine import MonteCarloEngine, PortfolioAllocation, SimulationParameters
from .portfolio_mapping import PortfolioMapper, RiskTolerance
from .results_calculator import ResultsCalculator
from .trade_off_analyzer import TradeOffAnalyzer, TradeOffScenario
from .logging_config import (
    SimulationLogger, performance_monitor, error_handler,
    ValidationError, CalculationError, log_simulation_config,
    log_portfolio_allocation, log_results_summary
)

logger = logging.getLogger(__name__)


@dataclass
class SimulationRequest:
    """Complete simulation request with all parameters"""
    # Basic parameters
    user_id: str
    simulation_name: Optional[str] = None
    
    # Demographics
    current_age: int = 35
    retirement_age: int = 65
    life_expectancy: int = 90
    
    # Financial parameters
    current_portfolio_value: float = 50_000
    annual_contribution: float = 12_000
    contribution_growth_rate: float = 0.03
    target_replacement_ratio: float = 0.80
    current_annual_income: float = 60_000
    
    # Risk preferences
    risk_tolerance: Union[str, RiskTolerance] = "moderate"
    custom_portfolio_allocation: Optional[Dict[str, float]] = None
    
    # Simulation settings
    n_simulations: int = 50_000
    random_seed: Optional[int] = None
    include_trade_off_analysis: bool = True
    include_stress_testing: bool = True
    
    # Advanced settings
    rebalancing_frequency: int = 12  # Monthly
    inflation_assumption: float = 0.025
    market_regime: str = "normal"


@dataclass
class SimulationResults:
    """Complete simulation results"""
    request_id: str
    simulation_name: Optional[str]
    timestamp: datetime
    
    # Core results
    success_probability: float
    median_retirement_balance: float
    percentile_10_balance: float
    percentile_90_balance: float
    
    # Detailed analysis
    comprehensive_results: Dict[str, Any]
    portfolio_allocation: Dict[str, float]
    etf_recommendations: List[Dict[str, Any]]
    
    # Trade-off analysis
    trade_off_analysis: Optional[Dict[str, Any]] = None
    stress_test_results: Optional[Dict[str, Any]] = None
    
    # Performance metrics
    simulation_time_seconds: float
    performance_metrics: Dict[str, Any]
    
    # Recommendations
    recommendations: Dict[str, Any]
    summary_report: str


class SimulationOrchestrator:
    """
    Main orchestrator for Monte Carlo retirement simulations
    
    Coordinates all simulation components to provide comprehensive
    retirement planning analysis with recommendations.
    """
    
    def __init__(self):
        """Initialize the orchestrator with all components"""
        self.sim_logger = SimulationLogger("simulation_orchestrator")
        self.logger = self.sim_logger.logger
        
        # Initialize components
        self.market_assumptions = CapitalMarketAssumptions()
        self.portfolio_mapper = PortfolioMapper()
        self.monte_carlo_engine = MonteCarloEngine(self.market_assumptions)
        self.results_calculator = ResultsCalculator()
        self.trade_off_analyzer = TradeOffAnalyzer(
            self.monte_carlo_engine, self.results_calculator
        )
        
        self.logger.info("Simulation orchestrator initialized with all components")
    
    @performance_monitor(SimulationLogger("orchestrator"))
    @error_handler(SimulationLogger("orchestrator"), raise_on_error=True)
    async def run_comprehensive_simulation(self, request: SimulationRequest) -> SimulationResults:
        """
        Run comprehensive retirement simulation with all analysis components
        
        Args:
            request: Complete simulation request
            
        Returns:
            Comprehensive simulation results
        """
        self.logger.info(f"Starting comprehensive simulation for user {request.user_id}")
        
        try:
            # Validate request
            self._validate_simulation_request(request)
            
            # Setup simulation parameters
            portfolio_allocation, simulation_params = self._prepare_simulation_inputs(request)
            
            # Log configuration
            self._log_simulation_setup(request, portfolio_allocation, simulation_params)
            
            # Run core Monte Carlo simulation
            with self.sim_logger.performance_timer("core_monte_carlo_simulation"):
                core_results = self.monte_carlo_engine.run_simulation(
                    portfolio_allocation, simulation_params
                )
            
            # Calculate comprehensive results
            with self.sim_logger.performance_timer("comprehensive_analysis"):
                comprehensive_results = self.results_calculator.calculate_comprehensive_results(
                    core_results, target_value=self._calculate_target_retirement_value(request)
                )
            
            # Get ETF recommendations
            etf_recommendations = self.portfolio_mapper.get_etf_recommendations(
                portfolio_allocation, expense_ratio_priority=True
            )
            
            # Run trade-off analysis if requested
            trade_off_results = None
            if request.include_trade_off_analysis:
                with self.sim_logger.performance_timer("trade_off_analysis"):
                    trade_off_results = await self._run_trade_off_analysis(
                        portfolio_allocation, simulation_params, request
                    )
            
            # Run stress testing if requested
            stress_test_results = None
            if request.include_stress_testing:
                with self.sim_logger.performance_timer("stress_testing"):
                    stress_test_results = self.monte_carlo_engine.run_stress_test(
                        portfolio_allocation, simulation_params
                    )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                comprehensive_results, trade_off_results, request
            )
            
            # Generate summary report
            summary_report = self._generate_summary_report(
                comprehensive_results, recommendations, request
            )
            
            # Compile final results
            results = SimulationResults(
                request_id=f"{request.user_id}_{datetime.now().isoformat()}",
                simulation_name=request.simulation_name,
                timestamp=datetime.now(),
                success_probability=comprehensive_results["outcome_metrics"]["success_probability"],
                median_retirement_balance=comprehensive_results["outcome_metrics"]["percentiles"]["percentile_50"],
                percentile_10_balance=comprehensive_results["outcome_metrics"]["percentiles"]["percentile_10"],
                percentile_90_balance=comprehensive_results["outcome_metrics"]["percentiles"]["percentile_90"],
                comprehensive_results=comprehensive_results,
                portfolio_allocation=portfolio_allocation.allocations,
                etf_recommendations=[asdict(etf) for etf in etf_recommendations],
                trade_off_analysis=trade_off_results,
                stress_test_results=stress_test_results,
                simulation_time_seconds=self.monte_carlo_engine.last_simulation_time,
                performance_metrics=self.monte_carlo_engine.get_performance_metrics(),
                recommendations=recommendations,
                summary_report=summary_report
            )
            
            # Log final results
            log_results_summary(comprehensive_results)
            self.sim_logger.log_simulation_end(True, {
                'success_probability': results.success_probability,
                'median_balance': results.median_retirement_balance
            })
            
            self.logger.info(f"Comprehensive simulation completed successfully for user {request.user_id}")
            
            return results
            
        except Exception as e:
            self.sim_logger.log_simulation_end(False)
            self.sim_logger.log_error(e, context="Comprehensive simulation failed")
            raise CalculationError(f"Simulation orchestration failed: {str(e)}") from e
    
    def _validate_simulation_request(self, request: SimulationRequest) -> None:
        """Validate simulation request parameters"""
        errors = []
        
        # Demographics validation
        if not 18 <= request.current_age <= 100:
            errors.append("Current age must be between 18 and 100")
        
        if request.retirement_age <= request.current_age:
            errors.append("Retirement age must be greater than current age")
        
        if request.life_expectancy <= request.retirement_age:
            errors.append("Life expectancy must be greater than retirement age")
        
        # Financial validation
        if request.current_portfolio_value < 0:
            errors.append("Current portfolio value cannot be negative")
        
        if request.annual_contribution < 0:
            errors.append("Annual contribution cannot be negative")
        
        if not 0 <= request.target_replacement_ratio <= 2.0:
            errors.append("Target replacement ratio must be between 0 and 200%")
        
        if request.current_annual_income <= 0:
            errors.append("Current annual income must be positive")
        
        # Risk tolerance validation
        if isinstance(request.risk_tolerance, str):
            try:
                RiskTolerance(request.risk_tolerance.lower())
            except ValueError:
                errors.append(f"Invalid risk tolerance: {request.risk_tolerance}")
        
        # Custom portfolio validation
        if request.custom_portfolio_allocation:
            is_valid, portfolio_errors = self.portfolio_mapper.validate_allocation(
                request.custom_portfolio_allocation
            )
            if not is_valid:
                errors.extend(portfolio_errors)
        
        # Simulation settings validation
        if not 1000 <= request.n_simulations <= 100_000:
            errors.append("Number of simulations must be between 1,000 and 100,000")
        
        if errors:
            raise ValidationError(f"Request validation failed: {'; '.join(errors)}")
    
    def _prepare_simulation_inputs(
        self, request: SimulationRequest
    ) -> tuple[PortfolioAllocation, SimulationParameters]:
        """Prepare simulation inputs from request"""
        
        # Determine portfolio allocation
        if request.custom_portfolio_allocation:
            portfolio_allocation = PortfolioAllocation(request.custom_portfolio_allocation)
        else:
            # Use risk tolerance and age to determine allocation
            if isinstance(request.risk_tolerance, str):
                risk_tolerance = RiskTolerance(request.risk_tolerance.lower())
            else:
                risk_tolerance = request.risk_tolerance
            
            portfolio_allocation = self.portfolio_mapper.get_age_adjusted_portfolio(
                risk_tolerance, request.current_age
            )
        
        # Calculate simulation parameters
        years_to_retirement = request.retirement_age - request.current_age
        retirement_years = request.life_expectancy - request.retirement_age
        
        # Calculate withdrawal rate based on replacement ratio
        target_annual_spending = request.current_annual_income * request.target_replacement_ratio
        # This is a simplified calculation - in practice, would need more sophisticated analysis
        withdrawal_rate = 0.04  # Start with standard 4% rule
        
        simulation_params = SimulationParameters(
            n_simulations=request.n_simulations,
            years_to_retirement=years_to_retirement,
            retirement_years=retirement_years,
            initial_portfolio_value=request.current_portfolio_value,
            annual_contribution=request.annual_contribution,
            contribution_growth_rate=request.contribution_growth_rate,
            withdrawal_rate=withdrawal_rate,
            rebalancing_frequency=request.rebalancing_frequency,
            random_seed=request.random_seed
        )
        
        return portfolio_allocation, simulation_params
    
    def _calculate_target_retirement_value(self, request: SimulationRequest) -> float:
        """Calculate target retirement portfolio value"""
        target_annual_spending = request.current_annual_income * request.target_replacement_ratio
        retirement_years = request.life_expectancy - request.retirement_age
        
        # Use 4% rule as baseline
        target_value = target_annual_spending / 0.04
        
        return target_value
    
    def _log_simulation_setup(
        self,
        request: SimulationRequest,
        portfolio: PortfolioAllocation,
        params: SimulationParameters
    ) -> None:
        """Log simulation setup details"""
        
        config = {
            "user_id": request.user_id,
            "current_age": request.current_age,
            "retirement_age": request.retirement_age,
            "years_to_retirement": params.years_to_retirement,
            "current_portfolio_value": params.initial_portfolio_value,
            "annual_contribution": params.annual_contribution,
            "n_simulations": params.n_simulations,
            "risk_tolerance": str(request.risk_tolerance)
        }
        
        log_simulation_config(config)
        log_portfolio_allocation(portfolio.allocations)
    
    async def _run_trade_off_analysis(
        self,
        portfolio: PortfolioAllocation,
        params: SimulationParameters,
        request: SimulationRequest
    ) -> Dict[str, Any]:
        """Run trade-off analysis in async context"""
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def run_analysis():
            return self.trade_off_analyzer.run_comprehensive_tradeoff_analysis(
                portfolio,
                params,
                scenarios_to_analyze=["increase_savings_3pct", "delay_retirement_2yr", "reduce_spending_10pct"]
            )
        
        # Run trade-off analysis in thread pool
        try:
            trade_off_results = await loop.run_in_executor(None, run_analysis)
            return trade_off_results
        except Exception as e:
            self.logger.warning(f"Trade-off analysis failed: {str(e)}")
            return None
    
    def _generate_recommendations(
        self,
        comprehensive_results: Dict[str, Any],
        trade_off_results: Optional[Dict[str, Any]],
        request: SimulationRequest
    ) -> Dict[str, Any]:
        """Generate actionable recommendations based on results"""
        
        success_rate = comprehensive_results["outcome_metrics"]["success_probability"]
        median_balance = comprehensive_results["outcome_metrics"]["percentiles"]["percentile_50"]
        
        recommendations = {
            "overall_assessment": self._assess_overall_situation(success_rate, comprehensive_results),
            "immediate_actions": [],
            "medium_term_strategies": [],
            "portfolio_adjustments": [],
            "priority_ranking": []
        }
        
        # Assess success probability
        if success_rate < 0.60:
            recommendations["immediate_actions"].extend([
                "Consider increasing savings rate by 3-5%",
                "Review and potentially delay retirement by 1-2 years",
                "Explore additional income sources"
            ])
        elif success_rate < 0.80:
            recommendations["medium_term_strategies"].extend([
                "Monitor progress annually and adjust as needed",
                "Consider slightly more aggressive portfolio allocation",
                "Plan for potential part-time work in early retirement"
            ])
        else:
            recommendations["immediate_actions"].append("Current plan looks strong - maintain course")
        
        # Portfolio-specific recommendations
        portfolio_metrics = self.portfolio_mapper.calculate_portfolio_metrics(
            PortfolioAllocation(request.custom_portfolio_allocation or {})
        )
        
        if portfolio_metrics["equity_allocation"] < 0.50 and request.current_age < 50:
            recommendations["portfolio_adjustments"].append(
                "Consider increasing equity allocation for better long-term growth"
            )
        
        # Trade-off analysis recommendations
        if trade_off_results and "recommendations" in trade_off_results:
            trade_off_recs = trade_off_results["recommendations"]
            if trade_off_recs["top_recommendations"]:
                recommendations["priority_ranking"] = trade_off_recs["top_recommendations"]
        
        return recommendations
    
    def _assess_overall_situation(
        self, success_rate: float, comprehensive_results: Dict[str, Any]
    ) -> str:
        """Assess overall retirement situation"""
        
        if success_rate >= 0.90:
            return "Excellent - Your retirement plan is on track with high probability of success"
        elif success_rate >= 0.80:
            return "Very Good - Your plan has strong probability of success with minor adjustments possible"
        elif success_rate >= 0.60:
            return "Good - Your plan is generally solid but could benefit from optimization"
        elif success_rate >= 0.40:
            return "Needs Attention - Significant improvements needed to ensure retirement security"
        else:
            return "Critical - Major changes required to achieve retirement goals"
    
    def _generate_summary_report(
        self,
        comprehensive_results: Dict[str, Any],
        recommendations: Dict[str, Any],
        request: SimulationRequest
    ) -> str:
        """Generate human-readable summary report"""
        
        success_rate = comprehensive_results["outcome_metrics"]["success_probability"]
        median_balance = comprehensive_results["outcome_metrics"]["percentiles"]["percentile_50"]
        p10_balance = comprehensive_results["outcome_metrics"]["percentiles"]["percentile_10"]
        p90_balance = comprehensive_results["outcome_metrics"]["percentiles"]["percentile_90"]
        
        report = f"""
RETIREMENT PLANNING ANALYSIS SUMMARY
===================================

PERSONAL PROFILE:
- Current Age: {request.current_age}
- Retirement Age: {request.retirement_age}
- Current Portfolio: ${request.current_portfolio_value:,.0f}
- Annual Savings: ${request.annual_contribution:,.0f}
- Risk Tolerance: {request.risk_tolerance}

SIMULATION RESULTS ({request.n_simulations:,} scenarios):
- SUCCESS PROBABILITY: {success_rate:.1%}
- Expected Portfolio at Retirement: ${median_balance:,.0f}
- Conservative Scenario (10th percentile): ${p10_balance:,.0f}
- Optimistic Scenario (90th percentile): ${p90_balance:,.0f}

OVERALL ASSESSMENT:
{recommendations["overall_assessment"]}

IMMEDIATE ACTION ITEMS:
"""
        
        for i, action in enumerate(recommendations["immediate_actions"], 1):
            report += f"{i}. {action}\n"
        
        if recommendations["priority_ranking"]:
            report += "\nHIGHEST IMPACT OPPORTUNITIES:\n"
            for i, priority in enumerate(recommendations["priority_ranking"][:3], 1):
                report += f"{i}. {priority.get('name', 'Unknown')}: {priority.get('improvement', 'N/A')} improvement\n"
        
        report += f"""
PORTFOLIO ALLOCATION:
"""
        
        if hasattr(request, 'custom_portfolio_allocation') and request.custom_portfolio_allocation:
            for asset, allocation in request.custom_portfolio_allocation.items():
                report += f"- {asset}: {allocation:.1%}\n"
        
        report += f"""
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis time: {self.monte_carlo_engine.last_simulation_time:.1f} seconds
"""
        
        return report.strip()
    
    async def run_quick_analysis(self, request: SimulationRequest) -> Dict[str, Any]:
        """
        Run quick analysis with reduced simulation count for fast feedback
        
        Args:
            request: Simulation request
            
        Returns:
            Quick analysis results
        """
        # Reduce simulation count for speed
        quick_request = request
        quick_request.n_simulations = min(5000, request.n_simulations)
        quick_request.include_trade_off_analysis = False
        quick_request.include_stress_testing = False
        
        results = await self.run_comprehensive_simulation(quick_request)
        
        return {
            "success_probability": results.success_probability,
            "median_balance": results.median_retirement_balance,
            "assessment": self._assess_overall_situation(
                results.success_probability, results.comprehensive_results
            ),
            "key_recommendations": results.recommendations["immediate_actions"][:3]
        }
    
    def get_default_request(self, user_id: str, **kwargs) -> SimulationRequest:
        """Get default simulation request with reasonable assumptions"""
        
        defaults = {
            "user_id": user_id,
            "current_age": 35,
            "retirement_age": 65,
            "current_portfolio_value": 50_000,
            "annual_contribution": 12_000,
            "current_annual_income": 60_000,
            "risk_tolerance": "moderate"
        }
        
        defaults.update(kwargs)
        
        return SimulationRequest(**defaults)
    
    async def batch_analysis(self, requests: List[SimulationRequest]) -> List[SimulationResults]:
        """
        Run batch analysis for multiple simulation requests
        
        Args:
            requests: List of simulation requests
            
        Returns:
            List of simulation results
        """
        results = []
        
        for i, request in enumerate(requests):
            self.logger.info(f"Processing batch simulation {i+1}/{len(requests)}")
            
            try:
                result = await self.run_comprehensive_simulation(request)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Batch simulation {i+1} failed: {str(e)}")
                # Continue with other simulations
                continue
        
        self.logger.info(f"Batch analysis completed: {len(results)}/{len(requests)} successful")
        
        return results