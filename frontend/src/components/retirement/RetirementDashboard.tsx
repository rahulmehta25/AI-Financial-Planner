import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  PiggyBank, 
  TrendingUp, 
  DollarSign, 
  Calendar, 
  Target, 
  AlertTriangle,
  Plus,
  Calculator,
  BookOpen,
  Heart
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import { RetirementAccountsList } from './RetirementAccountsList';
import { ContributionOptimizer } from './ContributionOptimizer';
import { RetirementProjections } from './RetirementProjections';
import { RothConversionAnalyzer } from './RothConversionAnalyzer';
import { Education529Planner } from './Education529Planner';
import { HSAPlanner } from './HSAPlanner';

interface RetirementAccount {
  id: string;
  account_type: string;
  account_name: string;
  current_balance: number;
  tax_treatment: string;
  is_active: boolean;
  financial_institution?: string;
  employer_name?: string;
}

interface ContributionLimits {
  regular_limit: number;
  catch_up_limit: number;
  total_limit: number;
  contributed_to_date: number;
  available_room: number;
}

interface RetirementSummary {
  total_balance: number;
  annual_contributions: number;
  employer_match: number;
  tax_savings: number;
  years_to_retirement: number;
  projected_retirement_income: number;
  replacement_ratio: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export const RetirementDashboard: React.FC = () => {
  const [accounts, setAccounts] = useState<RetirementAccount[]>([]);
  const [summary, setSummary] = useState<RetirementSummary | null>(null);
  const [contributionLimits, setContributionLimits] = useState<Record<string, ContributionLimits>>({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchRetirementData();
  }, []);

  const fetchRetirementData = async () => {
    try {
      setLoading(true);
      
      // Fetch retirement accounts
      const accountsResponse = await fetch('/api/v1/retirement/accounts', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const accountsData = await accountsResponse.json();
      setAccounts(accountsData);

      // Calculate summary
      const totalBalance = accountsData.reduce((sum: number, account: RetirementAccount) => 
        sum + account.current_balance, 0);
      
      setSummary({
        total_balance: totalBalance,
        annual_contributions: 25000, // This would be calculated from actual data
        employer_match: 5000,
        tax_savings: 7500,
        years_to_retirement: 25,
        projected_retirement_income: 4800,
        replacement_ratio: 0.8
      });

      // Fetch contribution limits for current year
      const accountTypes = ['traditional_401k', 'roth_ira', 'traditional_ira', 'hsa'];
      const limitsPromises = accountTypes.map(async (type) => {
        try {
          const response = await fetch(
            `/api/v1/retirement/contribution-room/${type}?age=35&income=100000&filing_status=single`,
            { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } }
          );
          if (response.ok) {
            const data = await response.json();
            return { type, data };
          }
        } catch (error) {
          console.error(`Error fetching limits for ${type}:`, error);
        }
        return null;
      });

      const limitsResults = await Promise.all(limitsPromises);
      const limitsMap: Record<string, ContributionLimits> = {};
      limitsResults.forEach(result => {
        if (result) {
          limitsMap[result.type] = result.data;
        }
      });
      setContributionLimits(limitsMap);

    } catch (error) {
      console.error('Error fetching retirement data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getAccountTypeDisplay = (type: string) => {
    const typeMap: Record<string, string> = {
      'traditional_401k': '401(k)',
      'roth_401k': 'Roth 401(k)',
      'traditional_ira': 'Traditional IRA',
      'roth_ira': 'Roth IRA',
      'education_529': '529 Education',
      'hsa': 'HSA',
    };
    return typeMap[type] || type;
  };

  const getAccountsByType = () => {
    const grouped = accounts.reduce((acc, account) => {
      const type = account.account_type;
      if (!acc[type]) acc[type] = [];
      acc[type].push(account);
      return acc;
    }, {} as Record<string, RetirementAccount[]>);

    return Object.entries(grouped).map(([type, accounts]) => ({
      type,
      displayName: getAccountTypeDisplay(type),
      accounts,
      totalBalance: accounts.reduce((sum, acc) => sum + acc.current_balance, 0),
      count: accounts.length
    }));
  };

  const getPieChartData = () => {
    return getAccountsByType().map(({ displayName, totalBalance }, index) => ({
      name: displayName,
      value: totalBalance,
      color: COLORS[index % COLORS.length]
    }));
  };

  const getContributionProgress = () => {
    return Object.entries(contributionLimits).map(([type, limits]) => {
      const progressPercentage = (limits.contributed_to_date / limits.total_limit) * 100;
      return {
        type: getAccountTypeDisplay(type),
        contributed: limits.contributed_to_date,
        limit: limits.total_limit,
        available: limits.available_room,
        progress: progressPercentage
      };
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Retirement Planning
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your retirement accounts and optimize your savings strategy
          </p>
        </div>
        <Button onClick={() => setActiveTab('accounts')} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Add Account
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
              <PiggyBank className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(summary.total_balance)}</div>
              <p className="text-xs text-muted-foreground">
                +12.5% from last year
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Annual Contributions</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(summary.annual_contributions)}</div>
              <p className="text-xs text-muted-foreground">
                Including employer match: {formatCurrency(summary.employer_match)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tax Savings</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(summary.tax_savings)}</div>
              <p className="text-xs text-muted-foreground">
                From tax-deferred contributions
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Years to Retirement</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.years_to_retirement}</div>
              <p className="text-xs text-muted-foreground">
                Projected income: {formatCurrency(summary.projected_retirement_income)}/month
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="accounts">Accounts</TabsTrigger>
          <TabsTrigger value="optimizer">Optimizer</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
          <TabsTrigger value="conversions">Conversions</TabsTrigger>
          <TabsTrigger value="529">529 Plans</TabsTrigger>
          <TabsTrigger value="hsa">HSA</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Account Allocation Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Account Allocation</CardTitle>
                <CardDescription>
                  Distribution of your retirement savings by account type
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={getPieChartData()}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {getPieChartData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Balance']} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Contribution Progress */}
            <Card>
              <CardHeader>
                <CardTitle>2025 Contribution Progress</CardTitle>
                <CardDescription>
                  Track your progress toward annual contribution limits
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {getContributionProgress().map((item) => (
                  <div key={item.type} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{item.type}</span>
                      <span>{formatCurrency(item.contributed)} / {formatCurrency(item.limit)}</span>
                    </div>
                    <Progress value={item.progress} className="h-2" />
                    <div className="text-xs text-muted-foreground">
                      {formatCurrency(item.available)} remaining
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Account Summary by Type */}
          <Card>
            <CardHeader>
              <CardTitle>Account Summary</CardTitle>
              <CardDescription>
                Overview of your retirement accounts by type
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {getAccountsByType().map(({ type, displayName, totalBalance, count }) => (
                  <div key={type} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">{displayName}</h3>
                      <Badge variant="secondary">{count} account{count !== 1 ? 's' : ''}</Badge>
                    </div>
                    <p className="text-2xl font-bold">{formatCurrency(totalBalance)}</p>
                    <p className="text-sm text-muted-foreground">
                      {count === 1 ? 'Single account' : `Across ${count} accounts`}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Action Items */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Recommended Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  You have ${(contributionLimits['traditional_401k']?.available_room || 0).toLocaleString()} 
                  remaining in your 401(k) contribution room. Consider increasing your contributions 
                  to maximize employer matching.
                </AlertDescription>
              </Alert>
              
              <Alert>
                <TrendingUp className="h-4 w-4" />
                <AlertDescription>
                  Based on your current savings rate, you're on track to replace 65% of your income 
                  in retirement. Consider increasing contributions to reach your 80% target.
                </AlertDescription>
              </Alert>

              <Alert>
                <Calculator className="h-4 w-4" />
                <AlertDescription>
                  You may benefit from a Roth conversion strategy. Use our analyzer to explore 
                  the potential tax savings.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="accounts">
          <RetirementAccountsList accounts={accounts} onAccountsChange={fetchRetirementData} />
        </TabsContent>

        <TabsContent value="optimizer">
          <ContributionOptimizer 
            accounts={accounts}
            contributionLimits={contributionLimits}
            onOptimizationComplete={fetchRetirementData}
          />
        </TabsContent>

        <TabsContent value="projections">
          <RetirementProjections accounts={accounts} />
        </TabsContent>

        <TabsContent value="conversions">
          <RothConversionAnalyzer accounts={accounts} />
        </TabsContent>

        <TabsContent value="529">
          <Education529Planner accounts={accounts.filter(a => a.account_type === 'education_529')} />
        </TabsContent>

        <TabsContent value="hsa">
          <HSAPlanner accounts={accounts.filter(a => a.account_type === 'hsa')} />
        </TabsContent>
      </Tabs>
    </div>
  );
};