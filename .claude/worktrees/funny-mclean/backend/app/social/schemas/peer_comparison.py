"""
Schemas for peer comparison and demographic insights
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from .social_base import SocialBaseResponse


class PeerComparisonResponse(SocialBaseResponse):
    """Response schema for peer comparison data"""
    
    # Cohort information
    cohort_age_group: Optional[str] = None
    cohort_income_range: Optional[str] = None
    cohort_location_region: Optional[str] = None
    cohort_size: int
    
    # Financial metrics percentiles (0-100, higher is better except debt)
    savings_rate_percentile: Optional[float] = None
    emergency_fund_percentile: Optional[float] = None
    debt_to_income_percentile: Optional[float] = None  # Higher = better (lower debt)
    investment_allocation_percentile: Optional[float] = None
    net_worth_percentile: Optional[float] = None
    
    # Goal progress comparisons
    goals_completion_rate_percentile: Optional[float] = None
    average_goal_progress_percentile: Optional[float] = None
    
    # Behavioral metrics
    financial_discipline_score: Optional[float] = None  # 0-100 composite score
    learning_engagement_percentile: Optional[float] = None
    
    # Insights and recommendations
    top_performing_behaviors: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    similar_user_count: Optional[int] = None
    
    # Comparison metadata
    comparison_date: datetime
    data_freshness_days: int
    confidence_score: Optional[float] = None  # 0-100
    
    # Data quality indicators
    contains_insufficient_data: bool = False
    privacy_protection_applied: bool = True
    
    class Config:
        from_attributes = True


class MetricPerformance(BaseModel):
    """Performance info for a specific metric"""
    
    percentile: Optional[float] = None
    performance_level: str  # "top performer", "above average", etc.
    improvement_potential: Optional[str] = None
    
    class Config:
        from_attributes = True


class PeerComparisonInsights(BaseModel):
    """Detailed insights from peer comparison"""
    
    overall_financial_health: str  # "excellent", "good", "fair", "needs improvement"
    overall_percentile: float  # Weighted average across metrics
    
    # Performance breakdown by category
    savings_performance: MetricPerformance
    debt_management: MetricPerformance
    goal_achievement: MetricPerformance
    investment_behavior: MetricPerformance
    
    # Personalized recommendations
    top_3_priorities: List[str]
    quick_wins: List[str]  # Easy improvements
    long_term_goals: List[str]  # Bigger improvements
    
    # Peer learning opportunities
    successful_peer_strategies: List[str]
    common_peer_mistakes: List[str]
    
    class Config:
        from_attributes = True


class DemographicMetric(BaseModel):
    """Aggregated metric for demographic group"""
    
    average: float
    median: float
    sample_size: int
    
    class Config:
        from_attributes = True


class DemographicInsightsResponse(BaseModel):
    """Response schema for demographic group insights"""
    
    demographic: Dict[str, Optional[str]]  # age_group, income_range, region
    sample_size: int
    
    # Aggregated metrics for this demographic
    metrics: Dict[str, DemographicMetric]
    
    # Common challenges and opportunities
    common_improvement_areas: List[Dict[str, Any]]  # suggestion + frequency
    top_performing_behaviors: List[str]
    
    # Data quality information
    data_quality: Dict[str, float]  # average_confidence, average_cohort_size
    
    # Demographic-specific insights
    demographic_trends: Optional[Dict[str, Any]] = None
    benchmark_comparisons: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ComparisonTrendPoint(BaseModel):
    """Single point in comparison trend data"""
    
    date: datetime
    percentile: float
    cohort_size: int
    confidence_score: float
    
    class Config:
        from_attributes = True


class MetricTrend(BaseModel):
    """Trend data for a specific metric"""
    
    metric_name: str
    trend_direction: str  # "improving", "declining", "stable"
    change_amount: float  # Percentile point change
    current_percentile: float
    data_points: int
    trend_data: List[ComparisonTrendPoint]
    
    class Config:
        from_attributes = True


class UserComparisonTrendsResponse(BaseModel):
    """Response schema for user's comparison trends over time"""
    
    user_id: UUID
    time_period_months: int
    
    # Trend analysis for each metric
    trends: Dict[str, Dict[str, Any]]  # metric_name -> trend_info
    
    # Overall trajectory
    overall_trajectory: str  # "improving", "declining", "mixed", "stable"
    most_improved_area: Optional[str] = None
    area_needing_attention: Optional[str] = None
    
    # Latest comparison info
    latest_comparison_date: datetime
    current_improvement_areas: List[str]
    
    # Progress milestones
    milestones_achieved: List[str]
    upcoming_milestones: List[str]
    
    class Config:
        from_attributes = True


class ComparisonFilters(BaseModel):
    """Filters for peer comparison queries"""
    
    age_group: Optional[str] = None
    income_range: Optional[str] = None
    region: Optional[str] = None
    minimum_cohort_size: int = Field(default=10, ge=5)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


class ComparisonRefreshRequest(BaseModel):
    """Request to refresh peer comparison data"""
    
    force_refresh: bool = False
    include_historical: bool = True
    
    class Config:
        from_attributes = True


class BenchmarkComparison(BaseModel):
    """Comparison against financial benchmarks"""
    
    metric_name: str
    user_value: Optional[float] = None
    user_percentile: Optional[float] = None
    recommended_target: Optional[float] = None
    national_average: Optional[float] = None
    peer_group_average: Optional[float] = None
    
    # Interpretation
    performance_rating: str  # "excellent", "good", "fair", "poor"
    gap_to_target: Optional[float] = None
    improvement_timeline: Optional[str] = None  # "short-term", "medium-term", "long-term"
    
    class Config:
        from_attributes = True


class BenchmarkComparisonResponse(BaseModel):
    """Response with benchmark comparisons"""
    
    user_id: UUID
    comparison_date: datetime
    
    # Individual benchmark comparisons
    savings_rate: BenchmarkComparison
    emergency_fund: BenchmarkComparison
    debt_ratio: BenchmarkComparison
    retirement_savings: BenchmarkComparison
    
    # Overall assessment
    overall_score: float  # 0-100
    financial_wellness_grade: str  # A, B, C, D, F
    
    # Recommendations based on benchmarks
    priority_improvements: List[str]
    celebration_worthy: List[str]  # Areas where user excels
    
    class Config:
        from_attributes = True