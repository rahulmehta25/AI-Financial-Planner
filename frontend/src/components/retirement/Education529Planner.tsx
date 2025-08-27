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
  BookOpen, 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  GraduationCap,
  MapPin,
  Calendar,
  Target,
  AlertTriangle,
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

interface Education529PlannerProps {
  accounts: RetirementAccount[];
}

interface EducationInputs {
  childAge: number;
  yearsToCollege: number;
  currentCollegeCost: number;
  educationInflationRate: number;
  expectedReturn: number;
  monthlyContribution: number;
  currentSavings: number;
  statePlan: string;
  isStateResident: boolean;
  numberOfChildren: number;
}

interface CollegeCostProjection {
  year: number;
  childAge: number;
  collegeYear: string;
  annualCost: number;
  cumulativeCost: number;
}

interface SavingsProjection {
  year: number;
  age: number;
  balance: number;
  contributions: number;
  growth: number;
}

const STATE_PLANS = [
  { value: 'CA', label: 'California (ScholarShare)', deduction: 0, limit: 529000 },
  { value: 'NY', label: 'New York (Direct Plan)', deduction: 10000, limit: 520000 },
  { value: 'VA', label: 'Virginia (Invest529)', deduction: 4000, limit: 500000 },
  { value: 'UT', label: 'Utah (my529)', deduction: 5920, limit: 540000 },
  { value: 'NV', label: 'Nevada (Vanguard 529)', deduction: 0, limit: 500000 },
  { value: 'IL', label: 'Illinois (Bright Start)', deduction: 10000, limit: 500000 },
];

const COLLEGE_TYPES = [
  { type: 'public_instate', label: 'Public In-State', avgCost: 28775 },
  { type: 'public_outstate', label: 'Public Out-of-State', avgCost: 46730 },
  { type: 'private', label: 'Private University', avgCost: 60420 },
  { type: 'community', label: 'Community College', avgCost: 4130 },
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

export const Education529Planner: React.FC<Education529PlannerProps> = ({ accounts }) => {
  const [inputs, setInputs] = useState<EducationInputs>({
    childAge: 5,
    yearsToCollege: 13,
    currentCollegeCost: 46730, // Average public out-of-state
    educationInflationRate: 0.05,
    expectedReturn: 0.06,
    monthlyContribution: 300,
    currentSavings: 0,
    statePlan: 'CA',
    isStateResident: true,
    numberOfChildren: 1,
  });

  const [activeTab, setActiveTab] = useState('planner');

  // Get existing 529 accounts
  const plan529Accounts = accounts.filter(account => account.account_type === 'education_529');
  const total529Balance = plan529Accounts.reduce((sum, account) => sum + account.current_balance, 0);

  React.useEffect(() => {
    if (total529Balance > 0 && inputs.currentSavings === 0) {
      setInputs(prev => ({ ...prev, currentSavings: total529Balance }));
    }
  }, [total529Balance]);

  const calculateCollegeCosts = (): CollegeCostProjection[] => {
    const costs: CollegeCostProjection[] = [];
    let cumulativeCost = 0;
    
    // Calculate costs for 4 years of college
    for (let i = 0; i < 4; i++) {
      const yearsFromNow = inputs.yearsToCollege + i;
      const inflatedCost = inputs.currentCollegeCost * Math.pow(1 + inputs.educationInflationRate, yearsFromNow);
      cumulativeCost += inflatedCost;
      
      costs.push({
        year: yearsFromNow,
        childAge: inputs.childAge + yearsFromNow,
        collegeYear: `Year ${i + 1}`,
        annualCost: inflatedCost,
        cumulativeCost: cumulativeCost,
      });
    }
    
    return costs;
  };

  const calculateSavingsGrowth = (): SavingsProjection[] => {
    const projections: SavingsProjection[] = [];
    let balance = inputs.currentSavings;
    const annualContribution = inputs.monthlyContribution * 12;
    
    for (let year = 0; year <= inputs.yearsToCollege; year++) {
      const age = inputs.childAge + year;
      const yearlyGrowth = balance * inputs.expectedReturn;
      
      projections.push({
        year,
        age,
        balance,
        contributions: year > 0 ? annualContribution : 0,
        growth: year > 0 ? yearlyGrowth : 0,
      });
      
      if (year < inputs.yearsToCollege) {
        balance += annualContribution;
        balance *= (1 + inputs.expectedReturn);
      }
    }
    
    return projections;
  };

  const getStateTaxBenefit = () => {
    const selectedState = STATE_PLANS.find(state => state.value === inputs.statePlan);
    if (!selectedState || !inputs.isStateResident) return 0;
    
    const annualContribution = inputs.monthlyContribution * 12;
    const deductibleAmount = Math.min(annualContribution, selectedState.deduction);
    
    // Assume 6% state tax rate (average)
    return deductibleAmount * 0.06;
  };

  const collegeCosts = calculateCollegeCosts();
  const savingsProjections = calculateSavingsGrowth();
  const finalBalance = savingsProjections[savingsProjections.length - 1]?.balance || 0;
  const totalCollegeCost = collegeCosts.reduce((sum, cost) => sum + cost.annualCost, 0);
  const shortfall = Math.max(0, totalCollegeCost - finalBalance);
  const coverageRatio = totalCollegeCost > 0 ? (finalBalance / totalCollegeCost) * 100 : 0;
  const annualStateTaxSavings = getStateTaxBenefit();

  const getExpenseBreakdown = () => {
    return [
      { name: 'Tuition & Fees', value: inputs.currentCollegeCost * 0.35, color: COLORS[0] },
      { name: 'Room & Board', value: inputs.currentCollegeCost * 0.30, color: COLORS[1] },
      { name: 'Books & Supplies', value: inputs.currentCollegeCost * 0.10, color: COLORS[2] },
      { name: 'Transportation', value: inputs.currentCollegeCost * 0.10, color: COLORS[3] },
      { name: 'Personal Expenses', value: inputs.currentCollegeCost * 0.15, color: COLORS[4] },
    ];
  };

  const getRecommendedContribution = () => {
    const totalNeeded = totalCollegeCost - inputs.currentSavings;
    const yearsRemaining = inputs.yearsToCollege;
    
    if (yearsRemaining <= 0) return 0;
    
    // Calculate payment needed using future value of annuity formula
    const rate = inputs.expectedReturn;
    const n = yearsRemaining;
    
    if (rate === 0) {
      return totalNeeded / n / 12;
    }
    
    const fvAnnuityFactor = (Math.pow(1 + rate, n) - 1) / rate;
    const recommendedAnnual = totalNeeded / fvAnnuityFactor;
    
    return Math.max(0, recommendedAnnual / 12);
  };

  const recommendedMonthly = getRecommendedContribution();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <GraduationCap className="h-8 w-8 text-blue-600" />
        <div>
          <h2 className="text-2xl font-bold">529 Education Planning</h2>
          <p className="text-muted-foreground">
            Plan and optimize your child's education savings with tax-advantaged 529 plans
          </p>
        </div>
      </div>

      {/* Existing 529 Accounts Summary */}
      {plan529Accounts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Your 529 Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plan529Accounts.map(account => (
                <div key={account.id} className="p-3 border rounded-lg">
                  <div className="font-medium">{account.account_name}</div>
                  <div className="text-2xl font-bold">{formatCurrency(account.current_balance)}</div>
                  <Badge variant="secondary">529 Plan</Badge>
                </div>
              ))}
              <div className="p-3 border rounded-lg bg-muted">
                <div className="font-medium">Total 529 Savings</div>
                <div className="text-2xl font-bold">{formatCurrency(total529Balance)}</div>
                <Badge variant="outline">Combined</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="planner">Education Planner</TabsTrigger>
          <TabsTrigger value="states">State Plans</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
        </TabsList>

        <TabsContent value="planner" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Form */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Planning Inputs</CardTitle>
                <CardDescription>Enter your education savings goals</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="childAge">Child's Age</Label>
                    <Input
                      id="childAge"
                      type="number"
                      min="0"
                      max="17"
                      value={inputs.childAge}
                      onChange={(e) => {
                        const age = parseInt(e.target.value) || 0;
                        setInputs({ 
                          ...inputs, 
                          childAge: age,
                          yearsToCollege: Math.max(0, 18 - age)
                        });
                      }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="yearsToCollege">Years to College</Label>
                    <Input
                      id="yearsToCollege"
                      type="number"
                      min="0"
                      max="20"
                      value={inputs.yearsToCollege}
                      onChange={(e) => setInputs({ ...inputs, yearsToCollege: parseInt(e.target.value) || 0 })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="collegeType">College Type</Label>
                  <Select
                    value={inputs.currentCollegeCost.toString()}
                    onValueChange={(value) => setInputs({ ...inputs, currentCollegeCost: parseFloat(value) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {COLLEGE_TYPES.map((type) => (
                        <SelectItem key={type.type} value={type.avgCost.toString()}>
                          {type.label} - {formatCurrency(type.avgCost)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="currentSavings">Current 529 Savings</Label>
                  <Input
                    id="currentSavings"
                    type="number"
                    min="0"
                    step="100"
                    value={inputs.currentSavings}
                    onChange={(e) => setInputs({ ...inputs, currentSavings: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="monthlyContribution">Monthly Contribution</Label>
                  <Input
                    id="monthlyContribution"
                    type="number"
                    min="0"
                    step="25"
                    value={inputs.monthlyContribution}
                    onChange={(e) => setInputs({ ...inputs, monthlyContribution: parseFloat(e.target.value) || 0 })}
                  />
                  {recommendedMonthly > inputs.monthlyContribution && (
                    <p className="text-sm text-muted-foreground">
                      Recommended: {formatCurrency(recommendedMonthly)}/month to fully fund college
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="statePlan">State Plan</Label>
                  <Select
                    value={inputs.statePlan}
                    onValueChange={(value) => setInputs({ ...inputs, statePlan: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STATE_PLANS.map((state) => (
                        <SelectItem key={state.value} value={state.value}>
                          {state.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="isStateResident"
                    checked={inputs.isStateResident}
                    onChange={(e) => setInputs({ ...inputs, isStateResident: e.target.checked })}
                  />
                  <Label htmlFor="isStateResident">State resident (for tax benefits)</Label>
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
              </CardContent>
            </Card>

            {/* Results */}
            <div className="lg:col-span-2 space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Projected Savings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(finalBalance)}</div>
                    <p className="text-xs text-muted-foreground">At college start</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Total College Cost</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(totalCollegeCost)}</div>
                    <p className="text-xs text-muted-foreground">4-year estimate</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Coverage Ratio</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{coverageRatio.toFixed(0)}%</div>
                    <p className="text-xs text-muted-foreground">
                      {shortfall > 0 ? `Shortfall: ${formatCurrency(shortfall)}` : 'Fully covered'}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Tax Benefits</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(annualStateTaxSavings)}</div>
                    <p className="text-xs text-muted-foreground">Annual state savings</p>
                  </CardContent>
                </Card>
              </div>

              {/* Coverage Progress */}
              <Card>
                <CardHeader>
                  <CardTitle>Education Funding Progress</CardTitle>
                  <CardDescription>
                    Track your progress toward funding your child's education
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Projected Savings vs. College Costs</span>
                      <span>{formatCurrency(finalBalance)} / {formatCurrency(totalCollegeCost)}</span>
                    </div>
                    <Progress value={Math.min(100, coverageRatio)} className="h-3" />
                    <div className="text-sm text-muted-foreground">
                      {coverageRatio >= 100 ? 
                        `Fully funded with ${formatCurrency(finalBalance - totalCollegeCost)} surplus` :
                        `${formatCurrency(shortfall)} shortfall remaining`
                      }
                    </div>
                  </div>

                  {shortfall > 0 && (
                    <Alert>
                      <Target className="h-4 w-4" />
                      <AlertDescription>
                        To close the gap, consider increasing monthly contributions to {formatCurrency(recommendedMonthly)} 
                        or starting with a {formatCurrency(shortfall / Math.pow(1 + inputs.expectedReturn, inputs.yearsToCollege))} lump sum.
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* Savings Growth Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Savings Growth Projection</CardTitle>
                  <CardDescription>
                    How your 529 savings will grow over time
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={savingsProjections}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="age" 
                          label={{ value: "Child's Age", position: 'insideBottom', offset: -10 }}
                        />
                        <YAxis tickFormatter={(value) => formatCurrency(value)} />
                        <Tooltip 
                          formatter={(value, name) => [formatCurrency(Number(value)), name]}
                          labelFormatter={(age) => `Child Age: ${age}`}
                        />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="balance" 
                          stroke="#8884d8" 
                          strokeWidth={3}
                          name="Account Balance"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* College Cost Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>College Cost Timeline</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {collegeCosts.map((cost) => (
                        <div key={cost.year} className="flex justify-between items-center p-2 border rounded">
                          <div>
                            <div className="font-medium">{cost.collegeYear}</div>
                            <div className="text-sm text-muted-foreground">Age {cost.childAge}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-medium">{formatCurrency(cost.annualCost)}</div>
                            <div className="text-sm text-muted-foreground">
                              Total: {formatCurrency(cost.cumulativeCost)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>College Expense Breakdown</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={getExpenseBreakdown()}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {getExpenseBreakdown().map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="states" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                State 529 Plan Comparison
              </CardTitle>
              <CardDescription>
                Compare features and benefits of different state 529 plans
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-muted">
                      <th className="border border-gray-300 p-3 text-left">State</th>
                      <th className="border border-gray-300 p-3 text-left">Plan Name</th>
                      <th className="border border-gray-300 p-3 text-left">State Tax Deduction</th>
                      <th className="border border-gray-300 p-3 text-left">Contribution Limit</th>
                      <th className="border border-gray-300 p-3 text-left">Key Features</th>
                    </tr>
                  </thead>
                  <tbody>
                    {STATE_PLANS.map((state) => (
                      <tr key={state.value}>
                        <td className="border border-gray-300 p-3 font-medium">{state.value}</td>
                        <td className="border border-gray-300 p-3">{state.label}</td>
                        <td className="border border-gray-300 p-3">
                          {state.deduction > 0 ? formatCurrency(state.deduction) : 'None'}
                        </td>
                        <td className="border border-gray-300 p-3">{formatCurrency(state.limit)}</td>
                        <td className="border border-gray-300 p-3">
                          {state.value === 'CA' && 'No state tax deduction, but no state income tax on withdrawals'}
                          {state.value === 'NY' && 'High deduction limit, age-based portfolios'}
                          {state.value === 'VA' && 'Solid deduction, low fees'}
                          {state.value === 'UT' && 'Low fees, Vanguard options'}
                          {state.value === 'NV' && 'Vanguard managed, low costs'}
                          {state.value === 'IL' && 'High deduction, age-based options'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="strategies" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Superfunding Strategy</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  Contribute 5 years' worth of gifts upfront to maximize growth time.
                </p>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Maximum 5-Year Gift:</span>
                    <span className="font-medium">{formatCurrency(90000)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Projected Growth:</span>
                    <span className="font-medium">
                      {formatCurrency(90000 * Math.pow(1 + inputs.expectedReturn, inputs.yearsToCollege))}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Single person can gift $18,000/year × 5 years = $90,000 without gift tax
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Grandparent Strategy</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  Have grandparents contribute to avoid impact on financial aid calculations.
                </p>
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Grandparent-owned 529 distributions count as student income for FAFSA, 
                    potentially reducing aid eligibility by up to 50% of the distribution amount.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Beneficiary Flexibility</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  529 plans offer flexibility to change beneficiaries within the family.
                </p>
                <ul className="space-y-2 text-sm">
                  <li>• Transfer to siblings if one child doesn't attend college</li>
                  <li>• Use for parents' continuing education</li>
                  <li>• Save for grandchildren's education</li>
                  <li>• Up to $10,000/year for K-12 tuition</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Investment Allocation</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  Age-based portfolios automatically become more conservative as college approaches.
                </p>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Ages 0-6:</span>
                    <span>80-90% Stocks</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ages 7-14:</span>
                    <span>60-70% Stocks</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ages 15-18:</span>
                    <span>30-40% Stocks</span>
                  </div>
                  <div className="flex justify-between">
                    <span>College Years:</span>
                    <span>10-20% Stocks</span>
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