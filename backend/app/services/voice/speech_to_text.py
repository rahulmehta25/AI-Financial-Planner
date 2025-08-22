"""Speech-to-Text Service Implementation."""

import asyncio
import io
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np

from google.cloud import speech_v1
from google.cloud.speech_v1 import types as speech_types
import speech_recognition as sr
import webrtcvad
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from .config import VoiceSettings, Language, FINANCIAL_VOCABULARY

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """Service for converting speech to text with multiple provider support."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize the speech-to-text service."""
        self.settings = settings or VoiceSettings()
        self.recognizer = sr.Recognizer()
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        
        # Initialize Google Cloud Speech client if credentials available
        self.google_client = None
        if self.settings.google_cloud_credentials_path:
            try:
                self.google_client = speech_v1.SpeechClient()
                logger.info("Google Cloud Speech client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Speech: {e}")
        
        # Configure recognizer settings
        self.recognizer.energy_threshold = self.settings.silence_threshold
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = self.settings.silence_duration
        
        # Speech contexts for improved recognition
        self.speech_contexts = self._build_speech_contexts()
        
        # Recognition history for context
        self.recognition_history: List[Dict] = []
    
    def _build_speech_contexts(self) -> List[speech_types.SpeechContext]:
        """Build speech contexts for improved financial domain recognition."""
        contexts = []
        
        # Financial vocabulary context
        if FINANCIAL_VOCABULARY:
            contexts.append(
                speech_types.SpeechContext(
                    phrases=FINANCIAL_VOCABULARY,
                    boost=10.0
                )
            )
        
        # Number and currency context
        contexts.append(
            speech_types.SpeechContext(
                phrases=[
                    "$", "dollars", "cents", "percent", "percentage",
                    "thousand", "million", "billion", "K", "M", "B"
                ],
                boost=5.0
            )
        )
        
        return contexts
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: Optional[Language] = None,
        enable_punctuation: bool = True,
        enable_word_confidence: bool = True,
        enable_speaker_diarization: bool = False,
        max_alternatives: int = 3
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio data in bytes
            language: Language code for transcription
            enable_punctuation: Add punctuation to transcript
            enable_word_confidence: Include word-level confidence scores
            enable_speaker_diarization: Identify different speakers
            max_alternatives: Maximum number of alternative transcriptions
            
        Returns:
            Transcription result with metadata
        """
        language = language or self.settings.default_language
        
        try:
            # Try Google Cloud Speech first if available
            if self.google_client:
                result = await self._transcribe_with_google(
                    audio_data, language, enable_punctuation,
                    enable_word_confidence, enable_speaker_diarization,
                    max_alternatives
                )
                if result:
                    return result
            
            # Fallback to offline speech recognition
            return await self._transcribe_offline(audio_data, language)
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _transcribe_with_google(
        self,
        audio_data: bytes,
        language: Language,
        enable_punctuation: bool,
        enable_word_confidence: bool,
        enable_speaker_diarization: bool,
        max_alternatives: int
    ) -> Optional[Dict[str, Any]]:
        """Transcribe using Google Cloud Speech-to-Text."""
        try:
            # Prepare audio for Google Cloud Speech
            audio = speech_types.RecognitionAudio(content=audio_data)
            
            # Configure recognition settings
            config = speech_types.RecognitionConfig(
                encoding=speech_types.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.settings.audio_sample_rate,
                language_code=language.value,
                max_alternatives=max_alternatives,
                enable_automatic_punctuation=enable_punctuation,
                enable_word_confidence=enable_word_confidence,
                enable_speaker_diarization=enable_speaker_diarization,
                diarization_speaker_count=2 if enable_speaker_diarization else 0,
                speech_contexts=self.speech_contexts,
                model=self.settings.google_speech_model,
                use_enhanced=self.settings.google_speech_use_enhanced,
                profanity_filter=self.settings.enable_profanity_filter
            )
            
            # Perform transcription
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.google_client.recognize(config=config, audio=audio)
            )
            
            if not response.results:
                return None
            
            # Process results
            result = response.results[0]
            alternatives = []
            
            for alt in result.alternatives:
                alt_data = {
                    "transcript": alt.transcript,
                    "confidence": alt.confidence if hasattr(alt, 'confidence') else None
                }
                
                if enable_word_confidence and alt.words:
                    alt_data["words"] = [
                        {
                            "word": word.word,
                            "start_time": word.start_time.total_seconds() if word.start_time else None,
                            "end_time": word.end_time.total_seconds() if word.end_time else None,
                            "confidence": word.confidence if hasattr(word, 'confidence') else None
                        }
                        for word in alt.words
                    ]
                
                alternatives.append(alt_data)
            
            # Build response
            transcription_result = {
                "success": True,
                "transcript": alternatives[0]["transcript"],
                "alternatives": alternatives,
                "language": language.value,
                "provider": "google_cloud",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add to history for context
            self.recognition_history.append(transcription_result)
            if len(self.recognition_history) > 10:
                self.recognition_history.pop(0)
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Google Cloud Speech error: {e}")
            return None
    
    async def _transcribe_offline(
        self,
        audio_data: bytes,
        language: Language
    ) -> Dict[str, Any]:
        """Fallback offline transcription using SpeechRecognition."""
        try:
            # Convert audio data to AudioData object
            audio = sr.AudioData(
                audio_data,
                self.settings.audio_sample_rate,
                2  # 16-bit audio
            )
            
            # Perform recognition
            transcript = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.recognizer.recognize_google(
                    audio,
                    language=language.value.replace('_', '-').lower()
                )
            )
            
            return {
                "success": True,
                "transcript": transcript,
                "alternatives": [{"transcript": transcript, "confidence": None}],
                "language": language.value,
                "provider": "offline",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except sr.UnknownValueError:
            return {
                "success": False,
                "error": "Speech not recognized",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Offline transcription error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def stream_transcribe(
        self,
        audio_stream: asyncio.Queue,
        language: Optional[Language] = None,
        interim_results: bool = True
    ) -> asyncio.Queue:
        """
        Real-time streaming transcription.
        
        Args:
            audio_stream: Queue of audio chunks
            language: Language for transcription
            interim_results: Include interim (partial) results
            
        Returns:
            Queue of transcription results
        """
        language = language or self.settings.default_language
        results_queue = asyncio.Queue()
        
        if not self.google_client:
            await results_queue.put({
                "success": False,
                "error": "Streaming requires Google Cloud Speech",
                "timestamp": datetime.utcnow().isoformat()
            })
            return results_queue
        
        # Start streaming transcription task
        asyncio.create_task(
            self._stream_transcribe_worker(
                audio_stream, results_queue, language, interim_results
            )
        )
        
        return results_queue
    
    async def _stream_transcribe_worker(
        self,
        audio_stream: asyncio.Queue,
        results_queue: asyncio.Queue,
        language: Language,
        interim_results: bool
    ):
        """Worker for streaming transcription."""
        try:
            config = speech_types.StreamingRecognitionConfig(
                config=speech_types.RecognitionConfig(
                    encoding=speech_types.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=self.settings.audio_sample_rate,
                    language_code=language.value,
                    enable_automatic_punctuation=True,
                    speech_contexts=self.speech_contexts,
                    model=self.settings.google_speech_model,
                    use_enhanced=self.settings.google_speech_use_enhanced
                ),
                interim_results=interim_results,
                single_utterance=False
            )
            
            async def request_generator():
                yield speech_types.StreamingRecognizeRequest(
                    streaming_config=config
                )
                
                while True:
                    chunk = await audio_stream.get()
                    if chunk is None:
                        break
                    yield speech_types.StreamingRecognizeRequest(
                        audio_content=chunk
                    )
            
            # Perform streaming recognition
            responses = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.google_client.streaming_recognize(request_generator())
            )
            
            for response in responses:
                for result in response.results:
                    await results_queue.put({
                        "success": True,
                        "transcript": result.alternatives[0].transcript,
                        "is_final": result.is_final,
                        "stability": result.stability if hasattr(result, 'stability') else None,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
            await results_queue.put({
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def detect_voice_activity(self, audio_data: bytes, frame_duration_ms: int = 30) -> List[Tuple[int, int]]:
        """
        Detect voice activity in audio data.
        
        Args:
            audio_data: Raw audio data
            frame_duration_ms: Frame duration in milliseconds (10, 20, or 30)
            
        Returns:
            List of (start, end) tuples for voice segments in milliseconds
        """
        # Convert audio to appropriate format
        audio = AudioSegment(
            audio_data,
            sample_width=2,
            frame_rate=self.settings.audio_sample_rate,
            channels=1
        )
        
        # Detect non-silent segments
        nonsilent_segments = detect_nonsilent(
            audio,
            min_silence_len=int(self.settings.silence_duration * 1000),
            silence_thresh=self.settings.silence_threshold - 16
        )
        
        return nonsilent_segments
    
    async def detect_language(self, audio_data: bytes) -> Language:
        """
        Detect the language of speech in audio data.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Detected language
        """
        if not self.settings.auto_detect_language:
            return self.settings.default_language
        
        # Try multiple languages and compare confidence
        results = []
        for lang in self.settings.supported_languages[:3]:  # Test top 3 languages
            result = await self.transcribe_audio(
                audio_data,
                language=lang,
                max_alternatives=1,
                enable_punctuation=False,
                enable_word_confidence=False
            )
            
            if result.get("success"):
                confidence = result.get("alternatives", [{}])[0].get("confidence", 0)
                results.append((lang, confidence))
        
        # Return language with highest confidence
        if results:
            results.sort(key=lambda x: x[1], reverse=True)
            return results[0][0]
        
        return self.settings.default_language
    
    def apply_noise_reduction(self, audio_data: bytes) -> bytes:
        """
        Apply noise reduction to audio data.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Processed audio data
        """
        # Convert to AudioSegment
        audio = AudioSegment(
            audio_data,
            sample_width=2,
            frame_rate=self.settings.audio_sample_rate,
            channels=1
        )
        
        # Apply basic noise reduction
        # Reduce volume of quiet parts (likely noise)
        quiet_threshold = self.settings.silence_threshold - 10
        
        def reduce_noise(chunk):
            if chunk.dBFS < quiet_threshold:
                return chunk - 10  # Reduce by 10dB
            return chunk
        
        # Process in chunks
        chunk_length = 100  # milliseconds
        processed_chunks = []
        
        for i in range(0, len(audio), chunk_length):
            chunk = audio[i:i + chunk_length]
            processed_chunks.append(reduce_noise(chunk))
        
        # Combine processed chunks
        processed_audio = sum(processed_chunks)
        
        return processed_audio.raw_data
    
    def get_recognition_stats(self) -> Dict[str, Any]:
        """Get statistics about recognition performance."""
        if not self.recognition_history:
            return {"total_recognitions": 0}
        
        successful = [r for r in self.recognition_history if r.get("success")]
        
        return {
            "total_recognitions": len(self.recognition_history),
            "successful_recognitions": len(successful),
            "success_rate": len(successful) / len(self.recognition_history) if self.recognition_history else 0,
            "providers_used": list(set(r.get("provider", "unknown") for r in self.recognition_history)),
            "languages_used": list(set(r.get("language", "unknown") for r in self.recognition_history)),
            "average_confidence": np.mean([
                r.get("alternatives", [{}])[0].get("confidence", 0)
                for r in successful
                if r.get("alternatives", [{}])[0].get("confidence") is not None
            ]) if successful else 0
        }