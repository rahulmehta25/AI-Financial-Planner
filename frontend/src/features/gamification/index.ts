// Main exports for the gamification feature

// Components
export { default as GamificationDashboard } from './components/GamificationDashboard';
export { default as GamificationProvider, GamificationContextProvider, useGamificationContext } from './components/GamificationProvider';

// Individual component exports
export {
  AchievementCard,
  AchievementGrid,
  AchievementSummary,
  BadgeDisplay,
  BadgeCollection,
  BadgeProgress,
  MilestoneTracker,
  MilestoneSummary,
  QuickAddMilestone,
  StreakCounter,
  StreakGrid,
  StreakSummary,
  Leaderboard,
  ChallengeSystem,
  ChallengeDetail,
  RewardSystem,
  PointsProgress,
  LevelProgression,
  AllLevelsModal,
  LevelBenefitsDetail,
  CelebrationAnimations,
  useCelebration,
  celebrationTriggers,
} from './components';

// Hooks
export { useGamificationEvents, useFinancialPlanningGamification } from './hooks/useGamificationEvents';

// Store
export { useGamificationStore } from './store/gamificationStore';

// Types
export * from './types';