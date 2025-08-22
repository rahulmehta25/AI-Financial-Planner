'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, 
  Target, 
  Calendar, 
  Clock, 
  Users, 
  Star, 
  CheckCircle, 
  AlertCircle,
  Play,
  Pause,
  Flag,
  Gift,
  PiggyBank,
  BarChart3,
  TrendingUp,
  CreditCard,
  Shield,
  BookOpen,
  Zap
} from 'lucide-react';
import { Challenge, ChallengeCategory, ChallengeRequirement, ChallengeReward } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';

interface ChallengeSystemProps {
  availableChallenges: Challenge[];
  activeChallenges: Challenge[];
  completedChallenges: Challenge[];
  onJoinChallenge: (challengeId: string) => void;
  onLeaveChallenge: (challengeId: string) => void;
  onViewChallenge: (challenge: Challenge) => void;
}

const challengeCategoryConfig: Record<ChallengeCategory, {
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  description: string;
}> = {
  savings: {
    icon: PiggyBank,
    color: 'from-green-400 to-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    description: 'Build your savings habits',
  },
  budgeting: {
    icon: BarChart3,
    color: 'from-blue-400 to-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
    description: 'Master your budget management',
  },
  investment: {
    icon: TrendingUp,
    color: 'from-purple-400 to-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-800',
    description: 'Grow your investment portfolio',
  },
  debt_payoff: {
    icon: CreditCard,
    color: 'from-red-400 to-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    description: 'Eliminate debt faster',
  },
  emergency_fund: {
    icon: Shield,
    color: 'from-orange-400 to-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-800',
    description: 'Build financial security',
  },
  education: {
    icon: BookOpen,
    color: 'from-indigo-400 to-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    textColor: 'text-indigo-800',
    description: 'Expand financial knowledge',
  },
  planning: {
    icon: Target,
    color: 'from-pink-400 to-pink-600',
    bgColor: 'bg-pink-50',
    borderColor: 'border-pink-200',
    textColor: 'text-pink-800',
    description: 'Improve financial planning',
  },
};

const difficultyConfig = {
  beginner: {
    color: 'bg-green-100 text-green-800 border-green-200',
    icon: '🌱',
  },
  intermediate: {
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    icon: '🌿',
  },
  advanced: {
    color: 'bg-purple-100 text-purple-800 border-purple-200',
    icon: '🌳',
  },
  expert: {
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: '👑',
  },
};

function ChallengeCard({ 
  challenge, 
  variant = 'available',
  onJoin,
  onLeave,
  onView 
}: { 
  challenge: Challenge;
  variant?: 'available' | 'active' | 'completed';
  onJoin?: (challengeId: string) => void;
  onLeave?: (challengeId: string) => void;
  onView?: (challenge: Challenge) => void;
}) {
  const config = challengeCategoryConfig[challenge.category];
  const Icon = config.icon;
  const difficultyConf = difficultyConfig[challenge.difficulty];

  const daysRemaining = challenge.endDate 
    ? Math.max(0, Math.ceil((new Date(challenge.endDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)))
    : challenge.duration;

  const isExpired = challenge.endDate && new Date() > new Date(challenge.endDate);
  const isCompleted = challenge.isCompleted;

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

  return (
    <motion.div
      id={`challenge-card-${challenge.id}`}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      className="cursor-pointer"
      onClick={() => onView?.(challenge)}
    >
      <Card
        className={`
          relative overflow-hidden transition-all duration-300 hover:shadow-md
          ${config.bgColor} ${config.borderColor}
          ${isCompleted ? 'ring-2 ring-green-300 ring-opacity-50' : ''}
          ${isExpired && !isCompleted ? 'ring-2 ring-red-300 ring-opacity-50' : ''}
        `}
      >
        {/* Status Indicators */}
        <div
          id={`challenge-status-${challenge.id}`}
          className="absolute top-3 right-3 z-10"
        >
          {isCompleted ? (
            <CheckCircle className="w-6 h-6 text-green-500" />
          ) : isExpired ? (
            <AlertCircle className="w-6 h-6 text-red-500" />
          ) : variant === 'active' ? (
            <Play className="w-6 h-6 text-blue-500" />
          ) : null}
        </div>

        <CardContent className="p-6">
          <div id={`challenge-content-${challenge.id}`} className="space-y-4">
            {/* Header */}
            <div className="flex items-start space-x-3">
              <div
                id={`challenge-icon-${challenge.id}`}
                className={`
                  p-3 rounded-full ${config.bgColor} ${config.borderColor} border
                  ${isCompleted ? 'bg-green-100 border-green-300' : ''}
                `}
              >
                <Icon
                  className={`w-6 h-6 ${
                    isCompleted ? 'text-green-600' : config.textColor
                  }`}
                />
              </div>

              <div className="flex-1 min-w-0">
                <h3
                  id={`challenge-title-${challenge.id}`}
                  className="font-semibold text-lg text-gray-900"
                >
                  {challenge.title}
                </h3>
                <p
                  id={`challenge-description-${challenge.id}`}
                  className="text-sm text-gray-600 mt-1"
                >
                  {challenge.description}
                </p>
              </div>
            </div>

            {/* Badges */}
            <div id={`challenge-badges-${challenge.id}`} className="flex flex-wrap gap-2">
              <Badge
                variant="outline"
                className={`${difficultyConf.color} capitalize`}
              >
                {difficultyConf.icon} {challenge.difficulty}
              </Badge>

              <Badge
                variant="outline"
                className={`${config.bgColor} ${config.textColor} ${config.borderColor} capitalize`}
              >
                {challenge.category.replace('_', ' ')}
              </Badge>

              <Badge variant="outline" className="bg-gray-50 text-gray-700">
                {challenge.duration} days
              </Badge>

              {challenge.maxParticipants && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  <Users className="w-3 h-3 mr-1" />
                  {challenge.participants}/{challenge.maxParticipants}
                </Badge>
              )}
            </div>

            {/* Progress (for active challenges) */}
            {variant === 'active' && (
              <div id={`challenge-progress-${challenge.id}`} className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">Progress</span>
                  <span className="text-sm text-gray-600">{Math.round(challenge.progress)}%</span>
                </div>
                <Progress value={challenge.progress} className="h-3" />

                {/* Requirements Progress */}
                <div className="space-y-2">
                  {challenge.requirements.map((req, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">{req.description}</span>
                      <span className="font-medium">
                        {req.current}/{req.target}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Rewards */}
            <div id={`challenge-rewards-${challenge.id}`} className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 flex items-center space-x-1">
                <Gift className="w-4 h-4" />
                <span>Rewards</span>
              </h4>
              <div className="flex flex-wrap gap-2">
                {challenge.rewards.map((reward, index) => (
                  <Badge key={index} className="bg-yellow-100 text-yellow-800 border-yellow-200">
                    {reward.description}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Timeline */}
            <div id={`challenge-timeline-${challenge.id}`} className="flex items-center space-x-4 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <Calendar className="w-4 h-4" />
                <span>
                  {challenge.startDate ? 
                    `Started ${new Date(challenge.startDate).toLocaleDateString()}` :
                    'Available to start'
                  }
                </span>
              </div>
              
              {variant === 'active' && (
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4" />
                  <span className={isExpired ? 'text-red-600 font-medium' : ''}>
                    {isExpired ? 'Expired' : `${daysRemaining} days left`}
                  </span>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div id={`challenge-actions-${challenge.id}`} className="flex space-x-2 pt-2">
              {variant === 'available' && (
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    onJoin?.(challenge.id);
                  }}
                  className="flex-1"
                  disabled={challenge.maxParticipants ? challenge.participants >= challenge.maxParticipants : false}
                >
                  Join Challenge
                </Button>
              )}

              {variant === 'active' && !isCompleted && (
                <Button
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    onLeave?.(challenge.id);
                  }}
                  className="flex-1"
                >
                  Leave Challenge
                </Button>
              )}

              {isCompleted && (
                <div className="flex-1 text-center">
                  <Badge className="bg-green-500 text-white">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Completed
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function ChallengeSystem({
  availableChallenges,
  activeChallenges,
  completedChallenges,
  onJoinChallenge,
  onLeaveChallenge,
  onViewChallenge,
}: ChallengeSystemProps) {
  const [activeTab, setActiveTab] = React.useState<'available' | 'active' | 'completed'>('available');
  const [selectedCategory, setSelectedCategory] = React.useState<ChallengeCategory | 'all'>('all');

  const filterChallengesByCategory = (challenges: Challenge[]) => {
    if (selectedCategory === 'all') return challenges;
    return challenges.filter(c => c.category === selectedCategory);
  };

  const filteredAvailable = filterChallengesByCategory(availableChallenges);
  const filteredActive = filterChallengesByCategory(activeChallenges);
  const filteredCompleted = filterChallengesByCategory(completedChallenges);

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
    <div id="challenge-system" className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Trophy className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <span>Financial Challenges</span>
              <p className="text-sm font-normal text-gray-600 mt-1">
                Complete challenges to earn rewards and build better financial habits
              </p>
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Challenge Stats */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{activeChallenges.length}</div>
              <div className="text-sm text-gray-600">Active</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{completedChallenges.length}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{availableChallenges.length}</div>
              <div className="text-sm text-gray-600">Available</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {completedChallenges.reduce((total, challenge) => 
                  total + challenge.rewards.filter(r => r.type === 'points').reduce((pts, r) => pts + r.value, 0), 0
                )}
              </div>
              <div className="text-sm text-gray-600">Points Earned</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={selectedCategory === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory('all')}
            >
              All Categories
            </Button>
            
            {Object.entries(challengeCategoryConfig).map(([category, config]) => {
              const Icon = config.icon;
              return (
                <Button
                  key={category}
                  variant={selectedCategory === category ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory(category as ChallengeCategory)}
                  className="flex items-center space-x-1"
                >
                  <Icon className="w-4 h-4" />
                  <span className="capitalize">{category.replace('_', ' ')}</span>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Tab Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('available')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'available'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Available ({filteredAvailable.length})
            </button>
            
            <button
              onClick={() => setActiveTab('active')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'active'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Active ({filteredActive.length})
            </button>
            
            <button
              onClick={() => setActiveTab('completed')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'completed'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Completed ({filteredCompleted.length})
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Challenge Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {activeTab === 'available' && 
          filteredAvailable.map(challenge => (
            <ChallengeCard
              key={challenge.id}
              challenge={challenge}
              variant="available"
              onJoin={onJoinChallenge}
              onView={onViewChallenge}
            />
          ))
        }

        {activeTab === 'active' && 
          filteredActive.map(challenge => (
            <ChallengeCard
              key={challenge.id}
              challenge={challenge}
              variant="active"
              onLeave={onLeaveChallenge}
              onView={onViewChallenge}
            />
          ))
        }

        {activeTab === 'completed' && 
          filteredCompleted.map(challenge => (
            <ChallengeCard
              key={challenge.id}
              challenge={challenge}
              variant="completed"
              onView={onViewChallenge}
            />
          ))
        }
      </motion.div>

      {/* Empty State */}
      {((activeTab === 'available' && filteredAvailable.length === 0) ||
        (activeTab === 'active' && filteredActive.length === 0) ||
        (activeTab === 'completed' && filteredCompleted.length === 0)) && (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="space-y-4">
              {activeTab === 'available' && (
                <>
                  <Target className="w-12 h-12 text-gray-400 mx-auto" />
                  <h3 className="text-lg font-medium text-gray-900">No Available Challenges</h3>
                  <p className="text-gray-600">
                    {selectedCategory === 'all' 
                      ? 'All challenges are currently in progress or completed.'
                      : `No ${selectedCategory.replace('_', ' ')} challenges available right now.`
                    }
                  </p>
                </>
              )}

              {activeTab === 'active' && (
                <>
                  <Play className="w-12 h-12 text-gray-400 mx-auto" />
                  <h3 className="text-lg font-medium text-gray-900">No Active Challenges</h3>
                  <p className="text-gray-600">
                    Join some challenges to start building better financial habits!
                  </p>
                </>
              )}

              {activeTab === 'completed' && (
                <>
                  <Trophy className="w-12 h-12 text-gray-400 mx-auto" />
                  <h3 className="text-lg font-medium text-gray-900">No Completed Challenges</h3>
                  <p className="text-gray-600">
                    Complete challenges to see them here and earn rewards!
                  </p>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Challenge Detail Modal Component
interface ChallengeDetailProps {
  challenge: Challenge;
  isOpen: boolean;
  onClose: () => void;
  onJoin?: (challengeId: string) => void;
  onLeave?: (challengeId: string) => void;
}

export function ChallengeDetail({
  challenge,
  isOpen,
  onClose,
  onJoin,
  onLeave,
}: ChallengeDetailProps) {
  if (!isOpen) return null;

  const config = challengeCategoryConfig[challenge.category];
  const Icon = config.icon;
  const difficultyConf = difficultyConfig[challenge.difficulty];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto"
      >
        <Card>
          <CardHeader className={`${config.bgColor} ${config.borderColor} border-b`}>
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <Icon className={`w-8 h-8 ${config.textColor}`} />
                <div>
                  <CardTitle className="text-xl">{challenge.title}</CardTitle>
                  <div className="flex items-center space-x-2 mt-2">
                    <Badge variant="outline" className={difficultyConf.color}>
                      {difficultyConf.icon} {challenge.difficulty}
                    </Badge>
                    <Badge variant="outline" className={`${config.bgColor} ${config.textColor}`}>
                      {challenge.category.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>
              </div>
              <Button variant="ghost" onClick={onClose}>
                ✕
              </Button>
            </div>
          </CardHeader>

          <CardContent className="p-6 space-y-6">
            <div>
              <h3 className="font-semibold text-lg mb-2">Description</h3>
              <p className="text-gray-600">{challenge.description}</p>
            </div>

            <div>
              <h3 className="font-semibold text-lg mb-3">Requirements</h3>
              <div className="space-y-3">
                {challenge.requirements.map((req, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span>{req.description}</span>
                    <div className="text-right">
                      <div className="font-medium">{req.current}/{req.target}</div>
                      <Progress value={(req.current / req.target) * 100} className="w-20 h-2 mt-1" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-lg mb-3">Rewards</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {challenge.rewards.map((reward, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <Gift className="w-5 h-5 text-yellow-600" />
                    <div>
                      <div className="font-medium">{reward.description}</div>
                      <div className="text-sm text-gray-600 capitalize">{reward.type}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900">Duration</h4>
                <p className="text-2xl font-bold text-blue-600">{challenge.duration} days</p>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900">Participants</h4>
                <p className="text-2xl font-bold text-green-600">
                  {challenge.participants}
                  {challenge.maxParticipants && `/${challenge.maxParticipants}`}
                </p>
              </div>
            </div>

            <div className="flex space-x-3">
              {!challenge.isActive && onJoin && (
                <Button
                  onClick={() => onJoin(challenge.id)}
                  className="flex-1"
                  disabled={challenge.maxParticipants ? challenge.participants >= challenge.maxParticipants : false}
                >
                  Join Challenge
                </Button>
              )}
              
              {challenge.isActive && onLeave && !challenge.isCompleted && (
                <Button
                  variant="outline"
                  onClick={() => onLeave(challenge.id)}
                  className="flex-1"
                >
                  Leave Challenge
                </Button>
              )}
              
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}