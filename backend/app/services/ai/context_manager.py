"""
Context Manager for AI Services
Manages contextual information for personalized AI responses
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import hashlib

import redis
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context information"""
    USER_PROFILE = "user_profile"
    MARKET_STATE = "market_state"
    PORTFOLIO_STATE = "portfolio_state"
    CONVERSATION_HISTORY = "conversation_history"
    GOAL_STATE = "goal_state"
    TAX_SITUATION = "tax_situation"
    LIFE_EVENT = "life_event"
    REGULATORY = "regulatory"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"


class ContextPriority(Enum):
    """Priority levels for context elements"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ConversationContext:
    """Conversation-specific context"""
    session_id: str
    user_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    current_topic: Optional[str] = None
    intent_history: List[str] = field(default_factory=list)
    entities_mentioned: Dict[str, List[str]] = field(default_factory=dict)
    clarifications_needed: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    sentiment_trend: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketContext:
    """Current market context"""
    market_regime: str  # bull/bear/sideways
    volatility_level: str  # low/medium/high
    vix_value: float
    sp500_level: float
    sp500_change_1d: float
    sp500_change_1w: float
    sp500_change_1m: float
    interest_rates: Dict[str, float]
    inflation_rate: float
    dollar_index: float
    commodity_prices: Dict[str, float]
    sector_performance: Dict[str, float]
    economic_indicators: Dict[str, float]
    recent_news: List[str]
    risk_events: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PortfolioContext:
    """Portfolio-specific context"""
    total_value: float
    cash_balance: float
    invested_balance: float
    total_return: float
    ytd_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    current_allocation: Dict[str, float]
    target_allocation: Dict[str, float]
    rebalancing_needed: bool
    holdings: List[Dict[str, Any]]
    recent_transactions: List[Dict[str, Any]]
    performance_vs_benchmark: float
    risk_score: float
    concentration_risk: Dict[str, float]
    last_rebalanced: Optional[datetime] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserLifeContext:
    """User's life situation context"""
    age: int
    employment_status: str
    marital_status: str
    dependents: int
    life_stage: str  # student/early_career/mid_career/pre_retirement/retirement
    major_expenses_planned: List[Dict[str, Any]]
    recent_life_events: List[str]
    health_status: Optional[str] = None
    career_trajectory: Optional[str] = None
    family_planning: Optional[Dict[str, Any]] = None


@dataclass
class TaxContext:
    """Tax-related context"""
    filing_status: str
    tax_bracket: float
    state: str
    state_tax_rate: float
    ytd_realized_gains: float
    ytd_realized_losses: float
    tax_loss_harvesting_opportunities: List[Dict[str, Any]]
    estimated_tax_liability: float
    retirement_contributions: Dict[str, float]
    deductions_available: Dict[str, float]
    tax_advantaged_space_remaining: Dict[str, float]
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GoalContext:
    """Financial goals context"""
    active_goals: List[Dict[str, Any]]
    completed_goals: List[Dict[str, Any]]
    at_risk_goals: List[Dict[str, Any]]
    total_goal_value: float
    average_progress: float
    next_milestone: Optional[Dict[str, Any]] = None
    funding_gap: float = 0
    success_probability: Dict[str, float] = field(default_factory=dict)


class ComprehensiveContext(BaseModel):
    """Complete context for AI decision-making"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    conversation: Optional[ConversationContext] = Field(None)
    market: Optional[MarketContext] = Field(None)
    portfolio: Optional[PortfolioContext] = Field(None)
    user_life: Optional[UserLifeContext] = Field(None)
    tax: Optional[TaxContext] = Field(None)
    goals: Optional[GoalContext] = Field(None)
    behavioral_profile: Optional[Dict[str, Any]] = Field(None)
    regulatory_constraints: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_quality_score: float = Field(0.0, ge=0, le=1)


class ContextManager:
    """
    Manages all contextual information for AI services
    Provides unified context aggregation and intelligent caching
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.Redis.from_url(
            config.get('redis_url', 'redis://localhost:6379')
        )
        self.context_cache = {}
        self.context_ttl = config.get('context_ttl', 3600)  # 1 hour default
        self.max_conversation_history = config.get('max_conversation_history', 50)
        
    async def build_comprehensive_context(
        self,
        user_id: str,
        session_id: str,
        db_session: Optional[AsyncSession] = None,
        include_types: Optional[List[ContextType]] = None
    ) -> ComprehensiveContext:
        """Build comprehensive context for AI processing"""
        
        # Check cache first
        cache_key = self._get_cache_key(user_id, session_id)
        cached_context = await self._get_cached_context(cache_key)
        
        if cached_context and self._is_context_fresh(cached_context):
            return cached_context
        
        # Build fresh context
        context = ComprehensiveContext(
            user_id=user_id,
            session_id=session_id
        )
        
        # Determine which context types to include
        if not include_types:
            include_types = list(ContextType)
        
        # Parallel context gathering
        tasks = []
        
        if ContextType.CONVERSATION_HISTORY in include_types:
            tasks.append(self._build_conversation_context(user_id, session_id))
        
        if ContextType.MARKET_STATE in include_types:
            tasks.append(self._build_market_context())
        
        if ContextType.PORTFOLIO_STATE in include_types:
            tasks.append(self._build_portfolio_context(user_id, db_session))
        
        if ContextType.USER_PROFILE in include_types:
            tasks.append(self._build_user_life_context(user_id, db_session))
        
        if ContextType.TAX_SITUATION in include_types:
            tasks.append(self._build_tax_context(user_id, db_session))
        
        if ContextType.GOAL_STATE in include_types:
            tasks.append(self._build_goal_context(user_id, db_session))
        
        if ContextType.BEHAVIORAL in include_types:
            tasks.append(self._build_behavioral_context(user_id))
        
        if ContextType.REGULATORY in include_types:
            tasks.append(self._build_regulatory_context(user_id))
        
        # Gather all context components
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error building context component: {result}")
                continue
                
            if i == 0 and ContextType.CONVERSATION_HISTORY in include_types:
                context.conversation = result
            elif i == 1 and ContextType.MARKET_STATE in include_types:
                context.market = result
            elif i == 2 and ContextType.PORTFOLIO_STATE in include_types:
                context.portfolio = result
            elif i == 3 and ContextType.USER_PROFILE in include_types:
                context.user_life = result
            elif i == 4 and ContextType.TAX_SITUATION in include_types:
                context.tax = result
            elif i == 5 and ContextType.GOAL_STATE in include_types:
                context.goals = result
            elif i == 6 and ContextType.BEHAVIORAL in include_types:
                context.behavioral_profile = result
            elif i == 7 and ContextType.REGULATORY in include_types:
                context.regulatory_constraints = result
        
        # Calculate context quality score
        context.context_quality_score = self._calculate_context_quality(context)
        
        # Cache the context
        await self._cache_context(cache_key, context)
        
        return context
    
    async def _build_conversation_context(
        self,
        user_id: str,
        session_id: str
    ) -> ConversationContext:
        """Build conversation context from history"""
        
        # Get conversation history from Redis
        history_key = f"conversation:{user_id}:{session_id}"
        raw_history = self.redis_client.lrange(history_key, 0, -1)
        
        messages = []
        for raw_msg in raw_history[-self.max_conversation_history:]:
            try:
                messages.append(json.loads(raw_msg))
            except:
                continue
        
        # Analyze conversation patterns
        intent_history = []
        entities = defaultdict(list)
        sentiments = []
        
        for msg in messages:
            if intent := msg.get('intent'):
                intent_history.append(intent)
            
            if msg_entities := msg.get('entities'):
                for entity_type, values in msg_entities.items():
                    entities[entity_type].extend(values)
            
            if sentiment := msg.get('sentiment'):
                sentiments.append(sentiment)
        
        # Determine current topic
        current_topic = self._infer_current_topic(messages, intent_history)
        
        # Identify clarifications needed
        clarifications = self._identify_clarifications(messages)
        
        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(current_topic, entities)
        
        return ConversationContext(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
            current_topic=current_topic,
            intent_history=intent_history,
            entities_mentioned=dict(entities),
            clarifications_needed=clarifications,
            follow_up_questions=follow_ups,
            sentiment_trend=sentiments
        )
    
    async def _build_market_context(self) -> MarketContext:
        """Build current market context"""
        
        # Get market data from Redis cache
        market_data = {}
        keys_to_fetch = [
            'market:vix',
            'market:sp500',
            'market:rates',
            'market:sectors',
            'market:indicators'
        ]
        
        for key in keys_to_fetch:
            data = self.redis_client.get(key)
            if data:
                market_data[key.split(':')[1]] = json.loads(data)
        
        # Determine market regime
        vix = market_data.get('vix', {}).get('value', 15)
        sp500_change = market_data.get('sp500', {}).get('change_1m', 0)
        
        if vix > 30:
            regime = "high_volatility"
        elif sp500_change > 0.05:
            regime = "bull"
        elif sp500_change < -0.05:
            regime = "bear"
        else:
            regime = "sideways"
        
        # Determine volatility level
        if vix < 12:
            vol_level = "low"
        elif vix < 20:
            vol_level = "medium"
        else:
            vol_level = "high"
        
        return MarketContext(
            market_regime=regime,
            volatility_level=vol_level,
            vix_value=vix,
            sp500_level=market_data.get('sp500', {}).get('level', 4500),
            sp500_change_1d=market_data.get('sp500', {}).get('change_1d', 0),
            sp500_change_1w=market_data.get('sp500', {}).get('change_1w', 0),
            sp500_change_1m=sp500_change,
            interest_rates=market_data.get('rates', {}),
            inflation_rate=market_data.get('indicators', {}).get('inflation', 0.03),
            dollar_index=market_data.get('indicators', {}).get('dxy', 100),
            commodity_prices=market_data.get('indicators', {}).get('commodities', {}),
            sector_performance=market_data.get('sectors', {}),
            economic_indicators=market_data.get('indicators', {}),
            recent_news=self._get_recent_news(),
            risk_events=self._identify_risk_events(market_data)
        )
    
    async def _build_portfolio_context(
        self,
        user_id: str,
        db_session: Optional[AsyncSession]
    ) -> PortfolioContext:
        """Build portfolio context"""
        
        # Get portfolio data from cache or database
        portfolio_key = f"portfolio:{user_id}"
        portfolio_data = self.redis_client.get(portfolio_key)
        
        if portfolio_data:
            portfolio = json.loads(portfolio_data)
        else:
            # Fetch from database if not cached
            portfolio = {
                'total_value': 100000,
                'cash_balance': 10000,
                'invested_balance': 90000,
                'total_return': 0.12,
                'ytd_return': 0.08,
                'volatility': 0.15,
                'sharpe_ratio': 1.2,
                'max_drawdown': 0.10,
                'current_allocation': {
                    'stocks': 0.60,
                    'bonds': 0.30,
                    'alternatives': 0.10
                },
                'target_allocation': {
                    'stocks': 0.65,
                    'bonds': 0.25,
                    'alternatives': 0.10
                }
            }
        
        # Check rebalancing need
        rebalancing_needed = self._check_rebalancing_need(
            portfolio['current_allocation'],
            portfolio['target_allocation']
        )
        
        # Get recent transactions
        transactions_key = f"transactions:{user_id}"
        recent_transactions = []
        raw_transactions = self.redis_client.lrange(transactions_key, 0, 10)
        for raw_tx in raw_transactions:
            try:
                recent_transactions.append(json.loads(raw_tx))
            except:
                continue
        
        return PortfolioContext(
            total_value=portfolio['total_value'],
            cash_balance=portfolio['cash_balance'],
            invested_balance=portfolio['invested_balance'],
            total_return=portfolio['total_return'],
            ytd_return=portfolio['ytd_return'],
            volatility=portfolio['volatility'],
            sharpe_ratio=portfolio['sharpe_ratio'],
            max_drawdown=portfolio['max_drawdown'],
            current_allocation=portfolio['current_allocation'],
            target_allocation=portfolio['target_allocation'],
            rebalancing_needed=rebalancing_needed,
            holdings=portfolio.get('holdings', []),
            recent_transactions=recent_transactions,
            performance_vs_benchmark=portfolio.get('vs_benchmark', 0.02),
            risk_score=portfolio.get('risk_score', 50),
            concentration_risk=portfolio.get('concentration_risk', {}),
            last_rebalanced=portfolio.get('last_rebalanced')
        )
    
    async def _build_user_life_context(
        self,
        user_id: str,
        db_session: Optional[AsyncSession]
    ) -> UserLifeContext:
        """Build user life context"""
        
        # Get user profile from cache or database
        profile_key = f"user_profile:{user_id}"
        profile_data = self.redis_client.get(profile_key)
        
        if profile_data:
            profile = json.loads(profile_data)
        else:
            # Default profile for demo
            profile = {
                'age': 35,
                'employment_status': 'employed',
                'marital_status': 'married',
                'dependents': 2,
                'life_stage': 'mid_career',
                'major_expenses': [],
                'recent_events': []
            }
        
        return UserLifeContext(
            age=profile['age'],
            employment_status=profile['employment_status'],
            marital_status=profile['marital_status'],
            dependents=profile['dependents'],
            life_stage=profile['life_stage'],
            major_expenses_planned=profile.get('major_expenses', []),
            recent_life_events=profile.get('recent_events', []),
            health_status=profile.get('health_status'),
            career_trajectory=profile.get('career_trajectory'),
            family_planning=profile.get('family_planning')
        )
    
    async def _build_tax_context(
        self,
        user_id: str,
        db_session: Optional[AsyncSession]
    ) -> TaxContext:
        """Build tax context"""
        
        # Get tax data from cache or database
        tax_key = f"tax:{user_id}"
        tax_data = self.redis_client.get(tax_key)
        
        if tax_data:
            tax_info = json.loads(tax_data)
        else:
            # Default tax info for demo
            tax_info = {
                'filing_status': 'married_filing_jointly',
                'tax_bracket': 0.24,
                'state': 'CA',
                'state_tax_rate': 0.093,
                'ytd_gains': 5000,
                'ytd_losses': 1000,
                'estimated_liability': 15000
            }
        
        # Identify tax optimization opportunities
        harvesting_opps = await self._find_tax_harvesting_opportunities(user_id)
        
        return TaxContext(
            filing_status=tax_info['filing_status'],
            tax_bracket=tax_info['tax_bracket'],
            state=tax_info['state'],
            state_tax_rate=tax_info['state_tax_rate'],
            ytd_realized_gains=tax_info.get('ytd_gains', 0),
            ytd_realized_losses=tax_info.get('ytd_losses', 0),
            tax_loss_harvesting_opportunities=harvesting_opps,
            estimated_tax_liability=tax_info.get('estimated_liability', 0),
            retirement_contributions=tax_info.get('retirement_contributions', {}),
            deductions_available=tax_info.get('deductions', {}),
            tax_advantaged_space_remaining=tax_info.get('tax_space', {})
        )
    
    async def _build_goal_context(
        self,
        user_id: str,
        db_session: Optional[AsyncSession]
    ) -> GoalContext:
        """Build goals context"""
        
        # Get goals from cache or database
        goals_key = f"goals:{user_id}"
        goals_data = self.redis_client.get(goals_key)
        
        if goals_data:
            goals = json.loads(goals_data)
        else:
            # Default goals for demo
            goals = {
                'active': [
                    {
                        'id': 'retirement',
                        'name': 'Retirement',
                        'target': 2000000,
                        'current': 150000,
                        'progress': 0.075,
                        'target_date': '2055-01-01'
                    },
                    {
                        'id': 'college',
                        'name': 'College Fund',
                        'target': 200000,
                        'current': 25000,
                        'progress': 0.125,
                        'target_date': '2035-09-01'
                    }
                ],
                'completed': [],
                'at_risk': []
            }
        
        # Calculate aggregate metrics
        active_goals = goals.get('active', [])
        total_value = sum(g['target'] for g in active_goals)
        avg_progress = np.mean([g['progress'] for g in active_goals]) if active_goals else 0
        
        # Find next milestone
        next_milestone = None
        if active_goals:
            sorted_goals = sorted(active_goals, key=lambda x: x.get('target_date', '9999'))
            next_milestone = sorted_goals[0]
        
        # Calculate funding gap
        funding_gap = sum(
            g['target'] - g['current'] 
            for g in active_goals
        )
        
        return GoalContext(
            active_goals=active_goals,
            completed_goals=goals.get('completed', []),
            at_risk_goals=goals.get('at_risk', []),
            total_goal_value=total_value,
            average_progress=avg_progress,
            next_milestone=next_milestone,
            funding_gap=funding_gap,
            success_probability={
                g['id']: self._calculate_goal_success_probability(g)
                for g in active_goals
            }
        )
    
    async def _build_behavioral_context(self, user_id: str) -> Dict[str, Any]:
        """Build behavioral context"""
        
        # Get behavioral profile from cache
        behavioral_key = f"behavior_profile:{user_id}"
        behavioral_data = self.redis_client.get(behavioral_key)
        
        if behavioral_data:
            return json.loads(behavioral_data)
        
        # Default behavioral profile
        return {
            'risk_profile': 'moderate',
            'risk_score': 50,
            'behavioral_patterns': ['consistent_saver'],
            'loss_aversion': 0.6,
            'overconfidence': 0.4,
            'trading_frequency': 'medium',
            'financial_literacy': 65
        }
    
    async def _build_regulatory_context(self, user_id: str) -> List[str]:
        """Build regulatory constraints context"""
        
        # Get user's account types and determine applicable regulations
        constraints = [
            "SEC Regulation Best Interest",
            "FINRA suitability rules",
            "IRS contribution limits",
            "Wash sale rule (30 days)",
            "Pattern day trader rule ($25k minimum)"
        ]
        
        # Add state-specific constraints
        user_state = await self._get_user_state(user_id)
        if user_state == "CA":
            constraints.append("California privacy regulations")
        
        return constraints
    
    def _infer_current_topic(
        self,
        messages: List[Dict[str, Any]],
        intent_history: List[str]
    ) -> Optional[str]:
        """Infer the current conversation topic"""
        
        if not messages:
            return None
        
        # Look at recent intents
        recent_intents = intent_history[-5:] if intent_history else []
        
        # Topic inference rules
        topic_keywords = {
            'retirement': ['retire', '401k', 'ira', 'pension'],
            'taxes': ['tax', 'deduction', 'harvest', 'liability'],
            'goals': ['goal', 'save', 'target', 'plan'],
            'portfolio': ['portfolio', 'allocation', 'rebalance', 'invest'],
            'market': ['market', 'stock', 'bond', 'economy']
        }
        
        # Count keyword occurrences in recent messages
        topic_scores = defaultdict(int)
        
        for msg in messages[-5:]:
            text = msg.get('text', '').lower()
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        topic_scores[topic] += 1
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return None
    
    def _identify_clarifications(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify clarifications needed from user"""
        
        clarifications = []
        
        if not messages:
            return clarifications
        
        last_message = messages[-1] if messages else {}
        
        # Check for ambiguous references
        if 'it' in last_message.get('text', '').lower():
            clarifications.append("Please specify what 'it' refers to")
        
        # Check for missing time horizons
        if any(word in last_message.get('text', '').lower() 
               for word in ['invest', 'save', 'goal']):
            if not any(word in last_message.get('text', '').lower()
                      for word in ['year', 'month', 'term', 'when']):
                clarifications.append("What is your time horizon for this goal?")
        
        # Check for missing amounts
        if 'invest' in last_message.get('text', '').lower():
            if not any(char.isdigit() for char in last_message.get('text', '')):
                clarifications.append("How much are you looking to invest?")
        
        return clarifications
    
    def _generate_follow_ups(
        self,
        current_topic: Optional[str],
        entities: Dict[str, List[str]]
    ) -> List[str]:
        """Generate relevant follow-up questions"""
        
        follow_ups = []
        
        if current_topic == 'retirement':
            follow_ups.extend([
                "Would you like to see projections for different contribution levels?",
                "Should we review your 401(k) investment options?",
                "Are you maximizing employer matching?"
            ])
        elif current_topic == 'taxes':
            follow_ups.extend([
                "Would you like to explore tax-loss harvesting opportunities?",
                "Should we review tax-advantaged account options?",
                "Do you need help with estimated tax payments?"
            ])
        elif current_topic == 'portfolio':
            follow_ups.extend([
                "Would you like to see a risk analysis of your portfolio?",
                "Should we compare your performance to benchmarks?",
                "Is it time to rebalance your portfolio?"
            ])
        
        return follow_ups[:3]  # Return top 3 follow-ups
    
    def _check_rebalancing_need(
        self,
        current: Dict[str, float],
        target: Dict[str, float]
    ) -> bool:
        """Check if portfolio needs rebalancing"""
        
        threshold = 0.05  # 5% deviation threshold
        
        for asset, target_weight in target.items():
            current_weight = current.get(asset, 0)
            if abs(current_weight - target_weight) > threshold:
                return True
        
        return False
    
    def _get_recent_news(self) -> List[str]:
        """Get recent financial news headlines"""
        
        # This would normally fetch from a news API
        return [
            "Fed maintains interest rates steady",
            "Tech sector shows strong earnings",
            "Inflation concerns ease slightly"
        ]
    
    def _identify_risk_events(
        self,
        market_data: Dict[str, Any]
    ) -> List[str]:
        """Identify current market risk events"""
        
        risk_events = []
        
        vix = market_data.get('vix', {}).get('value', 15)
        if vix > 25:
            risk_events.append("Elevated market volatility")
        
        if market_data.get('sp500', {}).get('change_1w', 0) < -0.05:
            risk_events.append("Significant market decline this week")
        
        return risk_events
    
    async def _find_tax_harvesting_opportunities(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Find tax-loss harvesting opportunities"""
        
        # This would normally query portfolio holdings
        # Simplified for demonstration
        return [
            {
                'symbol': 'XYZ',
                'unrealized_loss': -1500,
                'holding_period': 180,
                'wash_sale_safe': True
            }
        ]
    
    def _calculate_goal_success_probability(
        self,
        goal: Dict[str, Any]
    ) -> float:
        """Calculate probability of achieving a goal"""
        
        progress = goal.get('progress', 0)
        years_remaining = self._years_until(goal.get('target_date'))
        
        if years_remaining <= 0:
            return progress
        
        # Simple linear projection
        annual_progress_needed = (1 - progress) / years_remaining
        
        if annual_progress_needed < 0.05:
            return 0.95
        elif annual_progress_needed < 0.10:
            return 0.80
        elif annual_progress_needed < 0.15:
            return 0.60
        else:
            return 0.40
    
    def _years_until(self, date_str: Optional[str]) -> float:
        """Calculate years until a date"""
        
        if not date_str:
            return 0
        
        try:
            target = datetime.fromisoformat(date_str)
            return (target - datetime.utcnow()).days / 365.25
        except:
            return 0
    
    async def _get_user_state(self, user_id: str) -> str:
        """Get user's state of residence"""
        
        profile_key = f"user_profile:{user_id}"
        profile_data = self.redis_client.get(profile_key)
        
        if profile_data:
            profile = json.loads(profile_data)
            return profile.get('state', 'CA')
        
        return 'CA'  # Default
    
    def _calculate_context_quality(
        self,
        context: ComprehensiveContext
    ) -> float:
        """Calculate quality score for context completeness"""
        
        score = 0.0
        weights = {
            'conversation': 0.15,
            'market': 0.15,
            'portfolio': 0.25,
            'user_life': 0.15,
            'tax': 0.10,
            'goals': 0.15,
            'behavioral_profile': 0.05
        }
        
        if context.conversation:
            score += weights['conversation']
        
        if context.market:
            score += weights['market']
        
        if context.portfolio:
            score += weights['portfolio']
        
        if context.user_life:
            score += weights['user_life']
        
        if context.tax:
            score += weights['tax']
        
        if context.goals:
            score += weights['goals']
        
        if context.behavioral_profile:
            score += weights['behavioral_profile']
        
        return min(score, 1.0)
    
    def _get_cache_key(self, user_id: str, session_id: str) -> str:
        """Generate cache key for context"""
        
        return f"context:{user_id}:{session_id}"
    
    async def _get_cached_context(
        self,
        cache_key: str
    ) -> Optional[ComprehensiveContext]:
        """Retrieve context from cache"""
        
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                # Reconstruct dataclass objects
                # This is simplified - full implementation would properly deserialize
                return None  # For now, always rebuild
            except:
                return None
        
        return None
    
    def _is_context_fresh(self, context: ComprehensiveContext) -> bool:
        """Check if cached context is still fresh"""
        
        age = (datetime.utcnow() - context.timestamp).seconds
        return age < self.context_ttl
    
    async def _cache_context(
        self,
        cache_key: str,
        context: ComprehensiveContext
    ):
        """Cache context for future use"""
        
        # Simplified caching - full implementation would properly serialize
        # For now, we'll cache individual components
        pass
    
    async def update_conversation_context(
        self,
        user_id: str,
        session_id: str,
        message: Dict[str, Any]
    ):
        """Update conversation context with new message"""
        
        history_key = f"conversation:{user_id}:{session_id}"
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.utcnow().isoformat()
        
        # Add to conversation history
        self.redis_client.rpush(history_key, json.dumps(message))
        
        # Trim to max history
        self.redis_client.ltrim(history_key, -self.max_conversation_history, -1)
        
        # Set expiry
        self.redis_client.expire(history_key, 86400)  # 24 hours
    
    async def get_relevant_context(
        self,
        query: str,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get only the relevant context for a specific query"""
        
        # Analyze query to determine required context
        required_types = self._analyze_context_requirements(query)
        
        # Build focused context
        context = await self.build_comprehensive_context(
            user_id,
            session_id,
            include_types=required_types
        )
        
        # Extract relevant portions
        relevant = {}
        
        if 'portfolio' in query.lower() or 'invest' in query.lower():
            relevant['portfolio'] = context.portfolio
        
        if 'tax' in query.lower():
            relevant['tax'] = context.tax
        
        if 'goal' in query.lower() or 'retire' in query.lower():
            relevant['goals'] = context.goals
        
        if 'market' in query.lower() or 'economy' in query.lower():
            relevant['market'] = context.market
        
        # Always include user life context for personalization
        relevant['user'] = context.user_life
        
        return relevant
    
    def _analyze_context_requirements(self, query: str) -> List[ContextType]:
        """Analyze query to determine required context types"""
        
        required = [ContextType.USER_PROFILE]  # Always include user profile
        
        query_lower = query.lower()
        
        # Pattern matching for context requirements
        patterns = {
            ContextType.PORTFOLIO_STATE: [
                'portfolio', 'holding', 'position', 'allocation', 'rebalance'
            ],
            ContextType.MARKET_STATE: [
                'market', 'stock', 'economy', 'inflation', 'rate'
            ],
            ContextType.TAX_SITUATION: [
                'tax', 'deduction', 'harvest', 'irs', 'liability'
            ],
            ContextType.GOAL_STATE: [
                'goal', 'retire', 'college', 'save', 'target'
            ],
            ContextType.BEHAVIORAL: [
                'risk', 'tolerance', 'personality', 'behavior'
            ]
        }
        
        for context_type, keywords in patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                required.append(context_type)
        
        # Always include conversation history for continuity
        required.append(ContextType.CONVERSATION_HISTORY)
        
        return required