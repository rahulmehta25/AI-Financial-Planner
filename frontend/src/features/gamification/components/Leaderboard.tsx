'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, 
  Medal, 
  Award, 
  Crown, 
  TrendingUp, 
  Users, 
  Clock,
  Star,
  Target,
  Flame,
  Calendar,
  ChevronUp,
  ChevronDown,
  Minus
} from 'lucide-react';
import { Leaderboard as LeaderboardType, LeaderboardEntry, LeaderboardType as LBType, LeaderboardPeriod } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface LeaderboardProps {
  leaderboards: LeaderboardType[];
  currentUserId?: string;
  showUserOnly?: boolean;
  maxEntries?: number;
  refreshInterval?: number;
}

const leaderboardTypeConfig: Record<LBType, {
  icon: React.ComponentType<any>;
  label: string;
  description: string;
  color: string;
  unit: string;
}> = {
  total_points: {
    icon: Star,
    label: 'Total Points',
    description: 'All-time points earned',
    color: 'text-yellow-600',
    unit: 'pts',
  },
  monthly_points: {
    icon: Calendar,
    label: 'Monthly Points',
    description: 'Points earned this month',
    color: 'text-blue-600',
    unit: 'pts',
  },
  achievements: {
    icon: Trophy,
    label: 'Achievements',
    description: 'Total achievements unlocked',
    color: 'text-purple-600',
    unit: '',
  },
  streak_length: {
    icon: Flame,
    label: 'Streak Length',
    description: 'Longest active streak',
    color: 'text-orange-600',
    unit: 'days',
  },
  challenges_completed: {
    icon: Target,
    label: 'Challenges',
    description: 'Challenges completed',
    color: 'text-green-600',
    unit: '',
  },
  savings_growth: {
    icon: TrendingUp,
    label: 'Savings Growth',
    description: 'Monthly savings increase',
    color: 'text-emerald-600',
    unit: '%',
  },
};

const periodConfig: Record<LeaderboardPeriod, {
  label: string;
  description: string;
}> = {
  weekly: { label: 'This Week', description: 'Weekly leaders' },
  monthly: { label: 'This Month', description: 'Monthly leaders' },
  quarterly: { label: 'This Quarter', description: 'Quarterly leaders' },
  yearly: { label: 'This Year', description: 'Yearly leaders' },
  all_time: { label: 'All Time', description: 'All-time leaders' },
};

function getRankIcon(rank: number) {
  switch (rank) {
    case 1:
      return <Crown className="w-5 h-5 text-yellow-500" />;
    case 2:
      return <Medal className="w-5 h-5 text-gray-400" />;
    case 3:
      return <Award className="w-5 h-5 text-amber-600" />;
    default:
      return <span className="text-lg font-bold text-gray-600">#{rank}</span>;
  }
}

function getRankColor(rank: number) {
  switch (rank) {
    case 1:
      return 'bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-200';
    case 2:
      return 'bg-gradient-to-r from-gray-50 to-gray-100 border-gray-200';
    case 3:
      return 'bg-gradient-to-r from-amber-50 to-amber-100 border-amber-200';
    default:
      return 'bg-white border-gray-200';
  }
}

function generateAnonymousName(userId: string, rank: number): string {
  const adjectives = [
    'Smart', 'Wise', 'Savvy', 'Clever', 'Brilliant', 'Strategic', 'Prudent', 'Astute',
    'Sharp', 'Keen', 'Resourceful', 'Skilled', 'Expert', 'Master', 'Pro', 'Elite'
  ];
  
  const nouns = [
    'Investor', 'Saver', 'Planner', 'Budgeter', 'Analyst', 'Strategist', 'Builder',
    'Achiever', 'Tracker', 'Optimizer', 'Guardian', 'Navigator', 'Pioneer', 'Champion'
  ];

  // Use userId as seed for consistent anonymization
  const seed = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const adjIndex = (seed + rank) % adjectives.length;
  const nounIndex = (seed * 2 + rank) % nouns.length;
  
  return `${adjectives[adjIndex]} ${nouns[nounIndex]}`;
}

function generateAnonymousAvatar(userId: string): string {
  const colors = ['bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500', 'bg-pink-500', 'bg-indigo-500'];
  const seed = userId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return colors[seed % colors.length];
}

interface LeaderboardEntryCardProps {
  entry: LeaderboardEntry;
  leaderboardType: LBType;
  isCurrentUser?: boolean;
  showChange?: boolean;
  animated?: boolean;
}

function LeaderboardEntryCard({
  entry,
  leaderboardType,
  isCurrentUser = false,
  showChange = false,
  animated = true,
}: LeaderboardEntryCardProps) {
  const config = leaderboardTypeConfig[leaderboardType];
  const rankColor = getRankColor(entry.rank);
  const rankIcon = getRankIcon(entry.rank);

  const anonymousName = generateAnonymousName(entry.id, entry.rank);
  const anonymousAvatar = generateAnonymousAvatar(entry.id);

  const cardVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        delay: entry.rank * 0.1,
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
      id={`leaderboard-entry-${entry.id}`}
      variants={animated ? cardVariants : undefined}
      initial={animated ? 'hidden' : undefined}
      animate={animated ? 'visible' : undefined}
      whileHover={animated ? 'hover' : undefined}
    >
      <Card
        className={`
          ${rankColor} transition-all duration-300 hover:shadow-md
          ${isCurrentUser ? 'ring-2 ring-blue-400 ring-opacity-50' : ''}
        `}
      >
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            {/* Rank */}
            <div
              id={`leaderboard-rank-${entry.id}`}
              className="flex-shrink-0 w-12 h-12 flex items-center justify-center"
            >
              {rankIcon}
            </div>

            {/* Avatar */}
            <div id={`leaderboard-avatar-${entry.id}`} className="flex-shrink-0">
              <Avatar className="w-10 h-10">
                {entry.avatar ? (
                  <AvatarImage src={entry.avatar} alt={anonymousName} />
                ) : (
                  <AvatarFallback className={anonymousAvatar}>
                    {anonymousName.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                )}
              </Avatar>
            </div>

            {/* User Info */}
            <div id={`leaderboard-user-info-${entry.id}`} className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-gray-900 truncate">
                  {isCurrentUser ? 'You' : anonymousName}
                </h3>
                {isCurrentUser && (
                  <Badge className="bg-blue-500 text-white text-xs">You</Badge>
                )}
              </div>
              
              <div className="flex items-center space-x-3 text-sm text-gray-600">
                <span>Level {entry.level}</span>
                <span>•</span>
                <span>{entry.achievements} achievements</span>
                <span>•</span>
                <span>{entry.badges} badges</span>
              </div>
            </div>

            {/* Score */}
            <div id={`leaderboard-score-${entry.id}`} className="text-right">
              <div className={`text-xl font-bold ${config.color}`}>
                {entry.points.toLocaleString()}
                {config.unit && <span className="text-sm ml-1">{config.unit}</span>}
              </div>
              
              {showChange && (
                <div className="flex items-center justify-end text-sm">
                  {/* Mock change indicator - would come from API */}
                  <ChevronUp className="w-4 h-4 text-green-500" />
                  <span className="text-green-600">+12</span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function Leaderboard({
  leaderboards,
  currentUserId,
  showUserOnly = false,
  maxEntries = 10,
  refreshInterval = 300000, // 5 minutes
}: LeaderboardProps) {
  const [selectedLeaderboard, setSelectedLeaderboard] = React.useState<LeaderboardType | null>(
    leaderboards[0] || null
  );
  const [lastUpdated, setLastUpdated] = React.useState<Date>(new Date());

  // Auto-refresh leaderboard data
  React.useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        setLastUpdated(new Date());
        // Here you would typically refetch leaderboard data
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshInterval]);

  if (!selectedLeaderboard) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Leaderboards Available</h3>
          <p className="text-gray-600">Check back later for leaderboard data.</p>
        </CardContent>
      </Card>
    );
  }

  const typeConfig = leaderboardTypeConfig[selectedLeaderboard.type];
  const periodConfig_selected = periodConfig[selectedLeaderboard.period];

  const displayEntries = showUserOnly && currentUserId
    ? selectedLeaderboard.entries.filter(e => e.id === currentUserId).slice(0, 1)
    : selectedLeaderboard.entries.slice(0, maxEntries);

  const currentUserEntry = currentUserId 
    ? selectedLeaderboard.entries.find(e => e.id === currentUserId)
    : null;

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
    <div id="leaderboard-container" className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <typeConfig.icon className={`w-6 h-6 ${typeConfig.color}`} />
              </div>
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <span>{typeConfig.label}</span>
                  <Badge variant="outline">{periodConfig_selected.label}</Badge>
                </CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  {typeConfig.description} • {periodConfig_selected.description}
                </p>
              </div>
            </div>

            <div className="text-right text-sm text-gray-500">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4" />
                <span>Updated {lastUpdated.toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Leaderboard Type Selector */}
      {leaderboards.length > 1 && (
        <Card>
          <CardContent className="p-4">
            <Tabs 
              value={selectedLeaderboard.id} 
              onValueChange={(id) => {
                const lb = leaderboards.find(l => l.id === id);
                if (lb) setSelectedLeaderboard(lb);
              }}
            >
              <TabsList className="grid w-full grid-cols-2 lg:grid-cols-3">
                {leaderboards.map(lb => {
                  const config = leaderboardTypeConfig[lb.type];
                  return (
                    <TabsTrigger key={lb.id} value={lb.id} className="flex items-center space-x-2">
                      <config.icon className="w-4 h-4" />
                      <span>{config.label}</span>
                    </TabsTrigger>
                  );
                })}
              </TabsList>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Current User Position (if not in top entries) */}
      {!showUserOnly && currentUserEntry && currentUserEntry.rank > maxEntries && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Your Position</CardTitle>
          </CardHeader>
          <CardContent>
            <LeaderboardEntryCard
              entry={currentUserEntry}
              leaderboardType={selectedLeaderboard.type}
              isCurrentUser={true}
              showChange={true}
              animated={true}
            />
          </CardContent>
        </Card>
      )}

      {/* Leaderboard Entries */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Top {showUserOnly ? 'Your' : ''} Performers</span>
            <Badge variant="outline" className="flex items-center space-x-1">
              <Users className="w-3 h-3" />
              <span>{selectedLeaderboard.entries.length} participants</span>
            </Badge>
          </CardTitle>
        </CardHeader>

        <CardContent>
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="space-y-3"
          >
            {displayEntries.map(entry => (
              <LeaderboardEntryCard
                key={entry.id}
                entry={entry}
                leaderboardType={selectedLeaderboard.type}
                isCurrentUser={entry.id === currentUserId}
                showChange={true}
                animated={true}
              />
            ))}
          </motion.div>

          {displayEntries.length === 0 && (
            <div className="text-center py-8">
              <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Entries Yet</h3>
              <p className="text-gray-600">
                Be the first to appear on the leaderboard!
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Leaderboard Stats */}
      <LeaderboardStats 
        leaderboard={selectedLeaderboard}
        currentUserId={currentUserId}
      />
    </div>
  );
}

// Leaderboard Stats Component
interface LeaderboardStatsProps {
  leaderboard: LeaderboardType;
  currentUserId?: string;
}

function LeaderboardStats({ leaderboard, currentUserId }: LeaderboardStatsProps) {
  const entries = leaderboard.entries;
  const totalParticipants = entries.length;
  const averageScore = totalParticipants > 0 
    ? Math.round(entries.reduce((sum, e) => sum + e.points, 0) / totalParticipants)
    : 0;
  const topScore = entries.length > 0 ? entries[0].points : 0;
  const currentUserEntry = currentUserId ? entries.find(e => e.id === currentUserId) : null;

  return (
    <Card id="leaderboard-stats">
      <CardHeader>
        <CardTitle>Leaderboard Statistics</CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{totalParticipants}</div>
            <div className="text-sm text-gray-600">Participants</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{topScore.toLocaleString()}</div>
            <div className="text-sm text-gray-600">Top Score</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{averageScore.toLocaleString()}</div>
            <div className="text-sm text-gray-600">Average</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {currentUserEntry ? `#${currentUserEntry.rank}` : 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Your Rank</div>
          </div>
        </div>

        {currentUserEntry && (
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-blue-900">Your Performance</h4>
                <p className="text-sm text-blue-700">
                  You're in the top {Math.round((currentUserEntry.rank / totalParticipants) * 100)}% of participants
                </p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-blue-600">
                  {currentUserEntry.points.toLocaleString()}
                </div>
                <div className="text-sm text-blue-700">
                  {topScore - currentUserEntry.points > 0 
                    ? `${(topScore - currentUserEntry.points).toLocaleString()} from #1`
                    : 'Leading!'
                  }
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}