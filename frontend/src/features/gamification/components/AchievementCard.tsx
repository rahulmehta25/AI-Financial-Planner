'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Trophy, Lock, Star, Clock } from 'lucide-react';
import { Achievement } from '../types';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface AchievementCardProps {
  achievement: Achievement;
  size?: 'small' | 'medium' | 'large';
  showProgress?: boolean;
  onClick?: () => void;
}

const difficultyColors = {
  easy: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-blue-100 text-blue-800 border-blue-200',
  hard: 'bg-purple-100 text-purple-800 border-purple-200',
  legendary: 'bg-orange-100 text-orange-800 border-orange-200',
};

const categoryColors = {
  planning: 'bg-blue-50 border-blue-200',
  savings: 'bg-green-50 border-green-200',
  budgeting: 'bg-yellow-50 border-yellow-200',
  investment: 'bg-purple-50 border-purple-200',
  goals: 'bg-orange-50 border-orange-200',
  education: 'bg-indigo-50 border-indigo-200',
  consistency: 'bg-red-50 border-red-200',
  milestone: 'bg-pink-50 border-pink-200',
};

export default function AchievementCard({
  achievement,
  size = 'medium',
  showProgress = true,
  onClick,
}: AchievementCardProps) {
  const isUnlocked = achievement.isUnlocked;
  const progress = achievement.progress;

  const sizeClasses = {
    small: 'p-3',
    medium: 'p-4',
    large: 'p-6',
  };

  const iconSizes = {
    small: 'w-8 h-8 text-lg',
    medium: 'w-12 h-12 text-2xl',
    large: 'w-16 h-16 text-3xl',
  };

  return (
    <motion.div
      id={`achievement-card-${achievement.id}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="cursor-pointer"
      onClick={onClick}
    >
      <Card
        className={`
          relative overflow-hidden transition-all duration-300 hover:shadow-md
          ${categoryColors[achievement.category]}
          ${isUnlocked ? 'ring-2 ring-yellow-300 ring-opacity-50' : 'opacity-75'}
        `}
      >
        {isUnlocked && (
          <div
            id={`achievement-unlock-indicator-${achievement.id}`}
            className="absolute top-2 right-2"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="bg-yellow-400 rounded-full p-1"
            >
              <Trophy className="w-4 h-4 text-yellow-800" />
            </motion.div>
          </div>
        )}

        {achievement.hidden && !isUnlocked && (
          <div
            id={`achievement-hidden-indicator-${achievement.id}`}
            className="absolute top-2 right-2"
          >
            <Lock className="w-4 h-4 text-gray-400" />
          </div>
        )}

        <CardContent className={sizeClasses[size]}>
          <div id={`achievement-content-${achievement.id}`} className="space-y-3">
            {/* Icon and Title */}
            <div className="flex items-start space-x-3">
              <div
                id={`achievement-icon-${achievement.id}`}
                className={`
                  flex items-center justify-center rounded-full
                  ${iconSizes[size]}
                  ${isUnlocked ? 'bg-yellow-100' : 'bg-gray-100'}
                `}
              >
                {isUnlocked ? (
                  <span className="text-2xl">{achievement.icon}</span>
                ) : (
                  <Lock className="w-6 h-6 text-gray-400" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <h3
                  id={`achievement-title-${achievement.id}`}
                  className={`font-semibold ${
                    size === 'small' ? 'text-sm' : size === 'medium' ? 'text-base' : 'text-lg'
                  } ${isUnlocked ? 'text-gray-900' : 'text-gray-600'}`}
                >
                  {achievement.title}
                </h3>
                
                <p
                  id={`achievement-description-${achievement.id}`}
                  className={`text-gray-600 ${
                    size === 'small' ? 'text-xs' : 'text-sm'
                  } mt-1`}
                >
                  {achievement.description}
                </p>
              </div>
            </div>

            {/* Badges */}
            <div id={`achievement-badges-${achievement.id}`} className="flex flex-wrap gap-2">
              <Badge
                variant="outline"
                className={difficultyColors[achievement.difficulty]}
              >
                {achievement.difficulty}
              </Badge>
              
              <Badge variant="outline" className="bg-gray-50 text-gray-700">
                {achievement.points} pts
              </Badge>

              {achievement.category && (
                <Badge variant="outline" className="bg-gray-50 text-gray-700 capitalize">
                  {achievement.category}
                </Badge>
              )}
            </div>

            {/* Progress */}
            {showProgress && !isUnlocked && (
              <div id={`achievement-progress-${achievement.id}`} className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Progress</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}

            {/* Requirements */}
            {size !== 'small' && (
              <div id={`achievement-requirements-${achievement.id}`} className="space-y-1">
                <h4 className="text-sm font-medium text-gray-700">Requirements:</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  {achievement.requirements.map((req, index) => (
                    <li key={index} className="flex items-center space-x-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          isUnlocked ? 'bg-green-400' : 'bg-gray-300'
                        }`}
                      />
                      <span>{req.description}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Unlock Date */}
            {isUnlocked && achievement.unlockedAt && (
              <div
                id={`achievement-unlock-date-${achievement.id}`}
                className="flex items-center space-x-2 text-xs text-gray-500"
              >
                <Clock className="w-3 h-3" />
                <span>
                  Unlocked on {new Date(achievement.unlockedAt).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Achievement Grid Component
interface AchievementGridProps {
  achievements: Achievement[];
  filter?: 'all' | 'unlocked' | 'locked' | Achievement['category'];
  sortBy?: 'title' | 'difficulty' | 'points' | 'progress';
  showProgress?: boolean;
  onAchievementClick?: (achievement: Achievement) => void;
}

export function AchievementGrid({
  achievements,
  filter = 'all',
  sortBy = 'title',
  showProgress = true,
  onAchievementClick,
}: AchievementGridProps) {
  const filteredAchievements = achievements.filter(achievement => {
    if (filter === 'all') return true;
    if (filter === 'unlocked') return achievement.isUnlocked;
    if (filter === 'locked') return !achievement.isUnlocked;
    return achievement.category === filter;
  });

  const sortedAchievements = [...filteredAchievements].sort((a, b) => {
    switch (sortBy) {
      case 'difficulty':
        const difficultyOrder = { easy: 0, medium: 1, hard: 2, legendary: 3 };
        return difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
      case 'points':
        return b.points - a.points;
      case 'progress':
        return b.progress - a.progress;
      default:
        return a.title.localeCompare(b.title);
    }
  });

  return (
    <div
      id="achievement-grid"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      {sortedAchievements.map(achievement => (
        <AchievementCard
          key={achievement.id}
          achievement={achievement}
          showProgress={showProgress}
          onClick={() => onAchievementClick?.(achievement)}
        />
      ))}
    </div>
  );
}

// Achievement Summary Component
interface AchievementSummaryProps {
  achievements: Achievement[];
  className?: string;
}

export function AchievementSummary({ achievements, className }: AchievementSummaryProps) {
  const unlockedCount = achievements.filter(a => a.isUnlocked).length;
  const totalPoints = achievements
    .filter(a => a.isUnlocked)
    .reduce((sum, a) => sum + a.points, 0);

  const difficultyBreakdown = achievements.reduce((acc, achievement) => {
    if (achievement.isUnlocked) {
      acc[achievement.difficulty] = (acc[achievement.difficulty] || 0) + 1;
    }
    return acc;
  }, {} as Record<string, number>);

  return (
    <Card id="achievement-summary" className={className}>
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900">Achievement Summary</h3>
            <p className="text-gray-600">
              {unlockedCount} of {achievements.length} achievements unlocked
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{unlockedCount}</div>
              <div className="text-sm text-gray-600">Unlocked</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{totalPoints}</div>
              <div className="text-sm text-gray-600">Points Earned</div>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">By Difficulty:</h4>
            {Object.entries(difficultyBreakdown).map(([difficulty, count]) => (
              <div key={difficulty} className="flex justify-between text-sm">
                <span className="capitalize text-gray-600">{difficulty}:</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>

          <Progress
            value={(unlockedCount / achievements.length) * 100}
            className="h-3"
          />
        </div>
      </CardContent>
    </Card>
  );
}