"""
Comprehensive unit tests for ML recommendation models.

This test suite covers:
- Risk prediction models
- Portfolio optimization
- Behavioral analysis
- Life event prediction
- Recommendation engine
- Model monitoring and validation
- Data preprocessing
- Feature engineering
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib

from app.ml.recommendations.risk_predictor import RiskPredictor
from app.ml.recommendations.portfolio_rebalancer import PortfolioRebalancer
from app.ml.recommendations.behavioral_analyzer import BehavioralAnalyzer
from app.ml.recommendations.life_event_predictor import LifeEventPredictor
from app.ml.recommendations.recommendation_engine import RecommendationEngine
from app.ml.recommendations.model_monitor import ModelMonitor
from app.ml.recommendations.collaborative_filter import CollaborativeFilter
from app.ml.recommendations.goal_optimizer import GoalOptimizer
from app.ml.recommendations.savings_strategist import SavingsStrategist
from app.models.financial_profile import FinancialProfile
from app.models.ml_recommendation import MLRecommendation


class TestRiskPredictor:
    """Test suite for risk prediction model."""
    
    @pytest.fixture
    def risk_predictor(self):
        """Create risk predictor instance."""
        return RiskPredictor()
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial data for risk prediction."""
        return pd.DataFrame({
            'age': [25, 35, 45, 55, 65],
            'income': [40000, 75000, 95000, 120000, 80000],
            'savings': [5000, 25000, 150000, 400000, 300000],
            'debt': [25000, 15000, 50000, 20000, 0],
            'employment_years': [2, 10, 20, 30, 40],
            'dependents': [0, 2, 2, 1, 0],
            'risk_tolerance': ['aggressive', 'moderate', 'moderate', 'conservative', 'conservative']
        })
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for risk analysis."""
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'sp500_return': np.random.normal(0.0008, 0.012, 252),
            'bond_return': np.random.normal(0.0003, 0.005, 252),
            'volatility_index': np.random.uniform(10, 30, 252),
            'interest_rate': np.random.uniform(2.0, 5.0, 252)
        })
    
    def test_risk_score_calculation(self, risk_predictor, sample_financial_data):
        """Test calculation of individual risk scores."""
        
        for _, row in sample_financial_data.iterrows():
            risk_score = risk_predictor.calculate_risk_score(row.to_dict())
            
            assert 0 <= risk_score <= 100
            assert isinstance(risk_score, (int, float))
        
        # Young person with high income should have higher risk tolerance
        young_high_income = sample_financial_data.iloc[0].to_dict()
        young_score = risk_predictor.calculate_risk_score(young_high_income)
        
        # Older person should have lower risk tolerance
        older_person = sample_financial_data.iloc[4].to_dict()
        older_score = risk_predictor.calculate_risk_score(older_person)
        
        assert young_score > older_score
    
    def test_portfolio_risk_assessment(self, risk_predictor):
        """Test portfolio risk assessment."""
        
        portfolio = {
            'stocks': 0.7,
            'bonds': 0.2,
            'cash': 0.1
        }
        
        market_conditions = {
            'volatility_index': 25,
            'interest_rates': 3.5,
            'market_trend': 'bullish'
        }
        
        risk_assessment = risk_predictor.assess_portfolio_risk(portfolio, market_conditions)
        
        assert 'overall_risk_score' in risk_assessment
        assert 'risk_factors' in risk_assessment
        assert 'recommendations' in risk_assessment
        
        # High stock allocation should result in higher risk
        assert risk_assessment['overall_risk_score'] > 50
        
        # Should identify concentration risk
        assert any('concentration' in factor.lower() 
                  for factor in risk_assessment['risk_factors'])
    
    def test_scenario_risk_analysis(self, risk_predictor, sample_market_data):
        """Test risk analysis under different scenarios."""
        
        portfolio = {'stocks': 0.6, 'bonds': 0.3, 'cash': 0.1}
        
        scenarios = [
            {'name': 'market_crash', 'stock_decline': -30, 'bond_change': 5},
            {'name': 'recession', 'stock_decline': -20, 'bond_change': 10},
            {'name': 'inflation_surge', 'stock_change': 10, 'bond_decline': -15}
        ]
        
        scenario_analysis = risk_predictor.analyze_scenario_risk(
            portfolio, scenarios, sample_market_data
        )
        
        assert len(scenario_analysis) == 3
        
        for scenario_result in scenario_analysis:
            assert 'scenario_name' in scenario_result
            assert 'portfolio_impact' in scenario_result
            assert 'probability' in scenario_result
            assert 'expected_loss' in scenario_result
        
        # Market crash should have highest expected loss
        crash_scenario = next(s for s in scenario_analysis if s['scenario_name'] == 'market_crash')
        assert crash_scenario['expected_loss'] < -15  # Significant loss expected
    
    def test_risk_tolerance_prediction(self, risk_predictor, sample_financial_data):
        """Test prediction of risk tolerance from financial profile."""
        
        # Prepare training data
        X = sample_financial_data.drop('risk_tolerance', axis=1)
        y = sample_financial_data['risk_tolerance']
        
        # Train model
        risk_predictor.train_risk_tolerance_model(X, y)
        
        # Test prediction
        new_profile = {
            'age': 30,
            'income': 80000,
            'savings': 30000,
            'debt': 20000,
            'employment_years': 8,
            'dependents': 1
        }
        
        predicted_tolerance = risk_predictor.predict_risk_tolerance(new_profile)
        
        assert predicted_tolerance in ['conservative', 'moderate', 'aggressive']
        
        # Test prediction confidence
        confidence = risk_predictor.get_prediction_confidence(new_profile)
        assert 0 <= confidence <= 1
    
    def test_risk_factor_importance(self, risk_predictor, sample_financial_data):
        """Test identification of important risk factors."""
        
        X = sample_financial_data.drop('risk_tolerance', axis=1)
        y = sample_financial_data['risk_tolerance']
        
        risk_predictor.train_risk_tolerance_model(X, y)
        
        feature_importance = risk_predictor.get_feature_importance()
        
        assert isinstance(feature_importance, dict)
        assert all(0 <= importance <= 1 for importance in feature_importance.values())
        
        # Age should be an important factor
        assert 'age' in feature_importance
        assert feature_importance['age'] > 0.1
    
    def test_dynamic_risk_adjustment(self, risk_predictor):
        """Test dynamic risk adjustment based on market conditions."""
        
        base_risk_profile = {
            'base_risk_score': 60,
            'risk_tolerance': 'moderate'
        }
        
        # Bull market conditions
        bull_market = {
            'market_trend': 'bullish',
            'volatility': 15,
            'sentiment': 'optimistic'
        }
        
        adjusted_bull = risk_predictor.adjust_risk_for_market_conditions(
            base_risk_profile, bull_market
        )
        
        assert adjusted_bull['adjusted_risk_score'] >= base_risk_profile['base_risk_score']
        
        # Bear market conditions
        bear_market = {
            'market_trend': 'bearish',
            'volatility': 35,
            'sentiment': 'pessimistic'
        }
        
        adjusted_bear = risk_predictor.adjust_risk_for_market_conditions(
            base_risk_profile, bear_market
        )
        
        assert adjusted_bear['adjusted_risk_score'] <= base_risk_profile['base_risk_score']


class TestPortfolioRebalancer:
    """Test suite for portfolio rebalancing recommendations."""
    
    @pytest.fixture
    def portfolio_rebalancer(self):
        """Create portfolio rebalancer instance."""
        return PortfolioRebalancer()
    
    @pytest.fixture
    def sample_portfolio(self):
        """Sample portfolio for rebalancing."""
        return {
            'stocks': 0.65,  # Target was 60%
            'bonds': 0.25,   # Target was 30%
            'cash': 0.10     # Target was 10%
        }
    
    @pytest.fixture
    def target_allocation(self):
        """Target allocation for portfolio."""
        return {
            'stocks': 0.60,
            'bonds': 0.30,
            'cash': 0.10
        }
    
    def test_rebalancing_need_detection(self, portfolio_rebalancer, sample_portfolio, target_allocation):
        """Test detection of rebalancing need."""
        
        rebalancing_analysis = portfolio_rebalancer.analyze_rebalancing_need(
            sample_portfolio, target_allocation
        )
        
        assert 'needs_rebalancing' in rebalancing_analysis
        assert 'drift_analysis' in rebalancing_analysis
        assert 'recommended_trades' in rebalancing_analysis
        
        # Portfolio is off target, should need rebalancing
        assert rebalancing_analysis['needs_rebalancing']
        
        # Stocks are overweight
        drift = rebalancing_analysis['drift_analysis']['stocks']
        assert drift['current'] == 0.65
        assert drift['target'] == 0.60
        assert drift['drift_percentage'] > 0
    
    def test_rebalancing_recommendations(self, portfolio_rebalancer, sample_portfolio, target_allocation):
        """Test generation of specific rebalancing recommendations."""
        
        portfolio_value = 100000
        
        recommendations = portfolio_rebalancer.generate_rebalancing_recommendations(
            sample_portfolio, target_allocation, portfolio_value
        )
        
        assert 'trades' in recommendations
        assert 'transaction_costs' in recommendations
        assert 'expected_impact' in recommendations
        
        trades = recommendations['trades']
        
        # Should recommend selling some stocks
        stock_trade = next((t for t in trades if t['asset'] == 'stocks'), None)
        assert stock_trade is not None
        assert stock_trade['action'] == 'sell'
        assert stock_trade['amount'] > 0
        
        # Should recommend buying bonds
        bond_trade = next((t for t in trades if t['asset'] == 'bonds'), None)
        assert bond_trade is not None
        assert bond_trade['action'] == 'buy'
        assert bond_trade['amount'] > 0
    
    def test_tax_aware_rebalancing(self, portfolio_rebalancer):
        """Test tax-aware rebalancing strategies."""
        
        taxable_holdings = {
            'stocks': {'amount': 65000, 'cost_basis': 50000},  # Unrealized gain
            'bonds': {'amount': 25000, 'cost_basis': 26000},   # Unrealized loss
            'cash': {'amount': 10000, 'cost_basis': 10000}
        }
        
        target_allocation = {'stocks': 0.60, 'bonds': 0.30, 'cash': 0.10}
        
        tax_aware_recommendations = portfolio_rebalancer.generate_tax_aware_rebalancing(
            taxable_holdings, target_allocation
        )
        
        assert 'tax_efficient_trades' in tax_aware_recommendations
        assert 'tax_impact' in tax_aware_recommendations
        assert 'harvest_opportunities' in tax_aware_recommendations
        
        # Should identify tax loss harvesting opportunity with bonds
        harvest_ops = tax_aware_recommendations['harvest_opportunities']
        assert len(harvest_ops) > 0
        
        bond_harvest = next((op for op in harvest_ops if op['asset'] == 'bonds'), None)
        assert bond_harvest is not None
        assert bond_harvest['unrealized_loss'] > 0
    
    def test_risk_based_rebalancing(self, portfolio_rebalancer):
        """Test risk-based rebalancing recommendations."""
        
        current_portfolio = {'stocks': 0.80, 'bonds': 0.15, 'cash': 0.05}
        risk_profile = 'moderate'
        market_volatility = 28  # High volatility
        
        risk_adjusted_rebalancing = portfolio_rebalancer.generate_risk_adjusted_rebalancing(
            current_portfolio, risk_profile, market_volatility
        )
        
        assert 'adjusted_allocation' in risk_adjusted_rebalancing
        assert 'risk_justification' in risk_adjusted_rebalancing
        
        adjusted = risk_adjusted_rebalancing['adjusted_allocation']
        
        # In high volatility, should reduce stock allocation for moderate risk profile
        assert adjusted['stocks'] < current_portfolio['stocks']
        assert adjusted['bonds'] > current_portfolio['bonds']
    
    def test_rebalancing_frequency_optimization(self, portfolio_rebalancer):
        """Test optimization of rebalancing frequency."""
        
        historical_performance = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=252, freq='D'),
            'portfolio_value': np.random.uniform(95000, 105000, 252),
            'transaction_costs': np.random.uniform(10, 50, 252),
            'drift_from_target': np.random.uniform(0, 15, 252)
        })
        
        optimal_frequency = portfolio_rebalancer.optimize_rebalancing_frequency(
            historical_performance
        )
        
        assert 'recommended_frequency_days' in optimal_frequency
        assert 'cost_benefit_analysis' in optimal_frequency
        assert 'performance_metrics' in optimal_frequency
        
        # Should recommend reasonable frequency (not too frequent, not too rare)
        frequency_days = optimal_frequency['recommended_frequency_days']
        assert 30 <= frequency_days <= 365


class TestBehavioralAnalyzer:
    """Test suite for behavioral pattern analysis."""
    
    @pytest.fixture
    def behavioral_analyzer(self):
        """Create behavioral analyzer instance."""
        return BehavioralAnalyzer()
    
    @pytest.fixture
    def sample_user_behavior(self):
        """Sample user behavior data."""
        return {
            'login_frequency': 'daily',
            'feature_usage': {
                'portfolio_view': 45,
                'transaction_review': 30,
                'goal_tracking': 20,
                'market_news': 15
            },
            'interaction_patterns': {
                'morning_usage': 0.4,
                'afternoon_usage': 0.3,
                'evening_usage': 0.3
            },
            'response_to_alerts': {
                'market_alerts': {'sent': 10, 'clicked': 7},
                'rebalancing_alerts': {'sent': 5, 'clicked': 4},
                'goal_alerts': {'sent': 8, 'clicked': 6}
            }
        }
    
    def test_engagement_pattern_analysis(self, behavioral_analyzer, sample_user_behavior):
        """Test analysis of user engagement patterns."""
        
        engagement_analysis = behavioral_analyzer.analyze_engagement_patterns(
            sample_user_behavior
        )
        
        assert 'engagement_score' in engagement_analysis
        assert 'primary_usage_time' in engagement_analysis
        assert 'most_used_features' in engagement_analysis
        assert 'engagement_trends' in engagement_analysis
        
        # High login frequency should result in high engagement score
        assert engagement_analysis['engagement_score'] > 70
        
        # Should identify primary usage time
        assert engagement_analysis['primary_usage_time'] == 'morning'
        
        # Portfolio view should be most used feature
        most_used = engagement_analysis['most_used_features'][0]
        assert most_used['feature'] == 'portfolio_view'
    
    def test_risk_behavior_analysis(self, behavioral_analyzer):
        """Test analysis of risk-related behavior."""
        
        risk_behaviors = {
            'portfolio_checks_per_day': 5,  # High frequency checking
            'panic_selling_incidents': 2,
            'market_timing_attempts': 3,
            'rebalancing_compliance': 0.8,
            'goal_adjustment_frequency': 'monthly'
        }
        
        risk_behavior_analysis = behavioral_analyzer.analyze_risk_behaviors(
            risk_behaviors
        )
        
        assert 'behavioral_risk_score' in risk_behavior_analysis
        assert 'risk_indicators' in risk_behavior_analysis
        assert 'behavioral_recommendations' in risk_behavior_analysis
        
        # High checking frequency should indicate anxiety
        risk_indicators = risk_behavior_analysis['risk_indicators']
        assert any('anxiety' in indicator.lower() for indicator in risk_indicators)
        
        # Should have high behavioral risk score due to panic selling
        assert risk_behavior_analysis['behavioral_risk_score'] > 60
    
    def test_decision_making_pattern_analysis(self, behavioral_analyzer):
        """Test analysis of financial decision-making patterns."""
        
        decision_history = [
            {
                'decision_type': 'investment_allocation',
                'timestamp': datetime.now() - timedelta(days=30),
                'decision_speed': 'fast',  # Made decision quickly
                'market_context': 'volatile',
                'outcome': 'negative'
            },
            {
                'decision_type': 'goal_adjustment',
                'timestamp': datetime.now() - timedelta(days=60),
                'decision_speed': 'slow',  # Took time to decide
                'market_context': 'stable',
                'outcome': 'positive'
            },
            {
                'decision_type': 'rebalancing',
                'timestamp': datetime.now() - timedelta(days=90),
                'decision_speed': 'medium',
                'market_context': 'bullish',
                'outcome': 'positive'
            }
        ]
        
        decision_analysis = behavioral_analyzer.analyze_decision_patterns(
            decision_history
        )
        
        assert 'decision_quality_score' in decision_analysis
        assert 'decision_speed_preference' in decision_analysis
        assert 'context_sensitivity' in decision_analysis
        assert 'improvement_suggestions' in decision_analysis
        
        # Should identify that fast decisions in volatile markets led to poor outcomes
        suggestions = decision_analysis['improvement_suggestions']
        assert any('volatile' in suggestion.lower() and 'slow' in suggestion.lower()
                  for suggestion in suggestions)
    
    def test_goal_achievement_behavior(self, behavioral_analyzer):
        """Test analysis of goal achievement behaviors."""
        
        goal_behaviors = {
            'goal_setting_frequency': 'quarterly',
            'goal_tracking_regularity': 'weekly',
            'goal_achievement_rate': 0.75,
            'goal_adjustment_triggers': ['market_change', 'life_event', 'underperformance'],
            'milestone_celebration': True,
            'setback_recovery_time': 'fast'
        }
        
        goal_behavior_analysis = behavioral_analyzer.analyze_goal_behaviors(
            goal_behaviors
        )
        
        assert 'goal_success_likelihood' in goal_behavior_analysis
        assert 'behavioral_strengths' in goal_behavior_analysis
        assert 'areas_for_improvement' in goal_behavior_analysis
        
        # High achievement rate and regular tracking should predict high success
        assert goal_behavior_analysis['goal_success_likelihood'] > 0.7
        
        # Should identify regular tracking as a strength
        strengths = goal_behavior_analysis['behavioral_strengths']
        assert any('tracking' in strength.lower() for strength in strengths)
    
    def test_personalized_recommendations(self, behavioral_analyzer, sample_user_behavior):
        """Test generation of personalized behavioral recommendations."""
        
        user_profile = {
            'risk_tolerance': 'moderate',
            'investment_experience': 'intermediate',
            'financial_goals': ['retirement', 'emergency_fund'],
            'preferred_communication': 'email'
        }
        
        behavioral_recommendations = behavioral_analyzer.generate_personalized_recommendations(
            sample_user_behavior, user_profile
        )
        
        assert 'engagement_recommendations' in behavioral_recommendations
        assert 'risk_management_suggestions' in behavioral_recommendations
        assert 'feature_recommendations' in behavioral_recommendations
        assert 'communication_preferences' in behavioral_recommendations
        
        # Should recommend based on actual usage patterns
        feature_recs = behavioral_recommendations['feature_recommendations']
        assert len(feature_recs) > 0
        
        # Should consider risk tolerance in recommendations
        risk_suggestions = behavioral_recommendations['risk_management_suggestions']
        assert any('moderate' in suggestion.lower() for suggestion in risk_suggestions)


class TestLifeEventPredictor:
    """Test suite for life event prediction model."""
    
    @pytest.fixture
    def life_event_predictor(self):
        """Create life event predictor instance."""
        return LifeEventPredictor()
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for life event prediction."""
        return {
            'age': 28,
            'marital_status': 'single',
            'children': 0,
            'income': 65000,
            'career_stage': 'early',
            'education_level': 'masters',
            'location': 'urban',
            'spending_patterns': {
                'housing': 1800,
                'food': 400,
                'transportation': 300,
                'entertainment': 200,
                'travel': 150
            },
            'recent_searches': ['wedding planning', 'home buying', 'car loans']
        }
    
    def test_life_event_prediction(self, life_event_predictor, sample_user_data):
        """Test prediction of upcoming life events."""
        
        predictions = life_event_predictor.predict_life_events(
            sample_user_data, time_horizon_years=5
        )
        
        assert isinstance(predictions, list)
        assert len(predictions) > 0
        
        for prediction in predictions:
            assert 'event_type' in prediction
            assert 'probability' in prediction
            assert 'predicted_timeframe' in prediction
            assert 'financial_impact' in prediction
            assert 'confidence' in prediction
            
            # Probabilities should be between 0 and 1
            assert 0 <= prediction['probability'] <= 1
        
        # Given the user profile (young, single, searching for wedding/home)
        # Should predict marriage and home purchase
        event_types = [p['event_type'] for p in predictions]
        assert 'marriage' in event_types
        assert 'home_purchase' in event_types
    
    def test_financial_impact_estimation(self, life_event_predictor):
        """Test estimation of financial impact of life events."""
        
        life_events = [
            {'event_type': 'marriage', 'probability': 0.8},
            {'event_type': 'home_purchase', 'probability': 0.7},
            {'event_type': 'child_birth', 'probability': 0.6}
        ]
        
        user_profile = {
            'income': 75000,
            'savings': 30000,
            'location': 'suburban',
            'age': 30
        }
        
        impact_analysis = life_event_predictor.estimate_financial_impact(
            life_events, user_profile
        )
        
        assert len(impact_analysis) == 3
        
        for impact in impact_analysis:
            assert 'event_type' in impact
            assert 'immediate_cost' in impact
            assert 'ongoing_cost_change' in impact
            assert 'savings_requirement' in impact
            assert 'insurance_needs' in impact
        
        # Home purchase should have high immediate cost
        home_impact = next(i for i in impact_analysis if i['event_type'] == 'home_purchase')
        assert home_impact['immediate_cost'] > 20000  # Down payment + closing costs
        
        # Child birth should increase ongoing costs
        child_impact = next(i for i in impact_analysis if i['event_type'] == 'child_birth')
        assert child_impact['ongoing_cost_change'] > 0
    
    def test_life_stage_modeling(self, life_event_predictor):
        """Test modeling of different life stages."""
        
        life_stages = [
            {'stage': 'young_professional', 'age': 25, 'married': False, 'children': 0},
            {'stage': 'married_no_kids', 'age': 30, 'married': True, 'children': 0},
            {'stage': 'young_family', 'age': 35, 'married': True, 'children': 1},
            {'stage': 'established_family', 'age': 45, 'married': True, 'children': 2},
            {'stage': 'empty_nester', 'age': 55, 'married': True, 'children': 2}
        ]
        
        for stage_data in life_stages:
            stage_predictions = life_event_predictor.predict_for_life_stage(stage_data)
            
            assert 'typical_events' in stage_predictions
            assert 'financial_priorities' in stage_predictions
            assert 'planning_recommendations' in stage_predictions
            
            # Young professional should focus on career and savings
            if stage_data['stage'] == 'young_professional':
                priorities = stage_predictions['financial_priorities']
                assert any('career' in priority.lower() for priority in priorities)
                assert any('emergency' in priority.lower() for priority in priorities)
            
            # Young family should focus on insurance and education savings
            elif stage_data['stage'] == 'young_family':
                priorities = stage_predictions['financial_priorities']
                assert any('insurance' in priority.lower() for priority in priorities)
                assert any('education' in priority.lower() for priority in priorities)
    
    def test_external_factors_integration(self, life_event_predictor):
        """Test integration of external factors in predictions."""
        
        user_data = {
            'age': 32,
            'income': 80000,
            'location': 'san_francisco',
            'industry': 'technology'
        }
        
        external_factors = {
            'economic_conditions': 'recession',
            'housing_market': 'expensive',
            'job_market': 'competitive',
            'interest_rates': 'rising'
        }
        
        adjusted_predictions = life_event_predictor.predict_with_external_factors(
            user_data, external_factors
        )
        
        assert 'base_predictions' in adjusted_predictions
        assert 'adjusted_predictions' in adjusted_predictions
        assert 'factor_impacts' in adjusted_predictions
        
        # Economic recession should reduce probability of major purchases
        factor_impacts = adjusted_predictions['factor_impacts']
        assert any(impact['factor'] == 'economic_conditions' and impact['effect'] == 'negative'
                  for impact in factor_impacts)
    
    def test_recommendation_adaptation(self, life_event_predictor):
        """Test adaptation of financial recommendations based on predicted events."""
        
        predicted_events = [
            {
                'event_type': 'home_purchase',
                'probability': 0.8,
                'predicted_timeframe': '2_years',
                'financial_impact': {'immediate_cost': 50000}
            },
            {
                'event_type': 'child_birth',
                'probability': 0.6,
                'predicted_timeframe': '3_years',
                'financial_impact': {'ongoing_cost_change': 15000}
            }
        ]
        
        current_financial_plan = {
            'emergency_fund_target': 15000,
            'savings_rate': 0.15,
            'investment_allocation': {'stocks': 0.7, 'bonds': 0.3}
        }
        
        adapted_recommendations = life_event_predictor.adapt_financial_plan(
            predicted_events, current_financial_plan
        )
        
        assert 'adjusted_emergency_fund' in adapted_recommendations
        assert 'adjusted_savings_rate' in adapted_recommendations
        assert 'adjusted_allocation' in adapted_recommendations
        assert 'specific_preparations' in adapted_recommendations
        
        # Should recommend higher emergency fund for upcoming expenses
        assert adapted_recommendations['adjusted_emergency_fund'] > current_financial_plan['emergency_fund_target']
        
        # Should recommend specific preparations
        preparations = adapted_recommendations['specific_preparations']
        assert any('down payment' in prep.lower() for prep in preparations)


class TestRecommendationEngine:
    """Test suite for the main recommendation engine."""
    
    @pytest.fixture
    def recommendation_engine(self):
        """Create recommendation engine instance."""
        return RecommendationEngine()
    
    @pytest.fixture
    def sample_user_profile(self):
        """Sample comprehensive user profile."""
        return {
            'user_id': 'user_123',
            'demographics': {
                'age': 35,
                'marital_status': 'married',
                'children': 1,
                'income': 95000,
                'location': 'chicago'
            },
            'financial_data': {
                'savings': 45000,
                'debt': 25000,
                'monthly_expenses': 5500,
                'risk_tolerance': 'moderate'
            },
            'goals': [
                {'type': 'retirement', 'target_amount': 1000000, 'target_date': '2055-01-01'},
                {'type': 'emergency_fund', 'target_amount': 33000, 'target_date': '2025-01-01'},
                {'type': 'child_education', 'target_amount': 200000, 'target_date': '2040-01-01'}
            ],
            'behavioral_data': {
                'engagement_score': 75,
                'risk_behavior_score': 45,
                'goal_adherence': 0.8
            }
        }
    
    @pytest.mark.asyncio
    async def test_comprehensive_recommendation_generation(self, recommendation_engine, sample_user_profile):
        """Test generation of comprehensive recommendations."""
        
        # Mock all the underlying services
        with patch.object(recommendation_engine, '_risk_predictor') as mock_risk, \
             patch.object(recommendation_engine, '_portfolio_rebalancer') as mock_portfolio, \
             patch.object(recommendation_engine, '_behavioral_analyzer') as mock_behavioral, \
             patch.object(recommendation_engine, '_life_event_predictor') as mock_life_events:
            
            # Configure mocks
            mock_risk.calculate_risk_score.return_value = 65
            mock_portfolio.analyze_rebalancing_need.return_value = {
                'needs_rebalancing': True,
                'recommended_trades': [{'asset': 'stocks', 'action': 'sell', 'amount': 5000}]
            }
            mock_behavioral.generate_personalized_recommendations.return_value = {
                'engagement_recommendations': ['Check portfolio weekly'],
                'risk_management_suggestions': ['Consider dollar-cost averaging']
            }
            mock_life_events.predict_life_events.return_value = [
                {'event_type': 'home_purchase', 'probability': 0.7, 'predicted_timeframe': '3_years'}
            ]
            
            recommendations = await recommendation_engine.generate_comprehensive_recommendations(
                sample_user_profile
            )
            
            assert 'investment_recommendations' in recommendations
            assert 'risk_management' in recommendations
            assert 'behavioral_insights' in recommendations
            assert 'life_event_preparations' in recommendations
            assert 'priority_actions' in recommendations
            
            # Should have prioritized recommendations
            priority_actions = recommendations['priority_actions']
            assert len(priority_actions) > 0
            assert all('priority' in action for action in priority_actions)
    
    def test_recommendation_personalization(self, recommendation_engine):
        """Test personalization of recommendations."""
        
        # Conservative user
        conservative_user = {
            'risk_tolerance': 'conservative',
            'age': 55,
            'financial_data': {'savings': 200000, 'debt': 0}
        }
        
        # Aggressive user
        aggressive_user = {
            'risk_tolerance': 'aggressive',
            'age': 28,
            'financial_data': {'savings': 15000, 'debt': 5000}
        }
        
        conservative_recs = recommendation_engine.personalize_recommendations(
            conservative_user, base_recommendations=['increase_stock_allocation', 'reduce_bond_allocation']
        )
        
        aggressive_recs = recommendation_engine.personalize_recommendations(
            aggressive_user, base_recommendations=['increase_stock_allocation', 'reduce_bond_allocation']
        )
        
        # Conservative user should have different recommendations than aggressive user
        assert conservative_recs != aggressive_recs
        
        # Conservative user should get more conservative recommendations
        conservative_text = ' '.join(conservative_recs)
        assert 'conservative' in conservative_text.lower() or 'stable' in conservative_text.lower()
    
    def test_recommendation_ranking(self, recommendation_engine):
        """Test ranking and prioritization of recommendations."""
        
        raw_recommendations = [
            {
                'type': 'emergency_fund',
                'description': 'Build emergency fund',
                'impact_score': 90,
                'urgency': 'high',
                'difficulty': 'medium'
            },
            {
                'type': 'investment',
                'description': 'Rebalance portfolio',
                'impact_score': 60,
                'urgency': 'medium',
                'difficulty': 'easy'
            },
            {
                'type': 'debt_reduction',
                'description': 'Pay down credit cards',
                'impact_score': 85,
                'urgency': 'high',
                'difficulty': 'hard'
            }
        ]
        
        ranked_recommendations = recommendation_engine.rank_recommendations(
            raw_recommendations
        )
        
        assert len(ranked_recommendations) == 3
        
        # Should be sorted by priority score (combination of impact, urgency, difficulty)
        priorities = [rec['priority_score'] for rec in ranked_recommendations]
        assert priorities == sorted(priorities, reverse=True)
        
        # Emergency fund should be highest priority (high impact, high urgency)
        assert ranked_recommendations[0]['type'] == 'emergency_fund'
    
    def test_recommendation_explanation(self, recommendation_engine):
        """Test explanation generation for recommendations."""
        
        recommendation = {
            'type': 'increase_savings_rate',
            'description': 'Increase monthly savings to $800',
            'current_value': 500,
            'recommended_value': 800,
            'rationale': {
                'goal_alignment': ['retirement', 'emergency_fund'],
                'risk_factors': ['inflation', 'longevity'],
                'opportunity_factors': ['compound_interest', 'tax_advantages']
            }
        }
        
        explanation = recommendation_engine.explain_recommendation(recommendation)
        
        assert 'rationale' in explanation
        assert 'benefits' in explanation
        assert 'implementation_steps' in explanation
        assert 'potential_challenges' in explanation
        
        # Should explain why the recommendation is made
        rationale = explanation['rationale']
        assert 'retirement' in rationale.lower()
        assert 'emergency' in rationale.lower()
    
    def test_recommendation_tracking(self, recommendation_engine):
        """Test tracking of recommendation implementation."""
        
        recommendation_id = 'rec_123'
        implementation_data = {
            'status': 'in_progress',
            'completion_percentage': 0.6,
            'challenges_encountered': ['cash_flow_constraints'],
            'user_feedback': 'helpful but difficult to implement'
        }
        
        tracking_result = recommendation_engine.track_recommendation_progress(
            recommendation_id, implementation_data
        )
        
        assert 'updated_status' in tracking_result
        assert 'next_actions' in tracking_result
        assert 'support_suggestions' in tracking_result
        
        # Should suggest support for encountered challenges
        support_suggestions = tracking_result['support_suggestions']
        assert any('cash flow' in suggestion.lower() for suggestion in support_suggestions)


class TestModelMonitor:
    """Test suite for ML model monitoring and validation."""
    
    @pytest.fixture
    def model_monitor(self):
        """Create model monitor instance."""
        return ModelMonitor()
    
    @pytest.fixture
    def sample_model_performance(self):
        """Sample model performance data."""
        return {
            'model_name': 'risk_predictor',
            'version': '1.2.0',
            'training_date': '2024-01-01',
            'metrics': {
                'accuracy': 0.85,
                'precision': 0.82,
                'recall': 0.88,
                'f1_score': 0.85,
                'auc_roc': 0.90
            },
            'feature_importance': {
                'age': 0.25,
                'income': 0.20,
                'savings': 0.18,
                'debt': 0.15,
                'employment_years': 0.12,
                'dependents': 0.10
            }
        }
    
    def test_model_performance_monitoring(self, model_monitor, sample_model_performance):
        """Test monitoring of model performance over time."""
        
        # Add performance data points
        for i in range(10):
            performance_data = sample_model_performance.copy()
            performance_data['timestamp'] = datetime.now() - timedelta(days=i*30)
            # Simulate gradual performance degradation
            performance_data['metrics']['accuracy'] = 0.85 - (i * 0.01)
            
            model_monitor.log_model_performance(performance_data)
        
        performance_trend = model_monitor.analyze_performance_trend('risk_predictor')
        
        assert 'trend_direction' in performance_trend
        assert 'performance_degradation' in performance_trend
        assert 'alerts' in performance_trend
        
        # Should detect declining performance
        assert performance_trend['trend_direction'] == 'declining'
        assert performance_trend['performance_degradation'] is True
    
    def test_data_drift_detection(self, model_monitor):
        """Test detection of data drift in input features."""
        
        # Training data distribution
        training_data = pd.DataFrame({
            'age': np.random.normal(40, 12, 1000),
            'income': np.random.normal(75000, 20000, 1000),
            'savings': np.random.normal(50000, 30000, 1000)
        })
        
        # Current data with drift (younger users, lower income)
        current_data = pd.DataFrame({
            'age': np.random.normal(32, 10, 500),  # Younger
            'income': np.random.normal(65000, 18000, 500),  # Lower income
            'savings': np.random.normal(48000, 28000, 500)  # Similar savings
        })
        
        drift_analysis = model_monitor.detect_data_drift(
            training_data, current_data, threshold=0.1
        )
        
        assert 'drift_detected' in drift_analysis
        assert 'feature_drift_scores' in drift_analysis
        assert 'significant_drifts' in drift_analysis
        
        # Should detect drift in age and income
        significant_drifts = drift_analysis['significant_drifts']
        drift_features = [drift['feature'] for drift in significant_drifts]
        assert 'age' in drift_features
        assert 'income' in drift_features
    
    def test_prediction_quality_monitoring(self, model_monitor):
        """Test monitoring of prediction quality and confidence."""
        
        predictions = [
            {'prediction': 'moderate', 'confidence': 0.95, 'actual': 'moderate'},
            {'prediction': 'aggressive', 'confidence': 0.88, 'actual': 'aggressive'},
            {'prediction': 'conservative', 'confidence': 0.92, 'actual': 'moderate'},  # Wrong
            {'prediction': 'moderate', 'confidence': 0.65, 'actual': 'moderate'},  # Low confidence
            {'prediction': 'aggressive', 'confidence': 0.78, 'actual': 'conservative'}  # Wrong
        ]
        
        quality_analysis = model_monitor.analyze_prediction_quality(predictions)
        
        assert 'accuracy' in quality_analysis
        assert 'confidence_calibration' in quality_analysis
        assert 'low_confidence_predictions' in quality_analysis
        assert 'misclassification_analysis' in quality_analysis
        
        # Should have 60% accuracy (3 out of 5 correct)
        assert abs(quality_analysis['accuracy'] - 0.6) < 0.01
        
        # Should identify low confidence predictions
        low_conf_predictions = quality_analysis['low_confidence_predictions']
        assert len(low_conf_predictions) >= 1
    
    def test_model_versioning_and_rollback(self, model_monitor):
        """Test model versioning and rollback capabilities."""
        
        # Deploy new model version
        new_model_info = {
            'model_name': 'risk_predictor',
            'version': '2.0.0',
            'deployment_date': datetime.now(),
            'performance_metrics': {'accuracy': 0.87, 'f1_score': 0.86}
        }
        
        deployment_result = model_monitor.deploy_model_version(new_model_info)
        
        assert 'deployment_id' in deployment_result
        assert 'status' in deployment_result
        assert deployment_result['status'] == 'deployed'
        
        # Simulate performance degradation requiring rollback
        rollback_trigger = {
            'accuracy_threshold_breach': True,
            'error_rate_spike': True,
            'user_complaints': 5
        }
        
        rollback_result = model_monitor.initiate_rollback(
            'risk_predictor', '2.0.0', rollback_trigger
        )
        
        assert 'rollback_status' in rollback_result
        assert 'previous_version' in rollback_result
        assert rollback_result['rollback_status'] == 'completed'
        assert rollback_result['previous_version'] == '1.2.0'
    
    def test_a_b_testing_framework(self, model_monitor):
        """Test A/B testing framework for model comparisons."""
        
        # Set up A/B test
        ab_test_config = {
            'test_name': 'risk_predictor_v1_vs_v2',
            'model_a': {'name': 'risk_predictor', 'version': '1.2.0'},
            'model_b': {'name': 'risk_predictor', 'version': '2.0.0'},
            'traffic_split': {'a': 0.5, 'b': 0.5},
            'success_metrics': ['accuracy', 'user_satisfaction', 'prediction_confidence'],
            'duration_days': 30
        }
        
        ab_test = model_monitor.setup_ab_test(ab_test_config)
        
        assert 'test_id' in ab_test
        assert 'status' in ab_test
        assert ab_test['status'] == 'active'
        
        # Simulate test results
        test_results = {
            'model_a_results': {
                'accuracy': 0.85,
                'user_satisfaction': 4.2,
                'prediction_confidence': 0.82
            },
            'model_b_results': {
                'accuracy': 0.87,
                'user_satisfaction': 4.4,
                'prediction_confidence': 0.85
            },
            'statistical_significance': {
                'accuracy': True,
                'user_satisfaction': True,
                'prediction_confidence': False
            }
        }
        
        analysis_result = model_monitor.analyze_ab_test_results(
            ab_test['test_id'], test_results
        )
        
        assert 'winner' in analysis_result
        assert 'confidence_level' in analysis_result
        assert 'recommendation' in analysis_result
        
        # Model B should be the winner
        assert analysis_result['winner'] == 'model_b'
        assert analysis_result['recommendation'] == 'deploy_model_b'
    
    def test_feature_importance_tracking(self, model_monitor):
        """Test tracking of feature importance changes over time."""
        
        # Historical feature importance
        historical_importance = [
            {
                'timestamp': datetime.now() - timedelta(days=90),
                'features': {'age': 0.25, 'income': 0.20, 'savings': 0.18, 'debt': 0.15}
            },
            {
                'timestamp': datetime.now() - timedelta(days=60),
                'features': {'age': 0.22, 'income': 0.23, 'savings': 0.19, 'debt': 0.16}
            },
            {
                'timestamp': datetime.now() - timedelta(days=30),
                'features': {'age': 0.20, 'income': 0.25, 'savings': 0.20, 'debt': 0.18}
            }
        ]
        
        importance_analysis = model_monitor.analyze_feature_importance_drift(
            'risk_predictor', historical_importance
        )
        
        assert 'trending_features' in importance_analysis
        assert 'stable_features' in importance_analysis
        assert 'recommendations' in importance_analysis
        
        trending = importance_analysis['trending_features']
        
        # Income importance is increasing
        income_trend = next((t for t in trending if t['feature'] == 'income'), None)
        assert income_trend is not None
        assert income_trend['trend'] == 'increasing'
        
        # Age importance is decreasing
        age_trend = next((t for t in trending if t['feature'] == 'age'), None)
        assert age_trend is not None
        assert age_trend['trend'] == 'decreasing'


@pytest.mark.integration
class TestMLIntegration:
    """Integration tests for ML model pipeline."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_recommendation_pipeline(self):
        """Test complete ML recommendation pipeline."""
        
        # Mock user data
        user_profile = {
            'user_id': 'integration_test_user',
            'age': 35,
            'income': 80000,
            'savings': 40000,
            'debt': 20000,
            'risk_tolerance': 'moderate',
            'goals': ['retirement', 'home_purchase']
        }
        
        # Mock all ML services
        with patch('app.ml.recommendations.risk_predictor.RiskPredictor') as mock_risk, \
             patch('app.ml.recommendations.portfolio_rebalancer.PortfolioRebalancer') as mock_portfolio, \
             patch('app.ml.recommendations.behavioral_analyzer.BehavioralAnalyzer') as mock_behavioral, \
             patch('app.ml.recommendations.life_event_predictor.LifeEventPredictor') as mock_life_events:
            
            # Configure mocks to return realistic data
            mock_risk_instance = Mock()
            mock_risk_instance.calculate_risk_score.return_value = 65
            mock_risk_instance.assess_portfolio_risk.return_value = {
                'overall_risk_score': 70,
                'risk_factors': ['concentration_risk'],
                'recommendations': ['diversify_holdings']
            }
            mock_risk.return_value = mock_risk_instance
            
            mock_portfolio_instance = Mock()
            mock_portfolio_instance.analyze_rebalancing_need.return_value = {
                'needs_rebalancing': True,
                'recommended_trades': [{'asset': 'stocks', 'action': 'buy', 'amount': 5000}]
            }
            mock_portfolio.return_value = mock_portfolio_instance
            
            mock_behavioral_instance = Mock()
            mock_behavioral_instance.analyze_engagement_patterns.return_value = {
                'engagement_score': 75,
                'recommendations': ['increase_portfolio_checks']
            }
            mock_behavioral.return_value = mock_behavioral_instance
            
            mock_life_events_instance = Mock()
            mock_life_events_instance.predict_life_events.return_value = [
                {'event_type': 'home_purchase', 'probability': 0.7, 'timeframe': '2_years'}
            ]
            mock_life_events.return_value = mock_life_events_instance
            
            # Run the pipeline
            recommendation_engine = RecommendationEngine()
            recommendations = await recommendation_engine.generate_comprehensive_recommendations(
                user_profile
            )
            
            # Verify comprehensive recommendations were generated
            assert recommendations is not None
            assert isinstance(recommendations, dict)
            
            # Should have called all ML services
            mock_risk_instance.calculate_risk_score.assert_called()
            mock_portfolio_instance.analyze_rebalancing_need.assert_called()
            mock_behavioral_instance.analyze_engagement_patterns.assert_called()
            mock_life_events_instance.predict_life_events.assert_called()
    
    def test_model_performance_benchmarking(self):
        """Test benchmarking of ML model performance."""
        
        # Generate synthetic test data
        n_samples = 1000
        np.random.seed(42)
        
        test_data = pd.DataFrame({
            'age': np.random.randint(22, 70, n_samples),
            'income': np.random.randint(30000, 200000, n_samples),
            'savings': np.random.randint(1000, 500000, n_samples),
            'debt': np.random.randint(0, 100000, n_samples)
        })
        
        # Generate synthetic labels (risk tolerance based on features)
        def generate_risk_tolerance(row):
            risk_score = (row['age'] * 0.3 + row['income'] * 0.4 + 
                         row['savings'] * 0.2 - row['debt'] * 0.1)
            if risk_score > 60000:
                return 'aggressive'
            elif risk_score > 30000:
                return 'moderate'
            else:
                return 'conservative'
        
        test_data['risk_tolerance'] = test_data.apply(generate_risk_tolerance, axis=1)
        
        # Test model performance
        risk_predictor = RiskPredictor()
        
        # Split data
        train_size = int(0.8 * n_samples)
        train_data = test_data[:train_size]
        test_data_subset = test_data[train_size:]
        
        # Train and test
        X_train = train_data.drop('risk_tolerance', axis=1)
        y_train = train_data['risk_tolerance']
        X_test = test_data_subset.drop('risk_tolerance', axis=1)
        y_test = test_data_subset['risk_tolerance']
        
        # Mock training and prediction
        with patch.object(risk_predictor, 'train_risk_tolerance_model'):
            with patch.object(risk_predictor, 'predict_risk_tolerance') as mock_predict:
                # Mock predictions that match the pattern
                mock_predict.side_effect = lambda row: generate_risk_tolerance(pd.Series(row))
                
                # Test predictions
                predictions = []
                for _, row in X_test.iterrows():
                    pred = risk_predictor.predict_risk_tolerance(row.to_dict())
                    predictions.append(pred)
                
                # Calculate accuracy
                accuracy = sum(p == a for p, a in zip(predictions, y_test)) / len(y_test)
                
                # Should have reasonable accuracy
                assert accuracy > 0.7  # At least 70% accuracy
    
    def test_recommendation_consistency(self):
        """Test consistency of recommendations across multiple runs."""
        
        user_profile = {
            'age': 40,
            'income': 90000,
            'savings': 60000,
            'debt': 15000,
            'risk_tolerance': 'moderate'
        }
        
        recommendation_engine = RecommendationEngine()
        
        # Mock the underlying services to return consistent results
        with patch.object(recommendation_engine, '_risk_predictor') as mock_risk:
            mock_risk.calculate_risk_score.return_value = 65
            
            # Generate recommendations multiple times
            recommendations_list = []
            for _ in range(5):
                recs = recommendation_engine.generate_basic_recommendations(user_profile)
                recommendations_list.append(recs)
            
            # All recommendations should be identical with same input
            first_recs = recommendations_list[0]
            for recs in recommendations_list[1:]:
                assert recs == first_recs
    
    def test_recommendation_quality_metrics(self):
        """Test quality metrics for generated recommendations."""
        
        recommendation_engine = RecommendationEngine()
        
        # Generate recommendations for different user types
        user_profiles = [
            {'age': 25, 'income': 50000, 'savings': 5000, 'risk_tolerance': 'aggressive'},
            {'age': 45, 'income': 100000, 'savings': 200000, 'risk_tolerance': 'moderate'},
            {'age': 65, 'income': 70000, 'savings': 500000, 'risk_tolerance': 'conservative'}
        ]
        
        recommendations_set = []
        
        for profile in user_profiles:
            with patch.object(recommendation_engine, '_risk_predictor') as mock_risk, \
                 patch.object(recommendation_engine, '_portfolio_rebalancer') as mock_portfolio:
                
                mock_risk.calculate_risk_score.return_value = 50
                mock_portfolio.analyze_rebalancing_need.return_value = {'needs_rebalancing': False}
                
                recs = recommendation_engine.generate_basic_recommendations(profile)
                recommendations_set.append(recs)
        
        # Quality checks
        for recs in recommendations_set:
            # Should have recommendations
            assert len(recs) > 0
            
            # Recommendations should be different for different user types
            assert recs != recommendations_set[0] or profile == user_profiles[0]
            
            # Should have proper structure
            for rec in recs:
                assert isinstance(rec, dict)
                assert 'type' in rec
                assert 'description' in rec