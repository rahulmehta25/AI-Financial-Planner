import React, { useState, useEffect, useMemo } from 'react';
import { ChatSession, ChatMessage, chatService } from '@/services/chat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, 
  Calendar, 
  MessageSquare, 
  Trash2, 
  Download, 
  Star, 
  StarOff,
  Clock,
  Bot,
  User,
  Filter,
  SortDesc,
  MoreVertical,
  Eye,
  Archive
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ConversationHistoryProps {
  currentSessionId?: string;
  onSessionSelect: (session: ChatSession) => void;
  onSessionDelete?: (sessionId: string) => void;
  onExportConversation?: (session: ChatSession) => void;
  className?: string;
}

interface SessionWithMetrics extends ChatSession {
  messageCount: number;
  lastActivity: Date;
  isStarred: boolean;
  hasRecommendations: boolean;
  topics: string[];
}

const ConversationHistory: React.FC<ConversationHistoryProps> = ({
  currentSessionId,
  onSessionSelect,
  onSessionDelete,
  onExportConversation,
  className = ''
}) => {
  const { toast } = useToast();
  
  const [sessions, setSessions] = useState<SessionWithMetrics[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'date' | 'activity' | 'messages'>('date');
  const [filterBy, setFilterBy] = useState<'all' | 'starred' | 'recent' | 'has_recommendations'>('all');
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set());

  // Load conversations
  useEffect(() => {
    const loadConversations = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const chatSessions = await chatService.getChatSessions();
        
        // Enhance sessions with additional metrics
        const enhancedSessions: SessionWithMetrics[] = chatSessions.map(session => {
          const messageCount = session.messages?.length || 0;
          const lastMessage = session.messages?.[session.messages.length - 1];
          const lastActivity = lastMessage ? new Date(lastMessage.timestamp) : new Date(session.updatedAt);
          
          // Extract topics from messages
          const topics = extractTopicsFromMessages(session.messages || []);
          
          // Check for recommendations
          const hasRecommendations = session.messages?.some(msg => 
            msg.metadata?.suggestions || 
            msg.content.toLowerCase().includes('recommend')
          ) || false;

          return {
            ...session,
            messageCount,
            lastActivity,
            isStarred: localStorage.getItem(`starred-${session.id}`) === 'true',
            hasRecommendations,
            topics
          };
        });
        
        setSessions(enhancedSessions);
      } catch (err: any) {
        console.error('Failed to load conversations:', err);
        setError(err.message || 'Failed to load conversation history');
      } finally {
        setIsLoading(false);
      }
    };

    loadConversations();
  }, []);

  // Extract topics from conversation messages
  const extractTopicsFromMessages = (messages: ChatMessage[]): string[] => {
    const topics = new Set<string>();
    
    messages.forEach(message => {
      const content = message.content.toLowerCase();
      
      // Common financial topics
      if (content.includes('portfolio') || content.includes('investment')) topics.add('Portfolio');
      if (content.includes('retirement')) topics.add('Retirement');
      if (content.includes('tax')) topics.add('Tax');
      if (content.includes('budget') || content.includes('spending')) topics.add('Budgeting');
      if (content.includes('insurance')) topics.add('Insurance');
      if (content.includes('debt') || content.includes('loan')) topics.add('Debt');
      if (content.includes('savings') || content.includes('emergency fund')) topics.add('Savings');
      if (content.includes('goal')) topics.add('Goals');
      if (content.includes('risk')) topics.add('Risk Management');
      if (content.includes('real estate') || content.includes('home')) topics.add('Real Estate');
    });
    
    return Array.from(topics);
  };

  // Filter and sort sessions
  const filteredAndSortedSessions = useMemo(() => {
    let filtered = sessions;

    // Apply text search
    if (searchQuery) {
      filtered = filtered.filter(session =>
        session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        session.topics.some(topic => topic.toLowerCase().includes(searchQuery.toLowerCase())) ||
        session.messages?.some(msg => 
          msg.content.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    }

    // Apply filters
    switch (filterBy) {
      case 'starred':
        filtered = filtered.filter(session => session.isStarred);
        break;
      case 'recent':
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        filtered = filtered.filter(session => session.lastActivity > weekAgo);
        break;
      case 'has_recommendations':
        filtered = filtered.filter(session => session.hasRecommendations);
        break;
      default:
        break;
    }

    // Sort sessions
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'activity':
          return b.lastActivity.getTime() - a.lastActivity.getTime();
        case 'messages':
          return b.messageCount - a.messageCount;
        case 'date':
        default:
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      }
    });

    return filtered;
  }, [sessions, searchQuery, filterBy, sortBy]);

  const toggleStarred = (sessionId: string) => {
    setSessions(prev => prev.map(session => {
      if (session.id === sessionId) {
        const newStarred = !session.isStarred;
        localStorage.setItem(`starred-${sessionId}`, newStarred.toString());
        return { ...session, isStarred: newStarred };
      }
      return session;
    }));
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await chatService.deleteChatSession(sessionId);
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      onSessionDelete?.(sessionId);
      
      toast({
        title: "Conversation deleted",
        description: "The conversation has been permanently deleted.",
      });
    } catch (error) {
      toast({
        title: "Failed to delete",
        description: "Could not delete the conversation. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleExportSession = (session: SessionWithMetrics) => {
    onExportConversation?.(session);
  };

  const formatRelativeTime = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 bg-white/5 rounded animate-pulse" />
        <div className="space-y-2">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-16 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={`conversation-history ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-primary" />
          <h3 className="font-semibold">Conversation History</h3>
          <Badge variant="outline" className="glass border-white/20">
            {sessions.length}
          </Badge>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="space-y-3 mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 glass border-white/20 bg-white/5"
          />
        </div>

        <div className="flex gap-2">
          {/* Filter Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="glass border-white/20">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="glass bg-background/95 border-white/20">
              <DropdownMenuItem onClick={() => setFilterBy('all')}>
                All Conversations
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterBy('starred')}>
                <Star className="w-4 h-4 mr-2" />
                Starred
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterBy('recent')}>
                <Clock className="w-4 h-4 mr-2" />
                Recent (7 days)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setFilterBy('has_recommendations')}>
                <Bot className="w-4 h-4 mr-2" />
                With Recommendations
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Sort Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="glass border-white/20">
                <SortDesc className="w-4 h-4 mr-2" />
                Sort
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="glass bg-background/95 border-white/20">
              <DropdownMenuItem onClick={() => setSortBy('date')}>
                <Calendar className="w-4 h-4 mr-2" />
                By Date
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('activity')}>
                <Clock className="w-4 h-4 mr-2" />
                By Activity
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('messages')}>
                <MessageSquare className="w-4 h-4 mr-2" />
                By Messages
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Conversations List */}
      <ScrollArea className="h-[500px]">
        <div className="space-y-2">
          {filteredAndSortedSessions.map((session) => (
            <Card
              key={session.id}
              className={`glass border-white/10 hover:border-primary/30 transition-colors cursor-pointer group ${
                session.id === currentSessionId ? 'border-primary/50 bg-primary/5' : ''
              }`}
              onClick={() => onSessionSelect(session)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-medium text-sm truncate group-hover:text-primary transition-colors">
                        {session.title}
                      </h4>
                      {session.isStarred && (
                        <Star className="w-4 h-4 text-yellow-500 fill-current" />
                      )}
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mb-2">
                      <div className="flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" />
                        {session.messageCount} messages
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatRelativeTime(session.lastActivity)}
                      </div>
                    </div>

                    {/* Topics */}
                    {session.topics.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {session.topics.slice(0, 3).map((topic) => (
                          <Badge
                            key={topic}
                            variant="outline"
                            className="text-xs px-2 py-0 h-5 glass border-white/20"
                          >
                            {topic}
                          </Badge>
                        ))}
                        {session.topics.length > 3 && (
                          <Badge variant="outline" className="text-xs px-2 py-0 h-5 glass border-white/20">
                            +{session.topics.length - 3} more
                          </Badge>
                        )}
                      </div>
                    )}

                    {/* Indicators */}
                    <div className="flex items-center gap-2">
                      {session.hasRecommendations && (
                        <Badge variant="outline" className="text-xs glass border-success/30 text-success">
                          Has Recommendations
                        </Badge>
                      )}
                      {session.id === currentSessionId && (
                        <Badge variant="outline" className="text-xs glass border-primary/30 text-primary">
                          Current
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Actions Menu */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="glass bg-background/95 border-white/20" align="end">
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation();
                        onSessionSelect(session);
                      }}>
                        <Eye className="w-4 h-4 mr-2" />
                        View
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation();
                        toggleStarred(session.id);
                      }}>
                        {session.isStarred ? (
                          <>
                            <StarOff className="w-4 h-4 mr-2" />
                            Unstar
                          </>
                        ) : (
                          <>
                            <Star className="w-4 h-4 mr-2" />
                            Star
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation();
                        handleExportSession(session);
                      }}>
                        <Download className="w-4 h-4 mr-2" />
                        Export
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        className="text-destructive focus:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSession(session.id);
                        }}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardContent>
            </Card>
          ))}

          {filteredAndSortedSessions.length === 0 && (
            <div className="text-center py-8">
              <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-sm text-muted-foreground mb-2">
                {searchQuery || filterBy !== 'all'
                  ? 'No conversations match your criteria'
                  : 'No conversations yet'
                }
              </p>
              {searchQuery && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSearchQuery('')}
                  className="text-primary"
                >
                  Clear search
                </Button>
              )}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-primary">
              {sessions.length}
            </div>
            <div className="text-xs text-muted-foreground">Conversations</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-success">
              {sessions.reduce((sum, session) => sum + session.messageCount, 0)}
            </div>
            <div className="text-xs text-muted-foreground">Messages</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-accent">
              {sessions.filter(session => session.hasRecommendations).length}
            </div>
            <div className="text-xs text-muted-foreground">With Advice</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationHistory;