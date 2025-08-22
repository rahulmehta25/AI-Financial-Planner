import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  GamificationState,
  UserProgress,
  Achievement,
  Badge,
  Streak,
  Milestone,
  Challenge,
  LeaderboardEntry,
  Leaderboard,
  RewardRedemption,
  Level,
  ActivityLog,
  GamificationEvent,
  CelebrationConfig,
  GamificationConfig,
  UserStats,
  PointSource,
  ActivityType,
} from '../types';

interface GamificationActions {
  // User Progress
  initializeUserProgress: (userId: string) => void;
  updateUserStats: (stats: Partial<UserStats>) => void;
  addPoints: (amount: number, source: PointSource, description: string) => void;
  spendPoints: (amount: number, description: string) => boolean;
  
  // Achievements
  checkAchievements: (event: GamificationEvent) => Achievement[];
  unlockAchievement: (achievementId: string) => void;
  updateAchievementProgress: (achievementId: string, progress: number) => void;
  
  // Badges
  earnBadge: (badgeId: string) => void;
  checkBadgeEligibility: () => void;
  
  // Streaks
  updateStreak: (streakType: string, date?: Date) => void;
  resetStreak: (streakId: string) => void;
  checkStreakMilestones: (streak: Streak) => void;
  
  // Milestones
  updateMilestoneProgress: (milestoneId: string, currentValue: number) => void;
  completeMilestone: (milestoneId: string) => void;
  
  // Challenges
  joinChallenge: (challengeId: string) => void;
  leaveChallenge: (challengeId: string) => void;
  updateChallengeProgress: (challengeId: string, progress: Partial<Challenge>) => void;
  completeChallenge: (challengeId: string) => void;
  
  // Levels
  checkLevelUp: () => Level | null;
  levelUp: (newLevel: number) => void;
  
  // Leaderboards
  updateLeaderboards: () => void;
  getLeaderboardRank: (type: string) => number;
  
  // Celebrations
  triggerCelebration: (config: CelebrationConfig) => void;
  clearCelebrations: () => void;
  
  // Activity Log
  addActivity: (type: ActivityType, description: string, points?: number) => void;
  clearOldActivities: (daysToKeep: number) => void;
  
  // General
  processEvent: (event: GamificationEvent) => void;
  resetProgress: () => void;
  exportProgress: () => string;
  importProgress: (data: string) => boolean;
}

const defaultConfig: GamificationConfig = {
  pointsPerFormCompletion: 100,
  pointsPerGoalSet: 50,
  pointsPerMilestoneReached: 200,
  streakBonusMultiplier: 1.1,
  levelUpPointsBase: 1000,
  levelUpPointsMultiplier: 1.5,
  maxLevel: 100,
  dailyLoginPoints: 10,
  referralBonusPoints: 500,
};

const defaultLevels: Level[] = Array.from({ length: 100 }, (_, i) => {
  const level = i + 1;
  const pointsRequired = Math.floor(
    defaultConfig.levelUpPointsBase * Math.pow(defaultConfig.levelUpPointsMultiplier, level - 1)
  );
  
  return {
    level,
    title: getLevelTitle(level),
    description: getLevelDescription(level),
    pointsRequired,
    pointsToNext: level < 100 ? Math.floor(
      defaultConfig.levelUpPointsBase * Math.pow(defaultConfig.levelUpPointsMultiplier, level)
    ) - pointsRequired : 0,
    icon: getLevelIcon(level),
    color: getLevelColor(level),
    benefits: getLevelBenefits(level),
    isUnlocked: level === 1,
  };
});

const defaultAchievements: Achievement[] = [
  {
    id: 'first_form',
    title: 'Getting Started',
    description: 'Complete your first financial planning form',
    icon: '🎯',
    category: 'planning',
    difficulty: 'easy',
    points: 100,
    requirements: [{ type: 'form_completion', value: 1, description: 'Complete 1 form' }],
    isUnlocked: false,
    progress: 0,
  },
  {
    id: 'form_master',
    title: 'Form Master',
    description: 'Complete all sections of the financial planning form',
    icon: '📝',
    category: 'planning',
    difficulty: 'medium',
    points: 500,
    requirements: [{ type: 'form_completion', value: 6, description: 'Complete all form sections' }],
    isUnlocked: false,
    progress: 0,
  },
  {
    id: 'first_goal',
    title: 'Goal Setter',
    description: 'Set your first financial goal',
    icon: '🎯',
    category: 'goals',
    difficulty: 'easy',
    points: 75,
    requirements: [{ type: 'milestone', value: 1, description: 'Set 1 financial goal' }],
    isUnlocked: false,
    progress: 0,
  },
  {
    id: 'savings_starter',
    title: 'Savings Starter',
    description: 'Reach your first savings milestone',
    icon: '💰',
    category: 'savings',
    difficulty: 'medium',
    points: 250,
    requirements: [{ type: 'savings_target', value: 1000, description: 'Save $1,000' }],
    isUnlocked: false,
    progress: 0,
  },
  {
    id: 'consistency_king',
    title: 'Consistency King',
    description: 'Maintain a 30-day login streak',
    icon: '🔥',
    category: 'consistency',
    difficulty: 'hard',
    points: 750,
    requirements: [{ type: 'streak', value: 30, description: 'Login for 30 consecutive days' }],
    isUnlocked: false,
    progress: 0,
  },
  {
    id: 'challenge_champion',
    title: 'Challenge Champion',
    description: 'Complete 5 financial challenges',
    icon: '🏆',
    category: 'goals',
    difficulty: 'hard',
    points: 1000,
    requirements: [{ type: 'challenge_completion', value: 5, description: 'Complete 5 challenges' }],
    isUnlocked: false,
    progress: 0,
  },
  {
    id: 'point_collector',
    title: 'Point Collector',
    description: 'Earn 10,000 total points',
    icon: '⭐',
    category: 'milestone',
    difficulty: 'legendary',
    points: 2000,
    requirements: [{ type: 'points_earned', value: 10000, description: 'Earn 10,000 points' }],
    isUnlocked: false,
    progress: 0,
  },
];

function getLevelTitle(level: number): string {
  if (level <= 10) return `Novice ${level}`;
  if (level <= 25) return `Apprentice ${level}`;
  if (level <= 50) return `Expert ${level}`;
  if (level <= 75) return `Master ${level}`;
  return `Grandmaster ${level}`;
}

function getLevelDescription(level: number): string {
  if (level <= 10) return 'Just getting started with financial planning';
  if (level <= 25) return 'Building solid financial habits';
  if (level <= 50) return 'Demonstrating financial expertise';
  if (level <= 75) return 'Mastering advanced financial strategies';
  return 'Achieving financial planning excellence';
}

function getLevelIcon(level: number): string {
  if (level <= 10) return '🌱';
  if (level <= 25) return '🌿';
  if (level <= 50) return '🌳';
  if (level <= 75) return '🏆';
  return '👑';
}

function getLevelColor(level: number): string {
  if (level <= 10) return '#10B981';
  if (level <= 25) return '#3B82F6';
  if (level <= 50) return '#8B5CF6';
  if (level <= 75) return '#F59E0B';
  return '#EF4444';
}

function getLevelBenefits(level: number): any[] {
  const benefits = [];
  
  if (level % 5 === 0) {
    benefits.push({
      type: 'point_multiplier',
      value: 1 + (level * 0.01),
      description: `${(level * 1)}% bonus points`,
    });
  }
  
  if (level >= 10) {
    benefits.push({
      type: 'feature_unlock',
      value: 1,
      description: 'Advanced analytics access',
    });
  }
  
  if (level >= 25) {
    benefits.push({
      type: 'priority_support',
      value: 1,
      description: 'Priority customer support',
    });
  }
  
  return benefits;
}

export const useGamificationStore = create<GamificationState & GamificationActions>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        userProgress: null,
        achievements: defaultAchievements,
        availableBadges: [],
        leaderboards: [],
        availableChallenges: [],
        rewardRedemptions: [],
        levels: defaultLevels,
        config: defaultConfig,
        celebrations: [],
        isLoading: false,
        error: null,

        // Initialize user progress
        initializeUserProgress: (userId: string) => {
          const now = new Date();
          const initialProgress: UserProgress = {
            userId,
            level: 1,
            totalPoints: 0,
            availablePoints: 0,
            achievements: [],
            badges: [],
            streaks: [
              {
                id: 'daily_login',
                type: 'daily_login',
                name: 'Daily Login',
                description: 'Login every day to maintain your streak',
                icon: '📅',
                currentCount: 0,
                bestCount: 0,
                lastActivityDate: now,
                isActive: false,
                multiplier: 1.1,
              },
              {
                id: 'weekly_savings',
                type: 'weekly_savings',
                name: 'Weekly Savings',
                description: 'Update your savings every week',
                icon: '💰',
                currentCount: 0,
                bestCount: 0,
                lastActivityDate: now,
                isActive: false,
                multiplier: 1.2,
              },
            ],
            milestones: [],
            activeChallenges: [],
            completedChallenges: [],
            recentActivity: [],
            stats: {
              totalFormsCompleted: 0,
              totalGoalsSet: 0,
              totalChallengesCompleted: 0,
              longestStreak: 0,
              totalPointsEarned: 0,
              totalPointsSpent: 0,
              achievementsUnlocked: 0,
              badgesEarned: 0,
              milestonesReached: 0,
              daysActive: 1,
              lastLoginDate: now,
              joinDate: now,
            },
          };

          set({ userProgress: initialProgress });
        },

        // Update user stats
        updateUserStats: (stats: Partial<UserStats>) => {
          set((state) => ({
            userProgress: state.userProgress ? {
              ...state.userProgress,
              stats: { ...state.userProgress.stats, ...stats },
            } : null,
          }));
        },

        // Add points
        addPoints: (amount: number, source: PointSource, description: string) => {
          set((state) => {
            if (!state.userProgress) return state;

            const newTotalPoints = state.userProgress.totalPoints + amount;
            const newAvailablePoints = state.userProgress.availablePoints + amount;

            // Check for level up
            const currentLevel = state.userProgress.level;
            const newLevel = state.levels.findIndex(l => l.pointsRequired > newTotalPoints);
            const actualNewLevel = newLevel === -1 ? state.levels.length : newLevel;

            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type: 'points_earned',
              description,
              points: amount,
              timestamp: new Date(),
              metadata: { source },
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                totalPoints: newTotalPoints,
                availablePoints: newAvailablePoints,
                level: actualNewLevel,
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
                stats: {
                  ...state.userProgress.stats,
                  totalPointsEarned: state.userProgress.stats.totalPointsEarned + amount,
                },
              },
            };
          });

          // Check for level up
          get().checkLevelUp();
        },

        // Spend points
        spendPoints: (amount: number, description: string) => {
          const { userProgress } = get();
          if (!userProgress || userProgress.availablePoints < amount) {
            return false;
          }

          set((state) => {
            if (!state.userProgress) return state;

            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type: 'points_spent',
              description,
              points: -amount,
              timestamp: new Date(),
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                availablePoints: state.userProgress.availablePoints - amount,
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
                stats: {
                  ...state.userProgress.stats,
                  totalPointsSpent: state.userProgress.stats.totalPointsSpent + amount,
                },
              },
            };
          });

          return true;
        },

        // Check achievements
        checkAchievements: (event: GamificationEvent) => {
          const { achievements, userProgress } = get();
          if (!userProgress) return [];

          const unlockedAchievements: Achievement[] = [];

          achievements.forEach(achievement => {
            if (achievement.isUnlocked) return;

            let canUnlock = true;
            let progress = 0;

            achievement.requirements.forEach(req => {
              switch (req.type) {
                case 'form_completion':
                  progress = Math.min(100, (userProgress.stats.totalFormsCompleted / req.value) * 100);
                  if (userProgress.stats.totalFormsCompleted < req.value) canUnlock = false;
                  break;
                case 'points_earned':
                  progress = Math.min(100, (userProgress.stats.totalPointsEarned / req.value) * 100);
                  if (userProgress.stats.totalPointsEarned < req.value) canUnlock = false;
                  break;
                case 'challenge_completion':
                  progress = Math.min(100, (userProgress.stats.totalChallengesCompleted / req.value) * 100);
                  if (userProgress.stats.totalChallengesCompleted < req.value) canUnlock = false;
                  break;
                case 'streak':
                  const longestStreak = userProgress.stats.longestStreak;
                  progress = Math.min(100, (longestStreak / req.value) * 100);
                  if (longestStreak < req.value) canUnlock = false;
                  break;
              }
            });

            // Update progress
            get().updateAchievementProgress(achievement.id, progress);

            if (canUnlock) {
              get().unlockAchievement(achievement.id);
              unlockedAchievements.push({ ...achievement, isUnlocked: true, progress: 100 });
            }
          });

          return unlockedAchievements;
        },

        // Unlock achievement
        unlockAchievement: (achievementId: string) => {
          set((state) => {
            const achievement = state.achievements.find(a => a.id === achievementId);
            if (!achievement || achievement.isUnlocked || !state.userProgress) return state;

            const unlockedAchievement = {
              ...achievement,
              isUnlocked: true,
              unlockedAt: new Date(),
              progress: 100,
            };

            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type: 'achievement_unlocked',
              description: `Unlocked achievement: ${achievement.title}`,
              points: achievement.points,
              timestamp: new Date(),
              metadata: { achievementId },
            };

            return {
              ...state,
              achievements: state.achievements.map(a => 
                a.id === achievementId ? unlockedAchievement : a
              ),
              userProgress: {
                ...state.userProgress,
                achievements: [...state.userProgress.achievements, unlockedAchievement],
                totalPoints: state.userProgress.totalPoints + achievement.points,
                availablePoints: state.userProgress.availablePoints + achievement.points,
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
                stats: {
                  ...state.userProgress.stats,
                  achievementsUnlocked: state.userProgress.stats.achievementsUnlocked + 1,
                  totalPointsEarned: state.userProgress.stats.totalPointsEarned + achievement.points,
                },
              },
            };
          });
        },

        // Update achievement progress
        updateAchievementProgress: (achievementId: string, progress: number) => {
          set((state) => ({
            achievements: state.achievements.map(a =>
              a.id === achievementId ? { ...a, progress: Math.min(100, progress) } : a
            ),
          }));
        },

        // Earn badge
        earnBadge: (badgeId: string) => {
          set((state) => {
            const badge = state.availableBadges.find(b => b.id === badgeId);
            if (!badge || !state.userProgress) return state;

            const earnedBadge = { ...badge, earnedAt: new Date() };

            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type: 'badge_earned',
              description: `Earned badge: ${badge.name}`,
              timestamp: new Date(),
              metadata: { badgeId },
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                badges: [...state.userProgress.badges, earnedBadge],
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
                stats: {
                  ...state.userProgress.stats,
                  badgesEarned: state.userProgress.stats.badgesEarned + 1,
                },
              },
            };
          });
        },

        // Check badge eligibility
        checkBadgeEligibility: () => {
          // Implementation for checking badge eligibility
          const { userProgress, availableBadges } = get();
          if (!userProgress) return;

          availableBadges.forEach(badge => {
            if (userProgress.badges.some(b => b.id === badge.id)) return;

            let isEligible = false;

            switch (badge.criteria.type) {
              case 'achievement_unlock':
                isEligible = userProgress.achievements.length >= badge.criteria.value;
                break;
              case 'points_threshold':
                isEligible = userProgress.totalPoints >= badge.criteria.value;
                break;
              case 'level_reached':
                isEligible = userProgress.level >= badge.criteria.value;
                break;
            }

            if (isEligible) {
              get().earnBadge(badge.id);
            }
          });
        },

        // Update streak
        updateStreak: (streakType: string, date = new Date()) => {
          set((state) => {
            if (!state.userProgress) return state;

            const streakIndex = state.userProgress.streaks.findIndex(s => s.type === streakType);
            if (streakIndex === -1) return state;

            const streak = state.userProgress.streaks[streakIndex];
            const lastActivity = new Date(streak.lastActivityDate);
            const daysDiff = Math.floor((date.getTime() - lastActivity.getTime()) / (1000 * 60 * 60 * 24));

            let newCount = streak.currentCount;
            let isActive = streak.isActive;

            if (daysDiff === 1) {
              // Continue streak
              newCount += 1;
              isActive = true;
            } else if (daysDiff === 0) {
              // Same day, no change
              return state;
            } else {
              // Streak broken
              newCount = 1;
              isActive = true;
            }

            const updatedStreak = {
              ...streak,
              currentCount: newCount,
              bestCount: Math.max(streak.bestCount, newCount),
              lastActivityDate: date,
              isActive,
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                streaks: state.userProgress.streaks.map((s, i) => 
                  i === streakIndex ? updatedStreak : s
                ),
                stats: {
                  ...state.userProgress.stats,
                  longestStreak: Math.max(
                    state.userProgress.stats.longestStreak, 
                    newCount
                  ),
                },
              },
            };
          });
        },

        // Reset streak
        resetStreak: (streakId: string) => {
          set((state) => {
            if (!state.userProgress) return state;

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                streaks: state.userProgress.streaks.map(s =>
                  s.id === streakId ? { ...s, currentCount: 0, isActive: false } : s
                ),
              },
            };
          });
        },

        // Check streak milestones
        checkStreakMilestones: (streak: Streak) => {
          // Check for streak milestone achievements
          if (streak.currentCount > 0 && streak.currentCount % 7 === 0) {
            get().addPoints(
              50 * (streak.currentCount / 7),
              'streak_bonus',
              `${streak.currentCount}-day ${streak.name} streak`
            );
          }
        },

        // Update milestone progress
        updateMilestoneProgress: (milestoneId: string, currentValue: number) => {
          set((state) => {
            if (!state.userProgress) return state;

            const milestoneIndex = state.userProgress.milestones.findIndex(m => m.id === milestoneId);
            if (milestoneIndex === -1) return state;

            const milestone = state.userProgress.milestones[milestoneIndex];
            const progress = Math.min(currentValue, milestone.targetValue);
            const isCompleted = progress >= milestone.targetValue;

            const updatedMilestone = {
              ...milestone,
              currentValue: progress,
              isCompleted,
              completedAt: isCompleted && !milestone.isCompleted ? new Date() : milestone.completedAt,
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                milestones: state.userProgress.milestones.map((m, i) =>
                  i === milestoneIndex ? updatedMilestone : m
                ),
              },
            };
          });

          // Check if milestone was just completed
          const { userProgress } = get();
          if (userProgress) {
            const milestone = userProgress.milestones.find(m => m.id === milestoneId);
            if (milestone && milestone.isCompleted) {
              get().completeMilestone(milestoneId);
            }
          }
        },

        // Complete milestone
        completeMilestone: (milestoneId: string) => {
          set((state) => {
            if (!state.userProgress) return state;

            const milestone = state.userProgress.milestones.find(m => m.id === milestoneId);
            if (!milestone || milestone.isCompleted) return state;

            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type: 'milestone_reached',
              description: `Reached milestone: ${milestone.title}`,
              points: milestone.points,
              timestamp: new Date(),
              metadata: { milestoneId },
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                totalPoints: state.userProgress.totalPoints + milestone.points,
                availablePoints: state.userProgress.availablePoints + milestone.points,
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
                stats: {
                  ...state.userProgress.stats,
                  milestonesReached: state.userProgress.stats.milestonesReached + 1,
                  totalPointsEarned: state.userProgress.stats.totalPointsEarned + milestone.points,
                },
              },
            };
          });
        },

        // Join challenge
        joinChallenge: (challengeId: string) => {
          set((state) => {
            const challenge = state.availableChallenges.find(c => c.id === challengeId);
            if (!challenge || !state.userProgress) return state;

            const joinedChallenge = {
              ...challenge,
              startDate: new Date(),
              endDate: new Date(Date.now() + challenge.duration * 24 * 60 * 60 * 1000),
              isActive: true,
              progress: 0,
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                activeChallenges: [...state.userProgress.activeChallenges, joinedChallenge],
              },
            };
          });
        },

        // Leave challenge
        leaveChallenge: (challengeId: string) => {
          set((state) => {
            if (!state.userProgress) return state;

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                activeChallenges: state.userProgress.activeChallenges.filter(
                  c => c.id !== challengeId
                ),
              },
            };
          });
        },

        // Update challenge progress
        updateChallengeProgress: (challengeId: string, progress: Partial<Challenge>) => {
          set((state) => {
            if (!state.userProgress) return state;

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                activeChallenges: state.userProgress.activeChallenges.map(c =>
                  c.id === challengeId ? { ...c, ...progress } : c
                ),
              },
            };
          });
        },

        // Complete challenge
        completeChallenge: (challengeId: string) => {
          set((state) => {
            if (!state.userProgress) return state;

            const challenge = state.userProgress.activeChallenges.find(c => c.id === challengeId);
            if (!challenge) return state;

            const completedChallenge = {
              ...challenge,
              isCompleted: true,
              progress: 100,
            };

            let totalPoints = 0;
            challenge.rewards.forEach(reward => {
              if (reward.type === 'points') {
                totalPoints += reward.value;
              }
            });

            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type: 'challenge_completed',
              description: `Completed challenge: ${challenge.title}`,
              points: totalPoints,
              timestamp: new Date(),
              metadata: { challengeId },
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                activeChallenges: state.userProgress.activeChallenges.filter(
                  c => c.id !== challengeId
                ),
                completedChallenges: [...state.userProgress.completedChallenges, completedChallenge],
                totalPoints: state.userProgress.totalPoints + totalPoints,
                availablePoints: state.userProgress.availablePoints + totalPoints,
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
                stats: {
                  ...state.userProgress.stats,
                  totalChallengesCompleted: state.userProgress.stats.totalChallengesCompleted + 1,
                  totalPointsEarned: state.userProgress.stats.totalPointsEarned + totalPoints,
                },
              },
            };
          });
        },

        // Check level up
        checkLevelUp: () => {
          const { userProgress, levels } = get();
          if (!userProgress) return null;

          const currentLevel = userProgress.level;
          const newLevel = levels.findIndex(l => l.pointsRequired > userProgress.totalPoints);
          const actualNewLevel = newLevel === -1 ? levels.length : newLevel;

          if (actualNewLevel > currentLevel) {
            get().levelUp(actualNewLevel);
            return levels[actualNewLevel - 1];
          }

          return null;
        },

        // Level up
        levelUp: (newLevel: number) => {
          set((state) => {
            if (!state.userProgress) return state;

            const levelData = state.levels[newLevel - 1];
            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type: 'level_up',
              description: `Reached ${levelData.title}!`,
              timestamp: new Date(),
              metadata: { newLevel, levelTitle: levelData.title },
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                level: newLevel,
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
              },
            };
          });
        },

        // Update leaderboards
        updateLeaderboards: () => {
          // This would typically fetch from an API
          // For now, we'll implement a simple local leaderboard
        },

        // Get leaderboard rank
        getLeaderboardRank: (type: string) => {
          const { leaderboards, userProgress } = get();
          if (!userProgress) return 0;

          const leaderboard = leaderboards.find(l => l.type === type);
          if (!leaderboard) return 0;

          const userEntry = leaderboard.entries.find(e => e.id === userProgress.userId);
          return userEntry?.rank || 0;
        },

        // Trigger celebration
        triggerCelebration: (config: CelebrationConfig) => {
          set((state) => ({
            celebrations: [...state.celebrations, config],
          }));

          // Auto-clear celebration after duration
          setTimeout(() => {
            set((state) => ({
              celebrations: state.celebrations.filter(c => c !== config),
            }));
          }, config.duration);
        },

        // Clear celebrations
        clearCelebrations: () => {
          set({ celebrations: [] });
        },

        // Add activity
        addActivity: (type: ActivityType, description: string, points?: number) => {
          set((state) => {
            if (!state.userProgress) return state;

            const activity: ActivityLog = {
              id: Math.random().toString(36).substr(2, 9),
              type,
              description,
              points,
              timestamp: new Date(),
            };

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                recentActivity: [activity, ...state.userProgress.recentActivity].slice(0, 50),
              },
            };
          });
        },

        // Clear old activities
        clearOldActivities: (daysToKeep: number) => {
          set((state) => {
            if (!state.userProgress) return state;

            const cutoffDate = new Date(Date.now() - daysToKeep * 24 * 60 * 60 * 1000);

            return {
              ...state,
              userProgress: {
                ...state.userProgress,
                recentActivity: state.userProgress.recentActivity.filter(
                  a => new Date(a.timestamp) > cutoffDate
                ),
              },
            };
          });
        },

        // Process event
        processEvent: (event: GamificationEvent) => {
          const { addPoints, checkAchievements, updateStreak } = get();

          switch (event.type) {
            case 'form_completed':
              addPoints(defaultConfig.pointsPerFormCompletion, 'form_completion', 'Completed form section');
              break;
            case 'goal_created':
              addPoints(defaultConfig.pointsPerGoalSet, 'form_completion', 'Set financial goal');
              break;
            case 'daily_login':
              addPoints(defaultConfig.dailyLoginPoints, 'daily_login', 'Daily login bonus');
              updateStreak('daily_login');
              break;
            case 'milestone_reached':
              addPoints(defaultConfig.pointsPerMilestoneReached, 'milestone', 'Reached milestone');
              break;
          }

          // Check for achievements after processing event
          checkAchievements(event);
        },

        // Reset progress
        resetProgress: () => {
          set({
            userProgress: null,
            celebrations: [],
            isLoading: false,
            error: null,
          });
        },

        // Export progress
        exportProgress: () => {
          const { userProgress } = get();
          if (!userProgress) return '';
          
          return JSON.stringify(userProgress, null, 2);
        },

        // Import progress
        importProgress: (data: string) => {
          try {
            const userProgress = JSON.parse(data);
            set({ userProgress });
            return true;
          } catch {
            return false;
          }
        },
      }),
      {
        name: 'gamification-storage',
        partialize: (state) => ({
          userProgress: state.userProgress,
          achievements: state.achievements,
          config: state.config,
        }),
      }
    ),
    {
      name: 'gamification-store',
    }
  )
);