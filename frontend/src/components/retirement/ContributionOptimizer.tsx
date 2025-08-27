import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Separator } from '../ui/separator';
import { 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  Target, 
  Lightbulb,
  PieChart,
  ArrowRight
} from 'lucide-react';

interface RetirementAccount {
  id: string;
  account_type: string;
  account_name: string;
  current_balance: number;
  tax_treatment: string;
}

interface ContributionLimits {
  regular_limit: number;
  catch_up_limit: number;
  total_limit: number;
  contributed_to_date: number;
  available_room: number;
}

interface ContributionOptimizerProps {
  accounts: RetirementAccount[];
  contributionLimits: Record<string, ContributionLimits>;
  onOptimizationComplete: () => void;
}

interface OptimizationInputs {
  currentAge: number;
  retirementAge: number;
  currentIncome: number;
  availableCash: number;
  filingStatus: string;
  stateOfResidence: string;
  riskTolerance: string;
}

interface OptimizationResult {
  account_allocations: Record<string, number>;
  total_annual_contribution: number;
  tax_savings: number;
  employer_match_captured: number;
  strategy_explanation: string;
}

export const ContributionOptimizer: React.FC<ContributionOptimizerProps> = ({
  accounts,
  contributionLimits,
  onOptimizationComplete,
}) => {
  const [inputs, setInputs] = useState<OptimizationInputs>({
    currentAge: 35,
    retirementAge: 65,
    currentIncome: 100000,
    availableCash: 25000,
    filingStatus: 'single',
    stateOfResidence: 'CA',
    riskTolerance: 'moderate',
  });

  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleOptimize = async () => {
    setIsOptimizing(true);
    setError(null);

    try {
      const requestBody = {
        personal_info: {
          current_age: inputs.currentAge,
          retirement_age: inputs.retirementAge,
          current_income: inputs.currentIncome,
          filing_status: inputs.filingStatus,
          state_of_residence: inputs.stateOfResidence,
        },
        available_cash: inputs.availableCash,
        tax_year: 2025,
      };

      const response = await fetch('/api/v1/retirement/optimize-contributions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Optimization failed');
      }

      const optimizationResult = await response.json();
      setResult(optimizationResult);
    } catch (error) {
      console.error('Optimization error:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setIsOptimizing(false);
    }
  };

  const getMarginalTaxRate = () => {
    // Simplified tax bracket calculation
    if (inputs.currentIncome <= 11925) return 0.10;
    if (inputs.currentIncome <= 48475) return 0.12;
    if (inputs.currentIncome <= 103350) return 0.22;
    if (inputs.currentIncome <= 197300) return 0.24;
    if (inputs.currentIncome <= 250525) return 0.32;
    if (inputs.currentIncome <= 626350) return 0.35;
    return 0.37;
  };

  const getAccountDetails = (accountId: string) => {
    return accounts.find(account => account.id === accountId);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Calculator className="h-8 w-8 text-blue-600" />
        <div>
          <h2 className="text-2xl font-bold">Contribution Optimizer</h2>
          <p className="text-muted-foreground">
            Find the optimal allocation of your retirement contributions across accounts
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Your Information</CardTitle>
            <CardDescription>
              Enter your details to get personalized recommendations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
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
              <Label htmlFor="currentIncome">Annual Income</Label>
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
              <Label htmlFor="availableCash">Available for Retirement Savings</Label>
              <Input
                id="availableCash"
                type="number"
                min="0"
                step="100"
                value={inputs.availableCash}
                onChange={(e) => setInputs({ ...inputs, availableCash: parseFloat(e.target.value) || 0 })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="filingStatus">Tax Filing Status</Label>
              <Select
                value={inputs.filingStatus}
                onValueChange={(value) => setInputs({ ...inputs, filingStatus: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="single">Single</SelectItem>
                  <SelectItem value="married_filing_jointly">Married Filing Jointly</SelectItem>
                  <SelectItem value="married_filing_separately">Married Filing Separately</SelectItem>
                  <SelectItem value="head_of_household">Head of Household</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="stateOfResidence">State of Residence</Label>
              <Select
                value={inputs.stateOfResidence}
                onValueChange={(value) => setInputs({ ...inputs, stateOfResidence: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CA">California</SelectItem>
                  <SelectItem value="NY">New York</SelectItem>
                  <SelectItem value="TX">Texas</SelectItem>
                  <SelectItem value="FL">Florida</SelectItem>
                  <SelectItem value="WA">Washington</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {error && (
              <Alert>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button 
              onClick={handleOptimize} 
              disabled={isOptimizing || inputs.availableCash <= 0}
              className="w-full"
            >
              {isOptimizing ? 'Optimizing...' : 'Optimize Contributions'}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <DollarSign className="h-4 w-4" />
                      Total Contributions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(result.total_annual_contribution)}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {((result.total_annual_contribution / inputs.currentIncome) * 100).toFixed(1)}% of income
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      Tax Savings
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(result.tax_savings)}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {((result.tax_savings / inputs.currentIncome) * 100).toFixed(1)}% of income saved
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Target className="h-4 w-4" />
                      Employer Match
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(result.employer_match_captured)}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Free money captured
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Recommended Allocation */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5" />
                    Recommended Allocation
                  </CardTitle>
                  <CardDescription>
                    Optimal distribution of your {formatCurrency(inputs.availableCash)} across accounts
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(result.account_allocations).map(([accountId, amount]) => {
                    const account = getAccountDetails(accountId);
                    const percentage = (amount / result.total_annual_contribution) * 100;
                    
                    if (amount === 0) return null;
                    
                    return (
                      <div key={accountId} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                            <div>
                              <p className="font-medium">
                                {account ? account.account_name : 'Unknown Account'}
                              </p>
                              <p className="text-sm text-muted-foreground">
                                {account ? getAccountTypeDisplay(account.account_type) : 'Unknown Type'}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-medium">{formatCurrency(amount)}</p>
                            <p className="text-sm text-muted-foreground">{percentage.toFixed(1)}%</p>
                          </div>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              {/* Strategy Explanation */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5" />
                    Strategy Explanation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap">{result.strategy_explanation}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Tax Impact Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle>Tax Impact Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold mb-3">Current Year Benefits</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Marginal Tax Rate:</span>
                          <span>{(getMarginalTaxRate() * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tax-Deferred Contributions:</span>
                          <span>{formatCurrency(result.total_annual_contribution - result.employer_match_captured)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Federal Tax Savings:</span>
                          <span className="text-green-600 font-medium">{formatCurrency(result.tax_savings)}</span>
                        </div>
                        <Separator />
                        <div className="flex justify-between font-semibold">
                          <span>Net Cost:</span>
                          <span>{formatCurrency(result.total_annual_contribution - result.tax_savings - result.employer_match_captured)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-3">Long-term Benefits</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Employer Match (Annual):</span>
                          <span className="text-green-600">{formatCurrency(result.employer_match_captured)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>HSA Triple Tax Advantage:</span>
                          <span className="text-green-600">Maximized</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Estimated 20-Year Growth:</span>
                          <span>{formatCurrency(result.total_annual_contribution * 20 * 1.07)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Calculator className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Optimize Your Contributions</h3>
                <p className="text-muted-foreground text-center mb-6 max-w-md">
                  Enter your information to receive personalized recommendations for maximizing 
                  your retirement savings and minimizing taxes.
                </p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Fill out the form</span>
                  <ArrowRight className="h-4 w-4" />
                  <span>Get optimization</span>
                  <ArrowRight className="h-4 w-4" />
                  <span>Maximize savings</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};