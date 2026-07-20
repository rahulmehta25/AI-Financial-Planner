import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Settings,
  Activity,
  MessageCircle,
  Globe,
  User,
  HelpCircle,
  X,
  Check,
  AlertCircle,
  Loader,
  ChevronDown,
  ChevronUp,
  Headphones,
  Keyboard,
  Eye
} from 'lucide-react';

interface VoiceInterfaceProps {
  apiEndpoint: string;
  authToken: string;
  language?: string;
  enableWakeWord?: boolean;
  autoPlay?: boolean;
  theme?: 'light' | 'dark';
}

interface VoiceSession {
  sessionId: string;
  isActive: boolean;
  language: string;
  voiceGender: string;
  voiceProfile: string;
}

interface TranscriptEntry {
  id: string;
  type: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: Date;
  confidence?: number;
  intent?: any;
  entities?: any[];
}

const VoiceInterface: React.FC<VoiceInterfaceProps> = ({
  apiEndpoint,
  authToken,
  language = 'en-US',
  enableWakeWord = false,
  autoPlay = true,
  theme = 'light'
}) => {
  // State management
  const [session, setSession] = useState<VoiceSession | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState({
    language,
    voiceGender: 'NEUTRAL',
    voiceProfile: 'professional',
    speechRate: 1.0,
    pitch: 0,
    volume: 1.0,
    enableWakeWord,
    wakeWord: 'hey finance',
    sensitivity: 0.5,
    autoPlay,
    enableScreenReader: false,
    verbosityLevel: 'medium',
    keyboardNavigation: true,
    showTranscript: true,
    showVisualizer: true
  });
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showAccessibility, setShowAccessibility] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const webSocketRef = useRef<WebSocket | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const audioElementRef = useRef<HTMLAudioElement>(null);

  // WebSocket connection
  useEffect(() => {
    if (session?.sessionId) {
      connectWebSocket();
    }
    return () => {
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
    };
  }, [session]);

  const connectWebSocket = () => {
    setConnectionStatus('connecting');
    const wsUrl = `${apiEndpoint.replace('http', 'ws')}/voice/sessions/${session?.sessionId}/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnectionStatus('connected');
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error. Please try again.');
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');
      console.log('WebSocket disconnected');
    };

    webSocketRef.current = ws;
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'interim_transcript':
        setInterimTranscript(data.text);
        break;
      
      case 'final_transcript':
        addTranscriptEntry({
          id: Date.now().toString(),
          type: 'user',
          text: data.text,
          timestamp: new Date(),
          confidence: data.confidence,
          intent: data.intent,
          entities: data.entities
        });
        setInterimTranscript('');
        break;
      
      case 'audio_response':
        if (autoPlay && data.audio) {
          playAudioResponse(data.audio, data.format);
        }
        addTranscriptEntry({
          id: Date.now().toString(),
          type: 'assistant',
          text: data.text,
          timestamp: new Date()
        });
        break;
      
      case 'command_result':
        handleCommandResult(data.result);
        break;
      
      case 'wake_word_detected':
        handleWakeWordDetected();
        break;
      
      case 'error':
        setError(data.error);
        setIsProcessing(false);
        setIsListening(false);
        break;
    }
  };

  // Create voice session
  const createSession = async () => {
    try {
      const response = await fetch(`${apiEndpoint}/voice/sessions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          language: settings.language,
          voice_gender: settings.voiceGender,
          voice_profile: settings.voiceProfile
        })
      });

      const data = await response.json();
      if (data.success) {
        setSession({
          sessionId: data.session_id,
          isActive: true,
          language: settings.language,
          voiceGender: settings.voiceGender,
          voiceProfile: settings.voiceProfile
        });
      } else {
        throw new Error(data.message || 'Failed to create session');
      }
    } catch (error) {
      console.error('Error creating session:', error);
      setError('Failed to create voice session');
    }
  };

  // Start/stop listening
  const toggleListening = async () => {
    if (isListening) {
      stopListening();
    } else {
      await startListening();
    }
  };

  const startListening = async () => {
    if (!session) {
      await createSession();
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Set up audio context for visualization
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      // Start visualization
      visualizeAudio();

      // Set up media recorder
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          
          // Send audio chunk via WebSocket if streaming
          if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
            const reader = new FileReader();
            reader.onloadend = () => {
              const base64 = reader.result?.toString().split(',')[1];
              webSocketRef.current?.send(JSON.stringify({
                type: 'audio_data',
                audio: base64
              }));
            };
            reader.readAsDataURL(event.data);
          }
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (!webSocketRef.current || webSocketRef.current.readyState !== WebSocket.OPEN) {
          // Send complete audio if not streaming
          await sendAudioForProcessing(audioBlob);
        }
      };

      mediaRecorder.start(100); // Collect data every 100ms for streaming
      setIsListening(true);
      
      // Send start listening message
      webSocketRef.current?.send(JSON.stringify({
        type: 'start_listening',
        streaming: true,
        language: settings.language
      }));

    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Microphone access denied. Please grant permission and try again.');
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    
    setIsListening(false);
    setAudioLevel(0);
    
    // Send stop listening message
    webSocketRef.current?.send(JSON.stringify({
      type: 'stop_listening'
    }));
  };

  // Audio visualization
  const visualizeAudio = () => {
    if (!analyserRef.current || !isListening) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    setAudioLevel(average / 255);

    requestAnimationFrame(visualizeAudio);
  };

  // Send audio for processing
  const sendAudioForProcessing = async (audioBlob: Blob) => {
    if (!session) return;

    setIsProcessing(true);
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.webm');
    formData.append('auto_respond', settings.autoPlay.toString());

    try {
      const response = await fetch(`${apiEndpoint}/voice/sessions/${session.sessionId}/audio`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData
      });

      const data = await response.json();
      handleCommandResult(data);
    } catch (error) {
      console.error('Error processing audio:', error);
      setError('Failed to process audio');
    } finally {
      setIsProcessing(false);
    }
  };

  // Play audio response
  const playAudioResponse = (audioBase64: string, format: string) => {
    const audio = new Audio(`data:audio/${format};base64,${audioBase64}`);
    audio.volume = settings.volume;
    audio.playbackRate = settings.speechRate;
    
    audio.onplay = () => setIsSpeaking(true);
    audio.onended = () => setIsSpeaking(false);
    
    audio.play().catch(error => {
      console.error('Error playing audio:', error);
      setError('Failed to play audio response');
    });
    
    audioElementRef.current = audio;
  };

  // Handle command result
  const handleCommandResult = (result: any) => {
    if (result.action) {
      // Handle specific actions
      switch (result.action) {
        case 'show_balance_screen':
          // Navigate to balance screen
          window.location.href = '/dashboard/balance';
          break;
        case 'show_portfolio_screen':
          window.location.href = '/dashboard/portfolio';
          break;
        case 'show_goals_screen':
          window.location.href = '/dashboard/goals';
          break;
        // Add more action handlers
      }
    }
  };

  // Handle wake word detection
  const handleWakeWordDetected = () => {
    if (!isListening) {
      // Play wake sound
      const wakeSound = new Audio('/sounds/wake.mp3');
      wakeSound.play();
      
      // Start listening
      startListening();
    }
  };

  // Add transcript entry
  const addTranscriptEntry = (entry: TranscriptEntry) => {
    setTranscript(prev => [...prev, entry]);
    
    // Scroll to bottom
    setTimeout(() => {
      transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // Send text command
  const sendTextCommand = async (text: string) => {
    if (!session) {
      await createSession();
    }

    addTranscriptEntry({
      id: Date.now().toString(),
      type: 'user',
      text,
      timestamp: new Date()
    });

    setIsProcessing(true);

    try {
      const response = await fetch(`${apiEndpoint}/voice/sessions/${session?.sessionId}/text`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text,
          auto_respond: settings.autoPlay
        })
      });

      const data = await response.json();
      handleCommandResult(data);
    } catch (error) {
      console.error('Error sending text command:', error);
      setError('Failed to process command');
    } finally {
      setIsProcessing(false);
    }
  };

  // Enable/disable wake word
  const toggleWakeWord = () => {
    if (settings.enableWakeWord) {
      webSocketRef.current?.send(JSON.stringify({
        type: 'disable_wake_word'
      }));
    } else {
      webSocketRef.current?.send(JSON.stringify({
        type: 'enable_wake_word',
        wake_word: settings.wakeWord,
        sensitivity: settings.sensitivity,
        auto_listen: true
      }));
    }
    
    setSettings(prev => ({ ...prev, enableWakeWord: !prev.enableWakeWord }));
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!settings.keyboardNavigation) return;

      // Ctrl+Shift+M: Start/stop listening
      if (e.ctrlKey && e.shiftKey && e.key === 'M') {
        e.preventDefault();
        toggleListening();
      }
      
      // Ctrl+Shift+H: Show help
      if (e.ctrlKey && e.shiftKey && e.key === 'H') {
        e.preventDefault();
        setShowHelp(!showHelp);
      }
      
      // Escape: Cancel current action
      if (e.key === 'Escape') {
        stopListening();
        setIsProcessing(false);
        setError(null);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [settings.keyboardNavigation, showHelp]);

  return (
    <div className={`voice-interface ${theme}`} role="application" aria-label="Voice Interface">
      {/* Main Controls */}
      <div className="voice-controls" role="toolbar">
        <button
          className={`mic-button ${isListening ? 'listening' : ''} ${isProcessing ? 'processing' : ''}`}
          onClick={toggleListening}
          disabled={isProcessing}
          aria-label={isListening ? 'Stop listening' : 'Start listening'}
          aria-pressed={isListening}
        >
          {isProcessing ? (
            <Loader className="animate-spin" size={32} />
          ) : isListening ? (
            <MicOff size={32} />
          ) : (
            <Mic size={32} />
          )}
          
          {/* Audio level indicator */}
          {isListening && settings.showVisualizer && (
            <div 
              className="audio-level-ring" 
              style={{ 
                transform: `scale(${1 + audioLevel * 0.5})`,
                opacity: 0.3 + audioLevel * 0.7
              }}
            />
          )}
        </button>

        {/* Status indicators */}
        <div className="status-indicators" role="status" aria-live="polite">
          {connectionStatus === 'connected' && (
            <span className="status-badge connected">
              <Activity size={16} /> Connected
            </span>
          )}
          
          {isListening && (
            <span className="status-badge listening">
              <Mic size={16} /> Listening...
            </span>
          )}
          
          {isProcessing && (
            <span className="status-badge processing">
              <Loader className="animate-spin" size={16} /> Processing...
            </span>
          )}
          
          {isSpeaking && (
            <span className="status-badge speaking">
              <Volume2 size={16} /> Speaking...
            </span>
          )}
          
          {settings.enableWakeWord && (
            <span className="status-badge wake-word">
              <MessageCircle size={16} /> Wake word: {settings.wakeWord}
            </span>
          )}
        </div>

        {/* Action buttons */}
        <div className="action-buttons">
          <button
            onClick={() => setShowSettings(!showSettings)}
            aria-label="Settings"
            title="Settings (Ctrl+Shift+S)"
          >
            <Settings size={20} />
          </button>
          
          <button
            onClick={() => setShowHelp(!showHelp)}
            aria-label="Help"
            title="Help (Ctrl+Shift+H)"
          >
            <HelpCircle size={20} />
          </button>
          
          <button
            onClick={() => setShowAccessibility(!showAccessibility)}
            aria-label="Accessibility"
            title="Accessibility options"
          >
            <Eye size={20} />
          </button>
        </div>
      </div>

      {/* Transcript */}
      {settings.showTranscript && (
        <div className="transcript-container" role="log" aria-label="Conversation transcript">
          <h3>Conversation</h3>
          <div className="transcript-scroll">
            {transcript.map((entry) => (
              <div
                key={entry.id}
                className={`transcript-entry ${entry.type}`}
                role="article"
              >
                <div className="entry-header">
                  <span className="entry-type">
                    {entry.type === 'user' ? <User size={16} /> : <Headphones size={16} />}
                    {entry.type === 'user' ? 'You' : 'Assistant'}
                  </span>
                  <span className="entry-time">
                    {entry.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div className="entry-text">{entry.text}</div>
                {entry.confidence && (
                  <div className="entry-confidence">
                    Confidence: {(entry.confidence * 100).toFixed(1)}%
                  </div>
                )}
                {entry.intent && (
                  <div className="entry-intent">
                    Intent: {entry.intent.name} ({(entry.intent.confidence * 100).toFixed(1)}%)
                  </div>
                )}
                {entry.entities && entry.entities.length > 0 && (
                  <div className="entry-entities">
                    Entities: {entry.entities.map(e => `${e.type}: ${e.value}`).join(', ')}
                  </div>
                )}
              </div>
            ))}
            
            {interimTranscript && (
              <div className="transcript-entry interim">
                <div className="entry-text">{interimTranscript}...</div>
              </div>
            )}
            
            <div ref={transcriptEndRef} />
          </div>
        </div>
      )}

      {/* Text input */}
      <div className="text-input-container">
        <input
          type="text"
          placeholder="Type a command or question..."
          onKeyPress={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value) {
              sendTextCommand(e.currentTarget.value);
              e.currentTarget.value = '';
            }
          }}
          aria-label="Text command input"
        />
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-panel" role="dialog" aria-label="Voice settings">
          <div className="panel-header">
            <h3>Voice Settings</h3>
            <button onClick={() => setShowSettings(false)} aria-label="Close settings">
              <X size={20} />
            </button>
          </div>
          
          <div className="settings-content">
            <div className="setting-group">
              <label htmlFor="language">Language</label>
              <select
                id="language"
                value={settings.language}
                onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value }))}
              >
                <option value="en-US">English (US)</option>
                <option value="es-ES">Spanish</option>
                <option value="fr-FR">French</option>
                <option value="de-DE">German</option>
                <option value="zh-CN">Chinese</option>
                <option value="ja-JP">Japanese</option>
              </select>
            </div>

            <div className="setting-group">
              <label htmlFor="voice-gender">Voice Gender</label>
              <select
                id="voice-gender"
                value={settings.voiceGender}
                onChange={(e) => setSettings(prev => ({ ...prev, voiceGender: e.target.value }))}
              >
                <option value="NEUTRAL">Neutral</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
              </select>
            </div>

            <div className="setting-group">
              <label htmlFor="voice-profile">Voice Profile</label>
              <select
                id="voice-profile"
                value={settings.voiceProfile}
                onChange={(e) => setSettings(prev => ({ ...prev, voiceProfile: e.target.value }))}
              >
                <option value="professional">Professional</option>
                <option value="friendly">Friendly</option>
                <option value="assistive">Assistive</option>
              </select>
            </div>

            <div className="setting-group">
              <label htmlFor="speech-rate">Speech Rate</label>
              <input
                id="speech-rate"
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={settings.speechRate}
                onChange={(e) => setSettings(prev => ({ ...prev, speechRate: parseFloat(e.target.value) }))}
              />
              <span>{settings.speechRate}x</span>
            </div>

            <div className="setting-group">
              <label htmlFor="volume">Volume</label>
              <input
                id="volume"
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.volume}
                onChange={(e) => setSettings(prev => ({ ...prev, volume: parseFloat(e.target.value) }))}
              />
              <span>{Math.round(settings.volume * 100)}%</span>
            </div>

            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.enableWakeWord}
                  onChange={toggleWakeWord}
                />
                Enable Wake Word
              </label>
            </div>

            {settings.enableWakeWord && (
              <div className="setting-group">
                <label htmlFor="wake-word">Wake Word</label>
                <input
                  id="wake-word"
                  type="text"
                  value={settings.wakeWord}
                  onChange={(e) => setSettings(prev => ({ ...prev, wakeWord: e.target.value }))}
                />
              </div>
            )}

            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.autoPlay}
                  onChange={(e) => setSettings(prev => ({ ...prev, autoPlay: e.target.checked }))}
                />
                Auto-play Responses
              </label>
            </div>

            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.showTranscript}
                  onChange={(e) => setSettings(prev => ({ ...prev, showTranscript: e.target.checked }))}
                />
                Show Transcript
              </label>
            </div>

            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.showVisualizer}
                  onChange={(e) => setSettings(prev => ({ ...prev, showVisualizer: e.target.checked }))}
                />
                Show Audio Visualizer
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Help Panel */}
      {showHelp && (
        <div className="help-panel" role="dialog" aria-label="Voice commands help">
          <div className="panel-header">
            <h3>Voice Commands Help</h3>
            <button onClick={() => setShowHelp(false)} aria-label="Close help">
              <X size={20} />
            </button>
          </div>
          
          <div className="help-content">
            <section>
              <h4>Quick Commands</h4>
              <ul>
                <li>"Show my portfolio" - View investment portfolio</li>
                <li>"Check balance" - View account balances</li>
                <li>"Show goals" - View financial goals</li>
                <li>"Recent transactions" - View recent activity</li>
                <li>"Market update" - Get market summary</li>
                <li>"Calculate retirement" - Open retirement calculator</li>
              </ul>
            </section>

            <section>
              <h4>Keyboard Shortcuts</h4>
              <ul>
                <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>M</kbd> - Start/stop listening</li>
                <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>H</kbd> - Show help</li>
                <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> - Open settings</li>
                <li><kbd>Escape</kbd> - Cancel current action</li>
                <li><kbd>Enter</kbd> - Confirm action</li>
              </ul>
            </section>

            <section>
              <h4>Tips</h4>
              <ul>
                <li>Speak clearly and at a normal pace</li>
                <li>Wait for the listening indicator before speaking</li>
                <li>Use natural language - no need for specific phrases</li>
                <li>Enable wake word for hands-free activation</li>
                <li>Adjust speech rate and volume in settings</li>
              </ul>
            </section>
          </div>
        </div>
      )}

      {/* Accessibility Panel */}
      {showAccessibility && (
        <div className="accessibility-panel" role="dialog" aria-label="Accessibility options">
          <div className="panel-header">
            <h3>Accessibility Options</h3>
            <button onClick={() => setShowAccessibility(false)} aria-label="Close accessibility">
              <X size={20} />
            </button>
          </div>
          
          <div className="accessibility-content">
            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.enableScreenReader}
                  onChange={(e) => setSettings(prev => ({ ...prev, enableScreenReader: e.target.checked }))}
                />
                Enable Screen Reader Support
              </label>
            </div>

            <div className="setting-group">
              <label htmlFor="verbosity">Verbosity Level</label>
              <select
                id="verbosity"
                value={settings.verbosityLevel}
                onChange={(e) => setSettings(prev => ({ ...prev, verbosityLevel: e.target.value }))}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.keyboardNavigation}
                  onChange={(e) => setSettings(prev => ({ ...prev, keyboardNavigation: e.target.checked }))}
                />
                Enable Keyboard Navigation
              </label>
            </div>

            <div className="setting-group">
              <button onClick={() => document.body.classList.toggle('high-contrast')}>
                Toggle High Contrast Mode
              </button>
            </div>

            <div className="setting-group">
              <button onClick={() => document.body.style.fontSize = '120%'}>
                Increase Text Size
              </button>
              <button onClick={() => document.body.style.fontSize = '100%'}>
                Reset Text Size
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="error-message" role="alert">
          <AlertCircle size={20} />
          {error}
          <button onClick={() => setError(null)} aria-label="Dismiss error">
            <X size={16} />
          </button>
        </div>
      )}

      <style jsx>{`
        .voice-interface {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 1000;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .voice-interface.dark {
          color: #ffffff;
        }

        .voice-controls {
          display: flex;
          align-items: center;
          gap: 20px;
          background: white;
          border-radius: 60px;
          padding: 10px 20px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .dark .voice-controls {
          background: #1f2937;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .mic-button {
          position: relative;
          width: 60px;
          height: 60px;
          border-radius: 50%;
          border: none;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .mic-button:hover {
          transform: scale(1.05);
        }

        .mic-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .mic-button.listening {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          animation: pulse 1.5s infinite;
        }

        .mic-button.processing {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(240, 147, 251, 0.7);
          }
          70% {
            box-shadow: 0 0 0 20px rgba(240, 147, 251, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(240, 147, 251, 0);
          }
        }

        .audio-level-ring {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 100%;
          height: 100%;
          border: 3px solid currentColor;
          border-radius: 50%;
          pointer-events: none;
          transition: transform 0.1s ease, opacity 0.1s ease;
        }

        .status-indicators {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .status-badge {
          display: flex;
          align-items: center;
          gap: 5px;
          padding: 5px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          background: #f3f4f6;
        }

        .dark .status-badge {
          background: #374151;
        }

        .status-badge.connected {
          background: #d1fae5;
          color: #065f46;
        }

        .status-badge.listening {
          background: #fce7f3;
          color: #9f1239;
        }

        .status-badge.processing {
          background: #dbeafe;
          color: #1e3a8a;
        }

        .status-badge.speaking {
          background: #fef3c7;
          color: #92400e;
        }

        .status-badge.wake-word {
          background: #e9d5ff;
          color: #6b21a8;
        }

        .action-buttons {
          display: flex;
          gap: 10px;
        }

        .action-buttons button {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          border: none;
          background: #f3f4f6;
          color: #6b7280;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .dark .action-buttons button {
          background: #374151;
          color: #9ca3af;
        }

        .action-buttons button:hover {
          background: #e5e7eb;
          color: #111827;
        }

        .dark .action-buttons button:hover {
          background: #4b5563;
          color: #f3f4f6;
        }

        .transcript-container {
          position: fixed;
          bottom: 100px;
          right: 20px;
          width: 400px;
          max-height: 400px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
          padding: 15px;
        }

        .dark .transcript-container {
          background: #1f2937;
        }

        .transcript-scroll {
          max-height: 350px;
          overflow-y: auto;
          margin-top: 10px;
        }

        .transcript-entry {
          margin-bottom: 15px;
          padding: 10px;
          border-radius: 8px;
          background: #f9fafb;
        }

        .dark .transcript-entry {
          background: #374151;
        }

        .transcript-entry.user {
          background: #eff6ff;
          border-left: 3px solid #3b82f6;
        }

        .dark .transcript-entry.user {
          background: #1e3a8a;
        }

        .transcript-entry.assistant {
          background: #f0fdf4;
          border-left: 3px solid #10b981;
        }

        .dark .transcript-entry.assistant {
          background: #064e3b;
        }

        .transcript-entry.interim {
          opacity: 0.6;
          font-style: italic;
        }

        .entry-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 5px;
          font-size: 12px;
          color: #6b7280;
        }

        .entry-type {
          display: flex;
          align-items: center;
          gap: 5px;
          font-weight: 500;
        }

        .entry-text {
          font-size: 14px;
          line-height: 1.5;
        }

        .entry-confidence,
        .entry-intent,
        .entry-entities {
          margin-top: 5px;
          font-size: 11px;
          color: #9ca3af;
        }

        .text-input-container {
          position: fixed;
          bottom: 100px;
          left: 50%;
          transform: translateX(-50%);
          width: 90%;
          max-width: 500px;
        }

        .text-input-container input {
          width: 100%;
          padding: 12px 20px;
          border: 2px solid #e5e7eb;
          border-radius: 30px;
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s ease;
        }

        .dark .text-input-container input {
          background: #374151;
          border-color: #4b5563;
          color: white;
        }

        .text-input-container input:focus {
          border-color: #667eea;
        }

        .settings-panel,
        .help-panel,
        .accessibility-panel {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 90%;
          max-width: 500px;
          max-height: 80vh;
          background: white;
          border-radius: 12px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
          overflow: hidden;
        }

        .dark .settings-panel,
        .dark .help-panel,
        .dark .accessibility-panel {
          background: #1f2937;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .dark .panel-header {
          border-bottom-color: #374151;
        }

        .panel-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .panel-header button {
          width: 30px;
          height: 30px;
          border-radius: 50%;
          border: none;
          background: #f3f4f6;
          color: #6b7280;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .dark .panel-header button {
          background: #374151;
          color: #9ca3af;
        }

        .settings-content,
        .help-content,
        .accessibility-content {
          padding: 20px;
          max-height: calc(80vh - 70px);
          overflow-y: auto;
        }

        .setting-group {
          margin-bottom: 20px;
        }

        .setting-group label {
          display: block;
          margin-bottom: 5px;
          font-size: 14px;
          font-weight: 500;
        }

        .setting-group select,
        .setting-group input[type="text"],
        .setting-group input[type="range"] {
          width: 100%;
          padding: 8px;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          font-size: 14px;
        }

        .dark .setting-group select,
        .dark .setting-group input[type="text"],
        .dark .setting-group input[type="range"] {
          background: #374151;
          border-color: #4b5563;
          color: white;
        }

        .help-content section {
          margin-bottom: 25px;
        }

        .help-content h4 {
          margin: 0 0 10px 0;
          font-size: 16px;
          font-weight: 600;
        }

        .help-content ul {
          margin: 0;
          padding-left: 20px;
        }

        .help-content li {
          margin-bottom: 5px;
          font-size: 14px;
        }

        .help-content kbd {
          display: inline-block;
          padding: 2px 6px;
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-family: monospace;
          font-size: 12px;
        }

        .dark .help-content kbd {
          background: #374151;
          border-color: #4b5563;
        }

        .error-message {
          position: fixed;
          top: 20px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 20px;
          background: #fee2e2;
          color: #991b1b;
          border-radius: 8px;
          box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
          animation: slideDown 0.3s ease;
        }

        .dark .error-message {
          background: #991b1b;
          color: #fee2e2;
        }

        @keyframes slideDown {
          from {
            transform: translate(-50%, -100%);
            opacity: 0;
          }
          to {
            transform: translate(-50%, 0);
            opacity: 1;
          }
        }

        .error-message button {
          background: none;
          border: none;
          color: inherit;
          cursor: pointer;
          padding: 0;
          margin-left: 10px;
        }

        @media (max-width: 768px) {
          .voice-interface {
            bottom: 10px;
            right: 10px;
            left: 10px;
          }

          .voice-controls {
            flex-direction: column;
            border-radius: 12px;
            width: 100%;
          }

          .transcript-container {
            width: calc(100% - 20px);
            right: 10px;
            left: 10px;
          }

          .settings-panel,
          .help-panel,
          .accessibility-panel {
            width: 95%;
          }
        }
      `}</style>
    </div>
  );
};

export default VoiceInterface;