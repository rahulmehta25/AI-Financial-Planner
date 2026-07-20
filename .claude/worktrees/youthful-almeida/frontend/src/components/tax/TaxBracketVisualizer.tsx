import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Slider } from '../ui/slider';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Area, AreaChart } from 'recharts';
import { 
  BarChart3, 
  TrendingUp, 
  Calculator,
  Target,
  Percent,
  DollarSign,
  Info,
  AlertTriangle,
  ArrowUp,
  ArrowDown,
  Lightbulb,
  PieChart,
  Settings
} from 'lucide-react';

// Types for tax bracket visualization
interface TaxBracket {
  rate: number;
  min: number;
  max: number;
  taxOnBracket: number;
  cumulativeTax: number;
  marginalRate: number;
  effectiveRate: number;
}

interface FilingStatusBrackets {
  [key: string]: {
    brackets: Omit<TaxBracket, 'taxOnBracket' | 'cumulativeTax' | 'marginalRate' | 'effectiveRate'>[];
    standardDeduction: number;
  };
}

interface TaxAnalysis {
  federalTax: number;
  stateTax: number;
  ficaTax: number;
  totalTax: number;
  effectiveRate: number;
  marginalRate: number;
  takeHome: number;
  brackets: TaxBracket[];
}

interface TaxScenario {
  id: string;
  name: string;
  income: number;
  deductions: number;
  filingStatus: string;
  state: string;
  analysis: TaxAnalysis;
}

interface TaxOptimizationSuggestion {
  id: string;
  type: 'deduction' | 'contribution' | 'timing' | 'strategy';
  title: string;
  description: string;
  potentialSavings: number;
  implementation: string[];
  priority: 'high' | 'medium' | 'low';
}

export const TaxBracketVisualizer: React.FC = () => {
  const [currentIncome, setCurrentIncome] = useState(100000);
  const [filingStatus, setFilingStatus] = useState('married_filing_jointly');
  const [stateOfResidence, setStateOfResidence] = useState('california');
  const [itemizedDeductions, setItemizedDeductions] = useState(0);
  const [scenarios, setScenarios] = useState<TaxScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('current');
  const [loading, setLoading] = useState(false);
  const [optimizationSuggestions, setOptimizationSuggestions] = useState<TaxOptimizationSuggestion[]>([]);

  // 2024 Federal Tax Brackets
  const federalTaxBrackets: FilingStatusBrackets = {
    single: {
      standardDeduction: 14600,
      brackets: [
        { rate: 10, min: 0, max: 11600 },
        { rate: 12, min: 11600, max: 47150 },
        { rate: 22, min: 47150, max: 100525 },
        { rate: 24, min: 100525, max: 191850 },
        { rate: 32, min: 191850, max: 243725 },
        { rate: 35, min: 243725, max: 731200 },
        { rate: 37, min: 731200, max: Infinity }
      ]
    },
    married_filing_jointly: {
      standardDeduction: 29200,
      brackets: [
        { rate: 10, min: 0, max: 23200 },
        { rate: 12, min: 23200, max: 94300 },
        { rate: 22, min: 94300, max: 201050 },
        { rate: 24, min: 201050, max: 383900 },
        { rate: 32, min: 383900, max: 487450 },
        { rate: 35, min: 487450, max: 731200 },
        { rate: 37, min: 731200, max: Infinity }
      ]
    },
    head_of_household: {
      standardDeduction: 21900,
      brackets: [
        { rate: 10, min: 0, max: 16550 },
        { rate: 12, min: 16550, max: 63100 },
        { rate: 22, min: 63100, max: 100500 },
        { rate: 24, min: 100500, max: 191850 },
        { rate: 32, min: 191850, max: 243700 },
        { rate: 35, min: 243700, max: 731200 },
        { rate: 37, min: 731200, max: Infinity }
      ]
    }
  };

  useEffect(() => {
    calculateTaxScenarios();
  }, [currentIncome, filingStatus, stateOfResidence, itemizedDeductions]);

  const calculateTaxScenarios = async () => {
    try {
      setLoading(true);

      const scenarios: TaxScenario[] = [
        {
          id: 'current',
          name: 'Current Income',
          income: currentIncome,
          deductions: Math.max(itemizedDeductions, federalTaxBrackets[filingStatus].standardDeduction),
          filingStatus,
          state: stateOfResidence,
          analysis: calculateTaxAnalysis(currentIncome, filingStatus, stateOfResidence, itemizedDeductions)
        },
        {
          id: 'bonus10k',
          name: '+$10K Bonus',
          income: currentIncome + 10000,
          deductions: Math.max(itemizedDeductions, federalTaxBrackets[filingStatus].standardDeduction),
          filingStatus,
          state: stateOfResidence,
          analysis: calculateTaxAnalysis(currentIncome + 10000, filingStatus, stateOfResidence, itemizedDeductions)
        },
        {
          id: 'raise20k',
          name: '+$20K Raise',
          income: currentIncome + 20000,
          deductions: Math.max(itemizedDeductions, federalTaxBrackets[filingStatus].standardDeduction),
          filingStatus,
          state: stateOfResidence,
          analysis: calculateTaxAnalysis(currentIncome + 20000, filingStatus, stateOfResidence, itemizedDeductions)
        },
        {
          id: 'maxretirement',
          name: 'Max 401k ($23K)',
          income: currentIncome - 23000,
          deductions: Math.max(itemizedDeductions, federalTaxBrackets[filingStatus].standardDeduction),
          filingStatus,
          state: stateOfResidence,
          analysis: calculateTaxAnalysis(currentIncome - 23000, filingStatus, stateOfResidence, itemizedDeductions)
        }
      ];

      setScenarios(scenarios);
      generateOptimizationSuggestions(scenarios[0]);
      
    } catch (error) {
      console.error('Failed to calculate tax scenarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateTaxAnalysis = (
    income: number, 
    filingStatus: string, 
    state: string, 
    itemizedDeductions: number
  ): TaxAnalysis => {
    const brackets = federalTaxBrackets[filingStatus];
    const standardDeduction = brackets.standardDeduction;
    const effectiveDeduction = Math.max(itemizedDeductions, standardDeduction);
    const taxableIncome = Math.max(0, income - effectiveDeduction);
    
    // Calculate federal tax with bracket information
    let federalTax = 0;
    let cumulativeTax = 0;
    const taxBrackets: TaxBracket[] = [];
    
    for (let i = 0; i < brackets.brackets.length; i++) {
      const bracket = brackets.brackets[i];
      const taxableInThisBracket = Math.min(
        Math.max(0, taxableIncome - bracket.min),
        bracket.max - bracket.min
      );
      
      const taxOnBracket = taxableInThisBracket * (bracket.rate / 100);
      federalTax += taxOnBracket;
      cumulativeTax += taxOnBracket;
      
      taxBrackets.push({
        ...bracket,
        taxOnBracket,
        cumulativeTax,
        marginalRate: taxableIncome > bracket.min ? bracket.rate : 0,
        effectiveRate: income > 0 ? (cumulativeTax / income) * 100 : 0
      });
      
      if (taxableIncome <= bracket.max) break;
    }
    
    // Calculate state tax (simplified)
    let stateTax = 0;
    if (state === 'california') {
      // CA has progressive rates, simplified calculation
      if (taxableIncome > 0) {
        if (taxableIncome <= 20198) stateTax = taxableIncome * 0.01;
        else if (taxableIncome <= 47884) stateTax = 202 + (taxableIncome - 20198) * 0.02;
        else if (taxableIncome <= 75576) stateTax = 756 + (taxableIncome - 47884) * 0.04;
        else if (taxableIncome <= 104910) stateTax = 1864 + (taxableIncome - 75576) * 0.06;
        else if (taxableIncome <= 132590) stateTax = 3624 + (taxableIncome - 104910) * 0.08;
        else stateTax = 5838 + (taxableIncome - 132590) * 0.093;
      }
    } else if (state === 'texas' || state === 'florida') {
      stateTax = 0; // No state income tax
    } else {
      // Generic state tax rate
      stateTax = taxableIncome * 0.05;
    }
    
    // Calculate FICA taxes (Social Security + Medicare)
    const socialSecurityTax = Math.min(income, 160200) * 0.062; // 2024 SS wage base
    const medicareTax = income * 0.0145;
    const additionalMedicareTax = Math.max(0, income - (filingStatus === 'married_filing_jointly' ? 250000 : 200000)) * 0.009;
    const ficaTax = socialSecurityTax + medicareTax + additionalMedicareTax;
    
    const totalTax = federalTax + stateTax + ficaTax;
    const takeHome = income - totalTax;
    const effectiveRate = income > 0 ? (totalTax / income) * 100 : 0;
    const marginalRate = getCurrentMarginalRate(taxableIncome, brackets.brackets) + getStateMarginalRate(taxableIncome, state);
    
    return {
      federalTax,
      stateTax,
      ficaTax,
      totalTax,
      effectiveRate,
      marginalRate,
      takeHome,
      brackets: taxBrackets
    };
  };

  const getCurrentMarginalRate = (taxableIncome: number, brackets: any[]): number => {
    for (let i = brackets.length - 1; i >= 0; i--) {
      if (taxableIncome > brackets[i].min) {
        return brackets[i].rate;
      }
    }
    return brackets[0].rate;
  };

  const getStateMarginalRate = (taxableIncome: number, state: string): number => {
    if (state === 'california') {
      if (taxableIncome <= 20198) return 1;
      if (taxableIncome <= 47884) return 2;
      if (taxableIncome <= 75576) return 4;
      if (taxableIncome <= 104910) return 6;
      if (taxableIncome <= 132590) return 8;
      return 9.3;
    } else if (state === 'texas' || state === 'florida') {
      return 0;
    }
    return 5; // Generic state rate
  };

  const generateOptimizationSuggestions = (currentScenario: TaxScenario) => {
    const suggestions: TaxOptimizationSuggestion[] = [];

    // 401k contribution suggestion
    const max401k = 23000;
    const current401k = Math.max(0, currentIncome - currentScenario.income);
    if (current401k < max401k) {
      const additionalContribution = max401k - current401k;
      const taxSavings = additionalContribution * (currentScenario.analysis.marginalRate / 100);
      
      suggestions.push({
        id: '401k-max',
        type: 'contribution',
        title: 'Maximize 401(k) Contributions',
        description: `Increase your 401(k) contribution by $${additionalContribution.toLocaleString()} to reach the annual limit.`,
        potentialSavings: taxSavings,
        implementation: [
          'Increase payroll deduction percentage',
          'Consider catch-up contributions if 50+',
          'Review employer matching policy'
        ],
        priority: 'high'
      });
    }

    // HSA suggestion
    if (currentIncome > 50000) {
      const hsaLimit = 4300; // Individual limit for 2024
      const hsaTaxSavings = hsaLimit * (currentScenario.analysis.marginalRate / 100);
      
      suggestions.push({
        id: 'hsa-max',
        type: 'contribution',
        title: 'Maximize HSA Contributions',
        description: 'HSAs offer triple tax benefits: deductible contributions, tax-free growth, and tax-free qualified withdrawals.',
        potentialSavings: hsaTaxSavings,
        implementation: [
          'Enroll in high-deductible health plan',
          'Set up automatic HSA contributions',
          'Use HSA for long-term investment'
        ],
        priority: 'high'
      });
    }

    // Tax loss harvesting suggestion
    suggestions.push({
      id: 'tax-loss-harvest',
      type: 'strategy',
      title: 'Implement Tax Loss Harvesting',
      description: 'Harvest investment losses to offset capital gains and up to $3,000 of ordinary income annually.',
      potentialSavings: 3000 * (currentScenario.analysis.marginalRate / 100),
      implementation: [
        'Review investment accounts for unrealized losses',
        'Avoid wash sale rules (30-day period)',
        'Consider tax-managed index funds'
      ],
      priority: 'medium'
    });

    // Itemized deductions suggestion
    const standardDeduction = federalTaxBrackets[filingStatus].standardDeduction;
    if (itemizedDeductions === 0 && currentIncome > 75000) {
      suggestions.push({
        id: 'itemized-deductions',
        type: 'deduction',
        title: 'Consider Itemizing Deductions',
        description: `Track potential itemized deductions like mortgage interest, state/local taxes, and charitable contributions.`,
        potentialSavings: 2000 * (currentScenario.analysis.marginalRate / 100),
        implementation: [
          'Track mortgage interest and property taxes',
          'Document charitable contributions',
          'Consider bunching charitable donations'
        ],
        priority: 'medium'
      });
    }

    // Roth IRA conversion suggestion
    if (currentScenario.analysis.marginalRate < 22) {
      suggestions.push({
        id: 'roth-conversion',
        type: 'timing',
        title: 'Consider Roth IRA Conversion',
        description: 'Your current tax bracket may be favorable for Roth conversions to maximize tax-free growth.',
        potentialSavings: 5000, // Estimated long-term benefit
        implementation: [
          'Analyze current vs. future tax rates',
          'Convert traditional IRA funds gradually',
          'Pay conversion taxes from taxable accounts'
        ],
        priority: 'low'
      });
    }

    setOptimizationSuggestions(suggestions);
  };

  const prepareBracketChartData = (analysis: TaxAnalysis) => {
    return analysis.brackets.map((bracket, index) => ({
      bracket: `${bracket.rate}%`,
      rate: bracket.rate,
      min: bracket.min,
      max: bracket.max === Infinity ? currentIncome * 2 : bracket.max,
      tax: bracket.taxOnBracket,
      cumulative: bracket.cumulativeTax,
      range: `$${bracket.min.toLocaleString()} - ${bracket.max === Infinity ? '∞' : `$${bracket.max.toLocaleString()}`}`,
      width: Math.min(currentIncome, bracket.max) - bracket.min
    })).filter(bracket => bracket.tax > 0);
  };

  const prepareIncomeComparisonData = () => {
    const incomes = [];
    for (let income = 50000; income <= 500000; income += 25000) {
      const analysis = calculateTaxAnalysis(income, filingStatus, stateOfResidence, itemizedDeductions);
      incomes.push({
        income,
        effectiveRate: analysis.effectiveRate,
        marginalRate: analysis.marginalRate,
        takeHome: analysis.takeHome,
        totalTax: analysis.totalTax
      });
    }
    return incomes;
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <Card id="tax-bracket-loading" className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Tax Bracket Visualizer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentScenario = scenarios.find(s => s.id === selectedScenario) || scenarios[0];

  return (
    <div id="tax-bracket-visualizer" className="w-full space-y-6">
      {/* Input Controls */}
      <Card id="tax-inputs">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Tax Bracket Visualizer
          </CardTitle>
          <CardDescription>
            Visualize your tax brackets and explore optimization opportunities.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="annual-income">Annual Income</Label>
              <div className="flex items-center gap-2">
                <span className="text-lg font-medium">$</span>
                <Input
                  id="annual-income"
                  type="number"
                  value={currentIncome}
                  onChange={(e) => setCurrentIncome(parseFloat(e.target.value) || 0)}
                  className="flex-1"
                />
              </div>
              <Slider
                value={[currentIncome]}
                onValueChange={(value) => setCurrentIncome(value[0])}
                max={500000}
                min={20000}
                step={5000}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="filing-status">Filing Status</Label>
              <Select
                value={filingStatus}
                onValueChange={setFilingStatus}
              >
                <SelectTrigger id="filing-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="single">Single</SelectItem>
                  <SelectItem value="married_filing_jointly">Married Filing Jointly</SelectItem>
                  <SelectItem value="head_of_household">Head of Household</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="state-residence">State</Label>
              <Select
                value={stateOfResidence}
                onValueChange={setStateOfResidence}
              >
                <SelectTrigger id="state-residence">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="california">California</SelectItem>
                  <SelectItem value="texas">Texas</SelectItem>
                  <SelectItem value="florida">Florida</SelectItem>
                  <SelectItem value="new_york">New York</SelectItem>
                  <SelectItem value="generic">Other State</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="itemized-deductions">Itemized Deductions</Label>
              <Input
                id="itemized-deductions"
                type="number"
                value={itemizedDeductions}
                onChange={(e) => setItemizedDeductions(parseFloat(e.target.value) || 0)}
                placeholder={`Standard: $${federalTaxBrackets[filingStatus].standardDeduction.toLocaleString()}`}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tax Summary Cards */}
      {currentScenario && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card id="federal-tax-summary">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Federal Tax</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${currentScenario.analysis.federalTax.toLocaleString()}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="effective-rate-summary">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Effective Rate</p>
                  <p className="text-2xl font-bold text-green-600">
                    {currentScenario.analysis.effectiveRate.toFixed(1)}%
                  </p>
                </div>
                <Percent className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="marginal-rate-summary">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Marginal Rate</p>
                  <p className="text-2xl font-bold text-amber-600">
                    {currentScenario.analysis.marginalRate.toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-amber-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="take-home-summary">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Take Home</p>
                  <p className="text-2xl font-bold text-purple-600">
                    ${currentScenario.analysis.takeHome.toLocaleString()}
                  </p>
                </div>
                <Target className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Visualization */}
      <Card id="tax-bracket-visualization">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Tax Bracket Analysis</CardTitle>
            <Select value={selectedScenario} onValueChange={setSelectedScenario}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {scenarios.map(scenario => (
                  <SelectItem key={scenario.id} value={scenario.id}>
                    {scenario.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="brackets" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="brackets">Tax Brackets</TabsTrigger>
              <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
              <TabsTrigger value="optimization">Optimization</TabsTrigger>
              <TabsTrigger value="planning">Planning</TabsTrigger>
            </TabsList>

            <TabsContent value="brackets" className="space-y-6">
              {/* Tax Bracket Chart */}
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={prepareBracketChartData(currentScenario.analysis)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="bracket"
                      label={{ value: 'Tax Bracket', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis 
                      tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`}
                      label={{ value: 'Tax Amount', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      formatter={(value: any, name: string) => [
                        `$${parseFloat(value).toLocaleString()}`, 
                        name === 'tax' ? 'Tax in Bracket' : 'Cumulative Tax'
                      ]}
                      labelFormatter={(label) => `${label} Tax Bracket`}
                    />
                    <Bar dataKey="tax" fill="#3b82f6" name="Tax in Bracket" />
                    <Bar dataKey="cumulative" fill="#1d4ed8" name="Cumulative Tax" opacity={0.6} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Bracket Breakdown */}
              <div className="space-y-4">
                <h4 className="font-semibold">Tax Bracket Breakdown</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {currentScenario.analysis.brackets.filter(b => b.taxOnBracket > 0).map((bracket, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <Badge variant="outline" className="text-lg font-bold">
                          {bracket.rate}%
                        </Badge>
                        <span className="text-sm text-gray-600">
                          ${bracket.min.toLocaleString()} - {bracket.max === Infinity ? '∞' : `$${bracket.max.toLocaleString()}`}
                        </span>
                      </div>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span>Tax in bracket:</span>
                          <span className="font-medium">${bracket.taxOnBracket.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Cumulative tax:</span>
                          <span className="font-medium">${bracket.cumulativeTax.toLocaleString()}</span>
                        </div>
                      </div>
                      <Progress 
                        value={Math.min(100, ((Math.min(currentIncome, bracket.max) - bracket.min) / (bracket.max - bracket.min)) * 100)}
                        className="mt-2 h-2"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="scenarios" className="space-y-6">
              {/* Scenario Comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {scenarios.map(scenario => (
                  <Card 
                    key={scenario.id} 
                    className={`cursor-pointer transition-colors ${selectedScenario === scenario.id ? 'border-blue-500 bg-blue-50' : ''}`}
                    onClick={() => setSelectedScenario(scenario.id)}
                  >
                    <CardContent className="p-4">
                      <div className="space-y-3">
                        <h3 className="font-semibold">{scenario.name}</h3>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span>Income:</span>
                            <span>${scenario.income.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Total Tax:</span>
                            <span className="text-red-600">${scenario.analysis.totalTax.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Take Home:</span>
                            <span className="text-green-600">${scenario.analysis.takeHome.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Effective Rate:</span>
                            <span>{scenario.analysis.effectiveRate.toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Income vs Tax Rate Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Tax Rates by Income Level</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={prepareIncomeComparisonData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="income"
                          tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`}
                        />
                        <YAxis 
                          label={{ value: 'Tax Rate (%)', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                          formatter={(value: any, name: string) => [
                            name.includes('Rate') ? `${parseFloat(value).toFixed(1)}%` : `$${parseFloat(value).toLocaleString()}`, 
                            name
                          ]}
                          labelFormatter={(label) => `Income: $${parseFloat(label).toLocaleString()}`}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="effectiveRate" 
                          stroke="#22c55e" 
                          strokeWidth={2}
                          name="Effective Rate"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="marginalRate" 
                          stroke="#ef4444" 
                          strokeWidth={2}
                          name="Marginal Rate"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="optimization" className="space-y-6">
              <div className="space-y-4">
                {optimizationSuggestions.map(suggestion => (
                  <Card key={suggestion.id} className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">{suggestion.title}</CardTitle>
                          <CardDescription className="mt-1">
                            {suggestion.description}
                          </CardDescription>
                        </div>
                        <Badge className={getPriorityColor(suggestion.priority)}>
                          {suggestion.priority} priority
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Potential Savings</h4>
                          <p className="text-2xl font-bold text-green-600">
                            ${suggestion.potentialSavings.toLocaleString()}
                          </p>
                          <p className="text-sm text-gray-600">per year</p>
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Implementation Steps</h4>
                          <ol className="text-sm space-y-1 list-decimal list-inside">
                            {suggestion.implementation.map((step, index) => (
                              <li key={index}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      </div>
                      <div className="flex gap-2 pt-2 border-t">
                        <Button className="flex items-center gap-2">
                          <Lightbulb className="h-4 w-4" />
                          Learn More
                        </Button>
                        <Button variant="outline">
                          Add to Plan
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="planning" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Year-End Tax Planning</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        <div className="space-y-2">
                          <p className="font-medium">Key Tax Planning Opportunities</p>
                          <ul className="list-disc list-inside space-y-1 text-sm">
                            <li>Maximize retirement contributions before year-end</li>
                            <li>Harvest tax losses to offset capital gains</li>
                            <li>Consider charitable giving strategies</li>
                            <li>Review and adjust tax withholdings</li>
                            <li>Plan Roth IRA conversions in low-income years</li>
                          </ul>
                        </div>
                      </AlertDescription>
                    </Alert>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h4 className="font-semibold">Tax-Advantaged Account Limits (2024)</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between p-2 border rounded">
                            <span>401(k) Employee Contribution:</span>
                            <span className="font-medium">$23,000</span>
                          </div>
                          <div className="flex justify-between p-2 border rounded">
                            <span>401(k) Catch-up (50+):</span>
                            <span className="font-medium">$30,500</span>
                          </div>
                          <div className="flex justify-between p-2 border rounded">
                            <span>IRA Contribution:</span>
                            <span className="font-medium">$7,000</span>
                          </div>
                          <div className="flex justify-between p-2 border rounded">
                            <span>IRA Catch-up (50+):</span>
                            <span className="font-medium">$8,000</span>
                          </div>
                          <div className="flex justify-between p-2 border rounded">
                            <span>HSA Individual:</span>
                            <span className="font-medium">$4,300</span>
                          </div>
                          <div className="flex justify-between p-2 border rounded">
                            <span>HSA Family:</span>
                            <span className="font-medium">$8,550</span>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h4 className="font-semibold">Tax Rate Analysis</h4>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span>Current Marginal Rate:</span>
                            <span className="text-xl font-bold">
                              {currentScenario.analysis.marginalRate.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Current Effective Rate:</span>
                            <span className="text-xl font-bold">
                              {currentScenario.analysis.effectiveRate.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Next Bracket Threshold:</span>
                            <span className="text-xl font-bold">
                              ${federalTaxBrackets[filingStatus].brackets
                                .find(b => b.min > currentIncome)?.min.toLocaleString() || 'Max'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};