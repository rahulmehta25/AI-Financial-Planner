"""Azure Speech Services Integration for Speech Recognition and Text-to-Speech."""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import uuid

import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import (
    SpeechConfig, 
    SpeechRecognizer,
    SpeechSynthesizer,
    AudioConfig,
    KeywordRecognitionModel,
    PhraseListGrammar,
    CancellationReason,
    ResultReason,
    PropertyId
)
from azure.cognitiveservices.speech.audio import (
    AudioStreamFormat,
    PushAudioInputStream,
    AudioStreamContainerFormat
)

from .config import VoiceSettings, Language, VoiceGender, FINANCIAL_VOCABULARY

logger = logging.getLogger(__name__)


class AzureSpeechService:
    """Azure Speech Services integration for comprehensive voice capabilities."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize Azure Speech Services."""
        self.settings = settings or VoiceSettings()
        
        # Azure configuration
        self.speech_config = None
        self.speech_recognizer = None
        self.speech_synthesizer = None
        self.keyword_model = None
        
        # Initialize if credentials available
        if self.settings.azure_speech_key and self.settings.azure_speech_region:
            self._initialize_azure_services()
        
        # Recognition state
        self.is_recognizing = False
        self.recognition_session_id = None
        
        # Continuous recognition handlers
        self.recognition_callbacks = {
            'recognized': [],
            'recognizing': [],
            'session_started': [],
            'session_stopped': [],
            'canceled': []
        }
    
    def _initialize_azure_services(self):
        """Initialize Azure Speech configuration and services."""
        try:
            # Create speech configuration
            self.speech_config = SpeechConfig(
                subscription=self.settings.azure_speech_key,
                region=self.settings.azure_speech_region
            )
            
            # Set default language
            self.speech_config.speech_recognition_language = self.settings.default_language.value
            
            # Enable dictation mode for better punctuation
            self.speech_config.enable_dictation()
            
            # Set profanity filter
            if self.settings.enable_profanity_filter:
                self.speech_config.set_profanity(speechsdk.ProfanityOption.Masked)
            
            # Configure output format for detailed results
            self.speech_config.output_format = speechsdk.OutputFormat.Detailed
            
            # Set service properties for improved accuracy
            self.speech_config.set_service_property(
                "punctuation", "implicit",
                speechsdk.ServicePropertyChannel.UriQueryParameter
            )
            
            logger.info("Azure Speech Services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Speech Services: {e}")
            self.speech_config = None
    
    async def recognize_once(
        self,
        audio_data: bytes,
        language: Optional[Language] = None,
        enable_translation: bool = False,
        target_languages: Optional[List[Language]] = None
    ) -> Dict[str, Any]:
        """
        Perform one-shot speech recognition.
        
        Args:
            audio_data: Audio data in bytes
            language: Source language for recognition
            enable_translation: Enable speech translation
            target_languages: Target languages for translation
            
        Returns:
            Recognition result with transcript and metadata
        """
        if not self.speech_config:
            return {
                "success": False,
                "error": "Azure Speech Services not configured"
            }
        
        try:
            # Create audio stream
            stream_format = AudioStreamFormat(
                samples_per_second=self.settings.audio_sample_rate,
                bits_per_sample=16,
                channels=1
            )
            
            audio_stream = PushAudioInputStream(stream_format)
            audio_stream.write(audio_data)
            audio_stream.close()
            
            audio_config = AudioConfig(stream=audio_stream)
            
            # Configure language
            if language:
                self.speech_config.speech_recognition_language = language.value
            
            # Create recognizer with phrase list for financial terms
            recognizer = SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Add phrase list grammar for financial vocabulary
            phrase_list = PhraseListGrammar.from_recognizer(recognizer)
            for term in FINANCIAL_VOCABULARY:
                phrase_list.addPhrase(term)
            
            # Perform recognition
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                recognizer.recognize_once
            )
            
            # Process result
            if result.reason == ResultReason.RecognizedSpeech:
                return {
                    "success": True,
                    "transcript": result.text,
                    "confidence": result.json.get("NBest", [{}])[0].get("Confidence", 0),
                    "language": language.value if language else self.settings.default_language.value,
                    "duration": result.duration,
                    "offset": result.offset,
                    "provider": "azure",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif result.reason == ResultReason.NoMatch:
                return {
                    "success": False,
                    "error": "Speech not recognized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif result.reason == ResultReason.Canceled:
                cancellation = result.cancellation_details
                return {
                    "success": False,
                    "error": f"Recognition canceled: {cancellation.reason}",
                    "error_details": cancellation.error_details,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Azure recognition error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def start_continuous_recognition(
        self,
        language: Optional[Language] = None,
        enable_interim_results: bool = True
    ) -> str:
        """
        Start continuous speech recognition.
        
        Args:
            language: Recognition language
            enable_interim_results: Include partial recognition results
            
        Returns:
            Session ID for the recognition session
        """
        if not self.speech_config:
            raise Exception("Azure Speech Services not configured")
        
        if self.is_recognizing:
            return self.recognition_session_id
        
        try:
            # Configure language
            if language:
                self.speech_config.speech_recognition_language = language.value
            
            # Create recognizer for microphone input
            self.speech_recognizer = SpeechRecognizer(
                speech_config=self.speech_config
            )
            
            # Add phrase list for financial terms
            phrase_list = PhraseListGrammar.from_recognizer(self.speech_recognizer)
            for term in FINANCIAL_VOCABULARY:
                phrase_list.addPhrase(term)
            
            # Set up event handlers
            self.speech_recognizer.recognizing.connect(
                lambda evt: self._handle_recognizing(evt)
            )
            self.speech_recognizer.recognized.connect(
                lambda evt: self._handle_recognized(evt)
            )
            self.speech_recognizer.session_started.connect(
                lambda evt: self._handle_session_started(evt)
            )
            self.speech_recognizer.session_stopped.connect(
                lambda evt: self._handle_session_stopped(evt)
            )
            self.speech_recognizer.canceled.connect(
                lambda evt: self._handle_canceled(evt)
            )
            
            # Start continuous recognition
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.speech_recognizer.start_continuous_recognition
            )
            
            self.is_recognizing = True
            self.recognition_session_id = str(uuid.uuid4())
            
            logger.info(f"Started continuous recognition session: {self.recognition_session_id}")
            
            return self.recognition_session_id
            
        except Exception as e:
            logger.error(f"Failed to start continuous recognition: {e}")
            raise
    
    async def stop_continuous_recognition(self):
        """Stop continuous speech recognition."""
        if not self.is_recognizing or not self.speech_recognizer:
            return
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.speech_recognizer.stop_continuous_recognition
            )
            
            self.is_recognizing = False
            self.recognition_session_id = None
            
            logger.info("Stopped continuous recognition")
            
        except Exception as e:
            logger.error(f"Failed to stop continuous recognition: {e}")
    
    def _handle_recognizing(self, evt):
        """Handle interim recognition results."""
        for callback in self.recognition_callbacks['recognizing']:
            callback({
                "text": evt.result.text,
                "offset": evt.result.offset,
                "duration": evt.result.duration,
                "is_final": False,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _handle_recognized(self, evt):
        """Handle final recognition results."""
        if evt.result.reason == ResultReason.RecognizedSpeech:
            for callback in self.recognition_callbacks['recognized']:
                callback({
                    "text": evt.result.text,
                    "offset": evt.result.offset,
                    "duration": evt.result.duration,
                    "is_final": True,
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    def _handle_session_started(self, evt):
        """Handle session started event."""
        for callback in self.recognition_callbacks['session_started']:
            callback({
                "session_id": evt.session_id,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _handle_session_stopped(self, evt):
        """Handle session stopped event."""
        for callback in self.recognition_callbacks['session_stopped']:
            callback({
                "session_id": evt.session_id,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _handle_canceled(self, evt):
        """Handle cancellation event."""
        for callback in self.recognition_callbacks['canceled']:
            callback({
                "reason": evt.cancellation_details.reason,
                "error_details": evt.cancellation_details.error_details,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def add_recognition_callback(self, event_type: str, callback: callable):
        """Add a callback for recognition events."""
        if event_type in self.recognition_callbacks:
            self.recognition_callbacks[event_type].append(callback)
    
    async def synthesize_speech_azure(
        self,
        text: str,
        voice_name: Optional[str] = None,
        language: Optional[Language] = None,
        style: Optional[str] = None,
        style_degree: float = 1.0,
        output_format: str = "audio-16khz-128kbitrate-mono-mp3"
    ) -> Dict[str, Any]:
        """
        Synthesize speech using Azure Neural TTS.
        
        Args:
            text: Text to synthesize
            voice_name: Azure voice name (e.g., "en-US-JennyNeural")
            language: Target language
            style: Speaking style (e.g., "cheerful", "sad", "angry")
            style_degree: Style intensity (0.01 to 2.0)
            output_format: Audio output format
            
        Returns:
            Audio data and metadata
        """
        if not self.speech_config:
            return {
                "success": False,
                "error": "Azure Speech Services not configured"
            }
        
        try:
            # Configure synthesis
            if language:
                self.speech_config.speech_synthesis_language = language.value
            
            if voice_name:
                self.speech_config.speech_synthesis_voice_name = voice_name
            else:
                # Use default neural voice for the language
                voice_map = {
                    Language.ENGLISH: "en-US-JennyNeural",
                    Language.SPANISH: "es-ES-ElviraNeural",
                    Language.FRENCH: "fr-FR-DeniseNeural",
                    Language.GERMAN: "de-DE-KatjaNeural",
                    Language.CHINESE: "zh-CN-XiaoxiaoNeural",
                    Language.JAPANESE: "ja-JP-NanamiNeural"
                }
                self.speech_config.speech_synthesis_voice_name = voice_map.get(
                    language or self.settings.default_language,
                    "en-US-JennyNeural"
                )
            
            # Set output format
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat[output_format.replace("-", "_")]
            )
            
            # Create synthesizer
            synthesizer = SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # Return audio data instead of playing
            )
            
            # Build SSML if style is specified
            if style:
                ssml = self._build_ssml_with_style(text, voice_name, style, style_degree)
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    synthesizer.speak_ssml,
                    ssml
                )
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    synthesizer.speak_text,
                    text
                )
            
            # Process result
            if result.reason == ResultReason.SynthesizingAudioCompleted:
                return {
                    "success": True,
                    "audio_data": result.audio_data,
                    "duration": len(result.audio_data) / (16000 * 2),  # Approximate duration
                    "format": output_format,
                    "provider": "azure",
                    "voice": self.speech_config.speech_synthesis_voice_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif result.reason == ResultReason.Canceled:
                cancellation = result.cancellation_details
                return {
                    "success": False,
                    "error": f"Synthesis canceled: {cancellation.reason}",
                    "error_details": cancellation.error_details,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Azure synthesis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _build_ssml_with_style(self, text: str, voice: str, style: str, degree: float) -> str:
        """Build SSML with speaking style."""
        return f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice}">
                <mstts:express-as style="{style}" styledegree="{degree}">
                    {text}
                </mstts:express-as>
            </voice>
        </speak>
        """
    
    async def detect_language_azure(self, audio_data: bytes) -> Language:
        """
        Detect language from audio using Azure.
        
        Args:
            audio_data: Audio data in bytes
            
        Returns:
            Detected language
        """
        if not self.speech_config:
            return self.settings.default_language
        
        try:
            # Configure for language detection
            auto_detect_config = speechsdk.AutoDetectSourceLanguageConfig(
                languages=[lang.value for lang in self.settings.supported_languages]
            )
            
            # Create audio stream
            stream_format = AudioStreamFormat(
                samples_per_second=self.settings.audio_sample_rate,
                bits_per_sample=16,
                channels=1
            )
            
            audio_stream = PushAudioInputStream(stream_format)
            audio_stream.write(audio_data)
            audio_stream.close()
            
            audio_config = AudioConfig(stream=audio_stream)
            
            # Create recognizer with auto-detect
            recognizer = speechsdk.SourceLanguageRecognizer(
                speech_config=self.speech_config,
                auto_detect_source_language_config=auto_detect_config,
                audio_config=audio_config
            )
            
            # Perform recognition
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                recognizer.recognize_once
            )
            
            if result.reason == ResultReason.RecognizedSpeech:
                detected_lang = result.properties.get(
                    PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
                )
                
                # Map to Language enum
                for lang in Language:
                    if lang.value == detected_lang:
                        return lang
            
            return self.settings.default_language
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return self.settings.default_language
    
    async def setup_wake_word(
        self,
        wake_word_path: str,
        callback: callable
    ) -> bool:
        """
        Setup wake word detection.
        
        Args:
            wake_word_path: Path to wake word model file
            callback: Function to call when wake word detected
            
        Returns:
            True if setup successful
        """
        if not self.speech_config:
            return False
        
        try:
            # Load keyword model
            self.keyword_model = KeywordRecognitionModel(wake_word_path)
            
            # Create keyword recognizer
            keyword_recognizer = speechsdk.KeywordRecognizer()
            
            # Set up callback
            keyword_recognizer.recognized.connect(
                lambda evt: callback({
                    "wake_word_detected": True,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            # Start recognition
            await asyncio.get_event_loop().run_in_executor(
                None,
                keyword_recognizer.recognize_once_async,
                self.keyword_model
            )
            
            logger.info("Wake word detection configured")
            return True
            
        except Exception as e:
            logger.error(f"Wake word setup error: {e}")
            return False