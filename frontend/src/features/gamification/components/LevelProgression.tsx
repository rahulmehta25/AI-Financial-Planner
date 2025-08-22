'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Crown, 
  Star, 
  Zap, 
  TrendingUp, 
  Shield, 
  Target,
  Gift,
  Unlock,
  Lock,
  ChevronRight,
  Award,
  Sparkles,
  Users,
  Settings,
  BookOpen,
  Palette
} from 'lucide-react';
import { Level, LevelBenefit, UserProgress } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';

interface LevelProgressionProps {
  userProgress: UserProgress;
  levels: Level[];
  onViewAllLevels: () => void;
  onViewBenefits: (level: Level) => void;
}

const benefitTypeConfig: Record<LevelBenefit['type'], {
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  label: string;
}> = {
  point_multiplier: {
    icon: Zap,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 border-yellow-200',
    label: 'Points Boost',
  },
  feature_unlock: {
    icon: Unlock,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    label: 'Feature Unlock',
  },
  discount: {
    icon: Gift,
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    label: 'Discount',
  },
  priority_support: {
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    label: 'Priority Support',
  },
  exclusive_content: {
    icon: BookOpen,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50 border-indigo-200',
    label: 'Exclusive Content',
  },
};

function LevelCard({ 
  level, 
  isCurrentLevel = false, 
  isUnlocked = false,
  onClick
}: { 
  level: Level;
  isCurrentLevel?: boolean;
  isUnlocked?: boolean;
  onClick?: () => void;
}) {
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
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

  const glowVariants = {
    idle: { opacity: 0.5 },
    glow: {
      opacity: [0.5, 1, 0.5],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
  };

  return (
    <motion.div
      id={`level-card-${level.level}`}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      className="cursor-pointer"
      onClick={onClick}
    >
      <Card
        className={`
          relative overflow-hidden transition-all duration-300 hover:shadow-md
          ${isCurrentLevel ? 'ring-2 ring-blue-400 ring-opacity-50 bg-blue-50' : ''}
          ${isUnlocked ? 'bg-white' : 'bg-gray-50 opacity-75'}
        `}
      >
        {/* Current Level Glow */}
        {isCurrentLevel && (
          <motion.div
            variants={glowVariants}
            animate="glow"
            className="absolute inset-0 bg-gradient-to-br from-blue-200 to-purple-200 opacity-20"
          />
        )}

        {/* Lock/Unlock Indicator */}
        <div
          id={`level-status-${level.level}`}
          className="absolute top-3 right-3 z-10"
        >
          {isCurrentLevel ? (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="bg-blue-500 rounded-full p-1"
            >
              <Star className="w-4 h-4 text-white" />
            </motion.div>
          ) : isUnlocked ? (
            <Unlock className="w-5 h-5 text-green-500" />
          ) : (
            <Lock className="w-5 h-5 text-gray-400" />
          )}
        </div>

        <CardContent className="p-6">
          <div id={`level-content-${level.level}`} className="space-y-4">
            {/* Level Header */}
            <div className="flex items-center space-x-4">
              <div
                id={`level-icon-${level.level}`}
                className={`
                  w-16 h-16 rounded-full flex items-center justify-center text-2xl
                  ${isCurrentLevel ? 'bg-blue-100' : isUnlocked ? level.color.includes('yellow') ? 'bg-yellow-100' : 'bg-purple-100' : 'bg-gray-100'}
                  border-2 ${isCurrentLevel ? 'border-blue-300' : 'border-gray-200'}
                `}
                style={{ backgroundColor: isUnlocked ? level.color : undefined }}
              >
                <span>{level.icon}</span>
              </div>

              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h3
                    id={`level-title-${level.level}`}
                    className={`text-lg font-bold ${
                      isCurrentLevel ? 'text-blue-900' : 'text-gray-900'
                    }`}
                  >
                    Level {level.level}
                  </h3>
                  {isCurrentLevel && (
                    <Badge className="bg-blue-500 text-white text-xs">
                      Current
                    </Badge>
                  )}
                </div>
                
                <h4
                  id={`level-name-${level.level}`}
                  className={`font-semibold ${
                    isCurrentLevel ? 'text-blue-800' : 'text-gray-700'
                  }`}
                >
                  {level.title}
                </h4>
                
                <p
                  id={`level-description-${level.level}`}
                  className="text-sm text-gray-600 mt-1"
                >
                  {level.description}
                </p>
              </div>
            </div>

            {/* Points Requirement */}
            <div id={`level-points-${level.level}`} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Points Required</span>
                <span className="font-medium">
                  {level.pointsRequired.toLocaleString()}
                </span>
              </div>
              
              {level.pointsToNext > 0 && (
                <div className="text-xs text-gray-500">
                  Next level: {level.pointsToNext.toLocaleString()} points
                </div>
              )}
            </div>

            {/* Benefits Preview */}
            {level.benefits.length > 0 && (
              <div id={`level-benefits-${level.level}`} className="space-y-2">
                <h5 className="text-sm font-medium text-gray-700">Benefits</h5>
                <div className="flex flex-wrap gap-1">
                  {level.benefits.slice(0, 3).map((benefit, index) => {
                    const config = benefitTypeConfig[benefit.type];
                    const Icon = config.icon;
                    
                    return (
                      <Badge
                        key={index}
                        variant="outline"
                        className={`${config.bgColor} ${config.color} text-xs`}
                      >
                        <Icon className="w-3 h-3 mr-1" />
                        {config.label}
                      </Badge>
                    );
                  })}
                  {level.benefits.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{level.benefits.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function CurrentLevelProgress({ 
  userProgress, 
  currentLevel, 
  nextLevel 
}: {
  userProgress: UserProgress;
  currentLevel: Level;
  nextLevel?: Level;
}) {
  const pointsInCurrentLevel = userProgress.totalPoints - currentLevel.pointsRequired;
  const pointsForNextLevel = nextLevel ? nextLevel.pointsRequired - currentLevel.pointsRequired : 0;
  const progress = nextLevel ? (pointsInCurrentLevel / pointsForNextLevel) * 100 : 100;

  return (
    <Card id="current-level-progress">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <span>Level Progress</span>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Current Level Display */}
        <div className="text-center space-y-2">
          <div className="text-4xl font-bold text-blue-600">
            {userProgress.level}
          </div>
          <div className="text-lg font-semibold text-gray-900">
            {currentLevel.title}
          </div>
          <div className="text-sm text-gray-600">
            {currentLevel.description}
          </div>
        </div>

        {/* Progress Bar */}
        {nextLevel && (
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Progress to Level {nextLevel.level}</span>
              <span className="font-medium">{Math.round(progress)}%</span>
            </div>
            
            <Progress value={progress} className="h-4" />
            
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">
                {pointsInCurrentLevel.toLocaleString()} points in level
              </span>
              <span className="text-gray-600">
                {(pointsForNextLevel - pointsInCurrentLevel).toLocaleString()} to next
              </span>
            </div>
          </div>
        )}

        {/* Current Benefits */}
        {currentLevel.benefits.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Current Benefits</h4>
            <div className="space-y-2">
              {currentLevel.benefits.map((benefit, index) => {
                const config = benefitTypeConfig[benefit.type];
                const Icon = config.icon;
                
                return (
                  <div
                    key={index}
                    className={`flex items-center space-x-3 p-3 rounded-lg border ${config.bgColor}`}
                  >
                    <Icon className={`w-5 h-5 ${config.color}`} />
                    <div>
                      <div className="font-medium text-sm">{benefit.description}</div>
                      <div className="text-xs text-gray-600">{config.label}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Next Level Preview */}
        {nextLevel && (
          <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-blue-900">Next Level: {nextLevel.title}</h4>
              <ChevronRight className="w-5 h-5 text-blue-600" />
            </div>
            
            <div className="space-y-2">
              <div className="text-sm text-blue-800">
                Unlock at {nextLevel.pointsRequired.toLocaleString()} points
              </div>
              
              {nextLevel.benefits.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {nextLevel.benefits.slice(0, 2).map((benefit, index) => {
                    const config = benefitTypeConfig[benefit.type];
                    return (
                      <Badge
                        key={index}
                        variant="outline"
                        className="bg-blue-50 text-blue-700 border-blue-200 text-xs"
                      >
                        {benefit.description}
                      </Badge>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function LevelProgression({
  userProgress,
  levels,
  onViewAllLevels,
  onViewBenefits,
}: LevelProgressionProps) {
  const currentLevel = levels.find(l => l.level === userProgress.level) || levels[0];
  const nextLevel = levels.find(l => l.level === userProgress.level + 1);
  const nearbyLevels = levels.slice(
    Math.max(0, userProgress.level - 2),
    Math.min(levels.length, userProgress.level + 3)
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  return (
    <div id="level-progression" className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Crown className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <span>Level Progression</span>
                <p className="text-sm font-normal text-gray-600 mt-1">
                  Advance through levels to unlock exclusive benefits and features
                </p>
              </div>
            </div>
            
            <Button variant="outline" onClick={onViewAllLevels}>
              View All Levels
            </Button>
          </CardTitle>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Current Level Progress */}
        <div className="lg:col-span-1">
          <CurrentLevelProgress
            userProgress={userProgress}
            currentLevel={currentLevel}
            nextLevel={nextLevel}
          />
        </div>

        {/* Level Cards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Nearby Levels */}
          <Card>
            <CardHeader>
              <CardTitle>Your Level Journey</CardTitle>
            </CardHeader>
            
            <CardContent>
              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 md:grid-cols-2 gap-4"
              >
                {nearbyLevels.map(level => (
                  <LevelCard
                    key={level.level}
                    level={level}
                    isCurrentLevel={level.level === userProgress.level}
                    isUnlocked={level.level <= userProgress.level}
                    onClick={() => onViewBenefits(level)}
                  />
                ))}
              </motion.div>
            </CardContent>
          </Card>

          {/* Level Statistics */}
          <Card>
            <CardHeader>
              <CardTitle>Level Statistics</CardTitle>
            </CardHeader>
            
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {userProgress.level}
                  </div>
                  <div className="text-sm text-gray-600">Current Level</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {userProgress.totalPoints.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">Total Points</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {levels.filter(l => l.level <= userProgress.level).reduce(
                      (total, level) => total + level.benefits.length, 0
                    )}
                  </div>
                  <div className="text-sm text-gray-600">Active Benefits</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {Math.round(((userProgress.level - 1) / (levels.length - 1)) * 100)}%
                  </div>
                  <div className="text-sm text-gray-600">Progress</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Upcoming Milestones */}
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Milestones</CardTitle>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-3">
                {levels
                  .filter(l => l.level > userProgress.level)
                  .slice(0, 3)
                  .map(level => {
                    const pointsNeeded = level.pointsRequired - userProgress.totalPoints;
                    
                    return (
                      <div
                        key={level.level}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                        onClick={() => onViewBenefits(level)}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="text-lg">{level.icon}</div>
                          <div>
                            <div className="font-medium">Level {level.level}: {level.title}</div>
                            <div className="text-sm text-gray-600">
                              {level.benefits.length} new benefit{level.benefits.length !== 1 ? 's' : ''}
                            </div>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className="font-semibold text-blue-600">
                            {pointsNeeded.toLocaleString()}
                          </div>
                          <div className="text-xs text-gray-600">points needed</div>
                        </div>
                      </div>
                    );
                  })
                }
                
                {levels.filter(l => l.level > userProgress.level).length === 0 && (
                  <div className="text-center py-8">
                    <Crown className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Maximum Level Reached!
                    </h3>
                    <p className="text-gray-600">
                      Congratulations on reaching the highest level. Keep earning points for other rewards!
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// All Levels Modal Component
interface AllLevelsModalProps {
  levels: Level[];
  currentLevel: number;
  isOpen: boolean;
  onClose: () => void;
  onSelectLevel: (level: Level) => void;
}

export function AllLevelsModal({
  levels,
  currentLevel,
  isOpen,
  onClose,
  onSelectLevel,
}: AllLevelsModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-white rounded-lg max-w-6xl w-full max-h-screen overflow-hidden"
      >
        <Card className="h-full">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                <Crown className="w-6 h-6 text-purple-600" />
                <span>All Levels</span>
              </CardTitle>
              <Button variant="ghost" onClick={onClose}>
                ✕
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-6 overflow-y-auto max-h-[calc(100vh-200px)]">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {levels.map(level => (
                <LevelCard
                  key={level.level}
                  level={level}
                  isCurrentLevel={level.level === currentLevel}
                  isUnlocked={level.level <= currentLevel}
                  onClick={() => onSelectLevel(level)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

// Level Benefits Detail Component
interface LevelBenefitsDetailProps {
  level: Level;
  isOpen: boolean;
  onClose: () => void;
}

export function LevelBenefitsDetail({
  level,
  isOpen,
  onClose,
}: LevelBenefitsDetailProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto"
      >
        <Card>
          <CardHeader className="bg-gradient-to-r from-purple-50 to-blue-50 border-b">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="text-3xl">{level.icon}</div>
                <div>
                  <CardTitle className="text-xl">
                    Level {level.level}: {level.title}
                  </CardTitle>
                  <p className="text-gray-600 mt-1">{level.description}</p>
                </div>
              </div>
              <Button variant="ghost" onClick={onClose}>
                ✕
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-6 space-y-6">
            <div>
              <h3 className="font-semibold text-lg mb-2">Requirements</h3>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {level.pointsRequired.toLocaleString()} points
                </div>
                <div className="text-sm text-gray-600">Total points needed</div>
              </div>
            </div>

            {level.benefits.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-3">Benefits & Perks</h3>
                <div className="space-y-3">
                  {level.benefits.map((benefit, index) => {
                    const config = benefitTypeConfig[benefit.type];
                    const Icon = config.icon;
                    
                    return (
                      <div
                        key={index}
                        className={`flex items-start space-x-4 p-4 rounded-lg border ${config.bgColor}`}
                      >
                        <Icon className={`w-6 h-6 ${config.color} mt-1`} />
                        <div className="flex-1">
                          <div className="font-medium">{benefit.description}</div>
                          <div className="text-sm text-gray-600 mt-1">
                            {config.label}
                            {benefit.value && benefit.value !== 1 && (
                              <span className="ml-1">
                                ({benefit.value > 1 ? `${benefit.value}x` : `${benefit.value * 100}%`})
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="text-center">
              <Button onClick={onClose} className="px-8">
                Close
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}