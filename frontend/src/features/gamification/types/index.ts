// Gamification core types
export interface User {
  id: string;
  username: string;
  avatar?: string;
  joinDate: Date;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: AchievementCategory;
  difficulty: 'easy' | 'medium' | 'hard' | 'legendary';
  points: number;
  requirements: AchievementRequirement[];
  isUnlocked: boolean;
  unlockedAt?: Date;
  progress: number; // 0-100 percentage
  hidden?: boolean; // Hidden achievements
}

export type AchievementCategory = 
  | 'planning' 
  | 'savings' 
  | 'budgeting' 
  | 'investment' 
  | 'goals' 
  | 'education' 
  | 'consistency' 
  | 'milestone';

export interface AchievementRequirement {
  type: 'form_completion' | 'savings_target' | 'streak' | 'milestone' | 'challenge_completion' | 'points_earned';
  value: number;
  description: string;
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  earnedAt?: Date;
  criteria: BadgeCriteria;
}

export interface BadgeCriteria {
  type: 'achievement_unlock' | 'streak_milestone' | 'goal_completion' | 'level_reached' | 'points_threshold';
  value: number;
  metadata?: Record<string, any>;
}

export interface Streak {
  id: string;
  type: StreakType;
  name: string;
  description: string;
  icon: string;
  currentCount: number;
  bestCount: number;
  lastActivityDate: Date;
  isActive: boolean;
  multiplier: number; // Points multiplier for active streaks
}

export type StreakType = 
  | 'daily_login' 
  | 'weekly_savings' 
  | 'monthly_budget_review' 
  | 'goal_check_in' 
  | 'investment_review' 
  | 'education_completion';

export interface Milestone {
  id: string;
  title: string;
  description: string;
  category: MilestoneCategory;
  targetValue: number;
  currentValue: number;
  unit: string;
  icon: string;
  color: string;
  points: number;
  isCompleted: boolean;
  completedAt?: Date;
  deadline?: Date;
}

export type MilestoneCategory = 
  | 'savings_amount' 
  | 'investment_growth' 
  | 'debt_reduction' 
  | 'budget_adherence' 
  | 'goal_progress' 
  | 'emergency_fund';

export interface Challenge {
  id: string;
  title: string;
  description: string;
  category: ChallengeCategory;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  duration: number; // in days
  startDate?: Date;
  endDate?: Date;
  isActive: boolean;
  isCompleted: boolean;
  participants: number;
  maxParticipants?: number;
  requirements: ChallengeRequirement[];
  rewards: ChallengeReward[];
  progress: number; // 0-100 percentage
  icon: string;
  color: string;
}

export type ChallengeCategory = 
  | 'savings' 
  | 'budgeting' 
  | 'investment' 
  | 'debt_payoff' 
  | 'emergency_fund' 
  | 'education' 
  | 'planning';

export interface ChallengeRequirement {
  type: 'save_amount' | 'reduce_expense' | 'increase_income' | 'complete_lessons' | 'maintain_streak';
  target: number;
  current: number;
  description: string;
}

export interface ChallengeReward {
  type: 'points' | 'badge' | 'achievement' | 'title' | 'bonus_multiplier';
  value: number;
  itemId?: string;
  description: string;
}

export interface LeaderboardEntry {
  id: string;
  username: string;
  avatar?: string;
  rank: number;
  points: number;
  level: number;
  badges: number;
  achievements: number;
  isCurrentUser?: boolean;
}

export interface Leaderboard {
  id: string;
  name: string;
  description: string;
  type: LeaderboardType;
  period: LeaderboardPeriod;
  entries: LeaderboardEntry[];
  lastUpdated: Date;
}

export type LeaderboardType = 
  | 'total_points' 
  | 'monthly_points' 
  | 'achievements' 
  | 'streak_length' 
  | 'challenges_completed' 
  | 'savings_growth';

export type LeaderboardPeriod = 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'all_time';

export interface RewardPoint {
  id: string;
  amount: number;
  source: PointSource;
  description: string;
  earnedAt: Date;
  metadata?: Record<string, any>;
}

export type PointSource = 
  | 'achievement_unlock' 
  | 'challenge_completion' 
  | 'streak_bonus' 
  | 'milestone_reached' 
  | 'form_completion' 
  | 'daily_login' 
  | 'referral_bonus';

export interface RewardRedemption {
  id: string;
  name: string;
  description: string;
  cost: number; // in points
  type: RedemptionType;
  isAvailable: boolean;
  icon: string;
  category: RedemptionCategory;
  value?: number;
  expiresAt?: Date;
}

export type RedemptionType = 
  | 'discount_code' 
  | 'feature_unlock' 
  | 'consultation_credit' 
  | 'premium_trial' 
  | 'educational_content' 
  | 'custom_theme';

export type RedemptionCategory = 
  | 'services' 
  | 'features' 
  | 'education' 
  | 'customization' 
  | 'bonuses';

export interface Level {
  level: number;
  title: string;
  description: string;
  pointsRequired: number;
  pointsToNext: number;
  icon: string;
  color: string;
  benefits: LevelBenefit[];
  isUnlocked: boolean;
}

export interface LevelBenefit {
  type: 'point_multiplier' | 'feature_unlock' | 'discount' | 'priority_support' | 'exclusive_content';
  value: number;
  description: string;
}

export interface UserProgress {
  userId: string;
  level: number;
  totalPoints: number;
  availablePoints: number; // Points not yet spent
  achievements: Achievement[];
  badges: Badge[];
  streaks: Streak[];
  milestones: Milestone[];
  activeChallenges: Challenge[];
  completedChallenges: Challenge[];
  recentActivity: ActivityLog[];
  stats: UserStats;
}

export interface UserStats {
  totalFormsCompleted: number;
  totalGoalsSet: number;
  totalChallengesCompleted: number;
  longestStreak: number;
  totalPointsEarned: number;
  totalPointsSpent: number;
  achievementsUnlocked: number;
  badgesEarned: number;
  milestonesReached: number;
  daysActive: number;
  lastLoginDate: Date;
  joinDate: Date;
}

export interface ActivityLog {
  id: string;
  type: ActivityType;
  description: string;
  points?: number;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export type ActivityType = 
  | 'achievement_unlocked' 
  | 'badge_earned' 
  | 'level_up' 
  | 'streak_started' 
  | 'streak_extended' 
  | 'challenge_joined' 
  | 'challenge_completed' 
  | 'milestone_reached' 
  | 'points_earned' 
  | 'points_spent';

export interface CelebrationConfig {
  type: CelebrationType;
  duration: number; // in milliseconds
  intensity: 'low' | 'medium' | 'high' | 'epic';
  sound?: boolean;
  haptic?: boolean;
  showModal?: boolean;
  showToast?: boolean;
  showConfetti?: boolean;
}

export type CelebrationType = 
  | 'achievement_unlock' 
  | 'badge_earned' 
  | 'level_up' 
  | 'streak_milestone' 
  | 'challenge_complete' 
  | 'milestone_reached' 
  | 'first_time' 
  | 'rare_event';

export interface GamificationConfig {
  pointsPerFormCompletion: number;
  pointsPerGoalSet: number;
  pointsPerMilestoneReached: number;
  streakBonusMultiplier: number;
  levelUpPointsBase: number;
  levelUpPointsMultiplier: number;
  maxLevel: number;
  dailyLoginPoints: number;
  referralBonusPoints: number;
}

export interface GamificationState {
  userProgress: UserProgress | null;
  achievements: Achievement[];
  availableBadges: Badge[];
  leaderboards: Leaderboard[];
  availableChallenges: Challenge[];
  rewardRedemptions: RewardRedemption[];
  levels: Level[];
  config: GamificationConfig;
  celebrations: CelebrationConfig[];
  isLoading: boolean;
  error: string | null;
}

// Action types for gamification events
export interface GamificationEvent {
  type: GamificationEventType;
  userId: string;
  metadata: Record<string, any>;
  timestamp: Date;
}

export type GamificationEventType = 
  | 'form_completed' 
  | 'goal_created' 
  | 'goal_updated' 
  | 'milestone_reached' 
  | 'challenge_joined' 
  | 'challenge_progress' 
  | 'daily_login' 
  | 'streak_activity' 
  | 'points_earned' 
  | 'level_up' 
  | 'achievement_check';