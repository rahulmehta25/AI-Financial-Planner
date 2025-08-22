'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle, 
  Circle, 
  Clock, 
  Target, 
  TrendingUp, 
  DollarSign,
  PiggyBank,
  CreditCard,
  Shield,
  Calendar
} from 'lucide-react';
import { Milestone, MilestoneCategory } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface MilestoneTrackerProps {
  milestones: Milestone[];
  onMilestoneClick?: (milestone: Milestone) => void;
  showProgress?: boolean;
  groupByCategory?: boolean;
}

const categoryConfig: Record<MilestoneCategory, {
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
}> = {
  savings_amount: {
    icon: PiggyBank,
    color: 'from-green-400 to-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
  },
  investment_growth: {
    icon: TrendingUp,
    color: 'from-blue-400 to-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
  },
  debt_reduction: {
    icon: CreditCard,
    color: 'from-red-400 to-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
  },
  budget_adherence: {
    icon: Target,
    color: 'from-purple-400 to-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    textColor: 'text-purple-800',
  },
  goal_progress: {
    icon: Calendar,
    color: 'from-orange-400 to-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-800',
  },
  emergency_fund: {
    icon: Shield,
    color: 'from-indigo-400 to-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    textColor: 'text-indigo-800',
  },
};

function MilestoneCard({ 
  milestone, 
  onClick,
  showProgress = true 
}: { 
  milestone: Milestone;
  onClick?: (milestone: Milestone) => void;
  showProgress?: boolean;
}) {
  const config = categoryConfig[milestone.category];
  const Icon = config.icon;
  const progress = (milestone.currentValue / milestone.targetValue) * 100;
  const isCompleted = milestone.isCompleted;
  const isOverdue = milestone.deadline && new Date() > new Date(milestone.deadline) && !isCompleted;

  const formatValue = (value: number, unit: string) => {
    if (unit === '$' || unit === 'USD') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    }
    return `${value.toLocaleString()} ${unit}`;
  };

  return (
    <motion.div
      id={`milestone-card-${milestone.id}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="cursor-pointer"
      onClick={() => onClick?.(milestone)}
    >
      <Card
        className={`
          relative overflow-hidden transition-all duration-300 hover:shadow-md
          ${config.bgColor} ${config.borderColor}
          ${isCompleted ? 'ring-2 ring-green-300 ring-opacity-50' : ''}
          ${isOverdue ? 'ring-2 ring-red-300 ring-opacity-50' : ''}
        `}
      >
        {/* Status Indicator */}
        <div
          id={`milestone-status-${milestone.id}`}
          className="absolute top-3 right-3"
        >
          {isCompleted ? (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="text-green-500"
            >
              <CheckCircle className="w-6 h-6" />
            </motion.div>
          ) : isOverdue ? (
            <Clock className="w-6 h-6 text-red-500" />
          ) : (
            <Circle className="w-6 h-6 text-gray-400" />
          )}
        </div>

        <CardContent className="p-6">
          <div id={`milestone-content-${milestone.id}`} className="space-y-4">
            {/* Header */}
            <div className="flex items-start space-x-3">
              <div
                id={`milestone-icon-${milestone.id}`}
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
                  id={`milestone-title-${milestone.id}`}
                  className="font-semibold text-lg text-gray-900"
                >
                  {milestone.title}
                </h3>
                <p
                  id={`milestone-description-${milestone.id}`}
                  className="text-sm text-gray-600 mt-1"
                >
                  {milestone.description}
                </p>
              </div>
            </div>

            {/* Progress */}
            {showProgress && (
              <div id={`milestone-progress-${milestone.id}`} className="space-y-3">
                <div className="flex justify-between items-end">
                  <div className="space-y-1">
                    <div className="text-sm text-gray-600">Current Progress</div>
                    <div className="text-2xl font-bold text-gray-900">
                      {formatValue(milestone.currentValue, milestone.unit)}
                    </div>
                  </div>
                  <div className="text-right space-y-1">
                    <div className="text-sm text-gray-600">Target</div>
                    <div className="text-lg font-semibold text-gray-700">
                      {formatValue(milestone.targetValue, milestone.unit)}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Progress</span>
                    <span className="font-medium">
                      {Math.min(100, Math.round(progress))}%
                    </span>
                  </div>
                  <Progress 
                    value={Math.min(100, progress)} 
                    className="h-3"
                  />
                </div>
              </div>
            )}

            {/* Badges and Meta */}
            <div id={`milestone-meta-${milestone.id}`} className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge
                  variant="outline"
                  className={`${config.bgColor} ${config.textColor} ${config.borderColor} capitalize`}
                >
                  {milestone.category.replace('_', ' ')}
                </Badge>

                {milestone.points > 0 && (
                  <Badge variant="outline" className="bg-yellow-50 text-yellow-800 border-yellow-200">
                    {milestone.points} pts
                  </Badge>
                )}

                {isCompleted && (
                  <Badge className="bg-green-500 text-white">
                    Completed
                  </Badge>
                )}

                {isOverdue && (
                  <Badge variant="destructive">
                    Overdue
                  </Badge>
                )}
              </div>

              {/* Deadline */}
              {milestone.deadline && (
                <div
                  id={`milestone-deadline-${milestone.id}`}
                  className="flex items-center space-x-2 text-sm"
                >
                  <Calendar className="w-4 h-4 text-gray-500" />
                  <span className={isOverdue ? 'text-red-600 font-medium' : 'text-gray-600'}>
                    Due: {new Date(milestone.deadline).toLocaleDateString()}
                  </span>
                </div>
              )}

              {/* Completion Date */}
              {isCompleted && milestone.completedAt && (
                <div
                  id={`milestone-completed-${milestone.id}`}
                  className="flex items-center space-x-2 text-sm text-green-600"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>
                    Completed on {new Date(milestone.completedAt).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default function MilestoneTracker({
  milestones,
  onMilestoneClick,
  showProgress = true,
  groupByCategory = false,
}: MilestoneTrackerProps) {
  if (groupByCategory) {
    const groupedMilestones = milestones.reduce((groups, milestone) => {
      const category = milestone.category;
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(milestone);
      return groups;
    }, {} as Record<MilestoneCategory, Milestone[]>);

    return (
      <div id="milestone-tracker-grouped" className="space-y-8">
        {Object.entries(groupedMilestones).map(([category, categoryMilestones]) => {
          const config = categoryConfig[category as MilestoneCategory];
          const Icon = config.icon;

          return (
            <div key={category} className="space-y-4">
              <div className="flex items-center space-x-3">
                <Icon className={`w-6 h-6 ${config.textColor}`} />
                <h2 className="text-xl font-semibold capitalize">
                  {category.replace('_', ' ')}
                </h2>
                <Badge variant="outline" className="ml-auto">
                  {categoryMilestones.length} milestones
                </Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categoryMilestones.map(milestone => (
                  <MilestoneCard
                    key={milestone.id}
                    milestone={milestone}
                    onClick={onMilestoneClick}
                    showProgress={showProgress}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div
      id="milestone-tracker"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      {milestones.map(milestone => (
        <MilestoneCard
          key={milestone.id}
          milestone={milestone}
          onClick={onMilestoneClick}
          showProgress={showProgress}
        />
      ))}
    </div>
  );
}

// Milestone Summary Component
interface MilestoneSummaryProps {
  milestones: Milestone[];
  className?: string;
}

export function MilestoneSummary({ milestones, className }: MilestoneSummaryProps) {
  const completedCount = milestones.filter(m => m.isCompleted).length;
  const totalCount = milestones.length;
  const overdueCount = milestones.filter(m => 
    m.deadline && new Date() > new Date(m.deadline) && !m.isCompleted
  ).length;
  const totalPoints = milestones
    .filter(m => m.isCompleted)
    .reduce((sum, m) => sum + m.points, 0);

  const categoryStats = milestones.reduce((stats, milestone) => {
    const category = milestone.category;
    if (!stats[category]) {
      stats[category] = { total: 0, completed: 0 };
    }
    stats[category].total += 1;
    if (milestone.isCompleted) {
      stats[category].completed += 1;
    }
    return stats;
  }, {} as Record<string, { total: number; completed: number }>);

  return (
    <Card id="milestone-summary" className={className}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Target className="w-5 h-5" />
          <span>Milestone Progress</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{completedCount}</div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{totalCount}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{overdueCount}</div>
            <div className="text-sm text-gray-600">Overdue</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{totalPoints}</div>
            <div className="text-sm text-gray-600">Points</div>
          </div>
        </div>

        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span className="font-medium">
              {totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0}%
            </span>
          </div>
          <Progress 
            value={totalCount > 0 ? (completedCount / totalCount) * 100 : 0} 
            className="h-3"
          />
        </div>

        {/* Category Breakdown */}
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">By Category</h4>
          {Object.entries(categoryStats).map(([category, stats]) => {
            const config = categoryConfig[category as MilestoneCategory];
            const Icon = config.icon;
            const progress = stats.total > 0 ? (stats.completed / stats.total) * 100 : 0;

            return (
              <div key={category} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Icon className={`w-4 h-4 ${config.textColor}`} />
                    <span className="text-sm capitalize">
                      {category.replace('_', ' ')}
                    </span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {stats.completed}/{stats.total}
                  </span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// Quick Add Milestone Component
interface QuickAddMilestoneProps {
  onAdd: (milestone: Omit<Milestone, 'id'>) => void;
  categories: MilestoneCategory[];
}

export function QuickAddMilestone({ onAdd, categories }: QuickAddMilestoneProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [formData, setFormData] = React.useState({
    title: '',
    description: '',
    category: 'savings_amount' as MilestoneCategory,
    targetValue: 0,
    unit: '$',
    deadline: '',
    points: 100,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const milestone: Omit<Milestone, 'id'> = {
      ...formData,
      currentValue: 0,
      icon: categoryConfig[formData.category].icon.name,
      color: categoryConfig[formData.category].textColor,
      isCompleted: false,
      deadline: formData.deadline ? new Date(formData.deadline) : undefined,
    };

    onAdd(milestone);
    setIsOpen(false);
    setFormData({
      title: '',
      description: '',
      category: 'savings_amount',
      targetValue: 0,
      unit: '$',
      deadline: '',
      points: 100,
    });
  };

  if (!isOpen) {
    return (
      <Card
        id="quick-add-milestone-trigger"
        className="border-dashed cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsOpen(true)}
      >
        <CardContent className="p-6 text-center">
          <div className="space-y-2">
            <div className="w-12 h-12 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
              <Target className="w-6 h-6 text-gray-600" />
            </div>
            <h3 className="font-medium text-gray-900">Add New Milestone</h3>
            <p className="text-sm text-gray-600">Set a new financial goal to track</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card id="quick-add-milestone-form">
      <CardHeader>
        <CardTitle>Add New Milestone</CardTitle>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full p-2 border rounded-md"
              placeholder="e.g., Save for emergency fund"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full p-2 border rounded-md"
              placeholder="Describe your milestone..."
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  category: e.target.value as MilestoneCategory 
                }))}
                className="w-full p-2 border rounded-md"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Target Value</label>
              <input
                type="number"
                value={formData.targetValue}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  targetValue: Number(e.target.value) 
                }))}
                className="w-full p-2 border rounded-md"
                min="0"
                step="0.01"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Unit</label>
              <input
                type="text"
                value={formData.unit}
                onChange={(e) => setFormData(prev => ({ ...prev, unit: e.target.value }))}
                className="w-full p-2 border rounded-md"
                placeholder="$, days, etc."
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Deadline (Optional)</label>
              <input
                type="date"
                value={formData.deadline}
                onChange={(e) => setFormData(prev => ({ ...prev, deadline: e.target.value }))}
                className="w-full p-2 border rounded-md"
              />
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Add Milestone
            </button>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}