import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { 
  Calculator,
  TrendingDown,
  Target,
  BarChart3,
  Calendar,
  CheckSquare,
  DollarSign,
  PieChart,
  AlertTriangle,
  TrendingUp,
  FileText,
  Lightbulb,
  Clock,
  Star,
  Download,
  Share
} from 'lucide-react';

// Import the tax optimization components
import { TaxHarvestingOpportunities } from '../components/tax/TaxHarvestingOpportunities';
import { RothConversionCalculator } from '../components/tax/RothConversionCalculator';
import { AssetLocationOptimizer } from '../components/tax/AssetLocationOptimizer';
import { TaxBracketVisualizer } from '../components/tax/TaxBracketVisualizer';

// Types for tax optimization dashboard
interface TaxOptimizationSummary {
  totalPotentialSavings: number;
  ytdTaxLossHarvesting: number;
  taxDragReduction: number;
  completedActions: number;
  pendingActions: number;
  taxEfficiencyScore: number;
}

interface TaxPlanningChecklistItem {
  id: string;
  title: string;
  description: string;
  deadline: string;
  priority: 'high' | 'medium' | 'low';
  category: 'contributions' | 'harvesting' | 'planning' | 'optimization';
  completed: boolean;
  estimatedSavings?: number;
}

interface CapitalGainsLoss {
  id: string;
  security: string;
  quantity: number;
  purchaseDate: string;
  purchasePrice: number;
  currentPrice: number;
  unrealizedGainLoss: number;
  holdingPeriod: 'short' | 'long';
  account: string;
}

export const TaxOptimization: React.FC = () => {
  const [summary, setSummary] = useState<TaxOptimizationSummary | null>(null);
  const [checklist, setChecklist] = useState<TaxPlanningChecklistItem[]>([]);
  const [capitalGainsLosses, setCapitalGainsLosses] = useState<CapitalGainsLoss[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    initializeTaxOptimizationData();
  }, []);

  const initializeTaxOptimizationData = async () => {
    try {
      setLoading(true);
      
      // Mock tax optimization summary
      const mockSummary: TaxOptimizationSummary = {
        totalPotentialSavings: 12850,
        ytdTaxLossHarvesting: 8450,
        taxDragReduction: 2100,
        completedActions: 7,
        pendingActions: 5,
        taxEfficiencyScore: 82
      };

      // Mock year-end tax planning checklist
      const mockChecklist: TaxPlanningChecklistItem[] = [
        {
          id: '1',
          title: 'Maximize 401(k) Contributions',
          description: 'Ensure you\'re contributing the maximum $23,000 for 2024 ($30,500 if 50+)',
          deadline: '2024-12-31',
          priority: 'high',
          category: 'contributions',
          completed: false,
          estimatedSavings: 5520
        },
        {
          id: '2',
          title: 'Review Tax Loss Harvesting Opportunities',
          description: 'Harvest losses to offset capital gains and up to $3,000 of ordinary income',
          deadline: '2024-12-31',
          priority: 'high',
          category: 'harvesting',
          completed: true,
          estimatedSavings: 0
        },
        {
          id: '3',
          title: 'Consider Roth IRA Conversion',
          description: 'Evaluate converting traditional IRA funds while in lower tax brackets',
          deadline: '2024-12-31',
          priority: 'medium',
          category: 'optimization',
          completed: false,
          estimatedSavings: 1800
        },
        {
          id: '4',
          title: 'Make Charitable Contributions',
          description: 'Consider bunching charitable donations or using donor-advised funds',
          deadline: '2024-12-31',
          priority: 'medium',
          category: 'planning',
          completed: false,
          estimatedSavings: 960
        },
        {
          id: '5',
          title: 'Maximize HSA Contributions',
          description: 'Contribute the maximum $4,300 individual ($8,550 family) for triple tax benefits',
          deadline: '2024-12-31',
          priority: 'high',
          category: 'contributions',
          completed: true,
          estimatedSavings: 0
        },
        {
          id: '6',
          title: 'Review Asset Location Strategy',
          description: 'Optimize asset placement across taxable and tax-advantaged accounts',
          deadline: '2025-01-31',
          priority: 'medium',
          category: 'optimization',
          completed: false,
          estimatedSavings: 2100
        },
        {
          id: '7',
          title: 'Plan Q1 Estimated Tax Payments',
          description: 'Calculate and schedule quarterly estimated tax payments for next year',
          deadline: '2025-01-15',
          priority: 'medium',
          category: 'planning',
          completed: false,
          estimatedSavings: 0
        },
        {
          id: '8',
          title: 'Consider Tax-Efficient Fund Swaps',
          description: 'Switch to more tax-efficient index funds in taxable accounts',
          deadline: '2024-12-31',
          priority: 'low',
          category: 'optimization',
          completed: false,
          estimatedSavings: 450
        }
      ];

      // Mock capital gains/losses data
      const mockCapitalGainsLosses: CapitalGainsLoss[] = [
        {
          id: '1',
          security: 'VTI',
          quantity: 500,
          purchaseDate: '2023-03-15',
          purchasePrice: 220.50,
          currentPrice: 195.25,
          unrealizedGainLoss: -12625,
          holdingPeriod: 'long',
          account: 'Taxable Brokerage'
        },
        {
          id: '2',
          security: 'AAPL',
          quantity: 100,
          purchaseDate: '2024-08-01',
          purchasePrice: 225.00,
          currentPrice: 245.30,
          unrealizedGainLoss: 2030,
          holdingPeriod: 'short',
          account: 'Taxable Brokerage'
        },
        {
          id: '3',
          security: 'VXUS',
          quantity: 300,
          purchaseDate: '2023-06-10',
          purchasePrice: 58.75,
          currentPrice: 52.10,
          unrealizedGainLoss: -1995,
          holdingPeriod: 'long',
          account: 'Taxable Brokerage'
        },
        {
          id: '4',
          security: 'TSLA',
          quantity: 50,
          purchaseDate: '2024-01-20',
          purchasePrice: 185.00,
          currentPrice: 235.60,
          unrealizedGainLoss: 2530,
          holdingPeriod: 'long',
          account: 'Taxable Brokerage'
        }
      ];

      setSummary(mockSummary);
      setChecklist(mockChecklist);
      setCapitalGainsLosses(mockCapitalGainsLosses);

    } catch (error) {
      console.error('Failed to initialize tax optimization data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleChecklistItem = (id: string) => {
    setChecklist(prev => prev.map(item => 
      item.id === id ? { ...item, completed: !item.completed } : item
    ));
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'contributions': return <DollarSign className="h-4 w-4" />;
      case 'harvesting': return <TrendingDown className="h-4 w-4" />;
      case 'planning': return <Calendar className="h-4 w-4" />;
      case 'optimization': return <Target className="h-4 w-4" />;
      default: return <CheckSquare className="h-4 w-4" />;
    }
  };

  const getEfficiencyScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const totalUnrealizedGains = capitalGainsLosses
    .filter(item => item.unrealizedGainLoss > 0)
    .reduce((sum, item) => sum + item.unrealizedGainLoss, 0);

  const totalUnrealizedLosses = capitalGainsLosses
    .filter(item => item.unrealizedGainLoss < 0)
    .reduce((sum, item) => sum + Math.abs(item.unrealizedGainLoss), 0);

  if (loading) {
    return (
      <div id="tax-optimization-loading" className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded animate-pulse"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <div id="tax-optimization-dashboard" className="container mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div id="dashboard-header" className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tax Optimization Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Maximize your after-tax returns with comprehensive tax strategies
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Report
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Share className="h-4 w-4" />
            Share
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card id="total-potential-savings">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Potential Annual Savings</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${summary.totalPotentialSavings.toLocaleString()}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="ytd-harvesting">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">YTD Tax Loss Harvesting</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${summary.ytdTaxLossHarvesting.toLocaleString()}
                  </p>
                </div>
                <TrendingDown className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="tax-drag-reduction">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Tax Drag Reduction</p>
                  <p className="text-2xl font-bold text-purple-600">
                    ${summary.taxDragReduction.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">per year</p>
                </div>
                <Target className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="tax-efficiency-score">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Tax Efficiency Score</p>
                  <p className={`text-2xl font-bold ${getEfficiencyScoreColor(summary.taxEfficiencyScore)}`}>
                    {summary.taxEfficiencyScore}/100
                  </p>
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Star className="h-3 w-3 fill-current" />
                    <span>Excellent</span>
                  </div>
                </div>
                <BarChart3 className={`h-8 w-8 ${getEfficiencyScoreColor(summary.taxEfficiencyScore)}`} />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="harvesting">Tax Harvesting</TabsTrigger>
          <TabsTrigger value="roth">Roth Conversion</TabsTrigger>
          <TabsTrigger value="asset-location">Asset Location</TabsTrigger>
          <TabsTrigger value="brackets">Tax Brackets</TabsTrigger>
          <TabsTrigger value="planning">Year-End Planning</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tax Planning Checklist */}
            <Card id="tax-planning-checklist">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckSquare className="h-5 w-5" />
                  Year-End Tax Planning Checklist
                </CardTitle>
                <CardDescription>
                  Complete these actions to maximize your tax savings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {checklist.slice(0, 6).map(item => (
                    <div 
                      key={item.id} 
                      id={`checklist-item-${item.id}`}
                      className={`flex items-start gap-3 p-3 border rounded-lg transition-colors ${
                        item.completed ? 'bg-green-50 border-green-200' : 'hover:bg-gray-50'
                      }`}
                    >
                      <button
                        onClick={() => toggleChecklistItem(item.id)}
                        className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center ${
                          item.completed 
                            ? 'bg-green-500 border-green-500 text-white' 
                            : 'border-gray-300 hover:border-green-400'
                        }`}
                      >
                        {item.completed && <CheckSquare className="h-3 w-3" />}
                      </button>
                      
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className={`font-medium ${item.completed ? 'line-through text-gray-500' : ''}`}>
                              {item.title}
                            </h4>
                            <p className="text-sm text-gray-600 mt-1">
                              {item.description}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge className={getPriorityColor(item.priority)} variant="outline">
                                {item.priority}
                              </Badge>
                              {getCategoryIcon(item.category)}
                              <span className="text-xs text-gray-500">
                                Due: {new Date(item.deadline).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          {item.estimatedSavings && item.estimatedSavings > 0 && (
                            <div className="text-right">
                              <p className="text-sm font-medium text-green-600">
                                ${item.estimatedSavings.toLocaleString()}
                              </p>
                              <p className="text-xs text-gray-500">savings</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 pt-4 border-t">
                  <div className="flex justify-between text-sm">
                    <span>Progress: {checklist.filter(item => item.completed).length} of {checklist.length} completed</span>
                    <span className="font-medium">
                      ${checklist.filter(item => !item.completed).reduce((sum, item) => sum + (item.estimatedSavings || 0), 0).toLocaleString()} remaining savings
                    </span>
                  </div>
                  <Progress 
                    value={(checklist.filter(item => item.completed).length / checklist.length) * 100}
                    className="mt-2"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Capital Gains/Losses Tracker */}
            <Card id="capital-gains-losses">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Capital Gains & Losses Tracker
                </CardTitle>
                <CardDescription>
                  Monitor unrealized gains and losses for tax planning
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <p className="text-2xl font-bold text-green-600">
                        ${totalUnrealizedGains.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">Unrealized Gains</p>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <p className="text-2xl font-bold text-red-600">
                        ${totalUnrealizedLosses.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">Unrealized Losses</p>
                    </div>
                  </div>

                  {/* Holdings List */}
                  <div className="space-y-2">
                    {capitalGainsLosses.map(holding => (
                      <div key={holding.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{holding.security}</span>
                            <Badge variant="outline" className="text-xs">
                              {holding.holdingPeriod}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600">
                            {holding.quantity} shares • {holding.account}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`font-medium ${
                            holding.unrealizedGainLoss >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {holding.unrealizedGainLoss >= 0 ? '+' : ''}${holding.unrealizedGainLoss.toLocaleString()}
                          </p>
                          <p className="text-xs text-gray-500">
                            ${holding.currentPrice.toFixed(2)}/share
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card id="quick-actions">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Button 
                  variant="outline" 
                  className="h-auto flex flex-col items-center gap-2 p-4"
                  onClick={() => setActiveTab('harvesting')}
                >
                  <TrendingDown className="h-6 w-6" />
                  <div className="text-center">
                    <p className="font-medium">Review Harvest Opportunities</p>
                    <p className="text-xs text-gray-500">3 opportunities available</p>
                  </div>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="h-auto flex flex-col items-center gap-2 p-4"
                  onClick={() => setActiveTab('roth')}
                >
                  <Calculator className="h-6 w-6" />
                  <div className="text-center">
                    <p className="font-medium">Calculate Roth Conversion</p>
                    <p className="text-xs text-gray-500">Optimize tax timing</p>
                  </div>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="h-auto flex flex-col items-center gap-2 p-4"
                  onClick={() => setActiveTab('asset-location')}
                >
                  <Target className="h-6 w-6" />
                  <div className="text-center">
                    <p className="font-medium">Optimize Asset Location</p>
                    <p className="text-xs text-gray-500">Save $2,100/year</p>
                  </div>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="h-auto flex flex-col items-center gap-2 p-4"
                  onClick={() => setActiveTab('brackets')}
                >
                  <BarChart3 className="h-6 w-6" />
                  <div className="text-center">
                    <p className="font-medium">Analyze Tax Brackets</p>
                    <p className="text-xs text-gray-500">Plan contributions</p>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="harvesting">
          <TaxHarvestingOpportunities />
        </TabsContent>

        <TabsContent value="roth">
          <RothConversionCalculator />
        </TabsContent>

        <TabsContent value="asset-location">
          <AssetLocationOptimizer />
        </TabsContent>

        <TabsContent value="brackets">
          <TaxBracketVisualizer />
        </TabsContent>

        <TabsContent value="planning" className="space-y-6">
          {/* Complete Checklist */}
          <Card id="complete-checklist">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Complete Year-End Tax Planning Checklist
              </CardTitle>
              <CardDescription>
                All tax optimization actions for the current year
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {checklist.map(item => (
                  <div 
                    key={item.id}
                    id={`complete-checklist-item-${item.id}`}
                    className={`flex items-start gap-3 p-4 border rounded-lg transition-colors ${
                      item.completed ? 'bg-green-50 border-green-200' : 'hover:bg-gray-50'
                    }`}
                  >
                    <button
                      onClick={() => toggleChecklistItem(item.id)}
                      className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center ${
                        item.completed 
                          ? 'bg-green-500 border-green-500 text-white' 
                          : 'border-gray-300 hover:border-green-400'
                      }`}
                    >
                      {item.completed && <CheckSquare className="h-3 w-3" />}
                    </button>
                    
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className={`font-medium ${item.completed ? 'line-through text-gray-500' : ''}`}>
                            {item.title}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1 max-w-2xl">
                            {item.description}
                          </p>
                          <div className="flex items-center gap-3 mt-3">
                            <Badge className={getPriorityColor(item.priority)} variant="outline">
                              {item.priority}
                            </Badge>
                            <div className="flex items-center gap-1 text-sm text-gray-600">
                              {getCategoryIcon(item.category)}
                              <span className="capitalize">{item.category}</span>
                            </div>
                            <div className="flex items-center gap-1 text-sm text-gray-600">
                              <Clock className="h-4 w-4" />
                              <span>Due: {new Date(item.deadline).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                        {item.estimatedSavings && item.estimatedSavings > 0 && (
                          <div className="text-right ml-4">
                            <p className="text-lg font-bold text-green-600">
                              ${item.estimatedSavings.toLocaleString()}
                            </p>
                            <p className="text-xs text-gray-500">potential savings</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900">Important Tax Deadlines</h4>
                    <ul className="mt-2 space-y-1 text-sm text-blue-800">
                      <li>• December 31: Last day for most tax-deductible contributions</li>
                      <li>• December 31: Tax loss harvesting deadline</li>
                      <li>• January 15: Q4 estimated tax payment due</li>
                      <li>• April 15: Tax return filing deadline (following year)</li>
                      <li>• April 15: IRA contribution deadline for prior tax year</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};