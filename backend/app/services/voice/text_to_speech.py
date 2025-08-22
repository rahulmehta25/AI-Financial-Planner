"""Text-to-Speech Service Implementation."""

import asyncio
import hashlib
import io
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from google.cloud import texttospeech_v1 as texttospeech
import boto3
import pyttsx3
from pydub import AudioSegment

from .config import VoiceSettings, Language, VoiceGender, VOICE_PROFILES

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """Service for converting text to speech with multiple provider support."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize the text-to-speech service."""
        self.settings = settings or VoiceSettings()
        
        # Initialize providers
        self.google_client = None
        self.polly_client = None
        self.offline_engine = None
        
        # Audio cache for frequently used phrases
        self.audio_cache: Dict[str, Dict] = {}
        self.cache_max_size = 100
        self.cache_ttl = timedelta(hours=24)
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize TTS providers based on available credentials."""
        # Google Cloud Text-to-Speech
        if self.settings.google_cloud_credentials_path:
            try:
                self.google_client = texttospeech.TextToSpeechClient()
                logger.info("Google Cloud Text-to-Speech initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google TTS: {e}")
        
        # Amazon Polly
        if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
            try:
                self.polly_client = boto3.client(
                    'polly',
                    region_name=self.settings.aws_region,
                    aws_access_key_id=self.settings.aws_access_key_id,
                    aws_secret_access_key=self.settings.aws_secret_access_key
                )
                logger.info("Amazon Polly initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Amazon Polly: {e}")
        
        # Offline TTS engine (pyttsx3)
        try:
            self.offline_engine = pyttsx3.init()
            self._configure_offline_engine()
            logger.info("Offline TTS engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize offline TTS: {e}")
    
    def _configure_offline_engine(self):
        """Configure the offline TTS engine settings."""
        if not self.offline_engine:
            return
        
        # Set voice properties
        voices = self.offline_engine.getProperty('voices')
        
        # Try to find a voice matching the preferred gender
        gender_map = {
            VoiceGender.MALE: 'male',
            VoiceGender.FEMALE: 'female',
            VoiceGender.NEUTRAL: None
        }
        
        preferred_gender = gender_map.get(self.settings.default_voice_gender)
        if preferred_gender and voices:
            for voice in voices:
                if preferred_gender in voice.name.lower():
                    self.offline_engine.setProperty('voice', voice.id)
                    break
        
        # Set speech rate and volume
        self.offline_engine.setProperty(
            'rate',
            int(150 * self.settings.default_speech_rate)  # Base rate ~150 wpm
        )
        self.offline_engine.setProperty('volume', 1.0)
    
    async def synthesize_speech(
        self,
        text: str,
        language: Optional[Language] = None,
        voice_gender: Optional[VoiceGender] = None,
        voice_profile: Optional[str] = None,
        output_format: str = "mp3",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to convert to speech
            language: Target language
            voice_gender: Preferred voice gender
            voice_profile: Voice profile name (e.g., 'professional', 'friendly')
            output_format: Audio output format (mp3, wav, ogg)
            use_cache: Whether to use cached audio if available
            
        Returns:
            Audio data and metadata
        """
        # Validate and prepare parameters
        text = self._preprocess_text(text)
        if len(text) > self.settings.max_text_length:
            text = text[:self.settings.max_text_length]
        
        language = language or self.settings.default_language
        voice_gender = voice_gender or self.settings.default_voice_gender
        
        # Apply voice profile if specified
        if voice_profile and voice_profile in VOICE_PROFILES:
            profile = VOICE_PROFILES[voice_profile]
            voice_gender = profile.get("gender", voice_gender)
        
        # Check cache
        if use_cache and self.settings.cache_audio_responses:
            cached = self._get_cached_audio(text, language, voice_gender, output_format)
            if cached:
                return cached
        
        # Try synthesis with available providers
        result = None
        
        # Try Google Cloud TTS first
        if self.google_client:
            result = await self._synthesize_with_google(
                text, language, voice_gender, voice_profile, output_format
            )
        
        # Try Amazon Polly if Google fails or unavailable
        if not result and self.polly_client:
            result = await self._synthesize_with_polly(
                text, language, voice_gender, voice_profile, output_format
            )
        
        # Fallback to offline TTS
        if not result:
            result = await self._synthesize_offline(
                text, language, voice_gender, output_format
            )
        
        # Cache the result
        if result and result.get("success") and use_cache:
            self._cache_audio(
                text, language, voice_gender, output_format, result
            )
        
        return result
    
    async def _synthesize_with_google(
        self,
        text: str,
        language: Language,
        voice_gender: VoiceGender,
        voice_profile: Optional[str],
        output_format: str
    ) -> Optional[Dict[str, Any]]:
        """Synthesize using Google Cloud Text-to-Speech."""
        try:
            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code=language.value,
                ssml_gender=texttospeech.SsmlVoiceGender[voice_gender.value]
            )
            
            # Select audio configuration
            audio_config = texttospeech.AudioConfig(
                audio_encoding=self._get_google_audio_encoding(output_format),
                speaking_rate=self.settings.default_speech_rate,
                pitch=self.settings.default_pitch
            )
            
            # Build synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Perform synthesis
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.google_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            )
            
            return {
                "success": True,
                "audio_data": response.audio_content,
                "format": output_format,
                "provider": "google_cloud",
                "language": language.value,
                "voice_gender": voice_gender.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return None
    
    async def _synthesize_with_polly(
        self,
        text: str,
        language: Language,
        voice_gender: VoiceGender,
        voice_profile: Optional[str],
        output_format: str
    ) -> Optional[Dict[str, Any]]:
        """Synthesize using Amazon Polly."""
        try:
            # Map voice gender to Polly voice ID
            voice_id = self._get_polly_voice_id(language, voice_gender)
            
            # Map output format
            output_format_map = {
                "mp3": "mp3",
                "wav": "pcm",
                "ogg": "ogg_vorbis"
            }
            polly_format = output_format_map.get(output_format, "mp3")
            
            # Synthesize speech
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.polly_client.synthesize_speech(
                    Text=text,
                    OutputFormat=polly_format,
                    VoiceId=voice_id,
                    Engine=self.settings.polly_engine,
                    LanguageCode=language.value
                )
            )
            
            # Read audio stream
            audio_data = response['AudioStream'].read()
            
            # Convert PCM to WAV if needed
            if polly_format == "pcm":
                audio_data = self._pcm_to_wav(audio_data)
            
            return {
                "success": True,
                "audio_data": audio_data,
                "format": output_format,
                "provider": "amazon_polly",
                "language": language.value,
                "voice_gender": voice_gender.value,
                "voice_id": voice_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Amazon Polly error: {e}")
            return None
    
    async def _synthesize_offline(
        self,
        text: str,
        language: Language,
        voice_gender: VoiceGender,
        output_format: str
    ) -> Dict[str, Any]:
        """Synthesize using offline TTS engine."""
        try:
            if not self.offline_engine:
                raise Exception("Offline TTS engine not available")
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Synthesize
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.offline_engine.save_to_file(text, tmp_path)
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.offline_engine.runAndWait
            )
            
            # Read audio data
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            import os
            os.remove(tmp_path)
            
            return {
                "success": True,
                "audio_data": audio_data,
                "format": output_format,
                "provider": "offline",
                "language": language.value,
                "voice_gender": voice_gender.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Offline TTS error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better TTS output."""
        # Expand common financial abbreviations
        replacements = {
            "401k": "401 K",
            "IRA": "I R A",
            "ETF": "E T F",
            "YTD": "year to date",
            "QTD": "quarter to date",
            "MTD": "month to date",
            "ROI": "return on investment",
            "P/E": "price to earnings",
            "APR": "annual percentage rate",
            "APY": "annual percentage yield",
            "CD": "certificate of deposit",
            "FDIC": "F D I C",
            "SIPC": "S I P C"
        }
        
        for abbr, expansion in replacements.items():
            text = text.replace(abbr, expansion)
        
        # Handle currency symbols
        text = text.replace("$", "dollars ")
        text = text.replace("€", "euros ")
        text = text.replace("£", "pounds ")
        text = text.replace("¥", "yen ")
        
        # Handle percentages
        text = text.replace("%", " percent")
        
        return text
    
    def _get_google_audio_encoding(self, output_format: str):
        """Get Google Cloud TTS audio encoding enum."""
        encoding_map = {
            "mp3": texttospeech.AudioEncoding.MP3,
            "wav": texttospeech.AudioEncoding.LINEAR16,
            "ogg": texttospeech.AudioEncoding.OGG_OPUS
        }
        return encoding_map.get(output_format, texttospeech.AudioEncoding.MP3)
    
    def _get_polly_voice_id(self, language: Language, voice_gender: VoiceGender) -> str:
        """Get Amazon Polly voice ID based on language and gender."""
        # Map of language and gender to Polly voice IDs
        voice_map = {
            (Language.ENGLISH, VoiceGender.FEMALE): "Joanna",
            (Language.ENGLISH, VoiceGender.MALE): "Matthew",
            (Language.ENGLISH, VoiceGender.NEUTRAL): "Ivy",
            (Language.SPANISH, VoiceGender.FEMALE): "Penelope",
            (Language.SPANISH, VoiceGender.MALE): "Miguel",
            (Language.FRENCH, VoiceGender.FEMALE): "Celine",
            (Language.FRENCH, VoiceGender.MALE): "Mathieu",
            (Language.GERMAN, VoiceGender.FEMALE): "Marlene",
            (Language.GERMAN, VoiceGender.MALE): "Hans",
            (Language.ITALIAN, VoiceGender.FEMALE): "Carla",
            (Language.ITALIAN, VoiceGender.MALE): "Giorgio",
            (Language.PORTUGUESE, VoiceGender.FEMALE): "Vitoria",
            (Language.PORTUGUESE, VoiceGender.MALE): "Ricardo",
            (Language.JAPANESE, VoiceGender.FEMALE): "Mizuki",
            (Language.JAPANESE, VoiceGender.MALE): "Takumi",
            (Language.KOREAN, VoiceGender.FEMALE): "Seoyeon",
            (Language.CHINESE, VoiceGender.FEMALE): "Zhiyu"
        }
        
        return voice_map.get((language, voice_gender), "Joanna")
    
    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """Convert PCM audio data to WAV format."""
        audio = AudioSegment(
            pcm_data,
            sample_width=2,
            frame_rate=16000,
            channels=1
        )
        
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        return wav_io.getvalue()
    
    def _get_cache_key(
        self,
        text: str,
        language: Language,
        voice_gender: VoiceGender,
        output_format: str
    ) -> str:
        """Generate cache key for audio data."""
        key_data = f"{text}:{language.value}:{voice_gender.value}:{output_format}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_cached_audio(
        self,
        text: str,
        language: Language,
        voice_gender: VoiceGender,
        output_format: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached audio if available and not expired."""
        cache_key = self._get_cache_key(text, language, voice_gender, output_format)
        
        if cache_key in self.audio_cache:
            cached = self.audio_cache[cache_key]
            
            # Check if cache is still valid
            created_at = datetime.fromisoformat(cached["timestamp"])
            if datetime.utcnow() - created_at < self.cache_ttl:
                logger.info(f"Using cached audio for: {text[:50]}...")
                cached["from_cache"] = True
                return cached
            else:
                # Remove expired cache
                del self.audio_cache[cache_key]
        
        return None
    
    def _cache_audio(
        self,
        text: str,
        language: Language,
        voice_gender: VoiceGender,
        output_format: str,
        audio_data: Dict[str, Any]
    ):
        """Cache audio data for future use."""
        # Check cache size limit
        if len(self.audio_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = min(
                self.audio_cache.keys(),
                key=lambda k: self.audio_cache[k]["timestamp"]
            )
            del self.audio_cache[oldest_key]
        
        cache_key = self._get_cache_key(text, language, voice_gender, output_format)
        self.audio_cache[cache_key] = audio_data
    
    async def synthesize_ssml(
        self,
        ssml: str,
        language: Optional[Language] = None,
        voice_gender: Optional[VoiceGender] = None,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Synthesize SSML (Speech Synthesis Markup Language) to speech.
        
        Args:
            ssml: SSML markup text
            language: Target language
            voice_gender: Preferred voice gender
            output_format: Audio output format
            
        Returns:
            Audio data and metadata
        """
        language = language or self.settings.default_language
        voice_gender = voice_gender or self.settings.default_voice_gender
        
        if self.google_client:
            try:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=language.value,
                    ssml_gender=texttospeech.SsmlVoiceGender[voice_gender.value]
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=self._get_google_audio_encoding(output_format)
                )
                
                synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.google_client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )
                )
                
                return {
                    "success": True,
                    "audio_data": response.audio_content,
                    "format": output_format,
                    "provider": "google_cloud",
                    "language": language.value,
                    "voice_gender": voice_gender.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"SSML synthesis error: {e}")
        
        # Fallback to plain text synthesis
        # Strip SSML tags for fallback
        import re
        plain_text = re.sub(r'<[^>]+>', '', ssml)
        return await self.synthesize_speech(
            plain_text, language, voice_gender, output_format=output_format
        )
    
    def get_available_voices(self) -> Dict[str, List[Dict]]:
        """Get list of available voices from all providers."""
        voices = {
            "google_cloud": [],
            "amazon_polly": [],
            "offline": []
        }
        
        # Google Cloud voices
        if self.google_client:
            try:
                response = self.google_client.list_voices()
                for voice in response.voices:
                    voices["google_cloud"].append({
                        "name": voice.name,
                        "language": voice.language_codes[0] if voice.language_codes else None,
                        "gender": voice.ssml_gender.name if voice.ssml_gender else None
                    })
            except Exception as e:
                logger.error(f"Error listing Google voices: {e}")
        
        # Amazon Polly voices
        if self.polly_client:
            try:
                response = self.polly_client.describe_voices()
                for voice in response.get('Voices', []):
                    voices["amazon_polly"].append({
                        "id": voice['Id'],
                        "name": voice['Name'],
                        "language": voice['LanguageCode'],
                        "gender": voice['Gender']
                    })
            except Exception as e:
                logger.error(f"Error listing Polly voices: {e}")
        
        # Offline voices
        if self.offline_engine:
            try:
                for voice in self.offline_engine.getProperty('voices'):
                    voices["offline"].append({
                        "id": voice.id,
                        "name": voice.name,
                        "language": voice.languages[0] if voice.languages else None
                    })
            except Exception as e:
                logger.error(f"Error listing offline voices: {e}")
        
        return voices