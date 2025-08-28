import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { Separator } from '../ui/separator';
import { 
  TrendingDown, 
  TrendingUp, 
  Calendar, 
  DollarSign, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Calculator,
  Target,
  Percent
} from 'lucide-react';

// Types for tax loss harvesting data
interface HarvestingOpportunity {
  id: string;
  security: {
    symbol: string;
    name: string;
    sector: string;
    assetClass: string;
  };
  position: {
    shares: number;
    avgCostBasis: number;
    currentPrice: number;
    marketValue: number;
    unrealizedLoss: number;
    unrealizedLossPercent: number;
  };
  taxBenefits: {
    federalTaxSavings: number;
    stateTaxSavings: number;
    totalTaxSavings: number;
    carryForwardAmount?: number;
  };
  washSaleRisk: {
    isWashSaleRisk: boolean;
    riskLevel: 'Low' | 'Medium' | 'High';
    riskFactors: string[];
    waitPeriod?: number; // days until can repurchase
  };
  replacementOptions: ReplacementOption[];
  harvestRecommendation: {
    action: 'harvest' | 'hold' | 'partial';
    priority: 'High' | 'Medium' | 'Low';
    reasoning: string;
    optimalTiming?: string;
  };
  accountType: string;
  holdingPeriod: number; // days held
}

interface ReplacementOption {
  symbol: string;
  name: string;
  correlation: number;
  expense_ratio: number;
  liquidity: 'High' | 'Medium' | 'Low';
  suitabilityScore: number;
}

interface HarvestingSummary {
  totalOpportunities: number;
  totalPotentialLoss: number;
  totalTaxSavings: number;
  washSaleRisks: number;
  recommendedActions: number;
  carryForwardAvailable: number;
  ytdHarvested: number;
}

export const TaxHarvestingOpportunities: React.FC = () => {
  const [opportunities, setOpportunities] = useState<HarvestingOpportunity[]>([]);
  const [summary, setSummary] = useState<HarvestingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFilters, setSelectedFilters] = useState({
    priority: 'all',
    riskLevel: 'all',
    accountType: 'all'
  });
  const [activeOpportunity, setActiveOpportunity] = useState<HarvestingOpportunity | null>(null);

  useEffect(() => {
    fetchHarvestingOpportunities();
  }, [selectedFilters]);

  const fetchHarvestingOpportunities = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration
      const mockOpportunities: HarvestingOpportunity[] = [
        {
          id: '1',
          security: {
            symbol: 'VTI',
            name: 'Vanguard Total Stock Market ETF',
            sector: 'Broad Market',
            assetClass: 'US Equities'
          },
          position: {
            shares: 500,
            avgCostBasis: 220.50,
            currentPrice: 195.25,
            marketValue: 97625,
            unrealizedLoss: -12625,
            unrealizedLossPercent: -11.4
          },
          taxBenefits: {
            federalTaxSavings: 2525,
            stateTaxSavings: 631,
            totalTaxSavings: 3156,
            carryForwardAmount: 0
          },
          washSaleRisk: {
            isWashSaleRisk: false,
            riskLevel: 'Low',
            riskFactors: []
          },
          replacementOptions: [
            {
              symbol: 'ITOT',
              name: 'iShares Core S&P Total U.S. Stock Market ETF',
              correlation: 0.99,
              expense_ratio: 0.03,
              liquidity: 'High',
              suitabilityScore: 95
            },
            {
              symbol: 'SWTSX',
              name: 'Schwab Total Stock Market Index Fund',
              correlation: 0.98,
              expense_ratio: 0.03,
              liquidity: 'High',
              suitabilityScore: 92
            }
          ],
          harvestRecommendation: {
            action: 'harvest',
            priority: 'High',
            reasoning: 'Significant unrealized loss with high tax savings potential and low wash sale risk.'
          },
          accountType: 'Taxable',
          holdingPeriod: 180
        },
        {
          id: '2',
          security: {
            symbol: 'VXUS',
            name: 'Vanguard Total International Stock ETF',
            sector: 'International',
            assetClass: 'International Equities'
          },
          position: {
            shares: 300,
            avgCostBasis: 58.75,
            currentPrice: 52.10,
            marketValue: 15630,
            unrealizedLoss: -1995,
            unrealizedLossPercent: -11.3
          },
          taxBenefits: {
            federalTaxSavings: 399,
            stateTaxSavings: 100,
            totalTaxSavings: 499
          },
          washSaleRisk: {
            isWashSaleRisk: true,
            riskLevel: 'Medium',
            riskFactors: ['Similar ETF purchased in IRA 15 days ago'],
            waitPeriod: 16
          },
          replacementOptions: [
            {
              symbol: 'FTIHX',
              name: 'Fidelity Total International Index Fund',
              correlation: 0.97,
              expense_ratio: 0.06,
              liquidity: 'High',
              suitabilityScore: 88
            }
          ],
          harvestRecommendation: {
            action: 'hold',
            priority: 'Medium',
            reasoning: 'Wait for wash sale period to expire before harvesting.',
            optimalTiming: '16 days'
          },
          accountType: 'Taxable',
          holdingPeriod: 45
        }
      ];

      const mockSummary: HarvestingSummary = {
        totalOpportunities: mockOpportunities.length,
        totalPotentialLoss: mockOpportunities.reduce((sum, opp) => sum + Math.abs(opp.position.unrealizedLoss), 0),
        totalTaxSavings: mockOpportunities.reduce((sum, opp) => sum + opp.taxBenefits.totalTaxSavings, 0),
        washSaleRisks: mockOpportunities.filter(opp => opp.washSaleRisk.isWashSaleRisk).length,
        recommendedActions: mockOpportunities.filter(opp => opp.harvestRecommendation.action === 'harvest').length,
        carryForwardAvailable: 0,
        ytdHarvested: 8450
      };

      setOpportunities(mockOpportunities);
      setSummary(mockSummary);
    } catch (error) {
      console.error('Failed to fetch harvesting opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleHarvestAction = async (opportunityId: string, action: string) => {
    // Implementation for executing harvest action
    console.log(`Executing ${action} for opportunity ${opportunityId}`);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High': return 'bg-red-100 text-red-800 border-red-200';
      case 'Medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'High': return 'text-red-600';
      case 'Medium': return 'text-yellow-600';
      case 'Low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const filteredOpportunities = opportunities.filter(opp => {
    if (selectedFilters.priority !== 'all' && opp.harvestRecommendation.priority !== selectedFilters.priority) return false;
    if (selectedFilters.riskLevel !== 'all' && opp.washSaleRisk.riskLevel !== selectedFilters.riskLevel) return false;
    if (selectedFilters.accountType !== 'all' && opp.accountType !== selectedFilters.accountType) return false;
    return true;
  });

  if (loading) {
    return (
      <Card id="tax-harvesting-loading" className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingDown className="h-6 w-6" />
            Tax Loss Harvesting Opportunities
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
    <div id="tax-harvesting-opportunities" className="w-full space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card id="summary-opportunities">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Opportunities</p>
                  <p className="text-2xl font-bold">{summary.totalOpportunities}</p>
                </div>
                <Target className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="summary-potential-savings">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Potential Tax Savings</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${summary.totalTaxSavings.toLocaleString()}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="summary-wash-sale-risks">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Wash Sale Risks</p>
                  <p className="text-2xl font-bold text-amber-600">{summary.washSaleRisks}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-amber-600" />
              </div>
            </CardContent>
          </Card>

          <Card id="summary-ytd-harvested">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">YTD Harvested</p>
                  <p className="text-2xl font-bold text-blue-600">
                    ${summary.ytdHarvested.toLocaleString()}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Card id="harvesting-main-content">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingDown className="h-6 w-6" />
            Tax Loss Harvesting Opportunities
          </CardTitle>
          <CardDescription>
            Identify and execute tax-loss harvesting strategies while avoiding wash sale violations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="opportunities" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="opportunities">Opportunities</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

            <TabsContent value="opportunities" className="space-y-4">
              {/* Filters */}
              <div id="opportunity-filters" className="flex gap-4 flex-wrap">
                <select 
                  className="border rounded-md px-3 py-2 text-sm"
                  value={selectedFilters.priority}
                  onChange={(e) => setSelectedFilters({...selectedFilters, priority: e.target.value})}
                >
                  <option value="all">All Priorities</option>
                  <option value="High">High Priority</option>
                  <option value="Medium">Medium Priority</option>
                  <option value="Low">Low Priority</option>
                </select>

                <select 
                  className="border rounded-md px-3 py-2 text-sm"
                  value={selectedFilters.riskLevel}
                  onChange={(e) => setSelectedFilters({...selectedFilters, riskLevel: e.target.value})}
                >
                  <option value="all">All Risk Levels</option>
                  <option value="Low">Low Risk</option>
                  <option value="Medium">Medium Risk</option>
                  <option value="High">High Risk</option>
                </select>
              </div>

              {/* Opportunities List */}
              <div className="space-y-4">
                {filteredOpportunities.map((opportunity) => (
                  <Card key={opportunity.id} id={`opportunity-${opportunity.id}`} className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg font-semibold">
                            {opportunity.security.symbol} - {opportunity.security.name}
                          </CardTitle>
                          <CardDescription className="flex items-center gap-2 mt-1">
                            <span>{opportunity.security.sector}</span>
                            <Separator orientation="vertical" className="h-4" />
                            <span>{opportunity.accountType}</span>
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getPriorityColor(opportunity.harvestRecommendation.priority)}>
                            {opportunity.harvestRecommendation.priority}
                          </Badge>
                          {opportunity.washSaleRisk.isWashSaleRisk && (
                            <Badge variant="destructive" className="flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3" />
                              Wash Sale Risk
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Position Info */}
                        <div id={`position-info-${opportunity.id}`} className="space-y-2">
                          <h4 className="font-semibold text-sm">Position Details</h4>
                          <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                              <span>Shares:</span>
                              <span>{opportunity.position.shares.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Avg Cost:</span>
                              <span>${opportunity.position.avgCostBasis.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Current Price:</span>
                              <span>${opportunity.position.currentPrice.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between text-red-600 font-medium">
                              <span>Unrealized Loss:</span>
                              <span>${opportunity.position.unrealizedLoss.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between text-red-600">
                              <span>Loss %:</span>
                              <span>{opportunity.position.unrealizedLossPercent.toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>

                        {/* Tax Benefits */}
                        <div id={`tax-benefits-${opportunity.id}`} className="space-y-2">
                          <h4 className="font-semibold text-sm">Tax Savings</h4>
                          <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                              <span>Federal:</span>
                              <span className="text-green-600">${opportunity.taxBenefits.federalTaxSavings.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>State:</span>
                              <span className="text-green-600">${opportunity.taxBenefits.stateTaxSavings.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between font-medium">
                              <span>Total Savings:</span>
                              <span className="text-green-600">${opportunity.taxBenefits.totalTaxSavings.toLocaleString()}</span>
                            </div>
                          </div>
                        </div>

                        {/* Recommendation */}
                        <div id={`recommendation-${opportunity.id}`} className="space-y-2">
                          <h4 className="font-semibold text-sm">Recommendation</h4>
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              {opportunity.harvestRecommendation.action === 'harvest' ? (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              ) : opportunity.harvestRecommendation.action === 'hold' ? (
                                <Clock className="h-4 w-4 text-yellow-600" />
                              ) : (
                                <Calculator className="h-4 w-4 text-blue-600" />
                              )}
                              <span className="text-sm font-medium capitalize">
                                {opportunity.harvestRecommendation.action}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">
                              {opportunity.harvestRecommendation.reasoning}
                            </p>
                            {opportunity.harvestRecommendation.optimalTiming && (
                              <p className="text-sm text-blue-600">
                                Optimal timing: {opportunity.harvestRecommendation.optimalTiming}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Wash Sale Risk Details */}
                      {opportunity.washSaleRisk.isWashSaleRisk && (
                        <Alert id={`wash-sale-alert-${opportunity.id}`}>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            <div className="space-y-1">
                              <p className="font-medium">
                                Wash Sale Risk ({opportunity.washSaleRisk.riskLevel})
                              </p>
                              {opportunity.washSaleRisk.riskFactors.map((factor, index) => (
                                <p key={index} className="text-sm">• {factor}</p>
                              ))}
                              {opportunity.washSaleRisk.waitPeriod && (
                                <p className="text-sm font-medium">
                                  Wait {opportunity.washSaleRisk.waitPeriod} days before repurchasing
                                </p>
                              )}
                            </div>
                          </AlertDescription>
                        </Alert>
                      )}

                      {/* Replacement Options */}
                      {opportunity.replacementOptions.length > 0 && (
                        <div id={`replacement-options-${opportunity.id}`} className="space-y-2">
                          <h4 className="font-semibold text-sm">Replacement Options</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {opportunity.replacementOptions.map((replacement, index) => (
                              <div key={index} className="p-3 border rounded-md space-y-1">
                                <div className="flex justify-between items-start">
                                  <div>
                                    <p className="font-medium text-sm">{replacement.symbol}</p>
                                    <p className="text-xs text-gray-600">{replacement.name}</p>
                                  </div>
                                  <Badge variant="outline" className="text-xs">
                                    Score: {replacement.suitabilityScore}
                                  </Badge>
                                </div>
                                <div className="flex justify-between text-xs">
                                  <span>Correlation: {replacement.correlation}</span>
                                  <span>Expense: {replacement.expense_ratio}%</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div id={`action-buttons-${opportunity.id}`} className="flex gap-2 pt-2 border-t">
                        {opportunity.harvestRecommendation.action === 'harvest' ? (
                          <Button 
                            onClick={() => handleHarvestAction(opportunity.id, 'harvest')}
                            className="flex items-center gap-2"
                          >
                            <TrendingDown className="h-4 w-4" />
                            Execute Harvest
                          </Button>
                        ) : opportunity.harvestRecommendation.action === 'hold' ? (
                          <Button 
                            variant="secondary"
                            onClick={() => handleHarvestAction(opportunity.id, 'schedule')}
                            className="flex items-center gap-2"
                          >
                            <Calendar className="h-4 w-4" />
                            Schedule for Later
                          </Button>
                        ) : (
                          <Button 
                            variant="outline"
                            onClick={() => handleHarvestAction(opportunity.id, 'analyze')}
                            className="flex items-center gap-2"
                          >
                            <Calculator className="h-4 w-4" />
                            Analyze Further
                          </Button>
                        )}
                        <Button 
                          variant="outline"
                          onClick={() => setActiveOpportunity(opportunity)}
                        >
                          View Details
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {filteredOpportunities.length === 0 && (
                <Card id="no-opportunities">
                  <CardContent className="text-center py-8">
                    <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Harvesting Opportunities</h3>
                    <p className="text-gray-600">
                      Great! You currently have no tax loss harvesting opportunities that meet the selected criteria.
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="analytics" className="space-y-4">
              <Card id="harvesting-analytics">
                <CardHeader>
                  <CardTitle>Harvesting Analytics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div id="ytd-progress" className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Year-to-Date Tax Loss Harvesting</span>
                        <span>$8,450 of $3,000 annual limit</span>
                      </div>
                      <Progress value={100} className="w-full" />
                      <p className="text-sm text-gray-600">
                        Excess losses carry forward to future years
                      </p>
                    </div>
                    
                    <div id="potential-savings" className="space-y-2">
                      <h4 className="font-semibold">Potential Additional Savings</h4>
                      <div className="text-2xl font-bold text-green-600">
                        ${summary?.totalTaxSavings.toLocaleString() || '0'}
                      </div>
                      <p className="text-sm text-gray-600">
                        Based on current unrealized losses and tax brackets
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="history" className="space-y-4">
              <Card id="harvesting-history">
                <CardHeader>
                  <CardTitle>Harvesting History</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Historical tax loss harvesting data and performance metrics will be displayed here.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};