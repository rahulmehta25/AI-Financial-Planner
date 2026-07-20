"""WebSocket Server for Real-time Voice Processing."""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import base64

from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState
import numpy as np

from .voice_interface import VoiceInterface
from .speech_to_text import SpeechToTextService
from .text_to_speech import TextToSpeechService
from .azure_speech import AzureSpeechService
from .wake_word_detector import WakeWordDetector
from .nlu_service import NLUService
from .config import VoiceSettings, Language

logger = logging.getLogger(__name__)


class VoiceWebSocketManager:
    """Manages WebSocket connections for voice processing."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize WebSocket manager."""
        self.settings = settings or VoiceSettings()
        
        # Active connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_sessions: Dict[str, Dict] = {}
        
        # Voice services
        self.voice_interface = VoiceInterface(settings)
        self.stt_service = SpeechToTextService(settings)
        self.tts_service = TextToSpeechService(settings)
        self.azure_service = AzureSpeechService(settings) if settings.azure_speech_key else None
        self.wake_detector = WakeWordDetector(settings)
        self.nlu_service = NLUService()
        
        # Audio buffers for streaming
        self.audio_buffers: Dict[str, bytearray] = {}
        self.stream_queues: Dict[str, asyncio.Queue] = {}
        
        # Processing state
        self.processing_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """
        Accept WebSocket connection and initialize session.
        
        Args:
            websocket: WebSocket connection
            client_id: Optional client identifier
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        # Generate connection ID
        connection_id = client_id or str(uuid.uuid4())
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        # Initialize session
        session = {
            "connection_id": connection_id,
            "connected_at": datetime.utcnow().isoformat(),
            "voice_session_id": None,
            "language": self.settings.default_language,
            "is_listening": False,
            "wake_word_enabled": False,
            "streaming_mode": False,
            "audio_format": "pcm",
            "sample_rate": 16000,
            "interaction_count": 0
        }
        
        self.connection_sessions[connection_id] = session
        
        # Initialize audio buffer and stream queue
        self.audio_buffers[connection_id] = bytearray()
        self.stream_queues[connection_id] = asyncio.Queue()
        
        # Send welcome message
        await self.send_message(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "capabilities": {
                "speech_to_text": True,
                "text_to_speech": True,
                "wake_word": True,
                "streaming": True,
                "multi_language": True,
                "azure_available": self.azure_service is not None
            },
            "settings": {
                "default_language": self.settings.default_language.value,
                "wake_word": self.settings.wake_word,
                "sample_rate": session["sample_rate"]
            }
        })
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Handle WebSocket disconnection.
        
        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.active_connections:
            # Stop any active processing
            if connection_id in self.processing_tasks:
                self.processing_tasks[connection_id].cancel()
            
            # Clean up voice session
            session = self.connection_sessions.get(connection_id, {})
            if session.get("voice_session_id"):
                await self.voice_interface.end_session(session["voice_session_id"])
            
            # Clean up resources
            del self.active_connections[connection_id]
            del self.connection_sessions[connection_id]
            del self.audio_buffers[connection_id]
            del self.stream_queues[connection_id]
            
            logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """
        Handle incoming WebSocket message.
        
        Args:
            connection_id: Connection identifier
            message: Message data
        """
        try:
            message_type = message.get("type")
            
            if message_type == "audio_data":
                await self._handle_audio_data(connection_id, message)
            
            elif message_type == "text_command":
                await self._handle_text_command(connection_id, message)
            
            elif message_type == "start_listening":
                await self._start_listening(connection_id, message)
            
            elif message_type == "stop_listening":
                await self._stop_listening(connection_id)
            
            elif message_type == "enable_wake_word":
                await self._enable_wake_word(connection_id, message)
            
            elif message_type == "disable_wake_word":
                await self._disable_wake_word(connection_id)
            
            elif message_type == "synthesize_speech":
                await self._synthesize_speech(connection_id, message)
            
            elif message_type == "update_settings":
                await self._update_settings(connection_id, message)
            
            elif message_type == "ping":
                await self.send_message(connection_id, {"type": "pong"})
            
            else:
                await self.send_error(connection_id, f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(connection_id, str(e))
    
    async def _handle_audio_data(self, connection_id: str, message: Dict[str, Any]):
        """
        Handle incoming audio data.
        
        Args:
            connection_id: Connection identifier
            message: Message containing audio data
        """
        session = self.connection_sessions[connection_id]
        
        # Get audio data
        audio_base64 = message.get("audio")
        if not audio_base64:
            return
        
        # Decode audio
        try:
            audio_data = base64.b64decode(audio_base64)
        except:
            await self.send_error(connection_id, "Invalid audio data encoding")
            return
        
        # Handle based on mode
        if session.get("streaming_mode"):
            # Add to stream queue for real-time processing
            await self.stream_queues[connection_id].put(audio_data)
            
            # Start streaming processor if not running
            if connection_id not in self.processing_tasks:
                task = asyncio.create_task(
                    self._process_audio_stream(connection_id)
                )
                self.processing_tasks[connection_id] = task
        
        else:
            # Buffer audio for batch processing
            self.audio_buffers[connection_id].extend(audio_data)
            
            # Check if we have enough audio to process
            buffer_size = len(self.audio_buffers[connection_id])
            min_buffer_size = session["sample_rate"] * 2  # 1 second of audio
            
            if buffer_size >= min_buffer_size:
                # Process buffered audio
                await self._process_buffered_audio(connection_id)
    
    async def _process_audio_stream(self, connection_id: str):
        """
        Process audio stream in real-time.
        
        Args:
            connection_id: Connection identifier
        """
        session = self.connection_sessions[connection_id]
        
        try:
            # Use Azure continuous recognition if available
            if self.azure_service and session.get("use_azure", True):
                # Start continuous recognition
                recognition_session = await self.azure_service.start_continuous_recognition(
                    language=session.get("language")
                )
                
                # Set up callbacks
                self.azure_service.add_recognition_callback(
                    "recognizing",
                    lambda result: asyncio.create_task(
                        self._send_interim_transcript(connection_id, result)
                    )
                )
                
                self.azure_service.add_recognition_callback(
                    "recognized",
                    lambda result: asyncio.create_task(
                        self._send_final_transcript(connection_id, result)
                    )
                )
                
                # Process audio chunks
                while session.get("streaming_mode"):
                    try:
                        audio_chunk = await asyncio.wait_for(
                            self.stream_queues[connection_id].get(),
                            timeout=1.0
                        )
                        
                        # Feed audio to Azure (would need custom implementation)
                        # For now, accumulate and process in batches
                        self.audio_buffers[connection_id].extend(audio_chunk)
                        
                    except asyncio.TimeoutError:
                        continue
                
                # Stop recognition
                await self.azure_service.stop_continuous_recognition()
            
            else:
                # Use standard streaming transcription
                audio_stream = self.stream_queues[connection_id]
                results_queue = await self.stt_service.stream_transcribe(
                    audio_stream,
                    language=session.get("language")
                )
                
                # Process results
                while session.get("streaming_mode"):
                    try:
                        result = await asyncio.wait_for(
                            results_queue.get(),
                            timeout=1.0
                        )
                        
                        if result.get("success"):
                            if result.get("is_final"):
                                await self._send_final_transcript(connection_id, result)
                            else:
                                await self._send_interim_transcript(connection_id, result)
                    
                    except asyncio.TimeoutError:
                        continue
        
        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            await self.send_error(connection_id, f"Stream processing error: {e}")
        
        finally:
            # Clean up
            if connection_id in self.processing_tasks:
                del self.processing_tasks[connection_id]
    
    async def _process_buffered_audio(self, connection_id: str):
        """
        Process buffered audio data.
        
        Args:
            connection_id: Connection identifier
        """
        session = self.connection_sessions[connection_id]
        
        # Get buffered audio
        audio_data = bytes(self.audio_buffers[connection_id])
        
        # Clear buffer
        self.audio_buffers[connection_id].clear()
        
        # Send processing status
        await self.send_message(connection_id, {
            "type": "processing_audio",
            "audio_size": len(audio_data)
        })
        
        try:
            # Transcribe audio
            if self.azure_service and session.get("use_azure", True):
                result = await self.azure_service.recognize_once(
                    audio_data,
                    language=session.get("language")
                )
            else:
                result = await self.stt_service.transcribe_audio(
                    audio_data,
                    language=session.get("language")
                )
            
            if result.get("success"):
                # Perform NLU
                nlu_result = self.nlu_service.understand(
                    result["transcript"],
                    context=session.get("context")
                )
                
                # Send transcript with understanding
                await self.send_message(connection_id, {
                    "type": "transcription_result",
                    "transcript": result["transcript"],
                    "confidence": result.get("confidence"),
                    "language": result.get("language"),
                    "intent": nlu_result["intent"].__dict__,
                    "entities": [e.__dict__ for e in nlu_result["entities"]],
                    "sentiment": nlu_result["sentiment"]
                })
                
                # Process command through voice interface
                command_result = await self.voice_interface.process_text_command(
                    session.get("voice_session_id"),
                    result["transcript"]
                )
                
                # Send command result
                await self.send_message(connection_id, {
                    "type": "command_result",
                    "result": command_result
                })
                
                # Update interaction count
                session["interaction_count"] += 1
            
            else:
                await self.send_message(connection_id, {
                    "type": "transcription_error",
                    "error": result.get("error", "Unknown error")
                })
        
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            await self.send_error(connection_id, str(e))
    
    async def _handle_text_command(self, connection_id: str, message: Dict[str, Any]):
        """
        Handle text command input.
        
        Args:
            connection_id: Connection identifier
            message: Message containing text command
        """
        session = self.connection_sessions[connection_id]
        text = message.get("text", "")
        
        if not text:
            return
        
        try:
            # Perform NLU
            nlu_result = self.nlu_service.understand(
                text,
                context=session.get("context")
            )
            
            # Send understanding result
            await self.send_message(connection_id, {
                "type": "understanding_result",
                "text": text,
                "intent": nlu_result["intent"].__dict__,
                "entities": [e.__dict__ for e in nlu_result["entities"]],
                "sentiment": nlu_result["sentiment"]
            })
            
            # Process command
            if not session.get("voice_session_id"):
                session["voice_session_id"] = await self.voice_interface.create_session()
            
            result = await self.voice_interface.process_text_command(
                session["voice_session_id"],
                text
            )
            
            # Send result
            await self.send_message(connection_id, {
                "type": "command_result",
                "result": result
            })
            
            # Generate voice response if requested
            if message.get("generate_voice_response"):
                await self._generate_voice_response(
                    connection_id,
                    result.get("response_text", "Command processed")
                )
        
        except Exception as e:
            logger.error(f"Text command error: {e}")
            await self.send_error(connection_id, str(e))
    
    async def _synthesize_speech(self, connection_id: str, message: Dict[str, Any]):
        """
        Synthesize speech from text.
        
        Args:
            connection_id: Connection identifier
            message: Message containing text to synthesize
        """
        session = self.connection_sessions[connection_id]
        text = message.get("text", "")
        
        if not text:
            return
        
        try:
            # Synthesize speech
            if self.azure_service and message.get("use_azure", True):
                result = await self.azure_service.synthesize_speech_azure(
                    text,
                    voice_name=message.get("voice"),
                    language=session.get("language"),
                    style=message.get("style"),
                    style_degree=message.get("style_degree", 1.0)
                )
            else:
                result = await self.tts_service.synthesize_speech(
                    text,
                    language=session.get("language"),
                    voice_gender=message.get("voice_gender"),
                    voice_profile=message.get("voice_profile")
                )
            
            if result.get("success"):
                # Send audio data
                audio_base64 = base64.b64encode(result["audio_data"]).decode()
                
                await self.send_message(connection_id, {
                    "type": "audio_response",
                    "audio": audio_base64,
                    "format": result.get("format", "mp3"),
                    "duration": result.get("duration"),
                    "text": text
                })
            else:
                await self.send_error(connection_id, result.get("error", "Synthesis failed"))
        
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            await self.send_error(connection_id, str(e))
    
    async def _generate_voice_response(self, connection_id: str, text: str):
        """
        Generate and send voice response.
        
        Args:
            connection_id: Connection identifier
            text: Text to speak
        """
        await self._synthesize_speech(connection_id, {"text": text})
    
    async def _start_listening(self, connection_id: str, message: Dict[str, Any]):
        """
        Start listening for voice input.
        
        Args:
            connection_id: Connection identifier
            message: Configuration message
        """
        session = self.connection_sessions[connection_id]
        
        # Update session settings
        session["is_listening"] = True
        session["streaming_mode"] = message.get("streaming", False)
        session["language"] = Language(message.get("language", self.settings.default_language.value))
        session["use_azure"] = message.get("use_azure", True)
        
        # Create voice session if needed
        if not session.get("voice_session_id"):
            session["voice_session_id"] = await self.voice_interface.create_session(
                language=session["language"]
            )
        
        # Send confirmation
        await self.send_message(connection_id, {
            "type": "listening_started",
            "streaming": session["streaming_mode"],
            "language": session["language"].value
        })
    
    async def _stop_listening(self, connection_id: str):
        """
        Stop listening for voice input.
        
        Args:
            connection_id: Connection identifier
        """
        session = self.connection_sessions[connection_id]
        
        session["is_listening"] = False
        session["streaming_mode"] = False
        
        # Process any remaining buffered audio
        if self.audio_buffers[connection_id]:
            await self._process_buffered_audio(connection_id)
        
        # Send confirmation
        await self.send_message(connection_id, {
            "type": "listening_stopped"
        })
    
    async def _enable_wake_word(self, connection_id: str, message: Dict[str, Any]):
        """
        Enable wake word detection.
        
        Args:
            connection_id: Connection identifier
            message: Configuration message
        """
        session = self.connection_sessions[connection_id]
        
        # Set wake word
        wake_word = message.get("wake_word", self.settings.wake_word)
        self.wake_detector.wake_word = wake_word
        
        # Set sensitivity
        sensitivity = message.get("sensitivity", 0.5)
        self.wake_detector.set_sensitivity(sensitivity)
        
        # Add callback
        async def on_wake_word(event):
            await self.send_message(connection_id, {
                "type": "wake_word_detected",
                "wake_word": event["wake_word"],
                "timestamp": event["timestamp"]
            })
            
            # Auto-start listening
            if message.get("auto_listen", True):
                await self._start_listening(connection_id, {})
        
        self.wake_detector.add_wake_word_callback(on_wake_word)
        
        # Start detection
        await self.wake_detector.start_detection()
        
        session["wake_word_enabled"] = True
        
        # Send confirmation
        await self.send_message(connection_id, {
            "type": "wake_word_enabled",
            "wake_word": wake_word,
            "sensitivity": sensitivity
        })
    
    async def _disable_wake_word(self, connection_id: str):
        """
        Disable wake word detection.
        
        Args:
            connection_id: Connection identifier
        """
        session = self.connection_sessions[connection_id]
        
        await self.wake_detector.stop_detection()
        
        session["wake_word_enabled"] = False
        
        # Send confirmation
        await self.send_message(connection_id, {
            "type": "wake_word_disabled"
        })
    
    async def _update_settings(self, connection_id: str, message: Dict[str, Any]):
        """
        Update session settings.
        
        Args:
            connection_id: Connection identifier
            message: Settings to update
        """
        session = self.connection_sessions[connection_id]
        
        # Update language
        if "language" in message:
            session["language"] = Language(message["language"])
        
        # Update audio format
        if "audio_format" in message:
            session["audio_format"] = message["audio_format"]
        
        # Update sample rate
        if "sample_rate" in message:
            session["sample_rate"] = message["sample_rate"]
        
        # Send confirmation
        await self.send_message(connection_id, {
            "type": "settings_updated",
            "settings": {
                "language": session["language"].value,
                "audio_format": session["audio_format"],
                "sample_rate": session["sample_rate"]
            }
        })
    
    async def _send_interim_transcript(self, connection_id: str, result: Dict[str, Any]):
        """
        Send interim transcription result.
        
        Args:
            connection_id: Connection identifier
            result: Transcription result
        """
        await self.send_message(connection_id, {
            "type": "interim_transcript",
            "text": result.get("text", ""),
            "timestamp": result.get("timestamp")
        })
    
    async def _send_final_transcript(self, connection_id: str, result: Dict[str, Any]):
        """
        Send final transcription result.
        
        Args:
            connection_id: Connection identifier
            result: Transcription result
        """
        # Perform NLU on final transcript
        session = self.connection_sessions[connection_id]
        nlu_result = self.nlu_service.understand(
            result.get("text", ""),
            context=session.get("context")
        )
        
        await self.send_message(connection_id, {
            "type": "final_transcript",
            "text": result.get("text", ""),
            "intent": nlu_result["intent"].__dict__,
            "entities": [e.__dict__ for e in nlu_result["entities"]],
            "timestamp": result.get("timestamp")
        })
    
    async def send_message(self, connection_id: str, message: Dict[str, Any]):
        """
        Send message to client.
        
        Args:
            connection_id: Connection identifier
            message: Message to send
        """
        websocket = self.active_connections.get(connection_id)
        if websocket and websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                await self.disconnect(connection_id)
    
    async def send_error(self, connection_id: str, error: str):
        """
        Send error message to client.
        
        Args:
            connection_id: Connection identifier
            error: Error message
        """
        await self.send_message(connection_id, {
            "type": "error",
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude: Set of connection IDs to exclude
        """
        exclude = exclude or set()
        
        for connection_id in self.active_connections:
            if connection_id not in exclude:
                await self.send_message(connection_id, message)