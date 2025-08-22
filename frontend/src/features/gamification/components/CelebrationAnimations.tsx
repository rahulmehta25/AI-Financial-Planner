'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  Star, 
  Crown, 
  Zap, 
  Target, 
  Gift, 
  Sparkles,
  Medal,
  Award,
  Flame,
  TrendingUp,
  CheckCircle
} from 'lucide-react';
import { CelebrationConfig, CelebrationType } from '../types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CelebrationAnimationsProps {
  celebrations: CelebrationConfig[];
  onCelebrationComplete?: (celebration: CelebrationConfig) => void;
}

const celebrationTypeConfig: Record<CelebrationType, {
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  title: string;
  message: string;
}> = {
  achievement_unlock: {
    icon: Trophy,
    color: 'text-yellow-500',
    bgColor: 'from-yellow-100 to-yellow-200',
    title: 'Achievement Unlocked!',
    message: 'You earned a new achievement',
  },
  badge_earned: {
    icon: Medal,
    color: 'text-purple-500',
    bgColor: 'from-purple-100 to-purple-200',
    title: 'Badge Earned!',
    message: 'You received a new badge',
  },
  level_up: {
    icon: Crown,
    color: 'text-orange-500',
    bgColor: 'from-orange-100 to-orange-200',
    title: 'Level Up!',
    message: 'You reached a new level',
  },
  streak_milestone: {
    icon: Flame,
    color: 'text-red-500',
    bgColor: 'from-red-100 to-red-200',
    title: 'Streak Milestone!',
    message: 'Your streak is on fire',
  },
  challenge_complete: {
    icon: Target,
    color: 'text-green-500',
    bgColor: 'from-green-100 to-green-200',
    title: 'Challenge Complete!',
    message: 'You completed a challenge',
  },
  milestone_reached: {
    icon: TrendingUp,
    color: 'text-blue-500',
    bgColor: 'from-blue-100 to-blue-200',
    title: 'Milestone Reached!',
    message: 'You hit a major milestone',
  },
  first_time: {
    icon: Sparkles,
    color: 'text-pink-500',
    bgColor: 'from-pink-100 to-pink-200',
    title: 'First Time!',
    message: 'Your first achievement',
  },
  rare_event: {
    icon: Star,
    color: 'text-indigo-500',
    bgColor: 'from-indigo-100 to-indigo-200',
    title: 'Rare Achievement!',
    message: 'Something special happened',
  },
};

// Confetti Component
function Confetti({ intensity = 'medium' }: { intensity?: 'low' | 'medium' | 'high' | 'epic' }) {
  const particleCount = {
    low: 20,
    medium: 50,
    high: 80,
    epic: 120,
  }[intensity];

  const colors = [
    '#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
    '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3'
  ];

  const particles = Array.from({ length: particleCount }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    color: colors[Math.floor(Math.random() * colors.length)],
    size: Math.random() * 6 + 2,
    duration: Math.random() * 3 + 2,
    delay: Math.random() * 2,
  }));

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {particles.map(particle => (
        <motion.div
          key={particle.id}
          className="absolute rounded-full"
          style={{
            backgroundColor: particle.color,
            width: particle.size,
            height: particle.size,
            left: `${particle.x}%`,
            top: `${particle.y}%`,
          }}
          initial={{
            opacity: 1,
            scale: 0,
            rotate: 0,
            y: 0,
          }}
          animate={{
            opacity: [1, 1, 0],
            scale: [0, 1, 0.5],
            rotate: [0, 360, 720],
            y: [0, -200, -400],
            x: [0, Math.random() * 200 - 100],
          }}
          transition={{
            duration: particle.duration,
            delay: particle.delay,
            ease: 'easeOut',
          }}
        />
      ))}
    </div>
  );
}

// Fireworks Component
function Fireworks() {
  const fireworks = Array.from({ length: 5 }, (_, i) => ({
    id: i,
    x: Math.random() * 80 + 10,
    y: Math.random() * 60 + 20,
    delay: i * 0.3,
  }));

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {fireworks.map(firework => (
        <motion.div
          key={firework.id}
          className="absolute"
          style={{
            left: `${firework.x}%`,
            top: `${firework.y}%`,
          }}
          initial={{ scale: 0, opacity: 1 }}
          animate={{
            scale: [0, 2, 3],
            opacity: [1, 0.8, 0],
          }}
          transition={{
            duration: 1.5,
            delay: firework.delay,
            ease: 'easeOut',
          }}
        >
          <div className="relative">
            {Array.from({ length: 12 }, (_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 bg-yellow-400 rounded-full"
                initial={{ x: 0, y: 0, opacity: 1 }}
                animate={{
                  x: Math.cos((i * 30) * Math.PI / 180) * 80,
                  y: Math.sin((i * 30) * Math.PI / 180) * 80,
                  opacity: [1, 0.8, 0],
                }}
                transition={{
                  duration: 1.2,
                  delay: firework.delay + 0.2,
                  ease: 'easeOut',
                }}
              />
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// Sparkle Effect Component
function SparkleEffect({ count = 30 }: { count?: number }) {
  const sparkles = Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    delay: Math.random() * 2,
    duration: Math.random() * 2 + 1,
  }));

  return (
    <div className="fixed inset-0 pointer-events-none z-40">
      {sparkles.map(sparkle => (
        <motion.div
          key={sparkle.id}
          className="absolute"
          style={{
            left: `${sparkle.x}%`,
            top: `${sparkle.y}%`,
          }}
          initial={{ scale: 0, rotate: 0, opacity: 0 }}
          animate={{
            scale: [0, 1, 0],
            rotate: [0, 180, 360],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: sparkle.duration,
            delay: sparkle.delay,
            repeat: 2,
            ease: 'easeInOut',
          }}
        >
          <Sparkles className="w-4 h-4 text-yellow-400" />
        </motion.div>
      ))}
    </div>
  );
}

// Celebration Modal Component
function CelebrationModal({ 
  celebration, 
  isVisible,
  onClose 
}: {
  celebration: CelebrationConfig;
  isVisible: boolean;
  onClose: () => void;
}) {
  const config = celebrationTypeConfig[celebration.type];
  const Icon = config.icon;

  React.useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose();
      }, celebration.duration);

      return () => clearTimeout(timer);
    }
  }, [isVisible, celebration.duration, onClose]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            initial={{ scale: 0, opacity: 0, y: 50 }}
            animate={{ 
              scale: [0, 1.1, 1], 
              opacity: 1, 
              y: 0,
              transition: {
                type: 'spring',
                stiffness: 300,
                damping: 20,
              }
            }}
            exit={{ scale: 0.8, opacity: 0, y: 20 }}
            className="max-w-md w-full mx-4"
          >
            <Card className="overflow-hidden">
              <CardContent className="p-0">
                <div className={`bg-gradient-to-r ${config.bgColor} p-6 text-center relative overflow-hidden`}>
                  {/* Background decoration */}
                  <div className="absolute inset-0 opacity-10">
                    <div className="flex items-center justify-center h-full">
                      <Icon className="w-32 h-32" />
                    </div>
                  </div>

                  {/* Main content */}
                  <div className="relative z-10">
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ 
                        scale: 1, 
                        rotate: 0,
                        transition: {
                          type: 'spring',
                          stiffness: 200,
                          damping: 15,
                          delay: 0.2,
                        }
                      }}
                      className={`w-20 h-20 mx-auto mb-4 rounded-full bg-white flex items-center justify-center shadow-lg`}
                    >
                      <Icon className={`w-12 h-12 ${config.color}`} />
                    </motion.div>

                    <motion.h2
                      initial={{ y: 20, opacity: 0 }}
                      animate={{ 
                        y: 0, 
                        opacity: 1,
                        transition: { delay: 0.4 }
                      }}
                      className="text-2xl font-bold text-gray-800 mb-2"
                    >
                      {config.title}
                    </motion.h2>

                    <motion.p
                      initial={{ y: 20, opacity: 0 }}
                      animate={{ 
                        y: 0, 
                        opacity: 1,
                        transition: { delay: 0.6 }
                      }}
                      className="text-gray-600"
                    >
                      {config.message}
                    </motion.p>

                    {celebration.intensity === 'epic' && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ 
                          scale: 1,
                          transition: { delay: 0.8 }
                        }}
                        className="mt-4"
                      >
                        <Badge className="bg-yellow-500 text-white px-4 py-2 text-lg">
                          🎉 EPIC! 🎉
                        </Badge>
                      </motion.div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Celebration Toast Component
function CelebrationToast({ 
  celebration,
  isVisible,
  onClose 
}: {
  celebration: CelebrationConfig;
  isVisible: boolean;
  onClose: () => void;
}) {
  const config = celebrationTypeConfig[celebration.type];
  const Icon = config.icon;

  React.useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose();
      }, celebration.duration);

      return () => clearTimeout(timer);
    }
  }, [isVisible, celebration.duration, onClose]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed top-4 right-4 z-50"
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <Card className="shadow-lg min-w-80">
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <motion.div
                  initial={{ scale: 0, rotate: -90 }}
                  animate={{ 
                    scale: 1, 
                    rotate: 0,
                    transition: {
                      type: 'spring',
                      stiffness: 400,
                      damping: 20,
                      delay: 0.1,
                    }
                  }}
                  className={`p-2 rounded-full bg-gradient-to-r ${config.bgColor}`}
                >
                  <Icon className={`w-6 h-6 ${config.color}`} />
                </motion.div>

                <div className="flex-1">
                  <motion.h3
                    initial={{ y: 10, opacity: 0 }}
                    animate={{ 
                      y: 0, 
                      opacity: 1,
                      transition: { delay: 0.2 }
                    }}
                    className="font-semibold text-gray-900"
                  >
                    {config.title}
                  </motion.h3>
                  
                  <motion.p
                    initial={{ y: 10, opacity: 0 }}
                    animate={{ 
                      y: 0, 
                      opacity: 1,
                      transition: { delay: 0.3 }
                    }}
                    className="text-sm text-gray-600"
                  >
                    {config.message}
                  </motion.p>
                </div>

                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  ✕
                </button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Floating Achievement Component
function FloatingAchievement({ 
  celebration,
  isVisible,
  onClose 
}: {
  celebration: CelebrationConfig;
  isVisible: boolean;
  onClose: () => void;
}) {
  const config = celebrationTypeConfig[celebration.type];
  const Icon = config.icon;

  React.useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose();
      }, celebration.duration);

      return () => clearTimeout(timer);
    }
  }, [isVisible, celebration.duration, onClose]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed inset-0 flex items-center justify-center pointer-events-none z-40"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            initial={{ 
              scale: 0, 
              y: 100, 
              rotate: -10,
              opacity: 0 
            }}
            animate={{ 
              scale: [0, 1.2, 1], 
              y: [100, -20, 0],
              rotate: [-10, 5, 0],
              opacity: 1,
              transition: {
                type: 'spring',
                stiffness: 200,
                damping: 15,
                duration: 0.8,
              }
            }}
            exit={{ 
              scale: 0.8, 
              y: -50, 
              opacity: 0,
              transition: { duration: 0.3 }
            }}
            className="relative"
          >
            {/* Glow effect */}
            <motion.div
              className={`absolute inset-0 rounded-full bg-gradient-to-r ${config.bgColor} opacity-30 blur-xl`}
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />

            {/* Main icon */}
            <div className={`relative w-24 h-24 rounded-full bg-white shadow-2xl flex items-center justify-center`}>
              <Icon className={`w-12 h-12 ${config.color}`} />
            </div>

            {/* Orbiting particles */}
            {Array.from({ length: 6 }, (_, i) => (
              <motion.div
                key={i}
                className="absolute w-3 h-3 bg-yellow-400 rounded-full"
                style={{
                  left: '50%',
                  top: '50%',
                  marginLeft: -6,
                  marginTop: -6,
                }}
                animate={{
                  x: Math.cos((i * 60) * Math.PI / 180) * 50,
                  y: Math.sin((i * 60) * Math.PI / 180) * 50,
                  rotate: [0, 360],
                  opacity: [0, 1, 0],
                }}
                transition={{
                  duration: 3,
                  delay: i * 0.1,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
            ))}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function CelebrationAnimations({
  celebrations,
  onCelebrationComplete,
}: CelebrationAnimationsProps) {
  const [activeCelebrations, setActiveCelebrations] = React.useState<{
    [key: number]: CelebrationConfig;
  }>({});

  React.useEffect(() => {
    celebrations.forEach((celebration, index) => {
      if (!activeCelebrations[index]) {
        setActiveCelebrations(prev => ({
          ...prev,
          [index]: celebration,
        }));

        // Auto-remove after duration
        setTimeout(() => {
          setActiveCelebrations(prev => {
            const newActive = { ...prev };
            delete newActive[index];
            return newActive;
          });
          onCelebrationComplete?.(celebration);
        }, celebration.duration);
      }
    });
  }, [celebrations, activeCelebrations, onCelebrationComplete]);

  const handleCloseCelebration = (index: number) => {
    const celebration = activeCelebrations[index];
    setActiveCelebrations(prev => {
      const newActive = { ...prev };
      delete newActive[index];
      return newActive;
    });
    if (celebration) {
      onCelebrationComplete?.(celebration);
    }
  };

  return (
    <>
      {Object.entries(activeCelebrations).map(([index, celebration]) => (
        <React.Fragment key={index}>
          {/* Background Effects */}
          {celebration.showConfetti && (
            <Confetti intensity={celebration.intensity} />
          )}
          
          {celebration.intensity === 'epic' && <Fireworks />}
          
          {celebration.intensity !== 'low' && (
            <SparkleEffect count={celebration.intensity === 'epic' ? 50 : 30} />
          )}

          {/* Celebration UI */}
          {celebration.showModal && (
            <CelebrationModal
              celebration={celebration}
              isVisible={true}
              onClose={() => handleCloseCelebration(Number(index))}
            />
          )}

          {celebration.showToast && !celebration.showModal && (
            <CelebrationToast
              celebration={celebration}
              isVisible={true}
              onClose={() => handleCloseCelebration(Number(index))}
            />
          )}

          {!celebration.showModal && !celebration.showToast && (
            <FloatingAchievement
              celebration={celebration}
              isVisible={true}
              onClose={() => handleCloseCelebration(Number(index))}
            />
          )}
        </React.Fragment>
      ))}
    </>
  );
}

// Celebration Trigger Hook
export function useCelebration() {
  const [celebrations, setCelebrations] = React.useState<CelebrationConfig[]>([]);

  const triggerCelebration = React.useCallback((config: Partial<CelebrationConfig>) => {
    const celebration: CelebrationConfig = {
      type: 'achievement_unlock',
      duration: 3000,
      intensity: 'medium',
      sound: false,
      haptic: false,
      showModal: false,
      showToast: true,
      showConfetti: true,
      ...config,
    };

    setCelebrations(prev => [...prev, celebration]);
  }, []);

  const clearCelebrations = React.useCallback(() => {
    setCelebrations([]);
  }, []);

  const handleCelebrationComplete = React.useCallback((celebration: CelebrationConfig) => {
    setCelebrations(prev => prev.filter(c => c !== celebration));
  }, []);

  return {
    celebrations,
    triggerCelebration,
    clearCelebrations,
    handleCelebrationComplete,
  };
}

// Quick celebration triggers
export const celebrationTriggers = {
  achievementUnlocked: (intensity: CelebrationConfig['intensity'] = 'medium') => ({
    type: 'achievement_unlock' as const,
    duration: 4000,
    intensity,
    showModal: true,
    showConfetti: true,
  }),

  badgeEarned: (intensity: CelebrationConfig['intensity'] = 'medium') => ({
    type: 'badge_earned' as const,
    duration: 3000,
    intensity,
    showToast: true,
    showConfetti: true,
  }),

  levelUp: (intensity: CelebrationConfig['intensity'] = 'high') => ({
    type: 'level_up' as const,
    duration: 5000,
    intensity,
    showModal: true,
    showConfetti: true,
  }),

  streakMilestone: (intensity: CelebrationConfig['intensity'] = 'medium') => ({
    type: 'streak_milestone' as const,
    duration: 3000,
    intensity,
    showToast: true,
    showConfetti: true,
  }),

  challengeComplete: (intensity: CelebrationConfig['intensity'] = 'high') => ({
    type: 'challenge_complete' as const,
    duration: 4000,
    intensity,
    showModal: true,
    showConfetti: true,
  }),

  milestoneReached: (intensity: CelebrationConfig['intensity'] = 'medium') => ({
    type: 'milestone_reached' as const,
    duration: 3000,
    intensity,
    showToast: true,
    showConfetti: true,
  }),

  firstTime: (intensity: CelebrationConfig['intensity'] = 'high') => ({
    type: 'first_time' as const,
    duration: 4000,
    intensity,
    showModal: true,
    showConfetti: true,
  }),

  rareEvent: (intensity: CelebrationConfig['intensity'] = 'epic') => ({
    type: 'rare_event' as const,
    duration: 6000,
    intensity,
    showModal: true,
    showConfetti: true,
  }),
};