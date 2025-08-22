"""
Behavioral pattern analysis for spending and saving habits.

This module analyzes user financial behavior patterns to:
- Identify spending categories and trends
- Detect behavioral biases
- Predict future spending patterns
- Recommend behavioral interventions
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import xgboost as xgb
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.time_series import seasonal_decompose
import scipy.stats as stats
import joblib
import json
from pathlib import Path

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class BehavioralPatternAnalyzer:
    """Advanced behavioral pattern analysis for financial habits."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/ml/models/behavioral_analyzer"
        self.spending_classifier = None
        self.behavior_clusterer = None
        self.trend_predictor = None
        self.bias_detector = None
        self.scaler = StandardScaler()
        
        # Behavioral patterns and biases
        self.spending_categories = [
            'housing', 'transportation', 'food', 'healthcare', 'entertainment',
            'shopping', 'utilities', 'insurance', 'debt_payments', 'savings'
        ]
        
        self.behavioral_biases = [
            'loss_aversion', 'present_bias', 'overconfidence', 'anchoring',
            'mental_accounting', 'herd_behavior', 'confirmation_bias'
        ]
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load pre-trained behavioral analysis models."""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists():
                self.spending_classifier = joblib.load(model_dir / "spending_classifier.pkl")
                self.behavior_clusterer = joblib.load(model_dir / "behavior_clusterer.pkl")
                self.trend_predictor = joblib.load(model_dir / "trend_predictor.pkl")
                self.bias_detector = joblib.load(model_dir / "bias_detector.pkl")
                self.scaler = joblib.load(model_dir / "scaler.pkl")
                logger.info("Loaded pre-trained behavioral analysis models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _save_models(self) -> None:
        """Save trained models."""
        try:
            model_dir = Path(self.model_path)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            if self.spending_classifier:
                joblib.dump(self.spending_classifier, model_dir / "spending_classifier.pkl")
            if self.behavior_clusterer:
                joblib.dump(self.behavior_clusterer, model_dir / "behavior_clusterer.pkl")
            if self.trend_predictor:
                joblib.dump(self.trend_predictor, model_dir / "trend_predictor.pkl")
            if self.bias_detector:
                joblib.dump(self.bias_detector, model_dir / "bias_detector.pkl")
            
            joblib.dump(self.scaler, model_dir / "scaler.pkl")
            logger.info("Saved behavioral analysis models")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def analyze_spending_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's spending patterns and behavior."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                # Extract spending data (in real implementation, this would come from transactions)
                spending_data = self._extract_spending_data(user.financial_profile)
                
                # Analyze patterns
                pattern_analysis = {
                    'spending_breakdown': self._analyze_spending_breakdown(spending_data),
                    'temporal_patterns': self._analyze_temporal_patterns(spending_data),
                    'behavioral_insights': self._identify_behavioral_patterns(spending_data),
                    'comparison_metrics': self._calculate_comparison_metrics(user.financial_profile),
                    'spending_efficiency': self._calculate_spending_efficiency(user.financial_profile),
                    'recommendations': []
                }
                
                # Generate personalized recommendations
                pattern_analysis['recommendations'] = self._generate_behavioral_recommendations(
                    pattern_analysis, user.financial_profile
                )
                
                return pattern_analysis
                
        except Exception as e:
            logger.error(f"Failed to analyze spending patterns for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _extract_spending_data(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Extract and simulate spending data from financial profile."""
        # In real implementation, this would connect to transaction data
        # For now, we'll use the expense breakdown from the profile
        
        monthly_expenses = float(profile.monthly_expenses)
        expense_breakdown = profile.expense_breakdown or {}
        
        # If no breakdown available, use typical percentages
        if not expense_breakdown:
            typical_breakdown = {
                'housing': 0.30,
                'transportation': 0.15,
                'food': 0.12,
                'utilities': 0.08,
                'healthcare': 0.08,
                'entertainment': 0.05,
                'shopping': 0.10,
                'insurance': 0.05,
                'other': 0.07
            }
            expense_breakdown = {k: v * monthly_expenses for k, v in typical_breakdown.items()}
        
        # Generate synthetic time series data for demonstration
        months = 12
        spending_history = []
        
        for i in range(months):
            month_data = {}
            for category, base_amount in expense_breakdown.items():
                # Add some realistic variation
                seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 12)  # Seasonal variation
                random_factor = np.random.normal(1, 0.1)  # Random variation
                month_data[category] = base_amount * seasonal_factor * random_factor
            
            spending_history.append({
                'month': i,
                'date': datetime.now() - timedelta(days=30*i),
                'categories': month_data,
                'total': sum(month_data.values())
            })
        
        return {
            'history': spending_history,
            'monthly_average': monthly_expenses,
            'categories': list(expense_breakdown.keys())
        }
    
    def _analyze_spending_breakdown(self, spending_data: Dict) -> Dict[str, Any]:
        """Analyze spending breakdown by category."""
        history = spending_data['history']
        categories = spending_data['categories']
        
        breakdown = {}
        
        for category in categories:
            amounts = [month['categories'].get(category, 0) for month in history]
            
            breakdown[category] = {
                'average_monthly': np.mean(amounts),
                'percentage_of_total': np.mean(amounts) / spending_data['monthly_average'] * 100,
                'volatility': np.std(amounts) / np.mean(amounts) if np.mean(amounts) > 0 else 0,
                'trend': self._calculate_trend(amounts),
                'seasonal_pattern': self._detect_seasonal_pattern(amounts)
            }
        
        # Identify top spending categories
        top_categories = sorted(breakdown.items(), 
                              key=lambda x: x[1]['average_monthly'], 
                              reverse=True)[:5]
        
        return {
            'category_breakdown': breakdown,
            'top_categories': [cat[0] for cat in top_categories],
            'spending_diversity': self._calculate_spending_diversity(breakdown),
            'fixed_vs_variable': self._classify_fixed_variable_expenses(breakdown)
        }
    
    def _analyze_temporal_patterns(self, spending_data: Dict) -> Dict[str, Any]:
        """Analyze temporal spending patterns."""
        history = spending_data['history']
        monthly_totals = [month['total'] for month in history]
        
        patterns = {
            'monthly_trend': self._calculate_trend(monthly_totals),
            'volatility': np.std(monthly_totals) / np.mean(monthly_totals),
            'seasonality': self._detect_seasonal_pattern(monthly_totals),
            'spending_rhythm': self._analyze_spending_rhythm(history),
            'trend_analysis': {
                'direction': 'increasing' if self._calculate_trend(monthly_totals) > 0.02 else 
                           'decreasing' if self._calculate_trend(monthly_totals) < -0.02 else 'stable',
                'rate_of_change': self._calculate_trend(monthly_totals)
            }
        }
        
        return patterns
    
    def _identify_behavioral_patterns(self, spending_data: Dict) -> Dict[str, Any]:
        """Identify behavioral patterns and potential biases."""
        patterns = {
            'impulse_spending_score': self._calculate_impulse_score(spending_data),
            'budget_adherence_score': self._calculate_budget_adherence(spending_data),
            'seasonal_spending_bias': self._detect_seasonal_bias(spending_data),
            'category_anchoring': self._detect_category_anchoring(spending_data),
            'spending_consistency': self._calculate_spending_consistency(spending_data),
            'lifestyle_inflation': self._detect_lifestyle_inflation(spending_data)
        }
        
        return patterns
    
    def _calculate_comparison_metrics(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Calculate spending metrics compared to benchmarks."""
        annual_income = float(profile.annual_income)
        monthly_expenses = float(profile.monthly_expenses)
        
        # National averages by income bracket (approximate)
        income_bracket = self._get_income_bracket(annual_income)
        benchmark_ratios = self._get_benchmark_spending_ratios(income_bracket)
        
        user_breakdown = profile.expense_breakdown or {}
        comparison = {}
        
        for category, benchmark_ratio in benchmark_ratios.items():
            user_amount = user_breakdown.get(category, 0)
            user_ratio = user_amount / annual_income if annual_income > 0 else 0
            
            comparison[category] = {
                'user_ratio': user_ratio,
                'benchmark_ratio': benchmark_ratio,
                'difference': user_ratio - benchmark_ratio,
                'status': 'above_average' if user_ratio > benchmark_ratio * 1.1 else
                         'below_average' if user_ratio < benchmark_ratio * 0.9 else 'average'
            }
        
        return {
            'category_comparison': comparison,
            'overall_spending_ratio': monthly_expenses * 12 / annual_income,
            'savings_rate': max(0, (annual_income - monthly_expenses * 12) / annual_income),
            'income_bracket': income_bracket
        }
    
    def _calculate_spending_efficiency(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Calculate spending efficiency metrics."""
        annual_income = float(profile.annual_income)
        monthly_expenses = float(profile.monthly_expenses)
        net_worth = profile.net_worth
        
        efficiency = {
            'expense_ratio': monthly_expenses * 12 / annual_income,
            'net_worth_to_income': net_worth / annual_income if annual_income > 0 else 0,
            'debt_to_income': profile.debt_to_income_ratio,
            'housing_affordability': self._calculate_housing_affordability(profile),
            'emergency_fund_coverage': self._calculate_emergency_coverage(profile),
            'efficiency_score': 0  # Will be calculated below
        }
        
        # Calculate overall efficiency score (0-100)
        score_components = [
            max(0, 100 - efficiency['expense_ratio'] * 100),  # Lower expense ratio is better
            min(100, efficiency['net_worth_to_income'] * 10),  # Higher net worth is better
            max(0, 100 - efficiency['debt_to_income'] * 200),  # Lower debt is better
            min(100, efficiency['emergency_fund_coverage'] * 20)  # More coverage is better
        ]
        
        efficiency['efficiency_score'] = np.mean(score_components)
        
        return efficiency
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend using linear regression slope."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        slope, _, _, _, _ = stats.linregress(x, values)
        return slope / np.mean(values) if np.mean(values) != 0 else 0
    
    def _detect_seasonal_pattern(self, values: List[float]) -> Dict[str, Any]:
        """Detect seasonal patterns in spending."""
        if len(values) < 12:
            return {'has_pattern': False, 'strength': 0}
        
        # Simple seasonal analysis
        try:
            decomposition = seasonal_decompose(pd.Series(values), model='additive', period=12)
            seasonal_strength = np.std(decomposition.seasonal) / np.std(values)
            
            return {
                'has_pattern': seasonal_strength > 0.1,
                'strength': seasonal_strength,
                'peak_month': np.argmax(decomposition.seasonal) + 1
            }
        except:
            return {'has_pattern': False, 'strength': 0}
    
    def _analyze_spending_rhythm(self, history: List[Dict]) -> Dict[str, Any]:
        """Analyze spending rhythm and patterns."""
        if len(history) < 6:
            return {'rhythm': 'insufficient_data'}
        
        monthly_totals = [month['total'] for month in history]
        volatility = np.std(monthly_totals) / np.mean(monthly_totals)
        
        if volatility < 0.1:
            rhythm = 'very_consistent'
        elif volatility < 0.2:
            rhythm = 'consistent'
        elif volatility < 0.3:
            rhythm = 'moderately_variable'
        else:
            rhythm = 'highly_variable'
        
        return {
            'rhythm': rhythm,
            'volatility_score': volatility,
            'predictability': 1 - min(1, volatility)
        }
    
    def _calculate_impulse_score(self, spending_data: Dict) -> float:
        """Calculate impulse spending score based on volatility in discretionary categories."""
        discretionary_categories = ['entertainment', 'shopping', 'dining_out']
        history = spending_data['history']
        
        impulse_scores = []
        
        for category in discretionary_categories:
            amounts = [month['categories'].get(category, 0) for month in history]
            if amounts and np.mean(amounts) > 0:
                volatility = np.std(amounts) / np.mean(amounts)
                impulse_scores.append(volatility)
        
        return np.mean(impulse_scores) if impulse_scores else 0.5
    
    def _calculate_budget_adherence(self, spending_data: Dict) -> float:
        """Calculate budget adherence score."""
        # This would require budget data in real implementation
        # For now, calculate based on spending consistency
        history = spending_data['history']
        monthly_totals = [month['total'] for month in history]
        
        # Assume budget is the median spending
        budget = np.median(monthly_totals)
        adherence_scores = [1 - abs(total - budget) / budget for total in monthly_totals]
        
        return max(0, np.mean(adherence_scores))
    
    def _detect_seasonal_bias(self, spending_data: Dict) -> Dict[str, Any]:
        """Detect seasonal spending biases."""
        history = spending_data['history']
        
        # Analyze holiday/seasonal spending (November-December)
        holiday_months = [month for month in history 
                         if month['date'].month in [11, 12]]
        regular_months = [month for month in history 
                         if month['date'].month not in [11, 12]]
        
        if holiday_months and regular_months:
            holiday_avg = np.mean([month['total'] for month in holiday_months])
            regular_avg = np.mean([month['total'] for month in regular_months])
            
            seasonal_increase = (holiday_avg - regular_avg) / regular_avg
            
            return {
                'has_seasonal_bias': seasonal_increase > 0.2,
                'seasonal_increase_percentage': seasonal_increase * 100,
                'bias_strength': min(1, seasonal_increase / 0.5)
            }
        
        return {'has_seasonal_bias': False, 'seasonal_increase_percentage': 0}
    
    def _detect_category_anchoring(self, spending_data: Dict) -> Dict[str, Any]:
        """Detect anchoring bias in spending categories."""
        # Check if user spends similar amounts in categories regardless of need
        breakdown = spending_data.get('category_breakdown', {})
        
        anchoring_scores = []
        for category, data in breakdown.items():
            volatility = data.get('volatility', 0)
            # Low volatility might indicate anchoring to a fixed amount
            anchoring_score = max(0, 1 - volatility * 5)
            anchoring_scores.append(anchoring_score)
        
        return {
            'overall_anchoring_score': np.mean(anchoring_scores) if anchoring_scores else 0,
            'high_anchoring_categories': [cat for cat, data in breakdown.items() 
                                        if data.get('volatility', 1) < 0.1]
        }
    
    def _calculate_spending_consistency(self, spending_data: Dict) -> float:
        """Calculate overall spending consistency."""
        history = spending_data['history']
        monthly_totals = [month['total'] for month in history]
        
        if len(monthly_totals) < 2:
            return 0.5
        
        # Coefficient of variation (lower is more consistent)
        cv = np.std(monthly_totals) / np.mean(monthly_totals)
        consistency = max(0, 1 - cv)
        
        return consistency
    
    def _detect_lifestyle_inflation(self, spending_data: Dict) -> Dict[str, Any]:
        """Detect lifestyle inflation patterns."""
        history = spending_data['history']
        monthly_totals = [month['total'] for month in history[-6:]]  # Last 6 months
        
        if len(monthly_totals) < 6:
            return {'detected': False, 'trend': 0}
        
        trend = self._calculate_trend(monthly_totals)
        
        return {
            'detected': trend > 0.05,  # 5% monthly increase
            'trend': trend,
            'severity': 'high' if trend > 0.1 else 'moderate' if trend > 0.05 else 'low'
        }
    
    def _get_income_bracket(self, annual_income: float) -> str:
        """Get income bracket for comparison."""
        if annual_income < 30000:
            return 'low'
        elif annual_income < 75000:
            return 'middle'
        elif annual_income < 150000:
            return 'upper_middle'
        else:
            return 'high'
    
    def _get_benchmark_spending_ratios(self, income_bracket: str) -> Dict[str, float]:
        """Get benchmark spending ratios by income bracket."""
        # Approximate ratios based on Consumer Expenditure Survey
        benchmarks = {
            'low': {
                'housing': 0.35, 'transportation': 0.18, 'food': 0.15,
                'healthcare': 0.08, 'entertainment': 0.04
            },
            'middle': {
                'housing': 0.30, 'transportation': 0.16, 'food': 0.12,
                'healthcare': 0.07, 'entertainment': 0.05
            },
            'upper_middle': {
                'housing': 0.25, 'transportation': 0.14, 'food': 0.10,
                'healthcare': 0.06, 'entertainment': 0.06
            },
            'high': {
                'housing': 0.20, 'transportation': 0.12, 'food': 0.08,
                'healthcare': 0.05, 'entertainment': 0.08
            }
        }
        
        return benchmarks.get(income_bracket, benchmarks['middle'])
    
    def _calculate_housing_affordability(self, profile: FinancialProfile) -> float:
        """Calculate housing affordability ratio."""
        expense_breakdown = profile.expense_breakdown or {}
        housing_cost = expense_breakdown.get('housing', 0)
        monthly_income = float(profile.annual_income) / 12
        
        return housing_cost / monthly_income if monthly_income > 0 else 0
    
    def _calculate_emergency_coverage(self, profile: FinancialProfile) -> float:
        """Calculate emergency fund coverage in months."""
        liquid_assets = float(profile.liquid_assets or 0)
        monthly_expenses = float(profile.monthly_expenses)
        
        return liquid_assets / monthly_expenses if monthly_expenses > 0 else 0
    
    def _calculate_spending_diversity(self, breakdown: Dict) -> float:
        """Calculate spending diversity using Shannon entropy."""
        amounts = [data['average_monthly'] for data in breakdown.values()]
        total = sum(amounts)
        
        if total == 0:
            return 0
        
        probabilities = [amount / total for amount in amounts]
        entropy = -sum(p * np.log(p) for p in probabilities if p > 0)
        
        # Normalize by max possible entropy
        max_entropy = np.log(len(breakdown))
        return entropy / max_entropy if max_entropy > 0 else 0
    
    def _classify_fixed_variable_expenses(self, breakdown: Dict) -> Dict[str, List]:
        """Classify expenses as fixed vs variable based on volatility."""
        fixed_expenses = []
        variable_expenses = []
        
        for category, data in breakdown.items():
            volatility = data.get('volatility', 0)
            if volatility < 0.15:  # Low volatility suggests fixed expense
                fixed_expenses.append(category)
            else:
                variable_expenses.append(category)
        
        return {
            'fixed': fixed_expenses,
            'variable': variable_expenses
        }
    
    def _generate_behavioral_recommendations(self, analysis: Dict, 
                                           profile: FinancialProfile) -> List[str]:
        """Generate personalized behavioral recommendations."""
        recommendations = []
        
        # Spending efficiency recommendations
        efficiency = analysis.get('spending_efficiency', {})
        if efficiency.get('expense_ratio', 0) > 0.8:
            recommendations.append("Consider reducing expenses to improve savings rate")
        
        # Category-specific recommendations
        comparison = analysis.get('comparison_metrics', {}).get('category_comparison', {})
        for category, data in comparison.items():
            if data.get('status') == 'above_average' and data.get('difference', 0) > 0.05:
                recommendations.append(f"Consider reducing {category} expenses - currently above average")
        
        # Behavioral pattern recommendations
        behavioral = analysis.get('behavioral_insights', {})
        
        if behavioral.get('impulse_spending_score', 0) > 0.7:
            recommendations.append("Implement waiting periods for discretionary purchases to reduce impulse spending")
        
        if behavioral.get('budget_adherence_score', 1) < 0.7:
            recommendations.append("Create and stick to a detailed monthly budget")
        
        if behavioral.get('lifestyle_inflation', {}).get('detected', False):
            recommendations.append("Monitor lifestyle inflation - spending is increasing faster than recommended")
        
        # Temporal pattern recommendations
        temporal = analysis.get('temporal_patterns', {})
        if temporal.get('volatility', 0) > 0.3:
            recommendations.append("Work on spending consistency to improve financial predictability")
        
        # Emergency fund recommendation
        if efficiency.get('emergency_fund_coverage', 0) < 3:
            recommendations.append("Prioritize building 3-6 months of emergency fund coverage")
        
        return recommendations
    
    def predict_future_spending(self, user_id: str, months_ahead: int = 6) -> Dict[str, Any]:
        """Predict future spending patterns."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                # Get current spending data
                spending_data = self._extract_spending_data(user.financial_profile)
                
                # Simple trend-based prediction
                history = spending_data['history']
                monthly_totals = [month['total'] for month in history]
                
                # Calculate trend
                trend = self._calculate_trend(monthly_totals)
                current_average = np.mean(monthly_totals[-3:])  # Last 3 months average
                
                # Project future spending
                predictions = []
                for i in range(1, months_ahead + 1):
                    predicted_amount = current_average * (1 + trend * i)
                    predictions.append({
                        'month': i,
                        'predicted_amount': predicted_amount,
                        'confidence_interval': {
                            'lower': predicted_amount * 0.85,
                            'upper': predicted_amount * 1.15
                        }
                    })
                
                return {
                    'user_id': user_id,
                    'predictions': predictions,
                    'trend_direction': 'increasing' if trend > 0.02 else 
                                    'decreasing' if trend < -0.02 else 'stable',
                    'confidence_score': max(0.5, 1 - abs(trend) * 10),  # Lower confidence for high trends
                    'factors_affecting_prediction': self._identify_prediction_factors(user.financial_profile)
                }
                
        except Exception as e:
            logger.error(f"Failed to predict spending for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _identify_prediction_factors(self, profile: FinancialProfile) -> List[str]:
        """Identify factors that might affect spending predictions."""
        factors = []
        
        if profile.age < 30:
            factors.append("Young age may lead to lifestyle changes affecting spending")
        
        if profile.marital_status == 'single' and profile.age > 25:
            factors.append("Potential for marriage/partnership affecting expenses")
        
        if profile.dependents == 0 and profile.age > 30:
            factors.append("Potential for having children affecting family expenses")
        
        if profile.employment_status == 'employed' and profile.job_stability == 'unstable':
            factors.append("Job instability may affect income and spending patterns")
        
        if profile.debt_to_income_ratio > 0.3:
            factors.append("High debt levels may require future expense reduction")
        
        return factors