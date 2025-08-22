"""Tests for Voice Interface Services."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

from app.services.voice import (
    VoiceInterface,
    SpeechToTextService,
    TextToSpeechService,
    VoiceCommandParser,
    ConversationFlowManager,
    AccessibilityManager
)
from app.services.voice.config import Language, VoiceGender, VoiceSettings
from app.services.voice.voice_commands import CommandIntent
from app.services.voice.conversation_flow import ConversationState, FormField, ConversationFlow


class TestSpeechToText:
    """Test Speech-to-Text Service."""
    
    @pytest.fixture
    def stt_service(self):
        return SpeechToTextService()
    
    def test_initialization(self, stt_service):
        """Test STT service initialization."""
        assert stt_service is not None
        assert stt_service.settings is not None
        assert stt_service.recognizer is not None
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_offline(self, stt_service):
        """Test offline audio transcription."""
        # Mock audio data
        audio_data = b"mock_audio_data"
        
        with patch.object(stt_service, '_transcribe_offline') as mock_transcribe:
            mock_transcribe.return_value = {
                "success": True,
                "transcript": "Hello world",
                "provider": "offline"
            }
            
            result = await stt_service.transcribe_audio(audio_data)
            
            assert result["success"] is True
            assert result["transcript"] == "Hello world"
            assert result["provider"] == "offline"
    
    def test_detect_voice_activity(self, stt_service):
        """Test voice activity detection."""
        # Mock audio with silence
        audio_data = bytes(16000 * 2)  # 1 second of silence
        
        segments = stt_service.detect_voice_activity(audio_data)
        
        assert isinstance(segments, list)
    
    def test_apply_noise_reduction(self, stt_service):
        """Test noise reduction."""
        audio_data = bytes(16000 * 2)  # 1 second of audio
        
        processed = stt_service.apply_noise_reduction(audio_data)
        
        assert isinstance(processed, bytes)
    
    @pytest.mark.asyncio
    async def test_language_detection(self, stt_service):
        """Test language detection."""
        audio_data = b"mock_audio_data"
        
        with patch.object(stt_service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = {
                "success": True,
                "alternatives": [{"confidence": 0.9}]
            }
            
            language = await stt_service.detect_language(audio_data)
            
            assert isinstance(language, Language)


class TestTextToSpeech:
    """Test Text-to-Speech Service."""
    
    @pytest.fixture
    def tts_service(self):
        return TextToSpeechService()
    
    def test_initialization(self, tts_service):
        """Test TTS service initialization."""
        assert tts_service is not None
        assert tts_service.settings is not None
        assert tts_service.audio_cache is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_offline(self, tts_service):
        """Test offline speech synthesis."""
        text = "Hello world"
        
        with patch.object(tts_service, '_synthesize_offline') as mock_synth:
            mock_synth.return_value = {
                "success": True,
                "audio_data": b"audio_data",
                "provider": "offline"
            }
            
            result = await tts_service.synthesize_speech(text)
            
            assert result["success"] is True
            assert result["audio_data"] == b"audio_data"
            assert result["provider"] == "offline"
    
    def test_preprocess_text(self, tts_service):
        """Test text preprocessing."""
        text = "Your 401k balance is $10,000 with 5% returns"
        
        processed = tts_service._preprocess_text(text)
        
        assert "401 K" in processed
        assert "dollars" in processed
        assert "percent" in processed
    
    def test_cache_management(self, tts_service):
        """Test audio cache management."""
        cache_key = tts_service._get_cache_key(
            "test", Language.ENGLISH, VoiceGender.NEUTRAL, "mp3"
        )
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 64  # SHA256 hash length
    
    @pytest.mark.asyncio
    async def test_ssml_synthesis(self, tts_service):
        """Test SSML synthesis."""
        ssml = "<speak>Hello <break time='1s'/> world</speak>"
        
        with patch.object(tts_service, 'synthesize_speech') as mock_synth:
            mock_synth.return_value = {
                "success": True,
                "audio_data": b"audio_data"
            }
            
            result = await tts_service.synthesize_ssml(ssml)
            
            assert result["success"] is True


class TestVoiceCommands:
    """Test Voice Command Parser."""
    
    @pytest.fixture
    def parser(self):
        return VoiceCommandParser()
    
    def test_initialization(self, parser):
        """Test parser initialization."""
        assert parser is not None
        assert parser.command_patterns is not None
        assert parser.entity_extractors is not None
    
    def test_parse_navigation_command(self, parser):
        """Test navigation command parsing."""
        command = "Go to my portfolio"
        
        result = parser.parse_command(command)
        
        assert result["intent"] == CommandIntent.NAVIGATION
        assert result["confidence"] > 0.5
    
    def test_parse_query_command(self, parser):
        """Test query command parsing."""
        command = "What is my portfolio value?"
        
        result = parser.parse_command(command)
        
        assert result["intent"] == CommandIntent.QUERY
        assert result["confidence"] > 0.5
    
    def test_parse_action_command(self, parser):
        """Test action command parsing."""
        command = "Invest $5000 in stocks"
        
        result = parser.parse_command(command)
        
        assert result["intent"] == CommandIntent.ACTION
        assert "amount" in result["entities"]
        assert result["entities"]["amount"] == 5000.0
    
    def test_extract_entities(self, parser):
        """Test entity extraction."""
        text = "Transfer $1,500 from my 401k to IRA account in 3 months"
        
        entities = parser._extract_entities(text)
        
        assert "amount" in entities
        assert entities["amount"] == 1500.0
        assert "account_type" in entities
        assert "time_period" in entities
    
    def test_format_response_for_speech(self, parser):
        """Test response formatting for speech."""
        data = {
            "portfolio_value": 250000,
            "change_today": 1250
        }
        
        formatted = parser.format_response_for_speech(data)
        
        assert isinstance(formatted, str)
        assert "Portfolio Value" in formatted
        assert "250 thousand" in formatted or "250,000" in formatted
    
    def test_confirmation_prompt_generation(self, parser):
        """Test confirmation prompt generation."""
        action = "Transfer funds"
        entities = {
            "amount": 5000,
            "account_type": "IRA"
        }
        
        prompt = parser.generate_confirmation_prompt(action, entities)
        
        assert "confirm" in prompt.lower()
        assert "5,000" in prompt or "5000" in prompt
        assert "IRA" in prompt
    
    def test_help_response(self, parser):
        """Test help response generation."""
        help_text = parser.get_help_response("portfolio")
        
        assert isinstance(help_text, str)
        assert "portfolio" in help_text.lower()
    
    def test_context_management(self, parser):
        """Test conversation context."""
        parser.parse_command("What is my portfolio value?")
        parser.parse_command("How about my goals?")
        
        assert len(parser.context_stack) == 2
        
        parser.clear_context()
        assert len(parser.context_stack) == 0


class TestConversationFlow:
    """Test Conversation Flow Manager."""
    
    @pytest.fixture
    def flow_manager(self):
        return ConversationFlowManager()
    
    def test_initialization(self, flow_manager):
        """Test flow manager initialization."""
        assert flow_manager is not None
        assert len(flow_manager.flows) > 0
        assert "create_goal" in flow_manager.flows
    
    def test_start_flow(self, flow_manager):
        """Test starting a conversation flow."""
        result = flow_manager.start_flow("create_goal")
        
        assert result["success"] is True
        assert result["flow_name"] == "Create Financial Goal"
        assert result["prompt"] is not None
        assert flow_manager.active_flow is not None
    
    @pytest.mark.asyncio
    async def test_process_input(self, flow_manager):
        """Test processing user input in flow."""
        flow_manager.start_flow("create_goal")
        
        result = await flow_manager.process_input("retirement")
        
        assert result["success"] is True
        assert "prompt" in result
        assert flow_manager.active_flow.collected_data.get("goal_type") == "retirement"
    
    @pytest.mark.asyncio
    async def test_field_validation(self, flow_manager):
        """Test field validation in flow."""
        # Create test flow with validation
        test_flow = ConversationFlow(
            flow_id="test",
            name="Test Flow",
            description="Test",
            fields=[
                FormField(
                    name="amount",
                    prompt="Enter amount",
                    field_type="currency",
                    validation=lambda x: x > 0
                )
            ]
        )
        
        flow_manager.register_flow(test_flow)
        flow_manager.start_flow("test")
        
        # Test invalid input
        result = await flow_manager.process_input("-100")
        assert result["success"] is False
        
        # Test valid input
        result = await flow_manager.process_input("1000")
        assert result.get("flow_completed") is True
    
    @pytest.mark.asyncio
    async def test_flow_completion(self, flow_manager):
        """Test flow completion."""
        # Start simple flow
        flow_manager.start_flow("portfolio_review")
        
        # Complete all fields
        await flow_manager.process_input("performance")
        await flow_manager.process_input("this month")
        await flow_manager.process_input("yes")
        result = await flow_manager.process_input("yes")
        
        assert result.get("flow_completed") is True
        assert flow_manager.active_flow is None
    
    def test_cancel_flow(self, flow_manager):
        """Test canceling a flow."""
        flow_manager.start_flow("create_goal")
        
        result = flow_manager.cancel_flow()
        
        assert result["success"] is True
        assert flow_manager.active_flow is None


class TestVoiceInterface:
    """Test Main Voice Interface."""
    
    @pytest.fixture
    def voice_interface(self):
        return VoiceInterface()
    
    @pytest.mark.asyncio
    async def test_create_session(self, voice_interface):
        """Test session creation."""
        session_id = await voice_interface.create_session(
            user_id="test_user",
            language=Language.ENGLISH,
            voice_gender=VoiceGender.NEUTRAL
        )
        
        assert session_id is not None
        assert session_id in voice_interface.sessions
    
    @pytest.mark.asyncio
    async def test_process_text_command(self, voice_interface):
        """Test text command processing."""
        session_id = await voice_interface.create_session()
        
        result = await voice_interface.process_text_command(
            session_id,
            "What is my portfolio value?",
            auto_respond=False
        )
        
        assert result is not None
        assert "prompt" in result
    
    @pytest.mark.asyncio
    async def test_audio_response_generation(self, voice_interface):
        """Test audio response generation."""
        session_id = await voice_interface.create_session()
        
        with patch.object(voice_interface.tts_service, 'synthesize_speech') as mock_synth:
            mock_synth.return_value = {
                "success": True,
                "audio_data": b"audio_data"
            }
            
            result = await voice_interface.generate_audio_response(
                session_id,
                "Hello world"
            )
            
            assert result["success"] is True
    
    def test_close_session(self, voice_interface):
        """Test session closing."""
        async def test():
            session_id = await voice_interface.create_session()
            
            result = voice_interface.close_session(session_id)
            
            assert result["success"] is True
            assert session_id not in voice_interface.sessions
        
        asyncio.run(test())
    
    def test_get_analytics(self, voice_interface):
        """Test analytics retrieval."""
        analytics = voice_interface.get_analytics()
        
        assert "total_sessions" in analytics
        assert "success_rate" in analytics
        assert "active_sessions" in analytics


class TestAccessibilityManager:
    """Test Accessibility Manager."""
    
    @pytest.fixture
    def accessibility_manager(self):
        return AccessibilityManager()
    
    def test_initialization(self, accessibility_manager):
        """Test accessibility manager initialization."""
        assert accessibility_manager is not None
        assert accessibility_manager.keyboard_shortcuts is not None
        assert len(accessibility_manager.keyboard_shortcuts) > 0
    
    def test_format_for_screen_reader(self, accessibility_manager):
        """Test screen reader formatting."""
        # Test button
        formatted = accessibility_manager.format_for_screen_reader(
            "Submit", "button"
        )
        assert "Button" in formatted
        assert "Press Enter" in formatted
        
        # Test currency
        formatted = accessibility_manager.format_for_screen_reader(
            250000.50, "currency"
        )
        assert "$" in formatted
        assert "250,000.50" in formatted
        
        # Test table
        formatted = accessibility_manager.format_for_screen_reader(
            [[1, 2], [3, 4]], "table"
        )
        assert "Table" in formatted
        assert "2 rows" in formatted
    
    def test_generate_aria_attributes(self, accessibility_manager):
        """Test ARIA attribute generation."""
        aria = accessibility_manager.generate_aria_attributes(
            "button",
            "Submit",
            {"label": "Submit form", "required": True}
        )
        
        assert aria["role"] == "button"
        assert aria["aria-label"] == "Submit form"
        assert aria["aria-required"] == "true"
    
    def test_create_landmark(self, accessibility_manager):
        """Test landmark creation."""
        landmark = accessibility_manager.create_landmark(
            "navigation",
            "Main Navigation",
            ["Home", "Portfolio", "Goals"]
        )
        
        assert landmark["type"] == "navigation"
        assert landmark["label"] == "Main Navigation"
        assert landmark["aria"]["role"] == "navigation"
    
    def test_navigate_to_landmark(self, accessibility_manager):
        """Test landmark navigation."""
        # Create landmark first
        accessibility_manager.create_landmark(
            "main",
            "Main Content",
            "Content here"
        )
        
        result = accessibility_manager.navigate_to_landmark("Main Content")
        
        assert result["success"] is True
        assert result["announcement"] == "Navigated to Main Content"
    
    def test_keyboard_shortcuts(self, accessibility_manager):
        """Test keyboard shortcut handling."""
        result = accessibility_manager.handle_keyboard_shortcut("ctrl+shift+v")
        
        assert result["success"] is True
        assert result["action"] == "toggle_voice"
    
    def test_toggle_screen_reader(self, accessibility_manager):
        """Test screen reader toggle."""
        initial_state = accessibility_manager.screen_reader_enabled
        
        new_state = accessibility_manager.toggle_screen_reader()
        
        assert new_state != initial_state
    
    def test_verbosity_levels(self, accessibility_manager):
        """Test verbosity level changes."""
        accessibility_manager.set_verbosity_level("high")
        assert accessibility_manager.verbosity_level == "high"
        
        accessibility_manager.set_verbosity_level("low")
        assert accessibility_manager.verbosity_level == "low"
    
    def test_accessibility_report(self, accessibility_manager):
        """Test accessibility report generation."""
        report = accessibility_manager.export_accessibility_report()
        
        assert "wcag_compliance" in report
        assert "features" in report
        assert "languages_supported" in report
        assert len(report["languages_supported"]) > 0


# Integration Tests

class TestVoiceIntegration:
    """Integration tests for voice services."""
    
    @pytest.mark.asyncio
    async def test_full_voice_flow(self):
        """Test complete voice interaction flow."""
        interface = VoiceInterface()
        
        # Create session
        session_id = await interface.create_session(
            user_id="test_user",
            language=Language.ENGLISH
        )
        
        # Process command
        result = await interface.process_text_command(
            session_id,
            "Create a new retirement goal"
        )
        
        # Should start goal creation flow
        assert interface.flow_manager.active_flow is not None
        assert interface.flow_manager.active_flow.flow_id == "create_goal"
        
        # Continue flow
        await interface.process_text_command(session_id, "retirement")
        await interface.process_text_command(session_id, "My Retirement Fund")
        await interface.process_text_command(session_id, "one million dollars")
        
        # Close session
        interface.close_session(session_id)
    
    @pytest.mark.asyncio
    async def test_multilingual_support(self):
        """Test multi-language support."""
        interface = VoiceInterface()
        
        for language in [Language.ENGLISH, Language.SPANISH, Language.FRENCH]:
            session_id = await interface.create_session(language=language)
            
            session = interface.sessions[session_id]
            assert session.language == language
            
            interface.close_session(session_id)
    
    @pytest.mark.asyncio
    async def test_accessibility_integration(self):
        """Test accessibility integration."""
        interface = VoiceInterface()
        accessibility = AccessibilityManager()
        
        # Enable screen reader
        accessibility.toggle_screen_reader()
        
        # Format voice response for screen reader
        formatted = accessibility.format_for_screen_reader(
            "Your portfolio value is $250,000",
            "text"
        )
        
        assert formatted is not None
        
        # Generate ARIA attributes for voice controls
        aria = accessibility.generate_aria_attributes(
            "button",
            "Start Voice Command",
            {"label": "Press to start voice input"}
        )
        
        assert aria["aria-label"] == "Press to start voice input"