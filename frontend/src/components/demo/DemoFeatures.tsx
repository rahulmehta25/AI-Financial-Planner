"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Award, 
  Zap, 
  TrendingUp, 
  Shield, 
  Users, 
  Star,
  ChevronRight,
  Clock,
  DollarSign,
  Target,
  CheckCircle2,
  AlertCircle,
  Activity
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { formatCurrency } from '@/lib/utils';

interface DemoFeaturesProps {
  data: any;
  onFeatureClick?: (feature: string) => void;
}

export function GamificationPanel({ data }: { data: any }) {
  const [animatedLevel, setAnimatedLevel] = useState(0);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedLevel(data.achievements.level.progress);
    }, 500);
    return () => clearTimeout(timer);
  }, [data.achievements.level.progress]);

  return (
    <Card id="gamification-panel" className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Award className="w-5 h-5 text-yellow-600" />
          Your Achievements
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Level Progress */}
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              Level {data.achievements.level.current}
            </div>
            <Progress value={animatedLevel} className="mt-2" />
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {data.achievements.level.pointsToNext} points to Level {data.achievements.level.nextLevel}
            </div>
          </div>
          
          {/* Badges */}
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Recent Badges</h4>
            {data.achievements.badges.slice(0, 3).map((badge: any, index: number) => (
              <motion.div
                key={badge.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`flex items-center gap-3 p-2 rounded-lg ${
                  badge.earned ? 'bg-green-50 dark:bg-green-900/20' : 'bg-gray-50 dark:bg-gray-800'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  badge.earned ? 'bg-green-500' : 'bg-gray-300'
                }`}>
                  {badge.earned ? (
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  ) : (
                    <div className="w-2 h-2 bg-white rounded-full" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium">{badge.title}</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    {badge.description}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Streaks */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-lg font-bold text-blue-600">
                {data.achievements.streaks.savings.current}
              </div>
              <div className="text-xs text-blue-600">Day Streak</div>
            </div>
            <div className="text-center p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="text-lg font-bold text-purple-600">
                {data.achievements.streaks.goalProgress.current}
              </div>
              <div className="text-xs text-purple-600">Goals Met</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function AIRecommendationsPanel({ data }: { data: any }) {
  const [currentRec, setCurrentRec] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentRec((prev) => (prev + 1) % data.simulation.recommendations.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [data.simulation.recommendations.length]);

  return (
    <Card id="recommendations-panel" className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-600" />
          AI-Powered Recommendations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentRec}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="space-y-4"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-lg">
                  {data.simulation.recommendations[currentRec]?.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {data.simulation.recommendations[currentRec]?.description}
                </p>
                <div className="flex items-center gap-2 mt-3">
                  <Badge className={`${
                    data.simulation.recommendations[currentRec]?.priority === 'high' 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {data.simulation.recommendations[currentRec]?.priority} Priority
                  </Badge>
                  <Badge variant="outline">
                    {data.simulation.recommendations[currentRec]?.impact} Impact
                  </Badge>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <div className="flex space-x-1">
                {data.simulation.recommendations.map((_: any, index: number) => (
                  <div
                    key={index}
                    className={`w-2 h-2 rounded-full transition-colors duration-300 ${
                      index === currentRec ? 'bg-yellow-500' : 'bg-gray-300'
                    }`}
                  />
                ))}
              </div>
              <Button size="sm" variant="outline">
                Apply Recommendation
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </motion.div>
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}

export function RealTimeMetrics({ data }: { data: any }) {
  const [metrics, setMetrics] = useState({
    portfolioValue: data.profile.currentSavings,
    dailyChange: 0,
    weeklyReturn: 0,
    monthlyGrowth: 0
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        portfolioValue: prev.portfolioValue + (Math.random() - 0.5) * 100,
        dailyChange: (Math.random() - 0.5) * 2,
        weeklyReturn: (Math.random() - 0.3) * 3,
        monthlyGrowth: (Math.random() + 0.2) * 2
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, [data.profile.currentSavings]);

  return (
    <Card id="real-time-metrics" className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-green-600" />
          Live Market Data
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="text-2xl font-bold">
              {formatCurrency(metrics.portfolioValue)}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Current Portfolio Value
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">Daily Change</span>
              <span className={`text-sm font-medium ${
                metrics.dailyChange >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {metrics.dailyChange >= 0 ? '+' : ''}{metrics.dailyChange.toFixed(2)}%
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm">Weekly Return</span>
              <span className={`text-sm font-medium ${
                metrics.weeklyReturn >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {metrics.weeklyReturn >= 0 ? '+' : ''}{metrics.weeklyReturn.toFixed(2)}%
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm">Monthly Growth</span>
              <span className={`text-sm font-medium ${
                metrics.monthlyGrowth >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {metrics.monthlyGrowth >= 0 ? '+' : ''}{metrics.monthlyGrowth.toFixed(2)}%
              </span>
            </div>
          </div>
          
          <div className="pt-3 border-t">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Clock className="w-4 h-4" />
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function SocialFeaturesPanel({ data }: { data: any }) {
  const mockCommunityData = {
    ranking: 23,
    totalUsers: 156,
    recentAchievements: [
      { user: 'Sarah K.', achievement: 'Emergency Fund Complete', timeAgo: '2h ago' },
      { user: 'Mike R.', achievement: 'First $10K Saved', timeAgo: '5h ago' },
      { user: 'Anna L.', achievement: 'Debt Free Journey', timeAgo: '1d ago' }
    ],
    challenges: [
      { name: 'Save $500 This Month', participants: 42, progress: 78 },
      { name: 'Investment Streak', participants: 28, progress: 65 }
    ]
  };

  return (
    <Card id="social-features" className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5 text-blue-600" />
          Community & Social Features
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Community Ranking */}
          <div className="space-y-4">
            <h4 className="font-medium">Your Community Ranking</h4>
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">
                #{mockCommunityData.ranking}
              </div>
              <div className="text-sm text-blue-600">
                out of {mockCommunityData.totalUsers} members
              </div>
            </div>
            
            <div className="space-y-2">
              <h5 className="text-sm font-medium">Active Challenges</h5>
              {mockCommunityData.challenges.map((challenge, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{challenge.name}</span>
                    <span>{challenge.participants} participants</span>
                  </div>
                  <Progress value={challenge.progress} className="h-2" />
                </div>
              ))}
            </div>
          </div>
          
          {/* Recent Community Activity */}
          <div className="space-y-4">
            <h4 className="font-medium">Recent Community Wins</h4>
            <div className="space-y-3">
              {mockCommunityData.recentAchievements.map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="flex items-center gap-3 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg"
                >
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                    <Star className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium">{item.user}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {item.achievement}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {item.timeAgo}
                  </div>
                </motion.div>
              ))}
            </div>
            
            <Button variant="outline" size="sm" className="w-full">
              Join Community Challenge
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function TradeOffScenariosPanel({ data, onFeatureClick }: { data: any; onFeatureClick?: (feature: string) => void }) {
  const scenarios = [
    {
      id: 'aggressive',
      title: 'Aggressive Growth',
      description: 'Higher risk, higher potential returns',
      impact: { risk: '+25%', return: '+15%', timeline: '-3 years' },
      color: 'red'
    },
    {
      id: 'conservative',
      title: 'Conservative Approach',
      description: 'Lower risk, stable growth',
      impact: { risk: '-30%', return: '-8%', timeline: '+2 years' },
      color: 'green'
    },
    {
      id: 'increased-savings',
      title: 'Boost Savings Rate',
      description: 'Increase monthly contributions by 25%',
      impact: { risk: 'same', return: '+12%', timeline: '-2 years' },
      color: 'blue'
    }
  ];

  return (
    <Card id="trade-off-scenarios" className="col-span-3">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          Scenario Analysis & Trade-offs
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {scenarios.map((scenario, index) => (
            <motion.div
              key={scenario.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => onFeatureClick?.(scenario.id)}
            >
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full bg-${scenario.color}-500`} />
                  <h4 className="font-medium">{scenario.title}</h4>
                </div>
                
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {scenario.description}
                </p>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Risk:</span>
                    <span className={`font-medium ${
                      scenario.impact.risk.includes('+') ? 'text-red-600' :
                      scenario.impact.risk.includes('-') ? 'text-green-600' :
                      'text-gray-600'
                    }`}>
                      {scenario.impact.risk}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Return:</span>
                    <span className={`font-medium ${
                      scenario.impact.return.includes('+') ? 'text-green-600' :
                      scenario.impact.return.includes('-') ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {scenario.impact.return}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Timeline:</span>
                    <span className={`font-medium ${
                      scenario.impact.timeline.includes('-') ? 'text-green-600' :
                      scenario.impact.timeline.includes('+') ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {scenario.impact.timeline}
                    </span>
                  </div>
                </div>
                
                <Button size="sm" variant="outline" className="w-full">
                  Simulate Scenario
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function DemoFeatures({ data, onFeatureClick }: DemoFeaturesProps) {
  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Top Row - Key Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <GamificationPanel data={data} />
          <AIRecommendationsPanel data={data} />
          <RealTimeMetrics data={data} />
        </div>
        
        {/* Middle Row - Social Features */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SocialFeaturesPanel data={data} />
        </div>
        
        {/* Bottom Row - Scenarios */}
        <TradeOffScenariosPanel data={data} onFeatureClick={onFeatureClick} />
      </div>
    </TooltipProvider>
  );
}