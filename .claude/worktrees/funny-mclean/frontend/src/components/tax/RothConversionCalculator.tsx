import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Slider } from '../ui/slider';
import { Progress } from '../ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  Calendar,
  Target,
  AlertCircle,
  Info,
  Percent,
  PieChart,
  BarChart3
} from 'lucide-react';

// Types for Roth conversion analysis
interface ConversionScenario {
  id: string;
  name: string;
  conversionAmount: number;
  conversionYear: number;
  taxableIncome: number;
  currentTaxBracket: number;
  projectedTaxBracket: number;
  analysis: {
    immediateTraditionalTax: number;
    conversionTax: number;
    totalTax: number;
    effectiveTaxRate: number;
    marginalTaxRate: number;
  };
  projections: ConversionProjection[];
  breakEvenAnalysis: {
    breakEvenYear: number;
    totalSavingsAt65: number;
    totalSavingsAt70: number;
    totalSavingsAtLifeExpectancy: number;
  };
  rmdImpact: {
    currentRmdProjection: number;
    postConversionRmdProjection: number;
    rmdReduction: number;
    rmdReductionPercent: number;
  };
}

interface ConversionProjection {
  year: number;
  age: number;
  traditionalBalance: number;
  rothBalance: number;
  traditionalRmd?: number;
  rothWithdrawal?: number;
  totalTaxes: number;
  netWorth: number;
  afterTaxValue: number;
}

interface ConversionInputs {
  currentAge: number;
  retirementAge: number;
  lifeExpectancy: number;
  traditionalBalance: number;
  rothBalance: number;
  currentTaxableIncome: number;
  filingStatus: string;
  stateOfResidence: string;
  conversionAmount: number;
  conversionStrategy: 'lump_sum' | 'laddered' | 'bracket_fill';
  ladderYears?: number;
  bracketTargetLimit?: number;
}

interface TaxBracketInfo {
  bracket: number;
  min: number;
  max: number;
  available: number;
}

export const RothConversionCalculator: React.FC = () => {
  const [inputs, setInputs] = useState<ConversionInputs>({
    currentAge: 55,
    retirementAge: 65,
    lifeExpectancy: 85,
    traditionalBalance: 500000,
    rothBalance: 100000,
    currentTaxableIncome: 80000,
    filingStatus: 'married_filing_jointly',
    stateOfResidence: 'california',
    conversionAmount: 50000,
    conversionStrategy: 'lump_sum'
  });
  
  const [scenarios, setScenarios] = useState<ConversionScenario[]>([]);
  const [activeScenario, setActiveScenario] = useState<ConversionScenario | null>(null);
  const [loading, setLoading] = useState(false);
  const [taxBrackets, setTaxBrackets] = useState<TaxBracketInfo[]>([]);

  useEffect(() => {
    calculateConversionScenarios();
  }, [inputs]);

  const calculateConversionScenarios = async () => {
    try {
      setLoading(true);
      
      // Mock tax bracket data for 2024 (Married Filing Jointly)
      const mockTaxBrackets: TaxBracketInfo[] = [
        { bracket: 10, min: 0, max: 23200, available: Math.max(0, 23200 - inputs.currentTaxableIncome) },
        { bracket: 12, min: 23200, max: 94300, available: Math.max(0, Math.min(94300 - Math.max(inputs.currentTaxableIncome, 23200), inputs.conversionAmount)) },
        { bracket: 22, min: 94300, max: 201050, available: Math.max(0, Math.min(201050 - Math.max(inputs.currentTaxableIncome, 94300), inputs.conversionAmount)) },
        { bracket: 24, min: 201050, max: 383900, available: Math.max(0, Math.min(383900 - Math.max(inputs.currentTaxableIncome, 201050), inputs.conversionAmount)) },
        { bracket: 32, min: 383900, max: 487450, available: Math.max(0, Math.min(487450 - Math.max(inputs.currentTaxableIncome, 383900), inputs.conversionAmount)) },
        { bracket: 35, min: 487450, max: 731200, available: Math.max(0, Math.min(731200 - Math.max(inputs.currentTaxableIncome, 487450), inputs.conversionAmount)) },
        { bracket: 37, min: 731200, max: Infinity, available: Math.max(0, inputs.conversionAmount) }
      ];

      setTaxBrackets(mockTaxBrackets);

      // Generate scenarios
      const scenarios: ConversionScenario[] = [
        // No conversion scenario
        generateScenario('No Conversion', 0),
        // Current amount scenario
        generateScenario('Proposed Conversion', inputs.conversionAmount),
        // Bracket-filling scenario
        generateScenario('Fill Current Bracket', calculateBracketFillAmount(mockTaxBrackets)),
        // Maximum efficient scenario
        generateScenario('Maximum Efficient', Math.min(inputs.conversionAmount * 2, 100000))
      ];

      setScenarios(scenarios);
      setActiveScenario(scenarios[1]); // Default to proposed conversion
    } catch (error) {
      console.error('Failed to calculate conversion scenarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateScenario = (name: string, conversionAmount: number): ConversionScenario => {
    const currentMarginalRate = getCurrentMarginalTaxRate();
    const conversionTax = calculateConversionTax(conversionAmount);
    const projections = generateProjections(conversionAmount);
    
    return {
      id: `scenario-${name.toLowerCase().replace(/\s+/g, '-')}`,
      name,
      conversionAmount,
      conversionYear: new Date().getFullYear(),
      taxableIncome: inputs.currentTaxableIncome,
      currentTaxBracket: currentMarginalRate,
      projectedTaxBracket: estimateRetirementTaxRate(),
      analysis: {
        immediateTraditionalTax: 0, // Would be calculated when withdrawn later
        conversionTax,
        totalTax: conversionTax,
        effectiveTaxRate: conversionAmount > 0 ? (conversionTax / conversionAmount) * 100 : 0,
        marginalTaxRate: currentMarginalRate
      },
      projections,
      breakEvenAnalysis: calculateBreakEvenAnalysis(projections),
      rmdImpact: calculateRmdImpact(conversionAmount)
    };
  };

  const calculateBracketFillAmount = (brackets: TaxBracketInfo[]): number => {
    const currentBracket = brackets.find(b => 
      inputs.currentTaxableIncome >= b.min && inputs.currentTaxableIncome < b.max
    );
    return currentBracket ? Math.min(currentBracket.available, 50000) : 0;
  };

  const getCurrentMarginalTaxRate = (): number => {
    // Simplified tax bracket calculation
    if (inputs.currentTaxableIncome <= 23200) return 10;
    if (inputs.currentTaxableIncome <= 94300) return 12;
    if (inputs.currentTaxableIncome <= 201050) return 22;
    if (inputs.currentTaxableIncome <= 383900) return 24;
    if (inputs.currentTaxableIncome <= 487450) return 32;
    if (inputs.currentTaxableIncome <= 731200) return 35;
    return 37;
  };

  const calculateConversionTax = (conversionAmount: number): number => {
    if (conversionAmount === 0) return 0;
    
    let tax = 0;
    let remaining = conversionAmount;
    let taxableIncome = inputs.currentTaxableIncome;
    
    const brackets = [
      { rate: 0.10, min: 0, max: 23200 },
      { rate: 0.12, min: 23200, max: 94300 },
      { rate: 0.22, min: 94300, max: 201050 },
      { rate: 0.24, min: 201050, max: 383900 },
      { rate: 0.32, min: 383900, max: 487450 },
      { rate: 0.35, min: 487450, max: 731200 },
      { rate: 0.37, min: 731200, max: Infinity }
    ];
    
    for (const bracket of brackets) {
      if (remaining <= 0) break;
      
      const bracketStart = Math.max(bracket.min, taxableIncome);
      const bracketEnd = bracket.max;
      const availableInBracket = Math.max(0, bracketEnd - bracketStart);
      const taxableInBracket = Math.min(remaining, availableInBracket);
      
      if (taxableInBracket > 0) {
        tax += taxableInBracket * bracket.rate;
        remaining -= taxableInBracket;
        taxableIncome += taxableInBracket;
      }
    }
    
    // Add state tax (simplified - using 5% for CA)
    if (inputs.stateOfResidence === 'california') {
      tax += conversionAmount * 0.05;
    }
    
    return tax;
  };

  const estimateRetirementTaxRate = (): number => {
    // Estimate retirement tax rate based on projected RMDs and other income
    const estimatedRmd = inputs.traditionalBalance * 0.04; // Simplified RMD estimate
    const projectedRetirementIncome = estimatedRmd + (inputs.currentTaxableIncome * 0.3); // Assuming some other retirement income
    
    if (projectedRetirementIncome <= 23200) return 10;
    if (projectedRetirementIncome <= 94300) return 12;
    if (projectedRetirementIncome <= 201050) return 22;
    return 24; // Most retirees fall here
  };

  const generateProjections = (conversionAmount: number): ConversionProjection[] => {
    const projections: ConversionProjection[] = [];
    const yearsToProject = inputs.lifeExpectancy - inputs.currentAge;
    const growthRate = 0.07; // 7% annual growth assumption
    
    let traditionalBalance = inputs.traditionalBalance - conversionAmount;
    let rothBalance = inputs.rothBalance + conversionAmount;
    let totalTaxesPaid = conversionAmount > 0 ? calculateConversionTax(conversionAmount) : 0;
    
    for (let year = 0; year <= yearsToProject; year++) {
      const age = inputs.currentAge + year;
      const projectionYear = new Date().getFullYear() + year;
      
      // Apply growth
      traditionalBalance *= (1 + growthRate);
      rothBalance *= (1 + growthRate);
      
      // Calculate RMDs starting at age 73
      let traditionalRmd = 0;
      if (age >= 73) {
        const rmdFactor = getRmdFactor(age);
        traditionalRmd = traditionalBalance / rmdFactor;
        traditionalBalance -= traditionalRmd;
        totalTaxesPaid += traditionalRmd * (estimateRetirementTaxRate() / 100);
      }
      
      const netWorth = traditionalBalance + rothBalance;
      const afterTaxValue = traditionalBalance * (1 - estimateRetirementTaxRate() / 100) + rothBalance;
      
      projections.push({
        year: projectionYear,
        age,
        traditionalBalance,
        rothBalance,
        traditionalRmd: traditionalRmd > 0 ? traditionalRmd : undefined,
        totalTaxes: totalTaxesPaid,
        netWorth,
        afterTaxValue
      });
    }
    
    return projections;
  };

  const getRmdFactor = (age: number): number => {
    // Simplified RMD life expectancy factors
    const rmdTable: { [key: number]: number } = {
      73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
      78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
      83: 17.7, 84: 16.8, 85: 16.0
    };
    return rmdTable[age] || 16.0;
  };

  const calculateBreakEvenAnalysis = (projections: ConversionProjection[]) => {
    // Find break-even point where Roth strategy becomes more beneficial
    const breakEvenYear = projections.findIndex(p => p.age >= 70) + new Date().getFullYear();
    const projectionAt65 = projections.find(p => p.age === 65);
    const projectionAt70 = projections.find(p => p.age === 70);
    const projectionAtLifeExpectancy = projections.find(p => p.age === inputs.lifeExpectancy);
    
    return {
      breakEvenYear,
      totalSavingsAt65: projectionAt65?.afterTaxValue || 0,
      totalSavingsAt70: projectionAt70?.afterTaxValue || 0,
      totalSavingsAtLifeExpectancy: projectionAtLifeExpectancy?.afterTaxValue || 0
    };
  };

  const calculateRmdImpact = (conversionAmount: number) => {
    const age73Balance = inputs.traditionalBalance * Math.pow(1.07, 73 - inputs.currentAge);
    const age73BalanceAfterConversion = (inputs.traditionalBalance - conversionAmount) * Math.pow(1.07, 73 - inputs.currentAge);
    
    const currentRmdProjection = age73Balance / 26.5; // Age 73 RMD factor
    const postConversionRmdProjection = age73BalanceAfterConversion / 26.5;
    const rmdReduction = currentRmdProjection - postConversionRmdProjection;
    
    return {
      currentRmdProjection,
      postConversionRmdProjection,
      rmdReduction,
      rmdReductionPercent: (rmdReduction / currentRmdProjection) * 100
    };
  };

  const handleInputChange = (field: keyof ConversionInputs, value: any) => {
    setInputs(prev => ({ ...prev, [field]: value }));
  };

  const handleConversionAmountChange = (value: number) => {
    setInputs(prev => ({ ...prev, conversionAmount: value }));
  };

  if (loading) {
    return (
      <Card id="roth-conversion-loading" className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-6 w-6" />
            Roth Conversion Calculator
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

  return (
    <div id="roth-conversion-calculator" className="w-full space-y-6">
      <Card id="conversion-inputs">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-6 w-6" />
            Roth Conversion Calculator
          </CardTitle>
          <CardDescription>
            Analyze the tax implications and long-term benefits of Roth IRA conversions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div id="basic-info" className="space-y-4">
              <h4 className="font-semibold">Basic Information</h4>
              
              <div className="space-y-2">
                <Label htmlFor="current-age">Current Age</Label>
                <Input
                  id="current-age"
                  type="number"
                  value={inputs.currentAge}
                  onChange={(e) => handleInputChange('currentAge', parseInt(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="retirement-age">Retirement Age</Label>
                <Input
                  id="retirement-age"
                  type="number"
                  value={inputs.retirementAge}
                  onChange={(e) => handleInputChange('retirementAge', parseInt(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="filing-status">Filing Status</Label>
                <Select
                  value={inputs.filingStatus}
                  onValueChange={(value) => handleInputChange('filingStatus', value)}
                >
                  <SelectTrigger id="filing-status">
                    <SelectValue placeholder="Select filing status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="single">Single</SelectItem>
                    <SelectItem value="married_filing_jointly">Married Filing Jointly</SelectItem>
                    <SelectItem value="married_filing_separately">Married Filing Separately</SelectItem>
                    <SelectItem value="head_of_household">Head of Household</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div id="financial-info" className="space-y-4">
              <h4 className="font-semibold">Financial Information</h4>
              
              <div className="space-y-2">
                <Label htmlFor="traditional-balance">Traditional IRA/401k Balance</Label>
                <Input
                  id="traditional-balance"
                  type="number"
                  value={inputs.traditionalBalance}
                  onChange={(e) => handleInputChange('traditionalBalance', parseFloat(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="roth-balance">Roth IRA/401k Balance</Label>
                <Input
                  id="roth-balance"
                  type="number"
                  value={inputs.rothBalance}
                  onChange={(e) => handleInputChange('rothBalance', parseFloat(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="taxable-income">Current Taxable Income</Label>
                <Input
                  id="taxable-income"
                  type="number"
                  value={inputs.currentTaxableIncome}
                  onChange={(e) => handleInputChange('currentTaxableIncome', parseFloat(e.target.value))}
                />
              </div>
            </div>

            <div id="conversion-settings" className="space-y-4">
              <h4 className="font-semibold">Conversion Settings</h4>
              
              <div className="space-y-2">
                <Label htmlFor="conversion-amount">
                  Conversion Amount: ${inputs.conversionAmount.toLocaleString()}
                </Label>
                <Slider
                  id="conversion-amount"
                  value={[inputs.conversionAmount]}
                  onValueChange={(value) => handleConversionAmountChange(value[0])}
                  max={Math.min(inputs.traditionalBalance, 200000)}
                  step={1000}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="conversion-strategy">Conversion Strategy</Label>
                <Select
                  value={inputs.conversionStrategy}
                  onValueChange={(value: any) => handleInputChange('conversionStrategy', value)}
                >
                  <SelectTrigger id="conversion-strategy">
                    <SelectValue placeholder="Select strategy" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="lump_sum">Lump Sum</SelectItem>
                    <SelectItem value="laddered">Laddered (Multi-year)</SelectItem>
                    <SelectItem value="bracket_fill">Fill Tax Bracket</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Tax Bracket Visualization */}
              <div id="tax-bracket-fill" className="space-y-2">
                <Label>Current Tax Bracket Utilization</Label>
                <div className="space-y-1">
                  {taxBrackets.slice(0, 4).map((bracket, index) => {
                    const used = Math.max(0, Math.min(bracket.max, inputs.currentTaxableIncome) - bracket.min);
                    const available = bracket.max - bracket.min - used;
                    const usedPercent = (used / (bracket.max - bracket.min)) * 100;
                    
                    return (
                      <div key={index} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span>{bracket.bracket}% bracket</span>
                          <span>${available.toLocaleString()} available</span>
                        </div>
                        <Progress value={usedPercent} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scenario Comparison */}
      <Card id="scenario-comparison">
        <CardHeader>
          <CardTitle>Conversion Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeScenario?.id || scenarios[0]?.id} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              {scenarios.map((scenario) => (
                <TabsTrigger
                  key={scenario.id}
                  value={scenario.id}
                  onClick={() => setActiveScenario(scenario)}
                  className="text-xs"
                >
                  {scenario.name}
                </TabsTrigger>
              ))}
            </TabsList>

            {scenarios.map((scenario) => (
              <TabsContent key={scenario.id} value={scenario.id} className="space-y-6">
                {/* Scenario Summary */}
                <div id={`scenario-summary-${scenario.id}`} className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Conversion Amount</p>
                          <p className="text-2xl font-bold">${scenario.conversionAmount.toLocaleString()}</p>
                        </div>
                        <DollarSign className="h-8 w-8 text-blue-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Tax Cost</p>
                          <p className="text-2xl font-bold text-red-600">
                            ${scenario.analysis.conversionTax.toLocaleString()}
                          </p>
                        </div>
                        <Percent className="h-8 w-8 text-red-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">RMD Reduction</p>
                          <p className="text-2xl font-bold text-green-600">
                            {scenario.rmdImpact.rmdReductionPercent.toFixed(1)}%
                          </p>
                        </div>
                        <TrendingDown className="h-8 w-8 text-green-600" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-600">Break-Even</p>
                          <p className="text-2xl font-bold text-blue-600">
                            {scenario.breakEvenAnalysis.breakEvenYear}
                          </p>
                        </div>
                        <Target className="h-8 w-8 text-blue-600" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Tax Analysis */}
                <div id={`tax-analysis-${scenario.id}`} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Tax Analysis</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span>Current Marginal Rate:</span>
                          <span className="font-medium">{scenario.currentTaxBracket}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Projected Retirement Rate:</span>
                          <span className="font-medium">{scenario.projectedTaxBracket}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Effective Conversion Rate:</span>
                          <span className="font-medium">{scenario.analysis.effectiveTaxRate.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between pt-2 border-t">
                          <span className="font-semibold">Total Conversion Tax:</span>
                          <span className="font-semibold text-red-600">
                            ${scenario.analysis.conversionTax.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>RMD Impact Analysis</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span>Current RMD at 73:</span>
                          <span className="font-medium">
                            ${scenario.rmdImpact.currentRmdProjection.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Post-Conversion RMD:</span>
                          <span className="font-medium">
                            ${scenario.rmdImpact.postConversionRmdProjection.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between pt-2 border-t">
                          <span className="font-semibold">Annual RMD Reduction:</span>
                          <span className="font-semibold text-green-600">
                            ${scenario.rmdImpact.rmdReduction.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Projection Chart */}
                <Card id={`projection-chart-${scenario.id}`}>
                  <CardHeader>
                    <CardTitle>Long-term Projections</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={scenario.projections}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="age" />
                          <YAxis 
                            tickFormatter={(value) => `$${(value/1000000).toFixed(1)}M`}
                          />
                          <Tooltip 
                            formatter={(value: any, name: string) => [
                              `$${parseFloat(value).toLocaleString()}`, 
                              name
                            ]}
                            labelFormatter={(label) => `Age: ${label}`}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="traditionalBalance" 
                            stroke="#ef4444" 
                            strokeWidth={2}
                            name="Traditional Balance"
                          />
                          <Line 
                            type="monotone" 
                            dataKey="rothBalance" 
                            stroke="#22c55e" 
                            strokeWidth={2}
                            name="Roth Balance"
                          />
                          <Line 
                            type="monotone" 
                            dataKey="afterTaxValue" 
                            stroke="#3b82f6" 
                            strokeWidth={2}
                            name="After-Tax Value"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Key Insights */}
                <Card id={`insights-${scenario.id}`}>
                  <CardHeader>
                    <CardTitle>Key Insights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          <div className="space-y-2">
                            <p className="font-medium">
                              Conversion Tax Impact: {scenario.analysis.effectiveTaxRate.toFixed(1)}% effective rate
                            </p>
                            <p>
                              Converting ${scenario.conversionAmount.toLocaleString()} will cost 
                              ${scenario.analysis.conversionTax.toLocaleString()} in taxes this year.
                            </p>
                          </div>
                        </AlertDescription>
                      </Alert>

                      <Alert>
                        <TrendingUp className="h-4 w-4" />
                        <AlertDescription>
                          <div className="space-y-2">
                            <p className="font-medium">
                              Long-term Benefit: ${(scenario.breakEvenAnalysis.totalSavingsAtLifeExpectancy - scenario.analysis.conversionTax).toLocaleString()} net benefit
                            </p>
                            <p>
                              At life expectancy (age {inputs.lifeExpectancy}), this conversion strategy 
                              provides ${scenario.breakEvenAnalysis.totalSavingsAtLifeExpectancy.toLocaleString()} 
                              in after-tax value.
                            </p>
                          </div>
                        </AlertDescription>
                      </Alert>

                      {scenario.rmdImpact.rmdReduction > 0 && (
                        <Alert>
                          <Calendar className="h-4 w-4" />
                          <AlertDescription>
                            <div className="space-y-2">
                              <p className="font-medium">
                                RMD Reduction: {scenario.rmdImpact.rmdReductionPercent.toFixed(1)}% less required distributions
                              </p>
                              <p>
                                Starting at age 73, your required minimum distributions will be reduced by 
                                ${scenario.rmdImpact.rmdReduction.toLocaleString()} annually.
                              </p>
                            </div>
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};