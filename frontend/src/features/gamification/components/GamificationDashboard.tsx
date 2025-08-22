'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, 
  Star, 
  Target, 
  Users, 
  Gift, 
  Zap, 
  TrendingUp,
  Crown,
  Flame,
  Medal,
  Settings,
  BarChart3,
  Calendar,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { useGamificationStore } from '../store/gamificationStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';

// Import gamification components
import AchievementCard, { AchievementGrid, AchievementSummary } from './AchievementCard';
import BadgeDisplay, { BadgeCollection, BadgeProgress } from './BadgeDisplay';
import MilestoneTracker, { MilestoneSummary } from './MilestoneTracker';
import StreakCounter, { StreakGrid, StreakSummary } from './StreakCounter';
import Leaderboard from './Leaderboard';
import ChallengeSystem from './ChallengeSystem';
import RewardSystem, { PointsProgress } from './RewardSystem';
import LevelProgression, { AllLevelsModal, LevelBenefitsDetail } from './LevelProgression';
import CelebrationAnimations, { useCelebration, celebrationTriggers } from './CelebrationAnimations';

interface GamificationDashboardProps {
  userId?: string;
  className?: string;
}

// Quick Stats Component
function QuickStats({ userProgress }: { userProgress: any }) {
  if (!userProgress) return null;

  const stats = [
    {
      label: 'Level',
      value: userProgress.level,
      icon: Crown,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      label: 'Points',
      value: userProgress.totalPoints.toLocaleString(),
      icon: Star,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      label: 'Achievements',
      value: userProgress.achievements.filter((a: any) => a.isUnlocked).length,
      icon: Trophy,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Active Streaks',
      value: userProgress.streaks.filter((s: any) => s.isActive).length,
      icon: Flame,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className={`p-3 rounded-full ${stat.bgColor}`}>
                    <Icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-900">
                      {stat.value}
                    </div>
                    <div className="text-sm text-gray-600">{stat.label}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}

// Recent Activity Component
function RecentActivity({ activities }: { activities: any[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5" />
          <span>Recent Activity</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          {activities.slice(0, 5).map((activity, index) => (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
            >
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                {activity.type === 'achievement_unlocked' && <Trophy className="w-4 h-4 text-blue-600" />}
                {activity.type === 'badge_earned' && <Medal className="w-4 h-4 text-purple-600" />}
                {activity.type === 'level_up' && <Crown className="w-4 h-4 text-yellow-600" />}
                {activity.type === 'streak_extended' && <Flame className="w-4 h-4 text-orange-600" />}
                {activity.type === 'challenge_completed' && <Target className="w-4 h-4 text-green-600" />}
                {activity.type === 'milestone_reached' && <TrendingUp className="w-4 h-4 text-indigo-600" />}
                {activity.type === 'points_earned' && <Star className="w-4 h-4 text-yellow-600" />}
              </div>
              
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">
                  {activity.description}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(activity.timestamp).toLocaleDateString()}
                </div>
              </div>
              
              {activity.points && (
                <Badge className="bg-green-100 text-green-800">
                  +{activity.points}
                </Badge>
              )}
            </motion.div>
          ))}
          
          {activities.length === 0 && (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No recent activity yet</p>
              <p className="text-sm text-gray-400 mt-1">
                Start completing forms and setting goals to see your progress here!
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Progress Overview Component
function ProgressOverview({ userProgress }: { userProgress: any }) {
  if (!userProgress) return null;

  const completionStats = [
    {
      label: 'Achievements',
      current: userProgress.achievements.filter((a: any) => a.isUnlocked).length,
      total: userProgress.achievements.length,
      color: 'bg-blue-500',
    },
    {
      label: 'Challenges',
      current: userProgress.completedChallenges.length,
      total: userProgress.completedChallenges.length + userProgress.activeChallenges.length,
      color: 'bg-green-500',
    },
    {
      label: 'Milestones',
      current: userProgress.milestones.filter((m: any) => m.isCompleted).length,
      total: userProgress.milestones.length,
      color: 'bg-purple-500',
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Target className="w-5 h-5" />
          <span>Progress Overview</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {completionStats.map((stat, index) => {
          const percentage = stat.total > 0 ? (stat.current / stat.total) * 100 : 0;
          
          return (
            <div key={stat.label} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-gray-900">{stat.label}</span>
                <span className="text-gray-600">
                  {stat.current}/{stat.total}
                </span>
              </div>
              <Progress value={percentage} className="h-2" />
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export default function GamificationDashboard({ 
  userId, 
  className 
}: GamificationDashboardProps) {
  const {
    userProgress,
    achievements,
    availableBadges,
    leaderboards,
    availableChallenges,
    rewardRedemptions,
    levels,
    isLoading,
    error,
    // Actions
    initializeUserProgress,
    joinChallenge,
    leaveChallenge,
    processEvent,
    addPoints,
  } = useGamificationStore();

  const { 
    celebrations, 
    triggerCelebration, 
    handleCelebrationComplete 
  } = useCelebration();

  const [activeTab, setActiveTab] = React.useState('overview');
  const [showAllLevels, setShowAllLevels] = React.useState(false);
  const [showLevelBenefits, setShowLevelBenefits] = React.useState<any>(null);

  // Initialize user progress on mount
  React.useEffect(() => {
    if (userId && !userProgress) {
      initializeUserProgress(userId);
    }
  }, [userId, userProgress, initializeUserProgress]);

  // Handle gamification events
  const handleAchievementUnlock = React.useCallback((achievement: any) => {
    triggerCelebration(celebrationTriggers.achievementUnlocked(
      achievement.difficulty === 'legendary' ? 'epic' : 'high'
    ));
  }, [triggerCelebration]);

  const handleLevelUp = React.useCallback((newLevel: number) => {
    triggerCelebration(celebrationTriggers.levelUp(
      newLevel % 10 === 0 ? 'epic' : 'high'
    ));
  }, [triggerCelebration]);

  const handleChallengeComplete = React.useCallback((challenge: any) => {
    triggerCelebration(celebrationTriggers.challengeComplete(
      challenge.difficulty === 'expert' ? 'epic' : 'high'
    ));
  }, [triggerCelebration]);

  // Demo functions (would be replaced with real API calls)
  const handleJoinChallenge = React.useCallback((challengeId: string) => {
    joinChallenge(challengeId);
    addPoints(50, 'challenge_completion', 'Joined a new challenge');
  }, [joinChallenge, addPoints]);

  const handleRedeemReward = React.useCallback((redemptionId: string) => {
    // Implementation for reward redemption
    console.log('Redeeming reward:', redemptionId);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600">Loading your gamification progress...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="bg-red-50 border-red-200">
        <CardContent className="p-6 text-center">
          <div className="text-red-600 mb-2">Error loading gamification data</div>
          <p className="text-sm text-red-500">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!userProgress) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="space-y-4">
            <Sparkles className="w-12 h-12 text-gray-400 mx-auto" />
            <h3 className="text-lg font-medium text-gray-900">Welcome to Gamification!</h3>
            <p className="text-gray-600">
              Complete your first form section to start earning points and unlocking achievements.
            </p>
            <Button onClick={() => userId && initializeUserProgress(userId)}>
              Get Started
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div id="gamification-dashboard" className={`space-y-6 ${className}`}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4"
      >
        <h1 className="text-3xl font-bold text-gray-900">Financial Gamification</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Track your progress, earn rewards, and compete with others as you build better financial habits.
        </p>
      </motion.div>

      {/* Quick Stats */}
      <QuickStats userProgress={userProgress} />

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-8">
          <TabsTrigger value="overview" className="flex items-center space-x-1">
            <BarChart3 className="w-4 h-4" />
            <span className="hidden sm:inline">Overview</span>
          </TabsTrigger>
          
          <TabsTrigger value="achievements" className="flex items-center space-x-1">
            <Trophy className="w-4 h-4" />
            <span className="hidden sm:inline">Achievements</span>
          </TabsTrigger>
          
          <TabsTrigger value="progress" className="flex items-center space-x-1">
            <Target className="w-4 h-4" />
            <span className="hidden sm:inline">Progress</span>
          </TabsTrigger>
          
          <TabsTrigger value="streaks" className="flex items-center space-x-1">
            <Flame className="w-4 h-4" />
            <span className="hidden sm:inline">Streaks</span>
          </TabsTrigger>
          
          <TabsTrigger value="challenges" className="flex items-center space-x-1">
            <Target className="w-4 h-4" />
            <span className="hidden sm:inline">Challenges</span>
          </TabsTrigger>
          
          <TabsTrigger value="rewards" className="flex items-center space-x-1">
            <Gift className="w-4 h-4" />
            <span className="hidden sm:inline">Rewards</span>
          </TabsTrigger>
          
          <TabsTrigger value="levels" className="flex items-center space-x-1">
            <Crown className="w-4 h-4" />
            <span className="hidden sm:inline">Levels</span>
          </TabsTrigger>
          
          <TabsTrigger value="leaderboard" className="flex items-center space-x-1">
            <Users className="w-4 h-4" />
            <span className="hidden sm:inline">Leaderboard</span>
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RecentActivity activities={userProgress.recentActivity} />
            <ProgressOverview userProgress={userProgress} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AchievementSummary achievements={achievements} />
            <BadgeProgress badges={availableBadges} earnedBadges={userProgress.badges} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <StreakSummary streaks={userProgress.streaks} />
            <MilestoneSummary milestones={userProgress.milestones} />
          </div>
        </TabsContent>

        {/* Achievements Tab */}
        <TabsContent value="achievements" className="space-y-6">
          <AchievementGrid
            achievements={achievements}
            onAchievementClick={handleAchievementUnlock}
          />
        </TabsContent>

        {/* Progress Tab */}
        <TabsContent value="progress" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <BadgeCollection
              badges={availableBadges}
              earnedBadges={userProgress.badges}
              layout="showcase"
            />
          </div>
          
          <MilestoneTracker
            milestones={userProgress.milestones}
            groupByCategory={true}
          />
        </TabsContent>

        {/* Streaks Tab */}
        <TabsContent value="streaks" className="space-y-6">
          <StreakGrid
            streaks={userProgress.streaks}
            showInactiveStreaks={true}
          />
        </TabsContent>

        {/* Challenges Tab */}
        <TabsContent value="challenges" className="space-y-6">
          <ChallengeSystem
            availableChallenges={availableChallenges}
            activeChallenges={userProgress.activeChallenges}
            completedChallenges={userProgress.completedChallenges}
            onJoinChallenge={handleJoinChallenge}
            onLeaveChallenge={leaveChallenge}
            onViewChallenge={(challenge) => console.log('View challenge:', challenge)}
          />
        </TabsContent>

        {/* Rewards Tab */}
        <TabsContent value="rewards" className="space-y-6">
          <RewardSystem
            availablePoints={userProgress.availablePoints}
            totalPointsEarned={userProgress.totalPoints}
            recentPoints={userProgress.recentActivity
              .filter((a: any) => a.type === 'points_earned')
              .map((a: any) => ({
                id: a.id,
                amount: a.points || 0,
                source: 'form_completion' as any,
                description: a.description,
                earnedAt: a.timestamp,
              }))
            }
            availableRedemptions={rewardRedemptions}
            onRedeemReward={handleRedeemReward}
            onViewHistory={() => console.log('View history')}
          />
        </TabsContent>

        {/* Levels Tab */}
        <TabsContent value="levels" className="space-y-6">
          <LevelProgression
            userProgress={userProgress}
            levels={levels}
            onViewAllLevels={() => setShowAllLevels(true)}
            onViewBenefits={(level) => setShowLevelBenefits(level)}
          />
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="space-y-6">
          <Leaderboard
            leaderboards={leaderboards}
            currentUserId={userId}
            maxEntries={10}
          />
        </TabsContent>
      </Tabs>

      {/* Modals */}
      <AllLevelsModal
        levels={levels}
        currentLevel={userProgress.level}
        isOpen={showAllLevels}
        onClose={() => setShowAllLevels(false)}
        onSelectLevel={(level) => {
          setShowLevelBenefits(level);
          setShowAllLevels(false);
        }}
      />

      <LevelBenefitsDetail
        level={showLevelBenefits}
        isOpen={!!showLevelBenefits}
        onClose={() => setShowLevelBenefits(null)}
      />

      {/* Celebration Animations */}
      <CelebrationAnimations
        celebrations={celebrations}
        onCelebrationComplete={handleCelebrationComplete}
      />
    </div>
  );
}