'use client';

import React from 'react';
import { useGamificationStore } from '../store/gamificationStore';
import CelebrationAnimations, { useCelebration } from './CelebrationAnimations';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, Trophy, Flame, Crown, X, Zap } from 'lucide-react';

interface GamificationProviderProps {
  children: React.ReactNode;
  userId?: string;
  showFloatingIndicators?: boolean;
  showProgressBar?: boolean;
}

// Floating gamification indicators
function FloatingIndicators({ userProgress }: { userProgress: any }) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  if (!userProgress) return null;

  const indicators = [
    {
      icon: Crown,
      value: userProgress.level,
      label: 'Level',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      icon: Star,
      value: userProgress.availablePoints.toLocaleString(),
      label: 'Points',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      icon: Flame,
      value: userProgress.streaks.filter((s: any) => s.isActive).length,
      label: 'Streaks',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ];

  return (
    <motion.div
      className="fixed bottom-4 right-4 z-30"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 1 }}
    >
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mb-4 space-y-2"
          >
            {indicators.map((indicator, index) => {
              const Icon = indicator.icon;
              return (
                <motion.div
                  key={indicator.label}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="shadow-lg">
                    <CardContent className="p-3">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-full ${indicator.bgColor}`}>
                          <Icon className={`w-4 h-4 ${indicator.color}`} />
                        </div>
                        <div>
                          <div className="font-bold text-sm">{indicator.value}</div>
                          <div className="text-xs text-gray-600">{indicator.label}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-colors"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isExpanded ? (
          <X className="w-6 h-6" />
        ) : (
          <Trophy className="w-6 h-6" />
        )}
      </motion.button>
    </motion.div>
  );
}

// Progress bar for level progression
function LevelProgressBar({ userProgress, levels }: { userProgress: any; levels: any[] }) {
  if (!userProgress) return null;

  const currentLevel = levels.find(l => l.level === userProgress.level);
  const nextLevel = levels.find(l => l.level === userProgress.level + 1);

  if (!currentLevel || !nextLevel) return null;

  const pointsInCurrentLevel = userProgress.totalPoints - currentLevel.pointsRequired;
  const pointsForNextLevel = nextLevel.pointsRequired - currentLevel.pointsRequired;
  const progress = (pointsInCurrentLevel / pointsForNextLevel) * 100;

  return (
    <motion.div
      className="fixed top-0 left-0 right-0 z-20 bg-white shadow-sm border-b"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Crown className="w-5 h-5 text-purple-600" />
            <span className="font-semibold text-gray-900">
              Level {userProgress.level}: {currentLevel.title}
            </span>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Star className="w-4 h-4 text-yellow-600" />
              <span>{userProgress.availablePoints.toLocaleString()} points</span>
            </div>
            
            <div>
              {(pointsForNextLevel - pointsInCurrentLevel).toLocaleString()} to Level {nextLevel.level}
            </div>
          </div>
        </div>

        <div className="relative">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, progress)}%` }}
              transition={{ duration: 1, delay: 0.8 }}
            />
          </div>
          
          {/* Level markers */}
          <div className="absolute top-0 left-0 w-full h-2 flex justify-between">
            {[currentLevel.level, nextLevel.level].map((level, index) => (
              <div
                key={level}
                className={`w-4 h-4 -mt-1 rounded-full border-2 border-white ${
                  index === 0 ? 'bg-purple-500' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Achievement notification toast
function AchievementNotification({ 
  achievement, 
  isVisible, 
  onClose 
}: { 
  achievement: any; 
  isVisible: boolean; 
  onClose: () => void; 
}) {
  React.useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(onClose, 5000);
      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed top-20 right-4 z-40 max-w-sm"
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <Card className="shadow-lg border-yellow-200 bg-gradient-to-r from-yellow-50 to-orange-50">
            <CardContent className="p-4">
              <div className="flex items-start space-x-3">
                <div className="p-2 bg-yellow-100 rounded-full">
                  <Trophy className="w-6 h-6 text-yellow-600" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-semibold text-gray-900">Achievement Unlocked!</h3>
                    <Badge className="bg-yellow-500 text-white text-xs">
                      +{achievement.points}
                    </Badge>
                  </div>
                  
                  <h4 className="font-medium text-gray-800">{achievement.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{achievement.description}</p>
                </div>
                
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function GamificationProvider({
  children,
  userId,
  showFloatingIndicators = true,
  showProgressBar = false,
}: GamificationProviderProps) {
  const {
    userProgress,
    levels,
    initializeUserProgress,
    processEvent,
  } = useGamificationStore();

  const { celebrations, handleCelebrationComplete } = useCelebration();

  const [recentAchievement, setRecentAchievement] = React.useState<any>(null);

  // Initialize user progress
  React.useEffect(() => {
    if (userId && !userProgress) {
      initializeUserProgress(userId);
    }
  }, [userId, userProgress, initializeUserProgress]);

  // Track daily login
  React.useEffect(() => {
    if (userId && userProgress) {
      const today = new Date().toDateString();
      const lastLogin = userProgress.stats.lastLoginDate 
        ? new Date(userProgress.stats.lastLoginDate).toDateString()
        : null;

      if (lastLogin !== today) {
        processEvent({
          type: 'daily_login',
          userId,
          metadata: {},
          timestamp: new Date(),
        });
      }
    }
  }, [userId, userProgress, processEvent]);

  // Handle achievement notifications
  React.useEffect(() => {
    const handleAchievementUnlock = (event: CustomEvent) => {
      setRecentAchievement(event.detail.achievement);
    };

    window.addEventListener('achievement-unlocked' as any, handleAchievementUnlock);
    return () => {
      window.removeEventListener('achievement-unlocked' as any, handleAchievementUnlock);
    };
  }, []);

  return (
    <div className="relative">
      {/* Main content with potential top padding for progress bar */}
      <div className={showProgressBar && userProgress ? 'pt-20' : ''}>
        {children}
      </div>

      {/* Gamification UI overlays */}
      {userProgress && (
        <>
          {/* Level progress bar */}
          {showProgressBar && (
            <LevelProgressBar userProgress={userProgress} levels={levels} />
          )}

          {/* Floating indicators */}
          {showFloatingIndicators && (
            <FloatingIndicators userProgress={userProgress} />
          )}

          {/* Achievement notification */}
          <AchievementNotification
            achievement={recentAchievement}
            isVisible={!!recentAchievement}
            onClose={() => setRecentAchievement(null)}
          />
        </>
      )}

      {/* Celebration animations */}
      <CelebrationAnimations
        celebrations={celebrations}
        onCelebrationComplete={handleCelebrationComplete}
      />
    </div>
  );
}

// Context for gamification integration
interface GamificationContextType {
  trackFormCompletion: (step: string, userId: string) => void;
  trackGoalCreation: (goalData: any, userId: string) => void;
  trackMilestoneProgress: (milestoneId: string, currentValue: number, userId: string) => void;
  userProgress: any;
  isInitialized: boolean;
}

const GamificationContext = React.createContext<GamificationContextType | null>(null);

export function GamificationContextProvider({ 
  children, 
  userId 
}: { 
  children: React.ReactNode; 
  userId?: string; 
}) {
  const {
    userProgress,
    processEvent,
    initializeUserProgress,
  } = useGamificationStore();

  React.useEffect(() => {
    if (userId && !userProgress) {
      initializeUserProgress(userId);
    }
  }, [userId, userProgress, initializeUserProgress]);

  const trackFormCompletion = React.useCallback((step: string, userId: string) => {
    processEvent({
      type: 'form_completed',
      userId,
      metadata: { step },
      timestamp: new Date(),
    });
  }, [processEvent]);

  const trackGoalCreation = React.useCallback((goalData: any, userId: string) => {
    processEvent({
      type: 'goal_created',
      userId,
      metadata: { goalData },
      timestamp: new Date(),
    });
  }, [processEvent]);

  const trackMilestoneProgress = React.useCallback((milestoneId: string, currentValue: number, userId: string) => {
    processEvent({
      type: 'milestone_reached',
      userId,
      metadata: { milestoneId, currentValue },
      timestamp: new Date(),
    });
  }, [processEvent]);

  const value = {
    trackFormCompletion,
    trackGoalCreation,
    trackMilestoneProgress,
    userProgress,
    isInitialized: !!userProgress,
  };

  return (
    <GamificationContext.Provider value={value}>
      {children}
    </GamificationContext.Provider>
  );
}

export function useGamificationContext() {
  const context = React.useContext(GamificationContext);
  if (!context) {
    throw new Error('useGamificationContext must be used within GamificationContextProvider');
  }
  return context;
}