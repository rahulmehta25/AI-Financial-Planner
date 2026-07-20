import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Heart, 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  Shield,
  Activity,
  Calendar,
  Target,
  AlertTriangle,
  CheckCircle,
  Plus
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface RetirementAccount {
  id: string;
  account_type: string;
  account_name: string;
  current_balance: number;
  tax_treatment: string;
}

interface HSAPlannerProps {
  accounts: RetirementAccount[];
}

interface HSAInputs {
  currentAge: number;
  retirementAge: number;
  currentBalance: number;
  monthlyContribution: number;
  employerContribution: number;
  coverageType: 'self' | 'family';
  currentHealthSpending: number;
  expectedReturn: number;
  healthInflationRate: number;
  reimburseImmediately: boolean;
}

interface HSAProjection {
  year: number;
  age: number;
  balance: number;
  contributions: number;
  medicalExpenses: number;
  reimbursements: number;
  growth: number;
}

interface MedicalExpenseCategory {
  category: string;
  amount: number;
  color: string;
}

const COVERAGE_LIMITS_2025 = {
  self: { limit: 4300, catchup: 1000 },
  family: { limit: 8550, catchup: 1000 }
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

export const HSAPlanner: React.FC<HSAPlannerProps> = ({ accounts }) => {
  const [inputs, setInputs] = useState<HSAInputs>({
    currentAge: 35,
    retirementAge: 65,
    currentBalance: 0,
    monthlyContribution: 300,
    employerContribution: 1000,
    coverageType: 'family',
    currentHealthSpending: 5000,
    expectedReturn: 0.07,
    healthInflationRate: 0.06,
    reimburseImmediately: false,
  });

  const [activeTab, setActiveTab] = useState('planner');

  // Get existing HSA accounts
  const hsaAccounts = accounts.filter(account => account.account_type === 'hsa');
  const totalHSABalance = hsaAccounts.reduce((sum, account) => sum + account.current_balance, 0);

  React.useEffect(() => {
    if (totalHSABalance > 0 && inputs.currentBalance === 0) {
      setInputs(prev => ({ ...prev, currentBalance: totalHSABalance }));
    }
  }, [totalHSABalance]);

  const getContributionLimits = () => {
    const limits = COVERAGE_LIMITS_2025[inputs.coverageType];
    const catchupEligible = inputs.currentAge >= 55;
    const maxContribution = limits.limit + (catchupEligible ? limits.catchup : 0);
    
    return {
      baseLimit: limits.limit,
      catchupLimit: catchupEligible ? limits.catchup : 0,
      maxContribution,
    };
  };

  const calculateHSAProjections = (): HSAProjection[] => {
    const projections: HSAProjection[] = [];
    let balance = inputs.currentBalance;
    const annualContribution = (inputs.monthlyContribution * 12) + inputs.employerContribution;
    let medicalExpenses = inputs.currentHealthSpending;
    const limits = getContributionLimits();
    
    for (let year = 0; year <= inputs.retirementAge - inputs.currentAge + 20; year++) {
      const age = inputs.currentAge + year;
      const isRetired = age >= inputs.retirementAge;
      const isMedicare = age >= 65;
      
      // Stop HSA contributions at Medicare eligibility
      const yearlyContribution = isMedicare ? 0 : Math.min(annualContribution, limits.maxContribution);
      
      // Medical expenses grow with health inflation
      const yearlyMedicalExpenses = medicalExpenses * Math.pow(1 + inputs.healthInflationRate, year);
      
      // Reimbursement strategy
      let reimbursements = 0;
      if (inputs.reimburseImmediately) {
        reimbursements = Math.min(yearlyMedicalExpenses, balance + yearlyContribution);
      } else if (isRetired) {
        // In retirement, use HSA for medical expenses
        reimbursements = Math.min(yearlyMedicalExpenses, balance);
      }
      
      // Investment growth
      const yearlyGrowth = (balance + yearlyContribution - reimbursements) * inputs.expectedReturn;
      
      projections.push({
        year,
        age,
        balance: balance + yearlyContribution - reimbursements + yearlyGrowth,
        contributions: yearlyContribution,
        medicalExpenses: yearlyMedicalExpenses,
        reimbursements,
        growth: yearlyGrowth,
      });
      
      balance = balance + yearlyContribution - reimbursements + yearlyGrowth;
    }
    
    return projections;
  };

  const getTypicalMedicalExpenses = (): MedicalExpenseCategory[] => {
    const baseAmount = inputs.currentHealthSpending;
    return [
      { category: 'Doctor Visits', amount: baseAmount * 0.25, color: COLORS[0] },
      { category: 'Prescriptions', amount: baseAmount * 0.30, color: COLORS[1] },
      { category: 'Dental Care', amount: baseAmount * 0.15, color: COLORS[2] },
      { category: 'Vision Care', amount: baseAmount * 0.10, color: COLORS[3] },
      { category: 'Specialists', amount: baseAmount * 0.15, color: COLORS[4] },
      { category: 'Other', amount: baseAmount * 0.05, color: COLORS[5] },
    ];
  };

  const getRetirementHealthcareCosts = () => {
    // Fidelity estimates $300,000+ for healthcare costs in retirement
    const yearsInRetirement = 20; // Average
    const retirementHealthcareTotal = 315000; // Fidelity 2023 estimate
    const currentValue = retirementHealthcareTotal / Math.pow(1 + inputs.healthInflationRate, inputs.retirementAge - inputs.currentAge);
    
    return {
      totalCost: retirementHealthcareTotal,
      currentValue,
      annualCost: retirementHealthcareTotal / yearsInRetirement,
    };
  };

  const calculateTaxSavings = () => {
    const annualContribution = (inputs.monthlyContribution * 12) + inputs.employerContribution;
    const limits = getContributionLimits();
    const actualContribution = Math.min(annualContribution, limits.maxContribution);
    
    // Assume 22% federal + 6% state tax rate
    const marginalRate = 0.28;
    const annualTaxSavings = actualContribution * marginalRate;
    
    // Payroll tax savings (7.65% for employee portion)
    const payrollTaxSavings = (inputs.monthlyContribution * 12) * 0.0765;
    
    return {
      incomeTaxSavings: annualTaxSavings,
      payrollTaxSavings,
      totalAnnualSavings: annualTaxSavings + payrollTaxSavings,
    };
  };

  const hsaProjections = calculateHSAProjections();
  const medicalExpenseBreakdown = getTypicalMedicalExpenses();
  const retirementHealthcare = getRetirementHealthcareCosts();
  const taxSavings = calculateTaxSavings();
  const limits = getContributionLimits();
  
  const finalBalance = hsaProjections[hsaProjections.length - 1]?.balance || 0;
  const retirementBalance = hsaProjections.find(p => p.age === inputs.retirementAge)?.balance || 0;
  const currentAnnualContribution = (inputs.monthlyContribution * 12) + inputs.employerContribution;
  const contributionUtilization = (currentAnnualContribution / limits.maxContribution) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Heart className="h-8 w-8 text-red-600" />
        <div>
          <h2 className="text-2xl font-bold">HSA Planning</h2>
          <p className="text-muted-foreground">
            Maximize your Health Savings Account's triple tax advantage for healthcare and retirement
          </p>
        </div>
      </div>

      {/* Existing HSA Accounts Summary */}
      {hsaAccounts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Your HSA Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {hsaAccounts.map(account => (
                <div key={account.id} className="p-3 border rounded-lg">
                  <div className="font-medium">{account.account_name}</div>
                  <div className="text-2xl font-bold">{formatCurrency(account.current_balance)}</div>
                  <Badge variant="secondary">HSA</Badge>
                </div>
              ))}
              <div className="p-3 border rounded-lg bg-muted">
                <div className="font-medium">Total HSA Balance</div>
                <div className="text-2xl font-bold">{formatCurrency(totalHSABalance)}</div>
                <Badge variant="outline">Combined</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="planner">HSA Planner</TabsTrigger>
          <TabsTrigger value="strategy">Strategy</TabsTrigger>
          <TabsTrigger value="expenses">Medical Expenses</TabsTrigger>
        </TabsList>

        <TabsContent value="planner" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Form */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>HSA Planning Inputs</CardTitle>
                <CardDescription>Configure your HSA savings strategy</CardDescription>
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
                  <Label htmlFor="currentBalance">Current HSA Balance</Label>
                  <Input
                    id="currentBalance"
                    type="number"
                    min="0"
                    step="100"
                    value={inputs.currentBalance}
                    onChange={(e) => setInputs({ ...inputs, currentBalance: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="coverageType">Coverage Type</Label>
                  <Select
                    value={inputs.coverageType}
                    onValueChange={(value: 'self' | 'family') => setInputs({ ...inputs, coverageType: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="self">Self-Only Coverage</SelectItem>
                      <SelectItem value="family">Family Coverage</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="text-sm text-muted-foreground">
                    2025 limit: {formatCurrency(COVERAGE_LIMITS_2025[inputs.coverageType].limit)}
                    {inputs.currentAge >= 55 && ` + ${formatCurrency(COVERAGE_LIMITS_2025[inputs.coverageType].catchup)} catch-up`}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="monthlyContribution">Monthly Employee Contribution</Label>
                  <Input
                    id="monthlyContribution"
                    type="number"
                    min="0"
                    step="25"
                    value={inputs.monthlyContribution}
                    onChange={(e) => setInputs({ ...inputs, monthlyContribution: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="employerContribution">Annual Employer Contribution</Label>
                  <Input
                    id="employerContribution"
                    type="number"
                    min="0"
                    step="100"
                    value={inputs.employerContribution}
                    onChange={(e) => setInputs({ ...inputs, employerContribution: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="currentHealthSpending">Current Annual Health Spending</Label>
                  <Input
                    id="currentHealthSpending"
                    type="number"
                    min="0"
                    step="100"
                    value={inputs.currentHealthSpending}
                    onChange={(e) => setInputs({ ...inputs, currentHealthSpending: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="expectedReturn">Expected Annual Return (%)</Label>
                  <Input
                    id="expectedReturn"
                    type="number"
                    min="1"
                    max="12"
                    step="0.1"
                    value={(inputs.expectedReturn * 100).toFixed(1)}
                    onChange={(e) => setInputs({ ...inputs, expectedReturn: (parseFloat(e.target.value) || 0) / 100 })}
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="reimburseImmediately"
                    checked={inputs.reimburseImmediately}
                    onChange={(e) => setInputs({ ...inputs, reimburseImmediately: e.target.checked })}
                  />
                  <Label htmlFor="reimburseImmediately">Reimburse medical expenses immediately</Label>
                </div>
                <div className="text-sm text-muted-foreground">
                  Unchecked: Invest HSA and pay out-of-pocket for maximum growth (recommended)
                </div>
              </CardContent>
            </Card>

            {/* Results */}
            <div className="lg:col-span-2 space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Projected HSA at 65</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(retirementBalance)}</div>
                    <p className="text-xs text-muted-foreground">At retirement</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Healthcare Cost Coverage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {((retirementBalance / retirementHealthcare.totalCost) * 100).toFixed(0)}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Of estimated {formatCurrency(retirementHealthcare.totalCost)}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Annual Tax Savings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(taxSavings.totalAnnualSavings)}</div>
                    <p className="text-xs text-muted-foreground">
                      Income + payroll taxes
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Contribution Room</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(limits.maxContribution - currentAnnualContribution)}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Remaining for 2025
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Contribution Progress */}
              <Card>
                <CardHeader>
                  <CardTitle>2025 HSA Contribution Progress</CardTitle>
                  <CardDescription>
                    Track your progress toward the annual contribution limit
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Annual Contributions</span>
                      <span>{formatCurrency(currentAnnualContribution)} / {formatCurrency(limits.maxContribution)}</span>
                    </div>
                    <Progress value={contributionUtilization} className="h-3" />
                    <div className="text-sm text-muted-foreground">
                      {contributionUtilization >= 100 ? 
                        'Fully maximized!' :
                        `${formatCurrency(limits.maxContribution - currentAnnualContribution)} remaining`
                      }
                    </div>
                  </div>

                  {contributionUtilization < 100 && (
                    <Alert>
                      <Target className="h-4 w-4" />
                      <AlertDescription>
                        Consider increasing contributions by {formatCurrency((limits.maxContribution - currentAnnualContribution) / 12)}/month 
                        to maximize your triple tax advantage and save an additional {formatCurrency((limits.maxContribution - currentAnnualContribution) * 0.28)} in taxes.
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* HSA Growth Projection */}
              <Card>
                <CardHeader>
                  <CardTitle>HSA Balance Growth</CardTitle>
                  <CardDescription>
                    Projected HSA growth with your current contribution strategy
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={hsaProjections.filter((_, index) => index % 2 === 0)}>
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
                          strokeWidth={3}
                          name="HSA Balance"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="medicalExpenses" 
                          stroke="#82ca9d" 
                          strokeWidth={2}
                          name="Annual Medical Costs"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Tax Savings Breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Annual Tax Savings Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{formatCurrency(taxSavings.incomeTaxSavings)}</div>
                      <div className="text-sm text-muted-foreground">Federal + State Income Tax</div>
                      <div className="text-xs text-muted-foreground">~28% marginal rate</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{formatCurrency(taxSavings.payrollTaxSavings)}</div>
                      <div className="text-sm text-muted-foreground">Payroll Tax (FICA)</div>
                      <div className="text-xs text-muted-foreground">7.65% on employee contributions</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">{formatCurrency(taxSavings.totalAnnualSavings)}</div>
                      <div className="text-sm text-muted-foreground">Total Annual Savings</div>
                      <div className="text-xs text-muted-foreground">Triple tax advantage</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="strategy" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  Triple Tax Advantage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-green-600">1. Tax-Deductible Contributions</h4>
                    <p className="text-sm text-muted-foreground">
                      Contributions reduce your taxable income dollar-for-dollar. Save on federal, state, and payroll taxes.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-green-600">2. Tax-Free Growth</h4>
                    <p className="text-sm text-muted-foreground">
                      Investment earnings grow tax-free while invested in your HSA. No capital gains taxes on growth.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-green-600">3. Tax-Free Withdrawals</h4>
                    <p className="text-sm text-muted-foreground">
                      Withdrawals for qualified medical expenses are tax-free at any age. After 65, non-medical withdrawals are taxed like traditional IRA.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                  Optimal HSA Strategy
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 border border-green-200 bg-green-50 rounded-lg">
                    <h4 className="font-semibold text-green-800">Max Contributions</h4>
                    <p className="text-sm text-green-700">
                      Contribute the maximum allowed: {formatCurrency(limits.maxContribution)} for 2025
                    </p>
                  </div>
                  <div className="p-3 border border-blue-200 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-blue-800">Invest, Don't Spend</h4>
                    <p className="text-sm text-blue-700">
                      Pay medical expenses out-of-pocket and invest HSA funds for maximum growth
                    </p>
                  </div>
                  <div className="p-3 border border-purple-200 bg-purple-50 rounded-lg">
                    <h4 className="font-semibold text-purple-800">Save Receipts</h4>
                    <p className="text-sm text-purple-700">
                      Keep receipts to reimburse yourself tax-free later, creating a tax-free withdrawal mechanism
                    </p>
                  </div>
                  <div className="p-3 border border-orange-200 bg-orange-50 rounded-lg">
                    <h4 className="font-semibold text-orange-800">Retirement Asset at 65+</h4>
                    <p className="text-sm text-orange-700">
                      After 65, HSA becomes like a traditional IRA for non-medical expenses (taxed but no penalty)
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>HSA vs. Other Retirement Accounts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Feature</th>
                        <th className="text-left p-2">HSA</th>
                        <th className="text-left p-2">401(k)</th>
                        <th className="text-left p-2">Roth IRA</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="p-2">Tax Deduction</td>
                        <td className="p-2 text-green-600">✓</td>
                        <td className="p-2 text-green-600">✓</td>
                        <td className="p-2 text-red-600">✗</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2">Tax-Free Growth</td>
                        <td className="p-2 text-green-600">✓</td>
                        <td className="p-2 text-green-600">✓</td>
                        <td className="p-2 text-green-600">✓</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2">Tax-Free Withdrawals</td>
                        <td className="p-2 text-green-600">✓*</td>
                        <td className="p-2 text-red-600">✗</td>
                        <td className="p-2 text-green-600">✓</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2">Required Distributions</td>
                        <td className="p-2 text-green-600">None</td>
                        <td className="p-2 text-orange-600">Age 73</td>
                        <td className="p-2 text-green-600">None</td>
                      </tr>
                      <tr>
                        <td className="p-2">Early Withdrawal Penalty</td>
                        <td className="p-2 text-green-600">None*</td>
                        <td className="p-2 text-red-600">10%</td>
                        <td className="p-2 text-orange-600">Earnings only</td>
                      </tr>
                    </tbody>
                  </table>
                  <p className="text-xs text-muted-foreground mt-2">
                    * For qualified medical expenses
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Retirement Healthcare Planning</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Alert>
                    <Heart className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Healthcare costs in retirement:</strong> The average couple needs approximately 
                      {formatCurrency(retirementHealthcare.totalCost)} for healthcare expenses in retirement (Fidelity, 2023).
                    </AlertDescription>
                  </Alert>
                  
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold">{formatCurrency(retirementHealthcare.annualCost)}</div>
                      <div className="text-sm text-muted-foreground">Estimated Annual Healthcare Cost</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold">
                        {((retirementBalance / retirementHealthcare.totalCost) * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Coverage with Current Plan</div>
                    </div>
                  </div>
                  
                  {retirementBalance < retirementHealthcare.totalCost && (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Consider increasing HSA contributions to better cover estimated healthcare costs in retirement. 
                        You're currently projected to cover {((retirementBalance / retirementHealthcare.totalCost) * 100).toFixed(0)}% 
                        of expected costs.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="expenses" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Current Medical Expense Breakdown</CardTitle>
                <CardDescription>
                  Based on your annual spending of {formatCurrency(inputs.currentHealthSpending)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={medicalExpenseBreakdown}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="amount"
                      >
                        {medicalExpenseBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Qualified HSA Expenses</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div>
                    <h4 className="font-semibold text-green-600">Medical Care</h4>
                    <ul className="list-disc list-inside ml-2 text-muted-foreground">
                      <li>Doctor visits and specialists</li>
                      <li>Hospital services and surgery</li>
                      <li>Emergency room visits</li>
                      <li>Ambulance services</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-green-600">Prescriptions & Supplies</h4>
                    <ul className="list-disc list-inside ml-2 text-muted-foreground">
                      <li>Prescription medications</li>
                      <li>Medical equipment and supplies</li>
                      <li>First aid kits and bandages</li>
                      <li>Blood pressure monitors</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-green-600">Dental & Vision</h4>
                    <ul className="list-disc list-inside ml-2 text-muted-foreground">
                      <li>Dental cleanings and procedures</li>
                      <li>Eye exams and glasses</li>
                      <li>Contact lenses and solution</li>
                      <li>Orthodontic treatment</li>
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-green-600">Mental Health</h4>
                    <ul className="list-disc list-inside ml-2 text-muted-foreground">
                      <li>Therapy and counseling</li>
                      <li>Mental health medications</li>
                      <li>Substance abuse treatment</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Receipt Management Strategy</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Pro Tip:</strong> Save all medical receipts, even if you don't reimburse immediately. 
                      You can reimburse yourself tax-free years later, creating a tax-free withdrawal mechanism.
                    </AlertDescription>
                  </Alert>
                  
                  <div className="space-y-3">
                    <div className="p-3 border border-blue-200 bg-blue-50 rounded-lg">
                      <h4 className="font-semibold text-blue-800">Digital Storage</h4>
                      <p className="text-sm text-blue-700">
                        Use apps like HSAbank Mobile, Shoeboxed, or Evernote to store receipt images with dates and amounts.
                      </p>
                    </div>
                    
                    <div className="p-3 border border-green-200 bg-green-50 rounded-lg">
                      <h4 className="font-semibold text-green-800">Organization</h4>
                      <p className="text-sm text-green-700">
                        Create folders by year and expense type. Include provider name, service date, and amount paid.
                      </p>
                    </div>
                    
                    <div className="p-3 border border-purple-200 bg-purple-50 rounded-lg">
                      <h4 className="font-semibold text-purple-800">No Time Limit</h4>
                      <p className="text-sm text-purple-700">
                        HSA reimbursements have no time limit. Save receipts from today and reimburse in retirement tax-free.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>HSA Investment Strategy</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div className="p-3 border border-orange-200 bg-orange-50 rounded-lg">
                      <div className="text-lg font-bold">$1,000-$2,000</div>
                      <div className="text-sm text-orange-700">Cash Cushion</div>
                      <div className="text-xs text-muted-foreground">For immediate expenses</div>
                    </div>
                    <div className="p-3 border border-green-200 bg-green-50 rounded-lg">
                      <div className="text-lg font-bold">Remainder</div>
                      <div className="text-sm text-green-700">Invest for Growth</div>
                      <div className="text-xs text-muted-foreground">Long-term portfolio</div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-semibold">Recommended HSA Investment Allocation:</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Ages 20-40:</span>
                        <span>80-90% Stocks, 10-20% Bonds</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Ages 40-55:</span>
                        <span>60-70% Stocks, 30-40% Bonds</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Ages 55-65:</span>
                        <span>40-50% Stocks, 50-60% Bonds</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Ages 65+:</span>
                        <span>30-40% Stocks, 60-70% Bonds</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};