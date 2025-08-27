import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Slider } from '../ui/slider';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  TrendingUp, 
  DollarSign, 
  Calendar, 
  Target,
  BarChart3,
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
  AlertTriangle
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';

interface RetirementAccount {
  id: string;
  account_type: string;
  account_name: string;
  current_balance: number;
  tax_treatment: string;
}

interface RetirementProjectionsProps {
  accounts: RetirementAccount[];
}

interface ProjectionInputs {
  currentAge: number;
  retirementAge: number;
  lifeExpectancy: number;
  currentIncome: number;
  incomeGrowthRate: number;
  inflationRate: number;
  preRetirementReturn: number;
  postRetirementReturn: number;
  incomeReplacementRatio: number;
  annualContribution: number;
}

interface ProjectionResult {
  current_income: number;
  inflated_income_at_retirement: number;
  target_annual_retirement_income: number;
  total_retirement_need_pv: number;
  years_to_retirement: number;
  years_in_retirement: number;
}

interface AccountProjection {
  year: number;
  age: number;
  balance: number;
  annual_contribution: number;
  employer_match: number;
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(1)}%`;
};

export const RetirementProjections: React.FC<RetirementProjectionsProps> = ({ accounts }) => {
  const [inputs, setInputs] = useState<ProjectionInputs>({
    currentAge: 35,
    retirementAge: 65,
    lifeExpectancy: 90,
    currentIncome: 100000,
    incomeGrowthRate: 0.03,
    inflationRate: 0.025,
    preRetirementReturn: 0.07,
    postRetirementReturn: 0.05,
    incomeReplacementRatio: 0.80,
    annualContribution: 25000,
  });

  const [projectionResult, setProjectionResult] = useState<ProjectionResult | null>(null);
  const [accountProjections, setAccountProjections] = useState<Record<string, AccountProjection[]>>({});
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculateProjections = async () => {
    setIsCalculating(true);
    setError(null);

    try {
      // Calculate retirement income need
      const retirementRequest = {
        current_age: inputs.currentAge,
        retirement_age: inputs.retirementAge,
        life_expectancy: inputs.lifeExpectancy,
        filing_status: 'single',
        current_income: inputs.currentIncome,
      };

      const goalRequest = {
        income_replacement_ratio: inputs.incomeReplacementRatio,
        inflation_rate: inputs.inflationRate,
        years_in_retirement: inputs.lifeExpectancy - inputs.retirementAge,
      };

      const response = await fetch('/api/v1/retirement/retirement-projection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          personal_info: retirementRequest,
          retirement_goal: goalRequest,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to calculate retirement projections');
      }

      const result = await response.json();
      setProjectionResult(result);

      // Calculate individual account projections
      const projectionPromises = accounts.map(async (account) => {
        const projectionResponse = await fetch(`/api/v1/retirement/account-projections/${account.id}?years=${inputs.retirementAge - inputs.currentAge}&annual_contribution=${inputs.annualContribution / accounts.length}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (projectionResponse.ok) {
          const projectionData = await projectionResponse.json();
          return { accountId: account.id, projections: projectionData.projections };
        }
        return { accountId: account.id, projections: [] };
      });

      const allProjections = await Promise.all(projectionPromises);
      const projectionsMap: Record<string, AccountProjection[]> = {};
      allProjections.forEach(({ accountId, projections }) => {
        projectionsMap[accountId] = projections;
      });
      setAccountProjections(projectionsMap);

    } catch (error) {
      console.error('Error calculating projections:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setIsCalculating(false);
    }
  };

  useEffect(() => {
    if (accounts.length > 0) {
      calculateProjections();
    }
  }, [accounts]);

  const getTotalProjectionData = () => {
    const yearsToRetirement = inputs.retirementAge - inputs.currentAge;
    const data = [];
    
    for (let year = 0; year <= yearsToRetirement; year++) {
      const age = inputs.currentAge + year;
      let totalBalance = 0;
      
      // Sum all account balances for this year
      Object.values(accountProjections).forEach(projections => {
        const yearData = projections[year];
        if (yearData) {
          totalBalance += yearData.balance;
        }
      });
      
      // Add current balances for year 0
      if (year === 0) {
        totalBalance = accounts.reduce((sum, account) => sum + account.current_balance, 0);
      }
      
      data.push({
        year: year,
        age: age,
        totalBalance: totalBalance,
        contributions: year > 0 ? inputs.annualContribution : 0,
      });
    }
    
    return data;
  };

  const getWithdrawalProjectionData = () => {
    const withdrawalRate = 0.04; // 4% rule
    const yearsInRetirement = inputs.lifeExpectancy - inputs.retirementAge;
    const data = [];
    
    const finalBalance = getTotalProjectionData()[getTotalProjectionData().length - 1]?.totalBalance || 0;
    let remainingBalance = finalBalance;
    
    for (let year = 0; year <= yearsInRetirement; year++) {
      const age = inputs.retirementAge + year;
      const annualWithdrawal = remainingBalance * withdrawalRate;
      
      data.push({
        year: inputs.retirementAge - inputs.currentAge + year,
        age: age,
        balance: remainingBalance,
        withdrawal: annualWithdrawal,
      });
      
      // Apply growth and subtract withdrawal
      remainingBalance = (remainingBalance - annualWithdrawal) * (1 + inputs.postRetirementReturn);
    }
    
    return data;
  };

  const getSuccessProbability = () => {
    // Simplified Monte Carlo approximation
    const totalSaved = getTotalProjectionData()[getTotalProjectionData().length - 1]?.totalBalance || 0;
    const needAtRetirement = projectionResult?.total_retirement_need_pv || 0;
    
    if (needAtRetirement === 0) return 0;
    
    const ratio = totalSaved / needAtRetirement;
    
    if (ratio >= 1.2) return 95;
    if (ratio >= 1.0) return 85;
    if (ratio >= 0.8) return 65;
    if (ratio >= 0.6) return 40;
    return 20;
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

  const totalProjectionData = getTotalProjectionData();
  const withdrawalData = getWithdrawalProjectionData();
  const successProbability = getSuccessProbability();
  const finalBalance = totalProjectionData[totalProjectionData.length - 1]?.totalBalance || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <TrendingUp className="h-8 w-8 text-blue-600" />
        <div>
          <h2 className="text-2xl font-bold">Retirement Projections</h2>
          <p className="text-muted-foreground">
            Visualize your retirement savings growth and withdrawal scenarios
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Input Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Projection Settings</CardTitle>
            <CardDescription>Adjust assumptions to see different scenarios</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="currentAge">Current Age</Label>
                <Input
                  id="currentAge"
                  type="number"
                  min="18"
                  max="100"
                  value={inputs.currentAge}
                  onChange={(e) => setInputs({ ...inputs, currentAge: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="retirementAge">Retirement Age</Label>
                <Input
                  id="retirementAge"
                  type="number"
                  min="50"
                  max="75"
                  value={inputs.retirementAge}
                  onChange={(e) => setInputs({ ...inputs, retirementAge: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="lifeExpectancy">Life Expectancy</Label>
              <Input
                id="lifeExpectancy"
                type="number"
                min="70"
                max="120"
                value={inputs.lifeExpectancy}
                onChange={(e) => setInputs({ ...inputs, lifeExpectancy: parseInt(e.target.value) || 0 })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="currentIncome">Current Income</Label>
              <Input
                id="currentIncome"
                type="number"
                min="0"
                step="1000"
                value={inputs.currentIncome}
                onChange={(e) => setInputs({ ...inputs, currentIncome: parseFloat(e.target.value) || 0 })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="annualContribution">Annual Contribution</Label>
              <Input
                id="annualContribution"
                type="number"
                min="0"
                step="100"
                value={inputs.annualContribution}
                onChange={(e) => setInputs({ ...inputs, annualContribution: parseFloat(e.target.value) || 0 })}
              />
            </div>

            <div className="space-y-3">
              <div>
                <Label>Income Replacement Ratio: {formatPercent(inputs.incomeReplacementRatio)}</Label>
                <Slider
                  value={[inputs.incomeReplacementRatio]}
                  onValueChange={([value]) => setInputs({ ...inputs, incomeReplacementRatio: value })}
                  max={1.2}
                  min={0.3}
                  step={0.05}
                  className="mt-2"
                />
              </div>

              <div>
                <Label>Pre-Retirement Return: {formatPercent(inputs.preRetirementReturn)}</Label>
                <Slider
                  value={[inputs.preRetirementReturn]}
                  onValueChange={([value]) => setInputs({ ...inputs, preRetirementReturn: value })}
                  max={0.12}
                  min={0.03}
                  step={0.005}
                  className="mt-2"
                />
              </div>

              <div>
                <Label>Post-Retirement Return: {formatPercent(inputs.postRetirementReturn)}</Label>
                <Slider
                  value={[inputs.postRetirementReturn]}
                  onValueChange={([value]) => setInputs({ ...inputs, postRetirementReturn: value })}
                  max={0.08}
                  min={0.02}
                  step={0.005}
                  className="mt-2"
                />
              </div>

              <div>
                <Label>Inflation Rate: {formatPercent(inputs.inflationRate)}</Label>
                <Slider
                  value={[inputs.inflationRate]}
                  onValueChange={([value]) => setInputs({ ...inputs, inflationRate: value })}
                  max={0.05}
                  min={0.01}
                  step={0.005}
                  className="mt-2"
                />
              </div>
            </div>

            <Button onClick={calculateProjections} disabled={isCalculating} className="w-full">
              {isCalculating ? 'Calculating...' : 'Update Projections'}
            </Button>

            {error && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results Panel */}
        <div className="lg:col-span-3 space-y-6">
          {/* Summary Cards */}
          {projectionResult && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Projected Balance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatCurrency(finalBalance)}</div>
                  <p className="text-xs text-muted-foreground">At retirement</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Income Need</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(projectionResult.target_annual_retirement_income)}
                  </div>
                  <p className="text-xs text-muted-foreground">Annual in retirement</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Success Probability</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {successProbability}%
                  </div>
                  <p className="text-xs text-muted-foreground">Money lasting to {inputs.lifeExpectancy}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Years to Goal</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {inputs.retirementAge - inputs.currentAge}
                  </div>
                  <p className="text-xs text-muted-foreground">Until retirement</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Charts */}
          <Tabs defaultValue="accumulation" className="space-y-4">
            <TabsList>
              <TabsTrigger value="accumulation">Accumulation Phase</TabsTrigger>
              <TabsTrigger value="withdrawal">Withdrawal Phase</TabsTrigger>
              <TabsTrigger value="accounts">By Account</TabsTrigger>
            </TabsList>

            <TabsContent value="accumulation">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Savings Accumulation
                  </CardTitle>
                  <CardDescription>
                    Growth of your retirement savings until age {inputs.retirementAge}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={totalProjectionData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="age" />
                        <YAxis tickFormatter={(value) => formatCurrency(value)} />
                        <Tooltip 
                          formatter={(value, name) => [formatCurrency(Number(value)), name]}
                          labelFormatter={(age) => `Age ${age}`}
                        />
                        <Legend />
                        <Area 
                          type="monotone" 
                          dataKey="totalBalance" 
                          stackId="1" 
                          stroke="#8884d8" 
                          fill="#8884d8" 
                          name="Total Balance"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="withdrawal">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <LineChartIcon className="h-5 w-5" />
                    Retirement Withdrawal Phase
                  </CardTitle>
                  <CardDescription>
                    Balance trajectory during retirement with 4% withdrawal rate
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={withdrawalData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="age" />
                        <YAxis tickFormatter={(value) => formatCurrency(value)} />
                        <Tooltip 
                          formatter={(value, name) => [formatCurrency(Number(value)), name]}
                          labelFormatter={(age) => `Age ${age}`}
                        />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="balance" 
                          stroke="#8884d8" 
                          name="Remaining Balance"
                          strokeWidth={3}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="withdrawal" 
                          stroke="#82ca9d" 
                          name="Annual Withdrawal"
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="accounts">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {accounts.map((account) => {
                  const projections = accountProjections[account.id] || [];
                  if (projections.length === 0) return null;

                  return (
                    <Card key={account.id}>
                      <CardHeader>
                        <CardTitle className="text-lg">{account.account_name}</CardTitle>
                        <CardDescription>
                          {getAccountTypeDisplay(account.account_type)} • 
                          Current: {formatCurrency(account.current_balance)}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="h-48">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={projections}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="age" />
                              <YAxis tickFormatter={(value) => formatCurrency(value)} />
                              <Tooltip 
                                formatter={(value, name) => [formatCurrency(Number(value)), name]}
                                labelFormatter={(age) => `Age ${age}`}
                              />
                              <Line 
                                type="monotone" 
                                dataKey="balance" 
                                stroke="#8884d8" 
                                strokeWidth={2}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>
          </Tabs>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {successProbability < 70 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Low Success Probability ({successProbability}%)</strong>
                      <br />
                      Consider increasing your annual contributions or adjusting your retirement age. 
                      Current projections suggest a {successProbability}% chance your money will last until age {inputs.lifeExpectancy}.
                    </AlertDescription>
                  </Alert>
                )}

                {projectionResult && finalBalance < projectionResult.total_retirement_need_pv && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Shortfall Alert</strong>
                      <br />
                      You're projected to be short {formatCurrency(projectionResult.total_retirement_need_pv - finalBalance)} 
                      at retirement. Consider increasing contributions by {formatCurrency((projectionResult.total_retirement_need_pv - finalBalance) / (inputs.retirementAge - inputs.currentAge))} 
                      annually.
                    </AlertDescription>
                  </Alert>
                )}

                {successProbability >= 90 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Excellent Progress!</strong>
                      <br />
                      Your current savings rate puts you on track for a comfortable retirement. 
                      Consider if you want to retire earlier or increase your lifestyle in retirement.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};