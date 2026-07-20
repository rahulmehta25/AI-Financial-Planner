"""Integration module for AI narrative system with existing financial planning endpoints."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.simulation_result import SimulationResult
from ..models.financial_profile import FinancialProfile
from ..services.simulation_service import SimulationService
from ..simulations.trade_off_analyzer import TradeOffAnalyzer
from .narrative_generator import NarrativeGenerator, NarrativeRequest, NarrativeType
from .config import Language, AIConfig
from .enhanced_audit_logger import EnhancedAuditLogger

logger = logging.getLogger(__name__)


class AIIntegrationService:
    """Service to integrate AI narratives with financial planning system."""
    
    def __init__(
        self,
        narrative_generator: Optional[NarrativeGenerator] = None,
        audit_logger: Optional[EnhancedAuditLogger] = None
    ):
        """Initialize integration service."""
        self.config = AIConfig()
        self.narrative_generator = narrative_generator or NarrativeGenerator()
        self.audit_logger = audit_logger or EnhancedAuditLogger(self.config)
        
    async def enhance_simulation_results(
        self,
        simulation_result: SimulationResult,
        user_id: str,
        language: Language = Language.ENGLISH,
        include_all_narratives: bool = True
    ) -> Dict[str, Any]:
        """Enhance simulation results with AI narratives."""
        try:
            # Extract key metrics from simulation
            simulation_data = self._extract_simulation_metrics(simulation_result)
            
            narratives = {}
            
            # Generate simulation summary
            if include_all_narratives or "summary" in simulation_result.requested_narratives:
                summary_request = NarrativeRequest(
                    simulation_id=str(simulation_result.id),
                    user_id=user_id,
                    narrative_type=NarrativeType.SIMULATION_SUMMARY,
                    language=language,
                    data=simulation_data,
                    include_disclaimer=True
                )
                summary_response = await self.narrative_generator.generate_narrative(summary_request)
                narratives["summary"] = summary_response.narrative
            
            # Generate trade-off analysis if available
            if simulation_result.scenarios and len(simulation_result.scenarios) > 1:
                trade_off_data = self._extract_trade_off_data(simulation_result)
                trade_off_request = NarrativeRequest(
                    simulation_id=str(simulation_result.id),
                    user_id=user_id,
                    narrative_type=NarrativeType.TRADE_OFF_ANALYSIS,
                    language=language,
                    data=trade_off_data,
                    include_disclaimer=False
                )
                trade_off_response = await self.narrative_generator.generate_narrative(trade_off_request)
                narratives["trade_off_analysis"] = trade_off_response.narrative
            
            # Generate recommendations
            if include_all_narratives or "recommendations" in simulation_result.requested_narratives:
                recommendation_data = self._generate_recommendations(simulation_result)
                recommendation_request = NarrativeRequest(
                    simulation_id=str(simulation_result.id),
                    user_id=user_id,
                    narrative_type=NarrativeType.RECOMMENDATION,
                    language=language,
                    data=recommendation_data,
                    include_disclaimer=True
                )
                recommendation_response = await self.narrative_generator.generate_narrative(recommendation_request)
                narratives["recommendations"] = recommendation_response.narrative
            
            # Generate risk assessment
            if simulation_result.risk_metrics:
                risk_data = self._extract_risk_metrics(simulation_result)
                risk_request = NarrativeRequest(
                    simulation_id=str(simulation_result.id),
                    user_id=user_id,
                    narrative_type=NarrativeType.RISK_ASSESSMENT,
                    language=language,
                    data=risk_data,
                    include_disclaimer=False
                )
                risk_response = await self.narrative_generator.generate_narrative(risk_request)
                narratives["risk_assessment"] = risk_response.narrative
            
            # Log the enhancement
            await self.audit_logger.log_event(
                event_type="SIMULATION_ENHANCED",
                data={
                    "simulation_id": str(simulation_result.id),
                    "narratives_generated": list(narratives.keys()),
                    "language": language.value
                },
                user_id=user_id
            )
            
            return {
                "simulation_id": str(simulation_result.id),
                "original_results": simulation_result.to_dict(),
                "narratives": narratives,
                "language": language.value,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to enhance simulation results: {str(e)}")
            await self.audit_logger.log_error(
                user_id=user_id,
                simulation_id=str(simulation_result.id),
                error=str(e)
            )
            
            # Return original results without enhancement
            return {
                "simulation_id": str(simulation_result.id),
                "original_results": simulation_result.to_dict(),
                "narratives": {
                    "error": "Unable to generate narratives at this time. Please review the numerical results."
                },
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _extract_simulation_metrics(self, simulation_result: SimulationResult) -> Dict[str, Any]:
        """Extract key metrics from simulation result for narrative generation."""
        return {
            "num_simulations": simulation_result.num_simulations or 10000,
            "success_rate": simulation_result.success_probability * 100,
            "median_value": simulation_result.percentiles.get("50", 0),
            "best_case": simulation_result.percentiles.get("95", 0),
            "worst_case": simulation_result.percentiles.get("5", 0),
            "monthly_savings": simulation_result.required_monthly_savings or 0,
            "equity_pct": simulation_result.asset_allocation.get("equity", 60),
            "bond_pct": simulation_result.asset_allocation.get("bonds", 30),
            "expected_return": simulation_result.expected_return * 100,
            "std_dev": simulation_result.volatility * 100,
            "inflation_rate": simulation_result.inflation_assumption * 100,
            "historical_years": 30,  # Default value
            
            # Additional context
            "current_age": simulation_result.current_age,
            "retirement_age": simulation_result.retirement_age,
            "initial_portfolio": simulation_result.initial_portfolio_value,
            "years_to_retirement": simulation_result.retirement_age - simulation_result.current_age
        }
    
    def _extract_trade_off_data(self, simulation_result: SimulationResult) -> Dict[str, Any]:
        """Extract trade-off analysis data from multiple scenarios."""
        # Assuming we have at least 2 scenarios
        current = simulation_result.scenarios[0]
        conservative = simulation_result.scenarios[1] if len(simulation_result.scenarios) > 1 else current
        aggressive = simulation_result.scenarios[2] if len(simulation_result.scenarios) > 2 else current
        
        return {
            # Current strategy
            "current_success": current.get("success_rate", 0) * 100,
            "current_value": current.get("expected_value", 0),
            "current_risk": current.get("volatility", 0) * 100,
            
            # Conservative approach
            "conservative_equity": conservative.get("equity_allocation", 40),
            "conservative_success": conservative.get("success_rate", 0) * 100,
            "conservative_value": conservative.get("expected_value", 0),
            "conservative_risk_reduction": abs(current.get("volatility", 0) - conservative.get("volatility", 0)) * 100,
            
            # Aggressive approach
            "aggressive_equity": aggressive.get("equity_allocation", 80),
            "aggressive_success": aggressive.get("success_rate", 0) * 100,
            "aggressive_value": aggressive.get("expected_value", 0),
            "aggressive_risk_increase": abs(aggressive.get("volatility", 0) - current.get("volatility", 0)) * 100,
            
            # Optimal allocation
            "optimal_equity": simulation_result.optimal_allocation.get("equity", 60),
            "optimal_success": simulation_result.optimal_success_rate * 100,
            "optimal_value": simulation_result.optimal_expected_value,
            "sharpe_improvement": simulation_result.sharpe_ratio_improvement or 0,
            
            # Additional insights
            "additional_monthly": simulation_result.additional_monthly_needed or 0,
            "improvement_rate": simulation_result.improvement_with_additional * 100
        }
    
    def _generate_recommendations(self, simulation_result: SimulationResult) -> Dict[str, Any]:
        """Generate recommendation data based on simulation results."""
        # Calculate recommendations based on results
        current_success = simulation_result.success_probability
        target_success = 0.85  # Target 85% success rate
        
        # Determine recommended changes
        if current_success < target_success:
            additional_monthly = simulation_result.required_monthly_savings * 1.2
            improved_prob = min(current_success + 0.1, target_success)
        else:
            additional_monthly = simulation_result.required_monthly_savings
            improved_prob = current_success
        
        return {
            "recommended_equity": simulation_result.optimal_allocation.get("equity", 60),
            "recommended_bonds": simulation_result.optimal_allocation.get("bonds", 30),
            "return_improvement": 1.5,  # Placeholder
            "recommended_monthly": additional_monthly,
            "current_monthly": simulation_result.current_monthly_savings or 0,
            "additional_needed": max(0, additional_monthly - (simulation_result.current_monthly_savings or 0)),
            "current_prob": current_success * 100,
            "improved_prob": improved_prob * 100,
            "rebalance_months": 3,
            "deviation_threshold": 5,
            "cost_savings": 5000,  # Placeholder
            "tax_savings": 3000,  # Placeholder
            "insurance_gap": 100000,  # Placeholder
            "emergency_months": 6,
            "emergency_amount": simulation_result.emergency_fund_target or 30000
        }
    
    def _extract_risk_metrics(self, simulation_result: SimulationResult) -> Dict[str, Any]:
        """Extract risk metrics for risk assessment narrative."""
        return {
            "risk_profile": simulation_result.risk_profile or "Moderate",
            "volatility": simulation_result.volatility * 100,
            "max_drawdown": simulation_result.max_drawdown * 100,
            "var_95": simulation_result.value_at_risk_95 or 0,
            "crash_value": simulation_result.crash_scenario_value or 0,
            "recession_impact": simulation_result.recession_impact * 100,
            "recovery_months": simulation_result.expected_recovery_months or 18,
            "strategy_1": "Diversify across uncorrelated asset classes",
            "strategy_2": "Maintain 6-month emergency fund",
            "strategy_3": "Implement systematic rebalancing",
            "risk_alignment": self._assess_risk_alignment(simulation_result)
        }
    
    def _assess_risk_alignment(self, simulation_result: SimulationResult) -> str:
        """Assess if portfolio risk is aligned with user profile."""
        risk_score = simulation_result.volatility
        risk_profile = simulation_result.risk_profile or "Moderate"
        
        if risk_profile == "Conservative" and risk_score < 0.10:
            return "well-aligned"
        elif risk_profile == "Moderate" and 0.10 <= risk_score <= 0.20:
            return "well-aligned"
        elif risk_profile == "Aggressive" and risk_score > 0.20:
            return "well-aligned"
        else:
            return "misaligned - consider adjusting"
    
    async def create_goal_progress_narrative(
        self,
        financial_profile: FinancialProfile,
        goal_id: str,
        user_id: str,
        language: Language = Language.ENGLISH
    ) -> Dict[str, Any]:
        """Create narrative for goal progress tracking."""
        try:
            # Find the specific goal
            goal = next((g for g in financial_profile.goals if str(g.id) == goal_id), None)
            if not goal:
                raise ValueError(f"Goal {goal_id} not found")
            
            # Calculate progress metrics
            current_value = financial_profile.current_savings
            target_value = goal.target_amount
            time_remaining = (goal.target_date - datetime.utcnow()).days / 365.25
            progress_pct = (current_value / target_value * 100) if target_value > 0 else 0
            
            # Determine if on track
            required_monthly = (target_value - current_value) / (time_remaining * 12)
            current_monthly = financial_profile.monthly_savings
            on_track = current_monthly >= required_monthly
            
            # Prepare data for narrative
            goal_data = {
                "goal_name": goal.name,
                "goal_target": target_value,
                "current_progress": current_value,
                "progress_pct": progress_pct,
                "time_remaining": time_remaining,
                "on_track_status": "Yes" if on_track else "No",
                "required_monthly": required_monthly,
                "current_monthly": current_monthly,
                "contribution_gap": max(0, required_monthly - current_monthly),
                "best_case": target_value * 1.2,  # Placeholder
                "expected_case": target_value,
                "worst_case": target_value * 0.8,  # Placeholder
                "adjustment_message": "Increase monthly contributions" if not on_track else "Continue current strategy"
            }
            
            # Generate narrative
            request = NarrativeRequest(
                simulation_id=f"goal_{goal_id}",
                user_id=user_id,
                narrative_type=NarrativeType.GOAL_PROGRESS,
                language=language,
                data=goal_data,
                include_disclaimer=False
            )
            
            response = await self.narrative_generator.generate_narrative(request)
            
            return {
                "goal_id": goal_id,
                "goal_name": goal.name,
                "narrative": response.narrative,
                "metrics": goal_data,
                "on_track": on_track,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create goal progress narrative: {str(e)}")
            return {
                "goal_id": goal_id,
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def create_portfolio_review_narrative(
        self,
        portfolio_data: Dict[str, Any],
        user_id: str,
        language: Language = Language.ENGLISH
    ) -> Dict[str, Any]:
        """Create narrative for portfolio review."""
        try:
            # Extract portfolio metrics
            review_data = {
                "review_period": portfolio_data.get("period", "Last Quarter"),
                "start_value": portfolio_data.get("start_value", 0),
                "end_value": portfolio_data.get("end_value", 0),
                "net_change": portfolio_data.get("end_value", 0) - portfolio_data.get("start_value", 0),
                "change_pct": portfolio_data.get("return_pct", 0),
                "total_return": portfolio_data.get("total_return", 0),
                "annualized_return": portfolio_data.get("annualized_return", 0),
                "sharpe_ratio": portfolio_data.get("sharpe_ratio", 0),
                "alpha": portfolio_data.get("alpha", 0),
                "asset_performance_list": self._format_asset_performance(portfolio_data.get("assets", [])),
                "rebalancing_needed": "Yes" if portfolio_data.get("needs_rebalancing", False) else "No",
                "rebalancing_details": portfolio_data.get("rebalancing_details", "")
            }
            
            # Generate narrative
            request = NarrativeRequest(
                simulation_id=f"portfolio_review_{datetime.utcnow().strftime('%Y%m%d')}",
                user_id=user_id,
                narrative_type=NarrativeType.PORTFOLIO_REVIEW,
                language=language,
                data=review_data,
                include_disclaimer=True
            )
            
            response = await self.narrative_generator.generate_narrative(request)
            
            return {
                "narrative": response.narrative,
                "metrics": review_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create portfolio review narrative: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _format_asset_performance(self, assets: List[Dict[str, Any]]) -> str:
        """Format asset performance for narrative."""
        lines = []
        for asset in assets:
            name = asset.get("name", "Unknown")
            return_pct = asset.get("return", 0)
            weight = asset.get("weight", 0)
            lines.append(f"- {name}: {return_pct:.1f}% return ({weight:.0f}% of portfolio)")
        return "\n".join(lines) if lines else "No asset data available"
    
    async def batch_enhance_simulations(
        self,
        simulation_ids: List[str],
        user_id: str,
        language: Language = Language.ENGLISH
    ) -> List[Dict[str, Any]]:
        """Enhance multiple simulations in batch."""
        tasks = []
        for sim_id in simulation_ids:
            # In production, this would fetch the actual simulation result
            # For now, using placeholder
            simulation_result = SimulationResult(id=sim_id)  # Placeholder
            task = self.enhance_simulation_results(
                simulation_result,
                user_id,
                language,
                include_all_narratives=False
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to enhance simulation {simulation_ids[i]}: {str(result)}")
                successful_results.append({
                    "simulation_id": simulation_ids[i],
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        return successful_results