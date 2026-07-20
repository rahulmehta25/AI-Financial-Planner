import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Separator } from '../ui/separator';
import { 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  AlertTriangle,
  CheckCircle,
  ArrowRightLeft,
  Calendar,
  Target
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface RetirementAccount {
  id: string;
  account_type: string;
  account_name: string;
  current_balance: number;
  tax_treatment: string;
}

interface RothConversionAnalyzerProps {
  accounts: RetirementAccount[];
}

interface ConversionInputs {
  traditionalBalance: number;
  currentAge: number;
  currentTaxRate: number;
  expectedRetirementTaxRate: number;
  yearsToRetirement: number;
  conversionAmount: number;
}

interface ConversionResult {
  optimal_conversion_amount: number;
  years_to_convert: number[];
  tax_cost_of_conversion: number;
  lifetime_tax_savings: number;
  breakeven_age: number;
  conversion_timeline: Array<{
    year: number;
    conversion_amount: number;
    tax_cost: number;
    cumulative_converted: number;
  }>;
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

export const RothConversionAnalyzer: React.FC<RothConversionAnalyzerProps> = ({ accounts }) => {
  const [inputs, setInputs] = useState<ConversionInputs>({
    traditionalBalance: 0,
    currentAge: 45,
    currentTaxRate: 0.22,
    expectedRetirementTaxRate: 0.22,
    yearsToRetirement: 20,
    conversionAmount: 50000,
  });

  const [result, setResult] = useState<ConversionResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get traditional accounts
  const traditionalAccounts = accounts.filter(account => 
    account.tax_treatment === 'tax_deferred' && 
    (account.account_type.includes('401k') || account.account_type.includes('ira'))
  );

  const totalTraditionalBalance = traditionalAccounts.reduce((sum, account) => sum + account.current_balance, 0);

  // Initialize with actual balance if available
  React.useEffect(() => {
    if (totalTraditionalBalance > 0 && inputs.traditionalBalance === 0) {
      setInputs(prev => ({ ...prev, traditionalBalance: totalTraditionalBalance }));
    }
  }, [totalTraditionalBalance]);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams({
        traditional_balance: inputs.traditionalBalance.toString(),
        current_age: inputs.currentAge.toString(),
        current_tax_rate: inputs.currentTaxRate.toString(),
        expected_retirement_tax_rate: inputs.expectedRetirementTaxRate.toString(),
        years_to_retirement: inputs.yearsToRetirement.toString(),
      });

      const response = await fetch(`/api/v1/retirement/roth-conversion-analysis?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const analysisResult = await response.json();
      setResult(analysisResult);
    } catch (error) {
      console.error('Analysis error:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getConversionRecommendation = () => {
    if (!result) return null;

    const taxRateDifference = inputs.expectedRetirementTaxRate - inputs.currentTaxRate;
    const savingsPercent = (result.lifetime_tax_savings / result.tax_cost_of_conversion) * 100;

    if (taxRateDifference > 0.02) {
      return {
        type: 'highly_recommended',
        title: 'Highly Recommended',
        description: `Converting now could save you significant taxes since you expect to be in a higher tax bracket in retirement.`,
        color: 'green'
      };
    } else if (taxRateDifference < -0.02) {
      return {
        type: 'not_recommended',
        title: 'Not Recommended',
        description: `You're likely better off keeping your traditional accounts since you expect to be in a lower tax bracket in retirement.`,
        color: 'red'
      };
    } else {
      return {
        type: 'neutral',
        title: 'Neutral',
        description: `The tax benefits are minimal since your current and expected retirement tax rates are similar.`,
        color: 'yellow'
      };
    }
  };

  const getProjectedGrowth = () => {
    if (!result) return [];

    const data = [];
    const annualReturn = 0.07;
    let traditionalBalance = inputs.traditionalBalance - result.optimal_conversion_amount;
    let rothBalance = result.optimal_conversion_amount;

    for (let year = 0; year <= inputs.yearsToRetirement; year++) {
      data.push({
        year,
        traditionalBalance,
        rothBalance,
        totalBalance: traditionalBalance + rothBalance,
      });

      traditionalBalance *= (1 + annualReturn);
      rothBalance *= (1 + annualReturn);
    }

    return data;
  };

  const recommendation = getConversionRecommendation();
  const projectionData = getProjectedGrowth();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <ArrowRightLeft className="h-8 w-8 text-blue-600" />
        <div>
          <h2 className="text-2xl font-bold">Roth Conversion Analyzer</h2>
          <p className="text-muted-foreground">
            Analyze the tax implications of converting traditional retirement accounts to Roth
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Conversion Analysis</CardTitle>
            <CardDescription>
              Enter your details to analyze Roth conversion opportunities
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Current Accounts Summary */}
            {traditionalAccounts.length > 0 && (
              <div className="p-3 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">Your Traditional Accounts</h4>
                <div className="space-y-1 text-sm">
                  {traditionalAccounts.map(account => (
                    <div key={account.id} className="flex justify-between">
                      <span>{account.account_name}</span>
                      <span>{formatCurrency(account.current_balance)}</span>
                    </div>
                  ))}
                  <Separator className="my-2" />
                  <div className="flex justify-between font-medium">
                    <span>Total</span>
                    <span>{formatCurrency(totalTraditionalBalance)}</span>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="traditionalBalance">Traditional IRA/401(k) Balance</Label>
              <Input
                id="traditionalBalance"
                type="number"
                min="0"
                step="1000"
                value={inputs.traditionalBalance}
                onChange={(e) => setInputs({ ...inputs, traditionalBalance: parseFloat(e.target.value) || 0 })}
              />
            </div>

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
                <Label htmlFor="yearsToRetirement">Years to Retirement</Label>
                <Input
                  id="yearsToRetirement"
                  type="number"
                  min="1"
                  max="50"
                  value={inputs.yearsToRetirement}
                  onChange={(e) => setInputs({ ...inputs, yearsToRetirement: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="currentTaxRate">Current Tax Rate</Label>
              <select
                id="currentTaxRate"
                value={inputs.currentTaxRate}
                onChange={(e) => setInputs({ ...inputs, currentTaxRate: parseFloat(e.target.value) })}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value={0.10}>10% ($0 - $11,925)</option>
                <option value={0.12}>12% ($11,925 - $48,475)</option>
                <option value={0.22}>22% ($48,475 - $103,350)</option>
                <option value={0.24}>24% ($103,350 - $197,300)</option>
                <option value={0.32}>32% ($197,300 - $250,525)</option>
                <option value={0.35}>35% ($250,525 - $626,350)</option>
                <option value={0.37}>37% ($626,350+)</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="expectedRetirementTaxRate">Expected Retirement Tax Rate</Label>
              <select
                id="expectedRetirementTaxRate"
                value={inputs.expectedRetirementTaxRate}
                onChange={(e) => setInputs({ ...inputs, expectedRetirementTaxRate: parseFloat(e.target.value) })}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value={0.10}>10% - Lower retirement income</option>
                <option value={0.12}>12% - Modest retirement income</option>
                <option value={0.22}>22% - Similar to current</option>
                <option value={0.24}>24% - Higher retirement income</option>
                <option value={0.32}>32% - Much higher retirement income</option>
              </select>
            </div>

            {error && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button 
              onClick={handleAnalyze} 
              disabled={isAnalyzing || inputs.traditionalBalance <= 0}
              className="w-full"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Conversion'}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {result ? (
            <>
              {/* Recommendation Card */}
              {recommendation && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      {recommendation.type === 'highly_recommended' && <CheckCircle className="h-5 w-5 text-green-600" />}
                      {recommendation.type === 'not_recommended' && <AlertTriangle className="h-5 w-5 text-red-600" />}
                      {recommendation.type === 'neutral' && <Target className="h-5 w-5 text-yellow-600" />}
                      {recommendation.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground mb-4">{recommendation.description}</p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold">{formatCurrency(result.optimal_conversion_amount)}</div>
                        <div className="text-xs text-muted-foreground">Optimal Conversion</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{formatCurrency(result.tax_cost_of_conversion)}</div>
                        <div className="text-xs text-muted-foreground">Tax Cost</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{formatCurrency(result.lifetime_tax_savings)}</div>
                        <div className="text-xs text-muted-foreground">Lifetime Savings</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold">{result.breakeven_age}</div>
                        <div className="text-xs text-muted-foreground">Breakeven Age</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Conversion Timeline */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Conversion Timeline
                  </CardTitle>
                  <CardDescription>
                    Suggested conversion schedule over {result.years_to_convert.length} years
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {result.conversion_timeline.map((item) => (
                      <div key={item.year} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <Badge variant="outline">Year {item.year}</Badge>
                          <div>
                            <div className="font-medium">Convert {formatCurrency(item.conversion_amount)}</div>
                            <div className="text-sm text-muted-foreground">
                              Tax cost: {formatCurrency(item.tax_cost)}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">{formatCurrency(item.cumulative_converted)}</div>
                          <div className="text-sm text-muted-foreground">Cumulative</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Growth Projection Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Growth Projection</CardTitle>
                  <CardDescription>
                    Projected growth of traditional vs. Roth balances after conversion
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={projectionData.filter((_, index) => index % 5 === 0)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="year" />
                        <YAxis tickFormatter={(value) => formatCurrency(value)} />
                        <Tooltip 
                          formatter={(value, name) => [formatCurrency(Number(value)), name]}
                          labelFormatter={(year) => `Year ${year}`}
                        />
                        <Legend />
                        <Bar dataKey="traditionalBalance" stackId="a" fill="#8884d8" name="Traditional Balance" />
                        <Bar dataKey="rothBalance" stackId="a" fill="#82ca9d" name="Roth Balance" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Tax Implications */}
              <Card>
                <CardHeader>
                  <CardTitle>Tax Impact Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold mb-3">Conversion Costs</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Conversion Amount:</span>
                          <span>{formatCurrency(result.optimal_conversion_amount)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Current Tax Rate:</span>
                          <span>{formatPercent(inputs.currentTaxRate)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Immediate Tax Cost:</span>
                          <span className="text-red-600">{formatCurrency(result.tax_cost_of_conversion)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>After-Tax Conversion:</span>
                          <span>{formatCurrency(result.optimal_conversion_amount - result.tax_cost_of_conversion)}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3">Long-term Benefits</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Expected Retirement Rate:</span>
                          <span>{formatPercent(inputs.expectedRetirementTaxRate)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tax Rate Difference:</span>
                          <span className={inputs.expectedRetirementTaxRate > inputs.currentTaxRate ? 'text-green-600' : 'text-red-600'}>
                            {formatPercent(inputs.expectedRetirementTaxRate - inputs.currentTaxRate)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Lifetime Tax Savings:</span>
                          <span className="text-green-600">{formatCurrency(result.lifetime_tax_savings)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Net Benefit:</span>
                          <span className={result.lifetime_tax_savings > result.tax_cost_of_conversion ? 'text-green-600' : 'text-red-600'}>
                            {formatCurrency(result.lifetime_tax_savings - result.tax_cost_of_conversion)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Important Considerations */}
              <Card>
                <CardHeader>
                  <CardTitle>Important Considerations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Tax Payment Source:</strong> You'll need cash outside of your retirement accounts 
                        to pay the conversion taxes for maximum benefit.
                      </AlertDescription>
                    </Alert>
                    
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>5-Year Rule:</strong> Converted amounts must stay in the Roth IRA for at least 
                        5 years to avoid penalties on early withdrawals.
                      </AlertDescription>
                    </Alert>

                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Medicare Premiums:</strong> Large conversions may increase your Medicare premiums 
                        due to higher reported income in the conversion year.
                      </AlertDescription>
                    </Alert>

                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>State Taxes:</strong> This analysis only considers federal taxes. 
                        State tax implications may vary significantly.
                      </AlertDescription>
                    </Alert>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Calculator className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Roth Conversion Analysis</h3>
                <p className="text-muted-foreground text-center mb-6 max-w-md">
                  Enter your traditional retirement account balance and tax information to analyze 
                  potential Roth conversion opportunities.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                  <div className="text-center">
                    <DollarSign className="h-6 w-6 mx-auto mb-2" />
                    <div>Tax Optimization</div>
                  </div>
                  <div className="text-center">
                    <TrendingUp className="h-6 w-6 mx-auto mb-2" />
                    <div>Growth Analysis</div>
                  </div>
                  <div className="text-center">
                    <Target className="h-6 w-6 mx-auto mb-2" />
                    <div>Strategic Planning</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};