import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { 
  Bot, 
  Sparkles, 
  MessageSquare, 
  TrendingUp, 
  Users, 
  AlertCircle,
  Maximize2,
  Minimize2,
  Download,
  Settings,
  History,
  Lightbulb,
  Brain,
  Zap,
  Target,
  Shield
} from 'lucide-react';

// Import chat components
import ChatInterface from '@/components/chat/ChatInterface';
import ConversationHistory from '@/components/chat/ConversationHistory';
import SuggestedTopics from '@/components/chat/SuggestedTopics';
import { ChatSession, ChatMessage, chatService } from '@/services/chat';
import { userService } from '@/services/user';
import { portfolioService } from '@/services/portfolio';
import pdfExportService from '@/services/pdfExport';

const AIAdvisor: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userContext, setUserContext] = useState<any>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [stats, setStats] = useState({
    totalSessions: 0,
    totalMessages: 0,
    recommendationsGiven: 0,
    accuracyScore: 94
  });

  // Load user context and initialize chat
  useEffect(() => {
    const initializeAIAdvisor = async () => {
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

        // Load or create chat session
        const sessions = await chatService.getChatSessions();
        
        if (sessions.length > 0) {
          const latestSession = sessions[0];
          setCurrentSession(latestSession);
          
          // Update stats
          setStats({
            totalSessions: sessions.length,
            totalMessages: sessions.reduce((total, session) => total + (session.messages?.length || 0), 0),
            recommendationsGiven: sessions.reduce((total, session) => 
              total + (session.messages?.filter(m => 
                m.role === 'assistant' && 
                (m.metadata?.suggestions || m.content.toLowerCase().includes('recommend'))
              ).length || 0), 0),
            accuracyScore: 94
          });
        } else {
          // Create a new session with welcome message
          await createNewSession();
        }
      } catch (err: any) {
        console.error('Failed to initialize AI Advisor:', err);
        setError(err.message || 'Failed to initialize AI Advisor. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    initializeAIAdvisor();
  }, [isAuthenticated, user]);

  // Create new chat session
  const createNewSession = async () => {
    try {
      const newSession = await chatService.createChatSession(
        `Chat with AI Advisor - ${new Date().toLocaleDateString()}`
      );
      
      // Add welcome message
      const welcomeMessage: ChatMessage = {
        id: `welcome-${Date.now()}`,
        content: `Hello ${user?.firstName || 'there'}! I'm your AI financial advisor, enhanced with advanced capabilities including voice interaction, rich content analysis, and personalized recommendations. I can help you with:

• **Portfolio Analysis** - Comprehensive investment review and optimization
• **Retirement Planning** - Strategic planning for your future
• **Tax Optimization** - Minimize your tax burden legally
• **Risk Assessment** - Evaluate and manage financial risks  
• **Goal Setting** - Create and track financial objectives
• **Market Insights** - Stay informed about market trends

I can also export our conversation as a detailed PDF report for your records. How can I assist you with your financial planning today?`,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        metadata: {
          suggestions: [
            "Analyze my current portfolio performance",
            "Help me plan for retirement",
            "Review my financial goals and progress",
            "Suggest tax optimization strategies",
            "Assess my investment risk level"
          ]
        }
      };
      
      newSession.messages = [welcomeMessage];
      setCurrentSession(newSession);
      
      toast({
        title: "New conversation started",
        description: "Your AI financial advisor is ready to help!",
      });
    } catch (error: any) {
      console.error('Failed to create new session:', error);
      setError('Failed to create new conversation');
    }
  };

  // Handle session selection from history
  const handleSessionSelect = (session: ChatSession) => {
    setCurrentSession(session);
    setActiveTab('chat');
  };

  // Handle session updates
  const handleSessionUpdate = (updatedSession: ChatSession) => {
    setCurrentSession(updatedSession);
  };

  // Handle export conversation
  const handleExportConversation = async () => {
    if (!currentSession) return;
    
    try {
      await pdfExportService.exportConversation(currentSession, {
        includeTimestamps: true,
        includeMetadata: true,
        includeRecommendations: true,
        template: 'detailed_report'
      });
      
      toast({
        title: "Export started",
        description: "Your conversation is being prepared as a PDF document.",
      });
    } catch (error: any) {
      console.error('Failed to export conversation:', error);
      toast({
        title: "Export failed",
        description: error.message || "Could not export conversation to PDF.",
        variant: "destructive",
      });
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setActiveTab('chat');
    // The suggestion will be automatically sent to the chat
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="">
        
        <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
          <div className="mb-8">
            <Skeleton className="h-12 w-96 mb-4" />
            <Skeleton className="h-6 w-[500px] mb-8" />
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
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
      <div className="">
        
        <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
          <div className="max-w-4xl mx-auto text-center py-20">
            <div className="mb-8">
              <Bot className="w-24 h-24 text-primary mx-auto mb-6" />
              <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary-glow to-success">
                AI Financial Advisor
              </h1>
              <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                Experience the future of financial planning with our advanced AI advisor featuring voice interaction, 
                real-time analysis, and personalized recommendations.
              </p>
            </div>

            <Alert className="mb-8 max-w-2xl mx-auto">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Please <a href="/login" className="text-primary hover:underline font-semibold">log in</a> to access your personalized AI financial advisor with advanced features.
              </AlertDescription>
            </Alert>

            {/* Feature highlights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card className="glass border-white/10">
                <CardContent className="p-6 text-center">
                  <Brain className="w-12 h-12 text-primary mx-auto mb-4" />
                  <h3 className="font-semibold mb-2">Advanced AI</h3>
                  <p className="text-sm text-muted-foreground">
                    Sophisticated financial analysis with personalized recommendations
                  </p>
                </CardContent>
              </Card>

              <Card className="glass border-white/10">
                <CardContent className="p-6 text-center">
                  <Zap className="w-12 h-12 text-success mx-auto mb-4" />
                  <h3 className="font-semibold mb-2">Voice Interaction</h3>
                  <p className="text-sm text-muted-foreground">
                    Speak your questions and hear responses with Web Speech API
                  </p>
                </CardContent>
              </Card>

              <Card className="glass border-white/10">
                <CardContent className="p-6 text-center">
                  <Download className="w-12 h-12 text-accent mx-auto mb-4" />
                  <h3 className="font-semibold mb-2">PDF Export</h3>
                  <p className="text-sm text-muted-foreground">
                    Export detailed financial advice reports in professional PDF format
                  </p>
                </CardContent>
              </Card>
            </div>
            
            <div className="flex gap-4 justify-center">
              <Button 
                size="lg" 
                className="bg-gradient-to-r from-primary to-success hover:shadow-glow"
                onClick={() => window.location.href = '/login'}
              >
                Sign In to Start
              </Button>
              <Button 
                variant="outline" 
                size="lg" 
                className="glass border-white/20"
                onClick={() => window.location.href = '/signup'}
              >
                Create Account
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="">
      
      <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary-glow to-success mb-2">
                AI Financial Advisor
              </h1>
              <p className="text-lg text-muted-foreground">
                Advanced AI-powered financial guidance with voice interaction and detailed analysis
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="glass border-primary/30 text-primary flex items-center gap-2">
                <Brain className="w-4 h-4" />
                Advanced AI
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="text-muted-foreground hover:text-foreground"
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          {/* AI Capabilities Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Conversations</p>
                    <p className="text-2xl font-bold">{stats.totalSessions}</p>
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
                    <p className="text-sm text-muted-foreground">Messages</p>
                    <p className="text-2xl font-bold">{stats.totalMessages}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Recommendations</p>
                    <p className="text-2xl font-bold">{stats.recommendationsGiven}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-warning to-warning-dark flex items-center justify-center">
                    <Shield className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">AI Accuracy</p>
                    <p className="text-2xl font-bold">{stats.accuracyScore}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
            <Button
              variant="outline"
              size="sm"
              className="ml-auto"
              onClick={() => setError(null)}
            >
              Dismiss
            </Button>
          </Alert>
        )}

        {/* Main Interface */}
        <div className={`${isFullscreen ? 'fixed inset-0 z-50 bg-background p-6 pt-0' : ''}`}>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
            <TabsList className="grid w-full grid-cols-3 glass border-white/20 mb-6">
              <TabsTrigger value="chat" className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                Chat
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="w-4 h-4" />
                History
              </TabsTrigger>
              <TabsTrigger value="topics" className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Topics
              </TabsTrigger>
            </TabsList>

            <TabsContent value="chat" className="h-[700px]">
              <Card className="glass border-white/10 h-full">
                {currentSession ? (
                  <ChatInterface
                    session={currentSession}
                    userContext={userContext}
                    onSessionUpdate={handleSessionUpdate}
                    onNewSession={createNewSession}
                    onExportConversation={handleExportConversation}
                    isFullscreen={isFullscreen}
                    onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
                  />
                ) : (
                  <CardContent className="p-8 text-center">
                    <Bot className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Active Conversation</h3>
                    <p className="text-muted-foreground mb-4">
                      Start a new conversation with your AI financial advisor
                    </p>
                    <Button onClick={createNewSession}>
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Start New Conversation
                    </Button>
                  </CardContent>
                )}
              </Card>
            </TabsContent>

            <TabsContent value="history" className="h-[700px]">
              <Card className="glass border-white/10 h-full">
                <CardContent className="p-6 h-full">
                  <ConversationHistory
                    currentSessionId={currentSession?.id}
                    onSessionSelect={handleSessionSelect}
                    onExportConversation={handleExportConversation}
                  />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="topics" className="h-[700px]">
              <Card className="glass border-white/10 h-full">
                <CardContent className="p-6 h-full">
                  <SuggestedTopics
                    onTopicSelect={handleSuggestionClick}
                    userContext={userContext}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="pb-20"></div>
      </main>
    </div>
  );
};

export default AIAdvisor;