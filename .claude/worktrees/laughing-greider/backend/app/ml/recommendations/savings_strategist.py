"""
Personalized savings strategies based on ML predictions and behavioral analysis.

This module provides:
- Optimized savings allocation strategies
- Behavioral-based savings recommendations
- Automated savings rule suggestions
- Tax-efficient savings planning
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib
import json
from pathlib import Path

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class SavingsStrategist:
    """ML-powered personalized savings strategy generator."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/ml/models/savings_strategist"
        self.savings_optimizer = None
        self.behavior_predictor = None
        self.allocation_model = None
        self.scaler = StandardScaler()
        
        # Savings strategies and rules
        self.savings_strategies = {
            'aggressive_saver': {
                'target_rate': 0.30,
                'allocation': {'emergency': 0.20, 'investments': 0.50, 'goals': 0.30},
                'frequency': 'monthly',
                'automation_level': 'high'
            },
            'balanced_saver': {
                'target_rate': 0.20,
                'allocation': {'emergency': 0.30, 'investments': 0.40, 'goals': 0.30},
                'frequency': 'monthly',
                'automation_level': 'medium'
            },
            'conservative_saver': {
                'target_rate': 0.10,
                'allocation': {'emergency': 0.50, 'investments': 0.20, 'goals': 0.30},
                'frequency': 'monthly',
                'automation_level': 'low'
            },
            'goal_focused': {
                'target_rate': 0.15,
                'allocation': {'emergency': 0.25, 'investments': 0.25, 'goals': 0.50},
                'frequency': 'bi_weekly',
                'automation_level': 'high'
            }
        }
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load pre-trained savings strategy models."""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists():
                self.savings_optimizer = joblib.load(model_dir / "savings_optimizer.pkl")
                self.behavior_predictor = joblib.load(model_dir / "behavior_predictor.pkl")
                self.allocation_model = joblib.load(model_dir / "allocation_model.pkl")
                self.scaler = joblib.load(model_dir / "scaler.pkl")
                logger.info("Loaded pre-trained savings strategy models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _save_models(self) -> None:
        """Save trained models."""
        try:
            model_dir = Path(self.model_path)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            if self.savings_optimizer:
                joblib.dump(self.savings_optimizer, model_dir / "savings_optimizer.pkl")
            if self.behavior_predictor:
                joblib.dump(self.behavior_predictor, model_dir / "behavior_predictor.pkl")
            if self.allocation_model:
                joblib.dump(self.allocation_model, model_dir / "allocation_model.pkl")
            
            joblib.dump(self.scaler, model_dir / "scaler.pkl")
            logger.info("Saved savings strategy models")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def generate_savings_strategy(self, user_id: str) -> Dict[str, Any]:
        """Generate personalized savings strategy for a user."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                profile = user.financial_profile
                goals = user.goals or []
                
                # Analyze current financial situation
                financial_analysis = self._analyze_financial_situation(profile, goals)
                
                # Determine optimal savings rate
                optimal_savings_rate = self._calculate_optimal_savings_rate(profile, goals)
                
                # Generate savings allocation strategy
                allocation_strategy = self._generate_allocation_strategy(profile, goals, optimal_savings_rate)
                
                # Create automated savings plan
                automation_plan = self._create_automation_plan(profile, allocation_strategy)
                
                # Generate behavioral recommendations
                behavioral_tips = self._generate_behavioral_tips(profile, financial_analysis)
                
                # Tax optimization suggestions
                tax_optimization = self._generate_tax_optimization(profile, allocation_strategy)
                
                # Progress tracking plan
                tracking_plan = self._create_tracking_plan(profile, allocation_strategy)
                
                return {
                    'user_id': user_id,
                    'financial_analysis': financial_analysis,
                    'optimal_savings_rate': optimal_savings_rate,
                    'allocation_strategy': allocation_strategy,
                    'automation_plan': automation_plan,
                    'behavioral_recommendations': behavioral_tips,
                    'tax_optimization': tax_optimization,
                    'tracking_plan': tracking_plan,
                    'implementation_timeline': self._create_implementation_timeline(allocation_strategy),
                    'success_probability': self._estimate_success_probability(profile, allocation_strategy)
                }
                
        except Exception as e:
            logger.error(f"Failed to generate savings strategy for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _analyze_financial_situation(self, profile: FinancialProfile, goals: List) -> Dict[str, Any]:
        """Analyze current financial situation."""
        monthly_income = float(profile.annual_income) / 12
        monthly_expenses = float(profile.monthly_expenses)
        available_to_save = monthly_income - monthly_expenses
        
        analysis = {
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'available_to_save': available_to_save,
            'current_savings_rate': available_to_save / monthly_income if monthly_income > 0 else 0,
            'emergency_fund_status': self._assess_emergency_fund(profile),
            'debt_situation': self._assess_debt_situation(profile),
            'goal_funding_gap': self._calculate_goal_funding_gap(goals),
            'financial_health_score': self._calculate_financial_health_score(profile, goals),
            'savings_capacity': self._assess_savings_capacity(profile)
        }
        
        return analysis
    
    def _assess_emergency_fund(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Assess emergency fund adequacy."""
        liquid_assets = float(profile.liquid_assets or 0)
        monthly_expenses = float(profile.monthly_expenses)
        
        months_covered = liquid_assets / monthly_expenses if monthly_expenses > 0 else 0
        target_months = 6  # Standard recommendation
        
        return {
            'current_months_covered': months_covered,
            'target_months': target_months,
            'deficit_amount': max(0, (target_months - months_covered) * monthly_expenses),
            'status': 'adequate' if months_covered >= target_months else
                     'partial' if months_covered >= 3 else 'insufficient',
            'priority': 'high' if months_covered < 3 else 'medium' if months_covered < 6 else 'low'
        }
    
    def _assess_debt_situation(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Assess debt situation and payoff priority."""
        total_debt = (
            float(profile.credit_card_debt or 0) +
            float(profile.student_loans or 0) +
            float(profile.auto_loans or 0) +
            float(profile.other_debts or 0)
        )
        
        # Exclude mortgage from high-interest debt calculation
        high_interest_debt = float(profile.credit_card_debt or 0)
        
        debt_to_income = total_debt / float(profile.annual_income) if profile.annual_income > 0 else 0
        
        return {
            'total_debt': total_debt,
            'high_interest_debt': high_interest_debt,
            'debt_to_income_ratio': debt_to_income,
            'monthly_payments': self._estimate_monthly_debt_payments(profile),
            'payoff_priority': 'high' if high_interest_debt > 5000 else
                             'medium' if total_debt > 10000 else 'low',
            'strategy_recommendation': 'avalanche' if high_interest_debt > 0 else 'snowball'
        }
    
    def _estimate_monthly_debt_payments(self, profile: FinancialProfile) -> float:
        """Estimate monthly debt payments."""
        # Simplified estimation based on debt types
        credit_card_payment = float(profile.credit_card_debt or 0) * 0.03  # 3% minimum
        student_loan_payment = float(profile.student_loans or 0) * 0.01  # 1% typical
        auto_loan_payment = float(profile.auto_loans or 0) * 0.02  # 2% typical
        other_payment = float(profile.other_debts or 0) * 0.02
        
        return credit_card_payment + student_loan_payment + auto_loan_payment + other_payment
    
    def _calculate_goal_funding_gap(self, goals: List) -> Dict[str, Any]:
        """Calculate funding gap for all goals."""
        if not goals:
            return {'total_gap': 0, 'monthly_needed': 0, 'goals_analysis': []}
        
        total_gap = 0
        monthly_needed = 0
        goals_analysis = []
        
        for goal in goals:
            if goal.status == 'active':
                remaining_amount = float(goal.target_amount) - float(goal.current_amount or 0)
                required_monthly = remaining_amount / max(1, goal.months_remaining)
                
                total_gap += remaining_amount
                monthly_needed += required_monthly
                
                goals_analysis.append({
                    'goal_name': goal.name,
                    'remaining_amount': remaining_amount,
                    'required_monthly': required_monthly,
                    'months_remaining': goal.months_remaining,
                    'priority': goal.priority
                })
        
        return {
            'total_gap': total_gap,
            'monthly_needed': monthly_needed,
            'goals_analysis': goals_analysis
        }
    
    def _calculate_financial_health_score(self, profile: FinancialProfile, goals: List) -> float:
        """Calculate overall financial health score (0-100)."""
        scores = []
        
        # Emergency fund score
        emergency_months = float(profile.liquid_assets or 0) / float(profile.monthly_expenses)
        emergency_score = min(100, (emergency_months / 6) * 100)
        scores.append(emergency_score)
        
        # Debt score
        debt_ratio = profile.debt_to_income_ratio
        debt_score = max(0, 100 - (debt_ratio * 200))
        scores.append(debt_score)
        
        # Savings rate score
        monthly_income = float(profile.annual_income) / 12
        available_to_save = monthly_income - float(profile.monthly_expenses)
        savings_rate = available_to_save / monthly_income if monthly_income > 0 else 0
        savings_score = min(100, savings_rate * 500)  # 20% savings rate = 100 points
        scores.append(savings_score)
        
        # Goal progress score
        if goals:
            goal_progress = np.mean([g.progress_percentage for g in goals])
            scores.append(goal_progress)
        
        return np.mean(scores)
    
    def _assess_savings_capacity(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Assess savings capacity and constraints."""
        monthly_income = float(profile.annual_income) / 12
        monthly_expenses = float(profile.monthly_expenses)
        available_to_save = monthly_income - monthly_expenses
        
        # Calculate maximum realistic savings rate
        # Account for debt payments
        debt_payments = self._estimate_monthly_debt_payments(profile)
        adjusted_available = available_to_save - debt_payments
        
        max_savings_rate = adjusted_available / monthly_income if monthly_income > 0 else 0
        
        return {
            'theoretical_max': available_to_save,
            'realistic_max': adjusted_available,
            'max_savings_rate': max_savings_rate,
            'constraints': self._identify_savings_constraints(profile),
            'capacity_level': 'high' if max_savings_rate > 0.2 else
                            'medium' if max_savings_rate > 0.1 else 'low'
        }
    
    def _identify_savings_constraints(self, profile: FinancialProfile) -> List[str]:
        """Identify factors limiting savings capacity."""
        constraints = []
        
        if profile.debt_to_income_ratio > 0.3:
            constraints.append("High debt burden limits savings capacity")
        
        if profile.dependents > 0:
            constraints.append("Family expenses reduce available savings")
        
        if profile.job_stability == 'unstable':
            constraints.append("Job instability requires larger emergency fund")
        
        if profile.age > 50 and float(profile.retirement_accounts or 0) < float(profile.annual_income):
            constraints.append("Retirement catch-up contributions needed")
        
        return constraints
    
    def _calculate_optimal_savings_rate(self, profile: FinancialProfile, goals: List) -> Dict[str, Any]:
        """Calculate optimal savings rate based on goals and constraints."""
        # Base savings rate calculation
        capacity = self._assess_savings_capacity(profile)
        goal_gap = self._calculate_goal_funding_gap(goals)
        emergency_fund = self._assess_emergency_fund(profile)
        
        # Required savings for goals
        goal_monthly_need = goal_gap['monthly_needed']
        
        # Required savings for emergency fund
        emergency_monthly_need = emergency_fund['deficit_amount'] / 12  # Spread over 1 year
        
        # Total monthly savings needed
        total_monthly_needed = goal_monthly_need + emergency_monthly_need
        
        monthly_income = float(profile.annual_income) / 12
        optimal_rate = total_monthly_needed / monthly_income if monthly_income > 0 else 0
        
        # Cap at realistic maximum
        max_rate = capacity['max_savings_rate']
        achievable_rate = min(optimal_rate, max_rate)
        
        return {
            'target_rate': achievable_rate,
            'target_monthly_amount': achievable_rate * monthly_income,
            'goal_component': goal_monthly_need,
            'emergency_component': emergency_monthly_need,
            'is_achievable': optimal_rate <= max_rate,
            'shortfall': max(0, optimal_rate - max_rate) * monthly_income,
            'recommendation': self._get_savings_rate_recommendation(achievable_rate)
        }
    
    def _get_savings_rate_recommendation(self, rate: float) -> str:
        """Get recommendation category based on savings rate."""
        if rate >= 0.25:
            return 'aggressive_saver'
        elif rate >= 0.15:
            return 'balanced_saver'
        elif rate >= 0.1:
            return 'conservative_saver'
        else:
            return 'goal_focused'
    
    def _generate_allocation_strategy(self, profile: FinancialProfile, goals: List, 
                                   optimal_savings: Dict) -> Dict[str, Any]:
        """Generate allocation strategy for savings."""
        monthly_savings = optimal_savings['target_monthly_amount']
        emergency_fund = self._assess_emergency_fund(profile)
        debt_situation = self._assess_debt_situation(profile)
        
        # Priority-based allocation
        allocation = {
            'emergency_fund': 0,
            'debt_payoff': 0,
            'retirement': 0,
            'goals': 0,
            'investments': 0
        }
        
        remaining_savings = monthly_savings
        
        # 1. Emergency fund (if insufficient)
        if emergency_fund['status'] != 'adequate':
            emergency_allocation = min(remaining_savings * 0.5, emergency_fund['deficit_amount'] / 12)
            allocation['emergency_fund'] = emergency_allocation
            remaining_savings -= emergency_allocation
        
        # 2. High-interest debt payoff
        if debt_situation['high_interest_debt'] > 0:
            debt_allocation = min(remaining_savings * 0.3, debt_situation['monthly_payments'])
            allocation['debt_payoff'] = debt_allocation
            remaining_savings -= debt_allocation
        
        # 3. Retirement savings (age-based)
        retirement_target_rate = max(0.1, (65 - profile.age) / 1000)  # Age-based formula
        retirement_allocation = min(remaining_savings * 0.4, monthly_savings * retirement_target_rate)
        allocation['retirement'] = retirement_allocation
        remaining_savings -= retirement_allocation
        
        # 4. Goal funding
        goal_gap = self._calculate_goal_funding_gap(goals)
        goal_allocation = min(remaining_savings * 0.6, goal_gap['monthly_needed'])
        allocation['goals'] = goal_allocation
        remaining_savings -= goal_allocation
        
        # 5. Additional investments
        allocation['investments'] = remaining_savings
        
        # Convert to percentages
        allocation_percentages = {k: v/monthly_savings if monthly_savings > 0 else 0 
                                for k, v in allocation.items()}
        
        return {
            'monthly_amounts': allocation,
            'percentages': allocation_percentages,
            'total_monthly': monthly_savings,
            'priority_explanation': self._explain_allocation_priorities(allocation, profile),
            'rebalancing_triggers': self._define_rebalancing_triggers()
        }
    
    def _explain_allocation_priorities(self, allocation: Dict, profile: FinancialProfile) -> List[str]:
        """Explain allocation priority reasoning."""
        explanations = []
        
        if allocation['emergency_fund'] > 0:
            explanations.append("Emergency fund prioritized for financial security")
        
        if allocation['debt_payoff'] > 0:
            explanations.append("High-interest debt payoff for guaranteed returns")
        
        if allocation['retirement'] > 0:
            years_to_retirement = 65 - profile.age
            explanations.append(f"Retirement savings critical with {years_to_retirement} years remaining")
        
        if allocation['goals'] > 0:
            explanations.append("Goal funding for specific objectives")
        
        if allocation['investments'] > 0:
            explanations.append("Additional investments for wealth building")
        
        return explanations
    
    def _define_rebalancing_triggers(self) -> List[str]:
        """Define when to rebalance allocation."""
        return [
            "Emergency fund fully funded",
            "High-interest debt eliminated",
            "Major life event (marriage, children, job change)",
            "Significant income change (+/- 20%)",
            "Goal completion or modification",
            "Annual review"
        ]
    
    def _create_automation_plan(self, profile: FinancialProfile, allocation: Dict) -> Dict[str, Any]:
        """Create automated savings implementation plan."""
        monthly_amounts = allocation['monthly_amounts']
        
        automation_plan = {
            'recommended_frequency': self._determine_automation_frequency(profile),
            'account_setup': self._recommend_account_setup(),
            'automated_transfers': [],
            'manual_actions': [],
            'automation_score': 0
        }
        
        # Emergency fund automation
        if monthly_amounts['emergency_fund'] > 0:
            automation_plan['automated_transfers'].append({
                'purpose': 'Emergency Fund',
                'amount': monthly_amounts['emergency_fund'],
                'frequency': 'monthly',
                'account_type': 'high_yield_savings',
                'automation_level': 'high'
            })
        
        # Retirement automation
        if monthly_amounts['retirement'] > 0:
            automation_plan['automated_transfers'].append({
                'purpose': 'Retirement Savings',
                'amount': monthly_amounts['retirement'],
                'frequency': 'monthly',
                'account_type': '401k_or_ira',
                'automation_level': 'high'
            })
        
        # Goal savings automation
        if monthly_amounts['goals'] > 0:
            automation_plan['automated_transfers'].append({
                'purpose': 'Goal Savings',
                'amount': monthly_amounts['goals'],
                'frequency': 'monthly',
                'account_type': 'dedicated_savings',
                'automation_level': 'medium'
            })
        
        # Investment automation
        if monthly_amounts['investments'] > 0:
            automation_plan['automated_transfers'].append({
                'purpose': 'Investment Portfolio',
                'amount': monthly_amounts['investments'],
                'frequency': 'monthly',
                'account_type': 'brokerage',
                'automation_level': 'medium'
            })
        
        # Debt payoff (manual due to variability)
        if monthly_amounts['debt_payoff'] > 0:
            automation_plan['manual_actions'].append({
                'purpose': 'Debt Payoff',
                'amount': monthly_amounts['debt_payoff'],
                'frequency': 'monthly',
                'reason': 'Variable payment amounts and strategies'
            })
        
        # Calculate automation score
        total_automated = sum(t['amount'] for t in automation_plan['automated_transfers'])
        total_savings = sum(monthly_amounts.values())
        automation_plan['automation_score'] = total_automated / total_savings if total_savings > 0 else 0
        
        return automation_plan
    
    def _determine_automation_frequency(self, profile: FinancialProfile) -> str:
        """Determine optimal automation frequency."""
        if profile.income_stability == 'stable':
            return 'monthly'
        elif profile.income_stability == 'variable':
            return 'bi_weekly'
        else:
            return 'manual'
    
    def _recommend_account_setup(self) -> Dict[str, str]:
        """Recommend account types for different savings purposes."""
        return {
            'emergency_fund': 'High-yield savings account with instant access',
            'retirement': '401(k) with employer match, then Roth/Traditional IRA',
            'short_term_goals': 'CD or high-yield savings with goal timeline',
            'long_term_goals': 'Conservative investment account',
            'general_investment': 'Diversified brokerage account'
        }
    
    def _generate_behavioral_tips(self, profile: FinancialProfile, analysis: Dict) -> List[str]:
        """Generate behavioral savings tips."""
        tips = []
        
        # Based on savings capacity
        if analysis['savings_capacity']['capacity_level'] == 'low':
            tips.extend([
                "Start with micro-savings: Save loose change or $1 daily",
                "Use the 52-week challenge to build savings habit",
                "Review expenses weekly to find small savings opportunities"
            ])
        
        # Based on age
        if profile.age < 30:
            tips.extend([
                "Automate savings before you get used to spending the money",
                "Start retirement savings early to benefit from compound interest"
            ])
        elif profile.age > 50:
            tips.extend([
                "Consider catch-up contributions to retirement accounts",
                "Review and potentially increase savings rate as children become independent"
            ])
        
        # Based on family situation
        if profile.dependents > 0:
            tips.extend([
                "Set up education savings accounts (529 plans) for children",
                "Use family financial goals as motivation for saving"
            ])
        
        # Based on income stability
        if profile.income_stability != 'stable':
            tips.extend([
                "Save a higher percentage during high-income periods",
                "Build larger emergency fund due to income variability"
            ])
        
        # General behavioral tips
        tips.extend([
            "Pay yourself first - save before spending on discretionary items",
            "Use automatic transfers to remove temptation to skip savings",
            "Review and celebrate savings milestones monthly"
        ])
        
        return tips[:8]  # Limit to 8 most relevant tips
    
    def _generate_tax_optimization(self, profile: FinancialProfile, allocation: Dict) -> Dict[str, Any]:
        """Generate tax optimization recommendations."""
        optimization = {
            'retirement_tax_strategy': self._recommend_retirement_tax_strategy(profile),
            'tax_advantaged_accounts': self._recommend_tax_accounts(profile, allocation),
            'tax_loss_harvesting': self._assess_tax_loss_opportunities(profile),
            'timing_strategies': self._recommend_timing_strategies(profile)
        }
        
        return optimization
    
    def _recommend_retirement_tax_strategy(self, profile: FinancialProfile) -> Dict[str, str]:
        """Recommend retirement account tax strategy."""
        current_tax_bracket = self._estimate_tax_bracket(profile.annual_income)
        
        if current_tax_bracket <= 0.22:  # Lower tax brackets
            return {
                'primary_recommendation': 'Roth IRA/401(k)',
                'reasoning': 'Lower current tax rate favors Roth contributions',
                'secondary': 'Traditional for employer match'
            }
        else:  # Higher tax brackets
            return {
                'primary_recommendation': 'Traditional IRA/401(k)',
                'reasoning': 'Higher current tax rate favors traditional deductions',
                'secondary': 'Roth for diversification'
            }
    
    def _estimate_tax_bracket(self, annual_income: float) -> float:
        """Estimate marginal tax bracket."""
        # Simplified 2024 tax brackets (single filer)
        if annual_income <= 11000:
            return 0.10
        elif annual_income <= 44725:
            return 0.12
        elif annual_income <= 95375:
            return 0.22
        elif annual_income <= 182050:
            return 0.24
        elif annual_income <= 231250:
            return 0.32
        elif annual_income <= 578125:
            return 0.35
        else:
            return 0.37
    
    def _recommend_tax_accounts(self, profile: FinancialProfile, allocation: Dict) -> List[Dict]:
        """Recommend tax-advantaged accounts."""
        recommendations = []
        
        # HSA (if eligible)
        recommendations.append({
            'account_type': 'HSA',
            'annual_limit': 4150,  # 2024 individual limit
            'tax_benefit': 'Triple tax advantage',
            'priority': 'high' if profile.health_insurance_status else 'n/a'
        })
        
        # 401(k)
        recommendations.append({
            'account_type': '401(k)',
            'annual_limit': 23000,  # 2024 limit
            'tax_benefit': 'Pre-tax contributions reduce current taxes',
            'priority': 'high'
        })
        
        # IRA
        recommendations.append({
            'account_type': 'IRA',
            'annual_limit': 7000,  # 2024 limit
            'tax_benefit': 'Additional retirement savings',
            'priority': 'medium'
        })
        
        return recommendations
    
    def _assess_tax_loss_opportunities(self, profile: FinancialProfile) -> Dict[str, Any]:
        """Assess tax loss harvesting opportunities."""
        # This would require investment portfolio data
        return {
            'applicable': 'unknown',
            'recommendation': 'Review investment portfolio for tax loss harvesting opportunities',
            'estimated_benefit': 'Varies based on portfolio performance'
        }
    
    def _recommend_timing_strategies(self, profile: FinancialProfile) -> List[str]:
        """Recommend tax timing strategies."""
        strategies = []
        
        if profile.age >= 50:
            strategies.append("Make catch-up contributions to retirement accounts")
        
        strategies.extend([
            "Maximize contributions before year-end",
            "Consider Roth conversions in low-income years",
            "Time large purchases for maximum tax benefit"
        ])
        
        return strategies
    
    def _create_tracking_plan(self, profile: FinancialProfile, allocation: Dict) -> Dict[str, Any]:
        """Create progress tracking plan."""
        tracking_plan = {
            'monthly_metrics': [
                'Total savings amount',
                'Savings rate percentage',
                'Emergency fund growth',
                'Goal progress percentages',
                'Investment portfolio value'
            ],
            'quarterly_reviews': [
                'Allocation rebalancing',
                'Goal timeline adjustments',
                'Expense category analysis',
                'Income changes impact'
            ],
            'annual_assessments': [
                'Tax optimization review',
                'Insurance needs update',
                'Retirement projection update',
                'Overall strategy adjustment'
            ],
            'milestones': self._define_savings_milestones(profile, allocation),
            'alerts': self._define_progress_alerts()
        }
        
        return tracking_plan
    
    def _define_savings_milestones(self, profile: FinancialProfile, allocation: Dict) -> List[Dict]:
        """Define savings milestones to celebrate."""
        milestones = []
        
        # Emergency fund milestones
        monthly_expenses = float(profile.monthly_expenses)
        for months in [1, 3, 6]:
            milestones.append({
                'type': 'emergency_fund',
                'description': f'{months} months of expenses saved',
                'target_amount': months * monthly_expenses,
                'celebration': 'Treat yourself to something small'
            })
        
        # Net worth milestones
        current_net_worth = profile.net_worth
        for milestone in [10000, 25000, 50000, 100000]:
            if milestone > current_net_worth:
                milestones.append({
                    'type': 'net_worth',
                    'description': f'Net worth reaches ${milestone:,}',
                    'target_amount': milestone,
                    'celebration': 'Plan a special experience'
                })
                break
        
        return milestones
    
    def _define_progress_alerts(self) -> List[str]:
        """Define alerts for progress tracking."""
        return [
            "Savings rate drops below target for 2 consecutive months",
            "Emergency fund is used (rebuild alert)",
            "Goal timeline becomes unrealistic (>25% behind)",
            "Investment allocation drifts significantly",
            "Major expense impacts savings plan"
        ]
    
    def _create_implementation_timeline(self, allocation: Dict) -> Dict[str, List[str]]:
        """Create implementation timeline."""
        return {
            'week_1': [
                "Set up automatic transfers for retirement and emergency fund",
                "Open high-yield savings account if needed",
                "Calculate exact transfer amounts"
            ],
            'week_2': [
                "Set up goal-specific savings accounts",
                "Configure automated investing if applicable",
                "Download savings tracking app"
            ],
            'month_1': [
                "Review first month's progress",
                "Adjust automation if needed",
                "Celebrate first milestone"
            ],
            'month_3': [
                "Quarterly review and rebalancing",
                "Assess goal timeline progress",
                "Consider increasing savings rate"
            ],
            'month_6': [
                "Mid-year comprehensive review",
                "Update goals based on progress",
                "Optimize tax strategies"
            ],
            'year_1': [
                "Annual financial review",
                "Update automation for new year limits",
                "Plan next year's savings strategy"
            ]
        }
    
    def _estimate_success_probability(self, profile: FinancialProfile, allocation: Dict) -> Dict[str, Any]:
        """Estimate probability of successfully following savings plan."""
        factors = []
        
        # Income stability
        stability_scores = {'stable': 0.9, 'variable': 0.7, 'irregular': 0.5}
        factors.append(stability_scores.get(profile.income_stability, 0.7))
        
        # Automation level
        automation_score = sum(1 for transfer in allocation.get('automation_plan', {}).get('automated_transfers', []))
        automation_factor = min(1.0, automation_score / 4)
        factors.append(automation_factor)
        
        # Savings rate reasonableness
        target_rate = allocation.get('percentages', {}).get('total_monthly', 0)
        if target_rate <= 0.15:
            rate_factor = 0.9
        elif target_rate <= 0.25:
            rate_factor = 0.7
        else:
            rate_factor = 0.5
        factors.append(rate_factor)
        
        # Emergency fund status
        emergency_status = self._assess_emergency_fund(profile)['status']
        emergency_factors = {'adequate': 0.9, 'partial': 0.7, 'insufficient': 0.5}
        factors.append(emergency_factors.get(emergency_status, 0.6))
        
        overall_probability = np.mean(factors)
        
        return {
            'overall_probability': overall_probability,
            'confidence_level': 'high' if overall_probability > 0.8 else
                              'medium' if overall_probability > 0.6 else 'low',
            'key_risk_factors': self._identify_risk_factors(factors, profile),
            'improvement_suggestions': self._suggest_probability_improvements(factors)
        }
    
    def _identify_risk_factors(self, factors: List[float], profile: FinancialProfile) -> List[str]:
        """Identify factors that reduce success probability."""
        risks = []
        
        if profile.income_stability != 'stable':
            risks.append("Variable income may affect consistent savings")
        
        if profile.debt_to_income_ratio > 0.3:
            risks.append("High debt burden may compete with savings")
        
        if profile.dependents > 0:
            risks.append("Family expenses may create unexpected costs")
        
        return risks
    
    def _suggest_probability_improvements(self, factors: List[float]) -> List[str]:
        """Suggest improvements to increase success probability."""
        suggestions = []
        
        if factors[1] < 0.8:  # Low automation
            suggestions.append("Increase automation to reduce reliance on willpower")
        
        if factors[2] < 0.8:  # High savings rate
            suggestions.append("Consider starting with lower savings rate and increasing gradually")
        
        suggestions.extend([
            "Track progress weekly to stay motivated",
            "Set up accountability with family or advisor",
            "Start with smallest sustainable amount and build up"
        ])
        
        return suggestions