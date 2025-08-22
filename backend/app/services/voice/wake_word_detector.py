"""Wake Word Detection Service for Voice Activation."""

import asyncio
import logging
import numpy as np
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime, timedelta
import threading
import queue

import pvporcupine
import pyaudio
import sounddevice as sd
from scipy import signal

from .config import VoiceSettings

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Wake word detection using Porcupine and custom models."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize wake word detector."""
        self.settings = settings or VoiceSettings()
        
        # Porcupine wake word detector
        self.porcupine = None
        self.audio_stream = None
        
        # Detection state
        self.is_listening = False
        self.detection_thread = None
        self.audio_queue = queue.Queue()
        
        # Callbacks
        self.wake_word_callbacks = []
        self.post_wake_callbacks = []
        
        # Detection parameters
        self.sensitivity = 0.5  # 0 to 1
        self.wake_word = self.settings.wake_word
        self.cooldown_period = timedelta(seconds=2)  # Prevent rapid re-triggers
        self.last_detection_time = None
        
        # Audio parameters
        self.sample_rate = 16000
        self.frame_length = 512
        
        # Energy-based detection for custom wake words
        self.energy_threshold = 500
        self.energy_history = []
        self.max_energy_history = 50
        
        # Initialize detector
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize the wake word detection engine."""
        try:
            # Try to initialize Porcupine for built-in wake words
            access_key = self.settings.porcupine_access_key
            
            if access_key:
                # Map common wake words to Porcupine keywords
                keyword_map = {
                    "hey finance": "picovoice",
                    "ok finance": "alexa",
                    "hello assistant": "hey google"
                }
                
                keyword = keyword_map.get(self.wake_word.lower(), "picovoice")
                
                self.porcupine = pvporcupine.create(
                    access_key=access_key,
                    keywords=[keyword],
                    sensitivities=[self.sensitivity]
                )
                
                logger.info(f"Porcupine wake word detector initialized for '{keyword}'")
            else:
                logger.info("Using energy-based wake word detection")
                
        except Exception as e:
            logger.warning(f"Could not initialize Porcupine: {e}. Using fallback detection.")
            self.porcupine = None
    
    async def start_detection(self, callback: Optional[Callable] = None):
        """Start wake word detection."""
        if self.is_listening:
            logger.warning("Wake word detection already running")
            return
        
        if callback:
            self.wake_word_callbacks.append(callback)
        
        self.is_listening = True
        
        # Start detection based on available method
        if self.porcupine:
            await self._start_porcupine_detection()
        else:
            await self._start_energy_detection()
    
    async def _start_porcupine_detection(self):
        """Start detection using Porcupine."""
        try:
            # Initialize PyAudio
            pa = pyaudio.PyAudio()
            
            self.audio_stream = pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                stream_callback=self._porcupine_audio_callback
            )
            
            self.audio_stream.start_stream()
            
            logger.info("Porcupine wake word detection started")
            
            # Run detection in background thread
            self.detection_thread = threading.Thread(
                target=self._porcupine_detection_loop,
                daemon=True
            )
            self.detection_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start Porcupine detection: {e}")
            self.is_listening = False
            raise
    
    def _porcupine_audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback for Porcupine."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Add audio to queue for processing
        self.audio_queue.put(in_data)
        
        return (in_data, pyaudio.paContinue)
    
    def _porcupine_detection_loop(self):
        """Detection loop for Porcupine."""
        while self.is_listening:
            try:
                # Get audio from queue
                audio_data = self.audio_queue.get(timeout=1)
                
                # Convert to numpy array
                pcm = np.frombuffer(audio_data, dtype=np.int16)
                
                # Check for wake word
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    self._handle_wake_word_detected()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Detection loop error: {e}")
    
    async def _start_energy_detection(self):
        """Start energy-based wake word detection."""
        try:
            # Start audio stream with sounddevice
            self.audio_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                blocksize=self.frame_length,
                callback=self._energy_audio_callback
            )
            
            self.audio_stream.start()
            
            logger.info("Energy-based wake word detection started")
            
            # Run detection in async task
            asyncio.create_task(self._energy_detection_loop())
            
        except Exception as e:
            logger.error(f"Failed to start energy detection: {e}")
            self.is_listening = False
            raise
    
    def _energy_audio_callback(self, indata, frames, time, status):
        """Audio callback for energy-based detection."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Calculate energy
        audio = indata[:, 0]
        energy = np.sqrt(np.mean(audio ** 2))
        
        # Add to history
        self.energy_history.append(energy)
        if len(self.energy_history) > self.max_energy_history:
            self.energy_history.pop(0)
        
        # Put audio in queue for further processing
        self.audio_queue.put(audio.tobytes())
    
    async def _energy_detection_loop(self):
        """Detection loop for energy-based method."""
        consecutive_high_energy = 0
        required_consecutive = 5
        
        while self.is_listening:
            try:
                # Check energy levels
                if self.energy_history:
                    current_energy = self.energy_history[-1]
                    avg_energy = np.mean(self.energy_history)
                    
                    # Detect sudden energy increase (possible speech)
                    if current_energy > self.energy_threshold and current_energy > avg_energy * 1.5:
                        consecutive_high_energy += 1
                        
                        if consecutive_high_energy >= required_consecutive:
                            # Potential wake word detected - analyze audio
                            await self._analyze_potential_wake_word()
                            consecutive_high_energy = 0
                    else:
                        consecutive_high_energy = 0
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Energy detection loop error: {e}")
    
    async def _analyze_potential_wake_word(self):
        """Analyze audio to determine if wake word was spoken."""
        # Get recent audio from queue
        audio_buffer = b''
        
        try:
            # Collect recent audio (about 1 second)
            for _ in range(int(self.sample_rate / self.frame_length)):
                if not self.audio_queue.empty():
                    audio_buffer += self.audio_queue.get_nowait()
        except queue.Empty:
            pass
        
        if len(audio_buffer) > 0:
            # Simple pattern matching for wake word
            # In production, this would use a more sophisticated method
            # like DTW (Dynamic Time Warping) or a small neural network
            
            # For now, just check if energy pattern matches expected pattern
            # This is a placeholder - real implementation would be more complex
            if self._matches_wake_word_pattern(audio_buffer):
                self._handle_wake_word_detected()
    
    def _matches_wake_word_pattern(self, audio_data: bytes) -> bool:
        """Check if audio matches wake word pattern (simplified)."""
        # Convert to numpy array
        audio = np.frombuffer(audio_data, dtype=np.int16)
        
        # Calculate features
        # Zero crossing rate
        zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
        
        # Spectral centroid
        fft = np.fft.rfft(audio)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio), 1/self.sample_rate)
        centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
        
        # Simple heuristic - adjust based on actual wake word
        # These values would be learned from training data
        expected_zcr_range = (0.02, 0.1)
        expected_centroid_range = (500, 2000)
        
        if (expected_zcr_range[0] <= zcr <= expected_zcr_range[1] and
            expected_centroid_range[0] <= centroid <= expected_centroid_range[1]):
            return True
        
        return False
    
    def _handle_wake_word_detected(self):
        """Handle wake word detection."""
        # Check cooldown
        now = datetime.now()
        if self.last_detection_time:
            if now - self.last_detection_time < self.cooldown_period:
                return
        
        self.last_detection_time = now
        
        logger.info(f"Wake word '{self.wake_word}' detected")
        
        # Notify callbacks
        detection_event = {
            "wake_word": self.wake_word,
            "timestamp": now.isoformat(),
            "confidence": 0.8  # Placeholder confidence
        }
        
        for callback in self.wake_word_callbacks:
            try:
                callback(detection_event)
            except Exception as e:
                logger.error(f"Wake word callback error: {e}")
        
        # Execute post-wake actions
        self._execute_post_wake_actions()
    
    def _execute_post_wake_actions(self):
        """Execute actions after wake word detection."""
        for callback in self.post_wake_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Post-wake callback error: {e}")
    
    async def stop_detection(self):
        """Stop wake word detection."""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        # Stop audio stream
        if self.audio_stream:
            if hasattr(self.audio_stream, 'stop_stream'):
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            elif hasattr(self.audio_stream, 'stop'):
                self.audio_stream.stop()
                self.audio_stream.close()
        
        # Clean up Porcupine
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        
        # Wait for detection thread to finish
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2)
        
        logger.info("Wake word detection stopped")
    
    def add_wake_word_callback(self, callback: Callable):
        """Add callback for wake word detection."""
        if callback not in self.wake_word_callbacks:
            self.wake_word_callbacks.append(callback)
    
    def add_post_wake_callback(self, callback: Callable):
        """Add callback to execute after wake word."""
        if callback not in self.post_wake_callbacks:
            self.post_wake_callbacks.append(callback)
    
    def set_sensitivity(self, sensitivity: float):
        """Set detection sensitivity (0 to 1)."""
        self.sensitivity = max(0, min(1, sensitivity))
        
        # Update Porcupine if active
        if self.porcupine and self.is_listening:
            # Restart with new sensitivity
            asyncio.create_task(self._restart_detection())
    
    async def _restart_detection(self):
        """Restart detection with new parameters."""
        await self.stop_detection()
        self._initialize_detector()
        await self.start_detection()
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get wake word detection statistics."""
        return {
            "is_listening": self.is_listening,
            "wake_word": self.wake_word,
            "sensitivity": self.sensitivity,
            "detection_method": "porcupine" if self.porcupine else "energy",
            "last_detection": self.last_detection_time.isoformat() if self.last_detection_time else None,
            "energy_threshold": self.energy_threshold,
            "current_energy": self.energy_history[-1] if self.energy_history else 0
        }
    
    async def train_custom_wake_word(
        self,
        wake_word: str,
        audio_samples: List[bytes],
        negative_samples: Optional[List[bytes]] = None
    ) -> bool:
        """
        Train a custom wake word model (placeholder for actual implementation).
        
        Args:
            wake_word: The wake word phrase
            audio_samples: List of audio samples containing the wake word
            negative_samples: Optional negative samples without wake word
            
        Returns:
            True if training successful
        """
        logger.info(f"Training custom wake word: {wake_word}")
        
        # In a real implementation, this would:
        # 1. Extract features from audio samples
        # 2. Train a small neural network or SVM
        # 3. Save the model for later use
        # 4. Update detection to use the new model
        
        # For now, just update the wake word
        self.wake_word = wake_word
        self.settings.wake_word = wake_word
        
        logger.info(f"Custom wake word '{wake_word}' configured (training placeholder)")
        
        return True