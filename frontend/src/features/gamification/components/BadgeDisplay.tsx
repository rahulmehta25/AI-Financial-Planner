'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Star, Crown, Award, Zap } from 'lucide-react';
import { Badge as BadgeType } from '../types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface BadgeDisplayProps {
  badge: BadgeType;
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
  animate?: boolean;
}

const rarityConfig = {
  common: {
    color: 'from-gray-400 to-gray-600',
    textColor: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-300',
    icon: Star,
  },
  rare: {
    color: 'from-blue-400 to-blue-600',
    textColor: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-300',
    icon: Award,
  },
  epic: {
    color: 'from-purple-400 to-purple-600',
    textColor: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-300',
    icon: Zap,
  },
  legendary: {
    color: 'from-yellow-400 to-orange-500',
    textColor: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-300',
    icon: Crown,
  },
};

const sizeConfig = {
  small: {
    badgeSize: 'w-12 h-12',
    iconSize: 'w-4 h-4',
    textSize: 'text-xs',
    titleSize: 'text-sm',
  },
  medium: {
    badgeSize: 'w-16 h-16',
    iconSize: 'w-6 h-6',
    textSize: 'text-sm',
    titleSize: 'text-base',
  },
  large: {
    badgeSize: 'w-24 h-24',
    iconSize: 'w-8 h-8',
    textSize: 'text-base',
    titleSize: 'text-lg',
  },
};

export default function BadgeDisplay({
  badge,
  size = 'medium',
  showDetails = true,
  animate = true,
}: BadgeDisplayProps) {
  const rarity = rarityConfig[badge.rarity];
  const sizeStyles = sizeConfig[size];
  const RarityIcon = rarity.icon;

  const isEarned = !!badge.earnedAt;

  const badgeVariants = {
    hidden: { scale: 0, opacity: 0 },
    visible: {
      scale: 1,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 260,
        damping: 20,
      },
    },
    hover: {
      scale: 1.05,
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
      id={`badge-display-${badge.id}`}
      variants={animate ? badgeVariants : undefined}
      initial={animate ? 'hidden' : undefined}
      animate={animate ? 'visible' : undefined}
      whileHover={animate ? 'hover' : undefined}
      className="flex flex-col items-center space-y-2"
    >
      {/* Badge Circle */}
      <div
        id={`badge-circle-${badge.id}`}
        className={`
          relative ${sizeStyles.badgeSize} rounded-full flex items-center justify-center
          ${isEarned ? rarity.bgColor : 'bg-gray-200'}
          ${isEarned ? rarity.borderColor : 'border-gray-300'}
          border-2 shadow-lg overflow-hidden
        `}
      >
        {/* Gradient Overlay for Earned Badges */}
        {isEarned && (
          <div
            className={`absolute inset-0 bg-gradient-to-br ${rarity.color} opacity-20 rounded-full`}
          />
        )}

        {/* Glow Effect for Legendary Badges */}
        {isEarned && badge.rarity === 'legendary' && (
          <motion.div
            variants={glowVariants}
            animate="glow"
            className="absolute inset-0 bg-gradient-to-br from-yellow-300 to-orange-400 opacity-30 rounded-full blur-sm"
          />
        )}

        {/* Badge Icon */}
        <div
          id={`badge-icon-${badge.id}`}
          className={`
            ${sizeStyles.iconSize} flex items-center justify-center
            ${isEarned ? rarity.textColor : 'text-gray-400'}
          `}
        >
          {isEarned ? (
            <span className={sizeStyles.textSize}>{badge.icon}</span>
          ) : (
            <RarityIcon className={sizeStyles.iconSize} />
          )}
        </div>

        {/* Rarity Indicator */}
        {isEarned && (
          <div
            id={`badge-rarity-indicator-${badge.id}`}
            className="absolute -top-1 -right-1"
          >
            <RarityIcon
              className={`w-4 h-4 ${rarity.textColor} drop-shadow-sm`}
            />
          </div>
        )}
      </div>

      {/* Badge Details */}
      {showDetails && (
        <div
          id={`badge-details-${badge.id}`}
          className="text-center space-y-1 max-w-24"
        >
          <h3
            id={`badge-name-${badge.id}`}
            className={`font-semibold ${sizeStyles.titleSize} ${
              isEarned ? 'text-gray-900' : 'text-gray-500'
            } truncate`}
          >
            {badge.name}
          </h3>

          {size !== 'small' && (
            <p
              id={`badge-description-${badge.id}`}
              className={`${sizeStyles.textSize} text-gray-600 line-clamp-2`}
            >
              {badge.description}
            </p>
          )}

          <Badge
            variant="outline"
            className={`${rarity.bgColor} ${rarity.textColor} ${rarity.borderColor} text-xs`}
          >
            {badge.rarity}
          </Badge>

          {isEarned && badge.earnedAt && (
            <p
              id={`badge-earned-date-${badge.id}`}
              className="text-xs text-gray-500"
            >
              Earned {new Date(badge.earnedAt).toLocaleDateString()}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}

// Badge Collection Component
interface BadgeCollectionProps {
  badges: BadgeType[];
  earnedBadges: BadgeType[];
  filter?: 'all' | 'earned' | 'available' | BadgeType['rarity'];
  layout?: 'grid' | 'carousel' | 'showcase';
  onBadgeClick?: (badge: BadgeType) => void;
}

export function BadgeCollection({
  badges,
  earnedBadges,
  filter = 'all',
  layout = 'grid',
  onBadgeClick,
}: BadgeCollectionProps) {
  const earnedBadgeIds = new Set(earnedBadges.map(b => b.id));

  const filteredBadges = badges.filter(badge => {
    const isEarned = earnedBadgeIds.has(badge.id);
    
    if (filter === 'all') return true;
    if (filter === 'earned') return isEarned;
    if (filter === 'available') return !isEarned;
    return badge.rarity === filter;
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

  if (layout === 'grid') {
    return (
      <motion.div
        id="badge-collection-grid"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6"
      >
        {filteredBadges.map(badge => {
          const earnedBadge = earnedBadges.find(b => b.id === badge.id);
          const displayBadge = earnedBadge || badge;

          return (
            <motion.div
              key={badge.id}
              className="cursor-pointer"
              onClick={() => onBadgeClick?.(displayBadge)}
            >
              <BadgeDisplay
                badge={displayBadge}
                size="medium"
                showDetails={true}
                animate={true}
              />
            </motion.div>
          );
        })}
      </motion.div>
    );
  }

  if (layout === 'showcase') {
    const showcaseBadges = earnedBadges
      .sort((a, b) => {
        const rarityOrder = { legendary: 4, epic: 3, rare: 2, common: 1 };
        return rarityOrder[b.rarity] - rarityOrder[a.rarity];
      })
      .slice(0, 5);

    return (
      <Card id="badge-showcase" className="p-6">
        <CardContent className="space-y-4">
          <h3 className="text-lg font-semibold text-center">Badge Showcase</h3>
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="flex justify-center space-x-4"
          >
            {showcaseBadges.map(badge => (
              <motion.div
                key={badge.id}
                className="cursor-pointer"
                onClick={() => onBadgeClick?.(badge)}
              >
                <BadgeDisplay
                  badge={badge}
                  size="large"
                  showDetails={false}
                  animate={true}
                />
              </motion.div>
            ))}
          </motion.div>
          
          {showcaseBadges.length === 0 && (
            <p className="text-center text-gray-500">
              Earn badges to display them here!
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

  return null;
}

// Badge Progress Component
interface BadgeProgressProps {
  badges: BadgeType[];
  earnedBadges: BadgeType[];
  className?: string;
}

export function BadgeProgress({ badges, earnedBadges, className }: BadgeProgressProps) {
  const earnedCount = earnedBadges.length;
  const totalCount = badges.length;
  const progress = totalCount > 0 ? (earnedCount / totalCount) * 100 : 0;

  const rarityStats = badges.reduce((acc, badge) => {
    const isEarned = earnedBadges.some(earned => earned.id === badge.id);
    if (!acc[badge.rarity]) {
      acc[badge.rarity] = { total: 0, earned: 0 };
    }
    acc[badge.rarity].total += 1;
    if (isEarned) {
      acc[badge.rarity].earned += 1;
    }
    return acc;
  }, {} as Record<string, { total: number; earned: number }>);

  return (
    <Card id="badge-progress" className={className}>
      <CardContent className="p-6 space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold">Badge Collection Progress</h3>
          <p className="text-gray-600">
            {earnedCount} of {totalCount} badges collected ({Math.round(progress)}%)
          </p>
        </div>

        <div className="space-y-3">
          {Object.entries(rarityStats).map(([rarity, stats]) => {
            const rConfig = rarityConfig[rarity as keyof typeof rarityConfig];
            const RarityIcon = rConfig.icon;
            const rarityProgress = stats.total > 0 ? (stats.earned / stats.total) * 100 : 0;

            return (
              <div key={rarity} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <RarityIcon className={`w-4 h-4 ${rConfig.textColor}`} />
                    <span className="capitalize font-medium">{rarity}</span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {stats.earned}/{stats.total}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full bg-gradient-to-r ${rConfig.color}`}
                    style={{ width: `${rarityProgress}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}