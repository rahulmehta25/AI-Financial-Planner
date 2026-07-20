import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Sparkles, 
  TrendingUp, 
  DollarSign, 
  Shield, 
  PieChart, 
  Target, 
  CreditCard, 
  Home, 
  GraduationCap, 
  Heart, 
  Car, 
  Plane,
  Calendar,
  AlertTriangle,
  Info,
  ChevronRight,
  RotateCcw
} from 'lucide-react';

interface SuggestedTopic {
  id: string;
  category: string;
  title: string;
  description: string;
  prompt: string;
  icon: React.ReactNode;
  priority: 'high' | 'medium' | 'low';
  isPersonalized: boolean;
  contextHint?: string;
}

interface SuggestedTopicsProps {
  onTopicSelect: (prompt: string) => void;
  userContext?: {
    portfolioData?: any;
    financialProfile?: any;
    goals?: any[];
    recentActivity?: string[];
  };
  className?: string;
}

const SuggestedTopics: React.FC<SuggestedTopicsProps> = ({
  onTopicSelect,
  userContext,
  className = ''
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [topics, setTopics] = useState<SuggestedTopic[]>([]);

  // Categories for filtering
  const categories = [
    { id: 'all', name: 'All Topics', icon: <Sparkles className="w-4 h-4" /> },
    { id: 'portfolio', name: 'Portfolio', icon: <PieChart className="w-4 h-4" /> },
    { id: 'planning', name: 'Planning', icon: <Target className="w-4 h-4" /> },
    { id: 'investing', name: 'Investing', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'insurance', name: 'Insurance', icon: <Shield className="w-4 h-4" /> },
    { id: 'taxes', name: 'Taxes', icon: <DollarSign className="w-4 h-4" /> },
    { id: 'goals', name: 'Goals', icon: <Target className="w-4 h-4" /> }
  ];

  // Generate personalized and general topics
  useEffect(() => {
    const generateTopics = () => {
      const baseTopics: SuggestedTopic[] = [
        // Portfolio Analysis
        {
          id: 'portfolio-analysis',
          category: 'portfolio',
          title: 'Portfolio Health Check',
          description: 'Get a comprehensive analysis of your investment portfolio',
          prompt: 'Please analyze my current portfolio performance, asset allocation, and provide recommendations for improvement.',
          icon: <PieChart className="w-5 h-5" />,
          priority: 'high',
          isPersonalized: true,
          contextHint: 'Based on your current holdings'
        },
        {
          id: 'portfolio-rebalancing',
          category: 'portfolio',
          title: 'Rebalancing Strategy',
          description: 'Learn when and how to rebalance your investments',
          prompt: 'How should I approach rebalancing my portfolio? What are the best practices and timing considerations?',
          icon: <TrendingUp className="w-5 h-5" />,
          priority: 'medium',
          isPersonalized: false
        },
        
        // Financial Planning
        {
          id: 'retirement-planning',
          category: 'planning',
          title: 'Retirement Planning',
          description: 'Create a comprehensive retirement strategy',
          prompt: 'Help me create a detailed retirement plan. What should I consider for my age and financial situation?',
          icon: <Calendar className="w-5 h-5" />,
          priority: 'high',
          isPersonalized: true,
          contextHint: 'Tailored to your age and goals'
        },
        {
          id: 'emergency-fund',
          category: 'planning',
          title: 'Emergency Fund Guidance',
          description: 'Build and optimize your emergency savings',
          prompt: 'How much should I have in my emergency fund and where should I keep it for the best returns?',
          icon: <Shield className="w-5 h-5" />,
          priority: 'high',
          isPersonalized: true
        },
        
        // Investment Topics
        {
          id: 'investment-opportunities',
          category: 'investing',
          title: 'Investment Opportunities',
          description: 'Discover new investment options suited to your profile',
          prompt: 'What investment opportunities should I consider based on my risk tolerance and financial goals?',
          icon: <Target className="w-5 h-5" />,
          priority: 'medium',
          isPersonalized: true
        },
        {
          id: 'market-outlook',
          category: 'investing',
          title: 'Market Outlook',
          description: 'Understand current market conditions and impacts',
          prompt: 'What is the current market outlook and how might it affect my investment strategy?',
          icon: <TrendingUp className="w-5 h-5" />,
          priority: 'medium',
          isPersonalized: false
        },
        
        // Tax Optimization
        {
          id: 'tax-optimization',
          category: 'taxes',
          title: 'Tax Optimization',
          description: 'Strategies to minimize your tax burden',
          prompt: 'What tax optimization strategies should I consider for this year and beyond?',
          icon: <DollarSign className="w-5 h-5" />,
          priority: 'high',
          isPersonalized: true
        },
        {
          id: 'tax-loss-harvesting',
          category: 'taxes',
          title: 'Tax Loss Harvesting',
          description: 'Use losses to reduce your tax liability',
          prompt: 'How can I use tax loss harvesting to reduce my tax burden? What are the rules and strategies?',
          icon: <DollarSign className="w-5 h-5" />,
          priority: 'medium',
          isPersonalized: true
        },
        
        // Insurance
        {
          id: 'insurance-review',
          category: 'insurance',
          title: 'Insurance Needs Review',
          description: 'Evaluate your insurance coverage and gaps',
          prompt: 'Please review my insurance needs. What types of coverage should I have and how much?',
          icon: <Shield className="w-5 h-5" />,
          priority: 'medium',
          isPersonalized: true
        },
        
        // Goal-specific topics
        {
          id: 'home-buying',
          category: 'goals',
          title: 'Home Buying Strategy',
          description: 'Plan for your home purchase',
          prompt: 'I want to buy a home. How should I prepare financially and what factors should I consider?',
          icon: <Home className="w-5 h-5" />,
          priority: 'medium',
          isPersonalized: false
        },
        {
          id: 'education-savings',
          category: 'goals',
          title: 'Education Savings',
          description: 'Save for education expenses',
          prompt: 'What are the best ways to save for education expenses? Should I use a 529 plan or other options?',
          icon: <GraduationCap className="w-5 h-5" />,
          priority: 'low',
          isPersonalized: false
        }
      ];

      // Add personalized topics based on user context
      const personalizedTopics: SuggestedTopic[] = [];

      if (userContext?.portfolioData) {
        // Add portfolio-specific suggestions
        if (userContext.portfolioData.performance < 0) {
          personalizedTopics.push({
            id: 'portfolio-underperforming',
            category: 'portfolio',
            title: 'Portfolio Underperformance',
            description: 'Address portfolio performance issues',
            prompt: 'My portfolio seems to be underperforming. Can you analyze what might be going wrong and suggest improvements?',
            icon: <AlertTriangle className="w-5 h-5" />,
            priority: 'high',
            isPersonalized: true,
            contextHint: 'Based on recent performance'
          });
        }
      }

      if (userContext?.goals?.length) {
        userContext.goals.forEach((goal: any) => {
          if (goal.progress < 50) {
            personalizedTopics.push({
              id: `goal-behind-${goal.id}`,
              category: 'goals',
              title: `${goal.name} Strategy`,
              description: `Get back on track with your ${goal.name} goal`,
              prompt: `I'm behind on my ${goal.name} goal. Can you help me create a strategy to get back on track?`,
              icon: <Target className="w-5 h-5" />,
              priority: 'high',
              isPersonalized: true,
              contextHint: 'You\'re behind on this goal'
            });
          }
        });
      }

      setTopics([...personalizedTopics, ...baseTopics]);
    };

    generateTopics();
  }, [userContext]);

  const filteredTopics = topics.filter(topic => 
    selectedCategory === 'all' || topic.category === selectedCategory
  );

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-500/30 text-red-400';
      case 'medium': return 'border-yellow-500/30 text-yellow-400';
      case 'low': return 'border-green-500/30 text-green-400';
      default: return 'border-white/30';
    }
  };

  const handleTopicClick = (topic: SuggestedTopic) => {
    onTopicSelect(topic.prompt);
  };

  const refreshTopics = () => {
    // Re-generate topics (could also fetch from API)
    const generateNewTopics = () => {
      // This would typically call an API to get fresh, personalized topics
      setTopics(prev => [...prev].sort(() => Math.random() - 0.5));
    };
    generateNewTopics();
  };

  return (
    <div className={`suggested-topics ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <h3 className="font-semibold">Suggested Topics</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={refreshTopics}
          className="text-muted-foreground hover:text-foreground"
        >
          <RotateCcw className="w-4 h-4" />
        </Button>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map((category) => (
          <Button
            key={category.id}
            variant={selectedCategory === category.id ? 'default' : 'outline'}
            size="sm"
            className="h-8 text-xs glass border-white/20"
            onClick={() => setSelectedCategory(category.id)}
          >
            {category.icon}
            <span className="ml-1">{category.name}</span>
          </Button>
        ))}
      </div>

      {/* Topics List */}
      <ScrollArea className="h-[400px]">
        <div className="space-y-3">
          {filteredTopics.map((topic) => (
            <Card
              key={topic.id}
              className={`glass border-white/10 hover:border-primary/30 transition-colors cursor-pointer group ${
                topic.isPersonalized ? 'border-l-4 border-l-primary' : ''
              }`}
              onClick={() => handleTopicClick(topic)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="text-primary mt-1">
                    {topic.icon}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="font-medium text-sm group-hover:text-primary transition-colors">
                          {topic.title}
                        </h4>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {topic.description}
                        </p>
                      </div>
                      
                      <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
                    </div>
                    
                    <div className="flex items-center gap-2 mt-3">
                      {topic.isPersonalized && (
                        <Badge variant="outline" className="text-xs glass border-primary/30 text-primary">
                          Personalized
                        </Badge>
                      )}
                      
                      <Badge 
                        variant="outline" 
                        className={`text-xs glass ${getPriorityColor(topic.priority)}`}
                      >
                        {topic.priority} priority
                      </Badge>
                      
                      {topic.contextHint && (
                        <span className="text-xs text-muted-foreground">
                          {topic.contextHint}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {filteredTopics.length === 0 && (
            <div className="text-center py-8">
              <Info className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                No topics available for this category
              </p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <p className="text-xs text-muted-foreground mb-2">Quick Actions:</p>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs glass border-white/20 hover:bg-white/10"
            onClick={() => onTopicSelect("What's my current financial health score?")}
          >
            Financial Health
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs glass border-white/20 hover:bg-white/10"
            onClick={() => onTopicSelect("Show me my spending patterns from last month")}
          >
            Spending Analysis
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs glass border-white/20 hover:bg-white/10"
            onClick={() => onTopicSelect("What financial goals should I set for this year?")}
          >
            Goal Setting
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SuggestedTopics;