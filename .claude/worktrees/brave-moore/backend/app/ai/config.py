"""Configuration for AI narrative generation system."""

from typing import Dict, List, Optional
from pydantic import BaseSettings, Field
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    FALLBACK = "fallback"


class Language(str, Enum):
    """Supported languages for narrative generation."""
    ENGLISH = "en"
    SPANISH = "es"
    CHINESE = "zh"


class AIConfig(BaseSettings):
    """AI system configuration."""
    
    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Model Configuration
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_model: str = "claude-3-opus-20240229"
    
    # Temperature settings for controlled output
    narrative_temperature: float = 0.3  # Lower for more consistent output
    summary_temperature: float = 0.2    # Even lower for factual summaries
    
    # Token limits
    max_input_tokens: int = 4000
    max_output_tokens: int = 2000
    
    # Safety settings
    enable_content_filtering: bool = True
    enable_prompt_validation: bool = True
    enable_output_validation: bool = True
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Cache configuration
    enable_response_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # A/B Testing
    enable_ab_testing: bool = True
    ab_test_percentage: float = 0.1  # 10% of requests
    
    # Audit settings
    enable_audit_logging: bool = True
    audit_log_path: str = "/var/log/financial_ai/audit.log"
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    
    # Template settings
    template_version: str = "v1.0.0"
    strict_template_mode: bool = True  # Enforce template-only responses
    
    # Language settings
    default_language: Language = Language.ENGLISH
    supported_languages: List[Language] = [
        Language.ENGLISH,
        Language.SPANISH,
        Language.CHINESE
    ]
    
    # Compliance settings
    include_disclaimers: bool = True
    disclaimer_position: str = "both"  # "start", "end", or "both"
    
    # Numerical validation
    verify_numerical_consistency: bool = True
    numerical_tolerance: float = 0.01  # 1% tolerance for rounding
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
ai_config = AIConfig()