"""Main Voice Interface integrating all voice services."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import uuid

from .speech_to_text import SpeechToTextService
from .text_to_speech import TextToSpeechService
from .voice_commands import VoiceCommandParser, CommandIntent
from .conversation_flow import ConversationFlowManager, ConversationState
from .config import VoiceSettings, Language, VoiceGender, VOICE_SHORTCUTS

logger = logging.getLogger(__name__)


class VoiceSession:
    """Represents an active voice session."""
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.language = Language.ENGLISH
        self.voice_gender = VoiceGender.NEUTRAL
        self.voice_profile = "professional"
        self.is_active = True
        self.interaction_count = 0
        self.last_interaction = None
        self.context = {}
        self.history = []


class VoiceInterface:
    """Main voice interface coordinating all voice services."""
    
    def __init__(self, settings: Optional[VoiceSettings] = None):
        """Initialize the voice interface."""
        self.settings = settings or VoiceSettings()
        
        # Initialize services
        self.stt_service = SpeechToTextService(settings)
        self.tts_service = TextToSpeechService(settings)
        self.command_parser = VoiceCommandParser()
        self.flow_manager = ConversationFlowManager()
        
        # Session management
        self.sessions: Dict[str, VoiceSession] = {}
        self.active_sessions = 0
        
        # Command handlers
        self.command_handlers: Dict[CommandIntent, Callable] = {}
        self._register_default_handlers()
        
        # Voice shortcuts
        self.shortcuts = VOICE_SHORTCUTS
        
        # Analytics
        self.analytics = {
            "total_sessions": 0,
            "total_interactions": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "average_session_duration": 0
        }
    
    def _register_default_handlers(self):
        """Register default command handlers."""
        self.command_handlers[CommandIntent.NAVIGATION] = self._handle_navigation
        self.command_handlers[CommandIntent.QUERY] = self._handle_query
        self.command_handlers[CommandIntent.ACTION] = self._handle_action
        self.command_handlers[CommandIntent.HELP] = self._handle_help
        self.command_handlers[CommandIntent.CONFIRMATION] = self._handle_confirmation
        self.command_handlers[CommandIntent.CORRECTION] = self._handle_correction
        self.command_handlers[CommandIntent.CALCULATION] = self._handle_calculation
        self.command_handlers[CommandIntent.COMPARISON] = self._handle_comparison
    
    async def create_session(
        self,
        user_id: Optional[str] = None,
        language: Optional[Language] = None,
        voice_gender: Optional[VoiceGender] = None,
        voice_profile: Optional[str] = None
    ) -> str:
        """
        Create a new voice session.
        
        Args:
            user_id: Optional user identifier
            language: Preferred language
            voice_gender: Preferred voice gender
            voice_profile: Voice profile name
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session = VoiceSession(session_id, user_id)
        
        # Set preferences
        if language:
            session.language = language
        if voice_gender:
            session.voice_gender = voice_gender
        if voice_profile:
            session.voice_profile = voice_profile
        
        self.sessions[session_id] = session
        self.active_sessions += 1
        self.analytics["total_sessions"] += 1
        
        logger.info(f"Created voice session: {session_id}")
        
        return session_id
    
    async def process_audio(
        self,
        session_id: str,
        audio_data: bytes,
        auto_respond: bool = True
    ) -> Dict[str, Any]:
        """
        Process audio input and generate response.
        
        Args:
            session_id: Session ID
            audio_data: Raw audio data
            auto_respond: Automatically generate audio response
            
        Returns:
            Processing result with transcript and response
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Invalid session ID"
            }
        
        try:
            # Update session activity
            session.last_interaction = datetime.utcnow()
            session.interaction_count += 1
            
            # Speech to text
            transcription = await self.stt_service.transcribe_audio(
                audio_data,
                language=session.language
            )
            
            if not transcription.get("success"):
                return transcription
            
            transcript = transcription["transcript"]
            
            # Process command
            result = await self.process_text_command(
                session_id, transcript, auto_respond
            )
            
            # Add transcription info to result
            result["transcript"] = transcript
            result["transcription_confidence"] = transcription.get("alternatives", [{}])[0].get("confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_text_command(
        self,
        session_id: str,
        text: str,
        auto_respond: bool = True
    ) -> Dict[str, Any]:
        """
        Process text command and generate response.
        
        Args:
            session_id: Session ID
            text: Command text
            auto_respond: Automatically generate audio response
            
        Returns:
            Processing result with response
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Invalid session ID"
            }
        
        try:
            # Parse command
            parsed_command = self.command_parser.parse_command(text)
            intent = parsed_command["intent"]
            
            # Add to session history
            session.history.append({
                "type": "user",
                "text": text,
                "intent": intent,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Check if there's an active flow
            if self.flow_manager.active_flow:
                response = await self.flow_manager.process_input(text, parsed_command)
            else:
                # Check for flow triggers
                flow_trigger = self._check_flow_trigger(parsed_command)
                if flow_trigger:
                    response = self.flow_manager.start_flow(flow_trigger)
                else:
                    # Handle command normally
                    handler = self.command_handlers.get(
                        CommandIntent(intent),
                        self._handle_unknown
                    )
                    response = await handler(session, parsed_command)
            
            # Update analytics
            if response.get("success"):
                self.analytics["successful_commands"] += 1
            else:
                self.analytics["failed_commands"] += 1
            
            # Add to session history
            session.history.append({
                "type": "assistant",
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Generate audio response if requested
            if auto_respond and response.get("prompt"):
                audio_response = await self.generate_audio_response(
                    session_id, response["prompt"]
                )
                response["audio"] = audio_response
            
            return response
            
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_audio_response(
        self,
        session_id: str,
        text: str,
        use_ssml: bool = False
    ) -> Dict[str, Any]:
        """
        Generate audio response for text.
        
        Args:
            session_id: Session ID
            text: Response text
            use_ssml: Whether text contains SSML markup
            
        Returns:
            Audio response data
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Invalid session ID"
            }
        
        try:
            if use_ssml:
                audio_data = await self.tts_service.synthesize_ssml(
                    text,
                    language=session.language,
                    voice_gender=session.voice_gender
                )
            else:
                audio_data = await self.tts_service.synthesize_speech(
                    text,
                    language=session.language,
                    voice_gender=session.voice_gender,
                    voice_profile=session.voice_profile
                )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_flow_trigger(self, parsed_command: Dict[str, Any]) -> Optional[str]:
        """Check if command should trigger a conversation flow."""
        intent = parsed_command.get("intent")
        text = parsed_command.get("text", "").lower()
        
        # Map keywords to flows
        flow_triggers = {
            "create goal": "create_goal",
            "new goal": "create_goal",
            "add goal": "create_goal",
            "investment transaction": "investment_transaction",
            "buy stock": "investment_transaction",
            "sell stock": "investment_transaction",
            "portfolio review": "portfolio_review",
            "review portfolio": "portfolio_review",
            "retirement planning": "retirement_planning",
            "plan retirement": "retirement_planning"
        }
        
        for trigger, flow_id in flow_triggers.items():
            if trigger in text:
                return flow_id
        
        # Check intent-based triggers
        if intent == CommandIntent.ACTION:
            entities = parsed_command.get("entities", {})
            if "goal" in text:
                return "create_goal"
            elif any(word in text for word in ["buy", "sell", "invest"]):
                return "investment_transaction"
        
        return None
    
    async def _handle_navigation(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle navigation commands."""
        entities = command.get("entities", {})
        text = command.get("text", "").lower()
        
        # Extract destination
        destination = None
        navigation_map = {
            "portfolio": "portfolio_overview",
            "goals": "financial_goals",
            "investments": "investment_list",
            "settings": "user_settings",
            "dashboard": "main_dashboard",
            "transactions": "transaction_history",
            "reports": "financial_reports"
        }
        
        for keyword, route in navigation_map.items():
            if keyword in text:
                destination = route
                break
        
        if destination:
            return {
                "success": True,
                "action": "navigate",
                "destination": destination,
                "prompt": f"Navigating to {destination.replace('_', ' ')}."
            }
        
        return {
            "success": False,
            "error": "I couldn't determine where you want to go.",
            "prompt": "Please specify where you'd like to navigate."
        }
    
    async def _handle_query(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle query commands."""
        entities = command.get("entities", {})
        text = command.get("text", "").lower()
        
        # Determine query type
        if "portfolio" in text and "value" in text:
            # Mock portfolio value query
            return {
                "success": True,
                "query_type": "portfolio_value",
                "data": {
                    "total_value": 250000,
                    "change_today": 1250,
                    "change_percent": 0.5
                },
                "prompt": "Your portfolio is currently valued at $250,000, up $1,250 or 0.5% today."
            }
        
        elif "goal" in text:
            return {
                "success": True,
                "query_type": "goal_status",
                "prompt": "You have 3 active goals. Would you like details on a specific goal?"
            }
        
        elif "performance" in text:
            return {
                "success": True,
                "query_type": "performance",
                "prompt": "Your portfolio has returned 12.5% year to date, outperforming the market by 2.3%."
            }
        
        return {
            "success": True,
            "query_type": "general",
            "prompt": "I can help you with portfolio values, goal progress, performance, and more. What would you like to know?"
        }
    
    async def _handle_action(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle action commands."""
        entities = command.get("entities", {})
        text = command.get("text", "").lower()
        
        # Check for shortcuts
        for shortcut, description in self.shortcuts.items():
            if shortcut.lower() in text:
                return {
                    "success": True,
                    "action": "shortcut",
                    "shortcut": shortcut,
                    "description": description,
                    "prompt": f"Executing: {description}"
                }
        
        # Handle specific actions
        if "rebalance" in text:
            return {
                "success": True,
                "action": "rebalance",
                "prompt": "Would you like to rebalance your portfolio to match your target allocation?"
            }
        
        return {
            "success": True,
            "action": "generic",
            "prompt": "I'll help you with that action. Could you provide more details?"
        }
    
    async def _handle_help(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle help commands."""
        text = command.get("text", "").lower()
        
        # Extract help topic
        topic = None
        if "portfolio" in text:
            topic = "portfolio"
        elif "goal" in text:
            topic = "goals"
        elif "transaction" in text:
            topic = "transactions"
        
        help_response = self.command_parser.get_help_response(topic)
        
        return {
            "success": True,
            "action": "help",
            "topic": topic,
            "prompt": help_response
        }
    
    async def _handle_confirmation(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle confirmation commands."""
        text = command.get("text", "").lower()
        
        # Check for positive or negative confirmation
        is_confirmed = any(word in text for word in ["yes", "yeah", "correct", "confirm", "approve"])
        
        # Check if there's a pending action in context
        if "pending_action" in session.context:
            action = session.context["pending_action"]
            
            if is_confirmed:
                # Execute the pending action
                del session.context["pending_action"]
                return {
                    "success": True,
                    "action": "confirmed",
                    "executed_action": action,
                    "prompt": f"Confirmed. {action['description']} has been executed."
                }
            else:
                del session.context["pending_action"]
                return {
                    "success": True,
                    "action": "cancelled",
                    "prompt": "Action cancelled."
                }
        
        return {
            "success": False,
            "error": "No pending action to confirm",
            "prompt": "There's nothing to confirm at the moment."
        }
    
    async def _handle_correction(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle correction commands."""
        entities = command.get("entities", {})
        text = command.get("text", "")
        
        # Extract what needs to be corrected
        import re
        correction_match = re.search(r"(?:change|correct|make) (?:it|that) to (.+)", text, re.I)
        
        if correction_match:
            new_value = correction_match.group(1)
            
            # Check if there's something to correct in context
            if session.history:
                last_interaction = session.history[-2] if len(session.history) > 1 else None
                
                if last_interaction:
                    return {
                        "success": True,
                        "action": "correction",
                        "original": last_interaction.get("text"),
                        "corrected": new_value,
                        "prompt": f"Corrected to: {new_value}"
                    }
        
        return {
            "success": False,
            "error": "Could not determine what to correct",
            "prompt": "What would you like to correct?"
        }
    
    async def _handle_calculation(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle calculation commands."""
        entities = command.get("entities", {})
        text = command.get("text", "").lower()
        
        # Determine calculation type
        if "retirement" in text:
            return {
                "success": True,
                "calculation_type": "retirement",
                "prompt": "To calculate your retirement projection, I'll need some information. Would you like to start?"
            }
        elif "compound" in text:
            return {
                "success": True,
                "calculation_type": "compound_interest",
                "prompt": "I can calculate compound interest. Please provide the principal amount, rate, and time period."
            }
        elif "tax" in text:
            return {
                "success": True,
                "calculation_type": "tax",
                "prompt": "I can help calculate tax implications. What type of tax calculation do you need?"
            }
        
        return {
            "success": True,
            "calculation_type": "general",
            "prompt": "What would you like me to calculate?"
        }
    
    async def _handle_comparison(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle comparison commands."""
        text = command.get("text", "").lower()
        
        # Extract comparison items
        import re
        comparison_match = re.search(r"compare (.+) (?:with|to|and|versus|vs) (.+)", text, re.I)
        
        if comparison_match:
            item1 = comparison_match.group(1)
            item2 = comparison_match.group(2)
            
            return {
                "success": True,
                "action": "comparison",
                "items": [item1, item2],
                "prompt": f"Comparing {item1} with {item2}. Analysis in progress."
            }
        
        return {
            "success": False,
            "error": "Could not determine what to compare",
            "prompt": "What would you like to compare?"
        }
    
    async def _handle_unknown(self, session: VoiceSession, command: Dict) -> Dict[str, Any]:
        """Handle unknown commands."""
        return {
            "success": False,
            "error": "Command not recognized",
            "prompt": "I didn't understand that command. Could you please rephrase or say 'help' for assistance?"
        }
    
    async def stream_process(
        self,
        session_id: str,
        audio_stream: asyncio.Queue
    ) -> asyncio.Queue:
        """
        Process streaming audio input.
        
        Args:
            session_id: Session ID
            audio_stream: Queue of audio chunks
            
        Returns:
            Queue of responses
        """
        session = self.sessions.get(session_id)
        if not session:
            results = asyncio.Queue()
            await results.put({
                "success": False,
                "error": "Invalid session ID"
            })
            return results
        
        # Start streaming transcription
        transcription_queue = await self.stt_service.stream_transcribe(
            audio_stream,
            language=session.language
        )
        
        # Process transcriptions and generate responses
        response_queue = asyncio.Queue()
        
        async def process_transcriptions():
            while True:
                transcription = await transcription_queue.get()
                
                if transcription.get("is_final"):
                    # Process final transcript
                    response = await self.process_text_command(
                        session_id,
                        transcription["transcript"]
                    )
                    await response_queue.put(response)
                else:
                    # Send interim result
                    await response_queue.put({
                        "interim": True,
                        "transcript": transcription["transcript"]
                    })
        
        asyncio.create_task(process_transcriptions())
        
        return response_queue
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close a voice session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session summary
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        session.end_time = datetime.utcnow()
        session.is_active = False
        self.active_sessions -= 1
        
        # Calculate session duration
        duration = (session.end_time - session.start_time).total_seconds()
        
        # Update analytics
        current_avg = self.analytics["average_session_duration"]
        total_sessions = self.analytics["total_sessions"]
        self.analytics["average_session_duration"] = (
            (current_avg * (total_sessions - 1) + duration) / total_sessions
        )
        self.analytics["total_interactions"] += session.interaction_count
        
        # Generate session summary
        summary = {
            "session_id": session_id,
            "duration": duration,
            "interactions": session.interaction_count,
            "language": session.language.value,
            "commands_processed": len([h for h in session.history if h["type"] == "user"])
        }
        
        # Clean up session after summary
        del self.sessions[session_id]
        
        return {
            "success": True,
            "summary": summary
        }
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a session."""
        session = self.sessions.get(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        return {
            "success": True,
            "session_id": session_id,
            "user_id": session.user_id,
            "is_active": session.is_active,
            "language": session.language.value,
            "voice_gender": session.voice_gender.value,
            "voice_profile": session.voice_profile,
            "interaction_count": session.interaction_count,
            "start_time": session.start_time.isoformat(),
            "last_interaction": session.last_interaction.isoformat() if session.last_interaction else None,
            "has_active_flow": self.flow_manager.active_flow is not None
        }
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get voice interface analytics."""
        return {
            **self.analytics,
            "active_sessions": self.active_sessions,
            "success_rate": (
                self.analytics["successful_commands"] / 
                (self.analytics["successful_commands"] + self.analytics["failed_commands"])
                if (self.analytics["successful_commands"] + self.analytics["failed_commands"]) > 0
                else 0
            )
        }