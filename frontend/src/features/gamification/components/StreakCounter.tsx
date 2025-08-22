'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Flame, 
  Calendar, 
  TrendingUp, 
  Target, 
  Clock, 
  CheckCircle,
  PiggyBank,
  BookOpen,
  BarChart3,
  DollarSign
} from 'lucide-react';
import { Streak, StreakType } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface StreakCounterProps {
  streak: Streak;
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
  animated?: boolean;
  onStreakClick?: (streak: Streak) => void;
}

const streakConfig: Record<StreakType, {
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  description: string;
}> = {
  daily_login: {
    icon: Calendar,
    color: 'from-blue-400 to-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
    description: 'Daily app engagement',
  },
  weekly_savings: {
    icon: PiggyBank,
    color: 'from-green-400 to-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    description: 'Consistent saving habits',
  },
  monthly_budget_review: {
    icon: BarChart3,
    color: 'from-purple-400 to-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-800',
    description: 'Regular budget reviews',
  },
  goal_check_in: {
    icon: Target,
    color: 'from-orange-400 to-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-800',
    description: 'Goal progress updates',
  },
  investment_review: {
    icon: TrendingUp,
    color: 'from-indigo-400 to-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    textColor: 'text-indigo-800',
    description: 'Investment portfolio monitoring',
  },
  education_completion: {
    icon: BookOpen,
    color: 'from-pink-400 to-pink-600',
    bgColor: 'bg-pink-50',
    borderColor: 'border-pink-200',
    textColor: 'text-pink-800',
    description: 'Learning and education',
  },
};

function StreakFlame({ count, isActive, size = 'medium' }: { 
  count: number; 
  isActive: boolean; 
  size?: 'small' | 'medium' | 'large';
}) {
  const sizeConfig = {
    small: { icon: 'w-6 h-6', text: 'text-sm' },
    medium: { icon: 'w-8 h-8', text: 'text-base' },
    large: { icon: 'w-12 h-12', text: 'text-xl' },
  };

  const flameVariants = {
    inactive: { scale: 0.8, opacity: 0.5 },
    active: {
      scale: [0.8, 1.1, 1],
      opacity: [0.7, 1, 0.9],
      transition: {
        duration: 2,
        repeat: Infinity,
        repeatType: 'loop' as const,
      },
    },
  };

  return (
    <div className="relative flex items-center justify-center">
      <motion.div
        variants={flameVariants}
        animate={isActive ? 'active' : 'inactive'}
        className="relative"
      >
        <Flame 
          className={`
            ${sizeConfig[size].icon}
            ${isActive ? 'text-orange-500' : 'text-gray-400'}
            transition-colors duration-300
          `}
        />
        
        {/* Streak Count */}
        <div
          className={`
            absolute inset-0 flex items-center justify-center
            ${sizeConfig[size].text} font-bold
            ${isActive ? 'text-white' : 'text-gray-600'}
            drop-shadow-sm
          `}
        >
          {count}
        </div>
      </motion.div>

      {/* Glow Effect for High Streaks */}
      {isActive && count >= 30 && (
        <motion.div
          className="absolute inset-0 bg-orange-400 rounded-full opacity-20 blur-md"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
    </div>
  );
}

export default function StreakCounter({
  streak,
  size = 'medium',
  showDetails = true,
  animated = true,
  onStreakClick,
}: StreakCounterProps) {
  const config = streakConfig[streak.type];
  const Icon = config.icon;
  
  const daysSinceLastActivity = Math.floor(
    (new Date().getTime() - new Date(streak.lastActivityDate).getTime()) / (1000 * 60 * 60 * 24)
  );

  const getStreakStatus = () => {
    if (!streak.isActive) return 'inactive';
    if (daysSinceLastActivity === 0) return 'current';
    if (daysSinceLastActivity === 1) return 'at_risk';
    return 'broken';
  };

  const streakStatus = getStreakStatus();

  const statusConfig = {
    current: {
      badge: 'Active',
      badgeClass: 'bg-green-500 text-white',
      borderClass: 'border-green-300 ring-2 ring-green-200',
    },
    at_risk: {
      badge: 'At Risk',
      badgeClass: 'bg-yellow-500 text-white',
      borderClass: 'border-yellow-300 ring-2 ring-yellow-200',
    },
    broken: {
      badge: 'Broken',
      badgeClass: 'bg-red-500 text-white',
      borderClass: 'border-red-300',
    },
    inactive: {
      badge: 'Inactive',
      badgeClass: 'bg-gray-500 text-white',
      borderClass: 'border-gray-300',
    },
  };

  const currentStatus = statusConfig[streakStatus];

  const cardVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 30,
      },
    },
    hover: {
      scale: 1.02,
      transition: { duration: 0.2 },
    },
  };

  return (
    <motion.div
      id={`streak-counter-${streak.id}`}
      variants={animated ? cardVariants : undefined}
      initial={animated ? 'hidden' : undefined}
      animate={animated ? 'visible' : undefined}
      whileHover={animated ? 'hover' : undefined}
      className="cursor-pointer"
      onClick={() => onStreakClick?.(streak)}
    >
      <Card
        className={`
          relative overflow-hidden transition-all duration-300 hover:shadow-md
          ${config.bgColor} ${config.borderColor} ${currentStatus.borderClass}
        `}
      >
        {/* Status Badge */}
        <div
          id={`streak-status-${streak.id}`}
          className="absolute top-3 right-3 z-10"
        >
          <Badge className={currentStatus.badgeClass}>
            {currentStatus.badge}
          </Badge>
        </div>

        <CardContent className={size === 'small' ? 'p-4' : 'p-6'}>
          <div id={`streak-content-${streak.id}`} className="space-y-4">
            {/* Header */}
            <div className="flex items-center space-x-4">
              <div
                id={`streak-icon-container-${streak.id}`}
                className={`
                  p-3 rounded-full ${config.bgColor} ${config.borderColor} border
                  ${size === 'small' ? 'p-2' : 'p-3'}
                `}
              >
                <Icon
                  className={`
                    ${size === 'small' ? 'w-4 h-4' : size === 'medium' ? 'w-5 h-5' : 'w-6 h-6'}
                    ${config.textColor}
                  `}
                />
              </div>

              <div className="flex-1 min-w-0">
                <h3
                  id={`streak-name-${streak.id}`}
                  className={`
                    font-semibold text-gray-900
                    ${size === 'small' ? 'text-sm' : size === 'medium' ? 'text-base' : 'text-lg'}
                  `}
                >
                  {streak.name}
                </h3>
                
                {showDetails && (
                  <p
                    id={`streak-description-${streak.id}`}
                    className={`
                      text-gray-600 mt-1
                      ${size === 'small' ? 'text-xs' : 'text-sm'}
                    `}
                  >
                    {config.description}
                  </p>
                )}
              </div>

              <StreakFlame
                count={streak.currentCount}
                isActive={streak.isActive && streakStatus === 'current'}
                size={size}
              />
            </div>

            {/* Streak Statistics */}
            {showDetails && (
              <div id={`streak-stats-${streak.id}`} className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div
                      className={`
                        font-bold ${config.textColor}
                        ${size === 'small' ? 'text-lg' : size === 'medium' ? 'text-xl' : 'text-2xl'}
                      `}
                    >
                      {streak.currentCount}
                    </div>
                    <div
                      className={`
                        text-gray-600
                        ${size === 'small' ? 'text-xs' : 'text-sm'}
                      `}
                    >
                      Current
                    </div>
                  </div>

                  <div className="text-center">
                    <div
                      className={`
                        font-bold text-gray-700
                        ${size === 'small' ? 'text-lg' : size === 'medium' ? 'text-xl' : 'text-2xl'}
                      `}
                    >
                      {streak.bestCount}
                    </div>
                    <div
                      className={`
                        text-gray-600
                        ${size === 'small' ? 'text-xs' : 'text-sm'}
                      `}
                    >
                      Best
                    </div>
                  </div>
                </div>

                {/* Progress to Next Milestone */}
                {streak.isActive && (
                  <div id={`streak-progress-${streak.id}`} className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Next milestone</span>
                      <span>{getNextMilestone(streak.currentCount)} days</span>
                    </div>
                    <Progress
                      value={getProgressToNextMilestone(streak.currentCount)}
                      className="h-2"
                    />
                  </div>
                )}

                {/* Multiplier Info */}
                {streak.multiplier > 1 && streak.isActive && (
                  <div
                    id={`streak-multiplier-${streak.id}`}
                    className="flex items-center justify-center space-x-2 p-2 bg-yellow-50 border border-yellow-200 rounded-lg"
                  >
                    <DollarSign className="w-4 h-4 text-yellow-600" />
                    <span className="text-sm text-yellow-800 font-medium">
                      {streak.multiplier}x Points Multiplier
                    </span>
                  </div>
                )}

                {/* Last Activity */}
                <div
                  id={`streak-last-activity-${streak.id}`}
                  className="flex items-center space-x-2 text-xs text-gray-500"
                >
                  <Clock className="w-3 h-3" />
                  <span>
                    Last activity: {new Date(streak.lastActivityDate).toLocaleDateString()}
                  </span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Helper functions
function getNextMilestone(currentCount: number): number {
  const milestones = [7, 14, 30, 60, 90, 180, 365];
  return milestones.find(m => m > currentCount) || (Math.ceil(currentCount / 100) * 100);
}

function getProgressToNextMilestone(currentCount: number): number {
  const nextMilestone = getNextMilestone(currentCount);
  const previousMilestone = currentCount >= 7 ? 
    [0, 7, 14, 30, 60, 90, 180, 365].filter(m => m <= currentCount).pop() || 0 : 0;
  
  return ((currentCount - previousMilestone) / (nextMilestone - previousMilestone)) * 100;
}

// Streak Grid Component
interface StreakGridProps {
  streaks: Streak[];
  onStreakClick?: (streak: Streak) => void;
  showInactiveStreaks?: boolean;
  sortBy?: 'current' | 'best' | 'type' | 'status';
}

export function StreakGrid({
  streaks,
  onStreakClick,
  showInactiveStreaks = true,
  sortBy = 'current',
}: StreakGridProps) {
  const filteredStreaks = showInactiveStreaks 
    ? streaks 
    : streaks.filter(s => s.isActive);

  const sortedStreaks = [...filteredStreaks].sort((a, b) => {
    switch (sortBy) {
      case 'best':
        return b.bestCount - a.bestCount;
      case 'type':
        return a.type.localeCompare(b.type);
      case 'status':
        return Number(b.isActive) - Number(a.isActive);
      default:
        return b.currentCount - a.currentCount;
    }
  });

  return (
    <div
      id="streak-grid"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      {sortedStreaks.map(streak => (
        <StreakCounter
          key={streak.id}
          streak={streak}
          onStreakClick={onStreakClick}
          showDetails={true}
          animated={true}
        />
      ))}
    </div>
  );
}

// Streak Summary Component
interface StreakSummaryProps {
  streaks: Streak[];
  className?: string;
}

export function StreakSummary({ streaks, className }: StreakSummaryProps) {
  const activeStreaks = streaks.filter(s => s.isActive);
  const totalActiveCount = activeStreaks.reduce((sum, s) => sum + s.currentCount, 0);
  const longestActiveStreak = Math.max(...activeStreaks.map(s => s.currentCount), 0);
  const bestOverallStreak = Math.max(...streaks.map(s => s.bestCount), 0);

  const streaksByType = streaks.reduce((acc, streak) => {
    const config = streakConfig[streak.type];
    acc[streak.type] = {
      streak,
      config,
      isActive: streak.isActive,
    };
    return acc;
  }, {} as Record<string, any>);

  return (
    <Card id="streak-summary" className={className}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Flame className="w-5 h-5 text-orange-500" />
          <span>Streak Summary</span>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{activeStreaks.length}</div>
            <div className="text-sm text-gray-600">Active Streaks</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{totalActiveCount}</div>
            <div className="text-sm text-gray-600">Total Days</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{longestActiveStreak}</div>
            <div className="text-sm text-gray-600">Longest Active</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{bestOverallStreak}</div>
            <div className="text-sm text-gray-600">Best Ever</div>
          </div>
        </div>

        {/* Streak Types */}
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">By Type</h4>
          {Object.values(streaksByType).map(({ streak, config, isActive }: any) => (
            <div key={streak.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <div className="flex items-center space-x-3">
                <config.icon className={`w-4 h-4 ${config.textColor}`} />
                <span className="text-sm font-medium">{streak.name}</span>
                {isActive && (
                  <Badge className="bg-green-500 text-white text-xs">
                    Active
                  </Badge>
                )}
              </div>
              
              <div className="flex items-center space-x-4 text-sm">
                <div className="text-center">
                  <div className="font-semibold">{streak.currentCount}</div>
                  <div className="text-xs text-gray-500">Current</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold">{streak.bestCount}</div>
                  <div className="text-xs text-gray-500">Best</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Motivation Message */}
        {activeStreaks.length > 0 && (
          <div className="p-4 bg-gradient-to-r from-orange-50 to-yellow-50 border border-orange-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <Flame className="w-5 h-5 text-orange-500" />
              <span className="font-medium text-orange-800">
                Keep the momentum going!
              </span>
            </div>
            <p className="text-sm text-orange-700 mt-1">
              You have {activeStreaks.length} active streak{activeStreaks.length !== 1 ? 's' : ''} building great financial habits.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}