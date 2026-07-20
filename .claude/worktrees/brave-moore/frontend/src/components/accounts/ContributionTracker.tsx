import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  DollarSign,
  Target,
  Gift,
  Calendar,
  Calculator,
  Plus
} from 'lucide-react';
import { 
  ContributionProgress, 
  AccountType, 
  ContributionTrackerProps 
} from '@/types/accounts';

const getAccountTypeConfig = (accountType: AccountType) => {
  const configs = {
    [AccountType.TRADITIONAL_401K]: {
      name: '401(k) Traditional',
      color: 'bg-blue-100 text-blue-800 border-blue-200',
      icon: '🏢'
    },
    [AccountType.ROTH_401K]: {
      name: '401(k) Roth',
      color: 'bg-purple-100 text-purple-800 border-purple-200',
      icon: '🏢'
    },
    [AccountType.TRADITIONAL_IRA]: {
      name: 'Traditional IRA',
      color: 'bg-green-100 text-green-800 border-green-200',
      icon: '🏦'
    },
    [AccountType.ROTH_IRA]: {
      name: 'Roth IRA',
      color: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      icon: '🏦'
    },
    [AccountType.HSA]: {
      name: 'HSA',
      color: 'bg-red-100 text-red-800 border-red-200',
      icon: '❤️'
    },
    [AccountType.EDUCATION_529]: {
      name: '529 Plan',
      color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      icon: '🎓'
    },
    [AccountType.SEP_IRA]: {
      name: 'SEP IRA',
      color: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      icon: '🛡️'
    },
    [AccountType.SIMPLE_IRA]: {
      name: 'SIMPLE IRA',
      color: 'bg-cyan-100 text-cyan-800 border-cyan-200',
      icon: '🛡️'
    }
  };

  return configs[accountType] || {
    name: accountType.replace('_', ' '),
    color: 'bg-gray-100 text-gray-800 border-gray-200',
    icon: '💼'
  };
};

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatPercentage = (value: number) => {
  return `${value.toFixed(1)}%`;
};

const getProgressStatus = (progress: ContributionProgress) => {
  if (progress.progress_percentage >= 100) {
    return { status: 'complete', color: 'text-green-600', icon: CheckCircle };
  } else if (progress.progress_percentage >= 75) {
    return { status: 'on-track', color: 'text-blue-600', icon: TrendingUp };
  } else if (progress.months_remaining <= 3) {
    return { status: 'at-risk', color: 'text-orange-600', icon: Clock };
  } else {
    return { status: 'behind', color: 'text-red-600', icon: AlertCircle };
  }
};

const ContributionCard: React.FC<{
  progress: ContributionProgress;
  taxYear: number;
  onContribute?: (accountType: AccountType) => void;
}> = ({ progress, taxYear, onContribute }) => {
  const config = getAccountTypeConfig(progress.account_type);
  const progressStatus = getProgressStatus(progress);
  const StatusIcon = progressStatus.icon;

  const totalLimit = progress.catch_up_eligible && progress.catch_up_limit
    ? progress.annual_limit + progress.catch_up_limit
    : progress.annual_limit;

  const employerMatchData = progress.employer_match_available && {
    available: progress.employer_match_available,
    utilized: progress.employer_match_utilized || 0,
    remaining: progress.employer_match_available - (progress.employer_match_utilized || 0),
    percentage: progress.employer_match_utilized 
      ? (progress.employer_match_utilized / progress.employer_match_available) * 100 
      : 0
  };

  return (
    <Card 
      id={`contribution-card-${progress.account_type}`}
      className="transition-all duration-200 hover:shadow-md"
    >
      <CardHeader id={`contribution-header-${progress.account_type}`} className="pb-4">
        <div className="flex items-start justify-between">
          <div id={`contribution-title-${progress.account_type}`} className="flex items-start space-x-3">
            <div className="text-2xl">{config.icon}</div>
            <div>
              <CardTitle className="text-lg font-semibold text-gray-900">
                {config.name}
              </CardTitle>
              <div className="flex items-center space-x-2 mt-2">
                <Badge className={config.color}>
                  {taxYear} Contributions
                </Badge>
                {progress.catch_up_eligible && (
                  <Badge className="bg-orange-100 text-orange-800">
                    Catch-up Eligible
                  </Badge>
                )}
              </div>
            </div>
          </div>
          
          <div id={`contribution-status-${progress.account_type}`} className="flex items-center space-x-2">
            <StatusIcon className={`h-5 w-5 ${progressStatus.color}`} />
            {onContribute && (
              <Button
                id={`contribute-btn-${progress.account_type}`}
                size="sm"
                onClick={() => onContribute(progress.account_type)}
              >
                <Plus className="h-4 w-4 mr-1" />
                Contribute
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent id={`contribution-content-${progress.account_type}`} className="space-y-4">
        {/* Main Progress */}
        <div id={`main-progress-${progress.account_type}`} className="space-y-3">
          <div className="flex justify-between items-end">
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(progress.current_contributions)}
              </p>
              <p className="text-sm text-gray-600">
                of {formatCurrency(totalLimit)} limit
              </p>
            </div>
            <div className="text-right">
              <p className="text-lg font-semibold text-gray-700">
                {formatPercentage(progress.progress_percentage)}
              </p>
              <p className="text-xs text-gray-500">completed</p>
            </div>
          </div>
          
          <div id={`progress-bar-${progress.account_type}`} className="space-y-2">
            <Progress 
              value={Math.min(progress.progress_percentage, 100)} 
              className="h-3"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>Regular: {formatCurrency(progress.annual_limit)}</span>
              {progress.catch_up_eligible && progress.catch_up_limit && (
                <span>Catch-up: {formatCurrency(progress.catch_up_limit)}</span>
              )}
            </div>
          </div>
        </div>

        {/* Remaining Capacity */}
        <div id={`capacity-section-${progress.account_type}`} className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <div className="flex items-center space-x-1 mb-1">
              <Target className="h-4 w-4 text-gray-500" />
              <p className="text-sm font-medium text-gray-600">Remaining</p>
            </div>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(progress.remaining_capacity)}
            </p>
          </div>
          
          <div>
            <div className="flex items-center space-x-1 mb-1">
              <Calendar className="h-4 w-4 text-gray-500" />
              <p className="text-sm font-medium text-gray-600">Months Left</p>
            </div>
            <p className="text-lg font-semibold text-gray-900">
              {progress.months_remaining}
            </p>
          </div>
        </div>

        {/* Suggested Monthly Contribution */}
        {progress.suggested_monthly_contribution && (
          <div id={`suggestion-section-${progress.account_type}`} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <Calculator className="h-4 w-4 text-blue-600" />
              <p className="text-sm font-medium text-blue-800">Suggested Monthly</p>
            </div>
            <p className="text-xl font-bold text-blue-900">
              {formatCurrency(progress.suggested_monthly_contribution)}
            </p>
            <p className="text-xs text-blue-700 mt-1">
              To maximize your {taxYear} contribution limit
            </p>
          </div>
        )}

        {/* Employer Match Progress */}
        {employerMatchData && (
          <div id={`match-section-${progress.account_type}`} className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Gift className="h-4 w-4 text-green-600" />
                <p className="text-sm font-medium text-green-800">Employer Match</p>
              </div>
              <p className="text-sm font-semibold text-green-700">
                {formatPercentage(employerMatchData.percentage)}
              </p>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-green-700">
                  {formatCurrency(employerMatchData.utilized)}
                </span>
                <span className="text-green-600">
                  of {formatCurrency(employerMatchData.available)}
                </span>
              </div>
              <Progress 
                value={employerMatchData.percentage} 
                className="h-2"
              />
              {employerMatchData.remaining > 0 && (
                <p className="text-xs text-green-600">
                  {formatCurrency(employerMatchData.remaining)} match remaining
                </p>
              )}
            </div>
          </div>
        )}

        {/* Status Messages */}
        <div id={`status-messages-${progress.account_type}`}>
          {progress.progress_percentage >= 100 ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <p className="text-sm font-medium text-green-800">
                  Contribution limit reached for {taxYear}
                </p>
              </div>
            </div>
          ) : progress.months_remaining <= 2 ? (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-orange-600" />
                <p className="text-sm font-medium text-orange-800">
                  Time running out to maximize {taxYear} contributions
                </p>
              </div>
              {progress.suggested_monthly_contribution && (
                <p className="text-xs text-orange-700 mt-1">
                  Consider increasing monthly contributions to 
                  {formatCurrency(progress.suggested_monthly_contribution)}
                </p>
              )}
            </div>
          ) : progress.progress_percentage < 50 && progress.months_remaining <= 6 ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-yellow-600" />
                <p className="text-sm font-medium text-yellow-800">
                  Consider increasing contributions to maximize tax benefits
                </p>
              </div>
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
};

const ContributionTracker: React.FC<ContributionTrackerProps> = ({
  progress,
  taxYear,
  onContribute
}) => {
  const summaryStats = useMemo(() => {
    const totalContributions = progress.reduce((sum, p) => sum + p.current_contributions, 0);
    const totalLimits = progress.reduce((sum, p) => {
      const limit = p.catch_up_eligible && p.catch_up_limit 
        ? p.annual_limit + p.catch_up_limit
        : p.annual_limit;
      return sum + limit;
    }, 0);
    const totalRemaining = progress.reduce((sum, p) => sum + p.remaining_capacity, 0);
    const avgProgress = progress.reduce((sum, p) => sum + p.progress_percentage, 0) / progress.length;
    
    const completedAccounts = progress.filter(p => p.progress_percentage >= 100).length;
    const atRiskAccounts = progress.filter(p => 
      p.progress_percentage < 75 && p.months_remaining <= 3
    ).length;

    return {
      totalContributions,
      totalLimits,
      totalRemaining,
      avgProgress,
      completedAccounts,
      atRiskAccounts,
      totalAccounts: progress.length
    };
  }, [progress]);

  return (
    <div id="contribution-tracker-main" className="space-y-6">
      {/* Summary Cards */}
      <div id="contribution-summary" className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card id="total-contributions-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Contributed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(summaryStats.totalContributions)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="total-remaining-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Remaining Capacity</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(summaryStats.totalRemaining)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="average-progress-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Average Progress</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatPercentage(summaryStats.avgProgress)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="accounts-status-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summaryStats.completedAccounts}/{summaryStats.totalAccounts}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alert Section */}
      {summaryStats.atRiskAccounts > 0 && (
        <Card id="at-risk-alert" className="border-orange-200 bg-orange-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-sm font-medium text-orange-800">
                  Action Required: {summaryStats.atRiskAccounts} accounts need attention
                </p>
                <p className="text-xs text-orange-700">
                  Time is running out to maximize {taxYear} contributions
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Individual Account Progress */}
      <div id="individual-progress">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {taxYear} Contribution Progress
          </h3>
          <Badge className="bg-gray-100 text-gray-800">
            {progress.length} Accounts
          </Badge>
        </div>
        
        <div id="contribution-cards-grid" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {progress.map((accountProgress) => (
            <ContributionCard
              key={accountProgress.account_type}
              progress={accountProgress}
              taxYear={taxYear}
              onContribute={onContribute}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ContributionTracker;