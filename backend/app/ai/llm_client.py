"""LLM Client for integrating OpenAI and Anthropic APIs."""

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import openai
import anthropic
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import redis.asyncio as redis
from pydantic import BaseModel, Field

from .config import AIConfig, LLMProvider, Language
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class NarrativeType(str, Enum):
    """Types of narratives that can be generated."""
    SIMULATION_SUMMARY = "simulation_summary"
    TRADE_OFF_ANALYSIS = "trade_off_analysis"
    RECOMMENDATION = "recommendation"
    RISK_ASSESSMENT = "risk_assessment"
    GOAL_PROGRESS = "goal_progress"
    PORTFOLIO_REVIEW = "portfolio_review"


class LLMResponse(BaseModel):
    """Structured response from LLM."""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    cached: bool = False
    version: str = "v1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: AIConfig, audit_logger: AuditLogger):
        self.config = config
        self.audit_logger = audit_logger
        self.provider = LLMProvider.FALLBACK
        
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Generate narrative from prompt."""
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate API key is configured and working."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT-4 client implementation."""
    
    def __init__(self, config: AIConfig, audit_logger: AuditLogger):
        super().__init__(config, audit_logger)
        self.provider = LLMProvider.OPENAI
        
        if config.openai_api_key:
            self.client = AsyncOpenAI(api_key=config.openai_api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Generate narrative using OpenAI GPT-4."""
        if not self.client:
            raise ValueError("OpenAI client not configured")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional financial advisor assistant. Provide clear, accurate, and compliant financial guidance."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "text"}
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Log the generation
            await self.audit_logger.log_generation(
                provider=self.provider,
                model=self.config.openai_model,
                prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                tokens_used=tokens_used,
                success=True
            )
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=self.config.openai_model,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            await self.audit_logger.log_generation(
                provider=self.provider,
                model=self.config.openai_model,
                prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                tokens_used=0,
                success=False,
                error=str(e)
            )
            raise
    
    async def validate_api_key(self) -> bool:
        """Validate OpenAI API key."""
        if not self.client:
            return False
        
        try:
            # Test with a minimal request
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI API key validation failed: {str(e)}")
            return False


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client implementation."""
    
    def __init__(self, config: AIConfig, audit_logger: AuditLogger):
        super().__init__(config, audit_logger)
        self.provider = LLMProvider.ANTHROPIC
        
        if config.anthropic_api_key:
            self.client = AsyncAnthropic(api_key=config.anthropic_api_key)
        else:
            self.client = None
            logger.warning("Anthropic API key not configured")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Generate narrative using Anthropic Claude."""
        if not self.client:
            raise ValueError("Anthropic client not configured")
        
        try:
            response = await self.client.messages.create(
                model=self.config.anthropic_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system="You are a professional financial advisor assistant. Provide clear, accurate, and compliant financial guidance.",
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Log the generation
            await self.audit_logger.log_generation(
                provider=self.provider,
                model=self.config.anthropic_model,
                prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                tokens_used=tokens_used,
                success=True
            )
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=self.config.anthropic_model,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            await self.audit_logger.log_generation(
                provider=self.provider,
                model=self.config.anthropic_model,
                prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                tokens_used=0,
                success=False,
                error=str(e)
            )
            raise
    
    async def validate_api_key(self) -> bool:
        """Validate Anthropic API key."""
        if not self.client:
            return False
        
        try:
            # Test with a minimal request
            await self.client.messages.create(
                model="claude-3-haiku-20240307",  # Use cheaper model for testing
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic API key validation failed: {str(e)}")
            return False


class FallbackClient(BaseLLMClient):
    """Fallback client for when APIs are unavailable."""
    
    def __init__(self, config: AIConfig, audit_logger: AuditLogger):
        super().__init__(config, audit_logger)
        self.provider = LLMProvider.FALLBACK
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """Generate fallback narrative."""
        # Extract narrative type from kwargs if provided
        narrative_type = kwargs.get('narrative_type', NarrativeType.SIMULATION_SUMMARY)
        
        # Generate appropriate fallback based on type
        fallback_narratives = {
            NarrativeType.SIMULATION_SUMMARY: self._get_simulation_fallback(),
            NarrativeType.TRADE_OFF_ANALYSIS: self._get_tradeoff_fallback(),
            NarrativeType.RECOMMENDATION: self._get_recommendation_fallback(),
            NarrativeType.RISK_ASSESSMENT: self._get_risk_fallback(),
            NarrativeType.GOAL_PROGRESS: self._get_progress_fallback(),
            NarrativeType.PORTFOLIO_REVIEW: self._get_portfolio_fallback()
        }
        
        content = fallback_narratives.get(
            narrative_type,
            "Analysis complete. Please review the numerical results above for detailed information."
        )
        
        await self.audit_logger.log_generation(
            provider=self.provider,
            model="fallback",
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
            tokens_used=0,
            success=True,
            metadata={"fallback_type": narrative_type}
        )
        
        return LLMResponse(
            content=content,
            provider=self.provider,
            model="fallback",
            tokens_used=0
        )
    
    async def validate_api_key(self) -> bool:
        """Fallback is always available."""
        return True
    
    def _get_simulation_fallback(self) -> str:
        """Get fallback for simulation summary."""
        return """Based on the simulation results, your financial plan shows projected outcomes across multiple scenarios. 
        The analysis considers market volatility, inflation, and your specific goals. 
        Please review the detailed numerical results above for specific projections and probabilities."""
    
    def _get_tradeoff_fallback(self) -> str:
        """Get fallback for trade-off analysis."""
        return """The analysis identifies key trade-offs in your financial strategy. 
        Balancing risk and return, immediate needs and long-term goals requires careful consideration. 
        The numerical analysis above provides specific metrics for each scenario."""
    
    def _get_recommendation_fallback(self) -> str:
        """Get fallback for recommendations."""
        return """Based on the analysis, consider reviewing your current allocation and risk tolerance. 
        The simulation results suggest opportunities for optimization. 
        Consult with a qualified financial advisor for personalized recommendations."""
    
    def _get_risk_fallback(self) -> str:
        """Get fallback for risk assessment."""
        return """Risk assessment complete. The analysis evaluates market risk, inflation risk, and longevity risk. 
        Your current strategy shows specific risk metrics in the numerical results above. 
        Regular monitoring and rebalancing can help manage these risks."""
    
    def _get_progress_fallback(self) -> str:
        """Get fallback for goal progress."""
        return """Goal progress analysis shows your trajectory toward financial objectives. 
        Current projections and milestone achievements are detailed in the numerical results. 
        Continued monitoring will help ensure you stay on track."""
    
    def _get_portfolio_fallback(self) -> str:
        """Get fallback for portfolio review."""
        return """Portfolio review complete. Asset allocation, performance metrics, and rebalancing opportunities 
        are identified in the analysis above. Regular reviews help maintain alignment with your goals."""


class LLMClientManager:
    """Manages multiple LLM clients with fallback and caching."""
    
    def __init__(self, config: AIConfig, audit_logger: AuditLogger):
        self.config = config
        self.audit_logger = audit_logger
        
        # Initialize clients
        self.clients: Dict[LLMProvider, BaseLLMClient] = {
            LLMProvider.OPENAI: OpenAIClient(config, audit_logger),
            LLMProvider.ANTHROPIC: AnthropicClient(config, audit_logger),
            LLMProvider.FALLBACK: FallbackClient(config, audit_logger)
        }
        
        # Initialize Redis for caching if enabled
        self.redis_client = None
        if config.enable_response_caching:
            asyncio.create_task(self._init_redis())
        
        # A/B testing state
        self.ab_test_counter = 0
    
    async def _init_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {str(e)}. Caching disabled.")
            self.redis_client = None
    
    async def generate(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        narrative_type: NarrativeType = NarrativeType.SIMULATION_SUMMARY,
        language: Language = Language.ENGLISH,
        use_cache: bool = True,
        **kwargs
    ) -> LLMResponse:
        """Generate narrative with automatic fallback and caching."""
        
        # Check cache first
        if use_cache and self.redis_client:
            cached_response = await self._get_cached_response(prompt, language)
            if cached_response:
                return cached_response
        
        # Determine provider (A/B testing if enabled)
        if provider is None:
            provider = await self._select_provider()
        
        # Try primary provider
        response = None
        tried_providers = []
        
        for attempt_provider in [provider, LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.FALLBACK]:
            if attempt_provider in tried_providers:
                continue
            
            tried_providers.append(attempt_provider)
            client = self.clients[attempt_provider]
            
            try:
                # Validate API key first
                if attempt_provider != LLMProvider.FALLBACK:
                    if not await client.validate_api_key():
                        logger.warning(f"{attempt_provider} API key validation failed")
                        continue
                
                # Generate response
                response = await client.generate(
                    prompt=prompt,
                    temperature=kwargs.get('temperature', self.config.narrative_temperature),
                    max_tokens=kwargs.get('max_tokens', self.config.max_output_tokens),
                    narrative_type=narrative_type
                )
                
                # Cache successful response
                if use_cache and self.redis_client and response:
                    await self._cache_response(prompt, language, response)
                
                break
                
            except Exception as e:
                logger.error(f"{attempt_provider} failed: {str(e)}")
                continue
        
        if not response:
            # This should never happen as fallback should always work
            raise RuntimeError("All LLM providers failed including fallback")
        
        return response
    
    async def _select_provider(self) -> LLMProvider:
        """Select provider with A/B testing logic."""
        if not self.config.enable_ab_testing:
            # Default to OpenAI if available, else Anthropic
            if await self.clients[LLMProvider.OPENAI].validate_api_key():
                return LLMProvider.OPENAI
            elif await self.clients[LLMProvider.ANTHROPIC].validate_api_key():
                return LLMProvider.ANTHROPIC
            else:
                return LLMProvider.FALLBACK
        
        # A/B testing logic
        self.ab_test_counter += 1
        if self.ab_test_counter % 10 < self.config.ab_test_percentage * 10:
            # Use alternative provider for A/B test
            if await self.clients[LLMProvider.ANTHROPIC].validate_api_key():
                return LLMProvider.ANTHROPIC
        
        # Default provider
        if await self.clients[LLMProvider.OPENAI].validate_api_key():
            return LLMProvider.OPENAI
        elif await self.clients[LLMProvider.ANTHROPIC].validate_api_key():
            return LLMProvider.ANTHROPIC
        else:
            return LLMProvider.FALLBACK
    
    async def _get_cached_response(self, prompt: str, language: Language) -> Optional[LLMResponse]:
        """Get cached response if available."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"narrative:{hashlib.sha256(f'{prompt}:{language}'.encode()).hexdigest()}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                response = LLMResponse(**data)
                response.cached = True
                logger.info(f"Cache hit for narrative")
                return response
                
        except Exception as e:
            logger.error(f"Cache retrieval failed: {str(e)}")
        
        return None
    
    async def _cache_response(self, prompt: str, language: Language, response: LLMResponse):
        """Cache response for future use."""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"narrative:{hashlib.sha256(f'{prompt}:{language}'.encode()).hexdigest()}"
            cache_data = response.json()
            
            await self.redis_client.setex(
                cache_key,
                self.config.cache_ttl_seconds,
                cache_data
            )
            logger.info(f"Cached narrative response")
            
        except Exception as e:
            logger.error(f"Cache storage failed: {str(e)}")
    
    async def validate_all_providers(self) -> Dict[LLMProvider, bool]:
        """Validate all configured providers."""
        results = {}
        for provider, client in self.clients.items():
            results[provider] = await client.validate_api_key()
        return results