"""
Main recommendation engine that orchestrates all ML modules.

This engine provides a unified interface for:
- Goal optimization recommendations
- Portfolio rebalancing suggestions
- Risk tolerance predictions
- Behavioral insights
- Peer comparisons
- Savings strategies
- Life event predictions
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

from .goal_optimizer import GoalOptimizer
from .portfolio_rebalancer import PortfolioRebalancer
from .risk_predictor import RiskTolerancePredictor
from .behavioral_analyzer import BehavioralPatternAnalyzer
from .collaborative_filter import CollaborativeFilter
from .savings_strategist import SavingsStrategist
from .life_event_predictor import LifeEventPredictor
from .model_monitor import ModelMonitor

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Unified ML-powered recommendation engine for financial planning."""
    
    def __init__(self):
        # Initialize all ML modules
        self.goal_optimizer = GoalOptimizer()
        self.portfolio_rebalancer = PortfolioRebalancer()
        self.risk_predictor = RiskTolerancePredictor()
        self.behavioral_analyzer = BehavioralPatternAnalyzer()
        self.collaborative_filter = CollaborativeFilter()
        self.savings_strategist = SavingsStrategist()
        self.life_event_predictor = LifeEventPredictor()
        self.model_monitor = ModelMonitor()
        
        # Recommendation categories
        self.recommendation_categories = {
            'goal_optimization': 'Optimize your financial goals',
            'portfolio_rebalancing': 'Balance your investment portfolio',
            'risk_assessment': 'Understand your true risk tolerance',
            'behavioral_insights': 'Improve your financial habits',
            'peer_insights': 'Learn from similar users',
            'savings_strategy': 'Optimize your savings approach',
            'life_planning': 'Prepare for major life events'
        }
    
    async def generate_comprehensive_recommendations(self, user_id: str,
                                                   categories: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive recommendations across all categories."""
        try:
            # Default to all categories if none specified
            if categories is None:
                categories = list(self.recommendation_categories.keys())
            
            logger.info(f"Generating recommendations for user {user_id}, categories: {categories}")
            
            # Verify user exists
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
            
            # Generate recommendations concurrently
            recommendations = {}
            
            # Execute recommendations
            if 'goal_optimization' in categories:
                recommendations['goal_optimization'] = await self._get_goal_recommendations(user_id)
            
            if 'portfolio_rebalancing' in categories:
                recommendations['portfolio_rebalancing'] = await self._get_portfolio_recommendations(user_id)
            
            if 'risk_assessment' in categories:
                recommendations['risk_assessment'] = await self._get_risk_recommendations(user_id)
            
            if 'behavioral_insights' in categories:
                recommendations['behavioral_insights'] = await self._get_behavioral_recommendations(user_id)
            
            if 'peer_insights' in categories:
                recommendations['peer_insights'] = await self._get_peer_recommendations(user_id)
            
            if 'savings_strategy' in categories:
                recommendations['savings_strategy'] = await self._get_savings_recommendations(user_id)
            
            if 'life_planning' in categories:
                recommendations['life_planning'] = await self._get_life_event_recommendations(user_id)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(recommendations)
            
            # Prioritize recommendations
            prioritized_actions = self._prioritize_recommendations(recommendations)
            
            # Calculate overall financial health score
            financial_health_score = self._calculate_overall_health_score(recommendations)
            
            return {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'executive_summary': executive_summary,
                'financial_health_score': financial_health_score,
                'prioritized_actions': prioritized_actions,
                'recommendations': recommendations,
                'categories_analyzed': categories,
                'next_review_date': self._calculate_next_review_date(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive recommendations for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def _get_goal_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get goal optimization recommendations."""
        try:
            result = self.goal_optimizer.optimize_goals(user_id)
            
            # Add category metadata
            if 'error' not in result:
                result['category'] = 'goal_optimization'
                result['category_description'] = self.recommendation_categories['goal_optimization']
                result['priority'] = self._calculate_category_priority(result, 'goal_optimization')
            
            return result
        except Exception as e:
            logger.error(f"Failed to get goal recommendations: {e}")
            return {"error": str(e), "category": "goal_optimization"}
    
    async def _get_portfolio_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get portfolio rebalancing recommendations."""
        try:
            # Estimate portfolio value (in real implementation, this would come from investment data)
            portfolio_value = 100000  # Default value
            
            result = self.portfolio_rebalancer.generate_rebalancing_plan(user_id, portfolio_value)
            
            if 'error' not in result:
                result['category'] = 'portfolio_rebalancing'
                result['category_description'] = self.recommendation_categories['portfolio_rebalancing']
                result['priority'] = self._calculate_category_priority(result, 'portfolio_rebalancing')
            
            return result
        except Exception as e:
            logger.error(f"Failed to get portfolio recommendations: {e}")
            return {"error": str(e), "category": "portfolio_rebalancing"}
    
    async def _get_risk_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get risk tolerance recommendations."""
        try:
            result = self.risk_predictor.predict_actual_risk_tolerance(user_id)
            
            if 'error' not in result:
                # Also get risk capacity analysis
                capacity_analysis = self.risk_predictor.analyze_risk_capacity_vs_tolerance(user_id)
                result['risk_capacity_analysis'] = capacity_analysis
                
                result['category'] = 'risk_assessment'
                result['category_description'] = self.recommendation_categories['risk_assessment']
                result['priority'] = self._calculate_category_priority(result, 'risk_assessment')
            
            return result
        except Exception as e:
            logger.error(f"Failed to get risk recommendations: {e}")
            return {"error": str(e), "category": "risk_assessment"}
    
    async def _get_behavioral_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get behavioral pattern recommendations."""
        try:
            result = self.behavioral_analyzer.analyze_spending_patterns(user_id)
            
            if 'error' not in result:
                # Also get spending predictions
                predictions = self.behavioral_analyzer.predict_future_spending(user_id)
                result['spending_predictions'] = predictions
                
                result['category'] = 'behavioral_insights'
                result['category_description'] = self.recommendation_categories['behavioral_insights']
                result['priority'] = self._calculate_category_priority(result, 'behavioral_insights')
            
            return result
        except Exception as e:
            logger.error(f"Failed to get behavioral recommendations: {e}")
            return {"error": str(e), "category": "behavioral_insights"}
    
    async def _get_peer_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get peer comparison recommendations."""
        try:
            similar_users = self.collaborative_filter.find_similar_users(user_id)
            
            if 'error' not in similar_users:
                # Also get peer benchmarks
                benchmarks = self.collaborative_filter.get_peer_benchmarks(user_id)
                similar_users['peer_benchmarks'] = benchmarks
                
                similar_users['category'] = 'peer_insights'
                similar_users['category_description'] = self.recommendation_categories['peer_insights']
                similar_users['priority'] = self._calculate_category_priority(similar_users, 'peer_insights')
            
            return similar_users
        except Exception as e:
            logger.error(f"Failed to get peer recommendations: {e}")
            return {"error": str(e), "category": "peer_insights"}
    
    async def _get_savings_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get savings strategy recommendations."""
        try:
            result = self.savings_strategist.generate_savings_strategy(user_id)
            
            if 'error' not in result:
                result['category'] = 'savings_strategy'
                result['category_description'] = self.recommendation_categories['savings_strategy']
                result['priority'] = self._calculate_category_priority(result, 'savings_strategy')
            
            return result
        except Exception as e:
            logger.error(f"Failed to get savings recommendations: {e}")
            return {"error": str(e), "category": "savings_strategy"}
    
    async def _get_life_event_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Get life event predictions and recommendations."""
        try:
            result = self.life_event_predictor.predict_life_events(user_id)
            
            if 'error' not in result:
                result['category'] = 'life_planning'
                result['category_description'] = self.recommendation_categories['life_planning']
                result['priority'] = self._calculate_category_priority(result, 'life_planning')
            
            return result
        except Exception as e:
            logger.error(f"Failed to get life event recommendations: {e}")
            return {"error": str(e), "category": "life_planning"}
    
    def _calculate_category_priority(self, recommendation: Dict[str, Any], 
                                   category: str) -> str:
        """Calculate priority level for a recommendation category."""
        try:
            if 'error' in recommendation:
                return 'low'
            
            # Category-specific priority logic
            if category == 'goal_optimization':
                total_recommendations = len(recommendation.get('recommendations', []))
                if total_recommendations >= 3:
                    return 'high'
                elif total_recommendations >= 1:
                    return 'medium'
                else:
                    return 'low'
            
            elif category == 'portfolio_rebalancing':
                drift_analysis = recommendation.get('drift_analysis', {})
                if drift_analysis.get('rebalancing_needed', False):
                    return 'high'
                else:
                    return 'medium'
            
            elif category == 'risk_assessment':
                discrepancy = recommendation.get('discrepancy_analysis', {})
                if discrepancy.get('has_discrepancy', False):
                    severity = discrepancy.get('severity', 'low')
                    return 'high' if severity == 'high' else 'medium'
                else:
                    return 'low'
            
            elif category == 'behavioral_insights':
                efficiency = recommendation.get('spending_efficiency', {})
                score = efficiency.get('efficiency_score', 50)
                if score < 50:
                    return 'high'
                elif score < 70:
                    return 'medium'
                else:
                    return 'low'
            
            elif category == 'peer_insights':
                improvement_areas = recommendation.get('peer_benchmarks', {}).get('improvement_areas', [])
                if len(improvement_areas) >= 3:
                    return 'high'
                elif len(improvement_areas) >= 1:
                    return 'medium'
                else:
                    return 'low'
            
            elif category == 'savings_strategy':
                success_prob = recommendation.get('success_probability', {}).get('overall_probability', 0.5)
                if success_prob < 0.5:
                    return 'high'
                elif success_prob < 0.8:
                    return 'medium'
                else:
                    return 'low'
            
            elif category == 'life_planning':
                insights = recommendation.get('planning_insights', {})
                major_events = insights.get('major_upcoming_events', [])
                if len(major_events) >= 2:
                    return 'high'
                elif len(major_events) >= 1:
                    return 'medium'
                else:
                    return 'low'
            
            return 'medium'  # Default
            
        except Exception as e:
            logger.error(f"Failed to calculate priority for {category}: {e}")
            return 'low'
    
    def _generate_executive_summary(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of all recommendations."""
        summary = {
            'key_insights': [],
            'critical_actions': [],
            'opportunities': [],
            'overall_assessment': 'good'
        }
        
        try:
            critical_count = 0
            opportunity_count = 0
            
            for category, data in recommendations.items():
                if 'error' in data:
                    continue
                
                priority = data.get('priority', 'low')
                
                if priority == 'high':
                    critical_count += 1
                    # Extract key critical action
                    if category == 'goal_optimization':
                        if data.get('recommendations'):
                            summary['critical_actions'].append(
                                f"Optimize goal allocation: {len(data['recommendations'])} goals need attention"
                            )
                    elif category == 'portfolio_rebalancing':
                        if data.get('drift_analysis', {}).get('rebalancing_needed'):
                            summary['critical_actions'].append(
                                "Portfolio rebalancing required due to significant drift"
                            )
                    elif category == 'behavioral_insights':
                        efficiency = data.get('spending_efficiency', {}).get('efficiency_score', 50)
                        if efficiency < 50:
                            summary['critical_actions'].append(
                                f"Improve spending efficiency (current score: {efficiency:.0f}/100)"
                            )
                
                elif priority == 'medium':
                    opportunity_count += 1
                    # Extract opportunities
                    if category == 'savings_strategy':
                        optimal_rate = data.get('optimal_savings_rate', {}).get('target_rate', 0)
                        if optimal_rate > 0.15:
                            summary['opportunities'].append(
                                f"Increase savings rate to {optimal_rate:.1%} for better goal achievement"
                            )
                    elif category == 'peer_insights':
                        improvement_areas = data.get('peer_benchmarks', {}).get('improvement_areas', [])
                        if improvement_areas:
                            summary['opportunities'].append(
                                f"Benchmark improvements available in {len(improvement_areas)} areas"
                            )
            
            # Generate key insights
            if critical_count > 0:
                summary['key_insights'].append(f"{critical_count} areas require immediate attention")
            
            if opportunity_count > 0:
                summary['key_insights'].append(f"{opportunity_count} opportunities for improvement identified")
            
            # Assess overall financial health
            if critical_count >= 3:
                summary['overall_assessment'] = 'needs_improvement'
            elif critical_count >= 1:
                summary['overall_assessment'] = 'fair'
            elif opportunity_count >= 2:
                summary['overall_assessment'] = 'good'
            else:
                summary['overall_assessment'] = 'excellent'
            
            # Add general insights
            if 'life_planning' in recommendations:
                life_data = recommendations['life_planning']
                if not life_data.get('error'):
                    major_events = life_data.get('planning_insights', {}).get('major_upcoming_events', [])
                    if major_events:
                        summary['key_insights'].append(
                            f"Prepare for {len(major_events)} potential life events"
                        )
            
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            summary['error'] = str(e)
        
        return summary
    
    def _prioritize_recommendations(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize recommendations across all categories."""
        prioritized_actions = []
        
        try:
            # Collect all recommendations with priorities
            for category, data in recommendations.items():
                if 'error' in data:
                    continue
                
                priority = data.get('priority', 'low')
                category_desc = data.get('category_description', category)
                
                # Extract specific actions
                actions = self._extract_actionable_items(category, data)
                
                for action in actions:
                    prioritized_actions.append({
                        'category': category,
                        'category_description': category_desc,
                        'action': action,
                        'priority': priority,
                        'estimated_impact': self._estimate_action_impact(category, action),
                        'effort_level': self._estimate_effort_level(category, action)
                    })
            
            # Sort by priority (high -> medium -> low) and impact
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            impact_order = {'high': 3, 'medium': 2, 'low': 1}
            
            prioritized_actions.sort(
                key=lambda x: (
                    priority_order.get(x['priority'], 0),
                    impact_order.get(x['estimated_impact'], 0)
                ),
                reverse=True
            )
            
            # Return top 10 actions
            return prioritized_actions[:10]
            
        except Exception as e:
            logger.error(f"Failed to prioritize recommendations: {e}")
            return []
    
    def _extract_actionable_items(self, category: str, data: Dict[str, Any]) -> List[str]:
        """Extract actionable items from category recommendations."""
        actions = []
        
        try:
            if category == 'goal_optimization':
                recommendations = data.get('recommendations', [])
                for rec in recommendations[:3]:  # Top 3
                    if rec.get('reasoning'):
                        actions.extend(rec['reasoning'][:1])  # First reason
            
            elif category == 'portfolio_rebalancing':
                rebalancing_actions = data.get('rebalancing_actions', [])
                for action in rebalancing_actions[:2]:  # Top 2
                    asset = action.get('asset', 'portfolio')
                    action_type = action.get('action', 'rebalance')
                    amount = action.get('dollar_amount', 0)
                    actions.append(f"{action_type.title()} {asset}: ${amount:,.0f}")
            
            elif category == 'risk_assessment':
                recommendations = data.get('recommendations', [])
                actions.extend(recommendations[:2])  # Top 2
            
            elif category == 'behavioral_insights':
                behavioral_recs = data.get('behavioral_recommendations', [])
                actions.extend(behavioral_recs[:2])  # Top 2
            
            elif category == 'peer_insights':
                peer_recs = data.get('recommendations', [])
                actions.extend(peer_recs[:2])  # Top 2
            
            elif category == 'savings_strategy':
                behavioral_tips = data.get('behavioral_recommendations', [])
                actions.extend(behavioral_tips[:2])  # Top 2
            
            elif category == 'life_planning':
                priority_actions = data.get('planning_insights', {}).get('priority_actions', [])
                actions.extend(priority_actions[:2])  # Top 2
            
            return actions[:3]  # Max 3 actions per category
            
        except Exception as e:
            logger.error(f"Failed to extract actions for {category}: {e}")
            return []
    
    def _estimate_action_impact(self, category: str, action: str) -> str:
        """Estimate the potential impact of an action."""
        # Simple heuristic-based impact estimation
        high_impact_keywords = ['emergency', 'debt', 'rebalance', 'critical', 'immediate']
        medium_impact_keywords = ['increase', 'improve', 'optimize', 'review']
        
        action_lower = action.lower()
        
        if any(keyword in action_lower for keyword in high_impact_keywords):
            return 'high'
        elif any(keyword in action_lower for keyword in medium_impact_keywords):
            return 'medium'
        else:
            return 'low'
    
    def _estimate_effort_level(self, category: str, action: str) -> str:
        """Estimate the effort required for an action."""
        # Simple heuristic-based effort estimation
        high_effort_keywords = ['rebalance', 'optimize', 'restructure', 'overhaul']
        low_effort_keywords = ['review', 'consider', 'monitor', 'track']
        
        action_lower = action.lower()
        
        if any(keyword in action_lower for keyword in high_effort_keywords):
            return 'high'
        elif any(keyword in action_lower for keyword in low_effort_keywords):
            return 'low'
        else:
            return 'medium'
    
    def _calculate_overall_health_score(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall financial health score."""
        try:
            scores = []
            category_scores = {}
            
            # Extract scores from each category
            for category, data in recommendations.items():
                if 'error' in data:
                    continue
                
                category_score = 50  # Default neutral score
                
                if category == 'goal_optimization':
                    optimization_score = data.get('optimization_score', 50)
                    category_score = optimization_score
                
                elif category == 'behavioral_insights':
                    efficiency_score = data.get('spending_efficiency', {}).get('efficiency_score', 50)
                    category_score = efficiency_score
                
                elif category == 'savings_strategy':
                    success_prob = data.get('success_probability', {}).get('overall_probability', 0.5)
                    category_score = success_prob * 100
                
                elif category == 'life_planning':
                    readiness_score = data.get('planning_insights', {}).get('financial_readiness_score', 0.5)
                    category_score = readiness_score * 100
                
                elif category == 'risk_assessment':
                    confidence = data.get('confidence', 0.5)
                    has_discrepancy = data.get('discrepancy_analysis', {}).get('has_discrepancy', False)
                    category_score = (confidence * 100) if not has_discrepancy else 60
                
                scores.append(category_score)
                category_scores[category] = category_score
            
            overall_score = sum(scores) / len(scores) if scores else 50
            
            # Determine health level
            if overall_score >= 80:
                health_level = 'excellent'
            elif overall_score >= 70:
                health_level = 'good'
            elif overall_score >= 60:
                health_level = 'fair'
            else:
                health_level = 'needs_improvement'
            
            return {
                'overall_score': round(overall_score, 1),
                'health_level': health_level,
                'category_scores': {k: round(v, 1) for k, v in category_scores.items()},
                'areas_of_strength': [
                    cat for cat, score in category_scores.items() if score >= 75
                ],
                'areas_for_improvement': [
                    cat for cat, score in category_scores.items() if score < 60
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return {
                'overall_score': 50,
                'health_level': 'unknown',
                'error': str(e)
            }
    
    def _calculate_next_review_date(self, recommendations: Dict[str, Any]) -> str:
        """Calculate when the next review should occur."""
        try:
            # Base review frequency on priority and category
            min_days = 365  # Default to annual review
            
            for category, data in recommendations.items():
                if 'error' in data:
                    continue
                
                priority = data.get('priority', 'low')
                
                if priority == 'high':
                    min_days = min(min_days, 30)  # Monthly for high priority
                elif priority == 'medium':
                    min_days = min(min_days, 90)  # Quarterly for medium priority
                else:
                    min_days = min(min_days, 180)  # Semi-annual for low priority
            
            next_review = datetime.now().timestamp() + (min_days * 24 * 60 * 60)
            return datetime.fromtimestamp(next_review).isoformat()
            
        except Exception as e:
            logger.error(f"Failed to calculate next review date: {e}")
            # Default to 3 months
            next_review = datetime.now().timestamp() + (90 * 24 * 60 * 60)
            return datetime.fromtimestamp(next_review).isoformat()
    
    def train_all_models(self, retrain: bool = False) -> Dict[str, Any]:
        """Train all ML models."""
        try:
            training_results = {}
            
            # Train each model
            models_to_train = [
                ('goal_optimizer', self.goal_optimizer),
                ('risk_predictor', self.risk_predictor),
                ('collaborative_filter', self.collaborative_filter),
                ('life_event_predictor', self.life_event_predictor)
            ]
            
            for model_name, model_instance in models_to_train:
                try:
                    logger.info(f"Training {model_name}...")
                    
                    if hasattr(model_instance, 'train_models'):
                        result = model_instance.train_models(retrain=retrain)
                    elif hasattr(model_instance, 'train_risk_prediction_model'):
                        result = model_instance.train_risk_prediction_model(retrain=retrain)
                    elif hasattr(model_instance, 'train_collaborative_models'):
                        result = model_instance.train_collaborative_models(retrain=retrain)
                    elif hasattr(model_instance, 'train_life_event_models'):
                        result = model_instance.train_life_event_models(retrain=retrain)
                    else:
                        result = {"message": "No training method available"}
                    
                    training_results[model_name] = result
                    logger.info(f"Completed training {model_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to train {model_name}: {e}")
                    training_results[model_name] = {"error": str(e)}
            
            return {
                'training_completed': datetime.now().isoformat(),
                'models_trained': len([r for r in training_results.values() if 'error' not in r]),
                'models_failed': len([r for r in training_results.values() if 'error' in r]),
                'results': training_results
            }
            
        except Exception as e:
            logger.error(f"Failed to train all models: {e}")
            return {"error": str(e)}
    
    def get_recommendation_status(self) -> Dict[str, Any]:
        """Get status of all recommendation modules."""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'modules': {},
                'overall_health': 'healthy'
            }
            
            modules = [
                ('goal_optimizer', self.goal_optimizer),
                ('portfolio_rebalancer', self.portfolio_rebalancer),
                ('risk_predictor', self.risk_predictor),
                ('behavioral_analyzer', self.behavioral_analyzer),
                ('collaborative_filter', self.collaborative_filter),
                ('savings_strategist', self.savings_strategist),
                ('life_event_predictor', self.life_event_predictor)
            ]
            
            unhealthy_modules = 0
            
            for module_name, module_instance in modules:
                try:
                    # Basic health check - verify models are loaded
                    module_status = {
                        'status': 'healthy',
                        'models_loaded': 0,
                        'last_training': 'unknown'
                    }
                    
                    # Count loaded models
                    for attr_name in dir(module_instance):
                        attr = getattr(module_instance, attr_name)
                        if hasattr(attr, 'predict') or hasattr(attr, 'fit') or hasattr(attr, 'transform'):
                            if attr is not None:
                                module_status['models_loaded'] += 1
                    
                    if module_status['models_loaded'] == 0:
                        module_status['status'] = 'no_models'
                        unhealthy_modules += 1
                    
                    status['modules'][module_name] = module_status
                    
                except Exception as e:
                    status['modules'][module_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    unhealthy_modules += 1
            
            # Determine overall health
            if unhealthy_modules > len(modules) * 0.5:
                status['overall_health'] = 'critical'
            elif unhealthy_modules > 0:
                status['overall_health'] = 'degraded'
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get recommendation status: {e}")
            return {"error": str(e)}