import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  DollarSign, 
  PiggyBank, 
  Shield, 
  GraduationCap, 
  Heart,
  Building2,
  Eye,
  Settings
} from 'lucide-react';
import { 
  RetirementAccount, 
  AccountType, 
  AccountPerformance, 
  OptimizationSuggestion,
  AccountCardProps,
  TaxTreatment 
} from '@/types/accounts';

const getAccountTypeConfig = (accountType: AccountType) => {
  const configs = {
    [AccountType.TRADITIONAL_401K]: {
      icon: Building2,
      color: 'bg-blue-100 text-blue-800 border-blue-200',
      bgColor: 'bg-blue-50',
      name: '401(k) Traditional',
      description: 'Tax-deferred retirement savings'
    },
    [AccountType.ROTH_401K]: {
      icon: Building2,
      color: 'bg-purple-100 text-purple-800 border-purple-200',
      bgColor: 'bg-purple-50',
      name: '401(k) Roth',
      description: 'Tax-free retirement growth'
    },
    [AccountType.TRADITIONAL_IRA]: {
      icon: PiggyBank,
      color: 'bg-green-100 text-green-800 border-green-200',
      bgColor: 'bg-green-50',
      name: 'Traditional IRA',
      description: 'Individual retirement account'
    },
    [AccountType.ROTH_IRA]: {
      icon: PiggyBank,
      color: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      bgColor: 'bg-emerald-50',
      name: 'Roth IRA',
      description: 'Tax-free retirement savings'
    },
    [AccountType.HSA]: {
      icon: Heart,
      color: 'bg-red-100 text-red-800 border-red-200',
      bgColor: 'bg-red-50',
      name: 'Health Savings Account',
      description: 'Triple tax advantage'
    },
    [AccountType.EDUCATION_529]: {
      icon: GraduationCap,
      color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      bgColor: 'bg-yellow-50',
      name: '529 Education Plan',
      description: 'Education savings plan'
    },
    [AccountType.TAXABLE]: {
      icon: DollarSign,
      color: 'bg-gray-100 text-gray-800 border-gray-200',
      bgColor: 'bg-gray-50',
      name: 'Taxable Account',
      description: 'Brokerage investment account'
    },
    [AccountType.SEP_IRA]: {
      icon: Shield,
      color: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      bgColor: 'bg-indigo-50',
      name: 'SEP IRA',
      description: 'Self-employed retirement plan'
    },
    [AccountType.SIMPLE_IRA]: {
      icon: Shield,
      color: 'bg-cyan-100 text-cyan-800 border-cyan-200',
      bgColor: 'bg-cyan-50',
      name: 'SIMPLE IRA',
      description: 'Small business retirement plan'
    },
    [AccountType.PENSION]: {
      icon: Building2,
      color: 'bg-orange-100 text-orange-800 border-orange-200',
      bgColor: 'bg-orange-50',
      name: 'Pension Plan',
      description: 'Defined benefit retirement plan'
    }
  };

  return configs[accountType] || configs[AccountType.TAXABLE];
};

const getTaxTreatmentBadge = (taxTreatment: TaxTreatment) => {
  const treatments = {
    [TaxTreatment.TAX_DEFERRED]: {
      label: 'Tax Deferred',
      color: 'bg-blue-100 text-blue-800'
    },
    [TaxTreatment.TAX_FREE]: {
      label: 'Tax Free',
      color: 'bg-green-100 text-green-800'
    },
    [TaxTreatment.TRIPLE_TAX_ADVANTAGE]: {
      label: 'Triple Tax Advantage',
      color: 'bg-purple-100 text-purple-800'
    },
    [TaxTreatment.AFTER_TAX]: {
      label: 'After Tax',
      color: 'bg-gray-100 text-gray-800'
    }
  };

  return treatments[taxTreatment] || treatments[TaxTreatment.AFTER_TAX];
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
  return `${(value * 100).toFixed(2)}%`;
};

const AccountCard: React.FC<AccountCardProps> = ({
  account,
  performance,
  suggestions = [],
  onViewDetails,
  onOptimize
}) => {
  const accountConfig = getAccountTypeConfig(account.account_type);
  const taxTreatment = getTaxTreatmentBadge(account.tax_treatment);
  const IconComponent = accountConfig.icon;

  const highPrioritySuggestions = suggestions.filter(s => s.priority === 'high');
  const hasLoan = account.loan_balance && account.loan_balance > 0;
  const vestedPercentage = account.vested_balance && account.current_balance 
    ? (account.vested_balance / account.current_balance) * 100 
    : 100;

  return (
    <Card 
      id={`account-card-${account.id}`}
      className={`transition-all duration-200 hover:shadow-md border-l-4 ${accountConfig.color} ${accountConfig.bgColor}`}
    >
      <CardHeader id={`account-header-${account.id}`} className="pb-4">
        <div id={`account-title-section-${account.id}`} className="flex items-start justify-between">
          <div id={`account-info-${account.id}`} className="flex items-start space-x-3">
            <div id={`account-icon-${account.id}`} className={`p-2 rounded-lg ${accountConfig.color}`}>
              <IconComponent className="h-5 w-5" />
            </div>
            <div id={`account-details-${account.id}`}>
              <CardTitle id={`account-name-${account.id}`} className="text-lg font-semibold text-gray-900">
                {account.account_name}
              </CardTitle>
              <p id={`account-description-${account.id}`} className="text-sm text-gray-600 mt-1">
                {accountConfig.description}
              </p>
              <div id={`account-badges-${account.id}`} className="flex items-center space-x-2 mt-2">
                <Badge id={`account-type-badge-${account.id}`} className={accountConfig.color}>
                  {accountConfig.name}
                </Badge>
                <Badge id={`tax-treatment-badge-${account.id}`} className={taxTreatment.color}>
                  {taxTreatment.label}
                </Badge>
              </div>
            </div>
          </div>
          <div id={`account-actions-${account.id}`} className="flex space-x-2">
            {onViewDetails && (
              <Button 
                id={`view-details-btn-${account.id}`}
                variant="outline" 
                size="sm"
                onClick={() => onViewDetails(account.id)}
              >
                <Eye className="h-4 w-4" />
              </Button>
            )}
            {onOptimize && (
              <Button 
                id={`optimize-btn-${account.id}`}
                variant="outline" 
                size="sm"
                onClick={() => onOptimize(account.id)}
              >
                <Settings className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent id={`account-content-${account.id}`} className="space-y-4">
        {/* Balance Information */}
        <div id={`balance-section-${account.id}`} className="grid grid-cols-2 gap-4">
          <div id={`current-balance-${account.id}`} className="space-y-2">
            <p className="text-sm font-medium text-gray-600">Current Balance</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(account.current_balance)}
            </p>
          </div>
          
          {account.vested_balance && account.vested_balance !== account.current_balance && (
            <div id={`vested-balance-${account.id}`} className="space-y-2">
              <p className="text-sm font-medium text-gray-600">Vested Balance</p>
              <p className="text-xl font-semibold text-gray-800">
                {formatCurrency(account.vested_balance)}
              </p>
              <div id={`vesting-progress-${account.id}`} className="space-y-1">
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Vesting Progress</span>
                  <span>{vestedPercentage.toFixed(1)}%</span>
                </div>
                <Progress value={vestedPercentage} className="h-2" />
              </div>
            </div>
          )}
        </div>

        {/* Performance Information */}
        {performance && (
          <div id={`performance-section-${account.id}`} className="border-t pt-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div id={`ytd-return-${account.id}`}>
                <p className="text-xs text-gray-500">YTD Return</p>
                <div className="flex items-center justify-center space-x-1">
                  {performance.ytd_return_percentage >= 0 ? (
                    <TrendingUp className="h-3 w-3 text-green-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-500" />
                  )}
                  <span className={`text-sm font-semibold ${
                    performance.ytd_return_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatPercentage(performance.ytd_return_percentage)}
                  </span>
                </div>
              </div>
              
              <div id={`one-year-return-${account.id}`}>
                <p className="text-xs text-gray-500">1 Year</p>
                <div className="flex items-center justify-center space-x-1">
                  {performance.one_year_return >= 0 ? (
                    <TrendingUp className="h-3 w-3 text-green-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-500" />
                  )}
                  <span className={`text-sm font-semibold ${
                    performance.one_year_return >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatPercentage(performance.one_year_return)}
                  </span>
                </div>
              </div>
              
              <div id={`total-return-${account.id}`}>
                <p className="text-xs text-gray-500">Total Return</p>
                <div className="flex items-center justify-center space-x-1">
                  {performance.total_return_percentage >= 0 ? (
                    <TrendingUp className="h-3 w-3 text-green-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-500" />
                  )}
                  <span className={`text-sm font-semibold ${
                    performance.total_return_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatPercentage(performance.total_return_percentage)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loan Information */}
        {hasLoan && (
          <div id={`loan-section-${account.id}`} className="border-t pt-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <p className="text-sm font-medium text-yellow-800">Outstanding Loan</p>
              </div>
              <p className="text-lg font-semibold text-yellow-900">
                {formatCurrency(account.loan_balance!)}
              </p>
              {account.loan_details && (
                <div className="mt-2 text-xs text-yellow-700">
                  <p>Interest Rate: {formatPercentage(account.loan_details.interest_rate)}</p>
                  <p>Monthly Payment: {formatCurrency(account.loan_details.monthly_payment)}</p>
                  <p>Remaining Payments: {account.loan_details.remaining_payments}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Institution Information */}
        {account.financial_institution && (
          <div id={`institution-section-${account.id}`} className="border-t pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Financial Institution</p>
                <p className="text-sm font-medium text-gray-900">
                  {account.financial_institution}
                </p>
              </div>
              {account.account_number && (
                <div className="text-right">
                  <p className="text-xs text-gray-500">Account</p>
                  <p className="text-sm font-medium text-gray-900">
                    ****{account.account_number.slice(-4)}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* High Priority Suggestions */}
        {highPrioritySuggestions.length > 0 && (
          <div id={`suggestions-section-${account.id}`} className="border-t pt-4">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-orange-600" />
                <p className="text-sm font-medium text-orange-800">
                  Optimization Opportunities ({highPrioritySuggestions.length})
                </p>
              </div>
              <div className="space-y-2">
                {highPrioritySuggestions.slice(0, 2).map((suggestion) => (
                  <div key={suggestion.id} className="text-sm text-orange-700">
                    <p className="font-medium">{suggestion.title}</p>
                    {suggestion.potential_benefit && (
                      <p className="text-xs">
                        Potential benefit: {formatCurrency(suggestion.potential_benefit)}
                      </p>
                    )}
                  </div>
                ))}
                {highPrioritySuggestions.length > 2 && (
                  <p className="text-xs text-orange-600">
                    +{highPrioritySuggestions.length - 2} more suggestions
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Status Indicators */}
        <div id={`status-section-${account.id}`} className="border-t pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                {account.is_active ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-green-700">Active</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                    <span className="text-sm text-red-700">Inactive</span>
                  </>
                )}
              </div>
              
              {account.date_opened && (
                <div>
                  <span className="text-xs text-gray-500">
                    Opened {new Date(account.date_opened).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
            
            <div className="text-right">
              <p className="text-xs text-gray-500">Last Updated</p>
              <p className="text-xs text-gray-700">
                {new Date(account.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AccountCard;