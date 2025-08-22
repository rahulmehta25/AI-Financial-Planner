'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useFinancialPlanningStore } from '@/store/financialPlanningStore';
import { useFinancialPlanningGamification } from '../hooks/useGamificationEvents';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Star, Trophy, Zap, Target } from 'lucide-react';

/**
 * Example component showing how to integrate gamification with existing financial planning forms
 */
export default function FormIntegrationExample() {
  const { currentStep, completedSteps, nextStep, prevStep } = useFinancialPlanningStore();
  const { 
    completeFormStep, 
    getGamificationStatus, 
    hasAchievement,
    getActiveChallenges 
  } = useFinancialPlanningGamification();

  const [lastReward, setLastReward] = React.useState<any>(null);
  const gamificationStatus = getGamificationStatus();
  const activeChallenges = getActiveChallenges();

  // Handle form step completion with gamification
  const handleStepComplete = React.useCallback(() => {
    const userId = 'demo-user'; // In real app, get from auth context
    
    try {
      const result = completeFormStep(currentStep, userId);
      
      // Show reward feedback
      setLastReward(result);
      
      // Move to next step
      nextStep();
      
      // Clear reward after showing
      setTimeout(() => setLastReward(null), 3000);
      
    } catch (error) {
      console.error('Error completing form step:', error);
    }
  }, [currentStep, completeFormStep, nextStep]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Gamification Status Header */}
      {gamificationStatus && (
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Trophy className="w-5 h-5 text-purple-600" />
                  <span className="font-semibold">Level {gamificationStatus.level}</span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Star className="w-5 h-5 text-yellow-600" />
                  <span>{gamificationStatus.availablePoints.toLocaleString()} points</span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-orange-600" />
                  <span>{gamificationStatus.activeStreaks} active streaks</span>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-sm text-gray-600 mb-1">
                  Progress to next level
                </div>
                <Progress 
                  value={gamificationStatus.progressToNextLevel} 
                  className="w-32 h-2" 
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Challenges */}
      {activeChallenges.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-green-600" />
              <span>Active Challenges</span>
            </CardTitle>
          </CardHeader>
          
          <CardContent>
            <div className="space-y-3">
              {activeChallenges.slice(0, 2).map((challenge: any) => (
                <div key={challenge.id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{challenge.title}</h4>
                    <Badge variant="outline">
                      {Math.round(challenge.progress)}% complete
                    </Badge>
                  </div>
                  <Progress value={challenge.progress} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Form Progress with Gamification */}
      <Card>
        <CardHeader>
          <CardTitle>Financial Planning Form</CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Form Steps with Points */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { step: 'personal-info', title: 'Personal Info', points: 100 },
              { step: 'financial-snapshot', title: 'Financial Snapshot', points: 100 },
              { step: 'account-buckets', title: 'Account Buckets', points: 100 },
              { step: 'risk-preference', title: 'Risk Preference', points: 100 },
              { step: 'retirement-goals', title: 'Retirement Goals', points: 100 },
              { step: 'review', title: 'Review & Submit', points: 200 },
            ].map((formStep) => {
              const isCompleted = completedSteps.includes(formStep.step as any);
              const isCurrent = currentStep === formStep.step;
              
              return (
                <div
                  key={formStep.step}
                  className={`p-4 rounded-lg border ${
                    isCompleted 
                      ? 'bg-green-50 border-green-200' 
                      : isCurrent 
                      ? 'bg-blue-50 border-blue-200' 
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{formStep.title}</h4>
                    {isCompleted && (
                      <Badge className="bg-green-500 text-white">
                        +{formStep.points}
                      </Badge>
                    )}
                  </div>
                  
                  <div className="text-sm text-gray-600">
                    {isCompleted ? 'Completed' : isCurrent ? 'Current Step' : 'Pending'}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Mock Form Content */}
          <div className="p-6 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">
              Current Step: {currentStep.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </h3>
            
            <p className="text-gray-600 mb-6">
              This is where the actual form content would be displayed for the current step.
              Complete this step to earn points and unlock achievements!
            </p>

            {/* Achievement Hints */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <Card className="border-dashed border-yellow-300 bg-yellow-50">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Trophy className="w-4 h-4 text-yellow-600" />
                    <span className="font-medium text-yellow-800">Potential Achievement</span>
                  </div>
                  <p className="text-sm text-yellow-700">
                    Complete this step to unlock the "Getting Started" achievement!
                  </p>
                </CardContent>
              </Card>
              
              <Card className="border-dashed border-purple-300 bg-purple-50">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Zap className="w-4 h-4 text-purple-600" />
                    <span className="font-medium text-purple-800">Streak Bonus</span>
                  </div>
                  <p className="text-sm text-purple-700">
                    Keep your daily login streak going for bonus points!
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 'personal-info'}
              >
                Previous
              </Button>
              
              <Button
                onClick={handleStepComplete}
                className="flex-1"
              >
                Complete Step & Earn Points
              </Button>
            </div>
          </div>

          {/* Reward Feedback */}
          {lastReward && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="p-4 bg-green-50 border border-green-200 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-full">
                  <Star className="w-5 h-5 text-green-600" />
                </div>
                
                <div>
                  <h4 className="font-semibold text-green-800">Step Completed!</h4>
                  <p className="text-sm text-green-700">
                    You earned {lastReward.pointsEarned} points
                    {lastReward.achievements?.length > 0 && 
                      ` and unlocked ${lastReward.achievements.length} achievement(s)`
                    }
                    {lastReward.levelUp && ` and leveled up to Level ${lastReward.levelUp.level}`}!
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* Special Achievements Display */}
      <Card>
        <CardHeader>
          <CardTitle>Your Achievements</CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { id: 'first_form', title: 'Getting Started', icon: '🎯' },
              { id: 'form_master', title: 'Form Master', icon: '📝' },
              { id: 'first_goal', title: 'Goal Setter', icon: '🎯' },
              { id: 'consistency_king', title: 'Consistency King', icon: '🔥' },
            ].map((achievement) => {
              const isUnlocked = hasAchievement(achievement.id);
              
              return (
                <div
                  key={achievement.id}
                  className={`p-4 rounded-lg border text-center ${
                    isUnlocked 
                      ? 'bg-yellow-50 border-yellow-200' 
                      : 'bg-gray-50 border-gray-200 opacity-50'
                  }`}
                >
                  <div className="text-2xl mb-2">
                    {isUnlocked ? achievement.icon : '🔒'}
                  </div>
                  <h4 className="font-medium text-sm">{achievement.title}</h4>
                  <p className="text-xs text-gray-600 mt-1">
                    {isUnlocked ? 'Unlocked!' : 'Locked'}
                  </p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}