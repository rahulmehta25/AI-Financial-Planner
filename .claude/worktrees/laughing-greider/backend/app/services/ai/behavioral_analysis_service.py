"""
Behavioral Analysis Service
Analyzes user patterns, risk tolerance, and predicts financial behaviors
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from collections import defaultdict

from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import tensorflow as tf
from tensorflow import keras
from scipy import stats
import redis

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RiskProfile(Enum):
    """Risk tolerance profiles"""
    CONSERVATIVE = "conservative"
    MODERATELY_CONSERVATIVE = "moderately_conservative"
    MODERATE = "moderate"
    MODERATELY_AGGRESSIVE = "moderately_aggressive"
    AGGRESSIVE = "aggressive"


class LifeStage(Enum):
    """Life stage categories"""
    STUDENT = "student"
    EARLY_CAREER = "early_career"
    MID_CAREER = "mid_career"
    PRE_RETIREMENT = "pre_retirement"
    RETIREMENT = "retirement"
    LEGACY_PLANNING = "legacy_planning"


class BehaviorPattern(Enum):
    """Identified behavioral patterns"""
    PANIC_SELLER = "panic_seller"
    BUY_HIGH_SELL_LOW = "buy_high_sell_low"
    CONSISTENT_SAVER = "consistent_saver"
    MOMENTUM_CHASER = "momentum_chaser"
    VALUE_INVESTOR = "value_investor"
    PASSIVE_INVESTOR = "passive_investor"
    ACTIVE_TRADER = "active_trader"
    GOAL_ORIENTED = "goal_oriented"
    IMPULSIVE = "impulsive"


@dataclass
class UserBehaviorProfile:
    """Complete behavioral profile of a user"""
    user_id: str
    risk_profile: RiskProfile
    risk_score: float  # 0-100
    life_stage: LifeStage
    behavioral_patterns: List[BehaviorPattern]
    investment_personality: str
    saving_consistency: float  # 0-1
    trading_frequency: str  # low/medium/high
    loss_aversion_score: float  # 0-1
    overconfidence_score: float  # 0-1
    herding_tendency: float  # 0-1
    recency_bias: float  # 0-1
    goal_commitment: float  # 0-1
    financial_literacy_score: float  # 0-100
    stress_response: str  # fight/flight/freeze
    decision_speed: str  # impulsive/deliberate/balanced
    preferred_communication: str
    engagement_level: str  # low/medium/high
    anomalies_detected: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TransactionBehavior:
    """Analysis of transaction patterns"""
    average_transaction_size: float
    transaction_frequency: float  # per month
    peak_activity_hours: List[int]
    preferred_asset_classes: List[str]
    buy_sell_ratio: float
    holding_period_avg: float  # days
    reaction_time_to_events: float  # hours
    diversification_tendency: float  # 0-1


@dataclass
class GoalBehavior:
    """Analysis of goal-related behavior"""
    goal_achievement_rate: float  # 0-1
    goal_modification_frequency: float  # per year
    average_goal_timeline: float  # years
    commitment_score: float  # 0-1
    realistic_goal_setting: float  # 0-1
    progress_tracking_frequency: str  # daily/weekly/monthly/rarely


class PredictedBehavior(BaseModel):
    """Predicted future behavior"""
    action: str = Field(..., description="Predicted action")
    probability: float = Field(..., ge=0, le=1, description="Probability of action")
    timeframe: str = Field(..., description="Expected timeframe")
    triggers: List[str] = Field(default_factory=list, description="Potential triggers")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")


class BehavioralAnalysisService:
    """
    Advanced behavioral analysis using ML and psychological models
    to understand and predict user financial behaviors
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis.from_url(
            config.get('redis_url', 'redis://localhost:6379')
        )
        self.models = self._initialize_models()
        self.scaler = StandardScaler()
        self.behavioral_rules = self._load_behavioral_rules()
        self.risk_questionnaire = self._load_risk_questionnaire()
        
    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize ML models for behavioral analysis"""
        models = {}
        
        # Risk profiling model
        models['risk_classifier'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Anomaly detection model
        models['anomaly_detector'] = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
        # Pattern clustering model
        models['pattern_clusterer'] = KMeans(
            n_clusters=8,
            random_state=42
        )
        
        # Neural network for behavior prediction
        models['behavior_predictor'] = self._build_behavior_prediction_model()
        
        return models
    
    def _build_behavior_prediction_model(self) -> keras.Model:
        """Build neural network for behavior prediction"""
        model = keras.Sequential([
            keras.layers.Dense(128, activation='relu', input_shape=(50,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(10, activation='softmax')  # 10 behavior classes
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _load_behavioral_rules(self) -> Dict[str, Any]:
        """Load behavioral finance rules and heuristics"""
        return {
            'panic_seller': {
                'indicators': [
                    'sells_during_drawdown > 0.7',
                    'reaction_time < 24_hours',
                    'loss_realization_rate > 0.8'
                ],
                'threshold': 2
            },
            'momentum_chaser': {
                'indicators': [
                    'buys_after_rally > 0.6',
                    'performance_chasing_score > 0.7',
                    'trend_following_ratio > 0.8'
                ],
                'threshold': 2
            },
            'value_investor': {
                'indicators': [
                    'buys_during_dip > 0.6',
                    'fundamental_focus > 0.7',
                    'holding_period > 365'
                ],
                'threshold': 2
            },
            'consistent_saver': {
                'indicators': [
                    'monthly_contribution_consistency > 0.9',
                    'auto_invest_enabled',
                    'emergency_fund_maintained'
                ],
                'threshold': 2
            }
        }
    
    def _load_risk_questionnaire(self) -> List[Dict[str, Any]]:
        """Load risk assessment questionnaire"""
        return [
            {
                'question': 'How would you react to a 20% portfolio decline?',
                'options': {
                    'sell_everything': -2,
                    'sell_some': -1,
                    'hold': 0,
                    'buy_more': 2
                }
            },
            {
                'question': 'What is your investment timeline?',
                'options': {
                    'less_than_1_year': -2,
                    '1_3_years': -1,
                    '3_7_years': 0,
                    '7_10_years': 1,
                    'more_than_10_years': 2
                }
            },
            {
                'question': 'What percentage of income can you invest?',
                'options': {
                    'less_than_5': -2,
                    '5_10': -1,
                    '10_20': 0,
                    '20_30': 1,
                    'more_than_30': 2
                }
            }
        ]
    
    async def analyze_user_behavior(
        self,
        user_id: str,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]],
        goal_history: List[Dict[str, Any]],
        demographic_data: Dict[str, Any]
    ) -> UserBehaviorProfile:
        """Comprehensive behavioral analysis of user"""
        
        # Analyze transaction patterns
        transaction_behavior = await self._analyze_transactions(transaction_history)
        
        # Analyze risk tolerance
        risk_profile, risk_score = await self._assess_risk_tolerance(
            transaction_history,
            portfolio_history,
            demographic_data
        )
        
        # Detect behavioral patterns
        patterns = await self._detect_behavioral_patterns(
            transaction_history,
            portfolio_history
        )
        
        # Analyze goal-related behavior
        goal_behavior = await self._analyze_goal_behavior(goal_history)
        
        # Detect anomalies
        anomalies = await self._detect_anomalies(
            transaction_history,
            portfolio_history
        )
        
        # Calculate psychological scores
        psych_scores = await self._calculate_psychological_scores(
            transaction_history,
            portfolio_history,
            transaction_behavior
        )
        
        # Determine life stage
        life_stage = self._determine_life_stage(demographic_data)
        
        # Generate personality profile
        personality = await self._generate_investment_personality(
            patterns,
            risk_profile,
            psych_scores
        )
        
        # Create recommendations
        recommendations = await self._generate_behavioral_recommendations(
            patterns,
            risk_profile,
            psych_scores,
            anomalies
        )
        
        profile = UserBehaviorProfile(
            user_id=user_id,
            risk_profile=risk_profile,
            risk_score=risk_score,
            life_stage=life_stage,
            behavioral_patterns=patterns,
            investment_personality=personality,
            saving_consistency=goal_behavior.commitment_score,
            trading_frequency=self._classify_trading_frequency(
                transaction_behavior.transaction_frequency
            ),
            loss_aversion_score=psych_scores['loss_aversion'],
            overconfidence_score=psych_scores['overconfidence'],
            herding_tendency=psych_scores['herding'],
            recency_bias=psych_scores['recency_bias'],
            goal_commitment=goal_behavior.commitment_score,
            financial_literacy_score=await self._assess_financial_literacy(
                transaction_history,
                demographic_data
            ),
            stress_response=psych_scores['stress_response'],
            decision_speed=psych_scores['decision_speed'],
            preferred_communication=await self._determine_communication_preference(
                demographic_data,
                patterns
            ),
            engagement_level=self._classify_engagement(transaction_behavior),
            anomalies_detected=anomalies,
            recommendations=recommendations
        )
        
        # Cache the profile
        await self._cache_profile(profile)
        
        return profile
    
    async def _analyze_transactions(
        self,
        transactions: List[Dict[str, Any]]
    ) -> TransactionBehavior:
        """Analyze transaction patterns"""
        
        if not transactions:
            return TransactionBehavior(
                average_transaction_size=0,
                transaction_frequency=0,
                peak_activity_hours=[],
                preferred_asset_classes=[],
                buy_sell_ratio=1,
                holding_period_avg=0,
                reaction_time_to_events=0,
                diversification_tendency=0
            )
        
        df = pd.DataFrame(transactions)
        
        # Calculate metrics
        avg_size = df['amount'].mean()
        
        # Transaction frequency (per month)
        date_range = (df['timestamp'].max() - df['timestamp'].min()).days
        frequency = len(transactions) / max(date_range / 30, 1)
        
        # Peak activity hours
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        peak_hours = df['hour'].value_counts().head(3).index.tolist()
        
        # Asset class preferences
        asset_classes = df['asset_class'].value_counts().head(5).index.tolist()
        
        # Buy/Sell ratio
        buys = len(df[df['type'] == 'buy'])
        sells = len(df[df['type'] == 'sell'])
        buy_sell_ratio = buys / max(sells, 1)
        
        # Average holding period
        holding_periods = []
        for asset in df['symbol'].unique():
            asset_df = df[df['symbol'] == asset].sort_values('timestamp')
            buys = asset_df[asset_df['type'] == 'buy']
            sells = asset_df[asset_df['type'] == 'sell']
            
            for _, sell in sells.iterrows():
                prior_buys = buys[buys['timestamp'] < sell['timestamp']]
                if not prior_buys.empty:
                    holding_period = (sell['timestamp'] - prior_buys.iloc[-1]['timestamp']).days
                    holding_periods.append(holding_period)
        
        avg_holding = np.mean(holding_periods) if holding_periods else 365
        
        # Diversification tendency
        unique_assets = df['symbol'].nunique()
        total_transactions = len(df)
        diversification = min(unique_assets / max(total_transactions * 0.1, 1), 1)
        
        return TransactionBehavior(
            average_transaction_size=avg_size,
            transaction_frequency=frequency,
            peak_activity_hours=peak_hours,
            preferred_asset_classes=asset_classes,
            buy_sell_ratio=buy_sell_ratio,
            holding_period_avg=avg_holding,
            reaction_time_to_events=24,  # Placeholder
            diversification_tendency=diversification
        )
    
    async def _assess_risk_tolerance(
        self,
        transactions: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]],
        demographic_data: Dict[str, Any]
    ) -> Tuple[RiskProfile, float]:
        """Assess user's risk tolerance"""
        
        risk_score = 50  # Base score
        
        # Age factor
        age = demographic_data.get('age', 35)
        if age < 30:
            risk_score += 15
        elif age < 40:
            risk_score += 10
        elif age < 50:
            risk_score += 5
        elif age < 60:
            risk_score -= 5
        else:
            risk_score -= 15
        
        # Income stability factor
        income_stability = demographic_data.get('income_stability', 'stable')
        if income_stability == 'very_stable':
            risk_score += 10
        elif income_stability == 'unstable':
            risk_score -= 10
        
        # Analyze transaction behavior during market downturns
        if transactions:
            df = pd.DataFrame(transactions)
            
            # Check selling behavior during losses
            loss_transactions = df[df['realized_pnl'] < 0]
            if len(loss_transactions) > 0:
                panic_selling_ratio = len(loss_transactions) / len(df)
                if panic_selling_ratio > 0.3:
                    risk_score -= 20
                elif panic_selling_ratio < 0.1:
                    risk_score += 10
        
        # Portfolio volatility preference
        if portfolio_history:
            volatilities = [p.get('volatility', 0.15) for p in portfolio_history]
            avg_volatility = np.mean(volatilities)
            if avg_volatility > 0.25:
                risk_score += 15
            elif avg_volatility < 0.10:
                risk_score -= 15
        
        # Normalize score
        risk_score = max(0, min(100, risk_score))
        
        # Determine profile
        if risk_score < 20:
            profile = RiskProfile.CONSERVATIVE
        elif risk_score < 40:
            profile = RiskProfile.MODERATELY_CONSERVATIVE
        elif risk_score < 60:
            profile = RiskProfile.MODERATE
        elif risk_score < 80:
            profile = RiskProfile.MODERATELY_AGGRESSIVE
        else:
            profile = RiskProfile.AGGRESSIVE
        
        return profile, risk_score
    
    async def _detect_behavioral_patterns(
        self,
        transactions: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> List[BehaviorPattern]:
        """Detect behavioral patterns using ML and rules"""
        
        patterns = []
        
        if not transactions:
            return patterns
        
        df = pd.DataFrame(transactions)
        
        # Check for panic selling
        market_drops = df[df['market_condition'] == 'bear']
        if len(market_drops) > 0:
            sells_in_drops = market_drops[market_drops['type'] == 'sell']
            if len(sells_in_drops) / len(market_drops) > 0.7:
                patterns.append(BehaviorPattern.PANIC_SELLER)
        
        # Check for momentum chasing
        market_rallies = df[df['market_condition'] == 'bull']
        if len(market_rallies) > 0:
            buys_in_rallies = market_rallies[market_rallies['type'] == 'buy']
            if len(buys_in_rallies) / len(market_rallies) > 0.7:
                patterns.append(BehaviorPattern.MOMENTUM_CHASER)
        
        # Check for consistent saving
        monthly_contributions = df[df['type'] == 'deposit'].groupby(
            pd.to_datetime(df['timestamp']).dt.to_period('M')
        ).size()
        
        if len(monthly_contributions) > 6:
            consistency = monthly_contributions.std() / monthly_contributions.mean()
            if consistency < 0.2:
                patterns.append(BehaviorPattern.CONSISTENT_SAVER)
        
        # Check trading frequency
        date_range = (df['timestamp'].max() - df['timestamp'].min()).days
        trades_per_month = len(df[df['type'].isin(['buy', 'sell'])]) / max(date_range / 30, 1)
        
        if trades_per_month > 20:
            patterns.append(BehaviorPattern.ACTIVE_TRADER)
        elif trades_per_month < 2:
            patterns.append(BehaviorPattern.PASSIVE_INVESTOR)
        
        # Check for value investing
        if 'price_to_avg' in df.columns:
            buys_below_avg = df[(df['type'] == 'buy') & (df['price_to_avg'] < 0.95)]
            if len(buys_below_avg) / max(len(df[df['type'] == 'buy']), 1) > 0.6:
                patterns.append(BehaviorPattern.VALUE_INVESTOR)
        
        return patterns
    
    async def _detect_anomalies(
        self,
        transactions: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalous behavior using ML"""
        
        anomalies = []
        
        if len(transactions) < 10:
            return anomalies
        
        # Prepare features
        features = []
        for t in transactions:
            features.append([
                t.get('amount', 0),
                t.get('hour_of_day', 12),
                t.get('day_of_week', 3),
                1 if t.get('type') == 'buy' else 0,
                t.get('volatility_at_time', 0.15)
            ])
        
        X = np.array(features)
        
        # Detect anomalies
        if X.shape[0] > 0:
            predictions = self.models['anomaly_detector'].fit_predict(X)
            
            for i, pred in enumerate(predictions):
                if pred == -1:  # Anomaly
                    anomalies.append({
                        'type': 'transaction_anomaly',
                        'transaction_id': transactions[i].get('id'),
                        'description': f"Unusual transaction detected",
                        'severity': 'medium',
                        'timestamp': transactions[i].get('timestamp')
                    })
        
        # Check for sudden behavior changes
        if len(portfolio_history) > 30:
            recent = portfolio_history[-10:]
            historical = portfolio_history[-30:-10]
            
            recent_risk = np.mean([p.get('risk_score', 50) for p in recent])
            historical_risk = np.mean([p.get('risk_score', 50) for p in historical])
            
            if abs(recent_risk - historical_risk) > 20:
                anomalies.append({
                    'type': 'risk_shift',
                    'description': f"Significant risk profile change detected",
                    'severity': 'high',
                    'change': recent_risk - historical_risk
                })
        
        return anomalies
    
    async def _calculate_psychological_scores(
        self,
        transactions: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]],
        transaction_behavior: TransactionBehavior
    ) -> Dict[str, float]:
        """Calculate psychological trait scores"""
        
        scores = {
            'loss_aversion': 0.5,
            'overconfidence': 0.5,
            'herding': 0.5,
            'recency_bias': 0.5,
            'stress_response': 'balanced',
            'decision_speed': 'balanced'
        }
        
        if not transactions:
            return scores
        
        df = pd.DataFrame(transactions)
        
        # Loss aversion
        if 'realized_pnl' in df.columns:
            losses = df[df['realized_pnl'] < 0]
            gains = df[df['realized_pnl'] > 0]
            
            if len(losses) > 0 and len(gains) > 0:
                avg_loss = abs(losses['realized_pnl'].mean())
                avg_gain = gains['realized_pnl'].mean()
                
                # Higher ratio means more loss averse
                scores['loss_aversion'] = min(avg_loss / max(avg_gain, 1), 1.0)
        
        # Overconfidence (frequent trading after wins)
        if transaction_behavior.transaction_frequency > 10:
            scores['overconfidence'] = min(
                transaction_behavior.transaction_frequency / 20,
                1.0
            )
        
        # Herding tendency (buying popular assets)
        if 'popularity_rank' in df.columns:
            popular_buys = df[(df['type'] == 'buy') & (df['popularity_rank'] < 10)]
            scores['herding'] = len(popular_buys) / max(len(df[df['type'] == 'buy']), 1)
        
        # Recency bias
        if len(df) > 20:
            recent_weight = df.tail(10)['amount'].sum()
            total_weight = df['amount'].sum()
            scores['recency_bias'] = recent_weight / max(total_weight, 1)
        
        # Stress response
        if transaction_behavior.reaction_time_to_events < 6:
            scores['stress_response'] = 'flight'
        elif transaction_behavior.reaction_time_to_events > 48:
            scores['stress_response'] = 'freeze'
        else:
            scores['stress_response'] = 'fight'
        
        # Decision speed
        if transaction_behavior.transaction_frequency > 15:
            scores['decision_speed'] = 'impulsive'
        elif transaction_behavior.transaction_frequency < 2:
            scores['decision_speed'] = 'deliberate'
        else:
            scores['decision_speed'] = 'balanced'
        
        return scores
    
    async def _analyze_goal_behavior(
        self,
        goal_history: List[Dict[str, Any]]
    ) -> GoalBehavior:
        """Analyze goal-related behavior"""
        
        if not goal_history:
            return GoalBehavior(
                goal_achievement_rate=0,
                goal_modification_frequency=0,
                average_goal_timeline=10,
                commitment_score=0,
                realistic_goal_setting=0.5,
                progress_tracking_frequency='rarely'
            )
        
        achieved = len([g for g in goal_history if g.get('status') == 'achieved'])
        total = len(goal_history)
        achievement_rate = achieved / max(total, 1)
        
        # Goal modifications
        modifications = sum(g.get('modification_count', 0) for g in goal_history)
        years = len(set(g.get('year') for g in goal_history))
        modification_freq = modifications / max(years, 1)
        
        # Average timeline
        timelines = [g.get('timeline_years', 10) for g in goal_history]
        avg_timeline = np.mean(timelines)
        
        # Commitment score
        active_goals = [g for g in goal_history if g.get('status') == 'active']
        if active_goals:
            progress_rates = [g.get('progress_rate', 0) for g in active_goals]
            commitment = np.mean(progress_rates)
        else:
            commitment = achievement_rate
        
        # Realistic goal setting
        overambitious = len([g for g in goal_history if g.get('adjusted_down', False)])
        realistic = 1 - (overambitious / max(total, 1))
        
        # Progress tracking
        tracking_frequencies = [g.get('check_frequency', 'monthly') for g in goal_history]
        most_common = max(set(tracking_frequencies), key=tracking_frequencies.count)
        
        return GoalBehavior(
            goal_achievement_rate=achievement_rate,
            goal_modification_frequency=modification_freq,
            average_goal_timeline=avg_timeline,
            commitment_score=commitment,
            realistic_goal_setting=realistic,
            progress_tracking_frequency=most_common
        )
    
    def _determine_life_stage(self, demographic_data: Dict[str, Any]) -> LifeStage:
        """Determine user's life stage"""
        
        age = demographic_data.get('age', 35)
        employment = demographic_data.get('employment_status', 'employed')
        
        if age < 25 or employment == 'student':
            return LifeStage.STUDENT
        elif age < 35:
            return LifeStage.EARLY_CAREER
        elif age < 50:
            return LifeStage.MID_CAREER
        elif age < 60:
            return LifeStage.PRE_RETIREMENT
        elif age < 75:
            return LifeStage.RETIREMENT
        else:
            return LifeStage.LEGACY_PLANNING
    
    async def _generate_investment_personality(
        self,
        patterns: List[BehaviorPattern],
        risk_profile: RiskProfile,
        psych_scores: Dict[str, Any]
    ) -> str:
        """Generate investment personality description"""
        
        personality_traits = []
        
        # Risk-based traits
        if risk_profile in [RiskProfile.CONSERVATIVE, RiskProfile.MODERATELY_CONSERVATIVE]:
            personality_traits.append("Security-focused")
        elif risk_profile in [RiskProfile.AGGRESSIVE, RiskProfile.MODERATELY_AGGRESSIVE]:
            personality_traits.append("Growth-oriented")
        else:
            personality_traits.append("Balanced")
        
        # Pattern-based traits
        if BehaviorPattern.CONSISTENT_SAVER in patterns:
            personality_traits.append("Disciplined saver")
        if BehaviorPattern.ACTIVE_TRADER in patterns:
            personality_traits.append("Active participant")
        if BehaviorPattern.VALUE_INVESTOR in patterns:
            personality_traits.append("Value seeker")
        if BehaviorPattern.PASSIVE_INVESTOR in patterns:
            personality_traits.append("Set-and-forget investor")
        
        # Psychology-based traits
        if psych_scores['loss_aversion'] > 0.7:
            personality_traits.append("Risk-averse")
        if psych_scores['overconfidence'] > 0.7:
            personality_traits.append("Confident decision-maker")
        
        return ", ".join(personality_traits) if personality_traits else "Developing investor"
    
    async def _assess_financial_literacy(
        self,
        transactions: List[Dict[str, Any]],
        demographic_data: Dict[str, Any]
    ) -> float:
        """Assess financial literacy level"""
        
        score = 50  # Base score
        
        # Education factor
        education = demographic_data.get('education_level', 'bachelor')
        education_scores = {
            'high_school': -10,
            'bachelor': 0,
            'master': 10,
            'phd': 15,
            'mba': 20
        }
        score += education_scores.get(education, 0)
        
        # Experience factor
        years_investing = demographic_data.get('years_investing', 1)
        score += min(years_investing * 2, 20)
        
        # Diversity of investments
        if transactions:
            asset_types = set(t.get('asset_class') for t in transactions)
            score += min(len(asset_types) * 5, 20)
        
        # Professional certifications
        if demographic_data.get('has_financial_certification', False):
            score += 20
        
        return min(max(score, 0), 100)
    
    def _classify_trading_frequency(self, frequency: float) -> str:
        """Classify trading frequency"""
        if frequency < 2:
            return "low"
        elif frequency < 10:
            return "medium"
        else:
            return "high"
    
    def _classify_engagement(self, behavior: TransactionBehavior) -> str:
        """Classify user engagement level"""
        if behavior.transaction_frequency < 1:
            return "low"
        elif behavior.transaction_frequency < 5:
            return "medium"
        else:
            return "high"
    
    async def _determine_communication_preference(
        self,
        demographic_data: Dict[str, Any],
        patterns: List[BehaviorPattern]
    ) -> str:
        """Determine preferred communication style"""
        
        age = demographic_data.get('age', 35)
        
        if age < 35:
            base_pref = "digital-first, visual"
        elif age < 50:
            base_pref = "balanced, detailed"
        else:
            base_pref = "traditional, comprehensive"
        
        if BehaviorPattern.ACTIVE_TRADER in patterns:
            return f"{base_pref}, real-time updates"
        elif BehaviorPattern.PASSIVE_INVESTOR in patterns:
            return f"{base_pref}, periodic summaries"
        else:
            return f"{base_pref}, regular check-ins"
    
    async def _generate_behavioral_recommendations(
        self,
        patterns: List[BehaviorPattern],
        risk_profile: RiskProfile,
        psych_scores: Dict[str, float],
        anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate personalized behavioral recommendations"""
        
        recommendations = []
        
        # Pattern-based recommendations
        if BehaviorPattern.PANIC_SELLER in patterns:
            recommendations.append(
                "Consider setting stop-loss orders to manage emotions during market downturns"
            )
            recommendations.append(
                "Review your investment timeline - short-term volatility matters less for long-term goals"
            )
        
        if BehaviorPattern.MOMENTUM_CHASER in patterns:
            recommendations.append(
                "Implement a systematic investment approach to avoid chasing performance"
            )
            recommendations.append(
                "Consider dollar-cost averaging to reduce timing risk"
            )
        
        if BehaviorPattern.IMPULSIVE in patterns:
            recommendations.append(
                "Implement a 24-hour rule before making investment decisions"
            )
        
        # Psychology-based recommendations
        if psych_scores['loss_aversion'] > 0.7:
            recommendations.append(
                "Focus on total portfolio performance rather than individual positions"
            )
            recommendations.append(
                "Consider reframing losses as learning opportunities"
            )
        
        if psych_scores['overconfidence'] > 0.7:
            recommendations.append(
                "Maintain an investment journal to track decision accuracy"
            )
            recommendations.append(
                "Consider seeking second opinions on major investment decisions"
            )
        
        if psych_scores['herding'] > 0.7:
            recommendations.append(
                "Develop and stick to a personalized investment strategy"
            )
            recommendations.append(
                "Focus on fundamental analysis rather than market sentiment"
            )
        
        # Anomaly-based recommendations
        for anomaly in anomalies:
            if anomaly['type'] == 'risk_shift':
                recommendations.append(
                    "Recent behavior shows significant risk change - review and confirm your risk tolerance"
                )
            elif anomaly['type'] == 'transaction_anomaly':
                recommendations.append(
                    "Unusual trading pattern detected - ensure transactions align with your strategy"
                )
        
        return recommendations
    
    async def _cache_profile(self, profile: UserBehaviorProfile):
        """Cache user profile in Redis"""
        key = f"behavior_profile:{profile.user_id}"
        self.redis_client.setex(
            key,
            86400 * 7,  # 7 days
            json.dumps({
                'user_id': profile.user_id,
                'risk_profile': profile.risk_profile.value,
                'risk_score': profile.risk_score,
                'life_stage': profile.life_stage.value,
                'patterns': [p.value for p in profile.behavioral_patterns],
                'personality': profile.investment_personality,
                'recommendations': profile.recommendations,
                'last_updated': profile.last_updated.isoformat()
            })
        )
    
    async def predict_user_behavior(
        self,
        user_profile: UserBehaviorProfile,
        market_scenario: Dict[str, Any]
    ) -> List[PredictedBehavior]:
        """Predict user behavior in given market scenario"""
        
        predictions = []
        
        # Prepare features for ML model
        features = np.array([
            user_profile.risk_score / 100,
            user_profile.loss_aversion_score,
            user_profile.overconfidence_score,
            user_profile.herding_tendency,
            user_profile.recency_bias,
            user_profile.goal_commitment,
            market_scenario.get('volatility', 0.15),
            market_scenario.get('market_return', 0),
            market_scenario.get('interest_rate', 0.05),
            1 if market_scenario.get('regime') == 'bull' else 0
        ]).reshape(1, -1)
        
        # Pad features to match model input
        features_padded = np.pad(features, ((0, 0), (0, 40)), mode='constant')
        
        # Get predictions from neural network
        probabilities = self.models['behavior_predictor'].predict(features_padded)[0]
        
        # Map to behavior predictions
        behaviors = [
            ('increase_allocation', 'Likely to increase investment allocation'),
            ('decrease_allocation', 'Likely to reduce investment allocation'),
            ('rebalance_portfolio', 'Likely to rebalance portfolio'),
            ('take_profits', 'Likely to take profits'),
            ('cut_losses', 'Likely to cut losses'),
            ('hold_steady', 'Likely to maintain current strategy'),
            ('seek_advice', 'Likely to seek professional advice'),
            ('panic_sell', 'Risk of panic selling'),
            ('chase_performance', 'Risk of performance chasing'),
            ('do_nothing', 'Likely to take no action')
        ]
        
        for i, (action, description) in enumerate(behaviors):
            if probabilities[i] > 0.3:  # Threshold for inclusion
                
                # Determine triggers
                triggers = []
                if action in ['panic_sell', 'cut_losses']:
                    triggers.append(f"Market decline > {user_profile.risk_score / 5}%")
                elif action in ['chase_performance', 'increase_allocation']:
                    triggers.append(f"Market rally > {(100 - user_profile.risk_score) / 5}%")
                
                predictions.append(PredictedBehavior(
                    action=description,
                    probability=float(probabilities[i]),
                    timeframe="Next 30 days",
                    triggers=triggers,
                    confidence=0.7 + (0.3 * min(probabilities[i], 0.5))
                ))
        
        # Sort by probability
        predictions.sort(key=lambda x: x.probability, reverse=True)
        
        return predictions[:5]  # Return top 5 predictions
    
    async def get_behavioral_insights(
        self,
        user_profile: UserBehaviorProfile
    ) -> Dict[str, Any]:
        """Generate actionable behavioral insights"""
        
        insights = {
            'strengths': [],
            'weaknesses': [],
            'opportunities': [],
            'coaching_points': []
        }
        
        # Identify strengths
        if user_profile.saving_consistency > 0.8:
            insights['strengths'].append("Excellent saving discipline")
        if user_profile.goal_commitment > 0.7:
            insights['strengths'].append("Strong goal commitment")
        if BehaviorPattern.VALUE_INVESTOR in user_profile.behavioral_patterns:
            insights['strengths'].append("Value-oriented investment approach")
        
        # Identify weaknesses
        if user_profile.loss_aversion_score > 0.8:
            insights['weaknesses'].append("High loss aversion may limit growth")
        if BehaviorPattern.PANIC_SELLER in user_profile.behavioral_patterns:
            insights['weaknesses'].append("Tendency to sell during market stress")
        if user_profile.overconfidence_score > 0.8:
            insights['weaknesses'].append("Overconfidence may lead to excessive risk")
        
        # Identify opportunities
        if user_profile.financial_literacy_score < 50:
            insights['opportunities'].append("Improving financial literacy could enhance decision-making")
        if user_profile.trading_frequency == "high":
            insights['opportunities'].append("Reducing trading frequency could lower costs")
        
        # Coaching points
        insights['coaching_points'] = [
            f"Your {user_profile.investment_personality} style aligns with {user_profile.risk_profile.value} risk profile",
            f"Consider reviewing your portfolio every {self._suggest_review_frequency(user_profile)}",
            f"Your life stage ({user_profile.life_stage.value}) suggests focusing on {self._suggest_life_stage_focus(user_profile.life_stage)}"
        ]
        
        return insights
    
    def _suggest_review_frequency(self, profile: UserBehaviorProfile) -> str:
        """Suggest portfolio review frequency"""
        if profile.trading_frequency == "high":
            return "week"
        elif profile.engagement_level == "medium":
            return "month"
        else:
            return "quarter"
    
    def _suggest_life_stage_focus(self, life_stage: LifeStage) -> str:
        """Suggest focus based on life stage"""
        focus_map = {
            LifeStage.STUDENT: "building emergency fund and starting investments",
            LifeStage.EARLY_CAREER: "aggressive growth and retirement savings",
            LifeStage.MID_CAREER: "balanced growth and risk management",
            LifeStage.PRE_RETIREMENT: "capital preservation and income generation",
            LifeStage.RETIREMENT: "income stability and wealth preservation",
            LifeStage.LEGACY_PLANNING: "wealth transfer and tax optimization"
        }
        return focus_map.get(life_stage, "long-term wealth building")