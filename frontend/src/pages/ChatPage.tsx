import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Navigation } from "@/components/Navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Send, Bot, User, Sparkles, MessageSquare, TrendingUp, Loader2, AlertCircle } from "lucide-react";
import { ParticleBackground } from "@/components/ParticleBackground";
import { chatService, ChatMessage, ChatSession } from "@/services/chat";
import { userService } from "@/services/user";
import { portfolioService } from "@/services/portfolio";

const ChatPage = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userContext, setUserContext] = useState<any>(null);

  const quickPrompts = [
    "Analyze my portfolio performance",
    "Suggest investment opportunities", 
    "Help me plan for retirement",
    "Create a budget strategy",
    "Risk assessment for my goals"
  ];

  // Load user context and initialize chat
  useEffect(() => {
    const initializeChat = async () => {
      if (!isAuthenticated) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Load user context (portfolio, profile, etc.)
        const [portfolioData, financialProfile] = await Promise.allSettled([
          portfolioService.getPortfolioOverview().catch(() => null),
          userService.getFinancialProfile().catch(() => null)
        ]);

        const context = {
          portfolioData: portfolioData.status === 'fulfilled' ? portfolioData.value : null,
          financialProfile: financialProfile.status === 'fulfilled' ? financialProfile.value : null,
          user: user
        };
        setUserContext(context);

        // Try to get or create a chat session
        const sessions = await chatService.getChatSessions();
        if (sessions.length > 0) {
          const latestSession = sessions[0];
          setCurrentSession(latestSession);
          setMessages(latestSession.messages || []);
        } else {
          // Create a new session
          const newSession = await chatService.createChatSession(`Chat with ${user?.firstName || 'User'}`);
          setCurrentSession(newSession);
          
          // Add welcome message
          const welcomeMessage: ChatMessage = {
            id: `welcome-${Date.now()}`,
            content: `Hello ${user?.firstName || 'there'}! I'm your AI financial advisor. I can help you analyze your portfolio, create financial plans, and answer questions about your investments. How can I assist you today?`,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          };
          setMessages([welcomeMessage]);
        }
      } catch (err: any) {
        console.error('Failed to initialize chat:', err);
        setError(err.message || 'Failed to initialize chat. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    initializeChat();
  }, [isAuthenticated, user]);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !currentSession || isSending) return;

    const messageContent = inputMessage.trim();
    setInputMessage("");
    setIsSending(true);

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content: messageContent,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Send message to AI with user context
      const response = await chatService.sendMessage({
        message: messageContent,
        sessionId: currentSession.id,
        context: userContext
      });

      // Add AI response
      setMessages(prev => [...prev, response.message]);

      toast({
        title: "Message sent",
        description: "Your message has been processed successfully.",
      });
    } catch (err: any) {
      console.error('Failed to send message:', err);
      
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
  };

  const handleQuickPrompt = (prompt: string) => {
    setInputMessage(prompt);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background relative overflow-hidden">
        <ParticleBackground />
        <Navigation />
        
        <main className="relative z-10 pt-20 px-6 max-w-7xl mx-auto">
          <div className="mb-8">
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-6 w-80 mb-8" />
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="glass border-white/10">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <Skeleton className="w-12 h-12 rounded-lg" />
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-6 w-16" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Show authentication required state
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background relative overflow-hidden">
        <ParticleBackground />
        <Navigation />
        
        <main className="relative z-10 pt-20 px-6 max-w-7xl mx-auto">
          <div className="max-w-2xl mx-auto text-center py-20">
            <Alert className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Please <a href="/login" className="text-primary hover:underline font-semibold">log in</a> to access your personalized AI financial advisor.
              </AlertDescription>
            </Alert>
            <h1 className="text-4xl font-bold mb-4">AI Financial Advisor</h1>
            <p className="text-lg text-muted-foreground mb-8">
              Get personalized financial advice based on your portfolio and goals
            </p>
            <div className="flex gap-4 justify-center">
              <Button onClick={() => window.location.href = '/login'}>
                Sign In
              </Button>
              <Button variant="outline" onClick={() => window.location.href = '/signup'}>
                Get Started
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <ParticleBackground />
      <Navigation />
      
      <main className="relative z-10 pt-20 px-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary-glow to-success mb-2">
                AI Financial Advisor
              </h1>
              <p className="text-lg text-muted-foreground">
                Get personalized financial advice powered by artificial intelligence
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <Badge variant="outline" className="glass border-primary/30 text-primary">
                AI Powered
              </Badge>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Chat Sessions</p>
                    <p className="text-2xl font-bold">24</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-success to-success-dark flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Recommendations</p>
                    <p className="text-2xl font-bold">18</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
                    <Bot className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">AI Accuracy</p>
                    <p className="text-2xl font-bold">94%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <Card className="glass border-white/10 animate-fade-in h-[600px] flex flex-col">
              <CardHeader className="border-b border-white/10">
                <CardTitle className="flex items-center gap-2">
                  <Bot className="w-5 h-5 text-primary" />
                  Financial AI Assistant
                </CardTitle>
              </CardHeader>
              
              {/* Messages */}
              <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message, index) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 animate-fade-in ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'assistant' 
                        ? 'bg-gradient-to-br from-primary to-primary-glow' 
                        : 'bg-gradient-to-br from-success to-success-dark'
                    }`}>
                      {message.role === 'assistant' ? (
                        <Bot className="w-4 h-4 text-white" />
                      ) : (
                        <User className="w-4 h-4 text-white" />
                      )}
                    </div>
                    <div className={`max-w-[70%] p-4 rounded-2xl ${
                      message.role === 'assistant'
                        ? 'bg-white/5 border border-white/10'
                        : 'bg-gradient-to-br from-primary/20 to-success/20 border border-primary/20'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      {message.metadata?.suggestions && (
                        <div className="mt-3 space-y-1">
                          {message.metadata.suggestions.map((suggestion, i) => (
                            <Button
                              key={i}
                              variant="ghost"
                              size="sm"
                              className="h-auto p-2 text-xs text-left justify-start"
                              onClick={() => setInputMessage(suggestion)}
                            >
                              💡 {suggestion}
                            </Button>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground mt-2">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                
                {/* Loading indicator for AI response */}
                {isSending && (
                  <div className="flex gap-3 animate-fade-in">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="max-w-[70%] p-4 rounded-2xl bg-white/5 border border-white/10">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <p className="text-sm text-muted-foreground">AI is thinking...</p>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </CardContent>

              {/* Input */}
              <div className="p-4 border-t border-white/10">
                <div className="flex gap-2">
                  <Input
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask me anything about your finances..."
                    className="flex-1 glass border-white/20 bg-white/5"
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button 
                    onClick={handleSendMessage}
                    disabled={isSending || !inputMessage.trim()}
                    className="bg-gradient-to-r from-primary to-success hover:shadow-glow"
                  >
                    {isSending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="space-y-6">
            <Card className="glass border-white/10 animate-fade-in">
              <CardHeader>
                <CardTitle className="text-lg">Quick Prompts</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {quickPrompts.map((prompt, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="w-full text-left justify-start glass border-white/20 hover:bg-white/10 animate-fade-in"
                    style={{ animationDelay: `${index * 75}ms` }}
                    onClick={() => handleQuickPrompt(prompt)}
                  >
                    <Sparkles className="w-3 h-3 mr-2 text-primary" />
                    {prompt}
                  </Button>
                ))}
              </CardContent>
            </Card>

            <Card className="glass border-white/10 animate-fade-in">
              <CardHeader>
                <CardTitle className="text-lg">AI Capabilities</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-primary rounded-full" />
                  Portfolio Analysis
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-success rounded-full" />
                  Risk Assessment
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-accent rounded-full" />
                  Goal Planning
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-warning rounded-full" />
                  Market Insights
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-2 h-2 bg-primary-glow rounded-full" />
                  Tax Optimization
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="pb-20"></div>
      </main>
    </div>
  );
};

export default ChatPage;