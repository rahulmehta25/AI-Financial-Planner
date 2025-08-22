'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  PortfolioMetrics,
  RiskMetrics,
  PerformanceAttribution,
  CorrelationData,
  TimeSeriesData,
  AnalyticsFilter,
  ExportOptions,
  AnalyticsAlert,
} from '@/types/analytics';

import PortfolioAnalyticsChart from './PortfolioAnalyticsChart';
import CorrelationMatrix from './CorrelationMatrix';
import PerformanceAttributionChart from './PerformanceAttributionChart';
import RiskMetricsDashboard from './RiskMetricsDashboard';
import ExportManager from './ExportManager';
import { 
  WebSocketProvider, 
  useWebSocket, 
  useRiskAlerts, 
  ConnectionStatus 
} from './WebSocketProvider';

import { 
  TrendingUp, 
  TrendingDown,
  Activity,
  PieChart,
  BarChart3,
  AlertTriangle,
  Settings,
  RefreshCw,
  Calendar,
  Filter,
  Bell,
  X
} from 'lucide-react';

interface AnalyticsDashboardProps {
  portfolioId?: string;
  initialData?: {
    portfolioMetrics?: PortfolioMetrics;
    riskMetrics?: RiskMetrics;
    performanceAttribution?: PerformanceAttribution[];
    correlationData?: CorrelationData;
    timeSeriesData?: TimeSeriesData[];
  };
  className?: string;
}

const AnalyticsDashboardContent: React.FC<AnalyticsDashboardProps> = ({
  portfolioId,
  initialData,
  className = '',
}) => {
  // State
  const [activeTab, setActiveTab] = useState('overview');
  const [filter, setFilter] = useState<AnalyticsFilter>({
    dateRange: {
      start: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), // 1 year ago
      end: new Date()
    },
    frequency: 'daily',
    currency: 'USD',
    adjustments: {
      dividends: true,
      splits: true,
      inflation: false
    }
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // WebSocket hooks
  const { isConnected, realTimeData } = useWebSocket();
  const { alerts, unacknowledgedAlerts, acknowledgAlert } = useRiskAlerts();

  // Data state
  const [portfolioMetrics, setPortfolioMetrics] = useState<PortfolioMetrics | undefined>(
    initialData?.portfolioMetrics
  );
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | undefined>(
    initialData?.riskMetrics
  );
  const [performanceAttribution, setPerformanceAttribution] = useState<PerformanceAttribution[] | undefined>(
    initialData?.performanceAttribution
  );
  const [correlationData, setCorrelationData] = useState<CorrelationData | undefined>(
    initialData?.correlationData
  );
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[] | undefined>(
    initialData?.timeSeriesData
  );

  // Mock data generation for demo purposes
  const generateMockData = useMemo(() => {
    if (initialData?.portfolioMetrics) return initialData;

    const mockTimeSeriesData: TimeSeriesData[] = [];
    const startDate = new Date(filter.dateRange.start);
    const endDate = new Date(filter.dateRange.end);
    
    let currentValue = 100000;
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      const randomChange = (Math.random() - 0.5) * 0.02; // ±1% daily change
      currentValue *= (1 + randomChange);
      mockTimeSeriesData.push({
        date: new Date(d),
        value: currentValue,
        label: `Portfolio Value`
      });
    }

    const totalReturn = ((currentValue - 100000) / 100000) * 100;
    const volatility = 15 + Math.random() * 10; // 15-25% volatility
    const sharpeRatio = (totalReturn / 100) / (volatility / 100);

    const mockPortfolioMetrics: PortfolioMetrics = {
      totalReturn,
      annualizedReturn: totalReturn * (365 / mockTimeSeriesData.length),
      volatility,
      sharpeRatio,
      sortinoRatio: sharpeRatio * 1.2,
      maxDrawdown: 8 + Math.random() * 12,
      beta: 0.8 + Math.random() * 0.4,
      alpha: -2 + Math.random() * 4,
      informationRatio: -0.5 + Math.random(),
      trackingError: 3 + Math.random() * 5
    };

    const mockRiskMetrics: RiskMetrics = {
      var95: -1.5 - Math.random() * 2,
      var99: -2.5 - Math.random() * 3,
      cvar95: -2.0 - Math.random() * 2.5,
      cvar99: -3.5 - Math.random() * 4,
      expectedShortfall: -2.2 - Math.random() * 2,
      downsideDeviation: volatility * 0.7,
      maxDrawdown: mockPortfolioMetrics.maxDrawdown,
      ulcerIndex: 5 + Math.random() * 10,
      calmarRatio: mockPortfolioMetrics.annualizedReturn / mockPortfolioMetrics.maxDrawdown
    };

    const mockPerformanceAttribution: PerformanceAttribution[] = [
      {
        assetClass: 'US Stocks',
        allocation: 60,
        benchmark: 55,
        portfolioReturn: 12.5,
        allocationEffect: 0.25,
        selectionEffect: 0.15,
        totalContribution: 7.5,
        sectors: [
          { name: 'Technology', weight: 25, return: 15.2, benchmark: 12.8, contribution: 2.1 },
          { name: 'Healthcare', weight: 15, return: 8.9, benchmark: 9.2, contribution: 1.3 },
          { name: 'Financials', weight: 20, return: 11.1, benchmark: 10.5, contribution: 2.2 }
        ]
      },
      {
        assetClass: 'International Stocks',
        allocation: 25,
        benchmark: 30,
        portfolioReturn: 8.2,
        allocationEffect: -0.15,
        selectionEffect: 0.08,
        totalContribution: 2.05
      },
      {
        assetClass: 'Bonds',
        allocation: 10,
        benchmark: 10,
        portfolioReturn: 3.5,
        allocationEffect: 0.0,
        selectionEffect: 0.05,
        totalContribution: 0.35
      },
      {
        assetClass: 'REITs',
        allocation: 5,
        benchmark: 5,
        portfolioReturn: 6.8,
        allocationEffect: 0.0,
        selectionEffect: 0.02,
        totalContribution: 0.34
      }
    ];

    const assets = ['US Stocks', 'International Stocks', 'Bonds', 'REITs', 'Commodities'];
    const correlationMatrix = assets.map(() => 
      assets.map(() => -0.3 + Math.random() * 1.3)
    );
    // Ensure diagonal is 1
    correlationMatrix.forEach((row, i) => row[i] = 1);

    const mockCorrelationData: CorrelationData = {
      assets,
      matrix: correlationMatrix,
      metadata: {
        period: '1Y',
        frequency: 'daily',
        startDate: filter.dateRange.start,
        endDate: filter.dateRange.end
      }
    };

    return {
      portfolioMetrics: mockPortfolioMetrics,
      riskMetrics: mockRiskMetrics,
      performanceAttribution: mockPerformanceAttribution,
      correlationData: mockCorrelationData,
      timeSeriesData: mockTimeSeriesData
    };
  }, [filter, initialData]);

  // Initialize data
  useEffect(() => {
    const data = generateMockData;
    setPortfolioMetrics(data.portfolioMetrics);
    setRiskMetrics(data.riskMetrics);
    setPerformanceAttribution(data.performanceAttribution);
    setCorrelationData(data.correlationData);
    setTimeSeriesData(data.timeSeriesData);
  }, [generateMockData]);

  // Handle refresh
  const handleRefresh = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real app, you'd fetch fresh data here
      const data = generateMockData;
      setPortfolioMetrics(data.portfolioMetrics);
      setRiskMetrics(data.riskMetrics);
      setPerformanceAttribution(data.performanceAttribution);
      setCorrelationData(data.correlationData);
      setTimeSeriesData(data.timeSeriesData);
      setLastRefresh(new Date());
    } catch (err) {
      setError('Failed to refresh data');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle export
  const handleExport = (options: ExportOptions) => {
    console.log('Exporting with options:', options);
    // Implementation would handle the actual export
  };

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    if (!portfolioMetrics || !realTimeData) return null;

    return {
      currentValue: realTimeData.portfolioValue,
      dayChange: realTimeData.dayChange,
      dayChangePercent: realTimeData.dayChangePercent,
      totalReturn: portfolioMetrics.totalReturn,
      sharpeRatio: portfolioMetrics.sharpeRatio,
      maxDrawdown: portfolioMetrics.maxDrawdown
    };
  }, [portfolioMetrics, realTimeData]);

  return (
    <div className={`space-y-6 ${className}`} data-analytics-container>
      {/* Header */}
      <Card className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Portfolio Analytics Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Advanced analytics and risk management for your portfolio
            </p>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
              <ConnectionStatus />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Select value={filter.frequency} onValueChange={(value: any) => 
              setFilter(prev => ({ ...prev, frequency: value }))
            }>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab('export')}
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Alert Banner */}
        {unacknowledgedAlerts.length > 0 && (
          <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  {unacknowledgedAlerts.length} Risk Alert{unacknowledgedAlerts.length !== 1 ? 's' : ''}
                </h4>
                <div className="mt-2 space-y-1">
                  {unacknowledgedAlerts.slice(0, 3).map(alert => (
                    <div key={alert.id} className="flex items-center justify-between">
                      <span className="text-xs text-yellow-700 dark:text-yellow-300">
                        {alert.title}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => acknowledgAlert(alert.id)}
                        className="h-6 w-6 p-0"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Summary Cards */}
      {summaryStats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Portfolio Value</div>
                <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  ${summaryStats.currentValue.toLocaleString()}
                </div>
              </div>
              <PieChart className="h-6 w-6 text-blue-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Day Change</div>
                <div className={`text-lg font-bold ${summaryStats.dayChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {summaryStats.dayChange >= 0 ? '+' : ''}${summaryStats.dayChange.toLocaleString()}
                </div>
              </div>
              {summaryStats.dayChange >= 0 ? 
                <TrendingUp className="h-6 w-6 text-green-600" /> :
                <TrendingDown className="h-6 w-6 text-red-600" />
              }
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Day Change %</div>
                <div className={`text-lg font-bold ${summaryStats.dayChangePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {summaryStats.dayChangePercent >= 0 ? '+' : ''}{summaryStats.dayChangePercent.toFixed(2)}%
                </div>
              </div>
              <Activity className="h-6 w-6 text-blue-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Return</div>
                <div className={`text-lg font-bold ${summaryStats.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {summaryStats.totalReturn >= 0 ? '+' : ''}{summaryStats.totalReturn.toFixed(2)}%
                </div>
              </div>
              <BarChart3 className="h-6 w-6 text-green-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</div>
                <div className={`text-lg font-bold ${summaryStats.sharpeRatio > 1 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {summaryStats.sharpeRatio.toFixed(2)}
                </div>
              </div>
              <Activity className="h-6 w-6 text-blue-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</div>
                <div className="text-lg font-bold text-red-600">
                  -{summaryStats.maxDrawdown.toFixed(2)}%
                </div>
              </div>
              <TrendingDown className="h-6 w-6 text-red-600" />
            </div>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
          <TabsTrigger value="attribution">Attribution</TabsTrigger>
          <TabsTrigger value="correlation">Correlation</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {timeSeriesData && portfolioMetrics && (
              <PortfolioAnalyticsChart
                data={timeSeriesData}
                metrics={portfolioMetrics}
                title="Portfolio Performance"
                onExport={handleExport}
              />
            )}
            
            {riskMetrics && portfolioMetrics && timeSeriesData && (
              <RiskMetricsDashboard
                riskMetrics={riskMetrics}
                portfolioMetrics={portfolioMetrics}
                returns={timeSeriesData}
                className="xl:col-span-1"
              />
            )}
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          {timeSeriesData && portfolioMetrics && (
            <PortfolioAnalyticsChart
              data={timeSeriesData}
              metrics={portfolioMetrics}
              title="Detailed Performance Analysis"
              height={600}
              onExport={handleExport}
            />
          )}
        </TabsContent>

        <TabsContent value="risk">
          {riskMetrics && portfolioMetrics && timeSeriesData && (
            <RiskMetricsDashboard
              riskMetrics={riskMetrics}
              portfolioMetrics={portfolioMetrics}
              returns={timeSeriesData}
              onExport={handleExport}
            />
          )}
        </TabsContent>

        <TabsContent value="attribution">
          {performanceAttribution && (
            <PerformanceAttributionChart
              data={performanceAttribution}
              title="Performance Attribution Analysis"
              onExport={handleExport}
              onDrillDown={(item) => console.log('Drill down:', item)}
            />
          )}
        </TabsContent>

        <TabsContent value="correlation">
          {correlationData && (
            <CorrelationMatrix
              data={correlationData}
              title="Asset Correlation Analysis"
              onExport={handleExport}
              onCellClick={(asset1, asset2, correlation) => 
                console.log(`Correlation between ${asset1} and ${asset2}: ${correlation}`)
              }
            />
          )}
        </TabsContent>

        <TabsContent value="export">
          <ExportManager
            portfolioMetrics={portfolioMetrics}
            riskMetrics={riskMetrics}
            performanceAttribution={performanceAttribution}
            correlationData={correlationData}
            timeSeriesData={timeSeriesData}
          />
        </TabsContent>
      </Tabs>

      {/* Error Display */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50 dark:bg-red-900/20">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setError(null)}
              className="ml-auto h-6 w-6 p-0"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

// Main component with WebSocket provider
export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = (props) => {
  return (
    <WebSocketProvider autoConnect={true}>
      <AnalyticsDashboardContent {...props} />
    </WebSocketProvider>
  );
};

export default AnalyticsDashboard;