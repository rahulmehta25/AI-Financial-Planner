import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Play, 
  Square, 
  Settings,
  AlertCircle
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onSpeakText: (text: string) => void;
  className?: string;
  disabled?: boolean;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  serviceURI: string;
  grammars: SpeechGrammarList;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onnomatch: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onsoundstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onsoundend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onaudiostart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onaudioend: ((this: SpeechRecognition, ev: Event) => any) | null;
}

declare global {
  interface Window {
    SpeechRecognition?: {
      new (): SpeechRecognition;
    };
    webkitSpeechRecognition?: {
      new (): SpeechRecognition;
    };
    speechSynthesis: SpeechSynthesis;
  }
}

const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  onSpeakText,
  className = '',
  disabled = false
}) => {
  const { toast } = useToast();
  
  // Speech Recognition State
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Speech Synthesis State
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [speakingRate, setSpeakingRate] = useState(1);
  
  // Refs
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>();
  
  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const speechSynthesis = window.speechSynthesis;
    
    setIsSupported(!!(SpeechRecognition && speechSynthesis));
    
    if (!SpeechRecognition) {
      setError('Speech recognition not supported in this browser');
    }
  }, []);

  // Load available voices
  useEffect(() => {
    if (window.speechSynthesis) {
      const loadVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices();
        setVoices(availableVoices);
        
        // Select a good default voice (English, preferably neural/high quality)
        const preferredVoice = availableVoices.find(voice => 
          voice.lang.startsWith('en') && (voice.name.includes('Neural') || voice.name.includes('Premium'))
        ) || availableVoices.find(voice => voice.lang.startsWith('en')) || availableVoices[0];
        
        setSelectedVoice(preferredVoice);
      };

      // Load voices immediately and also listen for the event
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
      
      return () => {
        window.speechSynthesis.onvoiceschanged = null;
      };
    }
  }, []);

  // Initialize speech recognition
  const initializeSpeechRecognition = useCallback(() => {
    if (!isSupported) return null;
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
    
    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
      toast({
        title: "Voice input started",
        description: "Speak now to input your message.",
      });
    };
    
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = '';
      let final = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        
        if (event.results[i].isFinal) {
          final += transcript;
          setConfidence(event.results[i][0].confidence);
        } else {
          interim += transcript;
        }
      }
      
      if (final) {
        setTranscript(prev => prev + final);
        setInterimTranscript('');
        onTranscript(final);
      } else {
        setInterimTranscript(interim);
      }
    };
    
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      setError(`Speech recognition error: ${event.error}`);
      setIsListening(false);
      
      toast({
        title: "Voice input error",
        description: event.message || "Could not recognize speech",
        variant: "destructive",
      });
    };
    
    recognition.onend = () => {
      setIsListening(false);
      setInterimTranscript('');
    };
    
    return recognition;
  }, [isSupported, onTranscript, toast]);

  // Setup audio visualization
  const setupAudioVisualization = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.smoothingTimeConstant = 0.8;
      analyser.fftSize = 1024;
      
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Start visualization loop
      const updateAudioLevel = () => {
        if (analyserRef.current) {
          const bufferLength = analyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          analyserRef.current.getByteFrequencyData(dataArray);
          
          const average = dataArray.reduce((a, b) => a + b) / bufferLength;
          setAudioLevel(Math.min(100, (average / 255) * 100));
          
          if (isListening) {
            animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
          }
        }
      };
      
      updateAudioLevel();
      
    } catch (error) {
      console.error('Could not access microphone:', error);
      setError('Could not access microphone. Please check permissions.');
    }
  }, [isListening]);

  // Start listening
  const startListening = useCallback(async () => {
    if (disabled || !isSupported) return;
    
    try {
      const recognition = initializeSpeechRecognition();
      if (!recognition) return;
      
      recognitionRef.current = recognition;
      recognition.start();
      
      await setupAudioVisualization();
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      setError('Could not start voice input');
    }
  }, [disabled, isSupported, initializeSpeechRecognition, setupAudioVisualization]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    setIsListening(false);
    setAudioLevel(0);
  }, []);

  // Speak text
  const speakText = useCallback((text: string) => {
    if (!window.speechSynthesis || isSpeaking) return;
    
    // Stop any current speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    
    utterance.rate = speakingRate;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    utterance.onstart = () => {
      setIsSpeaking(true);
      toast({
        title: "Speaking",
        description: "AI response is being read aloud.",
      });
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
    };
    
    utterance.onerror = () => {
      setIsSpeaking(false);
      toast({
        title: "Speech error",
        description: "Could not read text aloud.",
        variant: "destructive",
      });
    };
    
    window.speechSynthesis.speak(utterance);
  }, [isSpeaking, selectedVoice, speakingRate, toast]);

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  // Handle voice input toggle
  const toggleVoiceInput = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopListening();
      stopSpeaking();
    };
  }, [stopListening, stopSpeaking]);

  if (!isSupported) {
    return (
      <Alert className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Voice features are not supported in this browser. Please use a modern browser like Chrome, Firefox, or Safari.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={`voice-input ${className}`}>
      {error && (
        <Alert className="mb-4" variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <div className="flex items-center gap-3">
        {/* Voice Input Button */}
        <Button
          variant={isListening ? "destructive" : "outline"}
          size="sm"
          className={`voice-input-btn ${isListening ? 'animate-pulse' : ''}`}
          onClick={toggleVoiceInput}
          disabled={disabled}
          title={isListening ? "Stop listening" : "Start voice input"}
        >
          {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </Button>

        {/* Text-to-Speech Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={isSpeaking ? stopSpeaking : () => onSpeakText && onSpeakText("Text to speech test")}
          disabled={disabled}
          title={isSpeaking ? "Stop speaking" : "Test text to speech"}
        >
          {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
        </Button>

        {/* Audio Level Indicator */}
        {isListening && (
          <div className="flex items-center gap-2 min-w-[100px]">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <Progress value={audioLevel} className="h-2 flex-1" />
          </div>
        )}

        {/* Status Badges */}
        {isListening && (
          <Badge variant="outline" className="text-xs glass border-green-500/30 text-green-400">
            Listening
          </Badge>
        )}
        
        {isSpeaking && (
          <Badge variant="outline" className="text-xs glass border-blue-500/30 text-blue-400">
            Speaking
          </Badge>
        )}
        
        {confidence > 0 && (
          <Badge variant="outline" className="text-xs glass border-white/20">
            {Math.round(confidence * 100)}% confidence
          </Badge>
        )}
      </div>

      {/* Live Transcript */}
      {(transcript || interimTranscript) && (
        <div className="mt-3 p-3 bg-white/5 border border-white/10 rounded-lg">
          <div className="text-sm">
            <span className="text-white">{transcript}</span>
            <span className="text-muted-foreground italic">{interimTranscript}</span>
          </div>
        </div>
      )}

      {/* Voice Settings */}
      <details className="mt-3">
        <summary className="cursor-pointer text-sm text-muted-foreground flex items-center gap-2">
          <Settings className="w-4 h-4" />
          Voice Settings
        </summary>
        
        <div className="mt-2 p-3 bg-white/5 border border-white/10 rounded-lg space-y-3">
          {/* Voice Selection */}
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Voice</label>
            <select 
              className="w-full p-2 bg-white/10 border border-white/20 rounded text-sm"
              value={selectedVoice?.name || ''}
              onChange={(e) => {
                const voice = voices.find(v => v.name === e.target.value);
                setSelectedVoice(voice || null);
              }}
            >
              {voices.map((voice) => (
                <option key={voice.name} value={voice.name} className="bg-gray-800">
                  {voice.name} ({voice.lang})
                </option>
              ))}
            </select>
          </div>

          {/* Speaking Rate */}
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">
              Speaking Rate: {speakingRate}x
            </label>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={speakingRate}
              onChange={(e) => setSpeakingRate(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>
      </details>
    </div>
  );
};

export default VoiceInput;