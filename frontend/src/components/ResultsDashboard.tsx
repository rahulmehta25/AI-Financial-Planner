"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SimulationResult, TradeOffScenario } from '@/types';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { ProbabilityChart, PortfolioAllocationChart, TradeOffChart } from '@/components/charts';
import {
  FileDown,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  Calendar,
  Target,
  BarChart3,
} from 'lucide-react';

interface ResultsDashboardProps {
  result: SimulationResult;
  onExportPDF?: () => void;
  onRunNewSimulation?: () => void;
  onApplyScenario?: (scenario: TradeOffScenario) => void;
}

export default function ResultsDashboard({
  result,
  onExportPDF,
  onRunNewSimulation,
  onApplyScenario,
}: ResultsDashboardProps) {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'scenarios' | 'narrative'>('overview');

  // Generate chart data from simulation result
  const chartData = result.projectedPortfolioValues.map((value, index) => ({
    year: new Date().getFullYear() + index,
    median: value,
    percentile10: result.percentile10Value * (value / result.medianPortfolioValue),
    percentile90: result.percentile90Value * (value / result.medianPortfolioValue),
    targetIncome: result.projectedAnnualIncome[index] || result.projectedAnnualIncome[result.projectedAnnualIncome.length - 1],
  }));

  const getSuccessIcon = (probability: number) => {
    if (probability >= 70) return <CheckCircle2 className="w-6 h-6 text-green-500" />;
    if (probability >= 40) return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
    return <AlertTriangle className="w-6 h-6 text-red-500" />;
  };

  const getSuccessColor = (probability: number) => {
    if (probability >= 70) return 'border-green-200 bg-green-50 dark:bg-green-900/20';
    if (probability >= 40) return 'border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20';
    return 'border-red-200 bg-red-50 dark:bg-red-900/20';
  };

  const MetricCard = ({ 
    icon, 
    title, 
    value, 
    subtitle, 
    color = 'text-gray-600' 
  }: {
    icon: React.ReactNode;
    title: string;
    value: string;
    subtitle?: string;
    color?: string;
  }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-800 ${color}`}>
            {icon}
          </div>
        </div>
        <div className="mt-4">
          <h3 className="text-2xl font-bold">{value}</h3>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div id="results-dashboard" className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div id="dashboard-header" className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                Your Financial Plan
              </h1>
              <p className="text-muted-foreground">
                Generated on {new Date(result.timestamp).toLocaleDateString()}
              </p>
            </div>
            
            <div className="flex gap-3">
              <Button
                id="export-pdf-button"
                onClick={onExportPDF}
                variant="outline"
                className="flex items-center gap-2"
              >
                <FileDown className="w-4 h-4" />
                Export PDF
              </Button>
              <Button
                id="run-new-simulation-button"
                onClick={onRunNewSimulation}
                className="flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Run New Analysis
              </Button>
            </div>
          </div>
        </div>

        {/* Success Overview */}
        <div id="success-overview" className={`mb-8 p-6 border rounded-lg ${getSuccessColor(result.probabilityOfSuccess)}`}>
          <div className="flex items-center gap-4 mb-4">
            {getSuccessIcon(result.probabilityOfSuccess)}
            <div>
              <h2 className="text-2xl font-bold">
                {formatPercent(result.probabilityOfSuccess)} Probability of Success
              </h2>
              <p className="text-muted-foreground">
                Based on 10,000 Monte Carlo simulations
              </p>
            </div>
          </div>
          
          {result.probabilityOfSuccess < 70 && (
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg">
              <p className="text-sm">
                <strong>Consider:</strong> Your current plan has some risk of not meeting your goals. 
                Review the trade-off scenarios below to see how small adjustments can improve your outcomes.
              </p>
            </div>
          )}
        </div>

        {/* Key Metrics */}
        <div id="key-metrics" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            icon={<Target className="w-5 h-5" />}
            title="Median Portfolio Value"
            value={formatCurrency(result.medianPortfolioValue)}
            subtitle="At retirement"
          />
          <MetricCard
            icon={<DollarSign className="w-5 h-5" />}
            title="Projected Annual Income"
            value={formatCurrency(result.projectedAnnualIncome[0] || 0)}
            subtitle="First year of retirement"
          />
          <MetricCard
            icon={<AlertTriangle className="w-5 h-5" />}
            title="Shortfall Risk"
            value={formatPercent(result.shortfallRisk)}
            subtitle="Probability of running out of money"
            color="text-orange-600"
          />
          <MetricCard
            icon={<BarChart3 className="w-5 h-5" />}
            title="Range of Outcomes"
            value={`${formatCurrency(result.percentile10Value)} - ${formatCurrency(result.percentile90Value)}`}
            subtitle="10th to 90th percentile"
          />
        </div>

        {/* Tab Navigation */}
        <div id="dashboard-tabs" className="mb-6">
          <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'scenarios', label: 'Trade-Offs', icon: TrendingUp },
              { id: 'narrative', label: 'AI Analysis', icon: Target },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  id={`tab-${tab.id}`}
                  onClick={() => setSelectedTab(tab.id as any)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    selectedTab === tab.id
                      ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div id="dashboard-content">
          {selectedTab === 'overview' && (
            <div className="space-y-8">
              {/* Probability Chart */}
              <ProbabilityChart 
                data={chartData}
                probabilityOfSuccess={result.probabilityOfSuccess}
              />
              
              {/* Portfolio Allocation */}
              <PortfolioAllocationChart 
                allocation={result.recommendedPortfolio}
              />
            </div>
          )}

          {selectedTab === 'scenarios' && (
            <TradeOffChart
              scenarios={result.tradeOffScenarios}
              baselineProbability={result.probabilityOfSuccess}
              onScenarioSelect={onApplyScenario}
            />
          )}

          {selectedTab === 'narrative' && (
            <Card id="ai-narrative-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  AI Financial Analysis
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Personalized insights and recommendations based on your financial profile
                </p>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {result.aiNarrative || 'AI narrative analysis is being generated...'}
                  </div>
                </div>
                
                {/* Action Items */}
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-3">
                    Key Action Items
                  </h3>
                  <div className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                    {result.tradeOffScenarios.map((scenario, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span>{scenario.recommendation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function generateDemoNarrative(result: SimulationResult, demoProfile?: string): string {
  const profileNarratives = {
    young_professional: `Based on our analysis of your financial profile as a young professional, you're in an excellent position to build long-term wealth. Your current savings rate and investment timeline give you significant advantages:

• **Growth Potential**: With a 30+ year investment horizon, you can take advantage of compound growth and market volatility
• **Risk Capacity**: Your age allows for a more aggressive portfolio allocation, maximizing growth potential
• **Goal Achievement**: Your emergency fund and house down payment goals are well-structured and achievable

Our Monte Carlo simulations show a ${result.scenarios?.realistic?.goalAchievementRate || 78}% probability of meeting your retirement goals with your current strategy. The projected portfolio value of ${formatCurrency(result.scenarios?.realistic?.finalValue || 1650000)} provides a strong foundation for financial independence.

**Key Insights:**
- Your current savings rate is commendable and sustainable
- Consider maximizing employer 401(k) matching for immediate returns
- International diversification could enhance risk-adjusted returns`,
    
    family_oriented: `Your family-focused financial plan demonstrates excellent prioritization and realistic goal setting. Our analysis reveals several strengths in your approach:

• **Education Planning**: Your 529 contributions are on track to cover projected education costs
• **Balanced Approach**: You're successfully juggling multiple financial priorities
• **Risk Management**: Your moderate risk tolerance aligns well with your family responsibilities

With an ${result.scenarios?.realistic?.goalAchievementRate || 81}% success probability, your plan shows strong potential for achieving all major goals. The expected portfolio value of ${formatCurrency(result.scenarios?.realistic?.finalValue || 1450000)} provides security for your family's future.

**Strategic Recommendations:**
- Consider increasing contributions to tax-advantaged accounts
- Review insurance coverage to protect against unforeseen events
- Explore 529 plan tax benefits in your state`,
    
    pre_retiree: `As you approach retirement, your financial plan reflects wisdom and strategic thinking. Our analysis shows you're well-positioned for a comfortable retirement:

• **Strong Foundation**: Your accumulated wealth provides excellent security
• **Conservative Approach**: Your risk reduction strategy is appropriate for your timeline
• **Healthcare Planning**: Dedicated healthcare reserves show forward-thinking

With an ${result.scenarios?.realistic?.goalAchievementRate || 88}% probability of success, you're on track for your retirement goals. The projected value of ${formatCurrency(result.scenarios?.realistic?.finalValue || 2200000)} should support your desired lifestyle.

**Pre-Retirement Considerations:**
- Social Security optimization strategy is crucial at your age
- Consider gradual portfolio de-risking as you approach retirement
- Healthcare cost planning becomes increasingly important`
  };
  
  return profileNarratives[demoProfile as keyof typeof profileNarratives] || 
    'This analysis provides insights into your financial position and recommendations for optimizing your strategy.';
}