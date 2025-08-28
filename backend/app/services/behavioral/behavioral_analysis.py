"""
Behavioral Finance Analysis System

This module implements sophisticated behavioral finance analysis including:
- Behavioral bias detection and measurement
- Nudge engine for behavioral improvements
- Mental accounting optimization
- Goal-based portfolio bucketing
- Commitment devices and behavioral guardrails
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import asyncio
from collections import defaultdict
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BehavioralBias(Enum):
    """Types of behavioral biases in financial decision-making"""
    LOSS_AVERSION = "loss_aversion"
    OVERCONFIDENCE = "overconfidence"
    HERDING = "herding"
    RECENCY = "recency"
    ANCHORING = "anchoring"
    CONFIRMATION = "confirmation"
    MENTAL_ACCOUNTING = "mental_accounting"
    ENDOWMENT = "endowment"
    DISPOSITION = "disposition"
    HOME_BIAS = "home_bias"
    FRAMING = "framing"
    AVAILABILITY = "availability"
    REGRET_AVERSION = "regret_aversion"
    STATUS_QUO = "status_quo"


class NudgeType(Enum):
    """Types of behavioral nudges"""
    REFRAMING = "reframing"
    SOCIAL_PROOF = "social_proof"
    DEFAULT_SETTING = "default_setting"
    SIMPLIFICATION = "simplification"
    COMMITMENT = "commitment"
    REMINDER = "reminder"
    FEEDBACK = "feedback"
    GAMIFICATION = "gamification"
    LOSS_FRAMING = "loss_framing"
    GAIN_FRAMING = "gain_framing"
    ANCHORING_ADJUSTMENT = "anchoring_adjustment"
    MENTAL_ACCOUNTING = "mental_accounting"


class GoalBucket(Enum):
    """Goal-based bucket categories"""
    SAFETY = "safety"
    SECURITY = "security"
    GROWTH = "growth"
    ASPIRATION = "aspiration"
    LEGACY = "legacy"


class CommitmentLevel(Enum):
    """Levels of commitment devices"""
    SOFT = "soft"  # Reminders and suggestions
    MODERATE = "moderate"  # Defaults and friction
    HARD = "hard"  # Locks and restrictions


@dataclass
class BiasDetection:
    """Detection result for a behavioral bias"""
    bias_type: BehavioralBias
    severity: float  # 0-1 scale
    confidence: float  # 0-1 scale
    evidence: List[str]
    impact_on_returns: float  # Estimated annual return impact
    recommended_nudges: List['Nudge']


@dataclass
class Nudge:
    """Behavioral nudge recommendation"""
    nudge_type: NudgeType
    message: str
    action: str
    expected_effectiveness: float  # 0-1 scale
    implementation_difficulty: str  # easy, moderate, hard
    personalization_factors: Dict[str, Any]
    timing: Optional[str] = None
    frequency: Optional[str] = None


@dataclass
class MentalAccount:
    """Mental accounting bucket"""
    name: str
    purpose: str
    current_value: float
    target_value: float
    time_horizon: int  # months
    risk_tolerance: str
    assets: List[str]
    allocation_percentage: float
    behavioral_constraints: List[str]


@dataclass
class GoalBasedBucket:
    """Goal-based investment bucket"""
    bucket_type: GoalBucket
    goal_description: str
    priority: int  # 1-5, 1 being highest
    current_allocation: float
    target_allocation: float
    time_horizon: int  # months
    required_return: float
    risk_budget: float
    assets: List[Dict[str, float]]
    behavioral_guardrails: List[str]


@dataclass
class CommitmentDevice:
    """Commitment device for behavioral control"""
    device_id: str
    level: CommitmentLevel
    description: str
    trigger_conditions: List[str]
    actions: List[str]
    override_requirements: Optional[Dict[str, Any]]
    effectiveness_score: float
    user_acceptance: float


@dataclass
class BehavioralProfile:
    """Complete behavioral profile of an investor"""
    user_id: str
    detected_biases: List[BiasDetection]
    risk_perception: float  # Behavioral risk tolerance
    loss_aversion_coefficient: float
    time_preference: float  # Discount rate for future rewards
    social_influence_sensitivity: float
    cognitive_load_capacity: float
    decision_style: str  # analytical, intuitive, dependent, spontaneous
    financial_literacy_score: float
    stress_response_pattern: str
    preferred_nudge_types: List[NudgeType]


class BehavioralFinanceAnalyzer:
    """
    Advanced behavioral finance analysis system with bias detection,
    nudge engine, and behavior-optimized portfolio construction
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the behavioral finance analyzer
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.bias_detection_models = self._initialize_bias_models()
        self.nudge_library = self._load_nudge_library()
        self.behavioral_profiles = {}
        self.commitment_devices = {}
        self.historical_behaviors = defaultdict(list)
        
        # Behavioral parameters
        self.loss_aversion_baseline = 2.25  # Kahneman-Tversky estimate
        self.hyperbolic_discount_rate = 0.95
        self.social_proof_weight = 0.3
        self.framing_effect_size = 0.15
        
        logger.info("BehavioralFinanceAnalyzer initialized successfully")
    
    def _initialize_bias_models(self) -> Dict[BehavioralBias, Any]:
        """Initialize bias detection models"""
        return {
            BehavioralBias.LOSS_AVERSION: self._detect_loss_aversion,
            BehavioralBias.OVERCONFIDENCE: self._detect_overconfidence,
            BehavioralBias.HERDING: self._detect_herding,
            BehavioralBias.RECENCY: self._detect_recency,
            BehavioralBias.ANCHORING: self._detect_anchoring,
            BehavioralBias.DISPOSITION: self._detect_disposition,
            BehavioralBias.HOME_BIAS: self._detect_home_bias,
            BehavioralBias.MENTAL_ACCOUNTING: self._detect_mental_accounting,
        }
    
    def _load_nudge_library(self) -> Dict[BehavioralBias, List[Nudge]]:
        """Load library of nudges for each bias"""
        library = {
            BehavioralBias.LOSS_AVERSION: [
                Nudge(
                    nudge_type=NudgeType.REFRAMING,
                    message="Focus on long-term gains rather than short-term losses",
                    action="reframe_portfolio_view",
                    expected_effectiveness=0.7,
                    implementation_difficulty="easy",
                    personalization_factors={"time_horizon": "long"}
                ),
                Nudge(
                    nudge_type=NudgeType.GAIN_FRAMING,
                    message="Your diversified portfolio has protected ${amount} in value",
                    action="highlight_downside_protection",
                    expected_effectiveness=0.65,
                    implementation_difficulty="easy",
                    personalization_factors={"loss_sensitivity": "high"}
                ),
            ],
            BehavioralBias.OVERCONFIDENCE: [
                Nudge(
                    nudge_type=NudgeType.FEEDBACK,
                    message="Your past predictions had {accuracy}% accuracy. Consider diversifying.",
                    action="show_prediction_history",
                    expected_effectiveness=0.8,
                    implementation_difficulty="moderate",
                    personalization_factors={"prediction_tracking": True}
                ),
                Nudge(
                    nudge_type=NudgeType.SOCIAL_PROOF,
                    message="90% of successful investors maintain diversified portfolios",
                    action="show_peer_comparison",
                    expected_effectiveness=0.6,
                    implementation_difficulty="easy",
                    personalization_factors={"peer_sensitive": True}
                ),
            ],
            BehavioralBias.HERDING: [
                Nudge(
                    nudge_type=NudgeType.REMINDER,
                    message="Remember your personal investment goals, not market trends",
                    action="highlight_personal_goals",
                    expected_effectiveness=0.7,
                    implementation_difficulty="easy",
                    personalization_factors={"goal_oriented": True}
                ),
            ],
            BehavioralBias.RECENCY: [
                Nudge(
                    nudge_type=NudgeType.ANCHORING_ADJUSTMENT,
                    message="Historical 10-year returns: {returns}%. Recent performance is temporary.",
                    action="show_long_term_perspective",
                    expected_effectiveness=0.75,
                    implementation_difficulty="easy",
                    personalization_factors={"time_perspective": "long"}
                ),
            ],
        }
        return library
    
    async def analyze_behavioral_profile(
        self,
        user_id: str,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]],
        questionnaire_responses: Optional[Dict[str, Any]] = None
    ) -> BehavioralProfile:
        """
        Comprehensive behavioral profile analysis
        
        Args:
            user_id: User identifier
            transaction_history: Historical transactions
            portfolio_history: Portfolio changes over time
            questionnaire_responses: Optional behavioral questionnaire
            
        Returns:
            Complete behavioral profile
        """
        try:
            # Detect various biases
            biases = await self._detect_all_biases(
                transaction_history,
                portfolio_history
            )
            
            # Calculate behavioral metrics
            loss_aversion = self._calculate_loss_aversion(
                transaction_history,
                portfolio_history
            )
            
            risk_perception = self._assess_risk_perception(
                portfolio_history,
                questionnaire_responses
            )
            
            time_preference = self._calculate_time_preference(
                transaction_history
            )
            
            social_influence = self._assess_social_influence(
                transaction_history,
                questionnaire_responses
            )
            
            # Determine decision style
            decision_style = self._classify_decision_style(
                transaction_history,
                questionnaire_responses
            )
            
            # Create profile
            profile = BehavioralProfile(
                user_id=user_id,
                detected_biases=biases,
                risk_perception=risk_perception,
                loss_aversion_coefficient=loss_aversion,
                time_preference=time_preference,
                social_influence_sensitivity=social_influence,
                cognitive_load_capacity=0.7,  # Default, can be assessed
                decision_style=decision_style,
                financial_literacy_score=self._assess_financial_literacy(
                    questionnaire_responses
                ),
                stress_response_pattern=self._identify_stress_pattern(
                    transaction_history
                ),
                preferred_nudge_types=self._identify_effective_nudges(biases)
            )
            
            # Store profile
            self.behavioral_profiles[user_id] = profile
            
            logger.info(f"Behavioral profile analyzed for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing behavioral profile: {str(e)}")
            raise
    
    async def _detect_all_biases(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> List[BiasDetection]:
        """Detect all behavioral biases"""
        biases = []
        
        for bias_type, detection_func in self.bias_detection_models.items():
            try:
                detection = await detection_func(
                    transaction_history,
                    portfolio_history
                )
                if detection and detection.severity > 0.3:  # Threshold
                    biases.append(detection)
            except Exception as e:
                logger.warning(f"Error detecting {bias_type}: {str(e)}")
        
        return sorted(biases, key=lambda x: x.severity, reverse=True)
    
    async def _detect_loss_aversion(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect loss aversion bias"""
        evidence = []
        
        # Analyze selling patterns
        gains_held = []
        losses_sold = []
        
        for tx in transaction_history:
            if tx.get('type') == 'sell':
                return_pct = tx.get('return_percentage', 0)
                holding_period = tx.get('holding_days', 0)
                
                if return_pct > 0:
                    gains_held.append(holding_period)
                else:
                    losses_sold.append(holding_period)
        
        # Calculate disposition effect
        if gains_held and losses_sold:
            avg_gain_hold = np.mean(gains_held)
            avg_loss_hold = np.mean(losses_sold)
            
            if avg_loss_hold < avg_gain_hold:
                evidence.append("Tendency to sell losers quickly and hold winners")
                severity = min((avg_gain_hold / avg_loss_hold - 1) * 0.5, 1.0)
            else:
                severity = 0.0
        else:
            severity = 0.0
        
        # Analyze portfolio volatility reaction
        volatility_reactions = self._analyze_volatility_response(portfolio_history)
        if volatility_reactions > 0.5:
            evidence.append("Overreaction to portfolio volatility")
            severity = max(severity, volatility_reactions)
        
        # Generate nudges
        nudges = self.nudge_library.get(BehavioralBias.LOSS_AVERSION, [])
        
        return BiasDetection(
            bias_type=BehavioralBias.LOSS_AVERSION,
            severity=severity,
            confidence=0.7 if evidence else 0.3,
            evidence=evidence,
            impact_on_returns=-0.02 * severity,  # -2% per unit severity
            recommended_nudges=nudges[:2]  # Top 2 nudges
        )
    
    async def _detect_overconfidence(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect overconfidence bias"""
        evidence = []
        
        # Analyze trading frequency
        trading_freq = len(transaction_history) / max(
            1,
            (datetime.now() - datetime.fromisoformat(
                transaction_history[0]['date']
            )).days / 30
        )
        
        if trading_freq > 10:  # More than 10 trades per month
            evidence.append(f"High trading frequency: {trading_freq:.1f}/month")
            severity = min(trading_freq / 20, 1.0)
        else:
            severity = 0.0
        
        # Analyze concentration
        if portfolio_history:
            latest_portfolio = portfolio_history[-1]
            positions = latest_portfolio.get('positions', [])
            if positions:
                concentration = max([p['weight'] for p in positions])
                if concentration > 0.3:  # More than 30% in single position
                    evidence.append(f"High concentration: {concentration:.1%}")
                    severity = max(severity, (concentration - 0.3) * 2)
        
        # Generate nudges
        nudges = self.nudge_library.get(BehavioralBias.OVERCONFIDENCE, [])
        
        return BiasDetection(
            bias_type=BehavioralBias.OVERCONFIDENCE,
            severity=severity,
            confidence=0.8 if evidence else 0.2,
            evidence=evidence,
            impact_on_returns=-0.035 * severity,  # -3.5% per unit severity
            recommended_nudges=nudges[:2]
        )
    
    async def _detect_herding(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect herding behavior"""
        evidence = []
        severity = 0.0
        
        # Analyze timing of trades relative to market movements
        momentum_trades = 0
        contrarian_trades = 0
        
        for tx in transaction_history:
            if tx.get('market_momentum'):
                if tx['type'] == 'buy' and tx['market_momentum'] > 0:
                    momentum_trades += 1
                elif tx['type'] == 'sell' and tx['market_momentum'] < 0:
                    momentum_trades += 1
                else:
                    contrarian_trades += 1
        
        if momentum_trades + contrarian_trades > 0:
            herding_ratio = momentum_trades / (momentum_trades + contrarian_trades)
            if herding_ratio > 0.7:
                evidence.append(f"High momentum following: {herding_ratio:.1%}")
                severity = (herding_ratio - 0.5) * 2
        
        # Check for popular stock concentration
        popular_stocks = self._identify_popular_stocks(transaction_history)
        if popular_stocks > 0.5:
            evidence.append("Concentration in trending stocks")
            severity = max(severity, popular_stocks)
        
        nudges = self.nudge_library.get(BehavioralBias.HERDING, [])
        
        return BiasDetection(
            bias_type=BehavioralBias.HERDING,
            severity=severity,
            confidence=0.6 if evidence else 0.2,
            evidence=evidence,
            impact_on_returns=-0.015 * severity,
            recommended_nudges=nudges[:1]
        )
    
    async def _detect_recency(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect recency bias"""
        evidence = []
        severity = 0.0
        
        # Analyze if recent winners are overweighted
        if portfolio_history and len(portfolio_history) > 3:
            recent_performers = []
            for i in range(len(portfolio_history) - 3, len(portfolio_history)):
                portfolio = portfolio_history[i]
                for position in portfolio.get('positions', []):
                    if position.get('recent_return', 0) > 0.1:  # 10% recent return
                        recent_performers.append(position['weight'])
            
            if recent_performers:
                avg_weight = np.mean(recent_performers)
                if avg_weight > 0.15:  # Overweight recent performers
                    evidence.append(f"Overweight recent winners: {avg_weight:.1%}")
                    severity = min((avg_weight - 0.1) * 5, 1.0)
        
        # Check for performance chasing
        performance_chasing = self._detect_performance_chasing(transaction_history)
        if performance_chasing > 0.5:
            evidence.append("Pattern of buying after price increases")
            severity = max(severity, performance_chasing)
        
        nudges = self.nudge_library.get(BehavioralBias.RECENCY, [])
        
        return BiasDetection(
            bias_type=BehavioralBias.RECENCY,
            severity=severity,
            confidence=0.7 if evidence else 0.3,
            evidence=evidence,
            impact_on_returns=-0.02 * severity,
            recommended_nudges=nudges[:1]
        )
    
    async def _detect_anchoring(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect anchoring bias"""
        evidence = []
        severity = 0.0
        
        # Analyze price anchoring in transactions
        for tx in transaction_history:
            if tx.get('reference_price') and tx.get('execution_price'):
                ref_price = tx['reference_price']
                exec_price = tx['execution_price']
                
                # Check if trades cluster around round numbers or previous highs
                if abs(exec_price - ref_price) / ref_price < 0.02:
                    evidence.append("Trading at reference price points")
                    severity = max(severity, 0.5)
        
        return BiasDetection(
            bias_type=BehavioralBias.ANCHORING,
            severity=severity,
            confidence=0.5 if evidence else 0.2,
            evidence=evidence,
            impact_on_returns=-0.01 * severity,
            recommended_nudges=[]
        )
    
    async def _detect_disposition(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect disposition effect"""
        evidence = []
        
        # Proportion of Gains Realized (PGR)
        gains_realized = 0
        gains_total = 0
        
        # Proportion of Losses Realized (PLR)
        losses_realized = 0
        losses_total = 0
        
        for tx in transaction_history:
            return_val = tx.get('return_value', 0)
            if return_val > 0:
                gains_total += 1
                if tx.get('type') == 'sell':
                    gains_realized += 1
            elif return_val < 0:
                losses_total += 1
                if tx.get('type') == 'sell':
                    losses_realized += 1
        
        pgr = gains_realized / max(gains_total, 1)
        plr = losses_realized / max(losses_total, 1)
        
        disposition_effect = pgr - plr
        
        if disposition_effect > 0.1:
            evidence.append(f"Disposition effect: {disposition_effect:.2f}")
            severity = min(disposition_effect * 2, 1.0)
        else:
            severity = 0.0
        
        return BiasDetection(
            bias_type=BehavioralBias.DISPOSITION,
            severity=severity,
            confidence=0.8 if evidence else 0.2,
            evidence=evidence,
            impact_on_returns=-0.025 * severity,
            recommended_nudges=[]
        )
    
    async def _detect_home_bias(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect home bias"""
        evidence = []
        severity = 0.0
        
        if portfolio_history:
            latest = portfolio_history[-1]
            domestic_weight = 0
            
            for position in latest.get('positions', []):
                if position.get('is_domestic', True):
                    domestic_weight += position['weight']
            
            # Compare to global market cap weight (US is ~60% of global)
            expected_domestic = 0.6
            if domestic_weight > expected_domestic + 0.2:
                evidence.append(f"Overweight domestic: {domestic_weight:.1%}")
                severity = min((domestic_weight - expected_domestic) * 2, 1.0)
        
        return BiasDetection(
            bias_type=BehavioralBias.HOME_BIAS,
            severity=severity,
            confidence=0.7 if evidence else 0.3,
            evidence=evidence,
            impact_on_returns=-0.01 * severity,
            recommended_nudges=[]
        )
    
    async def _detect_mental_accounting(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> BiasDetection:
        """Detect mental accounting bias"""
        evidence = []
        severity = 0.0
        
        # Check for separate mental accounts
        accounts = defaultdict(list)
        for tx in transaction_history:
            if tx.get('account_label'):
                accounts[tx['account_label']].append(tx)
        
        if len(accounts) > 3:
            evidence.append(f"Multiple mental accounts: {len(accounts)}")
            
            # Check for suboptimal allocation across accounts
            account_returns = []
            for account_txs in accounts.values():
                returns = [tx.get('return_percentage', 0) for tx in account_txs]
                if returns:
                    account_returns.append(np.mean(returns))
            
            if account_returns:
                return_dispersion = np.std(account_returns)
                if return_dispersion > 0.05:  # 5% dispersion
                    evidence.append(f"Return dispersion: {return_dispersion:.1%}")
                    severity = min(return_dispersion * 10, 1.0)
        
        return BiasDetection(
            bias_type=BehavioralBias.MENTAL_ACCOUNTING,
            severity=severity,
            confidence=0.6 if evidence else 0.2,
            evidence=evidence,
            impact_on_returns=-0.015 * severity,
            recommended_nudges=[]
        )
    
    def _analyze_volatility_response(
        self,
        portfolio_history: List[Dict[str, Any]]
    ) -> float:
        """Analyze response to portfolio volatility"""
        if len(portfolio_history) < 2:
            return 0.0
        
        volatility_events = 0
        overreactions = 0
        
        for i in range(1, len(portfolio_history)):
            prev = portfolio_history[i-1]
            curr = portfolio_history[i]
            
            if prev.get('volatility', 0) > 0.2:  # High volatility
                volatility_events += 1
                
                # Check for panic selling or buying
                allocation_change = abs(
                    curr.get('equity_allocation', 0) - 
                    prev.get('equity_allocation', 0)
                )
                
                if allocation_change > 0.1:  # 10% allocation change
                    overreactions += 1
        
        return overreactions / max(volatility_events, 1)
    
    def _identify_popular_stocks(
        self,
        transaction_history: List[Dict[str, Any]]
    ) -> float:
        """Identify concentration in popular/trending stocks"""
        popular_tickers = {'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA'}
        
        popular_trades = 0
        total_trades = 0
        
        for tx in transaction_history:
            if tx.get('ticker'):
                total_trades += 1
                if tx['ticker'] in popular_tickers:
                    popular_trades += 1
        
        return popular_trades / max(total_trades, 1)
    
    def _detect_performance_chasing(
        self,
        transaction_history: List[Dict[str, Any]]
    ) -> float:
        """Detect pattern of buying after price increases"""
        chase_trades = 0
        total_trades = 0
        
        for tx in transaction_history:
            if tx.get('type') == 'buy' and tx.get('prior_return'):
                total_trades += 1
                if tx['prior_return'] > 0.1:  # Bought after 10% gain
                    chase_trades += 1
        
        return chase_trades / max(total_trades, 1)
    
    def _calculate_loss_aversion(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate loss aversion coefficient"""
        # Implement prospect theory value function fitting
        gains = []
        losses = []
        
        for tx in transaction_history:
            return_val = tx.get('return_value', 0)
            if return_val > 0:
                gains.append(return_val)
            elif return_val < 0:
                losses.append(abs(return_val))
        
        if gains and losses:
            # Simplified loss aversion calculation
            avg_gain_sensitivity = np.mean(gains)
            avg_loss_sensitivity = np.mean(losses)
            
            # Loss aversion coefficient (typically 2-2.5)
            lambda_coefficient = avg_loss_sensitivity / max(avg_gain_sensitivity, 0.01)
            return min(max(lambda_coefficient, 1.0), 4.0)
        
        return self.loss_aversion_baseline
    
    def _assess_risk_perception(
        self,
        portfolio_history: List[Dict[str, Any]],
        questionnaire: Optional[Dict[str, Any]]
    ) -> float:
        """Assess behavioral risk perception"""
        perceived_risk = 0.5  # Default neutral
        
        # Analyze portfolio risk-taking
        if portfolio_history:
            recent_portfolios = portfolio_history[-5:]
            equity_allocations = [
                p.get('equity_allocation', 0) for p in recent_portfolios
            ]
            avg_equity = np.mean(equity_allocations) if equity_allocations else 0.5
            perceived_risk = avg_equity
        
        # Adjust based on questionnaire
        if questionnaire:
            stated_risk = questionnaire.get('risk_tolerance', 0.5)
            perceived_risk = 0.7 * perceived_risk + 0.3 * stated_risk
        
        return perceived_risk
    
    def _calculate_time_preference(
        self,
        transaction_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate time preference (hyperbolic discounting)"""
        holding_periods = []
        
        for tx in transaction_history:
            if tx.get('holding_days'):
                holding_periods.append(tx['holding_days'])
        
        if holding_periods:
            avg_holding = np.mean(holding_periods)
            
            # Convert to annual discount factor
            # Shorter holding = higher discount rate
            if avg_holding < 30:  # Less than a month
                return 0.5  # High time preference
            elif avg_holding < 365:  # Less than a year
                return 0.7
            else:
                return 0.9  # Low time preference
        
        return 0.8  # Default
    
    def _assess_social_influence(
        self,
        transaction_history: List[Dict[str, Any]],
        questionnaire: Optional[Dict[str, Any]]
    ) -> float:
        """Assess sensitivity to social influence"""
        social_score = 0.3  # Default
        
        # Check for social trading patterns
        social_indicators = 0
        total_indicators = 0
        
        for tx in transaction_history:
            if tx.get('trigger'):
                total_indicators += 1
                if 'social' in tx['trigger'].lower() or 'friend' in tx['trigger'].lower():
                    social_indicators += 1
        
        if total_indicators > 0:
            social_score = social_indicators / total_indicators
        
        # Adjust based on questionnaire
        if questionnaire and 'social_influence' in questionnaire:
            stated_social = questionnaire['social_influence']
            social_score = 0.6 * social_score + 0.4 * stated_social
        
        return social_score
    
    def _classify_decision_style(
        self,
        transaction_history: List[Dict[str, Any]],
        questionnaire: Optional[Dict[str, Any]]
    ) -> str:
        """Classify decision-making style"""
        # Analyze transaction patterns
        if not transaction_history:
            return "unknown"
        
        # Calculate metrics
        avg_decision_time = np.mean([
            tx.get('decision_time_hours', 24) 
            for tx in transaction_history
        ])
        
        research_depth = np.mean([
            tx.get('research_sources', 1)
            for tx in transaction_history
        ])
        
        # Classify based on patterns
        if avg_decision_time < 2 and research_depth < 2:
            return "spontaneous"
        elif avg_decision_time > 48 and research_depth > 5:
            return "analytical"
        elif research_depth > 3 and 'advisor' in str(transaction_history):
            return "dependent"
        else:
            return "intuitive"
    
    def _assess_financial_literacy(
        self,
        questionnaire: Optional[Dict[str, Any]]
    ) -> float:
        """Assess financial literacy level"""
        if not questionnaire:
            return 0.5  # Default medium literacy
        
        literacy_score = 0.0
        literacy_questions = questionnaire.get('financial_literacy', {})
        
        # Basic financial concepts
        weights = {
            'compound_interest': 0.2,
            'inflation': 0.2,
            'diversification': 0.2,
            'risk_return': 0.2,
            'market_efficiency': 0.2
        }
        
        for concept, weight in weights.items():
            if concept in literacy_questions:
                literacy_score += literacy_questions[concept] * weight
        
        return literacy_score
    
    def _identify_stress_pattern(
        self,
        transaction_history: List[Dict[str, Any]]
    ) -> str:
        """Identify stress response pattern"""
        stress_trades = []
        
        for tx in transaction_history:
            if tx.get('market_stress', 0) > 0.7:  # High stress period
                stress_trades.append(tx)
        
        if not stress_trades:
            return "untested"
        
        # Analyze behavior during stress
        panic_sells = sum(1 for tx in stress_trades if tx.get('type') == 'sell')
        bargain_hunts = sum(1 for tx in stress_trades if tx.get('type') == 'buy')
        
        if panic_sells > bargain_hunts * 2:
            return "panic_seller"
        elif bargain_hunts > panic_sells * 2:
            return "contrarian"
        else:
            return "steady"
    
    def _identify_effective_nudges(
        self,
        biases: List[BiasDetection]
    ) -> List[NudgeType]:
        """Identify most effective nudge types for detected biases"""
        nudge_effectiveness = defaultdict(float)
        
        for bias in biases:
            for nudge in bias.recommended_nudges:
                nudge_effectiveness[nudge.nudge_type] += (
                    nudge.expected_effectiveness * bias.severity
                )
        
        # Sort by effectiveness
        sorted_nudges = sorted(
            nudge_effectiveness.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [nudge_type for nudge_type, _ in sorted_nudges[:5]]
    
    async def create_nudge_engine(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> List[Nudge]:
        """
        Create personalized nudges based on behavioral profile
        
        Args:
            user_id: User identifier
            context: Current decision context
            
        Returns:
            List of personalized nudges
        """
        try:
            profile = self.behavioral_profiles.get(user_id)
            if not profile:
                logger.warning(f"No behavioral profile found for user {user_id}")
                return []
            
            nudges = []
            
            # Generate nudges for each detected bias
            for bias in profile.detected_biases[:3]:  # Top 3 biases
                bias_nudges = self._generate_contextual_nudges(
                    bias,
                    context,
                    profile
                )
                nudges.extend(bias_nudges)
            
            # Personalize nudges
            nudges = self._personalize_nudges(nudges, profile, context)
            
            # Rank by expected effectiveness
            nudges.sort(key=lambda x: x.expected_effectiveness, reverse=True)
            
            logger.info(f"Generated {len(nudges)} nudges for user {user_id}")
            return nudges[:5]  # Return top 5 nudges
            
        except Exception as e:
            logger.error(f"Error creating nudge engine: {str(e)}")
            raise
    
    def _generate_contextual_nudges(
        self,
        bias: BiasDetection,
        context: Dict[str, Any],
        profile: BehavioralProfile
    ) -> List[Nudge]:
        """Generate context-specific nudges for a bias"""
        nudges = []
        
        # Get base nudges for this bias
        base_nudges = self.nudge_library.get(bias.bias_type, [])
        
        for base_nudge in base_nudges:
            # Adapt nudge to context
            if self._is_nudge_appropriate(base_nudge, context, profile):
                personalized = self._adapt_nudge_to_context(
                    base_nudge,
                    context,
                    bias
                )
                nudges.append(personalized)
        
        return nudges
    
    def _is_nudge_appropriate(
        self,
        nudge: Nudge,
        context: Dict[str, Any],
        profile: BehavioralProfile
    ) -> bool:
        """Check if nudge is appropriate for current context"""
        # Check if nudge type is preferred
        if nudge.nudge_type not in profile.preferred_nudge_types:
            return False
        
        # Check context compatibility
        if nudge.personalization_factors:
            for factor, value in nudge.personalization_factors.items():
                if factor in context and context[factor] != value:
                    return False
        
        return True
    
    def _adapt_nudge_to_context(
        self,
        nudge: Nudge,
        context: Dict[str, Any],
        bias: BiasDetection
    ) -> Nudge:
        """Adapt nudge message to specific context"""
        # Create a copy
        adapted = Nudge(
            nudge_type=nudge.nudge_type,
            message=nudge.message,
            action=nudge.action,
            expected_effectiveness=nudge.expected_effectiveness,
            implementation_difficulty=nudge.implementation_difficulty,
            personalization_factors=nudge.personalization_factors.copy()
        )
        
        # Personalize message with context data
        if '{amount}' in adapted.message and 'portfolio_value' in context:
            adapted.message = adapted.message.replace(
                '{amount}',
                f"${context['portfolio_value']:,.0f}"
            )
        
        if '{returns}' in adapted.message and 'historical_return' in context:
            adapted.message = adapted.message.replace(
                '{returns}',
                f"{context['historical_return']:.1f}"
            )
        
        if '{accuracy}' in adapted.message:
            accuracy = 100 - (bias.severity * 50)  # Simplified
            adapted.message = adapted.message.replace(
                '{accuracy}',
                f"{accuracy:.0f}"
            )
        
        # Adjust timing based on context
        if context.get('urgency') == 'high':
            adapted.timing = "immediate"
        elif context.get('urgency') == 'low':
            adapted.timing = "weekly"
        else:
            adapted.timing = "daily"
        
        return adapted
    
    def _personalize_nudges(
        self,
        nudges: List[Nudge],
        profile: BehavioralProfile,
        context: Dict[str, Any]
    ) -> List[Nudge]:
        """Personalize nudges based on individual profile"""
        personalized = []
        
        for nudge in nudges:
            # Adjust effectiveness based on profile
            effectiveness = nudge.expected_effectiveness
            
            # Increase effectiveness for preferred nudge types
            if nudge.nudge_type in profile.preferred_nudge_types:
                effectiveness *= 1.2
            
            # Adjust for cognitive load
            if profile.cognitive_load_capacity < 0.5:
                if nudge.implementation_difficulty == "hard":
                    effectiveness *= 0.5
            
            # Adjust for decision style
            if profile.decision_style == "analytical":
                if nudge.nudge_type == NudgeType.FEEDBACK:
                    effectiveness *= 1.3
            elif profile.decision_style == "spontaneous":
                if nudge.nudge_type == NudgeType.DEFAULT_SETTING:
                    effectiveness *= 1.4
            
            nudge.expected_effectiveness = min(effectiveness, 1.0)
            personalized.append(nudge)
        
        return personalized
    
    async def optimize_mental_accounting(
        self,
        user_id: str,
        current_accounts: List[MentalAccount],
        goals: List[Dict[str, Any]]
    ) -> List[MentalAccount]:
        """
        Optimize mental accounting structure
        
        Args:
            user_id: User identifier
            current_accounts: Current mental accounts
            goals: Financial goals
            
        Returns:
            Optimized mental account structure
        """
        try:
            profile = self.behavioral_profiles.get(user_id)
            
            # Consolidate overlapping accounts
            optimized_accounts = self._consolidate_accounts(current_accounts)
            
            # Align with goals
            optimized_accounts = self._align_accounts_with_goals(
                optimized_accounts,
                goals
            )
            
            # Apply behavioral constraints
            if profile:
                optimized_accounts = self._apply_behavioral_constraints(
                    optimized_accounts,
                    profile
                )
            
            # Optimize allocation
            optimized_accounts = self._optimize_account_allocation(
                optimized_accounts
            )
            
            logger.info(f"Optimized mental accounting for user {user_id}")
            return optimized_accounts
            
        except Exception as e:
            logger.error(f"Error optimizing mental accounting: {str(e)}")
            raise
    
    def _consolidate_accounts(
        self,
        accounts: List[MentalAccount]
    ) -> List[MentalAccount]:
        """Consolidate overlapping mental accounts"""
        consolidated = []
        processed = set()
        
        for i, account in enumerate(accounts):
            if i in processed:
                continue
            
            # Find similar accounts
            similar = [account]
            for j, other in enumerate(accounts[i+1:], i+1):
                if self._accounts_similar(account, other):
                    similar.append(other)
                    processed.add(j)
            
            # Merge similar accounts
            if len(similar) > 1:
                merged = self._merge_accounts(similar)
                consolidated.append(merged)
            else:
                consolidated.append(account)
        
        return consolidated
    
    def _accounts_similar(
        self,
        acc1: MentalAccount,
        acc2: MentalAccount
    ) -> bool:
        """Check if two mental accounts are similar"""
        # Similar time horizon
        horizon_similar = abs(acc1.time_horizon - acc2.time_horizon) < 12
        
        # Similar risk tolerance
        risk_similar = acc1.risk_tolerance == acc2.risk_tolerance
        
        # Similar purpose
        purpose_similar = (
            acc1.purpose.lower() in acc2.purpose.lower() or
            acc2.purpose.lower() in acc1.purpose.lower()
        )
        
        return horizon_similar and (risk_similar or purpose_similar)
    
    def _merge_accounts(
        self,
        accounts: List[MentalAccount]
    ) -> MentalAccount:
        """Merge multiple mental accounts"""
        total_value = sum(acc.current_value for acc in accounts)
        total_target = sum(acc.target_value for acc in accounts)
        avg_horizon = np.mean([acc.time_horizon for acc in accounts])
        
        # Combine assets
        all_assets = []
        for acc in accounts:
            all_assets.extend(acc.assets)
        
        # Combine constraints
        all_constraints = []
        for acc in accounts:
            all_constraints.extend(acc.behavioral_constraints)
        
        return MentalAccount(
            name=f"Consolidated: {accounts[0].name}",
            purpose="; ".join([acc.purpose for acc in accounts]),
            current_value=total_value,
            target_value=total_target,
            time_horizon=int(avg_horizon),
            risk_tolerance=accounts[0].risk_tolerance,
            assets=list(set(all_assets)),
            allocation_percentage=sum(acc.allocation_percentage for acc in accounts),
            behavioral_constraints=list(set(all_constraints))
        )
    
    def _align_accounts_with_goals(
        self,
        accounts: List[MentalAccount],
        goals: List[Dict[str, Any]]
    ) -> List[MentalAccount]:
        """Align mental accounts with financial goals"""
        aligned = accounts.copy()
        
        # Create accounts for unmatched goals
        for goal in goals:
            matched = False
            for account in aligned:
                if self._goal_matches_account(goal, account):
                    matched = True
                    # Update account target
                    account.target_value = max(
                        account.target_value,
                        goal.get('target_amount', account.target_value)
                    )
                    break
            
            if not matched:
                # Create new mental account for goal
                new_account = MentalAccount(
                    name=goal.get('name', 'New Goal'),
                    purpose=goal.get('description', ''),
                    current_value=0,
                    target_value=goal.get('target_amount', 0),
                    time_horizon=goal.get('time_horizon_months', 60),
                    risk_tolerance=goal.get('risk_level', 'moderate'),
                    assets=[],
                    allocation_percentage=0,
                    behavioral_constraints=[]
                )
                aligned.append(new_account)
        
        return aligned
    
    def _goal_matches_account(
        self,
        goal: Dict[str, Any],
        account: MentalAccount
    ) -> bool:
        """Check if goal matches mental account"""
        # Name similarity
        if goal.get('name', '').lower() in account.name.lower():
            return True
        
        # Purpose similarity
        if goal.get('description', '').lower() in account.purpose.lower():
            return True
        
        # Time horizon similarity
        goal_horizon = goal.get('time_horizon_months', 0)
        if abs(goal_horizon - account.time_horizon) < 6:
            return True
        
        return False
    
    def _apply_behavioral_constraints(
        self,
        accounts: List[MentalAccount],
        profile: BehavioralProfile
    ) -> List[MentalAccount]:
        """Apply behavioral constraints to mental accounts"""
        for account in accounts:
            constraints = []
            
            # Loss aversion constraints
            if profile.loss_aversion_coefficient > 2.5:
                constraints.append("Limit downside to -10% annually")
                constraints.append("Rebalance quarterly to maintain risk level")
            
            # Time preference constraints
            if profile.time_preference < 0.6:  # High time preference
                constraints.append("Lock funds for minimum 6 months")
                constraints.append("Automatic transfers to prevent early withdrawal")
            
            # Overconfidence constraints
            for bias in profile.detected_biases:
                if bias.bias_type == BehavioralBias.OVERCONFIDENCE:
                    if bias.severity > 0.5:
                        constraints.append("Maximum 20% in single position")
                        constraints.append("Minimum 10 holdings required")
            
            account.behavioral_constraints = constraints
        
        return accounts
    
    def _optimize_account_allocation(
        self,
        accounts: List[MentalAccount]
    ) -> List[MentalAccount]:
        """Optimize allocation across mental accounts"""
        total_value = sum(acc.current_value for acc in accounts)
        
        if total_value == 0:
            # Equal allocation for new accounts
            for account in accounts:
                account.allocation_percentage = 1.0 / len(accounts)
        else:
            # Optimize based on goals and constraints
            allocations = self._solve_allocation_optimization(accounts)
            
            for account, allocation in zip(accounts, allocations):
                account.allocation_percentage = allocation
        
        return accounts
    
    def _solve_allocation_optimization(
        self,
        accounts: List[MentalAccount]
    ) -> List[float]:
        """Solve allocation optimization problem"""
        n_accounts = len(accounts)
        
        # Objective: minimize distance to targets
        def objective(weights):
            total_distance = 0
            for i, account in enumerate(accounts):
                current = weights[i] * sum(acc.current_value for acc in accounts)
                distance = (account.target_value - current) ** 2
                total_distance += distance
            return total_distance
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Sum to 1
        ]
        
        # Bounds (0 to 1 for each weight)
        bounds = [(0, 1) for _ in range(n_accounts)]
        
        # Initial guess (equal weights)
        x0 = np.ones(n_accounts) / n_accounts
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        return result.x.tolist() if result.success else x0.tolist()
    
    async def create_goal_based_buckets(
        self,
        user_id: str,
        goals: List[Dict[str, Any]],
        total_portfolio_value: float
    ) -> List[GoalBasedBucket]:
        """
        Create goal-based investment buckets
        
        Args:
            user_id: User identifier
            goals: Financial goals
            total_portfolio_value: Total portfolio value
            
        Returns:
            Goal-based bucket structure
        """
        try:
            profile = self.behavioral_profiles.get(user_id)
            
            # Categorize goals into buckets
            buckets = self._categorize_goals_into_buckets(goals)
            
            # Allocate portfolio across buckets
            buckets = self._allocate_to_buckets(
                buckets,
                total_portfolio_value,
                profile
            )
            
            # Apply behavioral guardrails
            buckets = self._apply_bucket_guardrails(buckets, profile)
            
            # Optimize within each bucket
            buckets = await self._optimize_bucket_portfolios(buckets)
            
            logger.info(f"Created {len(buckets)} goal-based buckets for user {user_id}")
            return buckets
            
        except Exception as e:
            logger.error(f"Error creating goal-based buckets: {str(e)}")
            raise
    
    def _categorize_goals_into_buckets(
        self,
        goals: List[Dict[str, Any]]
    ) -> List[GoalBasedBucket]:
        """Categorize goals into appropriate buckets"""
        buckets = {
            GoalBucket.SAFETY: [],
            GoalBucket.SECURITY: [],
            GoalBucket.GROWTH: [],
            GoalBucket.ASPIRATION: [],
            GoalBucket.LEGACY: []
        }
        
        for goal in goals:
            bucket_type = self._determine_bucket_type(goal)
            buckets[bucket_type].append(goal)
        
        # Create bucket objects
        bucket_objects = []
        for bucket_type, bucket_goals in buckets.items():
            if bucket_goals:
                bucket = self._create_bucket(bucket_type, bucket_goals)
                bucket_objects.append(bucket)
        
        return bucket_objects
    
    def _determine_bucket_type(self, goal: Dict[str, Any]) -> GoalBucket:
        """Determine appropriate bucket for a goal"""
        priority = goal.get('priority', 3)
        time_horizon = goal.get('time_horizon_months', 60)
        goal_type = goal.get('type', '').lower()
        
        # Safety: Emergency and essential near-term
        if 'emergency' in goal_type or time_horizon < 6:
            return GoalBucket.SAFETY
        
        # Security: Essential medium-term goals
        elif priority <= 2 and time_horizon < 36:
            return GoalBucket.SECURITY
        
        # Legacy: Long-term wealth transfer
        elif 'estate' in goal_type or 'legacy' in goal_type:
            return GoalBucket.LEGACY
        
        # Aspiration: Nice-to-have goals
        elif priority >= 4:
            return GoalBucket.ASPIRATION
        
        # Growth: Standard long-term goals
        else:
            return GoalBucket.GROWTH
    
    def _create_bucket(
        self,
        bucket_type: GoalBucket,
        goals: List[Dict[str, Any]]
    ) -> GoalBasedBucket:
        """Create a goal-based bucket"""
        # Aggregate goal characteristics
        total_target = sum(g.get('target_amount', 0) for g in goals)
        avg_horizon = np.mean([g.get('time_horizon_months', 60) for g in goals])
        min_priority = min(g.get('priority', 3) for g in goals)
        
        # Determine required return and risk budget
        required_return, risk_budget = self._calculate_bucket_parameters(
            bucket_type,
            avg_horizon,
            total_target
        )
        
        return GoalBasedBucket(
            bucket_type=bucket_type,
            goal_description="; ".join([g.get('name', '') for g in goals]),
            priority=min_priority,
            current_allocation=0,
            target_allocation=0,
            time_horizon=int(avg_horizon),
            required_return=required_return,
            risk_budget=risk_budget,
            assets=[],
            behavioral_guardrails=[]
        )
    
    def _calculate_bucket_parameters(
        self,
        bucket_type: GoalBucket,
        time_horizon: float,
        target_amount: float
    ) -> Tuple[float, float]:
        """Calculate required return and risk budget for bucket"""
        # Base parameters by bucket type
        params = {
            GoalBucket.SAFETY: (0.02, 0.05),  # 2% return, 5% risk
            GoalBucket.SECURITY: (0.04, 0.10),  # 4% return, 10% risk
            GoalBucket.GROWTH: (0.07, 0.15),  # 7% return, 15% risk
            GoalBucket.ASPIRATION: (0.10, 0.25),  # 10% return, 25% risk
            GoalBucket.LEGACY: (0.06, 0.12),  # 6% return, 12% risk
        }
        
        base_return, base_risk = params[bucket_type]
        
        # Adjust for time horizon
        time_factor = min(time_horizon / 120, 1.5)  # Cap at 10 years
        
        required_return = base_return * time_factor
        risk_budget = base_risk * np.sqrt(time_factor)
        
        return required_return, risk_budget
    
    def _allocate_to_buckets(
        self,
        buckets: List[GoalBasedBucket],
        total_value: float,
        profile: Optional[BehavioralProfile]
    ) -> List[GoalBasedBucket]:
        """Allocate portfolio value across buckets"""
        # Priority-based allocation
        total_priority = sum(1.0 / b.priority for b in buckets)
        
        for bucket in buckets:
            # Base allocation on priority
            base_allocation = (1.0 / bucket.priority) / total_priority
            
            # Adjust for behavioral factors
            if profile:
                if bucket.bucket_type == GoalBucket.SAFETY:
                    # Increase safety for high loss aversion
                    base_allocation *= (1 + 0.2 * (profile.loss_aversion_coefficient - 2))
                elif bucket.bucket_type == GoalBucket.ASPIRATION:
                    # Decrease aspiration for high loss aversion
                    base_allocation *= (1 - 0.1 * (profile.loss_aversion_coefficient - 2))
            
            bucket.target_allocation = base_allocation
            bucket.current_allocation = base_allocation * total_value
        
        # Normalize allocations
        total_allocation = sum(b.target_allocation for b in buckets)
        for bucket in buckets:
            bucket.target_allocation /= total_allocation
        
        return buckets
    
    def _apply_bucket_guardrails(
        self,
        buckets: List[GoalBasedBucket],
        profile: Optional[BehavioralProfile]
    ) -> List[GoalBasedBucket]:
        """Apply behavioral guardrails to buckets"""
        for bucket in buckets:
            guardrails = []
            
            # Safety bucket guardrails
            if bucket.bucket_type == GoalBucket.SAFETY:
                guardrails.append("No equities allowed")
                guardrails.append("Maximum 1-year duration")
                guardrails.append("Daily liquidity required")
            
            # Security bucket guardrails
            elif bucket.bucket_type == GoalBucket.SECURITY:
                guardrails.append("Maximum 40% equities")
                guardrails.append("Investment-grade bonds only")
                guardrails.append("Quarterly rebalancing")
            
            # Growth bucket guardrails
            elif bucket.bucket_type == GoalBucket.GROWTH:
                guardrails.append("60-80% equity allocation")
                guardrails.append("Global diversification required")
                guardrails.append("Annual rebalancing")
            
            # Aspiration bucket guardrails
            elif bucket.bucket_type == GoalBucket.ASPIRATION:
                guardrails.append("Alternative investments allowed")
                guardrails.append("Higher concentration permitted")
                guardrails.append("Locked for minimum 2 years")
            
            # Legacy bucket guardrails
            elif bucket.bucket_type == GoalBucket.LEGACY:
                guardrails.append("Tax-efficient vehicles required")
                guardrails.append("Estate planning integration")
                guardrails.append("Conservative growth focus")
            
            # Add behavioral guardrails
            if profile:
                for bias in profile.detected_biases:
                    if bias.severity > 0.5:
                        if bias.bias_type == BehavioralBias.OVERCONFIDENCE:
                            guardrails.append("Maximum 10% single position")
                        elif bias.bias_type == BehavioralBias.LOSS_AVERSION:
                            guardrails.append("Stop-loss at -15%")
            
            bucket.behavioral_guardrails = guardrails
        
        return buckets
    
    async def _optimize_bucket_portfolios(
        self,
        buckets: List[GoalBasedBucket]
    ) -> List[GoalBasedBucket]:
        """Optimize portfolio within each bucket"""
        for bucket in buckets:
            # Define asset universe for bucket
            assets = self._get_bucket_assets(bucket.bucket_type)
            
            # Optimize allocation
            weights = self._optimize_bucket_allocation(
                assets,
                bucket.required_return,
                bucket.risk_budget
            )
            
            # Create asset allocation
            bucket.assets = [
                {'asset': asset, 'weight': weight}
                for asset, weight in zip(assets, weights)
            ]
        
        return buckets
    
    def _get_bucket_assets(self, bucket_type: GoalBucket) -> List[str]:
        """Get appropriate assets for bucket type"""
        assets_map = {
            GoalBucket.SAFETY: [
                'money_market', 'treasury_bills', 'high_yield_savings'
            ],
            GoalBucket.SECURITY: [
                'investment_grade_bonds', 'dividend_stocks', 'balanced_funds'
            ],
            GoalBucket.GROWTH: [
                'us_equities', 'international_equities', 'growth_stocks', 'reits'
            ],
            GoalBucket.ASPIRATION: [
                'emerging_markets', 'commodities', 'private_equity', 'crypto'
            ],
            GoalBucket.LEGACY: [
                'blue_chip_stocks', 'municipal_bonds', 'dividend_aristocrats'
            ]
        }
        return assets_map.get(bucket_type, [])
    
    def _optimize_bucket_allocation(
        self,
        assets: List[str],
        required_return: float,
        risk_budget: float
    ) -> List[float]:
        """Optimize allocation within a bucket"""
        n_assets = len(assets)
        
        # Simplified optimization (equal weight for now)
        # In production, use historical returns and covariance
        weights = np.ones(n_assets) / n_assets
        
        # Adjust for risk budget (simplified)
        if risk_budget < 0.10:  # Conservative
            # Overweight safer assets (assume first assets are safer)
            weights = np.array([0.6, 0.3, 0.1] if n_assets >= 3 else weights)
        elif risk_budget > 0.20:  # Aggressive
            # Overweight riskier assets (assume last assets are riskier)
            weights = np.array([0.1, 0.3, 0.6] if n_assets >= 3 else weights)
        
        # Normalize
        weights = weights[:n_assets]  # Ensure correct length
        weights = weights / weights.sum()
        
        return weights.tolist()
    
    async def implement_commitment_devices(
        self,
        user_id: str,
        portfolio: Dict[str, Any],
        goals: List[Dict[str, Any]]
    ) -> List[CommitmentDevice]:
        """
        Implement commitment devices for behavioral control
        
        Args:
            user_id: User identifier
            portfolio: Current portfolio
            goals: Financial goals
            
        Returns:
            List of commitment devices
        """
        try:
            profile = self.behavioral_profiles.get(user_id)
            if not profile:
                logger.warning(f"No profile found for user {user_id}")
                return []
            
            devices = []
            
            # Create devices based on detected biases
            for bias in profile.detected_biases:
                if bias.severity > 0.4:  # Significant bias
                    bias_devices = self._create_bias_commitment_devices(
                        bias,
                        profile
                    )
                    devices.extend(bias_devices)
            
            # Add goal-based commitment devices
            goal_devices = self._create_goal_commitment_devices(goals, profile)
            devices.extend(goal_devices)
            
            # Add portfolio protection devices
            protection_devices = self._create_protection_devices(
                portfolio,
                profile
            )
            devices.extend(protection_devices)
            
            # Store devices
            self.commitment_devices[user_id] = devices
            
            logger.info(f"Implemented {len(devices)} commitment devices for user {user_id}")
            return devices
            
        except Exception as e:
            logger.error(f"Error implementing commitment devices: {str(e)}")
            raise
    
    def _create_bias_commitment_devices(
        self,
        bias: BiasDetection,
        profile: BehavioralProfile
    ) -> List[CommitmentDevice]:
        """Create commitment devices for specific bias"""
        devices = []
        
        if bias.bias_type == BehavioralBias.LOSS_AVERSION:
            devices.append(CommitmentDevice(
                device_id=f"loss_aversion_{datetime.now().timestamp()}",
                level=CommitmentLevel.MODERATE,
                description="Prevent panic selling during market downturns",
                trigger_conditions=[
                    "Portfolio down >10% in a week",
                    "Single position down >20%"
                ],
                actions=[
                    "Block sell orders for 48 hours",
                    "Require advisor approval for sells",
                    "Show long-term performance chart"
                ],
                override_requirements={
                    "cooling_period": 48,
                    "advisor_approval": True
                },
                effectiveness_score=0.75,
                user_acceptance=0.6
            ))
        
        elif bias.bias_type == BehavioralBias.OVERCONFIDENCE:
            devices.append(CommitmentDevice(
                device_id=f"overconfidence_{datetime.now().timestamp()}",
                level=CommitmentLevel.HARD,
                description="Enforce diversification limits",
                trigger_conditions=[
                    "Single position >25% of portfolio",
                    "Sector concentration >40%"
                ],
                actions=[
                    "Block trades increasing concentration",
                    "Force rebalancing alert",
                    "Require risk assessment quiz"
                ],
                override_requirements={
                    "risk_assessment_score": 0.8,
                    "written_justification": True
                },
                effectiveness_score=0.8,
                user_acceptance=0.5
            ))
        
        elif bias.bias_type == BehavioralBias.HERDING:
            devices.append(CommitmentDevice(
                device_id=f"herding_{datetime.now().timestamp()}",
                level=CommitmentLevel.SOFT,
                description="Encourage contrarian thinking",
                trigger_conditions=[
                    "Buying trending stocks",
                    "Following social media recommendations"
                ],
                actions=[
                    "Show contrarian indicators",
                    "Highlight personal goals",
                    "Delay order by 24 hours"
                ],
                override_requirements=None,
                effectiveness_score=0.6,
                user_acceptance=0.8
            ))
        
        return devices
    
    def _create_goal_commitment_devices(
        self,
        goals: List[Dict[str, Any]],
        profile: BehavioralProfile
    ) -> List[CommitmentDevice]:
        """Create commitment devices for goals"""
        devices = []
        
        for goal in goals:
            if goal.get('priority', 3) <= 2:  # High priority goals
                devices.append(CommitmentDevice(
                    device_id=f"goal_{goal.get('id', datetime.now().timestamp())}",
                    level=CommitmentLevel.MODERATE,
                    description=f"Protect funding for {goal.get('name', 'goal')}",
                    trigger_conditions=[
                        f"Withdrawal from {goal.get('name', 'goal')} bucket",
                        "Reallocation reducing goal funding"
                    ],
                    actions=[
                        "Require goal impact analysis",
                        "Show alternative funding sources",
                        "Implement 7-day waiting period"
                    ],
                    override_requirements={
                        "emergency": True,
                        "alternative_plan": True
                    },
                    effectiveness_score=0.7,
                    user_acceptance=0.7
                ))
        
        return devices
    
    def _create_protection_devices(
        self,
        portfolio: Dict[str, Any],
        profile: BehavioralProfile
    ) -> List[CommitmentDevice]:
        """Create portfolio protection devices"""
        devices = []
        
        # Drawdown protection
        devices.append(CommitmentDevice(
            device_id=f"drawdown_protection_{datetime.now().timestamp()}",
            level=CommitmentLevel.HARD,
            description="Protect against excessive drawdowns",
            trigger_conditions=[
                "Portfolio drawdown >20%",
                "Monthly loss >10%"
            ],
            actions=[
                "Automatically reduce equity allocation by 20%",
                "Shift to defensive assets",
                "Lock changes for 30 days"
            ],
            override_requirements={
                "professional_advisor": True,
                "risk_tolerance_reassessment": True
            },
            effectiveness_score=0.85,
            user_acceptance=0.4
        ))
        
        # Savings protection
        if profile.time_preference < 0.6:  # High time preference
            devices.append(CommitmentDevice(
                device_id=f"savings_protection_{datetime.now().timestamp()}",
                level=CommitmentLevel.MODERATE,
                description="Enforce regular savings",
                trigger_conditions=[
                    "Missed monthly contribution",
                    "Withdrawal from long-term savings"
                ],
                actions=[
                    "Automatic transfer from checking",
                    "Increase next month's contribution",
                    "Send commitment reminder"
                ],
                override_requirements={
                    "financial_hardship": True
                },
                effectiveness_score=0.7,
                user_acceptance=0.6
            ))
        
        return devices
    
    async def build_behavioral_portfolio(
        self,
        user_id: str,
        capital: float,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build behavior-optimized portfolio with guardrails
        
        Args:
            user_id: User identifier
            capital: Available capital
            constraints: Investment constraints
            
        Returns:
            Behavior-optimized portfolio
        """
        try:
            profile = self.behavioral_profiles.get(user_id)
            if not profile:
                raise ValueError(f"No behavioral profile for user {user_id}")
            
            # Adjust traditional optimization for behavioral factors
            behavioral_constraints = self._create_behavioral_constraints(
                profile,
                constraints
            )
            
            # Create behavioral utility function
            utility_params = self._create_utility_parameters(profile)
            
            # Optimize portfolio with behavioral considerations
            portfolio = await self._optimize_behavioral_portfolio(
                capital,
                behavioral_constraints,
                utility_params
            )
            
            # Apply behavioral tilts
            portfolio = self._apply_behavioral_tilts(portfolio, profile)
            
            # Add behavioral monitoring
            portfolio['behavioral_monitoring'] = self._setup_behavioral_monitoring(
                portfolio,
                profile
            )
            
            logger.info(f"Built behavioral portfolio for user {user_id}")
            return portfolio
            
        except Exception as e:
            logger.error(f"Error building behavioral portfolio: {str(e)}")
            raise
    
    def _create_behavioral_constraints(
        self,
        profile: BehavioralProfile,
        base_constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create behavioral constraints for optimization"""
        constraints = base_constraints or {}
        
        # Loss aversion constraints
        if profile.loss_aversion_coefficient > 2.5:
            constraints['max_drawdown'] = 0.15  # 15% maximum drawdown
            constraints['min_sharpe'] = 0.5
        
        # Overconfidence constraints
        overconfidence_bias = next(
            (b for b in profile.detected_biases 
             if b.bias_type == BehavioralBias.OVERCONFIDENCE),
            None
        )
        if overconfidence_bias and overconfidence_bias.severity > 0.5:
            constraints['max_position_size'] = 0.10  # 10% max per position
            constraints['min_positions'] = 15  # Minimum diversification
        
        # Time preference constraints
        if profile.time_preference < 0.7:  # Impatient
            constraints['liquidity_requirement'] = 0.3  # 30% liquid assets
        
        return constraints
    
    def _create_utility_parameters(
        self,
        profile: BehavioralProfile
    ) -> Dict[str, float]:
        """Create parameters for behavioral utility function"""
        return {
            'risk_aversion': profile.loss_aversion_coefficient,
            'loss_aversion': profile.loss_aversion_coefficient,
            'time_discount': profile.time_preference,
            'reference_point': 0.07,  # Expected return reference
            'probability_weighting': 0.65  # Kahneman-Tversky parameter
        }
    
    async def _optimize_behavioral_portfolio(
        self,
        capital: float,
        constraints: Dict[str, Any],
        utility_params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Optimize portfolio with behavioral utility"""
        # Simplified behavioral portfolio optimization
        # In production, integrate with actual optimization engine
        
        # Define behavioral utility function
        def behavioral_utility(weights, returns, risks):
            expected_return = np.dot(weights, returns)
            portfolio_risk = np.sqrt(np.dot(weights, risks**2))
            
            # Prospect theory utility
            reference = utility_params['reference_point']
            if expected_return >= reference:
                # Gains domain
                utility = (expected_return - reference) ** 0.88
            else:
                # Losses domain
                lambda_loss = utility_params['loss_aversion']
                utility = -lambda_loss * (reference - expected_return) ** 0.88
            
            # Risk penalty
            risk_aversion = utility_params['risk_aversion']
            utility -= risk_aversion * portfolio_risk ** 2
            
            return utility
        
        # Sample assets (simplified)
        assets = ['stocks', 'bonds', 'real_estate', 'commodities', 'cash']
        expected_returns = np.array([0.10, 0.04, 0.08, 0.06, 0.02])
        risks = np.array([0.20, 0.05, 0.15, 0.25, 0.01])
        
        # Optimize
        n_assets = len(assets)
        
        def objective(weights):
            return -behavioral_utility(weights, expected_returns, risks)
        
        # Constraints
        optimization_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        # Add behavioral constraints
        if 'max_position_size' in constraints:
            max_size = constraints['max_position_size']
            for i in range(n_assets):
                optimization_constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, i=i: max_size - x[i]
                })
        
        # Bounds
        bounds = [(0, 1) for _ in range(n_assets)]
        
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=optimization_constraints
        )
        
        # Create portfolio
        portfolio = {
            'capital': capital,
            'positions': [],
            'expected_return': 0,
            'risk': 0,
            'behavioral_score': 0
        }
        
        if result.success:
            weights = result.x
            for asset, weight in zip(assets, weights):
                if weight > 0.01:  # 1% threshold
                    portfolio['positions'].append({
                        'asset': asset,
                        'weight': weight,
                        'value': capital * weight
                    })
            
            portfolio['expected_return'] = np.dot(weights, expected_returns)
            portfolio['risk'] = np.sqrt(np.dot(weights, risks**2))
            portfolio['behavioral_score'] = -result.fun
        
        return portfolio
    
    def _apply_behavioral_tilts(
        self,
        portfolio: Dict[str, Any],
        profile: BehavioralProfile
    ) -> Dict[str, Any]:
        """Apply behavioral tilts to portfolio"""
        # Tilt based on behavioral factors
        positions = portfolio['positions']
        
        # Loss aversion tilt - increase defensive assets
        if profile.loss_aversion_coefficient > 2.5:
            for position in positions:
                if position['asset'] in ['bonds', 'cash']:
                    position['weight'] *= 1.1
                elif position['asset'] in ['stocks', 'commodities']:
                    position['weight'] *= 0.9
        
        # Time preference tilt - increase liquidity
        if profile.time_preference < 0.7:
            for position in positions:
                if position['asset'] == 'cash':
                    position['weight'] *= 1.2
                elif position['asset'] == 'real_estate':
                    position['weight'] *= 0.8
        
        # Renormalize weights
        total_weight = sum(p['weight'] for p in positions)
        for position in positions:
            position['weight'] /= total_weight
            position['value'] = portfolio['capital'] * position['weight']
        
        return portfolio
    
    def _setup_behavioral_monitoring(
        self,
        portfolio: Dict[str, Any],
        profile: BehavioralProfile
    ) -> Dict[str, Any]:
        """Setup behavioral monitoring for portfolio"""
        monitoring = {
            'triggers': [],
            'alerts': [],
            'review_frequency': 'monthly'
        }
        
        # Setup bias-specific triggers
        for bias in profile.detected_biases:
            if bias.bias_type == BehavioralBias.LOSS_AVERSION:
                monitoring['triggers'].append({
                    'type': 'drawdown',
                    'threshold': -0.10,
                    'action': 'loss_aversion_nudge'
                })
            elif bias.bias_type == BehavioralBias.OVERCONFIDENCE:
                monitoring['triggers'].append({
                    'type': 'concentration',
                    'threshold': 0.25,
                    'action': 'diversification_reminder'
                })
        
        # Setup performance monitoring
        monitoring['performance_tracking'] = {
            'benchmark': 'balanced_60_40',
            'evaluation_period': 'quarterly',
            'metrics': ['return', 'volatility', 'sharpe', 'max_drawdown']
        }
        
        # Setup behavioral alerts
        monitoring['behavioral_alerts'] = {
            'trading_frequency': {
                'threshold': 10,  # trades per month
                'message': 'High trading frequency detected'
            },
            'panic_indicator': {
                'threshold': 0.8,
                'message': 'Panic selling risk elevated'
            }
        }
        
        return monitoring


# Example usage
async def main():
    """Example usage of BehavioralFinanceAnalyzer"""
    
    # Initialize analyzer
    analyzer = BehavioralFinanceAnalyzer()
    
    # Sample transaction history
    transaction_history = [
        {
            'date': '2024-01-15T10:00:00',
            'type': 'buy',
            'ticker': 'AAPL',
            'return_percentage': 0.15,
            'holding_days': 45,
            'market_momentum': 0.8,
            'prior_return': 0.12
        },
        {
            'date': '2024-02-20T14:30:00',
            'type': 'sell',
            'ticker': 'GOOGL',
            'return_percentage': -0.08,
            'holding_days': 20,
            'market_momentum': -0.5
        }
    ]
    
    # Sample portfolio history
    portfolio_history = [
        {
            'date': '2024-01-01',
            'positions': [
                {'ticker': 'AAPL', 'weight': 0.30, 'recent_return': 0.12},
                {'ticker': 'GOOGL', 'weight': 0.25, 'recent_return': -0.05},
                {'ticker': 'MSFT', 'weight': 0.20, 'recent_return': 0.08}
            ],
            'equity_allocation': 0.75,
            'volatility': 0.18
        }
    ]
    
    # Analyze behavioral profile
    profile = await analyzer.analyze_behavioral_profile(
        user_id="user123",
        transaction_history=transaction_history,
        portfolio_history=portfolio_history
    )
    
    print(f"Detected {len(profile.detected_biases)} biases")
    print(f"Loss aversion coefficient: {profile.loss_aversion_coefficient:.2f}")
    print(f"Decision style: {profile.decision_style}")
    
    # Create nudges
    nudges = await analyzer.create_nudge_engine(
        user_id="user123",
        context={'portfolio_value': 100000, 'urgency': 'moderate'}
    )
    
    print(f"\nGenerated {len(nudges)} nudges:")
    for nudge in nudges:
        print(f"- {nudge.nudge_type.value}: {nudge.message}")
    
    # Create goal-based buckets
    goals = [
        {
            'name': 'Emergency Fund',
            'type': 'emergency',
            'target_amount': 20000,
            'time_horizon_months': 3,
            'priority': 1
        },
        {
            'name': 'Retirement',
            'type': 'retirement',
            'target_amount': 1000000,
            'time_horizon_months': 360,
            'priority': 2
        }
    ]
    
    buckets = await analyzer.create_goal_based_buckets(
        user_id="user123",
        goals=goals,
        total_portfolio_value=100000
    )
    
    print(f"\nCreated {len(buckets)} goal-based buckets:")
    for bucket in buckets:
        print(f"- {bucket.bucket_type.value}: {bucket.target_allocation:.1%} allocation")
    
    # Build behavioral portfolio
    portfolio = await analyzer.build_behavioral_portfolio(
        user_id="user123",
        capital=100000
    )
    
    print(f"\nBehavioral Portfolio:")
    print(f"Expected return: {portfolio['expected_return']:.1%}")
    print(f"Risk: {portfolio['risk']:.1%}")
    for position in portfolio['positions']:
        print(f"- {position['asset']}: {position['weight']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())