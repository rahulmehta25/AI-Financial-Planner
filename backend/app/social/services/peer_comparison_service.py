"""
Peer comparison service for demographic-based financial comparisons
"""

import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, case
from statistics import median, mean

from ..models.goal_sharing import PeerComparison, AgeGroup, IncomeRange
from ..models.user_social import UserSocialProfile
from ...models.user import User
from ...models.goal import Goal
from ...models.financial_profile import FinancialProfile
from .anonymization_service import AnonymizationService


class PeerComparisonService:
    """Service for privacy-preserving peer comparisons"""
    
    def __init__(self, db: Session):
        self.db = db
        self.anonymization_service = AnonymizationService(db)
        self.minimum_cohort_size = 10  # Minimum users for meaningful comparison
    
    def generate_peer_comparison(self, user_id: uuid.UUID, force_refresh: bool = False) -> Optional[PeerComparison]:
        """
        Generate comprehensive peer comparison for user
        """
        # Check if recent comparison exists
        if not force_refresh:
            recent_comparison = self.db.query(PeerComparison).filter(
                and_(
                    PeerComparison.user_id == user_id,
                    PeerComparison.comparison_date > datetime.utcnow() - timedelta(days=30)
                )
            ).first()
            
            if recent_comparison and recent_comparison.is_comparison_reliable():
                return recent_comparison
        
        # Get user's profile and financial data
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.financial_profile:
            return None
        
        user_profile = user.social_profile
        if not user_profile:
            return None
        
        # Determine user's cohort parameters
        cohort_params = self._get_user_cohort_parameters(user)
        if not cohort_params:
            return None
        
        # Find peer cohort
        peer_cohort = self._find_peer_cohort(user_id, cohort_params)
        
        if len(peer_cohort) < self.minimum_cohort_size:
            # Create comparison with insufficient data flag
            return self._create_insufficient_data_comparison(user_id, cohort_params, len(peer_cohort))
        
        # Calculate metrics and percentiles
        comparison_data = self._calculate_comparison_metrics(user, peer_cohort)
        
        # Generate insights and recommendations
        insights = self._generate_personalized_insights(comparison_data)
        
        # Create or update comparison record
        comparison = PeerComparison(
            user_id=user_id,
            cohort_age_group=cohort_params["age_group"],
            cohort_income_range=cohort_params["income_range"],
            cohort_location_region=cohort_params.get("region"),
            cohort_size=len(peer_cohort),
            **comparison_data,
            **insights,
            comparison_date=datetime.utcnow(),
            data_freshness_days=0,
            confidence_score=self._calculate_confidence_score(len(peer_cohort), comparison_data)
        )
        
        # Remove old comparisons for this user
        self.db.query(PeerComparison).filter(PeerComparison.user_id == user_id).delete()
        
        self.db.add(comparison)
        self.db.commit()
        
        return comparison
    
    def _get_user_cohort_parameters(self, user: User) -> Optional[Dict[str, Any]]:
        """Determine cohort parameters for user"""
        if not hasattr(user, 'birth_date') or not user.birth_date:
            return None
        
        age_group = self.anonymization_service.get_age_group(user.birth_date)
        if not age_group:
            return None
        
        # Get income from financial profile
        income_range = None
        if user.financial_profile and hasattr(user.financial_profile, 'annual_income'):
            income_range = self.anonymization_service.get_income_range(
                user.financial_profile.annual_income
            )
        
        # Get region from social profile
        region = None
        if user.social_profile and user.social_profile.location:
            region = self.anonymization_service.get_location_region(
                user.social_profile.location
            )
        
        return {
            "age_group": age_group,
            "income_range": income_range,
            "region": region
        }
    
    def _find_peer_cohort(self, user_id: uuid.UUID, cohort_params: Dict[str, Any]) -> List[User]:
        """Find users in the same demographic cohort"""
        
        # Start with basic age group matching
        base_query = self.db.query(User).join(
            UserSocialProfile, User.id == UserSocialProfile.user_id
        ).join(
            FinancialProfile, User.id == FinancialProfile.user_id, isouter=True
        ).filter(
            and_(
                User.id != user_id,  # Exclude the user themselves
                UserSocialProfile.is_active == True
            )
        )
        
        # Apply cohort filters with privacy settings
        cohort_users = []
        
        # Age group matching
        if cohort_params["age_group"]:
            # This would need to be implemented based on your User model structure
            # For now, we'll use a placeholder approach
            age_filtered_users = base_query.filter(
                # Add age filtering logic based on your User model
                User.id.isnot(None)  # Placeholder
            ).all()
            
            for user in age_filtered_users:
                if user.birth_date:
                    user_age_group = self.anonymization_service.get_age_group(user.birth_date)
                    if user_age_group == cohort_params["age_group"]:
                        # Check if user allows demographic comparisons
                        if (user.social_profile and user.social_profile.privacy_settings and
                            user.social_profile.privacy_settings.share_age_range):
                            cohort_users.append(user)
        
        return cohort_users
    
    def _calculate_comparison_metrics(self, user: User, peer_cohort: List[User]) -> Dict[str, float]:
        """Calculate user's percentile rankings within peer cohort"""
        
        metrics = {}
        
        # Collect peer data for comparison
        peer_data = {
            "savings_rates": [],
            "emergency_funds": [],
            "debt_ratios": [],
            "investment_allocations": [],
            "net_worths": [],
            "goal_completion_rates": [],
            "goal_progress_averages": []
        }
        
        # Extract data from peer cohort
        for peer in peer_cohort:
            if peer.financial_profile:
                fp = peer.financial_profile
                
                # Savings rate (if available)
                if hasattr(fp, 'monthly_income') and hasattr(fp, 'monthly_savings'):
                    if fp.monthly_income and fp.monthly_income > 0:
                        savings_rate = (fp.monthly_savings or 0) / fp.monthly_income * 100
                        peer_data["savings_rates"].append(savings_rate)
                
                # Emergency fund (if available)
                if hasattr(fp, 'emergency_fund_amount'):
                    peer_data["emergency_funds"].append(fp.emergency_fund_amount or 0)
                
                # Debt-to-income ratio
                if hasattr(fp, 'total_debt') and hasattr(fp, 'annual_income'):
                    if fp.annual_income and fp.annual_income > 0:
                        debt_ratio = (fp.total_debt or 0) / fp.annual_income * 100
                        peer_data["debt_ratios"].append(debt_ratio)
                
                # Net worth
                if hasattr(fp, 'net_worth'):
                    peer_data["net_worths"].append(fp.net_worth or 0)
            
            # Goal-related metrics
            user_goals = self.db.query(Goal).filter(Goal.user_id == peer.id).all()
            if user_goals:
                completed_goals = len([g for g in user_goals if g.is_achieved])
                completion_rate = (completed_goals / len(user_goals)) * 100
                peer_data["goal_completion_rates"].append(completion_rate)
                
                # Average progress across active goals
                active_goals = [g for g in user_goals if not g.is_achieved and g.target_amount > 0]
                if active_goals:
                    avg_progress = mean([
                        (g.current_amount / g.target_amount * 100) 
                        for g in active_goals
                    ])
                    peer_data["goal_progress_averages"].append(avg_progress)
        
        # Calculate user's own metrics
        user_metrics = self._extract_user_metrics(user)
        
        # Calculate percentiles for each metric
        for metric_name, peer_values in peer_data.items():
            if len(peer_values) >= self.minimum_cohort_size and metric_name in user_metrics:
                user_value = user_metrics[metric_name]
                if user_value is not None:
                    # For debt ratios, lower is better, so invert percentile
                    if metric_name == "debt_ratios":
                        percentile = self._calculate_percentile_rank(user_value, peer_values, reverse=True)
                    else:
                        percentile = self._calculate_percentile_rank(user_value, peer_values)
                    
                    # Map to database field names
                    field_mapping = {
                        "savings_rates": "savings_rate_percentile",
                        "emergency_funds": "emergency_fund_percentile",
                        "debt_ratios": "debt_to_income_percentile",
                        "investment_allocations": "investment_allocation_percentile",
                        "net_worths": "net_worth_percentile",
                        "goal_completion_rates": "goals_completion_rate_percentile",
                        "goal_progress_averages": "average_goal_progress_percentile"
                    }
                    
                    if metric_name in field_mapping:
                        metrics[field_mapping[metric_name]] = percentile
        
        return metrics
    
    def _extract_user_metrics(self, user: User) -> Dict[str, Optional[float]]:
        """Extract comparable metrics from user's financial profile"""
        metrics = {}
        
        if user.financial_profile:
            fp = user.financial_profile
            
            # Savings rate
            if hasattr(fp, 'monthly_income') and hasattr(fp, 'monthly_savings'):
                if fp.monthly_income and fp.monthly_income > 0:
                    metrics["savings_rates"] = (fp.monthly_savings or 0) / fp.monthly_income * 100
                else:
                    metrics["savings_rates"] = None
            
            # Emergency fund
            metrics["emergency_funds"] = getattr(fp, 'emergency_fund_amount', 0) or 0
            
            # Debt ratio
            if hasattr(fp, 'total_debt') and hasattr(fp, 'annual_income'):
                if fp.annual_income and fp.annual_income > 0:
                    metrics["debt_ratios"] = (fp.total_debt or 0) / fp.annual_income * 100
                else:
                    metrics["debt_ratios"] = None
            
            # Net worth
            metrics["net_worths"] = getattr(fp, 'net_worth', 0) or 0
        
        # Goal metrics
        user_goals = self.db.query(Goal).filter(Goal.user_id == user.id).all()
        if user_goals:
            completed_goals = len([g for g in user_goals if g.is_achieved])
            metrics["goal_completion_rates"] = (completed_goals / len(user_goals)) * 100
            
            active_goals = [g for g in user_goals if not g.is_achieved and g.target_amount > 0]
            if active_goals:
                metrics["goal_progress_averages"] = mean([
                    (g.current_amount / g.target_amount * 100) 
                    for g in active_goals
                ])
        
        return metrics
    
    def _calculate_percentile_rank(self, user_value: float, peer_values: List[float], 
                                 reverse: bool = False) -> float:
        """Calculate percentile rank of user value within peer group"""
        if not peer_values:
            return 50.0  # Default to median if no peer data
        
        # Add user value to the list for calculation
        all_values = peer_values + [user_value]
        all_values.sort(reverse=reverse)
        
        # Find user's rank
        user_rank = all_values.index(user_value) + 1
        
        # Calculate percentile (higher percentile = better performance, except for debt)
        percentile = ((len(all_values) - user_rank) / len(all_values)) * 100
        
        return round(percentile, 1)
    
    def _generate_personalized_insights(self, comparison_data: Dict[str, float]) -> Dict[str, Any]:
        """Generate personalized insights and recommendations"""
        
        insights = {
            "top_performing_behaviors": [],
            "improvement_suggestions": [],
            "similar_user_count": 0,
            "financial_discipline_score": 0.0,
            "learning_engagement_percentile": None
        }
        
        # Calculate overall financial discipline score
        discipline_components = []
        for metric, percentile in comparison_data.items():
            if percentile is not None and "percentile" in metric:
                # Weight different metrics differently
                if "savings_rate" in metric:
                    discipline_components.append(percentile * 0.3)
                elif "emergency_fund" in metric:
                    discipline_components.append(percentile * 0.25)
                elif "debt_to_income" in metric:
                    discipline_components.append(percentile * 0.25)
                elif "goal" in metric:
                    discipline_components.append(percentile * 0.2)
        
        if discipline_components:
            insights["financial_discipline_score"] = sum(discipline_components)
        
        # Generate improvement suggestions based on weak areas
        if comparison_data.get("savings_rate_percentile", 50) < 40:
            insights["improvement_suggestions"].append(
                "Consider automating your savings to improve your savings rate"
            )
        
        if comparison_data.get("emergency_fund_percentile", 50) < 30:
            insights["improvement_suggestions"].append(
                "Building a larger emergency fund could improve your financial security"
            )
        
        if comparison_data.get("debt_to_income_percentile", 50) < 40:
            insights["improvement_suggestions"].append(
                "Focus on debt reduction to improve your debt-to-income ratio"
            )
        
        if comparison_data.get("goals_completion_rate_percentile", 50) < 40:
            insights["improvement_suggestions"].append(
                "Try breaking large goals into smaller milestones to improve completion rates"
            )
        
        # Identify top performing behaviors
        for metric, percentile in comparison_data.items():
            if percentile and percentile >= 75:
                behavior_mapping = {
                    "savings_rate_percentile": "Consistent saving habits",
                    "emergency_fund_percentile": "Strong emergency preparedness",
                    "debt_to_income_percentile": "Effective debt management",
                    "goals_completion_rate_percentile": "Excellent goal achievement"
                }
                
                if metric in behavior_mapping:
                    insights["top_performing_behaviors"].append(behavior_mapping[metric])
        
        return insights
    
    def _calculate_confidence_score(self, cohort_size: int, metrics: Dict[str, float]) -> float:
        """Calculate confidence score for the comparison"""
        
        # Base confidence on cohort size
        size_confidence = min(cohort_size / 50.0, 1.0)  # Max confidence at 50+ peers
        
        # Adjust for data availability
        available_metrics = len([v for v in metrics.values() if v is not None])
        total_possible_metrics = 7  # Total number of comparison metrics
        data_confidence = available_metrics / total_possible_metrics
        
        # Combined confidence score
        return (size_confidence * 0.6 + data_confidence * 0.4) * 100
    
    def _create_insufficient_data_comparison(self, user_id: uuid.UUID, 
                                           cohort_params: Dict[str, Any], 
                                           actual_cohort_size: int) -> PeerComparison:
        """Create comparison record when insufficient peer data exists"""
        
        return PeerComparison(
            user_id=user_id,
            cohort_age_group=cohort_params["age_group"],
            cohort_income_range=cohort_params.get("income_range"),
            cohort_location_region=cohort_params.get("region"),
            cohort_size=actual_cohort_size,
            contains_insufficient_data=True,
            confidence_score=0.0,
            improvement_suggestions=["Join community discussions to help build peer comparison data"],
            comparison_date=datetime.utcnow(),
            data_freshness_days=0
        )
    
    def get_demographic_insights(self, age_group: Optional[str] = None,
                               income_range: Optional[str] = None,
                               region: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated insights for demographic groups"""
        
        # Build filter criteria
        filters = []
        if age_group:
            filters.append(PeerComparison.cohort_age_group == AgeGroup(age_group))
        if income_range:
            filters.append(PeerComparison.cohort_income_range == IncomeRange(income_range))
        if region:
            filters.append(PeerComparison.cohort_location_region == region)
        
        # Add data quality filters
        filters.extend([
            PeerComparison.contains_insufficient_data == False,
            PeerComparison.confidence_score >= 70,
            PeerComparison.comparison_date > datetime.utcnow() - timedelta(days=90)
        ])
        
        # Query for aggregate statistics
        comparisons = self.db.query(PeerComparison).filter(and_(*filters)).all()
        
        if len(comparisons) < 5:  # Minimum for meaningful insights
            return {"insufficient_data": True, "sample_size": len(comparisons)}
        
        # Calculate aggregate metrics
        metrics = {}
        metric_fields = [
            "savings_rate_percentile", "emergency_fund_percentile", 
            "debt_to_income_percentile", "goals_completion_rate_percentile",
            "financial_discipline_score"
        ]
        
        for field in metric_fields:
            values = [getattr(comp, field) for comp in comparisons if getattr(comp, field) is not None]
            if values:
                metrics[field] = {
                    "average": round(mean(values), 1),
                    "median": round(median(values), 1),
                    "sample_size": len(values)
                }
        
        # Common improvement areas
        all_suggestions = []
        for comp in comparisons:
            if comp.improvement_suggestions:
                all_suggestions.extend(comp.improvement_suggestions)
        
        # Count suggestion frequency
        suggestion_counts = {}
        for suggestion in all_suggestions:
            suggestion_counts[suggestion] = suggestion_counts.get(suggestion, 0) + 1
        
        top_suggestions = sorted(
            suggestion_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "demographic": {
                "age_group": age_group,
                "income_range": income_range,
                "region": region
            },
            "sample_size": len(comparisons),
            "metrics": metrics,
            "common_improvement_areas": [{"suggestion": s[0], "frequency": s[1]} for s in top_suggestions],
            "data_quality": {
                "average_confidence": round(mean([c.confidence_score for c in comparisons]), 1),
                "average_cohort_size": round(mean([c.cohort_size for c in comparisons]), 1)
            }
        }
    
    def get_user_comparison_trends(self, user_id: uuid.UUID, months: int = 12) -> Dict[str, Any]:
        """Get historical comparison trends for user"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
        
        comparisons = self.db.query(PeerComparison).filter(
            and_(
                PeerComparison.user_id == user_id,
                PeerComparison.comparison_date > cutoff_date
            )
        ).order_by(PeerComparison.comparison_date).all()
        
        if len(comparisons) < 2:
            return {"insufficient_data": True, "comparisons_count": len(comparisons)}
        
        # Track changes over time
        trends = {}
        metric_fields = [
            "savings_rate_percentile", "emergency_fund_percentile",
            "debt_to_income_percentile", "goals_completion_rate_percentile",
            "financial_discipline_score"
        ]
        
        for field in metric_fields:
            values = [(comp.comparison_date, getattr(comp, field)) 
                     for comp in comparisons if getattr(comp, field) is not None]
            
            if len(values) >= 2:
                # Calculate trend direction
                first_value = values[0][1]
                last_value = values[-1][1]
                change = last_value - first_value
                
                trends[field] = {
                    "trend_direction": "improving" if change > 5 else "declining" if change < -5 else "stable",
                    "change_amount": round(change, 1),
                    "current_percentile": round(last_value, 1),
                    "data_points": len(values)
                }
        
        return {
            "user_id": str(user_id),
            "time_period_months": months,
            "trends": trends,
            "latest_comparison_date": comparisons[-1].comparison_date.isoformat(),
            "improvement_areas": comparisons[-1].improvement_suggestions or []
        }