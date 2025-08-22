import { useCallback } from 'react';
import { useGamificationStore } from '../store/gamificationStore';
import { useCelebration, celebrationTriggers } from '../components/CelebrationAnimations';
import { GamificationEvent, FormStep } from '../types';

/**
 * Hook for integrating gamification events with the financial planning flow
 */
export function useGamificationEvents() {
  const {
    userProgress,
    processEvent,
    checkAchievements,
    updateStreak,
    addPoints,
    checkLevelUp,
    config,
  } = useGamificationStore();

  const { triggerCelebration } = useCelebration();

  // Track form completion events
  const trackFormCompletion = useCallback((step: FormStep, userId: string) => {
    const event: GamificationEvent = {
      type: 'form_completed',
      userId,
      metadata: { step },
      timestamp: new Date(),
    };

    // Process the event through the gamification system
    processEvent(event);

    // Check for achievements
    const unlockedAchievements = checkAchievements(event);
    
    // Trigger celebrations for new achievements
    unlockedAchievements.forEach(achievement => {
      const intensity = achievement.difficulty === 'legendary' ? 'epic' : 
                      achievement.difficulty === 'hard' ? 'high' : 'medium';
      triggerCelebration(celebrationTriggers.achievementUnlocked(intensity));
    });

    // Check for level up
    const newLevel = checkLevelUp();
    if (newLevel) {
      const intensity = newLevel.level % 10 === 0 ? 'epic' : 'high';
      triggerCelebration(celebrationTriggers.levelUp(intensity));
    }

    // Update daily login streak
    updateStreak('daily_login');

    return {
      pointsEarned: config.pointsPerFormCompletion,
      achievements: unlockedAchievements,
      levelUp: newLevel,
    };
  }, [processEvent, checkAchievements, triggerCelebration, checkLevelUp, updateStreak, config]);

  // Track goal creation events
  const trackGoalCreation = useCallback((goalData: any, userId: string) => {
    const event: GamificationEvent = {
      type: 'goal_created',
      userId,
      metadata: { goalData },
      timestamp: new Date(),
    };

    processEvent(event);

    // Check for first goal achievement
    if (userProgress && userProgress.stats.totalGoalsSet === 0) {
      triggerCelebration(celebrationTriggers.firstTime('high'));
    }

    const unlockedAchievements = checkAchievements(event);
    unlockedAchievements.forEach(achievement => {
      triggerCelebration(celebrationTriggers.achievementUnlocked('medium'));
    });

    return {
      pointsEarned: config.pointsPerGoalSet,
      achievements: unlockedAchievements,
    };
  }, [processEvent, checkAchievements, triggerCelebration, userProgress, config]);

  // Track milestone progress
  const trackMilestoneProgress = useCallback((milestoneId: string, currentValue: number, userId: string) => {
    const event: GamificationEvent = {
      type: 'milestone_reached',
      userId,
      metadata: { milestoneId, currentValue },
      timestamp: new Date(),
    };

    processEvent(event);

    // Check if milestone was completed
    const milestone = userProgress?.milestones.find(m => m.id === milestoneId);
    if (milestone && currentValue >= milestone.targetValue) {
      triggerCelebration(celebrationTriggers.milestoneReached('medium'));
      
      const unlockedAchievements = checkAchievements(event);
      unlockedAchievements.forEach(achievement => {
        triggerCelebration(celebrationTriggers.achievementUnlocked('medium'));
      });
    }

    return {
      pointsEarned: milestone?.isCompleted ? config.pointsPerMilestoneReached : 0,
      milestoneCompleted: milestone?.isCompleted,
    };
  }, [processEvent, triggerCelebration, userProgress, checkAchievements, config]);

  // Track daily login
  const trackDailyLogin = useCallback((userId: string) => {
    const event: GamificationEvent = {
      type: 'daily_login',
      userId,
      metadata: {},
      timestamp: new Date(),
    };

    processEvent(event);
    updateStreak('daily_login');

    // Check for streak milestones
    const loginStreak = userProgress?.streaks.find(s => s.type === 'daily_login');
    if (loginStreak && loginStreak.currentCount > 0 && loginStreak.currentCount % 7 === 0) {
      triggerCelebration(celebrationTriggers.streakMilestone('medium'));
    }

    return {
      pointsEarned: config.dailyLoginPoints,
      streakDay: loginStreak?.currentCount || 1,
    };
  }, [processEvent, updateStreak, userProgress, triggerCelebration, config]);

  // Track savings updates
  const trackSavingsUpdate = useCallback((savingsData: any, userId: string) => {
    updateStreak('weekly_savings');

    // Check for savings milestones
    const milestones = userProgress?.milestones.filter(m => 
      m.category === 'savings_amount' && !m.isCompleted
    ) || [];

    milestones.forEach(milestone => {
      if (savingsData.totalSavings >= milestone.targetValue) {
        trackMilestoneProgress(milestone.id, savingsData.totalSavings, userId);
      }
    });

    return {
      milestonesReached: milestones.filter(m => savingsData.totalSavings >= m.targetValue).length,
    };
  }, [updateStreak, userProgress, trackMilestoneProgress]);

  // Track simulation completion
  const trackSimulationCompletion = useCallback((simulationData: any, userId: string) => {
    // Add bonus points for completing simulation
    addPoints(
      200, 
      'form_completion', 
      'Completed financial simulation'
    );

    // Check for planning-related achievements
    const event: GamificationEvent = {
      type: 'form_completed',
      userId,
      metadata: { simulationData, type: 'simulation' },
      timestamp: new Date(),
    };

    const unlockedAchievements = checkAchievements(event);
    unlockedAchievements.forEach(achievement => {
      if (achievement.category === 'planning') {
        triggerCelebration(celebrationTriggers.achievementUnlocked('high'));
      }
    });

    return {
      pointsEarned: 200,
      achievements: unlockedAchievements,
    };
  }, [addPoints, checkAchievements, triggerCelebration]);

  // Get user's current gamification status
  const getGamificationStatus = useCallback(() => {
    if (!userProgress) return null;

    const currentLevel = userProgress.level;
    const nextLevelPoints = Math.floor(
      config.levelUpPointsBase * Math.pow(config.levelUpPointsMultiplier, currentLevel)
    );
    const progressToNextLevel = userProgress.totalPoints / nextLevelPoints * 100;

    return {
      level: currentLevel,
      totalPoints: userProgress.totalPoints,
      availablePoints: userProgress.availablePoints,
      progressToNextLevel: Math.min(100, progressToNextLevel),
      activeStreaks: userProgress.streaks.filter(s => s.isActive).length,
      unlockedAchievements: userProgress.achievements.filter(a => a.isUnlocked).length,
      completedChallenges: userProgress.completedChallenges.length,
    };
  }, [userProgress, config]);

  // Check if user has specific achievement
  const hasAchievement = useCallback((achievementId: string) => {
    return userProgress?.achievements.some(a => a.id === achievementId && a.isUnlocked) || false;
  }, [userProgress]);

  // Get current active challenges
  const getActiveChallenges = useCallback(() => {
    return userProgress?.activeChallenges || [];
  }, [userProgress]);

  // Get recent activity
  const getRecentActivity = useCallback((limit = 5) => {
    return userProgress?.recentActivity.slice(0, limit) || [];
  }, [userProgress]);

  return {
    // Event tracking functions
    trackFormCompletion,
    trackGoalCreation,
    trackMilestoneProgress,
    trackDailyLogin,
    trackSavingsUpdate,
    trackSimulationCompletion,
    
    // Status functions
    getGamificationStatus,
    hasAchievement,
    getActiveChallenges,
    getRecentActivity,
    
    // Direct access to user progress
    userProgress,
    isInitialized: !!userProgress,
  };
}

/**
 * Hook for gamification integration in specific financial planning components
 */
export function useFinancialPlanningGamification() {
  const {
    trackFormCompletion,
    trackGoalCreation,
    trackSavingsUpdate,
    trackSimulationCompletion,
    getGamificationStatus,
    hasAchievement,
  } = useGamificationEvents();

  // Helper for form step completion with context
  const completeFormStep = useCallback((step: FormStep, userId: string, formData?: any) => {
    const result = trackFormCompletion(step, userId);
    
    // Additional context-specific logic
    if (step === 'review' && formData) {
      // User completed the entire form
      const bonusResult = trackSimulationCompletion(formData, userId);
      return {
        ...result,
        bonusPoints: bonusResult.pointsEarned,
        totalPoints: result.pointsEarned + bonusResult.pointsEarned,
      };
    }

    return result;
  }, [trackFormCompletion, trackSimulationCompletion]);

  // Helper for goal creation with validation
  const createGoal = useCallback((goalData: any, userId: string) => {
    // Validate goal data
    if (!goalData.desiredMonthlyIncome || goalData.desiredMonthlyIncome <= 0) {
      throw new Error('Invalid goal data');
    }

    return trackGoalCreation(goalData, userId);
  }, [trackGoalCreation]);

  // Helper for savings tracking with milestone detection
  const updateSavings = useCallback((savingsData: any, userId: string) => {
    const result = trackSavingsUpdate(savingsData, userId);
    
    // Check for specific savings achievements
    const status = getGamificationStatus();
    const milestones = [1000, 5000, 10000, 25000, 50000, 100000];
    
    const reachedMilestones = milestones.filter(amount => 
      savingsData.totalSavings >= amount && 
      !hasAchievement(`savings_${amount}`)
    );

    return {
      ...result,
      savingsMilestones: reachedMilestones,
      currentLevel: status?.level,
    };
  }, [trackSavingsUpdate, getGamificationStatus, hasAchievement]);

  return {
    completeFormStep,
    createGoal,
    updateSavings,
    getGamificationStatus,
    hasAchievement,
  };
}