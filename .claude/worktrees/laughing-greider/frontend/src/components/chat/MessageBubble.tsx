import React, { useState, useRef } from 'react';
import { ChatMessage } from '@/services/chat';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Bot, 
  User, 
  Copy, 
  Check, 
  ThumbsUp, 
  ThumbsDown, 
  TrendingUp,
  DollarSign,
  PieChart,
  Calendar,
  AlertTriangle,
  Info,
  Download,
  Volume2,
  VolumeX
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: ChatMessage;
  isTyping?: boolean;
  showTimestamp?: boolean;
  onSuggestionClick?: (suggestion: string) => void;
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void;
  onSpeak?: (text: string) => void;
  isSpeaking?: boolean;
}

interface MessageData {
  text: string;
  tables?: Array<{
    title: string;
    headers: string[];
    rows: string[][];
  }>;
  charts?: Array<{
    title: string;
    type: 'bar' | 'line' | 'pie';
    data: any;
  }>;
  recommendations?: Array<{
    title: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    urgency: 'urgent' | 'normal' | 'low';
  }>;
  calculations?: Array<{
    label: string;
    value: string | number;
    description?: string;
  }>;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isTyping = false,
  showTimestamp = true,
  onSuggestionClick,
  onFeedback,
  onSpeak,
  isSpeaking = false
}) => {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);
  const messageRef = useRef<HTMLDivElement>(null);
  
  const isAssistant = message.role === 'assistant';
  
  // Parse message content if it contains structured data
  const parseMessageContent = (content: string): MessageData => {
    try {
      // Try to parse as JSON first (for structured responses)
      if (content.startsWith('{') || content.startsWith('[')) {
        const parsed = JSON.parse(content);
        return parsed;
      }
    } catch {
      // If not JSON, treat as plain text but look for markdown-like structures
    }
    
    return { text: content };
  };

  const messageData = parseMessageContent(message.content);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast({
        title: "Copied to clipboard",
        description: "Message content has been copied to your clipboard.",
      });
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Could not copy message to clipboard.",
        variant: "destructive",
      });
    }
  };

  const handleFeedback = (type: 'positive' | 'negative') => {
    setFeedback(type);
    onFeedback?.(message.id, type);
    toast({
      title: "Feedback recorded",
      description: `Thank you for your ${type} feedback!`,
    });
  };

  const handleSpeak = () => {
    if (onSpeak) {
      const textToSpeak = typeof messageData === 'object' ? messageData.text : message.content;
      onSpeak(textToSpeak);
    }
  };

  const getMessageIcon = () => {
    if (isAssistant) {
      return <Bot className="w-4 h-4 text-white" />;
    }
    return <User className="w-4 h-4 text-white" />;
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-500 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-500 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-500 bg-green-50 border-green-200';
      default: return 'text-gray-500 bg-gray-50 border-gray-200';
    }
  };

  const getUrgencyIcon = (urgency: string) => {
    switch (urgency) {
      case 'urgent': return <AlertTriangle className="w-4 h-4" />;
      case 'normal': return <Info className="w-4 h-4" />;
      default: return <Calendar className="w-4 h-4" />;
    }
  };

  return (
    <div
      id={`message-${message.id}`}
      className={`flex gap-3 animate-fade-in ${isAssistant ? '' : 'flex-row-reverse'}`}
      ref={messageRef}
      role="log"
      aria-label={`${isAssistant ? 'AI Assistant' : 'User'} message from ${new Date(message.timestamp).toLocaleTimeString()}`}
    >
      {/* Avatar */}
      <div 
        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
          isAssistant 
            ? 'bg-gradient-to-br from-primary to-primary-glow' 
            : 'bg-gradient-to-br from-success to-success-dark'
        }`}
        role="img"
        aria-label={isAssistant ? 'AI Assistant avatar' : 'User avatar'}
      >
        {getMessageIcon()}
      </div>

      {/* Message Content */}
      <div className={`max-w-[75%] ${isAssistant ? '' : 'text-right'}`}>
        {/* Message Bubble */}
        <div className={`p-4 rounded-2xl ${
          isAssistant
            ? 'bg-white/5 border border-white/10'
            : 'bg-gradient-to-br from-primary/20 to-success/20 border border-primary/20'
        }`}>
          {/* Main Text Content */}
          {messageData.text && (
            <div className="prose prose-sm prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  // Custom components for better styling
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                  strong: ({ children }) => <strong className="text-primary">{children}</strong>,
                  code: ({ children }) => <code className="bg-white/10 px-2 py-1 rounded text-xs">{children}</code>,
                }}
              >
                {messageData.text}
              </ReactMarkdown>
            </div>
          )}

          {/* Financial Tables */}
          {messageData.tables?.map((table, index) => (
            <Card key={index} className="mt-4 bg-white/5 border-white/10">
              <div className="p-4">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-primary" />
                  {table.title}
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10">
                        {table.headers.map((header, i) => (
                          <th key={i} className="text-left p-2 font-medium">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {table.rows.map((row, i) => (
                        <tr key={i} className="border-b border-white/5">
                          {row.map((cell, j) => (
                            <td key={j} className="p-2">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </Card>
          ))}

          {/* Financial Calculations */}
          {messageData.calculations && (
            <Card className="mt-4 bg-white/5 border-white/10">
              <div className="p-4">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-success" />
                  Financial Calculations
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {messageData.calculations.map((calc, index) => (
                    <div key={index} className="bg-white/5 rounded-lg p-3">
                      <div className="text-sm text-muted-foreground">{calc.label}</div>
                      <div className="text-lg font-semibold text-primary">{calc.value}</div>
                      {calc.description && (
                        <div className="text-xs text-muted-foreground mt-1">{calc.description}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {/* Recommendations */}
          {messageData.recommendations && (
            <div className="mt-4 space-y-3">
              <h4 className="font-semibold flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                Recommendations
              </h4>
              {messageData.recommendations.map((rec, index) => (
                <Card key={index} className={`bg-white/5 border-white/10 ${getImpactColor(rec.impact)}`}>
                  <div className="p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2">
                        {getUrgencyIcon(rec.urgency)}
                        <div>
                          <h5 className="font-medium text-sm">{rec.title}</h5>
                          <p className="text-xs text-muted-foreground mt-1">{rec.description}</p>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Badge variant="outline" className={`text-xs ${getImpactColor(rec.impact)}`}>
                          {rec.impact}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {rec.urgency}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Suggestions */}
          {message.metadata?.suggestions && (
            <div className="mt-4 space-y-2">
              <div className="text-sm text-muted-foreground">Suggested follow-ups:</div>
              <div className="flex flex-wrap gap-2">
                {message.metadata.suggestions.map((suggestion, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="h-auto p-2 text-xs glass border-white/20 hover:bg-white/10"
                    onClick={() => onSuggestionClick?.(suggestion)}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Confidence Score */}
          {message.metadata?.confidence && (
            <div className="mt-3 flex items-center gap-2">
              <Badge variant="outline" className="text-xs glass border-white/20">
                Confidence: {Math.round(message.metadata.confidence * 100)}%
              </Badge>
            </div>
          )}
        </div>

        {/* Message Actions */}
        {isAssistant && (
          <div className="flex items-center gap-2 mt-2 ml-2" role="group" aria-label="Message actions">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs hover:bg-white/10"
              onClick={handleCopy}
              aria-label={copied ? 'Message copied to clipboard' : 'Copy message to clipboard'}
              title={copied ? 'Copied!' : 'Copy message'}
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs hover:bg-white/10"
              onClick={handleSpeak}
              aria-label={isSpeaking ? 'Stop speaking message' : 'Speak message aloud'}
              title={isSpeaking ? 'Stop speaking' : 'Read aloud'}
            >
              {isSpeaking ? <VolumeX className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className={`h-6 px-2 text-xs hover:bg-white/10 ${
                feedback === 'positive' ? 'text-success' : ''
              }`}
              onClick={() => handleFeedback('positive')}
              aria-label="This message was helpful"
              title="Thumbs up - helpful response"
              aria-pressed={feedback === 'positive'}
            >
              <ThumbsUp className="w-3 h-3" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              className={`h-6 px-2 text-xs hover:bg-white/10 ${
                feedback === 'negative' ? 'text-destructive' : ''
              }`}
              onClick={() => handleFeedback('negative')}
              aria-label="This message was not helpful"
              title="Thumbs down - not helpful"
              aria-pressed={feedback === 'negative'}
            >
              <ThumbsDown className="w-3 h-3" />
            </Button>
          </div>
        )}

        {/* Timestamp */}
        {showTimestamp && (
          <div className={`text-xs text-muted-foreground mt-2 ${isAssistant ? 'ml-2' : 'mr-2'}`}>
            {new Date(message.timestamp).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;