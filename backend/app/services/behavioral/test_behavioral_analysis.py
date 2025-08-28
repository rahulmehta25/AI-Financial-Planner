"""
Test suite for Behavioral Finance Analysis System
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np

from behavioral_analysis import (
    BehavioralFinanceAnalyzer,
    BehavioralBias,
    NudgeType,
    GoalBucket,
    CommitmentLevel,
    MentalAccount,
    GoalBasedBucket
)


class TestBehavioralFinanceAnalyzer:
    """Test cases for BehavioralFinanceAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return BehavioralFinanceAnalyzer()
    
    @pytest.fixture
    def sample_transaction_history(self):
        """Create sample transaction history"""
        return [
            {
                'date': (datetime.now() - timedelta(days=90)).isoformat(),
                'type': 'buy',
                'ticker': 'AAPL',
                'return_percentage': 0.15,
                'return_value': 1500,
                'holding_days': 45,
                'market_momentum': 0.8,
                'prior_return': 0.12,
                'reference_price': 150,
                'execution_price': 152,
                'decision_time_hours': 24,
                'research_sources': 3
            },
            {
                'date': (datetime.now() - timedelta(days=60)).isoformat(),
                'type': 'sell',
                'ticker': 'GOOGL',
                'return_percentage': -0.08,
                'return_value': -800,
                'holding_days': 20,
                'market_momentum': -0.5,
                'trigger': 'market_decline'
            },
            {
                'date': (datetime.now() - timedelta(days=30)).isoformat(),
                'type': 'buy',
                'ticker': 'MSFT',
                'return_percentage': 0.05,
                'return_value': 500,
                'holding_days': 30,
                'market_momentum': 0.3,
                'prior_return': 0.08
            },
            {
                'date': (datetime.now() - timedelta(days=15)).isoformat(),
                'type': 'sell',
                'ticker': 'TSLA',
                'return_percentage': 0.25,
                'return_value': 2500,
                'holding_days': 60,
                'market_momentum': 0.9
            }
        ]
    
    @pytest.fixture
    def sample_portfolio_history(self):
        """Create sample portfolio history"""
        return [
            {
                'date': (datetime.now() - timedelta(days=90)).isoformat(),
                'positions': [
                    {'ticker': 'AAPL', 'weight': 0.30, 'recent_return': 0.12, 'is_domestic': True},
                    {'ticker': 'GOOGL', 'weight': 0.25, 'recent_return': -0.05, 'is_domestic': True},
                    {'ticker': 'MSFT', 'weight': 0.20, 'recent_return': 0.08, 'is_domestic': True},
                    {'ticker': 'AMZN', 'weight': 0.15, 'recent_return': 0.15, 'is_domestic': True},
                    {'ticker': 'BTC', 'weight': 0.10, 'recent_return': 0.30, 'is_domestic': False}
                ],
                'equity_allocation': 0.75,
                'volatility': 0.18
            },
            {
                'date': (datetime.now() - timedelta(days=60)).isoformat(),
                'positions': [
                    {'ticker': 'AAPL', 'weight': 0.35, 'recent_return': 0.10},
                    {'ticker': 'GOOGL', 'weight': 0.20, 'recent_return': -0.03},
                    {'ticker': 'MSFT', 'weight': 0.25, 'recent_return': 0.06}
                ],
                'equity_allocation': 0.80,
                'volatility': 0.22
            },
            {
                'date': (datetime.now() - timedelta(days=30)).isoformat(),
                'positions': [
                    {'ticker': 'AAPL', 'weight': 0.40, 'recent_return': 0.08},
                    {'ticker': 'GOOGL', 'weight': 0.30, 'recent_return': 0.02}
                ],
                'equity_allocation': 0.70,
                'volatility': 0.25
            }
        ]
    
    @pytest.fixture
    def sample_questionnaire(self):
        """Create sample questionnaire responses"""
        return {
            'risk_tolerance': 0.6,
            'financial_literacy': {
                'compound_interest': 0.8,
                'inflation': 0.7,
                'diversification': 0.9,
                'risk_return': 0.6,
                'market_efficiency': 0.5
            },
            'social_influence': 0.3
        }
    
    @pytest.mark.asyncio
    async def test_behavioral_profile_analysis(
        self,
        analyzer,
        sample_transaction_history,
        sample_portfolio_history,
        sample_questionnaire
    ):
        """Test behavioral profile analysis"""
        profile = await analyzer.analyze_behavioral_profile(
            user_id="test_user",
            transaction_history=sample_transaction_history,
            portfolio_history=sample_portfolio_history,
            questionnaire_responses=sample_questionnaire
        )
        
        assert profile is not None
        assert profile.user_id == "test_user"
        assert len(profile.detected_biases) > 0
        assert 0 <= profile.risk_perception <= 1
        assert profile.loss_aversion_coefficient > 0
        assert 0 <= profile.time_preference <= 1
        assert profile.decision_style in ['analytical', 'intuitive', 'dependent', 'spontaneous']
    
    @pytest.mark.asyncio
    async def test_loss_aversion_detection(
        self,
        analyzer,
        sample_transaction_history,
        sample_portfolio_history
    ):
        """Test loss aversion bias detection"""
        detection = await analyzer._detect_loss_aversion(
            sample_transaction_history,
            sample_portfolio_history
        )
        
        assert detection is not None
        assert detection.bias_type == BehavioralBias.LOSS_AVERSION
        assert 0 <= detection.severity <= 1
        assert 0 <= detection.confidence <= 1
        assert isinstance(detection.evidence, list)
        assert isinstance(detection.recommended_nudges, list)
    
    @pytest.mark.asyncio
    async def test_overconfidence_detection(
        self,
        analyzer,
        sample_transaction_history,
        sample_portfolio_history
    ):
        """Test overconfidence bias detection"""
        detection = await analyzer._detect_overconfidence(
            sample_transaction_history,
            sample_portfolio_history
        )
        
        assert detection is not None
        assert detection.bias_type == BehavioralBias.OVERCONFIDENCE
        if detection.evidence:
            assert detection.severity > 0
    
    @pytest.mark.asyncio
    async def test_nudge_engine(self, analyzer):
        """Test nudge engine creation"""
        # First create a profile
        profile = await analyzer.analyze_behavioral_profile(
            user_id="test_user",
            transaction_history=[],
            portfolio_history=[]
        )
        
        # Create nudges
        context = {
            'portfolio_value': 100000,
            'historical_return': 8.5,
            'urgency': 'moderate'
        }
        
        nudges = await analyzer.create_nudge_engine(
            user_id="test_user",
            context=context
        )
        
        assert isinstance(nudges, list)
        for nudge in nudges:
            assert nudge.nudge_type in NudgeType
            assert nudge.message
            assert nudge.action
            assert 0 <= nudge.expected_effectiveness <= 1
    
    @pytest.mark.asyncio
    async def test_mental_accounting_optimization(self, analyzer):
        """Test mental accounting optimization"""
        current_accounts = [
            MentalAccount(
                name="Emergency",
                purpose="Emergency fund",
                current_value=10000,
                target_value=20000,
                time_horizon=6,
                risk_tolerance="low",
                assets=["cash", "bonds"],
                allocation_percentage=0.2,
                behavioral_constraints=[]
            ),
            MentalAccount(
                name="Vacation",
                purpose="Annual vacation",
                current_value=5000,
                target_value=10000,
                time_horizon=12,
                risk_tolerance="moderate",
                assets=["stocks", "bonds"],
                allocation_percentage=0.1,
                behavioral_constraints=[]
            ),
            MentalAccount(
                name="Retirement",
                purpose="Retirement savings",
                current_value=50000,
                target_value=1000000,
                time_horizon=360,
                risk_tolerance="moderate",
                assets=["stocks", "bonds", "real_estate"],
                allocation_percentage=0.7,
                behavioral_constraints=[]
            )
        ]
        
        goals = [
            {
                'name': 'Emergency Fund',
                'description': 'Emergency savings',
                'target_amount': 25000,
                'time_horizon_months': 6
            },
            {
                'name': 'House Down Payment',
                'description': 'Down payment for house',
                'target_amount': 100000,
                'time_horizon_months': 36
            }
        ]
        
        optimized = await analyzer.optimize_mental_accounting(
            user_id="test_user",
            current_accounts=current_accounts,
            goals=goals
        )
        
        assert len(optimized) >= len(current_accounts)
        total_allocation = sum(acc.allocation_percentage for acc in optimized)
        assert abs(total_allocation - 1.0) < 0.01  # Should sum to 100%
    
    @pytest.mark.asyncio
    async def test_goal_based_buckets(self, analyzer):
        """Test goal-based bucket creation"""
        goals = [
            {
                'name': 'Emergency Fund',
                'type': 'emergency',
                'target_amount': 20000,
                'time_horizon_months': 3,
                'priority': 1
            },
            {
                'name': 'Kids Education',
                'type': 'education',
                'target_amount': 200000,
                'time_horizon_months': 180,
                'priority': 2
            },
            {
                'name': 'Retirement',
                'type': 'retirement',
                'target_amount': 1000000,
                'time_horizon_months': 360,
                'priority': 2
            },
            {
                'name': 'World Travel',
                'type': 'lifestyle',
                'target_amount': 50000,
                'time_horizon_months': 60,
                'priority': 4
            }
        ]
        
        buckets = await analyzer.create_goal_based_buckets(
            user_id="test_user",
            goals=goals,
            total_portfolio_value=100000
        )
        
        assert len(buckets) > 0
        
        # Check bucket properties
        for bucket in buckets:
            assert bucket.bucket_type in GoalBucket
            assert bucket.priority >= 1
            assert 0 <= bucket.target_allocation <= 1
            assert bucket.time_horizon > 0
            assert bucket.required_return >= 0
            assert bucket.risk_budget >= 0
            assert len(bucket.behavioral_guardrails) > 0
        
        # Check allocation sums to 100%
        total_allocation = sum(b.target_allocation for b in buckets)
        assert abs(total_allocation - 1.0) < 0.01
    
    @pytest.mark.asyncio
    async def test_commitment_devices(self, analyzer):
        """Test commitment device implementation"""
        # Create profile first
        profile = await analyzer.analyze_behavioral_profile(
            user_id="test_user",
            transaction_history=[],
            portfolio_history=[]
        )
        
        portfolio = {
            'value': 100000,
            'positions': [
                {'ticker': 'AAPL', 'weight': 0.4},
                {'ticker': 'GOOGL', 'weight': 0.3}
            ]
        }
        
        goals = [
            {
                'id': 'goal1',
                'name': 'Retirement',
                'priority': 1,
                'target_amount': 1000000
            }
        ]
        
        devices = await analyzer.implement_commitment_devices(
            user_id="test_user",
            portfolio=portfolio,
            goals=goals
        )
        
        assert isinstance(devices, list)
        for device in devices:
            assert device.level in CommitmentLevel
            assert device.description
            assert len(device.trigger_conditions) > 0
            assert len(device.actions) > 0
            assert 0 <= device.effectiveness_score <= 1
            assert 0 <= device.user_acceptance <= 1
    
    @pytest.mark.asyncio
    async def test_behavioral_portfolio_construction(self, analyzer):
        """Test behavior-optimized portfolio construction"""
        # Create profile
        profile = await analyzer.analyze_behavioral_profile(
            user_id="test_user",
            transaction_history=[],
            portfolio_history=[]
        )
        
        constraints = {
            'max_risk': 0.20,
            'min_return': 0.05,
            'max_positions': 20
        }
        
        portfolio = await analyzer.build_behavioral_portfolio(
            user_id="test_user",
            capital=100000,
            constraints=constraints
        )
        
        assert portfolio is not None
        assert portfolio['capital'] == 100000
        assert len(portfolio['positions']) > 0
        assert portfolio['expected_return'] >= 0
        assert portfolio['risk'] >= 0
        assert 'behavioral_monitoring' in portfolio
        
        # Check position weights sum to 1
        total_weight = sum(p['weight'] for p in portfolio['positions'])
        assert abs(total_weight - 1.0) < 0.01
        
        # Check behavioral monitoring setup
        monitoring = portfolio['behavioral_monitoring']
        assert 'triggers' in monitoring
        assert 'performance_tracking' in monitoring
        assert 'behavioral_alerts' in monitoring
    
    def test_behavioral_biases_enum(self):
        """Test behavioral bias enumeration"""
        assert BehavioralBias.LOSS_AVERSION
        assert BehavioralBias.OVERCONFIDENCE
        assert BehavioralBias.HERDING
        assert BehavioralBias.RECENCY
        assert len(BehavioralBias) >= 10  # Should have comprehensive list
    
    def test_nudge_types_enum(self):
        """Test nudge type enumeration"""
        assert NudgeType.REFRAMING
        assert NudgeType.SOCIAL_PROOF
        assert NudgeType.DEFAULT_SETTING
        assert len(NudgeType) >= 10  # Should have various nudge types
    
    def test_goal_bucket_enum(self):
        """Test goal bucket enumeration"""
        assert GoalBucket.SAFETY
        assert GoalBucket.SECURITY
        assert GoalBucket.GROWTH
        assert GoalBucket.ASPIRATION
        assert GoalBucket.LEGACY
        assert len(GoalBucket) == 5  # Should have exactly 5 buckets
    
    def test_commitment_level_enum(self):
        """Test commitment level enumeration"""
        assert CommitmentLevel.SOFT
        assert CommitmentLevel.MODERATE
        assert CommitmentLevel.HARD
        assert len(CommitmentLevel) == 3  # Should have exactly 3 levels


class TestBehavioralUtilityFunctions:
    """Test behavioral utility and helper functions"""
    
    @pytest.fixture
    def analyzer(self):
        return BehavioralFinanceAnalyzer()
    
    def test_loss_aversion_calculation(self, analyzer):
        """Test loss aversion coefficient calculation"""
        transaction_history = [
            {'return_value': 1000},
            {'return_value': -500},
            {'return_value': 800},
            {'return_value': -600}
        ]
        
        coefficient = analyzer._calculate_loss_aversion(
            transaction_history,
            []
        )
        
        assert coefficient > 1.0  # Should show loss aversion
        assert coefficient <= 4.0  # Should be capped
    
    def test_risk_perception_assessment(self, analyzer):
        """Test risk perception assessment"""
        portfolio_history = [
            {'equity_allocation': 0.6},
            {'equity_allocation': 0.7},
            {'equity_allocation': 0.65}
        ]
        
        questionnaire = {'risk_tolerance': 0.7}
        
        risk_perception = analyzer._assess_risk_perception(
            portfolio_history,
            questionnaire
        )
        
        assert 0 <= risk_perception <= 1
        assert abs(risk_perception - 0.66) < 0.1  # Close to weighted average
    
    def test_time_preference_calculation(self, analyzer):
        """Test time preference calculation"""
        transaction_history = [
            {'holding_days': 30},
            {'holding_days': 60},
            {'holding_days': 45}
        ]
        
        time_pref = analyzer._calculate_time_preference(transaction_history)
        
        assert 0 <= time_pref <= 1
        assert time_pref == 0.7  # Medium holding period
    
    def test_decision_style_classification(self, analyzer):
        """Test decision style classification"""
        transaction_history = [
            {'decision_time_hours': 72, 'research_sources': 6},
            {'decision_time_hours': 96, 'research_sources': 8}
        ]
        
        style = analyzer._classify_decision_style(
            transaction_history,
            None
        )
        
        assert style == 'analytical'  # Long decision time, high research
    
    def test_financial_literacy_assessment(self, analyzer):
        """Test financial literacy assessment"""
        questionnaire = {
            'financial_literacy': {
                'compound_interest': 1.0,
                'inflation': 0.8,
                'diversification': 0.9,
                'risk_return': 0.7,
                'market_efficiency': 0.6
            }
        }
        
        literacy = analyzer._assess_financial_literacy(questionnaire)
        
        assert 0 <= literacy <= 1
        assert abs(literacy - 0.8) < 0.01  # Average of scores


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def analyzer(self):
        return BehavioralFinanceAnalyzer()
    
    @pytest.mark.asyncio
    async def test_complete_behavioral_analysis_workflow(self, analyzer):
        """Test complete behavioral analysis workflow"""
        # Step 1: Analyze profile
        transaction_history = [
            {
                'date': datetime.now().isoformat(),
                'type': 'buy',
                'ticker': 'AAPL',
                'return_percentage': 0.10,
                'holding_days': 180
            }
        ]
        
        portfolio_history = [
            {
                'date': datetime.now().isoformat(),
                'positions': [{'ticker': 'AAPL', 'weight': 0.5}],
                'equity_allocation': 0.8
            }
        ]
        
        profile = await analyzer.analyze_behavioral_profile(
            user_id="integration_test",
            transaction_history=transaction_history,
            portfolio_history=portfolio_history
        )
        
        # Step 2: Create nudges
        nudges = await analyzer.create_nudge_engine(
            user_id="integration_test",
            context={'portfolio_value': 50000}
        )
        
        # Step 3: Create goal buckets
        goals = [
            {'name': 'Emergency', 'target_amount': 10000, 'time_horizon_months': 6, 'priority': 1}
        ]
        
        buckets = await analyzer.create_goal_based_buckets(
            user_id="integration_test",
            goals=goals,
            total_portfolio_value=50000
        )
        
        # Step 4: Build behavioral portfolio
        portfolio = await analyzer.build_behavioral_portfolio(
            user_id="integration_test",
            capital=50000
        )
        
        # Verify complete workflow
        assert profile is not None
        assert len(nudges) >= 0
        assert len(buckets) > 0
        assert portfolio['capital'] == 50000
        assert len(portfolio['positions']) > 0


def run_tests():
    """Run all tests"""
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_tests()