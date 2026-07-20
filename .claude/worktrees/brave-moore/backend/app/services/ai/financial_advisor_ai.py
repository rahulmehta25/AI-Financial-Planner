from typing import Dict, List, Optional, Any, Union, Tuple
import asyncio
import logging
import json
import re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import traceback

import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
import anthropic
import openai
from openai import AsyncOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS, Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import redis
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Initialize LLM clients
CLAUDE_CLIENT = None
OPENAI_CLIENT = None

class LLMProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC_CLAUDE = "claude-3-opus-20240229"
    OPENAI_GPT4 = "gpt-4-turbo-preview"
    OPENAI_GPT35 = "gpt-3.5-turbo-0125"
    
class TaskType(Enum):
    """Types of financial advisory tasks"""
    GENERAL_ADVICE = "general_advice"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    TAX_PLANNING = "tax_planning"
    RETIREMENT_PLANNING = "retirement_planning"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_ANALYSIS = "market_analysis"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    GOAL_PLANNING = "goal_planning"

class ComplianceLevel(Enum):
    """Compliance checking levels"""
    STRICT = "strict"  # Full regulatory compliance
    STANDARD = "standard"  # Standard disclaimers
    EDUCATIONAL = "educational"  # Educational content only

@dataclass
class UserContext:
    user_id: str
    profile: Dict[str, Any]
    portfolio_analysis: Dict[str, Any]
    goal_progress: List[Dict[str, Any]]

@dataclass
class MarketContext:
    current_market_conditions: str
    volatility_regime: str
    economic_outlook: str

@dataclass
class EnrichedContext:
    user_profile: Dict[str, Any]
    portfolio_analysis: Dict[str, Any]
    goal_progress: List[Dict[str, Any]]
    relevant_history: List[Dict[str, Any]]
    peer_comparisons: Dict[str, Any]
    market_insights: Dict[str, Any]
    historical_scenarios: List[Dict[str, Any]]
    regulatory_context: Dict[str, Any]

@dataclass
class ValidatedAdvice:
    narrative: str
    confidence: float
    validation_results: List[Dict[str, Any]]
    key_points: List[str]
    sources: List[str]

@dataclass
class ActionItem:
    title: str
    description: str
    priority: str
    impact: float
    steps: List[str]
    timeline: str
    dependencies: List[str]

@dataclass
class ActionPlan:
    items: List[ActionItem]
    total_estimated_impact: float
    implementation_timeline: str

@dataclass
class PersonalizedAdvice:
    narrative: str
    key_points: List[str]
    action_plan: ActionPlan
    visualizations: List[Dict[str, Any]]
    confidence_score: float
    sources: List[str]
    disclaimers: List[str]

class PersonalizedFinancialAdvisor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize LLM providers with fallback
        self._initialize_llm_providers()
        
        # Task-specific model mapping
        self.task_models = {
            TaskType.GENERAL_ADVICE: LLMProvider.ANTHROPIC_CLAUDE,
            TaskType.PORTFOLIO_ANALYSIS: LLMProvider.OPENAI_GPT4,
            TaskType.TAX_PLANNING: LLMProvider.ANTHROPIC_CLAUDE,
            TaskType.RETIREMENT_PLANNING: LLMProvider.OPENAI_GPT4,
            TaskType.RISK_ASSESSMENT: LLMProvider.OPENAI_GPT4,
            TaskType.MARKET_ANALYSIS: LLMProvider.OPENAI_GPT35,
            TaskType.REGULATORY_COMPLIANCE: LLMProvider.ANTHROPIC_CLAUDE,
            TaskType.GOAL_PLANNING: LLMProvider.ANTHROPIC_CLAUDE
        }
        
        # Initialize knowledge bases
        self.vector_store = self._initialize_vector_store()
        self.regulatory_kb = RegulatoryKnowledgeBase()
        self.market_kb = MarketKnowledgeBase()
        self.prompt_manager = PromptManager()
        
        # Initialize Redis for caching
        self.redis_client = redis.Redis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379'),
            decode_responses=True
        )
        
        # Response cache settings
        self.cache_ttl = self.config.get('cache_ttl', 3600)
        self.use_cache = self.config.get('use_cache', True)
        
        # Compliance settings
        self.compliance_level = ComplianceLevel(
            self.config.get('compliance_level', 'standard')
        )
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_requests=self.config.get('max_requests_per_minute', 60)
        )
    
    def _initialize_llm_providers(self):
        """Initialize LLM providers with error handling"""
        global CLAUDE_CLIENT, OPENAI_CLIENT
        
        # Initialize Anthropic Claude
        try:
            anthropic_key = self.config.get('anthropic_api_key')
            if anthropic_key:
                CLAUDE_CLIENT = anthropic.AsyncAnthropic(api_key=anthropic_key)
                logger.info("Anthropic Claude client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
        
        # Initialize OpenAI
        try:
            openai_key = self.config.get('openai_api_key')
            if openai_key:
                OPENAI_CLIENT = AsyncOpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_personalized_advice(
        self,
        user_query: str,
        user_context: UserContext,
        market_context: MarketContext
    ) -> PersonalizedAdvice:
        """Generate comprehensive personalized financial advice"""
        
        # Enrich context with relevant information
        enriched_context = await self._enrich_context(
            user_context,
            market_context,
            user_query
        )
        
        # Check cache first
        cache_key = self._generate_cache_key(user_query, user_context)
        if self.use_cache:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.info("Returning cached response")
                return cached_response
        
        # Check regulatory compliance
        compliance_check = await self.regulatory_kb.check_compliance(
            user_query,
            user_context,
            self.compliance_level
        )
        
        if not compliance_check.get('is_compliant', True):
            return self._generate_compliance_restricted_response(
                compliance_check.get('restrictions', [])
            )
        
        # Determine task type
        task_type = await self._classify_task(user_query, enriched_context)
        
        # Generate advice using appropriate LLM
        raw_advice = await self._generate_llm_response(
            task_type=task_type,
            query=user_query,
            context=enriched_context,
            guidelines=compliance_check.get('guidelines', [])
        )
        
        # Post-process and validate
        validated_advice = await self._validate_advice(
            raw_advice,
            user_context,
            compliance_check.get('guidelines', [])
        )
        
        # Generate actionable steps
        action_plan = await self._generate_action_plan(
            validated_advice,
            user_context
        )
        
        # Create visualizations
        visualizations = await self._generate_visualizations(
            validated_advice,
            user_context
        )
        
        return PersonalizedAdvice(
            narrative=validated_advice.narrative,
            key_points=validated_advice.key_points,
            action_plan=action_plan,
            visualizations=visualizations,
            confidence_score=validated_advice.confidence,
            sources=validated_advice.sources,
            disclaimers=self._generate_disclaimers(user_context)
        )
    
    async def _enrich_context(
        self,
        user_context: UserContext,
        market_context: MarketContext,
        query: str
    ) -> EnrichedContext:
        """Enrich context with additional relevant information"""
        
        # Retrieve relevant documents from vector store
        relevant_docs = await self.vector_store.similarity_search(
            query,
            k=5,
            filter={'user_id': user_context.user_id}
        )
        
        # Get peer comparisons
        peer_data = await self._get_peer_comparisons(user_context)
        
        # Get relevant market insights
        market_insights = await self.market_kb.get_relevant_insights(
            query,
            market_context
        )
        
        # Get historical similar scenarios
        historical_scenarios = await self._find_similar_scenarios(
            user_context,
            market_context
        )
        
        return EnrichedContext(
            user_profile=user_context.profile,
            portfolio_analysis=user_context.portfolio_analysis,
            goal_progress=user_context.goal_progress,
            relevant_history=relevant_docs,
            peer_comparisons=peer_data,
            market_insights=market_insights,
            historical_scenarios=historical_scenarios,
            regulatory_context=await self.regulatory_kb.get_context(
                user_context.profile.get('state', 'CA')
            )
        )
    
    async def _generate_llm_response(
        self,
        task_type: TaskType,
        query: str,
        context: EnrichedContext,
        guidelines: List[str]
    ) -> str:
        """Generate response using appropriate LLM with fallback"""
        
        # Get the appropriate model for this task
        primary_model = self.task_models.get(task_type, LLMProvider.ANTHROPIC_CLAUDE)
        
        # Build the prompt
        prompt = await self.prompt_manager.build_prompt(
            task_type=task_type,
            query=query,
            context=context,
            guidelines=guidelines
        )
        
        # Try primary LLM
        try:
            response = await self._call_llm(
                provider=primary_model,
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            if response:
                return response
        except Exception as e:
            logger.error(f"Primary LLM failed: {e}")
        
        # Fallback to secondary LLM
        fallback_model = (
            LLMProvider.OPENAI_GPT4 
            if primary_model != LLMProvider.OPENAI_GPT4 
            else LLMProvider.ANTHROPIC_CLAUDE
        )
        
        try:
            response = await self._call_llm(
                provider=fallback_model,
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            if response:
                return response
        except Exception as e:
            logger.error(f"Fallback LLM failed: {e}")
        
        # Final fallback to template response
        return self._generate_template_response(task_type, query, context)
    
    async def _call_llm(
        self,
        provider: LLMProvider,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """Call specific LLM provider"""
        
        # Rate limiting
        await self.rate_limiter.check_rate_limit()
        
        try:
            if provider == LLMProvider.ANTHROPIC_CLAUDE and CLAUDE_CLIENT:
                response = await CLAUDE_CLIENT.messages.create(
                    model=provider.value,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            
            elif provider in [LLMProvider.OPENAI_GPT4, LLMProvider.OPENAI_GPT35] and OPENAI_CLIENT:
                response = await OPENAI_CLIENT.chat.completions.create(
                    model=provider.value,
                    messages=[
                        {"role": "system", "content": "You are an expert financial advisor."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"LLM call failed for {provider.value}: {e}")
            raise
        
        return None
    
    async def _classify_task(self, query: str, context: EnrichedContext) -> TaskType:
        """Classify the type of financial task"""
        
        query_lower = query.lower()
        
        # Pattern matching for task classification
        patterns = {
            TaskType.TAX_PLANNING: ['tax', 'deduction', 'irs', '1099', 'w2', 'harvest'],
            TaskType.RETIREMENT_PLANNING: ['retire', '401k', 'ira', 'roth', 'pension', 'social security'],
            TaskType.PORTFOLIO_ANALYSIS: ['portfolio', 'allocation', 'diversification', 'rebalance'],
            TaskType.RISK_ASSESSMENT: ['risk', 'volatility', 'var', 'drawdown', 'hedge'],
            TaskType.MARKET_ANALYSIS: ['market', 'economy', 'inflation', 'rates', 'forecast'],
            TaskType.GOAL_PLANNING: ['goal', 'save', 'target', 'college', 'house', 'wedding'],
            TaskType.REGULATORY_COMPLIANCE: ['compliance', 'regulation', 'sec', 'finra', 'legal']
        }
        
        # Score each task type
        scores = {}
        for task_type, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                scores[task_type] = score
        
        # Return highest scoring task type or default to general advice
        if scores:
            return max(scores, key=scores.get)
        
        return TaskType.GENERAL_ADVICE
    
    async def _validate_advice(
        self,
        raw_advice: str,
        user_context: UserContext,
        guidelines: List[str]
    ) -> ValidatedAdvice:
        """Validate and fact-check the generated advice"""
        
        validation_tasks = [
            self._check_suitability(raw_advice, user_context),
            self._verify_calculations(raw_advice),
            self._check_regulatory_compliance(raw_advice, guidelines),
            self._verify_market_data(raw_advice),
            self._assess_risk_appropriateness(raw_advice, user_context)
        ]
        
        validation_results = await asyncio.gather(*validation_tasks)
        
        # Aggregate validation scores
        confidence_score = sum(r.get('score', 0) for r in validation_results) / len(validation_results)
        
        # Extract and correct any issues
        corrections = []
        for result in validation_results:
            if result.get('issues'):
                corrections.extend(result.get('corrections', []))
        
        # Apply corrections if needed
        if corrections:
            corrected_advice = await self._apply_corrections(
                raw_advice,
                corrections
            )
        else:
            corrected_advice = raw_advice
        
        return ValidatedAdvice(
            narrative=corrected_advice,
            confidence=confidence_score,
            validation_results=validation_results,
            key_points=self._extract_key_points(corrected_advice),
            sources=self._extract_sources(corrected_advice)
        )
    
    async def _generate_action_plan(
        self,
        advice: ValidatedAdvice,
        user_context: UserContext
    ) -> ActionPlan:
        """Generate specific actionable steps"""
        
        # Extract recommendations from advice
        recommendations = self._extract_recommendations(advice.narrative)
        
        action_items = []
        for rec in recommendations:
            # Determine priority
            priority = self._calculate_priority(rec, user_context)
            
            # Calculate impact
            impact = await self._estimate_impact(rec, user_context)
            
            # Generate implementation steps
            steps = await self._generate_implementation_steps(rec)
            
            action_items.append(
                ActionItem(
                    title=rec.get('title', 'Action Item'),
                    description=rec.get('description', ''),
                    priority=priority,
                    impact=impact,
                    steps=steps,
                    timeline=self._estimate_timeline(rec),
                    dependencies=self._identify_dependencies(rec, action_items)
                )
            )
        
        # Order by priority and dependencies
        ordered_items = self._order_action_items(action_items)
        
        return ActionPlan(
            items=ordered_items,
            total_estimated_impact=sum(item.impact for item in ordered_items),
            implementation_timeline=self._calculate_total_timeline(ordered_items)
        )
    
    def _generate_compliance_restricted_response(
        self,
        restrictions: List[str]
    ) -> PersonalizedAdvice:
        """Generate response when compliance restrictions apply"""
        
        return PersonalizedAdvice(
            narrative="I'm unable to provide specific advice due to regulatory restrictions.",
            key_points=["Consult with a licensed financial advisor", "Review regulatory guidelines"],
            action_plan=ActionPlan(items=[], total_estimated_impact=0, implementation_timeline="N/A"),
            visualizations=[],
            confidence_score=1.0,
            sources=[],
            disclaimers=["This response is restricted due to compliance requirements."]
        )
    
    def _generate_disclaimers(self, user_context: UserContext) -> List[str]:
        """Generate appropriate disclaimers"""
        
        disclaimers = [
            "This advice is for informational purposes only and should not be considered as investment advice.",
            "Past performance does not guarantee future results.",
            "Consider consulting with a qualified financial advisor before making investment decisions."
        ]
        
        return disclaimers
    
    # Placeholder methods for validation and analysis
    async def _check_suitability(self, advice: str, user_context: UserContext) -> Dict[str, Any]:
        return {'score': 0.8, 'issues': [], 'corrections': []}
    
    async def _verify_calculations(self, advice: str) -> Dict[str, Any]:
        return {'score': 0.9, 'issues': [], 'corrections': []}
    
    async def _check_regulatory_compliance(self, advice: str, guidelines: List[str]) -> Dict[str, Any]:
        return {'score': 0.95, 'issues': [], 'corrections': []}
    
    async def _verify_market_data(self, advice: str) -> Dict[str, Any]:
        return {'score': 0.85, 'issues': [], 'corrections': []}
    
    async def _assess_risk_appropriateness(self, advice: str, user_context: UserContext) -> Dict[str, Any]:
        return {'score': 0.8, 'issues': [], 'corrections': []}
    
    async def _apply_corrections(self, advice: str, corrections: List[str]) -> str:
        return advice
    
    def _extract_key_points(self, advice: str) -> List[str]:
        return ["Key point 1", "Key point 2", "Key point 3"]
    
    def _extract_sources(self, advice: str) -> List[str]:
        return ["Source 1", "Source 2"]
    
    def _extract_recommendations(self, advice: str) -> List[Dict[str, Any]]:
        return [{"title": "Recommendation 1", "description": "Description"}]
    
    def _calculate_priority(self, recommendation: Dict[str, Any], user_context: UserContext) -> str:
        return "high"
    
    async def _estimate_impact(self, recommendation: Dict[str, Any], user_context: UserContext) -> float:
        return 0.8
    
    async def _generate_implementation_steps(self, recommendation: Dict[str, Any]) -> List[str]:
        return ["Step 1", "Step 2", "Step 3"]
    
    def _estimate_timeline(self, recommendation: Dict[str, Any]) -> str:
        return "1-2 weeks"
    
    def _identify_dependencies(self, recommendation: Dict[str, Any], action_items: List[ActionItem]) -> List[str]:
        return []
    
    def _order_action_items(self, action_items: List[ActionItem]) -> List[ActionItem]:
        return sorted(action_items, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x.priority], reverse=True)
    
    def _calculate_total_timeline(self, action_items: List[ActionItem]) -> str:
        return "2-3 months"
    
    async def _get_peer_comparisons(self, user_context: UserContext) -> Dict[str, Any]:
        return {"peer_group": "similar_age_income", "comparison_data": {}}
    
    async def _find_similar_scenarios(self, user_context: UserContext, market_context: MarketContext) -> List[Dict[str, Any]]:
        return []
    
    def _initialize_vector_store(self):
        """Initialize vector store for RAG"""
        
        try:
            # Initialize embeddings
            embeddings = OpenAIEmbeddings(
                openai_api_key=self.config.get('openai_api_key')
            )
            
            # Try to load existing vector store
            vector_store_path = self.config.get('vector_store_path', './data/vector_store')
            
            try:
                # Load existing FAISS index
                vector_store = FAISS.load_local(vector_store_path, embeddings)
                logger.info("Loaded existing vector store")
            except:
                # Create new vector store with initial documents
                documents = self._load_knowledge_base_documents()
                vector_store = FAISS.from_documents(documents, embeddings)
                # Save for future use
                vector_store.save_local(vector_store_path)
                logger.info("Created new vector store")
            
            return vector_store
        
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return DummyVectorStore()
    
    def _load_knowledge_base_documents(self) -> List[Document]:
        """Load financial knowledge base documents"""
        
        documents = []
        
        # Financial planning fundamentals
        documents.append(Document(
            page_content="""Asset Allocation Strategies:
            - Age-based allocation: 100 minus age in stocks
            - Risk-based allocation: Conservative (20-40% stocks), Moderate (40-60%), Aggressive (60-80%)
            - Rebalancing: Quarterly or when allocation drifts 5% from target
            - Tax-efficient placement: High-growth in Roth, bonds in traditional IRA""",
            metadata={"category": "portfolio_management", "source": "knowledge_base"}
        ))
        
        # Tax optimization strategies
        documents.append(Document(
            page_content="""Tax Loss Harvesting:
            - Sell losing positions to offset gains
            - Avoid wash sale rule (30 days before/after)
            - Harvest up to $3,000 in ordinary income
            - Carry forward unlimited losses
            - Consider tax-managed funds and ETFs""",
            metadata={"category": "tax_planning", "source": "knowledge_base"}
        ))
        
        # Retirement planning
        documents.append(Document(
            page_content="""Retirement Savings Priority:
            1. 401(k) to employer match (free money)
            2. High-interest debt payoff
            3. Max out HSA (triple tax advantage)
            4. Max out Roth IRA
            5. Max out 401(k)
            6. Taxable investment account""",
            metadata={"category": "retirement_planning", "source": "knowledge_base"}
        ))
        
        return documents
    
    def _generate_cache_key(self, query: str, context: UserContext) -> str:
        """Generate cache key for response"""
        
        # Create hash of query and relevant context
        key_parts = [
            query,
            context.user_id,
            str(context.profile.get('risk_tolerance')),
            str(context.profile.get('age')),
            str(context.portfolio_analysis.get('total_value'))
        ]
        
        key_string = '|'.join(key_parts)
        return f"advice:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[PersonalizedAdvice]:
        """Get cached response if available"""
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Check if cache is still valid
                cached_time = datetime.fromisoformat(data.get('timestamp', ''))
                if (datetime.utcnow() - cached_time).seconds < self.cache_ttl:
                    # Reconstruct PersonalizedAdvice object
                    return PersonalizedAdvice(
                        narrative=data['narrative'],
                        key_points=data['key_points'],
                        action_plan=ActionPlan(**data['action_plan']),
                        visualizations=data['visualizations'],
                        confidence_score=data['confidence_score'],
                        sources=data['sources'],
                        disclaimers=data['disclaimers']
                    )
        except Exception as e:
            logger.error(f"Cache retrieval failed: {e}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response: PersonalizedAdvice):
        """Cache response for future use"""
        
        try:
            cache_data = {
                'narrative': response.narrative,
                'key_points': response.key_points,
                'action_plan': {
                    'items': [{
                        'title': item.title,
                        'description': item.description,
                        'priority': item.priority,
                        'impact': item.impact,
                        'steps': item.steps,
                        'timeline': item.timeline,
                        'dependencies': item.dependencies
                    } for item in response.action_plan.items],
                    'total_estimated_impact': response.action_plan.total_estimated_impact,
                    'implementation_timeline': response.action_plan.implementation_timeline
                },
                'visualizations': response.visualizations,
                'confidence_score': response.confidence_score,
                'sources': response.sources,
                'disclaimers': response.disclaimers,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data)
            )
        except Exception as e:
            logger.error(f"Cache storage failed: {e}")
    
    def _generate_template_response(self, task_type: TaskType, query: str, context: EnrichedContext) -> str:
        """Generate template-based fallback response"""
        
        templates = {
            TaskType.GENERAL_ADVICE: """Based on your financial profile, I recommend focusing on:
                1. Building an emergency fund (3-6 months expenses)
                2. Maximizing employer 401(k) match
                3. Paying off high-interest debt
                4. Diversifying investments across asset classes""",
            
            TaskType.TAX_PLANNING: """For tax optimization, consider:
                1. Maximizing tax-advantaged account contributions
                2. Tax-loss harvesting in taxable accounts
                3. Reviewing itemized vs standard deduction
                4. Planning charitable contributions""",
            
            TaskType.RETIREMENT_PLANNING: """For retirement planning:
                1. Target saving 10-15% of income
                2. Take full advantage of employer match
                3. Consider Roth conversions in low-income years
                4. Review Social Security claiming strategies"""
        }
        
        return templates.get(task_type, "Please consult with a financial advisor for personalized advice.")
    
    def _initialize_tools(self):
        return []

class RegulatoryKnowledgeBase:
    """Enhanced regulatory compliance knowledge base"""
    
    def __init__(self):
        self.regulations = self._load_regulations()
        self.restricted_terms = self._load_restricted_terms()
        self.required_disclaimers = self._load_disclaimers()
    
    async def check_compliance(
        self, 
        query: str, 
        user_context: UserContext,
        compliance_level: ComplianceLevel = ComplianceLevel.STANDARD
    ) -> Dict[str, Any]:
        """Check query and context for compliance issues"""
        
        is_compliant = True
        restrictions = []
        guidelines = []
        
        # Check for restricted terms
        query_lower = query.lower()
        for term, restriction in self.restricted_terms.items():
            if term in query_lower:
                if compliance_level == ComplianceLevel.STRICT:
                    is_compliant = False
                    restrictions.append(restriction)
                else:
                    guidelines.append(f"Caution: {restriction}")
        
        # Check for guaranteed returns language
        if any(word in query_lower for word in ['guarantee', 'assured', 'risk-free']):
            guidelines.append("Avoid guarantees - all investments carry risk")
        
        # Check for specific product recommendations
        if compliance_level == ComplianceLevel.STRICT:
            if any(word in query_lower for word in ['buy', 'sell', 'trade']):
                guidelines.append("Provide educational information only, not specific trade recommendations")
        
        # Add required disclaimers based on topic
        disclaimers = self._get_required_disclaimers(query, compliance_level)
        guidelines.extend(disclaimers)
        
        return {
            'is_compliant': is_compliant,
            'restrictions': restrictions,
            'guidelines': guidelines
        }
    
    async def get_context(self, state: str) -> Dict[str, Any]:
        """Get state and federal regulatory context"""
        
        federal_regs = [
            "SEC Regulation Best Interest",
            "FINRA Rule 2111 (Suitability)",
            "Investment Advisers Act of 1940",
            "Dodd-Frank Act provisions"
        ]
        
        state_regs = {
            'CA': ['California Consumer Privacy Act', 'CA Department of Business Oversight rules'],
            'NY': ['NY BitLicense requirements', 'Martin Act provisions'],
            'TX': ['Texas State Securities Board rules'],
        }
        
        return {
            'state_regulations': state_regs.get(state, []),
            'federal_regulations': federal_regs
        }
    
    def _load_regulations(self) -> Dict[str, Any]:
        """Load regulatory rules"""
        
        return {
            'fiduciary_duty': 'Act in client\'s best interest',
            'suitability': 'Recommendations must be suitable for client',
            'disclosure': 'Disclose all material conflicts of interest',
            'recordkeeping': 'Maintain records of all recommendations'
        }
    
    def _load_restricted_terms(self) -> Dict[str, str]:
        """Load restricted terms and their restrictions"""
        
        return {
            'insider': 'Cannot provide insider trading advice',
            'guaranteed': 'Cannot guarantee investment returns',
            'hot tip': 'Cannot provide unverified investment tips',
            'sure thing': 'No investment is a sure thing'
        }
    
    def _load_disclaimers(self) -> List[str]:
        """Load standard disclaimers"""
        
        return [
            "This is educational information only, not personalized investment advice",
            "Past performance does not guarantee future results",
            "All investments carry risk including potential loss of principal",
            "Consult with a qualified financial advisor before making investment decisions",
            "Tax implications vary by individual situation"
        ]
    
    def _get_required_disclaimers(self, query: str, compliance_level: ComplianceLevel) -> List[str]:
        """Get disclaimers required for specific query"""
        
        disclaimers = []
        query_lower = query.lower()
        
        if compliance_level == ComplianceLevel.STRICT:
            disclaimers.extend(self.required_disclaimers)
        
        # Add topic-specific disclaimers
        if 'crypto' in query_lower or 'bitcoin' in query_lower:
            disclaimers.append("Cryptocurrency investments are highly volatile and speculative")
        
        if 'option' in query_lower or 'derivative' in query_lower:
            disclaimers.append("Options and derivatives carry significant risk of loss")
        
        if 'margin' in query_lower or 'leverage' in query_lower:
            disclaimers.append("Margin trading amplifies both gains and losses")
        
        return disclaimers

class MarketKnowledgeBase:
    async def get_relevant_insights(self, query: str, market_context: MarketContext) -> Dict[str, Any]:
        return {'insights': [], 'trends': []}

class DummyVectorStore:
    async def similarity_search(self, query: str, k: int, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

class PromptManager:
    """Manages prompts for different financial advisory tasks"""
    
    def __init__(self):
        self.prompts = self._load_prompts()
    
    async def build_prompt(
        self,
        task_type: TaskType,
        query: str,
        context: EnrichedContext,
        guidelines: List[str]
    ) -> str:
        """Build task-specific prompt with context"""
        
        base_prompt = self.prompts.get(task_type, self.prompts[TaskType.GENERAL_ADVICE])
        
        # Format context for prompt
        context_str = self._format_context(context)
        guidelines_str = '\n'.join(f"- {g}" for g in guidelines) if guidelines else "None"
        
        return base_prompt.format(
            query=query,
            context=context_str,
            guidelines=guidelines_str,
            user_age=context.user_profile.get('age', 'unknown'),
            risk_tolerance=context.user_profile.get('risk_tolerance', 'moderate'),
            portfolio_value=context.portfolio_analysis.get('total_value', 0),
            goals=self._format_goals(context.goal_progress)
        )
    
    def _load_prompts(self) -> Dict[TaskType, str]:
        """Load prompt templates for each task type"""
        
        return {
            TaskType.GENERAL_ADVICE: """You are an expert financial advisor providing personalized advice.

User Query: {query}

User Context:
{context}

Regulatory Guidelines:
{guidelines}

Provide comprehensive financial advice that:
1. Directly addresses the user's question
2. Considers their age ({user_age}), risk tolerance ({risk_tolerance}), and portfolio value (${portfolio_value:,.0f})
3. Aligns with their financial goals: {goals}
4. Includes specific, actionable recommendations
5. Explains reasoning using chain-of-thought
6. Identifies risks and considerations
7. Remains compliant with regulations
8. Uses clear, accessible language

Structure your response with:
- Executive Summary (2-3 sentences)
- Situation Analysis
- Recommendations (numbered list)
- Risk Considerations
- Next Steps
- Important Disclaimers""",
            
            TaskType.TAX_PLANNING: """You are a tax-focused financial advisor.

User Query: {query}

Tax Context:
{context}

Guidelines: {guidelines}

Provide tax optimization advice focusing on:
1. Tax-efficient investment strategies
2. Tax loss harvesting opportunities
3. Retirement account optimization
4. Deduction maximization
5. State and federal considerations

Ensure all advice is general in nature and recommend consulting a tax professional for specific situations.""",
            
            TaskType.RETIREMENT_PLANNING: """You are a retirement planning specialist.

User Query: {query}

Retirement Context:
{context}

Current Age: {user_age}
Portfolio Value: ${portfolio_value:,.0f}
Risk Tolerance: {risk_tolerance}

Provide retirement planning advice covering:
1. Savings rate recommendations
2. Account type optimization (401k, IRA, Roth)
3. Asset allocation by age
4. Social Security optimization
5. Healthcare planning
6. Estate planning considerations

Include specific calculations and projections where appropriate."""
        }
    
    def _format_context(self, context: EnrichedContext) -> str:
        """Format context for inclusion in prompt"""
        
        sections = []
        
        if context.user_profile:
            sections.append(f"User Profile: {json.dumps(context.user_profile, indent=2)}")
        
        if context.portfolio_analysis:
            sections.append(f"Portfolio: {json.dumps(context.portfolio_analysis, indent=2)}")
        
        if context.goal_progress:
            sections.append(f"Goals: {json.dumps(context.goal_progress, indent=2)}")
        
        return '\n\n'.join(sections)
    
    def _format_goals(self, goals: List[Dict[str, Any]]) -> str:
        """Format goals for prompt"""
        
        if not goals:
            return "No specific goals defined"
        
        goal_strs = []
        for goal in goals[:3]:  # Top 3 goals
            goal_strs.append(
                f"{goal.get('name', 'Goal')}: ${goal.get('target_amount', 0):,.0f} "
                f"by {goal.get('target_date', 'unspecified')}"
            )
        
        return ', '.join(goal_strs)

class RateLimiter:
    """Rate limiting for LLM calls"""
    
    def __init__(self, max_requests: int = 60):
        self.max_requests = max_requests
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self):
        """Check and enforce rate limits"""
        
        async with self.lock:
            now = datetime.utcnow()
            # Remove requests older than 1 minute
            self.requests = [
                req for req in self.requests 
                if (now - req).seconds < 60
            ]
            
            if len(self.requests) >= self.max_requests:
                wait_time = 60 - (now - self.requests[0]).seconds
                if wait_time > 0:
                    logger.warning(f"Rate limit reached, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
            
            self.requests.append(now)
