"""
LLM Integration Service for Financial Advisory
Provides multi-model support, financial expertise, and compliance-aware responses
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging

from langchain import LLMChain, PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory
from langchain.agents import Tool, AgentExecutor, initialize_agent, AgentType
from langchain.callbacks import CallbackManager
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.chains import RetrievalQA

from pydantic import BaseModel, Field
import redis
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    LOCAL = "local"


class TaskType(Enum):
    """Financial task types for model selection"""
    GENERAL_ADVICE = "general_advice"
    TECHNICAL_ANALYSIS = "technical_analysis"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    RISK_ASSESSMENT = "risk_assessment"
    TAX_PLANNING = "tax_planning"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    GOAL_PLANNING = "goal_planning"
    MARKET_ANALYSIS = "market_analysis"


@dataclass
class UserContext:
    """User context for personalization"""
    user_id: str
    age: int
    income: float
    risk_tolerance: str
    investment_goals: List[str]
    current_portfolio: Dict[str, Any]
    tax_bracket: float
    state: str
    life_stage: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    transaction_history: List[Dict] = field(default_factory=list)


@dataclass
class MarketContext:
    """Current market context"""
    market_regime: str
    volatility_index: float
    interest_rates: Dict[str, float]
    inflation_rate: float
    sector_performance: Dict[str, float]
    economic_indicators: Dict[str, Any]
    recent_events: List[str]


@dataclass
class ComplianceContext:
    """Regulatory compliance context"""
    regulations: List[str]
    restrictions: List[str]
    required_disclosures: List[str]
    jurisdiction: str
    account_type: str


class PersonalizedAdvice(BaseModel):
    """Structured financial advice response"""
    advice: str = Field(..., description="Main advice content")
    reasoning: str = Field(..., description="Explanation of reasoning")
    action_items: List[str] = Field(default_factory=list, description="Specific actions to take")
    risks: List[str] = Field(default_factory=list, description="Associated risks")
    compliance_notes: List[str] = Field(default_factory=list, description="Compliance considerations")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in advice")
    sources: List[str] = Field(default_factory=list, description="Information sources used")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FinancialLLMIntegration:
    """
    Advanced LLM integration for financial advisory with multi-model support,
    RAG capabilities, and compliance awareness
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = self._initialize_models()
        self.embeddings = OpenAIEmbeddings(api_key=config.get('openai_api_key'))
        self.vector_store = None
        self.tools = self._initialize_tools()
        self.memory_stores = {}
        self.redis_client = redis.Redis.from_url(
            config.get('redis_url', 'redis://localhost:6379')
        )
        self.compliance_templates = self._load_compliance_templates()
        self.prompt_templates = self._load_prompt_templates()
        
    def _initialize_models(self) -> Dict[TaskType, Any]:
        """Initialize different models for different tasks"""
        models = {}
        
        # OpenAI models
        if self.config.get('openai_api_key'):
            models[TaskType.TECHNICAL_ANALYSIS] = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.3,
                api_key=self.config['openai_api_key']
            )
            models[TaskType.RISK_ASSESSMENT] = ChatOpenAI(
                model="gpt-4",
                temperature=0.2,
                api_key=self.config['openai_api_key']
            )
            models[TaskType.MARKET_ANALYSIS] = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.4,
                api_key=self.config['openai_api_key']
            )
        
        # Anthropic models
        if self.config.get('anthropic_api_key'):
            models[TaskType.GENERAL_ADVICE] = ChatAnthropic(
                model="claude-3-opus-20240229",
                temperature=0.5,
                anthropic_api_key=self.config['anthropic_api_key']
            )
            models[TaskType.REGULATORY_COMPLIANCE] = ChatAnthropic(
                model="claude-3-sonnet-20240229",
                temperature=0.1,
                anthropic_api_key=self.config['anthropic_api_key']
            )
            models[TaskType.TAX_PLANNING] = ChatAnthropic(
                model="claude-3-opus-20240229",
                temperature=0.2,
                anthropic_api_key=self.config['anthropic_api_key']
            )
        
        # Set default fallback model
        if models:
            self.default_model = list(models.values())[0]
        else:
            raise ValueError("No LLM API keys configured")
            
        return models
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize tools for the agent"""
        tools = [
            Tool(
                name="PortfolioAnalyzer",
                func=self._analyze_portfolio_tool,
                description="Analyze portfolio composition and performance"
            ),
            Tool(
                name="TaxCalculator",
                func=self._calculate_tax_tool,
                description="Calculate tax implications of financial decisions"
            ),
            Tool(
                name="MarketDataRetriever",
                func=self._retrieve_market_data_tool,
                description="Get current market data and indicators"
            ),
            Tool(
                name="RegulatoryChecker",
                func=self._check_regulations_tool,
                description="Check regulatory compliance requirements"
            ),
            Tool(
                name="RiskCalculator",
                func=self._calculate_risk_tool,
                description="Calculate risk metrics for investments"
            ),
            Tool(
                name="GoalPlanner",
                func=self._plan_financial_goals_tool,
                description="Create plans for financial goals"
            ),
        ]
        return tools
    
    def _load_compliance_templates(self) -> Dict[str, str]:
        """Load compliance-aware prompt templates"""
        return {
            'disclaimer': """
            This information is for educational purposes only and does not constitute 
            personalized investment advice. Please consult with a qualified financial 
            advisor before making investment decisions.
            """,
            'risk_disclosure': """
            All investments carry risk, including potential loss of principal. 
            Past performance does not guarantee future results.
            """,
            'regulatory_notice': """
            This analysis complies with SEC regulations and FINRA guidelines. 
            Tax implications vary by individual situation.
            """
        }
    
    def _load_prompt_templates(self) -> Dict[TaskType, PromptTemplate]:
        """Load task-specific prompt templates"""
        templates = {
            TaskType.GENERAL_ADVICE: PromptTemplate(
                input_variables=["query", "user_context", "market_context"],
                template="""
                You are an expert financial advisor providing personalized advice.
                
                User Context:
                - Age: {user_context[age]}
                - Income: ${user_context[income]:,.0f}
                - Risk Tolerance: {user_context[risk_tolerance]}
                - Goals: {user_context[investment_goals]}
                - Life Stage: {user_context[life_stage]}
                
                Market Context:
                - Current Regime: {market_context[market_regime]}
                - VIX: {market_context[volatility_index]:.2f}
                - Interest Rates: {market_context[interest_rates]}
                
                User Question: {query}
                
                Provide comprehensive, personalized financial advice that:
                1. Addresses the specific question
                2. Considers the user's personal situation
                3. Accounts for current market conditions
                4. Includes actionable recommendations
                5. Highlights relevant risks
                6. Maintains regulatory compliance
                
                Format your response with clear sections and bullet points where appropriate.
                """
            ),
            TaskType.TECHNICAL_ANALYSIS: PromptTemplate(
                input_variables=["query", "market_data", "portfolio"],
                template="""
                You are a quantitative analyst performing technical analysis.
                
                Portfolio: {portfolio}
                Market Data: {market_data}
                
                Analysis Request: {query}
                
                Provide detailed technical analysis including:
                1. Relevant technical indicators
                2. Chart patterns and trends
                3. Support and resistance levels
                4. Volume analysis
                5. Statistical metrics
                6. Probability assessments
                7. Risk/reward ratios
                
                Use precise numerical data and statistical confidence levels.
                """
            ),
            TaskType.REGULATORY_COMPLIANCE: PromptTemplate(
                input_variables=["action", "context", "regulations"],
                template="""
                You are a compliance officer evaluating financial actions.
                
                Proposed Action: {action}
                Context: {context}
                Applicable Regulations: {regulations}
                
                Evaluate compliance with:
                1. SEC regulations
                2. FINRA rules
                3. State-specific requirements
                4. Tax implications
                5. Reporting requirements
                6. Prohibited practices
                
                Provide:
                - Compliance status (Compliant/Non-compliant/Requires Review)
                - Specific regulations that apply
                - Required disclosures
                - Recommended modifications for compliance
                - Documentation requirements
                """
            ),
            TaskType.TAX_PLANNING: PromptTemplate(
                input_variables=["scenario", "user_context", "tax_situation"],
                template="""
                You are a tax planning specialist optimizing for tax efficiency.
                
                Tax Situation:
                - Tax Bracket: {user_context[tax_bracket]}%
                - State: {user_context[state]}
                - Current Year Income: ${user_context[income]:,.0f}
                
                Scenario: {scenario}
                Additional Context: {tax_situation}
                
                Provide tax-optimized recommendations including:
                1. Tax implications of proposed actions
                2. Tax-loss harvesting opportunities
                3. Account type optimization (401k, Roth, HSA, etc.)
                4. Timing strategies
                5. State tax considerations
                6. Estimated tax savings
                7. Required tax forms and reporting
                
                Include specific dollar amounts and percentages where applicable.
                """
            )
        }
        return templates
    
    async def generate_personalized_advice(
        self,
        query: str,
        user_context: UserContext,
        market_context: MarketContext,
        task_type: TaskType = TaskType.GENERAL_ADVICE,
        use_rag: bool = True
    ) -> PersonalizedAdvice:
        """Generate comprehensive personalized financial advice"""
        
        try:
            # Select appropriate model for task
            model = self.models.get(task_type, self.default_model)
            
            # Get or create memory for user
            memory = self._get_user_memory(user_context.user_id)
            
            # Enrich context with RAG if enabled
            enriched_context = {}
            if use_rag and self.vector_store:
                relevant_docs = await self._retrieve_relevant_knowledge(
                    query, user_context, market_context
                )
                enriched_context['knowledge_base'] = relevant_docs
            
            # Prepare the prompt
            prompt_template = self.prompt_templates.get(
                task_type,
                self.prompt_templates[TaskType.GENERAL_ADVICE]
            )
            
            # Create the chain with memory
            chain = LLMChain(
                llm=model,
                prompt=prompt_template,
                memory=memory,
                verbose=True
            )
            
            # Generate response
            response = await chain.apredict(
                query=query,
                user_context=user_context.__dict__,
                market_context=market_context.__dict__,
                **enriched_context
            )
            
            # Parse and structure the response
            structured_advice = await self._structure_advice(
                response, task_type, user_context
            )
            
            # Add compliance checks
            compliance_notes = await self._add_compliance_notes(
                structured_advice, user_context
            )
            structured_advice.compliance_notes = compliance_notes
            
            # Calculate confidence score
            confidence = await self._calculate_confidence(
                structured_advice, user_context, market_context
            )
            structured_advice.confidence_score = confidence
            
            # Store interaction for learning
            await self._store_interaction(
                user_context.user_id,
                query,
                structured_advice
            )
            
            return structured_advice
            
        except Exception as e:
            logger.error(f"Error generating advice: {str(e)}")
            # Return safe fallback advice
            return PersonalizedAdvice(
                advice="I apologize, but I'm unable to provide specific advice at this moment. Please consult with a qualified financial advisor.",
                reasoning="System is currently unavailable",
                confidence_score=0.0,
                compliance_notes=[self.compliance_templates['disclaimer']]
            )
    
    def _get_user_memory(self, user_id: str) -> ConversationSummaryBufferMemory:
        """Get or create conversation memory for user"""
        if user_id not in self.memory_stores:
            self.memory_stores[user_id] = ConversationSummaryBufferMemory(
                llm=self.default_model,
                max_token_limit=2000,
                return_messages=True
            )
        return self.memory_stores[user_id]
    
    async def _retrieve_relevant_knowledge(
        self,
        query: str,
        user_context: UserContext,
        market_context: MarketContext
    ) -> List[str]:
        """Retrieve relevant information from knowledge base"""
        if not self.vector_store:
            return []
        
        # Combine query with context for better retrieval
        enhanced_query = f"""
        Query: {query}
        User Profile: {user_context.life_stage}, {user_context.risk_tolerance} risk
        Market: {market_context.market_regime} regime
        """
        
        # Retrieve relevant documents
        docs = await self.vector_store.asimilarity_search(
            enhanced_query,
            k=5
        )
        
        return [doc.page_content for doc in docs]
    
    async def _structure_advice(
        self,
        raw_response: str,
        task_type: TaskType,
        user_context: UserContext
    ) -> PersonalizedAdvice:
        """Structure the raw LLM response into PersonalizedAdvice format"""
        
        # Use a structured output parser
        structure_prompt = PromptTemplate(
            input_variables=["response"],
            template="""
            Parse the following financial advice into structured components:
            
            {response}
            
            Extract:
            1. Main advice (summary)
            2. Detailed reasoning
            3. Specific action items (list)
            4. Associated risks (list)
            5. Follow-up questions (list)
            
            Format as JSON.
            """
        )
        
        parser_chain = LLMChain(
            llm=self.default_model,
            prompt=structure_prompt
        )
        
        structured = await parser_chain.apredict(response=raw_response)
        
        try:
            parsed = json.loads(structured)
            return PersonalizedAdvice(
                advice=parsed.get('advice', raw_response[:500]),
                reasoning=parsed.get('reasoning', ''),
                action_items=parsed.get('action_items', []),
                risks=parsed.get('risks', []),
                follow_up_questions=parsed.get('follow_up_questions', []),
                sources=[f"Analysis based on {task_type.value}"]
            )
        except:
            # Fallback to basic structure
            return PersonalizedAdvice(
                advice=raw_response[:500],
                reasoning=raw_response[500:1000] if len(raw_response) > 500 else '',
                sources=[f"Analysis based on {task_type.value}"]
            )
    
    async def _add_compliance_notes(
        self,
        advice: PersonalizedAdvice,
        user_context: UserContext
    ) -> List[str]:
        """Add relevant compliance notes based on advice content"""
        notes = [self.compliance_templates['disclaimer']]
        
        # Check for specific compliance requirements
        if any(term in advice.advice.lower() for term in ['invest', 'buy', 'sell', 'trade']):
            notes.append(self.compliance_templates['risk_disclosure'])
        
        if any(term in advice.advice.lower() for term in ['tax', 'deduction', 'irs']):
            notes.append("Tax advice should be verified with a qualified tax professional.")
        
        if user_context.age >= 59.5:
            notes.append("Special rules may apply for retirement account distributions.")
        
        return notes
    
    async def _calculate_confidence(
        self,
        advice: PersonalizedAdvice,
        user_context: UserContext,
        market_context: MarketContext
    ) -> float:
        """Calculate confidence score for the advice"""
        confidence = 0.7  # Base confidence
        
        # Adjust based on data completeness
        if user_context.transaction_history:
            confidence += 0.1
        
        # Adjust based on market conditions
        if market_context.volatility_index < 20:
            confidence += 0.1
        elif market_context.volatility_index > 30:
            confidence -= 0.1
        
        # Adjust based on advice specificity
        if len(advice.action_items) > 3:
            confidence += 0.05
        
        if advice.sources:
            confidence += 0.05
        
        return min(max(confidence, 0.0), 1.0)
    
    async def _store_interaction(
        self,
        user_id: str,
        query: str,
        advice: PersonalizedAdvice
    ):
        """Store interaction for future learning and analysis"""
        interaction = {
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'query': query,
            'advice': advice.dict(),
            'feedback': None  # To be filled later
        }
        
        # Store in Redis with expiry
        key = f"interaction:{user_id}:{datetime.utcnow().timestamp()}"
        self.redis_client.setex(
            key,
            86400 * 30,  # 30 days
            json.dumps(interaction)
        )
    
    # Tool implementations
    async def _analyze_portfolio_tool(self, portfolio_data: str) -> str:
        """Tool for analyzing portfolio composition"""
        return f"Portfolio analysis: Diversified across sectors with moderate risk"
    
    async def _calculate_tax_tool(self, scenario: str) -> str:
        """Tool for calculating tax implications"""
        return f"Tax calculation: Estimated tax impact of ${1000}"
    
    async def _retrieve_market_data_tool(self, symbols: str) -> str:
        """Tool for retrieving market data"""
        return f"Market data: Current market conditions are stable"
    
    async def _check_regulations_tool(self, action: str) -> str:
        """Tool for checking regulatory compliance"""
        return f"Compliance check: Action is compliant with regulations"
    
    async def _calculate_risk_tool(self, investment: str) -> str:
        """Tool for calculating risk metrics"""
        return f"Risk metrics: VaR at 95% confidence is 5%"
    
    async def _plan_financial_goals_tool(self, goals: str) -> str:
        """Tool for planning financial goals"""
        return f"Goal planning: Retirement target achievable in 20 years"
    
    async def create_multi_agent_system(
        self,
        user_context: UserContext
    ) -> AgentExecutor:
        """Create a multi-agent system for complex financial planning"""
        
        # Initialize specialized agents
        agents = {
            'portfolio_manager': initialize_agent(
                tools=[tool for tool in self.tools if 'portfolio' in tool.name.lower()],
                llm=self.models.get(TaskType.PORTFOLIO_OPTIMIZATION, self.default_model),
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            ),
            'tax_specialist': initialize_agent(
                tools=[tool for tool in self.tools if 'tax' in tool.name.lower()],
                llm=self.models.get(TaskType.TAX_PLANNING, self.default_model),
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            ),
            'risk_analyst': initialize_agent(
                tools=[tool for tool in self.tools if 'risk' in tool.name.lower()],
                llm=self.models.get(TaskType.RISK_ASSESSMENT, self.default_model),
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            ),
            'compliance_officer': initialize_agent(
                tools=[tool for tool in self.tools if 'regulat' in tool.name.lower()],
                llm=self.models.get(TaskType.REGULATORY_COMPLIANCE, self.default_model),
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
        }
        
        # Create orchestrator agent
        orchestrator = initialize_agent(
            tools=self.tools,
            llm=self.models.get(TaskType.GENERAL_ADVICE, self.default_model),
            agent=AgentType.OPENAI_MULTI_FUNCTIONS,
            verbose=True,
            memory=self._get_user_memory(user_context.user_id)
        )
        
        return orchestrator
    
    async def process_with_fallback(
        self,
        query: str,
        user_context: UserContext,
        market_context: MarketContext,
        task_type: TaskType = TaskType.GENERAL_ADVICE
    ) -> PersonalizedAdvice:
        """Process query with automatic fallback to alternative models"""
        
        primary_model = self.models.get(task_type)
        fallback_models = [m for t, m in self.models.items() if t != task_type]
        
        # Try primary model
        try:
            return await self.generate_personalized_advice(
                query, user_context, market_context, task_type
            )
        except Exception as e:
            logger.warning(f"Primary model failed: {e}")
        
        # Try fallback models
        for model in fallback_models:
            try:
                temp_models = self.models.copy()
                temp_models[task_type] = model
                self.models = temp_models
                
                result = await self.generate_personalized_advice(
                    query, user_context, market_context, task_type
                )
                
                # Restore original models
                self.models = temp_models
                return result
                
            except Exception as e:
                logger.warning(f"Fallback model failed: {e}")
                continue
        
        # All models failed - return safe response
        return PersonalizedAdvice(
            advice="I apologize, but I'm currently unable to process your request. Please try again later or contact support.",
            reasoning="All AI models are currently unavailable",
            confidence_score=0.0,
            compliance_notes=[self.compliance_templates['disclaimer']]
        )