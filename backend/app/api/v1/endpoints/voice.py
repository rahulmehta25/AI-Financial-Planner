"""Voice Interface API Endpoints."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import base64

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.database.utils import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.voice import (
    VoiceInterface,
    AccessibilityManager,
    Language,
    VoiceGender
)
from app.services.voice.config import VoiceSettings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize voice services
voice_interface = VoiceInterface()
accessibility_manager = AccessibilityManager()


@router.post("/sessions")
async def create_voice_session(
    language: Optional[str] = None,
    voice_gender: Optional[str] = None,
    voice_profile: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new voice session.
    
    - **language**: Preferred language (en-US, es-ES, fr-FR, etc.)
    - **voice_gender**: Preferred voice gender (MALE, FEMALE, NEUTRAL)
    - **voice_profile**: Voice profile (professional, friendly, assistive)
    """
    try:
        # Parse language and gender if provided
        lang = Language(language) if language else None
        gender = VoiceGender(voice_gender) if voice_gender else None
        
        session_id = await voice_interface.create_session(
            user_id=str(current_user.id),
            language=lang,
            voice_gender=gender,
            voice_profile=voice_profile
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Voice session created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/audio")
async def process_audio(
    session_id: str,
    audio_file: UploadFile = File(...),
    auto_respond: bool = Form(True),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process audio input and get response.
    
    - **session_id**: Voice session ID
    - **audio_file**: Audio file (WAV, MP3, OGG)
    - **auto_respond**: Generate audio response
    """
    try:
        # Read audio data
        audio_data = await audio_file.read()
        
        # Process audio
        result = await voice_interface.process_audio(
            session_id,
            audio_data,
            auto_respond=auto_respond
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/text")
async def process_text_command(
    session_id: str,
    text: str,
    auto_respond: bool = True,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process text command and get response.
    
    - **session_id**: Voice session ID
    - **text**: Command text
    - **auto_respond**: Generate audio response
    """
    try:
        result = await voice_interface.process_text_command(
            session_id,
            text,
            auto_respond=auto_respond
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing text command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(
    text: str,
    language: Optional[str] = None,
    voice_gender: Optional[str] = None,
    voice_profile: Optional[str] = None,
    output_format: str = "mp3",
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Synthesize text to speech.
    
    - **text**: Text to synthesize
    - **language**: Target language
    - **voice_gender**: Voice gender
    - **voice_profile**: Voice profile
    - **output_format**: Audio format (mp3, wav, ogg)
    """
    try:
        # Create temporary session for synthesis
        session_id = await voice_interface.create_session(
            user_id=str(current_user.id)
        )
        
        # Generate audio
        audio_response = await voice_interface.generate_audio_response(
            session_id,
            text
        )
        
        # Close temporary session
        voice_interface.close_session(session_id)
        
        if not audio_response.get("success"):
            raise HTTPException(status_code=500, detail=audio_response.get("error"))
        
        # Return audio stream
        audio_data = audio_response.get("audio_data")
        if audio_data:
            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type=f"audio/{output_format}",
                headers={
                    "Content-Disposition": f"attachment; filename=speech.{output_format}"
                }
            )
        
        raise HTTPException(status_code=500, detail="Failed to generate audio")
        
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/sessions/{session_id}/stream")
async def stream_voice_session(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for real-time voice streaming.
    
    Sends audio chunks to the server and receives transcriptions and responses.
    """
    await websocket.accept()
    
    # Create audio stream queue
    audio_stream = asyncio.Queue()
    
    # Start processing stream
    response_queue = await voice_interface.stream_process(session_id, audio_stream)
    
    try:
        # Handle bidirectional communication
        async def receive_audio():
            """Receive audio chunks from client."""
            while True:
                try:
                    data = await websocket.receive_bytes()
                    await audio_stream.put(data)
                except WebSocketDisconnect:
                    await audio_stream.put(None)  # Signal end of stream
                    break
        
        async def send_responses():
            """Send responses to client."""
            while True:
                response = await response_queue.get()
                await websocket.send_json(response)
                
                if response.get("session_ended"):
                    break
        
        # Run both tasks concurrently
        await asyncio.gather(
            receive_audio(),
            send_responses()
        )
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.get("/sessions/{session_id}")
async def get_session_info(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get information about a voice session."""
    return voice_interface.get_session_info(session_id)


@router.delete("/sessions/{session_id}")
async def close_voice_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Close a voice session."""
    return voice_interface.close_session(session_id)


@router.get("/flows")
async def get_available_flows(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available conversation flows."""
    flows = voice_interface.flow_manager.flows
    
    return {
        "flows": [
            {
                "id": flow_id,
                "name": flow.name,
                "description": flow.description,
                "fields_count": len(flow.fields)
            }
            for flow_id, flow in flows.items()
        ]
    }


@router.post("/flows/{flow_id}/start")
async def start_conversation_flow(
    flow_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start a conversation flow."""
    return voice_interface.flow_manager.start_flow(flow_id)


@router.get("/flows/status")
async def get_flow_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current flow status."""
    return voice_interface.flow_manager.get_flow_state()


@router.post("/flows/cancel")
async def cancel_flow(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Cancel current conversation flow."""
    return voice_interface.flow_manager.cancel_flow()


@router.get("/shortcuts")
async def get_voice_shortcuts(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available voice shortcuts."""
    return {
        "shortcuts": voice_interface.shortcuts
    }


@router.get("/analytics")
async def get_voice_analytics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get voice interface analytics."""
    return voice_interface.get_analytics()


# Accessibility endpoints

@router.get("/accessibility/status")
async def get_accessibility_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get accessibility settings status."""
    return accessibility_manager.get_accessibility_status()


@router.post("/accessibility/screen-reader/toggle")
async def toggle_screen_reader(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Toggle screen reader on/off."""
    enabled = accessibility_manager.toggle_screen_reader()
    return {
        "screen_reader_enabled": enabled,
        "message": f"Screen reader {'enabled' if enabled else 'disabled'}"
    }


@router.put("/accessibility/verbosity")
async def set_verbosity_level(
    level: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Set screen reader verbosity level.
    
    - **level**: Verbosity level (low, medium, high)
    """
    if level not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Invalid verbosity level")
    
    accessibility_manager.set_verbosity_level(level)
    return {
        "verbosity_level": level,
        "message": f"Verbosity level set to {level}"
    }


@router.get("/accessibility/keyboard-shortcuts")
async def get_keyboard_shortcuts(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get keyboard shortcuts for voice commands."""
    return {
        "shortcuts": accessibility_manager.keyboard_shortcuts
    }


@router.post("/accessibility/format")
async def format_for_screen_reader(
    content: Any,
    element_type: str = "text",
    context: Optional[Dict] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Format content for screen reader.
    
    - **content**: Content to format
    - **element_type**: Type of element
    - **context**: Additional context
    """
    formatted = accessibility_manager.format_for_screen_reader(
        content, element_type, context
    )
    
    return {
        "formatted_text": formatted,
        "aria_attributes": accessibility_manager.generate_aria_attributes(
            element_type, content, context
        )
    }


@router.get("/accessibility/landmarks")
async def get_landmarks(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get navigation landmarks."""
    return {
        "landmarks": list(accessibility_manager.landmarks.keys())
    }


@router.post("/accessibility/landmarks/{landmark_label}/navigate")
async def navigate_to_landmark(
    landmark_label: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Navigate to a specific landmark."""
    return accessibility_manager.navigate_to_landmark(landmark_label)


@router.get("/accessibility/report")
async def get_accessibility_report(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get accessibility compliance report."""
    return accessibility_manager.export_accessibility_report()


@router.get("/languages")
async def get_supported_languages(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get supported languages for voice services."""
    settings = VoiceSettings()
    return {
        "languages": [
            {
                "code": lang.value,
                "name": lang.name.replace("_", " ").title()
            }
            for lang in settings.supported_languages
        ],
        "default": settings.default_language.value
    }


@router.get("/voices")
async def get_available_voices(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available voices from all providers."""
    return voice_interface.tts_service.get_available_voices()


@router.get("/voice-profiles")
async def get_voice_profiles(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available voice profiles."""
    from app.services.voice.config import VOICE_PROFILES
    
    return {
        "profiles": [
            {
                "name": name,
                "settings": settings
            }
            for name, settings in VOICE_PROFILES.items()
        ]
    }