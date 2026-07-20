"""
Interactive Financial Coaching Session Manager

Provides conversational coaching interface with Q&A, scenario planning,
and decision support capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json
from dataclasses import dataclass
import uuid

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.base import SessionLocal
from app.models.user import User
from app.ai.llm_client import LLMClientManager
from app.ai.config import AIConfig

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """States of coaching conversation."""
    GREETING = "greeting"
    ASSESSMENT = "assessment"
    EXPLORATION = "exploration"
    PLANNING = "planning"
    ACTION = "action"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"


class ConversationTopic(str, Enum):
    """Topics for coaching conversations."""
    GENERAL_ADVICE = "general_advice"
    GOAL_PLANNING = "goal_planning"
    BUDGET_REVIEW = "budget_review"
    INVESTMENT_STRATEGY = "investment_strategy"
    DEBT_STRATEGY = "debt_strategy"
    SCENARIO_PLANNING = "scenario_planning"
    FINANCIAL_EDUCATION = "financial_education"
    CRISIS_SUPPORT = "crisis_support"
    PROGRESS_REVIEW = "progress_review"


@dataclass
class Message:
    """Represents a message in coaching conversation."""
    id: str
    role: str  # 'user' or 'coach'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class CoachingConversation:
    """Represents a coaching conversation session."""
    conversation_id: str
    user_id: str
    topic: ConversationTopic
    state: ConversationState
    messages: List[Message]
    context: Dict[str, Any]
    action_items: List[str]
    insights_generated: List[Dict]
    started_at: datetime
    last_activity: datetime
    is_active: bool


class ScenarioAnalysis(BaseModel):
    """Scenario planning analysis result."""
    scenario_name: str
    description: str
    assumptions: Dict[str, Any]
    projected_outcomes: Dict[str, float]
    probability_of_success: float
    risks: List[str]
    opportunities: List[str]
    recommended_actions: List[str]
    timeline: str


class DecisionFramework(BaseModel):
    """Decision support framework."""
    decision_question: str
    options: List[Dict[str, Any]]
    evaluation_criteria: List[str]
    pros_cons: Dict[str, List[str]]
    recommendation: str
    confidence_level: float
    supporting_data: Dict[str, Any]


class InteractiveCoachingManager:
    """Manages interactive coaching sessions and conversations."""
    
    def __init__(self, llm_manager: LLMClientManager, config: AIConfig):
        self.llm_manager = llm_manager
        self.config = config
        
        # Active conversations storage
        self.active_conversations: Dict[str, CoachingConversation] = {}
        
        # Conversation flow templates
        self.conversation_flows = self._initialize_conversation_flows()
        
        # Q&A knowledge base
        self.qa_knowledge = self._initialize_qa_knowledge()
        
        # Scenario templates
        self.scenario_templates = self._initialize_scenario_templates()
    
    async def start_conversation(
        self,
        user_id: str,
        topic: Optional[ConversationTopic] = None,
        initial_message: Optional[str] = None
    ) -> CoachingConversation:
        """Start a new coaching conversation."""
        
        try:
            # Create conversation
            conversation = CoachingConversation(
                conversation_id=str(uuid.uuid4()),
                user_id=user_id,
                topic=topic or ConversationTopic.GENERAL_ADVICE,
                state=ConversationState.GREETING,
                messages=[],
                context=await self._build_user_context(user_id),
                action_items=[],
                insights_generated=[],
                started_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_active=True
            )
            
            # Generate greeting
            greeting = await self._generate_greeting(conversation)
            
            # Add greeting message
            conversation.messages.append(Message(
                id=str(uuid.uuid4()),
                role='coach',
                content=greeting,
                timestamp=datetime.utcnow(),
                metadata={'state': ConversationState.GREETING.value}
            ))
            
            # Process initial message if provided
            if initial_message:
                response = await self.process_message(
                    conversation.conversation_id,
                    initial_message
                )
                conversation.messages.extend(response['messages'])
            
            # Store conversation
            self.active_conversations[conversation.conversation_id] = conversation
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error starting conversation: {str(e)}")
            raise
    
    async def process_message(
        self,
        conversation_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """Process user message and generate response."""
        
        try:
            # Get conversation
            conversation = self.active_conversations.get(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Add user message
            user_msg = Message(
                id=str(uuid.uuid4()),
                role='user',
                content=user_message,
                timestamp=datetime.utcnow(),
                metadata={}
            )
            conversation.messages.append(user_msg)
            
            # Update conversation state
            conversation.state = await self._determine_next_state(
                conversation, user_message
            )
            
            # Generate response based on state and context
            response = await self._generate_response(
                conversation, user_message
            )
            
            # Add coach response
            coach_msg = Message(
                id=str(uuid.uuid4()),
                role='coach',
                content=response['content'],
                timestamp=datetime.utcnow(),
                metadata=response.get('metadata', {})
            )
            conversation.messages.append(coach_msg)
            
            # Extract action items if any
            if response.get('action_items'):
                conversation.action_items.extend(response['action_items'])
            
            # Update last activity
            conversation.last_activity = datetime.utcnow()
            
            return {
                'messages': [user_msg, coach_msg],
                'state': conversation.state.value,
                'action_items': response.get('action_items', []),
                'insights': response.get('insights', [])
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'messages': [],
                'error': str(e)
            }
    
    async def analyze_scenario(
        self,
        user_id: str,
        scenario_description: str,
        parameters: Dict[str, Any]
    ) -> ScenarioAnalysis:
        """Analyze a financial scenario for the user."""
        
        try:
            # Build scenario prompt
            prompt = await self._build_scenario_prompt(
                user_id, scenario_description, parameters
            )
            
            # Generate scenario analysis
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1500
            )
            
            # Parse and structure analysis
            analysis = await self._parse_scenario_analysis(
                llm_response.content,
                scenario_description,
                parameters
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing scenario: {str(e)}")
            return self._get_fallback_scenario_analysis(scenario_description)
    
    async def provide_decision_support(
        self,
        user_id: str,
        decision_question: str,
        options: List[str],
        context: Optional[Dict] = None
    ) -> DecisionFramework:
        """Provide structured decision support."""
        
        try:
            # Build decision support prompt
            prompt = await self._build_decision_prompt(
                user_id, decision_question, options, context
            )
            
            # Generate decision analysis
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.4,
                max_tokens=1200
            )
            
            # Parse and structure framework
            framework = await self._parse_decision_framework(
                llm_response.content,
                decision_question,
                options
            )
            
            return framework
            
        except Exception as e:
            logger.error(f"Error providing decision support: {str(e)}")
            return self._get_fallback_decision_framework(decision_question, options)
    
    async def answer_question(
        self,
        user_id: str,
        question: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Answer a specific financial question."""
        
        try:
            # Classify question type
            question_type = await self._classify_question(question)
            
            # Build Q&A prompt
            prompt = await self._build_qa_prompt(
                user_id, question, question_type, context
            )
            
            # Generate answer
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            # Structure response
            return {
                'question': question,
                'answer': llm_response.content,
                'question_type': question_type,
                'confidence': 0.85,
                'related_topics': await self._get_related_topics(question_type),
                'follow_up_questions': await self._generate_follow_up_questions(question)
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                'question': question,
                'answer': "I apologize, but I'm having trouble processing your question. Could you please rephrase it?",
                'error': str(e)
            }
    
    async def _build_user_context(self, user_id: str) -> Dict[str, Any]:
        """Build user context for conversation."""
        
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Build comprehensive context
            return {
                'user_id': user_id,
                'name': user.first_name,
                'financial_profile': {
                    'income': 75000,  # Would fetch from profile
                    'expenses': 5000,
                    'savings': 15000,
                    'investments': 25000,
                    'debt': 10000
                },
                'goals': ['retirement', 'home_purchase', 'emergency_fund'],
                'risk_tolerance': 'moderate',
                'experience_level': 'intermediate',
                'recent_topics': [],
                'preferences': {
                    'communication_style': 'conversational',
                    'detail_level': 'moderate'
                }
            }
    
    async def _generate_greeting(self, conversation: CoachingConversation) -> str:
        """Generate personalized greeting."""
        
        context = conversation.context
        topic = conversation.topic
        
        prompt = f"""
        Generate a warm, professional greeting for a financial coaching conversation.
        
        User: {context.get('name', 'there')}
        Topic: {topic.value}
        Experience Level: {context.get('experience_level', 'beginner')}
        
        The greeting should:
        1. Be welcoming and professional
        2. Acknowledge the topic if specific
        3. Set expectations for the conversation
        4. Invite the user to share their questions or concerns
        
        Keep it concise (2-3 sentences).
        """
        
        try:
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=150
            )
            return llm_response.content
        except:
            return f"Hello {context.get('name', 'there')}! I'm here to help with your {topic.value.replace('_', ' ')} questions. What would you like to discuss today?"
    
    async def _determine_next_state(
        self,
        conversation: CoachingConversation,
        user_message: str
    ) -> ConversationState:
        """Determine next conversation state based on context."""
        
        current_state = conversation.state
        message_lower = user_message.lower()
        
        # State transition logic
        if current_state == ConversationState.GREETING:
            if any(word in message_lower for word in ['help', 'question', 'need', 'want']):
                return ConversationState.ASSESSMENT
            else:
                return ConversationState.EXPLORATION
        
        elif current_state == ConversationState.ASSESSMENT:
            if len(conversation.messages) > 4:
                return ConversationState.PLANNING
            else:
                return ConversationState.EXPLORATION
        
        elif current_state == ConversationState.EXPLORATION:
            if any(word in message_lower for word in ['plan', 'strategy', 'should i', 'what if']):
                return ConversationState.PLANNING
            elif any(word in message_lower for word in ['do', 'action', 'next', 'step']):
                return ConversationState.ACTION
        
        elif current_state == ConversationState.PLANNING:
            if any(word in message_lower for word in ['implement', 'start', 'begin', 'do']):
                return ConversationState.ACTION
        
        elif current_state == ConversationState.ACTION:
            if any(word in message_lower for word in ['check', 'review', 'progress']):
                return ConversationState.FOLLOW_UP
            elif any(word in message_lower for word in ['bye', 'thanks', 'goodbye', 'done']):
                return ConversationState.CLOSING
        
        # Default to maintaining current state
        return current_state
    
    async def _generate_response(
        self,
        conversation: CoachingConversation,
        user_message: str
    ) -> Dict[str, Any]:
        """Generate coach response based on conversation context."""
        
        # Build conversation history
        history = self._build_conversation_history(conversation)
        
        # Create prompt based on state
        prompt = f"""
        You are a professional financial coach having a conversation with a user.
        
        Conversation Topic: {conversation.topic.value}
        Current State: {conversation.state.value}
        User Experience: {conversation.context.get('experience_level', 'intermediate')}
        
        Conversation History:
        {history}
        
        User's Latest Message: {user_message}
        
        Based on the conversation state and context, provide an appropriate response that:
        1. Directly addresses the user's message
        2. Maintains a {conversation.context.get('preferences', {}).get('communication_style', 'professional')} tone
        3. Guides the conversation forward
        4. Provides specific, actionable information when appropriate
        5. Asks clarifying questions if needed
        
        For state '{conversation.state.value}':
        - Focus on {self._get_state_focus(conversation.state)}
        - Keep response concise but informative
        - If appropriate, suggest next steps or action items
        """
        
        try:
            llm_response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract action items if mentioned
            action_items = await self._extract_action_items(llm_response.content)
            
            return {
                'content': llm_response.content,
                'action_items': action_items,
                'metadata': {
                    'state': conversation.state.value,
                    'topic': conversation.topic.value
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'content': "I understand your question. Let me think about the best way to help you with that.",
                'action_items': [],
                'metadata': {}
            }
    
    def _build_conversation_history(self, conversation: CoachingConversation) -> str:
        """Build formatted conversation history."""
        
        # Limit to last 10 messages for context
        recent_messages = conversation.messages[-10:]
        
        history = []
        for msg in recent_messages:
            role = "Coach" if msg.role == 'coach' else "User"
            # Truncate long messages
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            history.append(f"{role}: {content}")
        
        return "\n".join(history)
    
    def _get_state_focus(self, state: ConversationState) -> str:
        """Get focus description for conversation state."""
        
        focus_map = {
            ConversationState.GREETING: "welcoming and understanding initial needs",
            ConversationState.ASSESSMENT: "understanding the user's situation and goals",
            ConversationState.EXPLORATION: "exploring options and possibilities",
            ConversationState.PLANNING: "creating actionable plans and strategies",
            ConversationState.ACTION: "defining specific next steps and implementation",
            ConversationState.FOLLOW_UP: "reviewing progress and adjusting plans",
            ConversationState.CLOSING: "summarizing key points and ensuring clarity"
        }
        
        return focus_map.get(state, "providing helpful guidance")
    
    async def _extract_action_items(self, content: str) -> List[str]:
        """Extract action items from response content."""
        
        action_items = []
        
        # Simple extraction based on patterns
        lines = content.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(marker in line_lower for marker in ['action:', 'step:', 'todo:', '•', '-']):
                # Clean and add action item
                item = line.strip('•-* ').strip()
                if len(item) > 10 and len(item) < 200:  # Reasonable length
                    action_items.append(item)
        
        return action_items[:5]  # Limit to 5 items
    
    async def _build_scenario_prompt(
        self,
        user_id: str,
        scenario_description: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Build prompt for scenario analysis."""
        
        return f"""
        Analyze this financial scenario for the user:
        
        Scenario: {scenario_description}
        
        Parameters:
        {json.dumps(parameters, indent=2)}
        
        Provide a comprehensive analysis including:
        1. Key assumptions being made
        2. Projected financial outcomes (with specific numbers)
        3. Probability of success (as percentage)
        4. Main risks to consider
        5. Opportunities that might arise
        6. Specific recommended actions
        7. Realistic timeline
        
        Base your analysis on sound financial principles and provide specific, actionable insights.
        """
    
    async def _parse_scenario_analysis(
        self,
        llm_content: str,
        scenario_description: str,
        parameters: Dict
    ) -> ScenarioAnalysis:
        """Parse scenario analysis from LLM response."""
        
        # Simple parsing - in production would use structured output
        return ScenarioAnalysis(
            scenario_name=scenario_description[:50],
            description=scenario_description,
            assumptions=parameters,
            projected_outcomes={
                'best_case': 50000,
                'expected': 35000,
                'worst_case': 20000
            },
            probability_of_success=0.75,
            risks=['Market volatility', 'Income stability', 'Unexpected expenses'],
            opportunities=['Tax advantages', 'Compound growth', 'Employer matching'],
            recommended_actions=[
                'Start with conservative assumptions',
                'Build emergency fund first',
                'Review quarterly and adjust'
            ],
            timeline='12-24 months'
        )
    
    def _get_fallback_scenario_analysis(self, scenario_description: str) -> ScenarioAnalysis:
        """Get fallback scenario analysis."""
        
        return ScenarioAnalysis(
            scenario_name=scenario_description[:50],
            description=scenario_description,
            assumptions={'default': 'standard'},
            projected_outcomes={'expected': 0},
            probability_of_success=0.5,
            risks=['Unable to fully analyze at this time'],
            opportunities=['Please consult with a financial advisor'],
            recommended_actions=['Gather more information', 'Consider multiple scenarios'],
            timeline='Varies'
        )
    
    async def _build_decision_prompt(
        self,
        user_id: str,
        decision_question: str,
        options: List[str],
        context: Optional[Dict]
    ) -> str:
        """Build prompt for decision support."""
        
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        return f"""
        Help the user make this financial decision:
        
        Question: {decision_question}
        
        Options:
        {options_text}
        
        Additional Context: {json.dumps(context) if context else 'None'}
        
        Provide a structured decision analysis:
        1. Key evaluation criteria to consider
        2. Pros and cons of each option
        3. Your recommendation with reasoning
        4. Confidence level (0-1)
        5. Important data points to support the decision
        
        Be objective, thorough, and consider both short-term and long-term implications.
        """
    
    async def _parse_decision_framework(
        self,
        llm_content: str,
        decision_question: str,
        options: List[str]
    ) -> DecisionFramework:
        """Parse decision framework from LLM response."""
        
        # Simple parsing - in production would use structured output
        return DecisionFramework(
            decision_question=decision_question,
            options=[{'name': opt, 'score': 0.5} for opt in options],
            evaluation_criteria=['Cost', 'Risk', 'Timeline', 'Impact on goals'],
            pros_cons={
                options[0]: ['Pro 1', 'Pro 2'],
                options[1]: ['Pro 1', 'Con 1'] if len(options) > 1 else []
            },
            recommendation=options[0] if options else 'Need more information',
            confidence_level=0.75,
            supporting_data={'analysis': 'Based on financial best practices'}
        )
    
    def _get_fallback_decision_framework(
        self,
        decision_question: str,
        options: List[str]
    ) -> DecisionFramework:
        """Get fallback decision framework."""
        
        return DecisionFramework(
            decision_question=decision_question,
            options=[{'name': opt} for opt in options],
            evaluation_criteria=['Consider all factors carefully'],
            pros_cons={},
            recommendation='Please gather more information before deciding',
            confidence_level=0.3,
            supporting_data={}
        )
    
    async def _classify_question(self, question: str) -> str:
        """Classify the type of financial question."""
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['invest', 'stock', 'bond', 'portfolio']):
            return 'investment'
        elif any(word in question_lower for word in ['save', 'savings', 'emergency']):
            return 'savings'
        elif any(word in question_lower for word in ['budget', 'expense', 'spend']):
            return 'budgeting'
        elif any(word in question_lower for word in ['debt', 'loan', 'credit']):
            return 'debt'
        elif any(word in question_lower for word in ['tax', 'deduction', 'irs']):
            return 'tax'
        elif any(word in question_lower for word in ['retire', '401k', 'ira']):
            return 'retirement'
        else:
            return 'general'
    
    async def _build_qa_prompt(
        self,
        user_id: str,
        question: str,
        question_type: str,
        context: Optional[Dict]
    ) -> str:
        """Build prompt for Q&A."""
        
        return f"""
        Answer this financial question clearly and accurately:
        
        Question: {question}
        Question Type: {question_type}
        
        Provide a helpful answer that:
        1. Directly addresses the question
        2. Is accurate and compliant with financial regulations
        3. Includes specific examples or numbers when helpful
        4. Mentions important caveats or considerations
        5. Suggests next steps if appropriate
        
        Keep the answer concise but complete (2-3 paragraphs).
        """
    
    async def _get_related_topics(self, question_type: str) -> List[str]:
        """Get related topics for a question type."""
        
        related_map = {
            'investment': ['diversification', 'risk management', 'asset allocation'],
            'savings': ['emergency fund', 'high-yield accounts', 'automatic saving'],
            'budgeting': ['expense tracking', '50/30/20 rule', 'zero-based budgeting'],
            'debt': ['debt avalanche', 'debt snowball', 'credit score'],
            'tax': ['deductions', 'tax-advantaged accounts', 'withholding'],
            'retirement': ['compound interest', 'employer matching', 'retirement income']
        }
        
        return related_map.get(question_type, ['financial planning', 'money management'])
    
    async def _generate_follow_up_questions(self, original_question: str) -> List[str]:
        """Generate relevant follow-up questions."""
        
        # Simple generation - in production would use LLM
        return [
            "Would you like more specific examples?",
            "How does this apply to your current situation?",
            "What's your timeline for implementing this?"
        ]
    
    def _initialize_conversation_flows(self) -> Dict:
        """Initialize conversation flow templates."""
        return {
            ConversationTopic.GOAL_PLANNING: {
                'stages': ['identify_goals', 'prioritize', 'quantify', 'timeline', 'action_plan'],
                'questions': [
                    "What are your main financial goals?",
                    "Which goal is most important to you right now?",
                    "How much money do you need for this goal?",
                    "When would you like to achieve this?",
                    "What steps can you take this month?"
                ]
            }
        }
    
    def _initialize_qa_knowledge(self) -> Dict:
        """Initialize Q&A knowledge base."""
        return {
            'common_questions': {
                'how_much_emergency_fund': "Aim for 3-6 months of essential expenses in your emergency fund.",
                'when_start_investing': "Start investing as soon as you have an emergency fund and high-interest debt paid off.",
                'how_budget': "Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings and debt payment."
            }
        }
    
    def _initialize_scenario_templates(self) -> Dict:
        """Initialize scenario planning templates."""
        return {
            'home_purchase': {
                'parameters': ['purchase_price', 'down_payment', 'interest_rate', 'timeline'],
                'analysis_points': ['affordability', 'monthly_payment', 'total_cost', 'opportunity_cost']
            },
            'retirement_planning': {
                'parameters': ['current_age', 'retirement_age', 'desired_income', 'current_savings'],
                'analysis_points': ['required_savings_rate', 'investment_return_needed', 'gap_analysis']
            }
        }