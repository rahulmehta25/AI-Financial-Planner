import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  BrainCircuit,
  Send,
  MessageSquare,
  Lightbulb,
} from 'lucide-react';
import { AI_ADVISOR_RESPONSES } from '@/data/demoData';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SUGGESTED_QUESTIONS = [
  { key: '401k', label: 'Should I increase my 401(k) contributions?' },
  { key: 'recession', label: 'How should I rebalance for a potential recession?' },
  { key: 'tax_harvesting', label: 'What tax loss harvesting opportunities do I have?' },
];

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: `Hello! I'm your AI financial advisor. I can help you with personalized investment guidance based on your $247K portfolio across 8 holdings.

Here are some topics I can help with:

- **401(k) optimization** and contribution strategies
- **Portfolio rebalancing** for different market conditions
- **Tax loss harvesting** opportunities in your portfolio

Select a question below or type your own to get started.`,
  timestamp: new Date(),
};

const AIAdvisor: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const findResponse = (text: string): string => {
    const lower = text.toLowerCase();
    if (lower.includes('401k') || lower.includes('401(k)') || lower.includes('increase') && lower.includes('contribution')) {
      return AI_ADVISOR_RESPONSES['401k'].answer;
    }
    if (lower.includes('rebalance') || lower.includes('recession') || lower.includes('downturn')) {
      return AI_ADVISOR_RESPONSES['recession'].answer;
    }
    if (lower.includes('tax') || lower.includes('harvest') || lower.includes('loss')) {
      return AI_ADVISOR_RESPONSES['tax_harvesting'].answer;
    }
    return `That's a great question. Based on your current portfolio of $247K across 8 diversified holdings, here are my thoughts:

Your portfolio shows strong performance with significant gains across most positions, particularly NVDA (+71.7%) and AMZN (+39.5%). Your overall allocation is growth-oriented with 66% in technology.

For a more specific analysis, try asking me about:
- **401(k) contributions** - optimization strategies
- **Recession preparedness** - defensive rebalancing
- **Tax loss harvesting** - saving on taxes

I can provide detailed, actionable advice on any of these topics.`;
  };

  const handleSend = (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      const response = findResponse(messageText);
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsTyping(false);
    }, 800);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
              <BrainCircuit className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">AI Model</p>
              <p className="text-sm font-semibold">Advanced</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Messages</p>
              <p className="text-sm font-semibold">{messages.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center">
              <Lightbulb className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Topics</p>
              <p className="text-sm font-semibold">{SUGGESTED_QUESTIONS.length} available</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chat Area */}
      <Card className="flex flex-col" style={{ height: '600px' }}>
        <CardHeader className="pb-3 border-b shrink-0">
          <CardTitle className="flex items-center gap-2 text-lg">
            <BrainCircuit className="h-5 w-5 text-emerald-600" />
            AI Financial Advisor
            <Badge variant="outline" className="ml-auto text-xs font-normal">Demo Mode</Badge>
          </CardTitle>
        </CardHeader>

        {/* Messages */}
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-lg px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-muted'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none prose-p:my-1 prose-li:my-0.5 prose-headings:my-2 prose-strong:text-foreground">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg px-4 py-3 text-sm text-muted-foreground">
                <span className="animate-pulse">Analyzing your portfolio...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </CardContent>

        {/* Suggested Questions */}
        <div className="px-4 py-2 border-t shrink-0">
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((q) => (
              <Button
                key={q.key}
                variant="outline"
                size="sm"
                className="text-xs h-7"
                onClick={() => handleSend(q.label)}
                disabled={isTyping}
              >
                {q.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="p-4 border-t shrink-0">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your portfolio..."
              disabled={isTyping}
              className="flex-1"
            />
            <Button
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AIAdvisor;
