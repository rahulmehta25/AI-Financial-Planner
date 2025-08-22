'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Star, 
  Gift, 
  ShoppingCart, 
  Coins, 
  Crown, 
  Zap, 
  Palette, 
  BookOpen, 
  Settings,
  Check,
  Clock,
  AlertCircle,
  Sparkles,
  TrendingUp,
  Users,
  Calendar,
  Coffee,
  Smartphone,
  Headphones
} from 'lucide-react';
import { 
  RewardPoint, 
  RewardRedemption, 
  RedemptionType, 
  RedemptionCategory, 
  PointSource 
} from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

interface RewardSystemProps {
  availablePoints: number;
  totalPointsEarned: number;
  recentPoints: RewardPoint[];
  availableRedemptions: RewardRedemption[];
  onRedeemReward: (redemptionId: string) => void;
  onViewHistory: () => void;
}

const pointSourceConfig: Record<PointSource, {
  icon: React.ComponentType<any>;
  color: string;
  label: string;
}> = {
  achievement_unlock: {
    icon: Star,
    color: 'text-yellow-600',
    label: 'Achievement',
  },
  challenge_completion: {
    icon: Gift,
    color: 'text-purple-600',
    label: 'Challenge',
  },
  streak_bonus: {
    icon: Zap,
    color: 'text-orange-600',
    label: 'Streak Bonus',
  },
  milestone_reached: {
    icon: TrendingUp,
    color: 'text-green-600',
    label: 'Milestone',
  },
  form_completion: {
    icon: Check,
    color: 'text-blue-600',
    label: 'Form Complete',
  },
  daily_login: {
    icon: Calendar,
    color: 'text-indigo-600',
    label: 'Daily Login',
  },
  referral_bonus: {
    icon: Users,
    color: 'text-pink-600',
    label: 'Referral',
  },
};

const redemptionTypeConfig: Record<RedemptionType, {
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  label: string;
}> = {
  discount_code: {
    icon: Gift,
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    label: 'Discount Code',
  },
  feature_unlock: {
    icon: Crown,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    label: 'Premium Feature',
  },
  consultation_credit: {
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    label: 'Consultation',
  },
  premium_trial: {
    icon: Sparkles,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 border-yellow-200',
    label: 'Premium Trial',
  },
  educational_content: {
    icon: BookOpen,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50 border-indigo-200',
    label: 'Educational Content',
  },
  custom_theme: {
    icon: Palette,
    color: 'text-pink-600',
    bgColor: 'bg-pink-50 border-pink-200',
    label: 'Custom Theme',
  },
};

const categoryConfig: Record<RedemptionCategory, {
  icon: React.ComponentType<any>;
  label: string;
}> = {
  services: { icon: Users, label: 'Services' },
  features: { icon: Settings, label: 'Features' },
  education: { icon: BookOpen, label: 'Education' },
  customization: { icon: Palette, label: 'Customization' },
  bonuses: { icon: Gift, label: 'Bonuses' },
};

function PointsOverview({ 
  availablePoints, 
  totalPointsEarned, 
  recentPoints 
}: {
  availablePoints: number;
  totalPointsEarned: number;
  recentPoints: RewardPoint[];
}) {
  const todaysPoints = recentPoints
    .filter(p => new Date(p.earnedAt).toDateString() === new Date().toDateString())
    .reduce((sum, p) => sum + p.amount, 0);

  const weeklyPoints = recentPoints
    .filter(p => {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return new Date(p.earnedAt) > weekAgo;
    })
    .reduce((sum, p) => sum + p.amount, 0);

  return (
    <Card id="points-overview">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Coins className="w-5 h-5 text-yellow-600" />
          <span>Your Points</span>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Main Points Display */}
        <div className="text-center space-y-2">
          <div className="text-4xl font-bold text-yellow-600">
            {availablePoints.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Available Points</div>
          <div className="text-xs text-gray-500">
            {totalPointsEarned.toLocaleString()} earned total
          </div>
        </div>

        {/* Points Breakdown */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-xl font-bold text-blue-600">{todaysPoints}</div>
            <div className="text-sm text-blue-700">Today</div>
          </div>
          
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-xl font-bold text-green-600">{weeklyPoints}</div>
            <div className="text-sm text-green-700">This Week</div>
          </div>
        </div>

        {/* Recent Points Activity */}
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">Recent Activity</h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {recentPoints.slice(0, 5).map(point => {
              const config = pointSourceConfig[point.source];
              const Icon = config.icon;
              
              return (
                <div key={point.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Icon className={`w-4 h-4 ${config.color}`} />
                    <div>
                      <div className="text-sm font-medium">{point.description}</div>
                      <div className="text-xs text-gray-500">
                        {new Date(point.earnedAt).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm font-bold text-green-600">
                    +{point.amount}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function RewardCard({ 
  redemption, 
  availablePoints, 
  onRedeem 
}: {
  redemption: RewardRedemption;
  availablePoints: number;
  onRedeem: (redemptionId: string) => void;
}) {
  const typeConfig = redemptionTypeConfig[redemption.type];
  const Icon = typeConfig.icon;
  const canAfford = availablePoints >= redemption.cost;
  const isExpired = redemption.expiresAt && new Date() > new Date(redemption.expiresAt);

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
      scale: canAfford ? 1.02 : 1,
      transition: { duration: 0.2 },
    },
  };

  return (
    <motion.div
      id={`reward-card-${redemption.id}`}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
    >
      <Card
        className={`
          relative overflow-hidden transition-all duration-300
          ${typeConfig.bgColor}
          ${canAfford ? 'hover:shadow-md cursor-pointer' : 'opacity-60'}
          ${isExpired ? 'ring-2 ring-red-300' : ''}
        `}
      >
        {/* Availability Badge */}
        <div className="absolute top-3 right-3">
          {isExpired ? (
            <Badge variant="destructive" className="text-xs">
              Expired
            </Badge>
          ) : !redemption.isAvailable ? (
            <Badge className="bg-gray-500 text-white text-xs">
              Unavailable
            </Badge>
          ) : canAfford ? (
            <Badge className="bg-green-500 text-white text-xs">
              Available
            </Badge>
          ) : (
            <Badge className="bg-orange-500 text-white text-xs">
              Need More Points
            </Badge>
          )}
        </div>

        <CardContent className="p-6">
          <div className="space-y-4">
            {/* Header */}
            <div className="flex items-start space-x-3">
              <div className={`p-3 rounded-full ${typeConfig.bgColor} border`}>
                <Icon className={`w-6 h-6 ${typeConfig.color}`} />
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-lg text-gray-900">{redemption.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{redemption.description}</p>
              </div>
            </div>

            {/* Cost */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Coins className="w-5 h-5 text-yellow-600" />
                <span className="text-2xl font-bold text-gray-900">
                  {redemption.cost.toLocaleString()}
                </span>
                <span className="text-sm text-gray-600">points</span>
              </div>

              {redemption.value && (
                <div className="text-right">
                  <div className="text-sm text-gray-600">Value</div>
                  <div className="font-semibold">${redemption.value}</div>
                </div>
              )}
            </div>

            {/* Category */}
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className={`${typeConfig.bgColor} ${typeConfig.color}`}>
                {typeConfig.label}
              </Badge>
              
              <Badge variant="outline" className="capitalize">
                {redemption.category.replace('_', ' ')}
              </Badge>
            </div>

            {/* Expiration */}
            {redemption.expiresAt && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                <span>
                  Expires {new Date(redemption.expiresAt).toLocaleDateString()}
                </span>
              </div>
            )}

            {/* Action Button */}
            <Button
              onClick={() => onRedeem(redemption.id)}
              disabled={!canAfford || !redemption.isAvailable || isExpired}
              className="w-full"
              variant={canAfford ? 'default' : 'outline'}
            >
              {isExpired ? 'Expired' : 
               !redemption.isAvailable ? 'Unavailable' :
               !canAfford ? `Need ${(redemption.cost - availablePoints).toLocaleString()} more points` :
               'Redeem Now'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function RewardSystem({
  availablePoints,
  totalPointsEarned,
  recentPoints,
  availableRedemptions,
  onRedeemReward,
  onViewHistory,
}: RewardSystemProps) {
  const [selectedCategory, setSelectedCategory] = React.useState<RedemptionCategory | 'all'>('all');
  const [sortBy, setSortBy] = React.useState<'cost' | 'value' | 'expiry'>('cost');

  const filteredRedemptions = availableRedemptions.filter(redemption => {
    if (selectedCategory === 'all') return true;
    return redemption.category === selectedCategory;
  });

  const sortedRedemptions = [...filteredRedemptions].sort((a, b) => {
    switch (sortBy) {
      case 'cost':
        return a.cost - b.cost;
      case 'value':
        return (b.value || 0) - (a.value || 0);
      case 'expiry':
        if (!a.expiresAt && !b.expiresAt) return 0;
        if (!a.expiresAt) return 1;
        if (!b.expiresAt) return -1;
        return new Date(a.expiresAt).getTime() - new Date(b.expiresAt).getTime();
      default:
        return 0;
    }
  });

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
    <div id="reward-system" className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Gift className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <span>Reward Store</span>
                <p className="text-sm font-normal text-gray-600 mt-1">
                  Redeem your points for exclusive rewards and benefits
                </p>
              </div>
            </div>
            
            <Button variant="outline" onClick={onViewHistory}>
              View History
            </Button>
          </CardTitle>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Points Overview */}
        <div className="lg:col-span-1">
          <PointsOverview
            availablePoints={availablePoints}
            totalPointsEarned={totalPointsEarned}
            recentPoints={recentPoints}
          />
        </div>

        {/* Filters and Rewards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Filters */}
          <Card>
            <CardContent className="p-4 space-y-4">
              {/* Category Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Category</label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={selectedCategory === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory('all')}
                  >
                    All
                  </Button>
                  
                  {Object.entries(categoryConfig).map(([category, config]) => {
                    const Icon = config.icon;
                    return (
                      <Button
                        key={category}
                        variant={selectedCategory === category ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedCategory(category as RedemptionCategory)}
                        className="flex items-center space-x-1"
                      >
                        <Icon className="w-4 h-4" />
                        <span>{config.label}</span>
                      </Button>
                    );
                  })}
                </div>
              </div>

              {/* Sort Filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Sort by</label>
                <div className="flex space-x-2">
                  <Button
                    variant={sortBy === 'cost' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSortBy('cost')}
                  >
                    Cost (Low to High)
                  </Button>
                  <Button
                    variant={sortBy === 'value' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSortBy('value')}
                  >
                    Value (High to Low)
                  </Button>
                  <Button
                    variant={sortBy === 'expiry' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSortBy('expiry')}
                  >
                    Expiring Soon
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Rewards Grid */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            {sortedRedemptions.map(redemption => (
              <RewardCard
                key={redemption.id}
                redemption={redemption}
                availablePoints={availablePoints}
                onRedeem={onRedeemReward}
              />
            ))}
          </motion.div>

          {/* Empty State */}
          {sortedRedemptions.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center">
                <div className="space-y-4">
                  <Gift className="w-12 h-12 text-gray-400 mx-auto" />
                  <h3 className="text-lg font-medium text-gray-900">No Rewards Available</h3>
                  <p className="text-gray-600">
                    {selectedCategory === 'all'
                      ? 'No rewards are currently available. Check back later!'
                      : `No ${selectedCategory} rewards available right now.`
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Points Earning Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-yellow-600" />
            <span>Earn More Points</span>
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
              <Check className="w-6 h-6 text-blue-600" />
              <div>
                <div className="font-medium">Complete Forms</div>
                <div className="text-sm text-gray-600">100 points per section</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
              <div>
                <div className="font-medium">Reach Milestones</div>
                <div className="text-sm text-gray-600">200+ points each</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
              <Gift className="w-6 h-6 text-purple-600" />
              <div>
                <div className="font-medium">Complete Challenges</div>
                <div className="text-sm text-gray-600">500+ points each</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg">
              <Zap className="w-6 h-6 text-orange-600" />
              <div>
                <div className="font-medium">Maintain Streaks</div>
                <div className="text-sm text-gray-600">Bonus multipliers</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-indigo-50 rounded-lg">
              <Calendar className="w-6 h-6 text-indigo-600" />
              <div>
                <div className="font-medium">Daily Login</div>
                <div className="text-sm text-gray-600">10 points daily</div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-3 bg-pink-50 rounded-lg">
              <Users className="w-6 h-6 text-pink-600" />
              <div>
                <div className="font-medium">Refer Friends</div>
                <div className="text-sm text-gray-600">500 points per referral</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Points Progress Component
interface PointsProgressProps {
  currentPoints: number;
  nextRewardThreshold: number;
  nextRewardName: string;
}

export function PointsProgress({ 
  currentPoints, 
  nextRewardThreshold, 
  nextRewardName 
}: PointsProgressProps) {
  const progress = (currentPoints / nextRewardThreshold) * 100;
  const pointsNeeded = nextRewardThreshold - currentPoints;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Next Reward</h3>
            <Badge variant="outline">{nextRewardName}</Badge>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium">
                {currentPoints.toLocaleString()} / {nextRewardThreshold.toLocaleString()}
              </span>
            </div>
            <Progress value={Math.min(100, progress)} className="h-3" />
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {pointsNeeded > 0 ? pointsNeeded.toLocaleString() : 0}
            </div>
            <div className="text-sm text-gray-600">
              {pointsNeeded > 0 ? 'points needed' : 'Ready to redeem!'}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}