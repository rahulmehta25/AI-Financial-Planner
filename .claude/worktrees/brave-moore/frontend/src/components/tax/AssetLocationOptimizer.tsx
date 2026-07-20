import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { 
  PieChart as PieChartIcon,
  TrendingUp, 
  Shield,
  Target,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  DollarSign,
  Percent,
  Calculator,
  ArrowRight,
  BarChart3,
  Zap
} from 'lucide-react';

// Types for asset location optimization
interface AssetClass {
  id: string;
  name: string;
  category: 'stocks' | 'bonds' | 'alternatives' | 'cash';
  taxEfficiency: 'high' | 'medium' | 'low';
  expectedReturn: number;
  volatility: number;
  dividendYield?: number;
  turnover?: number;
  taxDrag: number; // Annual tax drag percentage
}

interface Account {
  id: string;
  name: string;
  type: 'taxable' | 'traditional_401k' | 'roth_401k' | 'traditional_ira' | 'roth_ira' | 'hsa';
  balance: number;
  taxTreatment: 'taxable' | 'tax_deferred' | 'tax_free';
  contributionsRemaining?: number;
  canContribute: boolean;
}

interface AssetAllocation {
  assetClassId: string;
  targetPercent: number;
  currentAmount: number;
  targetAmount: number;
}

interface AccountAllocation {
  accountId: string;
  allocations: AssetAllocation[];
}

interface OptimizationRecommendation {
  id: string;
  type: 'move' | 'rebalance' | 'new_contribution';
  priority: 'high' | 'medium' | 'low';
  assetClass: string;
  fromAccount?: string;
  toAccount: string;
  amount: number;
  taxSavings: number;
  reasoning: string;
  implementation: {
    steps: string[];
    considerations: string[];
  };
}

interface OptimizationResults {
  currentTaxDrag: number;
  optimizedTaxDrag: number;
  annualTaxSavings: number;
  lifetimeTaxSavings: number;
  recommendations: OptimizationRecommendation[];
  accountAllocations: AccountAllocation[];
}

export const AssetLocationOptimizer: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [assetClasses, setAssetClasses] = useState<AssetClass[]>([]);
  const [currentAllocations, setCurrentAllocations] = useState<AccountAllocation[]>([]);
  const [optimizationResults, setOptimizationResults] = useState<OptimizationResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedView, setSelectedView] = useState<'current' | 'recommended'>('current');

  useEffect(() => {
    initializeData();
  }, []);

  const initializeData = async () => {
    try {
      setLoading(true);
      
      // Mock asset classes with tax efficiency data
      const mockAssetClasses: AssetClass[] = [
        {
          id: 'us_stocks',
          name: 'US Total Stock Market',
          category: 'stocks',
          taxEfficiency: 'high',
          expectedReturn: 0.10,
          volatility: 0.15,
          dividendYield: 0.02,
          turnover: 0.05,
          taxDrag: 0.15 // 0.15% annual tax drag
        },
        {
          id: 'international_stocks',
          name: 'International Developed Markets',
          category: 'stocks',
          taxEfficiency: 'medium',
          expectedReturn: 0.09,
          volatility: 0.16,
          dividendYield: 0.03,
          turnover: 0.08,
          taxDrag: 0.45
        },
        {
          id: 'emerging_markets',
          name: 'Emerging Markets',
          category: 'stocks',
          taxEfficiency: 'low',
          expectedReturn: 0.11,
          volatility: 0.22,
          dividendYield: 0.02,
          turnover: 0.15,
          taxDrag: 0.65
        },
        {
          id: 'corporate_bonds',
          name: 'Corporate Bonds',
          category: 'bonds',
          taxEfficiency: 'low',
          expectedReturn: 0.05,
          volatility: 0.04,
          dividendYield: 0.04,
          turnover: 0.20,
          taxDrag: 1.2
        },
        {
          id: 'treasury_bonds',
          name: 'Treasury Bonds',
          category: 'bonds',
          taxEfficiency: 'medium',
          expectedReturn: 0.04,
          volatility: 0.03,
          dividendYield: 0.03,
          turnover: 0.10,
          taxDrag: 0.8
        },
        {
          id: 'municipal_bonds',
          name: 'Municipal Bonds',
          category: 'bonds',
          taxEfficiency: 'high',
          expectedReturn: 0.035,
          volatility: 0.035,
          dividendYield: 0.03,
          turnover: 0.05,
          taxDrag: 0.05
        },
        {
          id: 'reits',
          name: 'Real Estate Investment Trusts',
          category: 'alternatives',
          taxEfficiency: 'low',
          expectedReturn: 0.08,
          volatility: 0.18,
          dividendYield: 0.04,
          turnover: 0.25,
          taxDrag: 1.8
        },
        {
          id: 'commodities',
          name: 'Commodities',
          category: 'alternatives',
          taxEfficiency: 'low',
          expectedReturn: 0.06,
          volatility: 0.20,
          turnover: 0.30,
          taxDrag: 2.1
        }
      ];

      // Mock accounts
      const mockAccounts: Account[] = [
        {
          id: 'taxable',
          name: 'Taxable Brokerage',
          type: 'taxable',
          balance: 250000,
          taxTreatment: 'taxable',
          canContribute: true
        },
        {
          id: 'traditional_401k',
          name: 'Traditional 401(k)',
          type: 'traditional_401k',
          balance: 180000,
          taxTreatment: 'tax_deferred',
          contributionsRemaining: 23000,
          canContribute: true
        },
        {
          id: 'roth_401k',
          name: 'Roth 401(k)',
          type: 'roth_401k',
          balance: 45000,
          taxTreatment: 'tax_free',
          contributionsRemaining: 23000,
          canContribute: true
        },
        {
          id: 'traditional_ira',
          name: 'Traditional IRA',
          type: 'traditional_ira',
          balance: 85000,
          taxTreatment: 'tax_deferred',
          contributionsRemaining: 7000,
          canContribute: true
        },
        {
          id: 'roth_ira',
          name: 'Roth IRA',
          type: 'roth_ira',
          balance: 65000,
          taxTreatment: 'tax_free',
          contributionsRemaining: 7000,
          canContribute: true
        },
        {
          id: 'hsa',
          name: 'Health Savings Account',
          type: 'hsa',
          balance: 25000,
          taxTreatment: 'tax_free',
          contributionsRemaining: 4300,
          canContribute: true
        }
      ];

      // Mock current allocations (suboptimal)
      const mockCurrentAllocations: AccountAllocation[] = [
        {
          accountId: 'taxable',
          allocations: [
            { assetClassId: 'us_stocks', targetPercent: 40, currentAmount: 100000, targetAmount: 100000 },
            { assetClassId: 'corporate_bonds', targetPercent: 40, currentAmount: 100000, targetAmount: 100000 },
            { assetClassId: 'reits', targetPercent: 20, currentAmount: 50000, targetAmount: 50000 }
          ]
        },
        {
          accountId: 'traditional_401k',
          allocations: [
            { assetClassId: 'us_stocks', targetPercent: 60, currentAmount: 108000, targetAmount: 108000 },
            { assetClassId: 'international_stocks', targetPercent: 40, currentAmount: 72000, targetAmount: 72000 }
          ]
        },
        {
          accountId: 'roth_401k',
          allocations: [
            { assetClassId: 'us_stocks', targetPercent: 100, currentAmount: 45000, targetAmount: 45000 }
          ]
        },
        {
          accountId: 'traditional_ira',
          allocations: [
            { assetClassId: 'international_stocks', targetPercent: 50, currentAmount: 42500, targetAmount: 42500 },
            { assetClassId: 'emerging_markets', targetPercent: 50, currentAmount: 42500, targetAmount: 42500 }
          ]
        },
        {
          accountId: 'roth_ira',
          allocations: [
            { assetClassId: 'emerging_markets', targetPercent: 60, currentAmount: 39000, targetAmount: 39000 },
            { assetClassId: 'reits', targetPercent: 40, currentAmount: 26000, targetAmount: 26000 }
          ]
        },
        {
          accountId: 'hsa',
          allocations: [
            { assetClassId: 'us_stocks', targetPercent: 100, currentAmount: 25000, targetAmount: 25000 }
          ]
        }
      ];

      setAssetClasses(mockAssetClasses);
      setAccounts(mockAccounts);
      setCurrentAllocations(mockCurrentAllocations);
      
      // Calculate optimization
      const optimization = calculateOptimization(mockAccounts, mockAssetClasses, mockCurrentAllocations);
      setOptimizationResults(optimization);
      
    } catch (error) {
      console.error('Failed to initialize asset location data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateOptimization = (
    accounts: Account[], 
    assetClasses: AssetClass[], 
    currentAllocations: AccountAllocation[]
  ): OptimizationResults => {
    // Calculate current tax drag
    let currentTaxDrag = 0;
    let totalAssets = 0;

    currentAllocations.forEach(accountAlloc => {
      const account = accounts.find(a => a.id === accountAlloc.accountId);
      if (!account) return;

      accountAlloc.allocations.forEach(alloc => {
        const assetClass = assetClasses.find(ac => ac.id === alloc.assetClassId);
        if (!assetClass) return;

        totalAssets += alloc.currentAmount;
        
        // Only taxable accounts contribute to tax drag
        if (account.taxTreatment === 'taxable') {
          currentTaxDrag += (alloc.currentAmount * assetClass.taxDrag / 100);
        }
      });
    });

    // Generate optimization recommendations
    const recommendations: OptimizationRecommendation[] = [
      {
        id: 'reits-to-tax-deferred',
        type: 'move',
        priority: 'high',
        assetClass: 'REITs',
        fromAccount: 'Taxable Brokerage',
        toAccount: 'Traditional 401(k)',
        amount: 50000,
        taxSavings: 900,
        reasoning: 'REITs have high tax drag (1.8%) in taxable accounts due to dividend distributions taxed as ordinary income.',
        implementation: {
          steps: [
            'Sell REITs in taxable account',
            'Purchase equivalent REITs in Traditional 401(k)',
            'Use proceeds to buy tax-efficient assets in taxable account'
          ],
          considerations: [
            'May trigger capital gains in taxable account',
            'Check 401(k) investment options for REIT funds'
          ]
        }
      },
      {
        id: 'bonds-to-tax-deferred',
        type: 'move',
        priority: 'high',
        assetClass: 'Corporate Bonds',
        fromAccount: 'Taxable Brokerage',
        toAccount: 'Traditional IRA',
        amount: 75000,
        taxSavings: 675,
        reasoning: 'Bond interest is taxed as ordinary income, making them inefficient in taxable accounts.',
        implementation: {
          steps: [
            'Gradually sell corporate bonds in taxable account',
            'Purchase bonds in Traditional IRA through contributions and conversions',
            'Replace with tax-efficient stock index funds in taxable account'
          ],
          considerations: [
            'Spread over multiple years due to IRA contribution limits',
            'Consider tax-loss harvesting opportunities'
          ]
        }
      },
      {
        id: 'emerging-markets-optimization',
        type: 'move',
        priority: 'medium',
        assetClass: 'Emerging Markets',
        fromAccount: 'Traditional IRA',
        toAccount: 'Roth IRA',
        amount: 42500,
        taxSavings: 255,
        reasoning: 'High-growth potential assets like emerging markets are more tax-efficient in Roth accounts.',
        implementation: {
          steps: [
            'Perform Roth conversion of emerging market holdings',
            'Pay conversion taxes from taxable account',
            'Maintain overall asset allocation'
          ],
          considerations: [
            'Evaluate current tax bracket vs. future expectations',
            'Consider multi-year conversion strategy'
          ]
        }
      }
    ];

    // Calculate optimized tax drag
    const optimizedTaxDrag = currentTaxDrag * 0.35; // Assuming 65% reduction
    const annualTaxSavings = currentTaxDrag - optimizedTaxDrag;
    const lifetimeTaxSavings = annualTaxSavings * 25; // 25 years to retirement

    // Generate optimized allocations
    const optimizedAccountAllocations: AccountAllocation[] = generateOptimizedAllocations(
      accounts, 
      assetClasses, 
      currentAllocations
    );

    return {
      currentTaxDrag,
      optimizedTaxDrag,
      annualTaxSavings,
      lifetimeTaxSavings,
      recommendations,
      accountAllocations: optimizedAccountAllocations
    };
  };

  const generateOptimizedAllocations = (
    accounts: Account[],
    assetClasses: AssetClass[],
    currentAllocations: AccountAllocation[]
  ): AccountAllocation[] => {
    // Optimize allocations based on tax efficiency principles
    return currentAllocations.map(accountAlloc => {
      const account = accounts.find(a => a.id === accountAlloc.accountId);
      if (!account) return accountAlloc;

      let optimizedAllocations = [...accountAlloc.allocations];

      // Tax-specific optimization rules
      if (account.taxTreatment === 'taxable') {
        // Favor tax-efficient assets in taxable accounts
        optimizedAllocations = optimizedAllocations.map(alloc => {
          const assetClass = assetClasses.find(ac => ac.id === alloc.assetClassId);
          if (assetClass?.taxEfficiency === 'low') {
            // Reduce inefficient assets in taxable accounts
            return { ...alloc, targetAmount: alloc.currentAmount * 0.2 };
          }
          return alloc;
        });
      } else if (account.taxTreatment === 'tax_deferred') {
        // Favor tax-inefficient assets in tax-deferred accounts
        optimizedAllocations = optimizedAllocations.map(alloc => {
          const assetClass = assetClasses.find(ac => ac.id === alloc.assetClassId);
          if (assetClass?.taxEfficiency === 'low') {
            // Increase inefficient assets in tax-deferred accounts
            return { ...alloc, targetAmount: alloc.currentAmount * 1.5 };
          }
          return alloc;
        });
      }

      return { ...accountAlloc, allocations: optimizedAllocations };
    });
  };

  const getTaxEfficiencyColor = (efficiency: string) => {
    switch (efficiency) {
      case 'high': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAccountTypeColor = (taxTreatment: string) => {
    switch (taxTreatment) {
      case 'taxable': return '#ef4444';
      case 'tax_deferred': return '#f59e0b';
      case 'tax_free': return '#10b981';
      default: return '#6b7280';
    }
  };

  const prepareAllocationChartData = (allocations: AccountAllocation[]) => {
    const data: any[] = [];
    
    allocations.forEach(accountAlloc => {
      const account = accounts.find(a => a.id === accountAlloc.accountId);
      if (!account) return;

      accountAlloc.allocations.forEach(alloc => {
        const assetClass = assetClasses.find(ac => ac.id === alloc.assetClassId);
        if (!assetClass) return;

        data.push({
          name: `${assetClass.name} (${account.name})`,
          value: alloc.currentAmount,
          account: account.name,
          assetClass: assetClass.name,
          taxTreatment: account.taxTreatment,
          color: getAccountTypeColor(account.taxTreatment)
        });
      });
    });

    return data;
  };

  if (loading) {
    return (
      <Card id="asset-location-loading" className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-6 w-6" />
            Asset Location Optimizer
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

  const chartData = prepareAllocationChartData(currentAllocations);

  return (
    <div id="asset-location-optimizer" className="w-full space-y-6">
      {/* Summary Cards */}
      {optimizationResults && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card id="current-tax-drag">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Current Tax Drag</p>
                  <p className="text-2xl font-bold text-red-600">
                    ${optimizationResults.currentTaxDrag.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">per year</p>
                </div>
                <TrendingUp className="h-8 w-8 text-red-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="potential-savings">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Annual Savings</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${optimizationResults.annualTaxSavings.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">potential</p>
                </div>
                <DollarSign className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="lifetime-impact">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Lifetime Savings</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${(optimizationResults.lifetimeTaxSavings / 1000).toFixed(0)}K
                  </p>
                  <p className="text-xs text-gray-500">projected</p>
                </div>
                <Target className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="efficiency-improvement">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Tax Efficiency</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {((1 - optimizationResults.optimizedTaxDrag / optimizationResults.currentTaxDrag) * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-gray-500">improvement</p>
                </div>
                <Zap className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Card id="asset-location-main">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-6 w-6" />
            Asset Location Optimizer
          </CardTitle>
          <CardDescription>
            Optimize asset placement across account types to minimize tax drag and maximize after-tax returns.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
              <TabsTrigger value="allocations">Allocations</TabsTrigger>
              <TabsTrigger value="analysis">Analysis</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {/* Tax Efficiency by Asset Class */}
              <Card id="asset-efficiency">
                <CardHeader>
                  <CardTitle>Asset Class Tax Efficiency</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {assetClasses.map(assetClass => (
                      <div key={assetClass.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <h4 className="font-medium">{assetClass.name}</h4>
                            <Badge className={getTaxEfficiencyColor(assetClass.taxEfficiency)}>
                              {assetClass.taxEfficiency} efficiency
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            {assetClass.taxDrag}% annual tax drag
                            {assetClass.dividendYield && ` • ${(assetClass.dividendYield * 100).toFixed(1)}% dividend yield`}
                            {assetClass.turnover && ` • ${(assetClass.turnover * 100).toFixed(0)}% turnover`}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">
                            {(assetClass.expectedReturn * 100).toFixed(1)}% return
                          </p>
                          <p className="text-xs text-gray-500">
                            {(assetClass.volatility * 100).toFixed(0)}% volatility
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Current vs Optimized Comparison */}
              {optimizationResults && (
                <Card id="optimization-comparison">
                  <CardHeader>
                    <CardTitle>Optimization Impact</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                          <h4 className="font-semibold text-center">Current Portfolio</h4>
                          <div className="text-center space-y-2">
                            <p className="text-3xl font-bold text-red-600">
                              ${optimizationResults.currentTaxDrag.toLocaleString()}
                            </p>
                            <p className="text-sm text-gray-600">Annual Tax Drag</p>
                          </div>
                        </div>
                        <div className="space-y-4">
                          <h4 className="font-semibold text-center">Optimized Portfolio</h4>
                          <div className="text-center space-y-2">
                            <p className="text-3xl font-bold text-green-600">
                              ${optimizationResults.optimizedTaxDrag.toLocaleString()}
                            </p>
                            <p className="text-sm text-gray-600">Annual Tax Drag</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-center py-4 border-t">
                        <div className="flex items-center justify-center gap-2 text-2xl font-bold text-green-600">
                          <ArrowRight className="h-6 w-6" />
                          ${optimizationResults.annualTaxSavings.toLocaleString()} saved annually
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-4">
              {optimizationResults && (
                <div className="space-y-4">
                  {optimizationResults.recommendations.map((rec, index) => (
                    <Card key={rec.id} id={`recommendation-${rec.id}`} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <CardTitle className="text-lg">
                              Move {rec.assetClass} to {rec.toAccount}
                            </CardTitle>
                            <CardDescription className="mt-1">
                              {rec.reasoning}
                            </CardDescription>
                          </div>
                          <Badge className={getPriorityColor(rec.priority)}>
                            {rec.priority} priority
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="space-y-2">
                            <h4 className="font-semibold text-sm">Financial Impact</h4>
                            <div className="space-y-1 text-sm">
                              <div className="flex justify-between">
                                <span>Amount:</span>
                                <span className="font-medium">${rec.amount.toLocaleString()}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Annual Tax Savings:</span>
                                <span className="font-medium text-green-600">
                                  ${rec.taxSavings.toLocaleString()}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span>25-Year Savings:</span>
                                <span className="font-medium text-green-600">
                                  ${(rec.taxSavings * 25).toLocaleString()}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <h4 className="font-semibold text-sm">Implementation Steps</h4>
                            <ol className="text-sm space-y-1 list-decimal list-inside">
                              {rec.implementation.steps.map((step, stepIndex) => (
                                <li key={stepIndex}>{step}</li>
                              ))}
                            </ol>
                          </div>

                          <div className="space-y-2">
                            <h4 className="font-semibold text-sm">Considerations</h4>
                            <ul className="text-sm space-y-1 list-disc list-inside">
                              {rec.implementation.considerations.map((consideration, considIndex) => (
                                <li key={considIndex}>{consideration}</li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        <div className="flex gap-2 pt-2 border-t">
                          <Button className="flex items-center gap-2">
                            <CheckCircle className="h-4 w-4" />
                            Implement Recommendation
                          </Button>
                          <Button variant="outline">
                            Schedule for Review
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="allocations" className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Asset Allocation by Account</h3>
                <Select value={selectedView} onValueChange={(value: any) => setSelectedView(value)}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="current">Current Allocation</SelectItem>
                    <SelectItem value="recommended">Recommended Allocation</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Allocation Visualization */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card id="allocation-pie-chart">
                  <CardHeader>
                    <CardTitle>Portfolio Allocation</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, value }) => `${name}: $${(value/1000).toFixed(0)}k`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {chartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value: any) => [`$${parseFloat(value).toLocaleString()}`, 'Value']} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                <Card id="account-breakdown">
                  <CardHeader>
                    <CardTitle>Account Breakdown</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {accounts.map(account => {
                        const accountAlloc = currentAllocations.find(a => a.accountId === account.id);
                        if (!accountAlloc) return null;

                        const totalValue = accountAlloc.allocations.reduce((sum, alloc) => sum + alloc.currentAmount, 0);
                        const taxColor = getAccountTypeColor(account.taxTreatment);

                        return (
                          <div key={account.id} className="p-4 border rounded-lg">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <div 
                                  className="w-4 h-4 rounded"
                                  style={{ backgroundColor: taxColor }}
                                />
                                <h4 className="font-semibold">{account.name}</h4>
                                <Badge variant="outline">
                                  {account.taxTreatment.replace('_', ' ')}
                                </Badge>
                              </div>
                              <span className="font-semibold">
                                ${totalValue.toLocaleString()}
                              </span>
                            </div>
                            <div className="space-y-2">
                              {accountAlloc.allocations.map(alloc => {
                                const assetClass = assetClasses.find(ac => ac.id === alloc.assetClassId);
                                const percentage = (alloc.currentAmount / totalValue) * 100;
                                
                                return (
                                  <div key={alloc.assetClassId} className="flex justify-between text-sm">
                                    <span>{assetClass?.name}</span>
                                    <div className="text-right">
                                      <span className="font-medium">{percentage.toFixed(1)}%</span>
                                      <span className="text-gray-500 ml-2">
                                        ${alloc.currentAmount.toLocaleString()}
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="analysis" className="space-y-6">
              <Card id="tax-drag-analysis">
                <CardHeader>
                  <CardTitle>Tax Drag Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Total Portfolio Value</p>
                        <p className="text-2xl font-bold">
                          ${accounts.reduce((sum, acc) => sum + acc.balance, 0).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Taxable Assets</p>
                        <p className="text-2xl font-bold">
                          ${accounts.find(a => a.type === 'taxable')?.balance.toLocaleString()}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-600">Tax-Sheltered Assets</p>
                        <p className="text-2xl font-bold">
                          ${accounts.filter(a => a.type !== 'taxable').reduce((sum, acc) => sum + acc.balance, 0).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="space-y-2">
                          <p className="font-medium">Asset Location Principles</p>
                          <ul className="list-disc list-inside space-y-1 text-sm">
                            <li><strong>Taxable accounts:</strong> Tax-efficient assets (index funds, muni bonds)</li>
                            <li><strong>Tax-deferred accounts:</strong> Tax-inefficient assets (bonds, REITs, active funds)</li>
                            <li><strong>Tax-free accounts:</strong> High-growth potential assets (small cap, emerging markets)</li>
                            <li><strong>HSA accounts:</strong> Conservative investments until age 65, then aggressive growth</li>
                          </ul>
                        </div>
                      </AlertDescription>
                    </Alert>
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