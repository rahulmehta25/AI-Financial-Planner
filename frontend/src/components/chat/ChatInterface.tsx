import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ChatMessage, ChatSession, chatService } from '@/services/chat';
import { userService } from '@/services/user';
import { portfolioService } from '@/services/portfolio';
import MessageBubble from './MessageBubble';
import VoiceInput from './VoiceInput';
import ErrorBoundary from './ErrorBoundary';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Send, 
  Bot, 
  Loader2, 
  AlertCircle, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Download,
  Settings,
  Maximize2,
  Minimize2,
  Plus,
  RefreshCw
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ChatInterfaceProps {
  session: ChatSession;
  userContext?: {
    portfolioData?: any;
    financialProfile?: any;
    goals?: any[];
  };
  onSessionUpdate?: (session: ChatSession) => void;
  onNewSession?: () => void;
  onExportConversation?: () => void;
  className?: string;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

interface TypingState {
  isTyping: boolean;
  message: string;
  progress: number;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  session,
  userContext,
  onSessionUpdate,
  onNewSession,
  onExportConversation,
  className = '',
  isFullscreen = false,
  onToggleFullscreen
}) => {
  const { toast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  const [messages, setMessages] = useState<ChatMessage[]>(session.messages || []);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [typingState, setTypingState] = useState<TypingState>({ isTyping: false, message: '', progress: 0 });
  const [error, setError] = useState<string | null>(null);
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentSpeechId, setCurrentSpeechId] = useState<string | null>(null);
  const [messageHistory, setMessageHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typingState.isTyping]);

  // Update messages when session changes
  useEffect(() => {
    setMessages(session.messages || []);
    setError(null);
  }, [session]);

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;
      
      const ws = chatService.connectToChat(session.id, (message: ChatMessage) => {
        setMessages(prev => [...prev, message]);
        setTypingState({ isTyping: false, message: '', progress: 0 });
      });
      
      if (ws) {
        wsRef.current = ws;
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [session.id]);

  // Text to speech functionality
  const speakText = useCallback((text: string, messageId?: string) => {
    if (isSpeaking && messageId === currentSpeechId) {
      // Stop current speech
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setCurrentSpeechId(null);
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setCurrentSpeechId(messageId || null);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setCurrentSpeechId(null);
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setCurrentSpeechId(null);
    };

    window.speechSynthesis.speak(utterance);
  }, [isSpeaking, currentSpeechId]);

  // Simulate typing indicator with streaming response
  const simulateTypingResponse = useCallback((response: string) => {
    setTypingState({ isTyping: true, message: '', progress: 0 });
    
    const words = response.split(' ');
    let currentIndex = 0;
    
    const typeNextWord = () => {
      if (currentIndex < words.length) {
        setTypingState(prev => ({
          isTyping: true,
          message: prev.message + (currentIndex > 0 ? ' ' : '') + words[currentIndex],
          progress: (currentIndex / words.length) * 100
        }));
        currentIndex++;
        setTimeout(typeNextWord, 50 + Math.random() * 100); // Variable typing speed
      } else {
        setTypingState({ isTyping: false, message: '', progress: 0 });
      }
    };
    
    typeNextWord();
  }, []);

  // Handle sending message
  const handleSendMessage = useCallback(async (messageText?: string) => {
    const textToSend = messageText || inputMessage.trim();
    if (!textToSend || isSending) return;

    // Add to history
    setMessageHistory(prev => [textToSend, ...prev.slice(0, 19)]); // Keep last 20
    setHistoryIndex(-1);
    
    setInputMessage('');
    setIsSending(true);
    setError(null);

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content: textToSend,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Send message to AI with user context
      const response = await chatService.sendMessage({
        message: textToSend,
        sessionId: session.id,
        context: userContext
      });

      // Simulate typing for better UX
      simulateTypingResponse(response.message.content);
      
      // Add AI response after typing simulation
      setTimeout(() => {
        setMessages(prev => [...prev, response.message]);
        
        // Update session
        const updatedSession = {
          ...session,
          messages: [...messages, userMessage, response.message],
          updatedAt: new Date().toISOString()
        };
        onSessionUpdate?.(updatedSession);
      }, 50 * response.message.content.split(' ').length + 1000);

    } catch (err: any) {
      console.error('Failed to send message:', err);
      setError(err.message || 'Failed to send message');
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        content: "I apologize, but I'm having trouble processing your message right now. Please try again in a moment.",
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      toast({
        title: "Message failed",
        description: err.message || "Failed to send message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSending(false);
    }
  }, [inputMessage, isSending, session, userContext, onSessionUpdate, messages, simulateTypingResponse, toast]);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    } else if (e.key === 'ArrowUp' && inputMessage === '' && messageHistory.length > 0) {
      e.preventDefault();
      const newIndex = Math.min(historyIndex + 1, messageHistory.length - 1);
      setHistoryIndex(newIndex);
      setInputMessage(messageHistory[newIndex]);
    } else if (e.key === 'ArrowDown' && historyIndex >= 0) {
      e.preventDefault();
      const newIndex = Math.max(historyIndex - 1, -1);
      setHistoryIndex(newIndex);
      setInputMessage(newIndex >= 0 ? messageHistory[newIndex] : '');
    }
  }, [inputMessage, messageHistory, historyIndex, handleSendMessage]);

  // Handle voice input
  const handleVoiceTranscript = useCallback((transcript: string) => {
    setInputMessage(prev => prev + (prev ? ' ' : '') + transcript);
  }, []);

  // Handle message feedback
  const handleMessageFeedback = useCallback((messageId: string, feedback: 'positive' | 'negative') => {
    // This could send feedback to the backend for model improvement
    console.log(`Feedback for message ${messageId}: ${feedback}`);
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [inputMessage]);

  return (
    <ErrorBoundary>
      <div className={`chat-interface flex flex-col h-full ${className}`} role="region" aria-label="AI Chat Interface">
        {/* Header */}
        <CardHeader className="border-b border-white/10 flex-shrink-0 py-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 min-w-0">
            <Bot className="w-5 h-5 text-primary flex-shrink-0" aria-hidden="true" />
            <span className="truncate">{session.title}</span>
            <Badge variant="outline" className="glass border-white/20 flex-shrink-0 tabular-nums">
              {messages.length} messages
            </Badge>
          </CardTitle>

          <div className="flex items-center gap-1 flex-shrink-0">
            {/* Voice Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsVoiceEnabled(!isVoiceEnabled)}
              className={`transition-colors ${isVoiceEnabled ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
              aria-label={isVoiceEnabled ? 'Disable voice input' : 'Enable voice input'}
              aria-pressed={isVoiceEnabled}
            >
              {isVoiceEnabled ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
            </Button>

            {/* New Session */}
            <Button variant="ghost" size="sm" onClick={onNewSession} aria-label="Start new conversation" className="transition-colors hover:text-primary">
              <Plus className="w-4 h-4" />
            </Button>

            {/* Export */}
            <Button variant="ghost" size="sm" onClick={onExportConversation} aria-label="Export conversation as PDF" className="transition-colors hover:text-primary">
              <Download className="w-4 h-4" />
            </Button>

            {/* Fullscreen Toggle */}
            {onToggleFullscreen && (
              <Button variant="ghost" size="sm" onClick={onToggleFullscreen} aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'} className="transition-colors hover:text-primary">
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive" className="m-4 flex-shrink-0 animate-fade-in" role="alert">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between gap-4">
            <span>{error}</span>
            <Button
              variant="outline"
              size="sm"
              className="flex-shrink-0"
              onClick={() => setError(null)}
              aria-label="Dismiss error"
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" aria-live="polite" aria-atomic="false">
        <div className="space-y-4">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onSuggestionClick={(suggestion) => handleSendMessage(suggestion)}
              onFeedback={handleMessageFeedback}
              onSpeak={(text) => speakText(text, message.id)}
              isSpeaking={isSpeaking && currentSpeechId === message.id}
            />
          ))}
          
          {/* Typing Indicator */}
          {typingState.isTyping && (
            <div className="flex gap-3 animate-fade-in" role="status" aria-label="AI is generating a response">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center flex-shrink-0" aria-hidden="true">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="max-w-[75%]">
                <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" aria-hidden="true" />
                    <span className="text-sm text-muted-foreground">AI is thinking...</span>
                  </div>
                  {typingState.progress > 0 && (
                    <Progress value={typingState.progress} className="h-1.5 mb-2" aria-label={`Response progress: ${Math.round(typingState.progress)}%`} />
                  )}
                  {typingState.message && (
                    <p className="text-sm leading-relaxed">{typingState.message}</p>
                  )}
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-white/10 flex-shrink-0">
        {isVoiceEnabled && (
          <VoiceInput
            onTranscript={handleVoiceTranscript}
            onSpeakText={speakText}
            className="mb-3"
            disabled={isSending}
          />
        )}
        
        <div className="flex gap-2" role="group" aria-label="Message input">
          <div className="flex-1">
            <Textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about your finances..."
              className="glass border-white/20 bg-white/5 resize-none min-h-[40px] max-h-[120px]"
              disabled={isSending}
              aria-label="Type your financial question here"
              aria-describedby={inputMessage ? "input-help" : undefined}
            />
            {inputMessage && (
              <div id="input-help" className="text-xs text-muted-foreground mt-1" role="status">
                Press Enter to send, Shift+Enter for new line
              </div>
            )}
          </div>
          
          <Button 
            onClick={() => handleSendMessage()}
            disabled={isSending || !inputMessage.trim()}
            className="bg-gradient-to-r from-primary to-success hover:shadow-glow self-end"
            aria-label={isSending ? "Sending message..." : "Send message"}
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="w-4 h-4" aria-hidden="true" />
            )}
          </Button>
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
};

export default ChatInterface;