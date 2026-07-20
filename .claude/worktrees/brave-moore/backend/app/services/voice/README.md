# Voice Interface and Accessibility Services

A comprehensive voice interface system for the Financial Planning application with full accessibility support, multi-language capabilities, and conversational AI features.

## Features

### Core Voice Capabilities
- **Speech-to-Text (STT)**: Convert voice input to text using Google Cloud Speech-to-Text with offline fallback
- **Text-to-Speech (TTS)**: Generate natural speech from text using Google Cloud TTS and Amazon Polly
- **Voice Commands**: Natural language command parsing with financial domain understanding
- **Conversation Flows**: Multi-turn voice-guided form completion and workflows
- **Real-time Streaming**: WebSocket-based real-time voice interaction

### Accessibility Features
- **Screen Reader Support**: Full compatibility with JAWS, NVDA, VoiceOver, and TalkBack
- **ARIA Attributes**: Comprehensive ARIA labeling and landmarks
- **Keyboard Navigation**: Complete keyboard shortcut system
- **High Contrast Mode**: Support for visual accessibility
- **Voice Feedback**: Audio confirmation for all actions

### Multi-Language Support
Supported languages:
- English (en-US)
- Spanish (es-ES)
- French (fr-FR)
- German (de-DE)
- Italian (it-IT)
- Portuguese (pt-BR)
- Chinese (zh-CN)
- Japanese (ja-JP)
- Korean (ko-KR)
- Arabic (ar-SA)
- Hindi (hi-IN)
- Russian (ru-RU)

## Architecture

```
voice/
├── __init__.py                 # Package initialization
├── config.py                   # Configuration and settings
├── speech_to_text.py          # STT service implementation
├── text_to_speech.py          # TTS service implementation
├── voice_commands.py          # Command parsing and intent recognition
├── conversation_flow.py       # Multi-turn conversation management
├── voice_interface.py         # Main interface coordinator
└── accessibility_manager.py   # Accessibility features
```

## Configuration

### Environment Variables

```bash
# Google Cloud Speech-to-Text
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_SPEECH_MODEL=latest_long
GOOGLE_SPEECH_USE_ENHANCED=true

# Amazon Polly
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
POLLY_ENGINE=neural

# Azure Cognitive Services (optional)
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=your-region

# Voice Settings
DEFAULT_LANGUAGE=en-US
DEFAULT_VOICE_GENDER=NEUTRAL
DEFAULT_SPEECH_RATE=1.0
DEFAULT_PITCH=0.0

# Audio Settings
AUDIO_SAMPLE_RATE=16000
AUDIO_ENCODING=LINEAR16
MAX_RECORDING_DURATION=60
SILENCE_THRESHOLD=500
SILENCE_DURATION=1.5

# Accessibility
SCREEN_READER_ENABLED=true
HIGH_CONTRAST_MODE=false
KEYBOARD_NAVIGATION=true
VOICE_FEEDBACK_ENABLED=true
```

## API Endpoints

### Session Management

#### Create Voice Session
```http
POST /api/v1/voice/sessions
{
  "language": "en-US",
  "voice_gender": "NEUTRAL",
  "voice_profile": "professional"
}
```

#### Get Session Info
```http
GET /api/v1/voice/sessions/{session_id}
```

#### Close Session
```http
DELETE /api/v1/voice/sessions/{session_id}
```

### Voice Processing

#### Process Audio Input
```http
POST /api/v1/voice/sessions/{session_id}/audio
Content-Type: multipart/form-data

audio_file: [audio data]
auto_respond: true
```

#### Process Text Command
```http
POST /api/v1/voice/sessions/{session_id}/text
{
  "text": "What is my portfolio value?",
  "auto_respond": true
}
```

#### Synthesize Speech
```http
POST /api/v1/voice/synthesize
{
  "text": "Your portfolio is valued at $250,000",
  "language": "en-US",
  "voice_gender": "FEMALE",
  "output_format": "mp3"
}
```

### WebSocket Streaming
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/voice/sessions/{session_id}/stream');

// Send audio chunks
ws.send(audioChunk);

// Receive transcriptions and responses
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response);
};
```

### Conversation Flows

#### Start Flow
```http
POST /api/v1/voice/flows/{flow_id}/start
{
  "session_id": "session-123"
}
```

#### Get Flow Status
```http
GET /api/v1/voice/flows/status?session_id=session-123
```

### Accessibility

#### Get Accessibility Status
```http
GET /api/v1/voice/accessibility/status
```

#### Toggle Screen Reader
```http
POST /api/v1/voice/accessibility/screen-reader/toggle
```

#### Get Keyboard Shortcuts
```http
GET /api/v1/voice/accessibility/keyboard-shortcuts
```

## Voice Commands

### Navigation Commands
- "Go to portfolio"
- "Open my goals"
- "Show investments"
- "Navigate to settings"

### Query Commands
- "What is my portfolio value?"
- "How much have I saved for retirement?"
- "Show me my investment performance"
- "Calculate my retirement projection"

### Action Commands
- "Create a new goal"
- "Invest $5000 in stocks"
- "Rebalance my portfolio"
- "Update my risk profile"

### Voice Shortcuts
- "Portfolio summary" - Quick portfolio overview
- "Retirement status" - Retirement goal progress
- "Recent transactions" - Latest investment activity
- "Market update" - Market summary
- "Goal progress" - All goals status
- "Risk assessment" - Current risk profile
- "Tax summary" - YTD tax implications
- "Next steps" - Personalized recommendations

## Conversation Flows

### Available Flows

#### Create Goal Flow
Guides user through creating a financial goal:
1. Goal type selection
2. Goal naming
3. Target amount
4. Target date
5. Monthly contribution (optional)
6. Risk tolerance (optional)

#### Investment Transaction Flow
Executes investment transactions:
1. Transaction type (buy/sell)
2. Asset type
3. Ticker or fund name
4. Amount specification
5. Account selection

#### Portfolio Review Flow
Voice-guided portfolio analysis:
1. Review type selection
2. Time period
3. Benchmark comparison
4. Detail level

#### Retirement Planning Flow
Comprehensive retirement planning:
1. Current age
2. Retirement age
3. Current savings
4. Monthly income needed
5. Social Security expectations
6. Pension information
7. Inflation assumptions

## Usage Examples

### Python Client Example

```python
import asyncio
from app.services.voice import VoiceInterface

async def main():
    # Initialize interface
    interface = VoiceInterface()
    
    # Create session
    session_id = await interface.create_session(
        user_id="user123",
        language="en-US",
        voice_gender="FEMALE",
        voice_profile="friendly"
    )
    
    # Process voice command
    result = await interface.process_text_command(
        session_id,
        "What's my portfolio value?"
    )
    
    print(f"Response: {result['prompt']}")
    
    # Start a conversation flow
    flow_result = interface.flow_manager.start_flow("create_goal")
    print(f"Flow started: {flow_result['prompt']}")
    
    # Continue flow
    await interface.process_text_command(session_id, "retirement")
    await interface.process_text_command(session_id, "My Retirement Fund")
    await interface.process_text_command(session_id, "one million dollars")
    
    # Close session
    interface.close_session(session_id)

asyncio.run(main())
```

### JavaScript/TypeScript Example

```typescript
// Create voice session
const response = await fetch('/api/v1/voice/sessions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    language: 'en-US',
    voice_gender: 'NEUTRAL'
  })
});

const { session_id } = await response.json();

// Process text command
const commandResponse = await fetch(`/api/v1/voice/sessions/${session_id}/text`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    text: 'Show my retirement goal progress',
    auto_respond: true
  })
});

const result = await commandResponse.json();
console.log(result.prompt);

// Play audio response if available
if (result.audio) {
  const audio = new Audio(`data:audio/mp3;base64,${result.audio.audio_data}`);
  audio.play();
}
```

## Accessibility Integration

### Screen Reader Example

```python
from app.services.voice import AccessibilityManager

manager = AccessibilityManager()

# Enable screen reader
manager.toggle_screen_reader()

# Format content for screen reader
formatted = manager.format_for_screen_reader(
    content={"value": 250000, "change": 1250},
    element_type="currency",
    context={"label": "Portfolio Value"}
)

# Generate ARIA attributes
aria = manager.generate_aria_attributes(
    element_type="button",
    content="Start Voice Input",
    context={
        "label": "Start voice command input",
        "description": "Press to begin speaking",
        "required": False
    }
)
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+V | Toggle voice input |
| Ctrl+Shift+M | Start voice command |
| Ctrl+Shift+H | Voice help |
| Ctrl+Shift+S | Stop listening |
| Ctrl+Shift+R | Repeat last response |
| Alt+P | Portfolio summary |
| Alt+G | Goals summary |
| Alt+T | Transactions summary |
| F1 | Context help |
| Escape | Cancel action |
| Enter | Confirm action |

## Performance Optimization

### Caching
- Audio responses are cached for frequently used phrases
- Cache TTL: 24 hours
- Maximum cache size: 100 entries

### Streaming
- Real-time audio streaming via WebSocket
- Interim results for better UX
- Automatic reconnection on disconnect

### Resource Management
- Maximum concurrent sessions: 100
- Session timeout: 30 minutes of inactivity
- Audio chunk size: 4096 bytes for streaming

## Security Considerations

### Privacy
- Profanity filter enabled by default
- PII redaction in transcriptions
- Audio data not permanently stored
- Session data encrypted in transit

### Authentication
- All endpoints require authentication
- Session-based access control
- User-specific voice profiles

### Rate Limiting
- 100 requests per minute per user
- 1000 synthesis requests per day
- WebSocket connection limit: 10 per user

## Troubleshooting

### Common Issues

#### No Audio Output
1. Check TTS service credentials
2. Verify audio format compatibility
3. Ensure browser audio permissions

#### Poor Recognition Accuracy
1. Check microphone quality
2. Reduce background noise
3. Speak clearly and at moderate pace
4. Verify language settings match speech

#### Slow Response Times
1. Check network latency
2. Enable audio caching
3. Use streaming for long interactions
4. Consider offline TTS for common phrases

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

Run tests:
```bash
pytest tests/test_voice_interface.py -v
```

Test coverage:
```bash
pytest tests/test_voice_interface.py --cov=app.services.voice --cov-report=html
```

## Future Enhancements

- [ ] Voice biometric authentication
- [ ] Custom wake word detection
- [ ] Emotion detection in voice
- [ ] Voice-based portfolio visualization descriptions
- [ ] Integration with smart speakers (Alexa, Google Home)
- [ ] Offline mode with local models
- [ ] Voice training for personalization
- [ ] Multi-speaker conversation support