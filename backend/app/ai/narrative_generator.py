"""Main narrative generator with dual LLM integration."""

import asyncio
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
import openai
import anthropic
from langchain.cache import InMemoryCache
import logging
import random

from .config import AIConfig, LLMProvider, Language
from .template_manager import TemplateManager, TemplateType
from .safety_controller import SafetyController
from .audit_logger import AuditLogger


class NarrativeGenerator:
    """Main class for generating AI narratives with safety controls."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        """Initialize narrative generator.
        
        Args:
            config: AI configuration object
        """
        self.config = config or AIConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.template_manager = TemplateManager()
        self.safety_controller = SafetyController()
        self.audit_logger = AuditLogger()
        
        # Initialize LLM clients
        self._initialize_llm_clients()
        
        # Initialize cache
        self.cache = InMemoryCache() if self.config.enable_response_caching else None
        
        # Track metrics for A/B testing
        self.ab_test_metrics = {
            "openai": {"requests": 0, "latency": [], "errors": 0},
            "anthropic": {"requests": 0, "latency": [], "errors": 0}
        }
    
    def _initialize_llm_clients(self):
        """Initialize LLM API clients."""
        # OpenAI client
        if self.config.openai_api_key:
            openai.api_key = self.config.openai_api_key
            self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
        else:
            self.openai_client = None
            self.logger.warning("OpenAI API key not configured")
        
        # Anthropic client
        if self.config.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        else:
            self.anthropic_client = None
            self.logger.warning("Anthropic API key not configured")
    
    async def generate_narrative(self,
                                template_type: TemplateType,
                                data: Dict[str, Any],
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None,
                                language: Language = Language.ENGLISH,
                                provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """Generate a narrative using the specified template and data.
        
        Args:
            template_type: Type of narrative template
            data: Data for template variables
            user_id: User identifier for logging
            session_id: Session identifier
            language: Target language
            provider: Specific LLM provider to use
            
        Returns:
            Dictionary with narrative and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Render template with data
            template_text = self.template_manager.render_template(
                template_type, data, language.value
            )
            
            # Step 2: Check cache
            cache_key = self._generate_cache_key(template_type, data, language)
            if self.cache:
                cached_response = await self._check_cache(cache_key)
                if cached_response:
                    await self.audit_logger.log_cache_event(True, cache_key)
                    return cached_response
                else:
                    await self.audit_logger.log_cache_event(False, cache_key)
            
            # Step 3: Validate prompt safety
            is_valid, error = self.safety_controller.validate_prompt(template_text)
            if not is_valid:
                await self.audit_logger.log_safety_violation(
                    "prompt_validation", template_text, user_id
                )
                return self._create_fallback_response(template_type, data, error)
            
            # Step 4: Log prompt
            await self.audit_logger.log_prompt(
                template_text, template_type.value, user_id, session_id
            )
            
            # Step 5: Choose provider (A/B testing if enabled)
            if not provider:
                provider = self._select_provider()
            
            # Step 6: Generate narrative with LLM
            narrative, tokens_used, latency = await self._generate_with_llm(
                provider, template_text, template_type
            )
            
            # Step 7: Validate output safety
            is_valid, error = self.safety_controller.validate_output(
                narrative, template_type.value, data
            )
            if not is_valid:
                await self.audit_logger.log_safety_violation(
                    "output_validation", narrative, user_id
                )
                narrative = self.safety_controller.sanitize_output(narrative)
            
            # Step 8: Add disclaimers
            narrative_with_disclaimers = self.safety_controller.add_disclaimers(
                narrative, template_type.value, self.config.disclaimer_position
            )
            
            # Step 9: Log response
            await self.audit_logger.log_response(
                narrative_with_disclaimers,
                self.config.openai_model if provider == LLMProvider.OPENAI else self.config.anthropic_model,
                provider.value,
                tokens_used,
                latency * 1000,
                user_id,
                session_id
            )
            
            # Step 10: Cache response
            response = {
                "narrative": narrative_with_disclaimers,
                "template_type": template_type.value,
                "language": language.value,
                "provider": provider.value,
                "tokens_used": tokens_used,
                "generation_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self.cache:
                await self._cache_response(cache_key, response)
            
            # Step 11: Track A/B test metrics
            if self.config.enable_ab_testing:
                await self._track_ab_metrics(provider, latency, False)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating narrative: {str(e)}")
            
            # Track error for A/B testing
            if provider and self.config.enable_ab_testing:
                await self._track_ab_metrics(provider, 0, True)
            
            # Return fallback response
            return self._create_fallback_response(template_type, data, str(e))
    
    async def _generate_with_llm(self,
                                provider: LLMProvider,
                                prompt: str,
                                template_type: TemplateType) -> Tuple[str, int, float]:
        """Generate narrative using specified LLM provider.
        
        Args:
            provider: LLM provider to use
            prompt: Rendered template prompt
            template_type: Type of template
            
        Returns:
            Tuple of (narrative, tokens_used, latency_seconds)
        """
        start_time = time.time()
        
        # Create system prompt for structured generation
        system_prompt = self._create_system_prompt(template_type)
        
        try:
            if provider == LLMProvider.OPENAI and self.openai_client:
                narrative, tokens = await self._call_openai(system_prompt, prompt)
            elif provider == LLMProvider.ANTHROPIC and self.anthropic_client:
                narrative, tokens = await self._call_anthropic(system_prompt, prompt)
            else:
                # Use fallback
                return self._generate_fallback_narrative(template_type, prompt), 0, 0
            
            latency = time.time() - start_time
            
            # Log API call
            await self.audit_logger.log_api_call(
                provider.value,
                self.config.openai_model if provider == LLMProvider.OPENAI else self.config.anthropic_model,
                "completions",
                200,
                latency * 1000
            )
            
            return narrative, tokens, latency
            
        except Exception as e:
            latency = time.time() - start_time
            
            # Log API error
            await self.audit_logger.log_api_call(
                provider.value,
                self.config.openai_model if provider == LLMProvider.OPENAI else self.config.anthropic_model,
                "completions",
                500,
                latency * 1000,
                str(e)
            )
            
            # Try other provider or fallback
            if provider == LLMProvider.OPENAI and self.anthropic_client:
                return await self._generate_with_llm(LLMProvider.ANTHROPIC, prompt, template_type)
            elif provider == LLMProvider.ANTHROPIC and self.openai_client:
                return await self._generate_with_llm(LLMProvider.OPENAI, prompt, template_type)
            else:
                return self._generate_fallback_narrative(template_type, prompt), 0, latency
    
    async def _call_openai(self, system_prompt: str, user_prompt: str) -> Tuple[str, int]:
        """Call OpenAI API.
        
        Args:
            system_prompt: System instructions
            user_prompt: User prompt
            
        Returns:
            Tuple of (response_text, tokens_used)
        """
        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config.narrative_temperature,
            max_tokens=self.config.max_output_tokens,
            response_format={"type": "text"}
        )
        
        return response.choices[0].message.content, response.usage.total_tokens
    
    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> Tuple[str, int]:
        """Call Anthropic API.
        
        Args:
            system_prompt: System instructions
            user_prompt: User prompt
            
        Returns:
            Tuple of (response_text, tokens_used)
        """
        message = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model=self.config.anthropic_model,
            max_tokens=self.config.max_output_tokens,
            temperature=self.config.narrative_temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Calculate approximate tokens (Anthropic doesn't provide exact count)
        tokens = len(user_prompt.split()) + len(message.content[0].text.split())
        
        return message.content[0].text, tokens * 1.3  # Approximate token count
    
    def _create_system_prompt(self, template_type: TemplateType) -> str:
        """Create system prompt for LLM.
        
        Args:
            template_type: Type of template
            
        Returns:
            System prompt string
        """
        return f"""You are a financial planning assistant providing educational information.

CRITICAL RULES:
1. NEVER provide specific investment advice or recommendations
2. ALWAYS maintain the structure and format of the provided template
3. ONLY fill in the template variables with the provided data
4. DO NOT add new information not present in the template
5. Maintain a professional, educational tone
6. Include appropriate disclaimers about not being financial advice
7. Verify all numbers match the provided data exactly
8. Use clear, simple language accessible to non-experts

Template Type: {template_type.value}

Your response should follow the exact structure of the template, only replacing
placeholders with actual values. Do not deviate from the template format."""
    
    def _select_provider(self) -> LLMProvider:
        """Select LLM provider with A/B testing logic.
        
        Returns:
            Selected provider
        """
        # Check if both providers are available
        if not self.openai_client and not self.anthropic_client:
            return LLMProvider.FALLBACK
        elif not self.openai_client:
            return LLMProvider.ANTHROPIC
        elif not self.anthropic_client:
            return LLMProvider.OPENAI
        
        # A/B testing logic
        if self.config.enable_ab_testing:
            if random.random() < self.config.ab_test_percentage:
                # Use alternative provider for testing
                return LLMProvider.ANTHROPIC
        
        # Default to OpenAI
        return LLMProvider.OPENAI
    
    def _generate_cache_key(self,
                           template_type: TemplateType,
                           data: Dict[str, Any],
                           language: Language) -> str:
        """Generate cache key for response.
        
        Args:
            template_type: Template type
            data: Template data
            language: Language
            
        Returns:
            Cache key string
        """
        key_data = {
            "template": template_type.value,
            "data_hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
            "language": language.value,
            "version": self.config.template_version
        }
        
        return hashlib.sha256(json.dumps(key_data).encode()).hexdigest()
    
    async def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check cache for existing response.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached response or None
        """
        # Simple in-memory cache check
        # In production, this would use Redis or similar
        return None  # Placeholder
    
    async def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache a response.
        
        Args:
            cache_key: Cache key
            response: Response to cache
        """
        # Simple in-memory cache storage
        # In production, this would use Redis with TTL
        pass  # Placeholder
    
    def _generate_fallback_narrative(self,
                                    template_type: TemplateType,
                                    prompt: str) -> str:
        """Generate fallback narrative without LLM.
        
        Args:
            template_type: Template type
            prompt: Original prompt
            
        Returns:
            Fallback narrative text
        """
        # Return the template as-is with a note
        return f"{prompt}\n\n[Note: This is a template-based response. For enhanced narratives, please ensure AI services are configured.]"
    
    def _create_fallback_response(self,
                                 template_type: TemplateType,
                                 data: Dict[str, Any],
                                 error: str) -> Dict[str, Any]:
        """Create fallback response when generation fails.
        
        Args:
            template_type: Template type
            data: Template data
            error: Error message
            
        Returns:
            Fallback response dictionary
        """
        # Render basic template without AI enhancement
        try:
            narrative = self.template_manager.render_template(
                template_type, data, validate=False
            )
            narrative = self.safety_controller.add_disclaimers(
                narrative, template_type.value
            )
        except:
            narrative = "Unable to generate narrative at this time. Please try again later."
        
        return {
            "narrative": narrative,
            "template_type": template_type.value,
            "language": Language.ENGLISH.value,
            "provider": LLMProvider.FALLBACK.value,
            "tokens_used": 0,
            "generation_time_ms": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "fallback": True
        }
    
    async def _track_ab_metrics(self,
                               provider: LLMProvider,
                               latency: float,
                               error: bool):
        """Track metrics for A/B testing.
        
        Args:
            provider: Provider used
            latency: Response latency
            error: Whether an error occurred
        """
        if provider.value in self.ab_test_metrics:
            metrics = self.ab_test_metrics[provider.value]
            metrics["requests"] += 1
            if error:
                metrics["errors"] += 1
            else:
                metrics["latency"].append(latency)
    
    async def get_ab_test_results(self) -> Dict[str, Any]:
        """Get A/B test results.
        
        Returns:
            A/B test metrics and analysis
        """
        results = {}
        
        for provider, metrics in self.ab_test_metrics.items():
            avg_latency = sum(metrics["latency"]) / len(metrics["latency"]) if metrics["latency"] else 0
            error_rate = metrics["errors"] / metrics["requests"] if metrics["requests"] > 0 else 0
            
            results[provider] = {
                "total_requests": metrics["requests"],
                "average_latency_seconds": avg_latency,
                "error_rate": f"{error_rate * 100:.2f}%",
                "success_rate": f"{(1 - error_rate) * 100:.2f}%"
            }
        
        return results
    
    async def generate_batch_narratives(self,
                                       requests: List[Dict[str, Any]],
                                       user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate multiple narratives in batch.
        
        Args:
            requests: List of narrative requests
            user_id: User identifier
            
        Returns:
            List of generated narratives
        """
        tasks = []
        
        for request in requests:
            task = self.generate_narrative(
                template_type=TemplateType(request["template_type"]),
                data=request["data"],
                user_id=user_id,
                language=Language(request.get("language", "en")),
                provider=LLMProvider(request.get("provider")) if request.get("provider") else None
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)