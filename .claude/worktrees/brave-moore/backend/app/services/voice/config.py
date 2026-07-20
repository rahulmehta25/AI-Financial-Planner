"""Voice Service Configuration."""

from typing import Dict, List, Optional
from pydantic import BaseSettings, Field
from enum import Enum


class VoiceProvider(str, Enum):
    """Supported voice service providers."""
    GOOGLE_CLOUD = "google_cloud"
    AMAZON_POLLY = "amazon_polly"
    AZURE = "azure"
    OFFLINE = "offline"


class Language(str, Enum):
    """Supported languages for voice services."""
    ENGLISH = "en-US"
    SPANISH = "es-ES"
    FRENCH = "fr-FR"
    GERMAN = "de-DE"
    ITALIAN = "it-IT"
    PORTUGUESE = "pt-BR"
    CHINESE = "zh-CN"
    JAPANESE = "ja-JP"
    KOREAN = "ko-KR"
    ARABIC = "ar-SA"
    HINDI = "hi-IN"
    RUSSIAN = "ru-RU"


class VoiceGender(str, Enum):
    """Voice gender options."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    NEUTRAL = "NEUTRAL"


class VoiceSettings(BaseSettings):
    """Voice service configuration settings."""
    
    # Google Cloud Speech-to-Text
    google_cloud_project_id: Optional[str] = Field(None, env="GOOGLE_CLOUD_PROJECT_ID")
    google_cloud_credentials_path: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    google_speech_model: str = Field("latest_long", env="GOOGLE_SPEECH_MODEL")
    google_speech_use_enhanced: bool = Field(True, env="GOOGLE_SPEECH_USE_ENHANCED")
    
    # Amazon Polly
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    polly_engine: str = Field("neural", env="POLLY_ENGINE")  # neural or standard
    
    # Azure Cognitive Services
    azure_speech_key: Optional[str] = Field(None, env="AZURE_SPEECH_KEY")
    azure_speech_region: Optional[str] = Field(None, env="AZURE_SPEECH_REGION")
    
    # Default Settings
    default_language: Language = Field(Language.ENGLISH, env="DEFAULT_LANGUAGE")
    default_voice_gender: VoiceGender = Field(VoiceGender.NEUTRAL, env="DEFAULT_VOICE_GENDER")
    default_speech_rate: float = Field(1.0, env="DEFAULT_SPEECH_RATE")  # 0.5 to 2.0
    default_pitch: float = Field(0.0, env="DEFAULT_PITCH")  # -20 to 20 semitones
    
    # Audio Settings
    audio_sample_rate: int = Field(16000, env="AUDIO_SAMPLE_RATE")
    audio_encoding: str = Field("LINEAR16", env="AUDIO_ENCODING")
    max_recording_duration: int = Field(60, env="MAX_RECORDING_DURATION")  # seconds
    silence_threshold: int = Field(500, env="SILENCE_THRESHOLD")
    silence_duration: float = Field(1.5, env="SILENCE_DURATION")  # seconds
    
    # Voice Command Settings
    command_timeout: int = Field(10, env="COMMAND_TIMEOUT")  # seconds
    wake_word: str = Field("hey finance", env="WAKE_WORD")
    confirmation_required: bool = Field(True, env="CONFIRMATION_REQUIRED")
    
    # Accessibility Settings
    screen_reader_enabled: bool = Field(True, env="SCREEN_READER_ENABLED")
    high_contrast_mode: bool = Field(False, env="HIGH_CONTRAST_MODE")
    keyboard_navigation: bool = Field(True, env="KEYBOARD_NAVIGATION")
    voice_feedback_enabled: bool = Field(True, env="VOICE_FEEDBACK_ENABLED")
    
    # Multi-language Support
    supported_languages: List[Language] = Field(
        default=[
            Language.ENGLISH, Language.SPANISH, Language.FRENCH,
            Language.GERMAN, Language.CHINESE, Language.JAPANESE
        ],
        env="SUPPORTED_LANGUAGES"
    )
    auto_detect_language: bool = Field(True, env="AUTO_DETECT_LANGUAGE")
    
    # Performance Settings
    enable_streaming: bool = Field(True, env="ENABLE_STREAMING")
    cache_audio_responses: bool = Field(True, env="CACHE_AUDIO_RESPONSES")
    max_concurrent_sessions: int = Field(100, env="MAX_CONCURRENT_SESSIONS")
    
    # Security Settings
    enable_profanity_filter: bool = Field(True, env="ENABLE_PROFANITY_FILTER")
    enable_pii_redaction: bool = Field(True, env="ENABLE_PII_REDACTION")
    max_text_length: int = Field(5000, env="MAX_TEXT_LENGTH")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Voice profiles for different contexts
VOICE_PROFILES: Dict[str, Dict] = {
    "professional": {
        "gender": VoiceGender.NEUTRAL,
        "speech_rate": 0.95,
        "pitch": -2.0,
        "style": "businesslike"
    },
    "friendly": {
        "gender": VoiceGender.FEMALE,
        "speech_rate": 1.0,
        "pitch": 2.0,
        "style": "conversational"
    },
    "assistive": {
        "gender": VoiceGender.NEUTRAL,
        "speech_rate": 0.85,
        "pitch": 0.0,
        "style": "clear"
    },
    "emergency": {
        "gender": VoiceGender.MALE,
        "speech_rate": 1.2,
        "pitch": 0.0,
        "style": "urgent"
    }
}


# Financial domain vocabulary for improved recognition
FINANCIAL_VOCABULARY = [
    "portfolio", "investment", "retirement", "401k", "IRA", "Roth IRA",
    "stocks", "bonds", "mutual funds", "ETF", "dividend", "yield",
    "asset allocation", "diversification", "risk tolerance", "compound interest",
    "expense ratio", "capital gains", "tax loss harvesting", "rebalancing",
    "dollar cost averaging", "Monte Carlo simulation", "Sharpe ratio",
    "standard deviation", "volatility", "beta", "alpha", "correlation",
    "emergency fund", "budget", "savings", "debt", "mortgage", "inflation",
    "Social Security", "pension", "annuity", "estate planning", "beneficiary",
    "fiduciary", "financial advisor", "robo-advisor", "target date fund"
]


# Voice command intents
VOICE_INTENTS = {
    "navigation": [
        "go to", "open", "show", "navigate", "take me to", "display"
    ],
    "query": [
        "what is", "how much", "tell me about", "show me", "calculate", "analyze"
    ],
    "action": [
        "add", "create", "update", "delete", "save", "submit", "invest", "withdraw"
    ],
    "help": [
        "help", "assist", "guide", "explain", "what can you do", "how do I"
    ],
    "confirmation": [
        "yes", "no", "confirm", "cancel", "correct", "incorrect", "approve", "reject"
    ],
    "correction": [
        "change", "modify", "edit", "fix", "correct", "update"
    ]
}


# Accessibility shortcuts
VOICE_SHORTCUTS = {
    "portfolio summary": "Show portfolio overview with current values and performance",
    "retirement status": "Display retirement goal progress and projections",
    "recent transactions": "List recent investment transactions",
    "market update": "Provide market summary and portfolio impact",
    "goal progress": "Show progress on all financial goals",
    "risk assessment": "Display current risk profile and recommendations",
    "tax summary": "Show year-to-date tax implications",
    "next steps": "Provide personalized action items and recommendations"
}


voice_settings = VoiceSettings()