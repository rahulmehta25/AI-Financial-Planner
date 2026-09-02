import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, 
  TrendingDown,
  Plus,
  BarChart3,
  Target,
  AlertCircle,
  CheckCircle,
  DollarSign,
  PieChart,
  Activity,
  Settings,
  RefreshCw,
  Download,
  Filter,
  Search,
  Calendar
} from 'lucide-react';

// Import our custom components
import AccountCard from '@/components/accounts/AccountCard';
import ContributionTracker from '@/components/accounts/ContributionTracker';
import TransactionList from '@/components/accounts/TransactionList';
import { PlaidLinkWithInstitutions } from '@/components/accounts/PlaidLinkButton';

// Import types
import {
  RetirementAccount,
  AccountType,
  TaxTreatment,
  AccountPerformance,
  OptimizationSuggestion,
  ContributionProgress,
  Transaction,
  TransactionFilters
} from '@/types/accounts';

// Mock data for demonstration
const mockAccounts: RetirementAccount[] = [
  {
    id: '1',
    user_id: 'user-1',
    account_type: AccountType.TRADITIONAL_401K,
    account_name: 'Company 401(k) Plan',
    financial_institution: 'Fidelity',
    tax_treatment: TaxTreatment.TAX_DEFERRED,
    is_active: true,
    current_balance: 125000,
    vested_balance: 108000,
    employer_name: 'Tech Corp',
    loan_balance: 0,
    created_at: '2022-01-15T00:00:00Z',
    updated_at: '2025-01-15T00:00:00Z',
    account_number: '****1234'
  },
  {
    id: '2',
    user_id: 'user-1',
    account_type: AccountType.ROTH_IRA,
    account_name: 'Roth IRA',
    financial_institution: 'Charles Schwab',
    tax_treatment: TaxTreatment.TAX_FREE,
    is_active: true,
    current_balance: 45000,
    created_at: '2020-03-10T00:00:00Z',
    updated_at: '2025-01-15T00:00:00Z',
    account_number: '****5678'
  },
  {
    id: '3',
    user_id: 'user-1',
    account_type: AccountType.HSA,
    account_name: 'Health Savings Account',
    financial_institution: 'HSA Bank',
    tax_treatment: TaxTreatment.TRIPLE_TAX_ADVANTAGE,
    is_active: true,
    current_balance: 8500,
    created_at: '2023-06-01T00:00:00Z',
    updated_at: '2025-01-15T00:00:00Z',
    account_number: '****9012'
  },
  {
    id: '4',
    user_id: 'user-1',
    account_type: AccountType.EDUCATION_529,
    account_name: 'Child Education Fund',
    financial_institution: 'Vanguard',
    tax_treatment: TaxTreatment.AFTER_TAX,
    is_active: true,
    current_balance: 25000,
    created_at: '2021-09-15T00:00:00Z',
    updated_at: '2025-01-15T00:00:00Z',
    account_number: '****3456'
  }
];

const mockPerformance: AccountPerformance[] = [
  {
    account_id: '1',
    total_return: 18500,
    total_return_percentage: 0.174,
    ytd_return: 2800,
    ytd_return_percentage: 0.023,
    one_year_return: 0.089,
    three_year_return: 0.127,
    five_year_return: 0.084,
    inception_return: 0.174,
    dividend_yield: 0.018,
    expense_ratio: 0.0075,
    last_updated: '2025-01-15T00:00:00Z'
  },
  {
    account_id: '2',
    total_return: 12000,
    total_return_percentage: 0.364,
    ytd_return: 1200,
    ytd_return_percentage: 0.027,
    one_year_return: 0.095,
    three_year_return: 0.142,
    five_year_return: 0.098,
    inception_return: 0.364,
    dividend_yield: 0.022,
    expense_ratio: 0.003,
    last_updated: '2025-01-15T00:00:00Z'
  }
];

const mockSuggestions: OptimizationSuggestion[] = [
  {
    id: '1',
    account_id: '1',
    type: 'contribution',
    priority: 'high',
    title: 'Maximize Employer Match',
    description: 'You\'re not maximizing your employer match. Consider increasing contributions to get the full $3,000 match.',
    potential_benefit: 3000,
    effort_required: 'low',
    action_items: [
      'Increase 401(k) contribution to 6% of salary',
      'Set up automatic contribution increases',
      'Review match calculation quarterly'
    ]
  },
  {
    id: '2',
    account_id: '2',
    type: 'tax',
    priority: 'medium',
    title: 'Consider Roth Conversion',
    description: 'Your current tax bracket may make a Roth conversion beneficial for long-term tax savings.',
    potential_benefit: 8500,
    effort_required: 'medium',
    action_items: [
      'Calculate conversion tax impact',
      'Consider converting $10,000 from Traditional IRA',
      'Plan conversion timing for lower tax years'
    ]
  },
  {
    id: '3',
    account_id: '3',
    type: 'contribution',
    priority: 'high',
    title: 'Maximize HSA Contributions',
    description: 'HSA offers triple tax advantage. Consider maximizing contributions for retirement healthcare costs.',
    potential_benefit: 2000,
    effort_required: 'low',
    action_items: [
      'Increase HSA contribution to $4,300 limit',
      'Invest HSA funds for long-term growth',
      'Keep receipts for future reimbursement'
    ]
  }
];

const mockContributionProgress: ContributionProgress[] = [
  {
    account_type: AccountType.TRADITIONAL_401K,
    current_contributions: 15000,
    annual_limit: 23500,
    catch_up_eligible: false,
    employer_match_available: 3000,
    employer_match_utilized: 2250,
    remaining_capacity: 8500,
    progress_percentage: 63.8,
    months_remaining: 4,
    suggested_monthly_contribution: 2125
  },
  {
    account_type: AccountType.ROTH_IRA,
    current_contributions: 4500,
    annual_limit: 7000,
    catch_up_eligible: false,
    remaining_capacity: 2500,
    progress_percentage: 64.3,
    months_remaining: 4,
    suggested_monthly_contribution: 625
  },
  {
    account_type: AccountType.HSA,
    current_contributions: 2800,
    annual_limit: 4300,
    catch_up_eligible: false,
    remaining_capacity: 1500,
    progress_percentage: 65.1,
    months_remaining: 4,
    suggested_monthly_contribution: 375
  }
];

const mockTransactions: Transaction[] = [
  {
    id: '1',
    account_id: '1',
    transaction_date: '2025-01-10T00:00:00Z',
    type: 'contribution',
    category: 'Employee Contribution',
    amount: 1250,
    description: 'Bi-weekly payroll contribution',
    balance_after: 125000
  },
  {
    id: '2',
    account_id: '1',
    transaction_date: '2025-01-10T00:00:00Z',
    type: 'contribution',
    category: 'Employer Match',
    amount: 625,
    description: 'Employer matching contribution',
    balance_after: 125625
  },
  {
    id: '3',
    account_id: '2',
    transaction_date: '2025-01-08T00:00:00Z',
    type: 'dividend',
    category: 'Dividend Income',
    amount: 85,
    description: 'VTSAX Dividend Distribution',
    balance_after: 45085
  },
  {
    id: '4',
    account_id: '3',
    transaction_date: '2025-01-05T00:00:00Z',
    type: 'contribution',
    category: 'HSA Contribution',
    amount: 350,
    description: 'Monthly HSA contribution',
    balance_after: 8500
  },
  {
    id: '5',
    account_id: '1',
    transaction_date: '2024-12-28T00:00:00Z',
    type: 'fee',
    category: 'Administrative Fee',
    amount: -25,
    description: 'Quarterly administrative fee',
    balance_after: 124375
  }
];

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

const AccountsManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [transactionFilters, setTransactionFilters] = useState<TransactionFilters>({});
  const [isLoading, setIsLoading] = useState(false);

  // Calculate portfolio summary
  const portfolioSummary = useMemo(() => {
    const totalBalance = mockAccounts.reduce((sum, account) => sum + account.current_balance, 0);
    const totalPerformance = mockPerformance.reduce((sum, perf) => sum + perf.total_return, 0);
    const totalPerformancePercentage = totalPerformance / totalBalance;
    const ytdPerformance = mockPerformance.reduce((sum, perf) => sum + perf.ytd_return, 0);
    const ytdPerformancePercentage = ytdPerformance / totalBalance;

    const highPrioritySuggestions = mockSuggestions.filter(s => s.priority === 'high').length;
    const totalPotentialBenefit = mockSuggestions.reduce((sum, s) => sum + (s.potential_benefit || 0), 0);

    return {
      totalBalance,
      totalPerformance,
      totalPerformancePercentage,
      ytdPerformance,
      ytdPerformancePercentage,
      accountCount: mockAccounts.length,
      activeAccounts: mockAccounts.filter(a => a.is_active).length,
      highPrioritySuggestions,
      totalPotentialBenefit
    };
  }, []);

  const handleAccountView = (accountId: string) => {
    setSelectedAccountId(accountId);
    setActiveTab('transactions');
  };

  const handleAccountOptimize = (accountId: string) => {
    setSelectedAccountId(accountId);
    setActiveTab('optimization');
  };

  const handlePlaidSuccess = (publicToken: string, metadata: any) => {
    console.log('Plaid link successful:', { publicToken, metadata });
    // In a real app, you would send this to your backend to exchange for access token
    // and fetch account data
  };

  const handleContribute = (accountType: AccountType) => {
    console.log('Navigate to contribution flow for:', accountType);
    // Navigate to contribution form or modal
  };

  const handleTransactionCategorize = (transactionId: string, category: string) => {
    console.log('Categorize transaction:', { transactionId, category });
    // Update transaction category
  };

  const filteredTransactions = selectedAccountId
    ? mockTransactions.filter(t => t.account_id === selectedAccountId)
    : mockTransactions;

  return (
    <div id="accounts-management-page" className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div id="page-header" className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Account Management</h1>
          <p className="text-gray-600 mt-1">
            Monitor and optimize your retirement and investment accounts
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Sync
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Account
          </Button>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div id="portfolio-summary" className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card id="total-balance-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Balance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(portfolioSummary.totalBalance)}
                </p>
                <div className="flex items-center space-x-1 mt-1">
                  {portfolioSummary.ytdPerformancePercentage >= 0 ? (
                    <TrendingUp className="h-3 w-3 text-green-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-500" />
                  )}
                  <span className={`text-xs ${
                    portfolioSummary.ytdPerformancePercentage >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatPercentage(portfolioSummary.ytdPerformancePercentage)} YTD
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="total-performance-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Gains</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(portfolioSummary.totalPerformance)}
                </p>
                <p className="text-xs text-green-600 mt-1">
                  {formatPercentage(portfolioSummary.totalPerformancePercentage)} return
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="accounts-count-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <PieChart className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Active Accounts</p>
                <p className="text-2xl font-bold text-gray-900">
                  {portfolioSummary.activeAccounts}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  of {portfolioSummary.accountCount} total accounts
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card id="optimization-card">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Optimization</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(portfolioSummary.totalPotentialBenefit)}
                </p>
                <p className="text-xs text-orange-600 mt-1">
                  {portfolioSummary.highPrioritySuggestions} high priority items
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* High Priority Alerts */}
      {portfolioSummary.highPrioritySuggestions > 0 && (
        <Alert id="high-priority-alert" className="border-orange-200 bg-orange-50">
          <AlertCircle className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800">
            <div className="flex items-center justify-between">
              <span>
                You have {portfolioSummary.highPrioritySuggestions} high-priority optimization opportunities 
                that could save you {formatCurrency(portfolioSummary.totalPotentialBenefit)}.
              </span>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setActiveTab('optimization')}
                className="border-orange-300 text-orange-700 hover:bg-orange-100"
              >
                Review Now
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList id="main-tabs" className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="contributions">Contributions</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
          <TabsTrigger value="connect">Connect</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Account Overview</h2>
              <Badge className="bg-gray-100 text-gray-800">
                {mockAccounts.length} Accounts
              </Badge>
            </div>
            
            <div id="accounts-grid" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {mockAccounts.map((account) => {
                const accountPerformance = mockPerformance.find(p => p.account_id === account.id);
                const accountSuggestions = mockSuggestions.filter(s => s.account_id === account.id);
                
                return (
                  <AccountCard
                    key={account.id}
                    account={account}
                    performance={accountPerformance}
                    suggestions={accountSuggestions}
                    onViewDetails={handleAccountView}
                    onOptimize={handleAccountOptimize}
                  />
                );
              })}
            </div>
          </div>
        </TabsContent>

        {/* Contributions Tab */}
        <TabsContent value="contributions" className="space-y-6">
          <ContributionTracker
            progress={mockContributionProgress}
            taxYear={2025}
            onContribute={handleContribute}
          />
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Transaction History</h2>
            {selectedAccountId && (
              <div className="flex items-center space-x-2">
                <Badge className="bg-blue-100 text-blue-800">
                  {mockAccounts.find(a => a.id === selectedAccountId)?.account_name}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedAccountId(null)}
                >
                  Show All Accounts
                </Button>
              </div>
            )}
          </div>

          <TransactionList
            accountId={selectedAccountId || undefined}
            transactions={filteredTransactions}
            loading={isLoading}
            hasMore={false}
            onCategorize={handleTransactionCategorize}
            filters={transactionFilters}
            onFilterChange={setTransactionFilters}
          />
        </TabsContent>

        {/* Optimization Tab */}
        <TabsContent value="optimization" className="space-y-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Optimization Suggestions</h2>
            <Badge className="bg-orange-100 text-orange-800">
              {mockSuggestions.length} Opportunities
            </Badge>
          </div>

          <div id="optimization-suggestions" className="space-y-4">
            {mockSuggestions.map((suggestion) => {
              const account = mockAccounts.find(a => a.id === suggestion.account_id);
              const priorityColors = {
                high: 'border-red-200 bg-red-50',
                medium: 'border-orange-200 bg-orange-50',
                low: 'border-yellow-200 bg-yellow-50'
              };

              return (
                <Card 
                  key={suggestion.id}
                  id={`suggestion-${suggestion.id}`}
                  className={priorityColors[suggestion.priority]}
                >
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg font-semibold">
                          {suggestion.title}
                        </CardTitle>
                        <p className="text-sm text-gray-600 mt-1">
                          {account?.account_name} • {account?.financial_institution}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={`${
                          suggestion.priority === 'high' ? 'bg-red-100 text-red-800' :
                          suggestion.priority === 'medium' ? 'bg-orange-100 text-orange-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {suggestion.priority.charAt(0).toUpperCase() + suggestion.priority.slice(1)}
                        </Badge>
                        {suggestion.potential_benefit && (
                          <Badge className="bg-green-100 text-green-800">
                            +{formatCurrency(suggestion.potential_benefit)}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent>
                    <p className="text-gray-700 mb-4">{suggestion.description}</p>
                    
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900 mb-2">Action Items:</p>
                        <ul className="space-y-1">
                          {suggestion.action_items.map((item, index) => (
                            <li key={index} className="flex items-start space-x-2 text-sm text-gray-700">
                              <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="flex items-center justify-between pt-4 border-t">
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>Effort: {suggestion.effort_required}</span>
                          {suggestion.deadline && (
                            <span>Deadline: {new Date(suggestion.deadline).toLocaleDateString()}</span>
                          )}
                        </div>
                        <Button size="sm">
                          Take Action
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Connect Tab */}
        <TabsContent value="connect" className="space-y-6">
          <div className="max-w-2xl mx-auto">
            <PlaidLinkWithInstitutions
              onSuccess={handlePlaidSuccess}
              onExit={(error, metadata) => {
                console.log('Plaid link exited:', { error, metadata });
              }}
              onLoad={() => {
                console.log('Plaid link loaded');
              }}
              showInstitutions={true}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AccountsManagement;