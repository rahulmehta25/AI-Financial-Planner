"""
Enhanced Conversation Manager for Multi-Turn Financial Advisory Conversations
Handles context management, conversation flow, and memory across sessions
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import hashlib
import uuid

import redis
from pydantic import BaseModel, Field
import numpy as np
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .context_management import (
    ContextManager, 
    ComprehensiveContext,
    ConversationContext
)

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """States of a conversation"""
    GREETING = "greeting"
    GATHERING_INFO = "gathering_info"
    ANALYZING = "analyzing"
    PROVIDING_ADVICE = "providing_advice"
    CLARIFYING = "clarifying"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"

class Intent(Enum):
    """User intent types"""
    QUESTION = "question"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"
    GREETING = "greeting"
    FAREWELL = "farewell"
    REQUEST_INFO = "request_info"
    PROVIDE_INFO = "provide_info"
    FEEDBACK = "feedback"

@dataclass
class ConversationTurn:
    """Single turn in conversation"""
    turn_id: str
    user_message: str
    ai_response: str
    intent: Intent
    entities: Dict[str, Any]
    sentiment: float
    confidence: float
    timestamp: datetime
    context_snapshot: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None

@dataclass
class ConversationSession:
    """Complete conversation session"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    state: ConversationState = ConversationState.GREETING
    turns: List[ConversationTurn] = field(default_factory=list)
    topic_history: List[str] = field(default_factory=list)
    goals_discussed: List[str] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    satisfaction_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConversationMemory:
    """Manages conversation memory and history"""
    
    def __init__(self, redis_client: redis.Redis, max_history: int = 50):
        self.redis_client = redis_client
        self.max_history = max_history
        self.memory_ttl = 86400  # 24 hours
        
    async def store_turn(
        self,
        session_id: str,
        turn: ConversationTurn
    ):
        """Store a conversation turn"""
        
        key = f"conversation:turn:{session_id}:{turn.turn_id}"
        turn_data = {
            'turn_id': turn.turn_id,
            'user_message': turn.user_message,
            'ai_response': turn.ai_response,
            'intent': turn.intent.value,
            'entities': json.dumps(turn.entities),
            'sentiment': turn.sentiment,
            'confidence': turn.confidence,
            'timestamp': turn.timestamp.isoformat(),
            'context_snapshot': json.dumps(turn.context_snapshot) if turn.context_snapshot else None,
            'feedback': turn.feedback
        }
        
        self.redis_client.hset(key, mapping=turn_data)
        self.redis_client.expire(key, self.memory_ttl)
        
        # Add to session history
        history_key = f"conversation:history:{session_id}"
        self.redis_client.rpush(history_key, turn.turn_id)
        self.redis_client.ltrim(history_key, -self.max_history, -1)
        self.redis_client.expire(history_key, self.memory_ttl)
    
    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """Retrieve session history"""
        
        history_key = f"conversation:history:{session_id}"
        turn_ids = self.redis_client.lrange(history_key, 0, limit or -1)
        
        turns = []
        for turn_id in turn_ids:
            turn_key = f"conversation:turn:{session_id}:{turn_id.decode()}"
            turn_data = self.redis_client.hgetall(turn_key)
            
            if turn_data:
                turns.append(ConversationTurn(
                    turn_id=turn_data[b'turn_id'].decode(),
                    user_message=turn_data[b'user_message'].decode(),
                    ai_response=turn_data[b'ai_response'].decode(),
                    intent=Intent(turn_data[b'intent'].decode()),
                    entities=json.loads(turn_data[b'entities'].decode()),
                    sentiment=float(turn_data[b'sentiment']),
                    confidence=float(turn_data[b'confidence']),
                    timestamp=datetime.fromisoformat(turn_data[b'timestamp'].decode()),
                    context_snapshot=json.loads(turn_data[b'context_snapshot'].decode()) 
                        if turn_data.get(b'context_snapshot') else None,
                    feedback=turn_data.get(b'feedback', b'').decode() or None
                ))
        
        return turns
    
    async def get_user_history(
        self,
        user_id: str,
        days: int = 30
    ) -> List[ConversationSession]:
        """Get user's conversation history"""
        
        sessions_key = f"user:sessions:{user_id}"
        session_ids = self.redis_client.smembers(sessions_key)
        
        sessions = []
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        for session_id in session_ids:
            session_key = f"conversation:session:{session_id.decode()}"
            session_data = self.redis_client.hgetall(session_key)
            
            if session_data:
                start_time = datetime.fromisoformat(session_data[b'start_time'].decode())
                if start_time > cutoff_date:
                    sessions.append(await self._load_session(session_id.decode()))
        
        return sorted(sessions, key=lambda x: x.start_time, reverse=True)
    
    async def _load_session(self, session_id: str) -> ConversationSession:
        """Load complete session from Redis"""
        
        session_key = f"conversation:session:{session_id}"
        session_data = self.redis_client.hgetall(session_key)
        
        if not session_data:
            return None
        
        turns = await self.get_session_history(session_id)
        
        return ConversationSession(
            session_id=session_id,
            user_id=session_data[b'user_id'].decode(),
            start_time=datetime.fromisoformat(session_data[b'start_time'].decode()),
            end_time=datetime.fromisoformat(session_data[b'end_time'].decode()) 
                if session_data.get(b'end_time') else None,
            state=ConversationState(session_data[b'state'].decode()),
            turns=turns,
            topic_history=json.loads(session_data.get(b'topic_history', b'[]').decode()),
            goals_discussed=json.loads(session_data.get(b'goals_discussed', b'[]').decode()),
            action_items=json.loads(session_data.get(b'action_items', b'[]').decode()),
            satisfaction_score=float(session_data[b'satisfaction_score']) 
                if session_data.get(b'satisfaction_score') else None,
            metadata=json.loads(session_data.get(b'metadata', b'{}').decode())
        )

class ConversationFlow:
    """Manages conversation flow and state transitions"""
    
    def __init__(self):
        self.state_transitions = {
            ConversationState.GREETING: [
                ConversationState.GATHERING_INFO,
                ConversationState.ANALYZING
            ],
            ConversationState.GATHERING_INFO: [
                ConversationState.CLARIFYING,
                ConversationState.ANALYZING,
                ConversationState.PROVIDING_ADVICE
            ],
            ConversationState.ANALYZING: [
                ConversationState.PROVIDING_ADVICE,
                ConversationState.CLARIFYING
            ],
            ConversationState.PROVIDING_ADVICE: [
                ConversationState.FOLLOW_UP,
                ConversationState.CLARIFYING,
                ConversationState.CLOSING
            ],
            ConversationState.CLARIFYING: [
                ConversationState.GATHERING_INFO,
                ConversationState.ANALYZING,
                ConversationState.PROVIDING_ADVICE
            ],
            ConversationState.FOLLOW_UP: [
                ConversationState.PROVIDING_ADVICE,
                ConversationState.CLOSING
            ],
            ConversationState.CLOSING: []
        }
    
    def get_next_state(
        self,
        current_state: ConversationState,
        intent: Intent,
        context: Dict[str, Any]
    ) -> ConversationState:
        """Determine next conversation state"""
        
        # Handle special intents
        if intent == Intent.FAREWELL:
            return ConversationState.CLOSING
        
        if intent == Intent.GREETING and current_state != ConversationState.GREETING:
            return current_state  # Stay in current state
        
        # State-specific transitions
        if current_state == ConversationState.GREETING:
            if intent in [Intent.QUESTION, Intent.REQUEST_INFO]:
                return ConversationState.GATHERING_INFO
        
        elif current_state == ConversationState.GATHERING_INFO:
            if self._has_enough_info(context):
                return ConversationState.ANALYZING
            elif intent == Intent.CLARIFICATION:
                return ConversationState.CLARIFYING
        
        elif current_state == ConversationState.ANALYZING:
            return ConversationState.PROVIDING_ADVICE
        
        elif current_state == ConversationState.PROVIDING_ADVICE:
            if intent == Intent.QUESTION:
                return ConversationState.FOLLOW_UP
            elif intent in [Intent.CONFIRMATION, Intent.FEEDBACK]:
                return ConversationState.CLOSING
            elif intent == Intent.CLARIFICATION:
                return ConversationState.CLARIFYING
        
        elif current_state == ConversationState.CLARIFYING:
            if intent == Intent.PROVIDE_INFO:
                if self._has_enough_info(context):
                    return ConversationState.ANALYZING
                else:
                    return ConversationState.GATHERING_INFO
        
        elif current_state == ConversationState.FOLLOW_UP:
            if intent in [Intent.CONFIRMATION, Intent.FEEDBACK]:
                return ConversationState.CLOSING
            else:
                return ConversationState.PROVIDING_ADVICE
        
        # Default: stay in current state
        return current_state
    
    def _has_enough_info(self, context: Dict[str, Any]) -> bool:
        """Check if we have enough information to proceed"""
        
        required_fields = ['user_profile', 'financial_goals', 'risk_tolerance']
        return all(context.get(field) for field in required_fields)
    
    def generate_state_prompt(self, state: ConversationState) -> str:
        """Generate appropriate prompt for current state"""
        
        prompts = {
            ConversationState.GREETING: "Hello! I'm your AI financial advisor. How can I help you today?",
            ConversationState.GATHERING_INFO: "To provide the best advice, I need to understand your situation better.",
            ConversationState.ANALYZING: "Let me analyze your financial situation...",
            ConversationState.PROVIDING_ADVICE: "Based on your situation, here's my recommendation:",
            ConversationState.CLARIFYING: "I need to clarify a few things:",
            ConversationState.FOLLOW_UP: "Is there anything else you'd like to know?",
            ConversationState.CLOSING: "Thank you for the conversation. Feel free to return anytime!"
        }
        
        return prompts.get(state, "How can I assist you?")

class ConversationManager:
    """
    Main conversation manager orchestrating multi-turn conversations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.redis_client = redis.Redis.from_url(
            config.get('redis_url', 'redis://localhost:6379')
        )
        
        self.context_manager = ContextManager(config)
        self.memory = ConversationMemory(self.redis_client)
        self.flow_manager = ConversationFlow()
        
        # Conversation settings
        self.max_turns = config.get('max_turns', 20)
        self.session_timeout = config.get('session_timeout', 1800)  # 30 minutes
        
        # Active sessions
        self.active_sessions = {}
    
    async def start_session(
        self,
        user_id: str,
        initial_message: Optional[str] = None
    ) -> ConversationSession:
        """Start a new conversation session"""
        
        session_id = str(uuid.uuid4())
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            state=ConversationState.GREETING
        )
        
        # Store in Redis
        session_key = f"conversation:session:{session_id}"
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'start_time': session.start_time.isoformat(),
            'state': session.state.value
        }
        
        self.redis_client.hset(session_key, mapping=session_data)
        self.redis_client.expire(session_key, self.session_timeout)
        
        # Track user sessions
        user_sessions_key = f"user:sessions:{user_id}"
        self.redis_client.sadd(user_sessions_key, session_id)
        
        # Cache in memory
        self.active_sessions[session_id] = session
        
        # Process initial message if provided
        if initial_message:
            await self.process_message(session_id, initial_message)
        
        return session
    
    async def process_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Process a user message in the conversation"""
        
        # Get or load session
        session = await self._get_session(session_id)
        if not session:
            return {
                'error': 'Session not found or expired',
                'session_id': session_id
            }
        
        # Check turn limit
        if len(session.turns) >= self.max_turns:
            return {
                'error': 'Maximum conversation length reached',
                'suggestion': 'Please start a new conversation'
            }
        
        # Analyze message
        intent = await self._detect_intent(message)
        entities = await self._extract_entities(message)
        sentiment = await self._analyze_sentiment(message)
        
        # Build context
        context = await self.context_manager.build_comprehensive_context(
            user_id=session.user_id,
            session_id=session_id
        )
        
        # Update conversation context
        await self.context_manager.update_conversation_context(
            user_id=session.user_id,
            session_id=session_id,
            message={
                'text': message,
                'intent': intent.value,
                'entities': entities,
                'sentiment': sentiment,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Determine next state
        next_state = self.flow_manager.get_next_state(
            session.state,
            intent,
            asdict(context)
        )
        
        # Generate response based on state
        response = await self._generate_response(
            session=session,
            message=message,
            intent=intent,
            entities=entities,
            context=context,
            next_state=next_state
        )
        
        # Create conversation turn
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            user_message=message,
            ai_response=response['text'],
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            confidence=response.get('confidence', 0.8),
            timestamp=datetime.utcnow(),
            context_snapshot={
                'state': next_state.value,
                'topics': session.topic_history[-3:] if session.topic_history else []
            }
        )
        
        # Store turn
        await self.memory.store_turn(session_id, turn)
        
        # Update session
        session.turns.append(turn)
        session.state = next_state
        
        # Update topics if new topic detected
        if topic := entities.get('topic'):
            if topic not in session.topic_history:
                session.topic_history.append(topic)
        
        # Extract action items if any
        if action_items := response.get('action_items'):
            session.action_items.extend(action_items)
        
        # Update session in Redis
        await self._update_session(session)
        
        return {
            'session_id': session_id,
            'response': response['text'],
            'state': next_state.value,
            'confidence': response.get('confidence', 0.8),
            'suggestions': response.get('suggestions', []),
            'visualizations': response.get('visualizations', []),
            'action_items': response.get('action_items', []),
            'turn_number': len(session.turns),
            'max_turns': self.max_turns
        }
    
    async def end_session(
        self,
        session_id: str,
        satisfaction_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """End a conversation session"""
        
        session = await self._get_session(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        session.end_time = datetime.utcnow()
        session.satisfaction_score = satisfaction_score
        
        # Generate session summary
        summary = await self._generate_session_summary(session)
        
        # Store final session state
        await self._update_session(session)
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return {
            'session_id': session_id,
            'duration': (session.end_time - session.start_time).seconds,
            'turns': len(session.turns),
            'topics_discussed': session.topic_history,
            'action_items': session.action_items,
            'summary': summary,
            'satisfaction_score': satisfaction_score
        }
    
    async def _get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get session from cache or Redis"""
        
        # Check memory cache
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Load from Redis
        session = await self.memory._load_session(session_id)
        if session:
            self.active_sessions[session_id] = session
        
        return session
    
    async def _update_session(self, session: ConversationSession):
        """Update session in Redis"""
        
        session_key = f"conversation:session:{session.session_id}"
        session_data = {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else '',
            'state': session.state.value,
            'topic_history': json.dumps(session.topic_history),
            'goals_discussed': json.dumps(session.goals_discussed),
            'action_items': json.dumps(session.action_items),
            'satisfaction_score': str(session.satisfaction_score) if session.satisfaction_score else '',
            'metadata': json.dumps(session.metadata)
        }
        
        self.redis_client.hset(session_key, mapping=session_data)
        self.redis_client.expire(session_key, self.session_timeout)
    
    async def _detect_intent(self, message: str) -> Intent:
        """Detect user intent from message"""
        
        message_lower = message.lower()
        
        # Simple pattern matching (could be replaced with ML model)
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning']):
            return Intent.GREETING
        
        elif any(word in message_lower for word in ['bye', 'goodbye', 'thanks', 'thank you']):
            return Intent.FAREWELL
        
        elif '?' in message:
            if any(word in message_lower for word in ['what', 'how', 'why', 'when', 'where']):
                return Intent.QUESTION
            else:
                return Intent.CLARIFICATION
        
        elif any(word in message_lower for word in ['yes', 'correct', 'right', 'exactly']):
            return Intent.CONFIRMATION
        
        elif any(word in message_lower for word in ['no', 'wrong', 'incorrect']):
            return Intent.REJECTION
        
        elif any(word in message_lower for word in ['tell me', 'show me', 'explain']):
            return Intent.REQUEST_INFO
        
        elif any(word in message_lower for word in ['my', 'i have', 'i am', 'i want']):
            return Intent.PROVIDE_INFO
        
        elif any(word in message_lower for word in ['good', 'bad', 'great', 'terrible']):
            return Intent.FEEDBACK
        
        return Intent.QUESTION
    
    async def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message"""
        
        entities = {}
        message_lower = message.lower()
        
        # Extract monetary amounts
        import re
        money_pattern = r'\$[\d,]+\.?\d*[kmb]?'
        if money_match := re.search(money_pattern, message_lower):
            entities['amount'] = money_match.group()
        
        # Extract percentages
        percent_pattern = r'\d+\.?\d*%'
        if percent_match := re.search(percent_pattern, message):
            entities['percentage'] = percent_match.group()
        
        # Extract time periods
        time_keywords = {
            'years': ['year', 'years', 'annual', 'annually'],
            'months': ['month', 'months', 'monthly'],
            'weeks': ['week', 'weeks', 'weekly']
        }
        
        for unit, keywords in time_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Try to extract number before keyword
                    pattern = rf'(\d+)\s*{keyword}'
                    if match := re.search(pattern, message_lower):
                        entities[f'time_{unit}'] = int(match.group(1))
                    break
        
        # Extract topics
        topic_keywords = {
            'retirement': ['retire', '401k', 'ira', 'pension'],
            'taxes': ['tax', 'deduction', 'irs', 'refund'],
            'investment': ['invest', 'stock', 'bond', 'portfolio'],
            'savings': ['save', 'saving', 'emergency fund'],
            'debt': ['debt', 'loan', 'mortgage', 'credit']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                entities['topic'] = topic
                break
        
        return entities
    
    async def _analyze_sentiment(self, message: str) -> float:
        """Analyze message sentiment"""
        
        # Simple sentiment analysis (could be replaced with ML model)
        positive_words = ['good', 'great', 'excellent', 'happy', 'pleased', 'satisfied']
        negative_words = ['bad', 'terrible', 'unhappy', 'worried', 'concerned', 'frustrated']
        
        message_lower = message.lower()
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return min(0.5 + (positive_count * 0.1), 1.0)
        elif negative_count > positive_count:
            return max(0.5 - (negative_count * 0.1), 0.0)
        else:
            return 0.5
    
    async def _generate_response(
        self,
        session: ConversationSession,
        message: str,
        intent: Intent,
        entities: Dict[str, Any],
        context: ComprehensiveContext,
        next_state: ConversationState
    ) -> Dict[str, Any]:
        """Generate appropriate response based on context"""
        
        response = {
            'text': '',
            'confidence': 0.8,
            'suggestions': [],
            'visualizations': [],
            'action_items': []
        }
        
        # Get state-appropriate base prompt
        base_prompt = self.flow_manager.generate_state_prompt(next_state)
        
        # Customize based on intent and context
        if next_state == ConversationState.GREETING:
            response['text'] = base_prompt
            response['suggestions'] = [
                "Tell me about your financial goals",
                "Review my portfolio",
                "Help with retirement planning"
            ]
        
        elif next_state == ConversationState.GATHERING_INFO:
            missing_info = self._identify_missing_info(context)
            if missing_info:
                response['text'] = f"{base_prompt} Could you tell me about your {missing_info[0]}?"
            else:
                response['text'] = "I have the information I need. Let me analyze your situation."
        
        elif next_state == ConversationState.PROVIDING_ADVICE:
            # This would integrate with the PersonalizedFinancialAdvisor
            response['text'] = f"{base_prompt} Based on your {entities.get('topic', 'situation')}, "
            response['text'] += "I recommend diversifying your portfolio and maximizing tax-advantaged accounts."
            response['action_items'] = [
                {'title': 'Review asset allocation', 'priority': 'high'},
                {'title': 'Increase 401k contribution', 'priority': 'medium'}
            ]
        
        elif next_state == ConversationState.CLARIFYING:
            response['text'] = f"{base_prompt} When you mentioned {entities.get('topic', 'that')}, "
            response['text'] += "did you mean in the context of your current portfolio or future planning?"
        
        elif next_state == ConversationState.FOLLOW_UP:
            response['text'] = base_prompt
            response['suggestions'] = self._generate_follow_up_suggestions(session.topic_history)
        
        elif next_state == ConversationState.CLOSING:
            response['text'] = base_prompt
            if session.action_items:
                response['text'] += f" You have {len(session.action_items)} action items to review."
        
        return response
    
    def _identify_missing_info(self, context: ComprehensiveContext) -> List[str]:
        """Identify what information is missing"""
        
        missing = []
        
        if not context.user_life or not context.user_life.age:
            missing.append("age and life situation")
        
        if not context.goals or not context.goals.active_goals:
            missing.append("financial goals")
        
        if not context.portfolio:
            missing.append("current investments")
        
        return missing
    
    def _generate_follow_up_suggestions(self, topic_history: List[str]) -> List[str]:
        """Generate relevant follow-up suggestions"""
        
        suggestions = []
        
        if 'retirement' in topic_history:
            suggestions.extend([
                "Calculate retirement savings needed",
                "Optimize Social Security claiming strategy",
                "Review healthcare planning"
            ])
        
        if 'investment' in topic_history:
            suggestions.extend([
                "Analyze portfolio risk",
                "Compare to market benchmarks",
                "Review rebalancing schedule"
            ])
        
        if 'taxes' in topic_history:
            suggestions.extend([
                "Identify tax loss harvesting opportunities",
                "Review tax-advantaged account usage",
                "Estimate quarterly payments"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    async def _generate_session_summary(self, session: ConversationSession) -> str:
        """Generate summary of conversation session"""
        
        summary_parts = []
        
        # Topics discussed
        if session.topic_history:
            summary_parts.append(f"Topics discussed: {', '.join(session.topic_history)}")
        
        # Key insights
        if session.turns:
            key_turns = sorted(
                session.turns, 
                key=lambda x: x.confidence, 
                reverse=True
            )[:3]
            summary_parts.append("Key insights provided on: " + 
                ', '.join(set(t.entities.get('topic', 'general') for t in key_turns if t.entities)))
        
        # Action items
        if session.action_items:
            summary_parts.append(f"Generated {len(session.action_items)} action items")
        
        # Goals identified
        if session.goals_discussed:
            summary_parts.append(f"Financial goals: {', '.join(session.goals_discussed)}")
        
        return " | ".join(summary_parts)
    
    async def get_conversation_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for user's conversations"""
        
        sessions = await self.memory.get_user_history(user_id, days)
        
        if not sessions:
            return {'message': 'No conversation history found'}
        
        # Calculate analytics
        total_sessions = len(sessions)
        total_turns = sum(len(s.turns) for s in sessions)
        avg_session_length = total_turns / total_sessions if total_sessions > 0 else 0
        
        # Topic frequency
        topic_counts = defaultdict(int)
        for session in sessions:
            for topic in session.topic_history:
                topic_counts[topic] += 1
        
        # Intent distribution
        intent_counts = defaultdict(int)
        for session in sessions:
            for turn in session.turns:
                intent_counts[turn.intent.value] += 1
        
        # Satisfaction metrics
        rated_sessions = [s for s in sessions if s.satisfaction_score is not None]
        avg_satisfaction = (
            sum(s.satisfaction_score for s in rated_sessions) / len(rated_sessions)
            if rated_sessions else None
        )
        
        # Time patterns
        hour_distribution = defaultdict(int)
        for session in sessions:
            hour_distribution[session.start_time.hour] += 1
        
        return {
            'total_sessions': total_sessions,
            'total_turns': total_turns,
            'avg_session_length': avg_session_length,
            'top_topics': dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            'intent_distribution': dict(intent_counts),
            'avg_satisfaction': avg_satisfaction,
            'peak_hours': dict(sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]),
            'total_action_items': sum(len(s.action_items) for s in sessions)
        }