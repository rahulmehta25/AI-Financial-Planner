import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  AnalyticsState,
  PortfolioMetrics,
  RiskMetrics,
  PerformanceAttribution,
  CorrelationData,
  TimeSeriesData,
  RealTimeData,
  AnalyticsFilter,
  AnalyticsAlert,
  WebSocketMessage,
  BacktestResult,
  OptimizationResult,
  StressTestScenario,
  MonteCarloAnalysis,
} from '@/types/analytics';

interface AnalyticsStore extends AnalyticsState {
  // Data setters
  setPortfolioMetrics: (metrics: PortfolioMetrics) => void;
  setRiskMetrics: (metrics: RiskMetrics) => void;
  setPerformanceAttribution: (attribution: PerformanceAttribution[]) => void;
  setCorrelationData: (data: CorrelationData) => void;
  setTimeSeriesData: (data: TimeSeriesData[]) => void;
  setRealTimeData: (data: RealTimeData) => void;

  // Filter management
  updateFilter: (updates: Partial<AnalyticsFilter>) => void;
  setDateRange: (start: Date, end: Date) => void;
  setFrequency: (frequency: AnalyticsFilter['frequency']) => void;

  // Alert management
  addAlert: (alert: Omit<AnalyticsAlert, 'id' | 'timestamp'>) => void;
  acknowledgeAlert: (alertId: string) => void;
  clearAlert: (alertId: string) => void;
  clearAllAlerts: () => void;
  getUnacknowledgedAlerts: () => AnalyticsAlert[];

  // Extended analytics data
  backtestResults: BacktestResult[];
  optimizationResults: OptimizationResult[];
  stressTestScenarios: StressTestScenario[];
  monteCarloAnalysis: MonteCarloAnalysis | null;

  // Extended analytics setters
  setBacktestResults: (results: BacktestResult[]) => void;
  addBacktestResult: (result: BacktestResult) => void;
  setOptimizationResults: (results: OptimizationResult[]) => void;
  addOptimizationResult: (result: OptimizationResult) => void;
  setStressTestScenarios: (scenarios: StressTestScenario[]) => void;
  setMonteCarloAnalysis: (analysis: MonteCarloAnalysis) => void;

  // Loading and error states
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;

  // WebSocket message handling
  handleWebSocketMessage: (message: WebSocketMessage) => void;

  // Data refresh
  refreshData: () => Promise<void>;
  setLastUpdated: (date: Date) => void;

  // Calculations
  calculateSharpeRatio: (returns: number[], riskFreeRate?: number) => number;
  calculateSortinoRatio: (returns: number[], targetReturn?: number) => number;
  calculateMaxDrawdown: (values: number[]) => number;
  calculateVaR: (returns: number[], confidence: number) => number;
  calculateCorrelation: (series1: number[], series2: number[]) => number;

  // Utility functions
  exportData: (format: 'csv' | 'json', dataType?: string) => string;
  resetStore: () => void;
  getFormattedMetrics: () => { [key: string]: string };
}

const defaultFilter: AnalyticsFilter = {
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
};

export const useAnalyticsStore = create<AnalyticsStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        portfolioMetrics: null,
        riskMetrics: null,
        performanceAttribution: null,
        correlationData: null,
        timeSeriesData: null,
        realTimeData: null,
        filter: defaultFilter,
        isLoading: false,
        error: null,
        lastUpdated: null,
        alerts: [],
        backtestResults: [],
        optimizationResults: [],
        stressTestScenarios: [],
        monteCarloAnalysis: null,

        // Data setters
        setPortfolioMetrics: (metrics: PortfolioMetrics) =>
          set({ portfolioMetrics: metrics, lastUpdated: new Date() }),

        setRiskMetrics: (metrics: RiskMetrics) =>
          set({ riskMetrics: metrics, lastUpdated: new Date() }),

        setPerformanceAttribution: (attribution: PerformanceAttribution[]) =>
          set({ performanceAttribution: attribution, lastUpdated: new Date() }),

        setCorrelationData: (data: CorrelationData) =>
          set({ correlationData: data, lastUpdated: new Date() }),

        setTimeSeriesData: (data: TimeSeriesData[]) =>
          set({ timeSeriesData: data, lastUpdated: new Date() }),

        setRealTimeData: (data: RealTimeData) =>
          set({ realTimeData: data }),

        // Filter management
        updateFilter: (updates: Partial<AnalyticsFilter>) =>
          set((state) => ({
            filter: { ...state.filter, ...updates }
          })),

        setDateRange: (start: Date, end: Date) =>
          set((state) => ({
            filter: {
              ...state.filter,
              dateRange: { start, end }
            }
          })),

        setFrequency: (frequency: AnalyticsFilter['frequency']) =>
          set((state) => ({
            filter: { ...state.filter, frequency }
          })),

        // Alert management
        addAlert: (alertData) =>
          set((state) => {
            const alert: AnalyticsAlert = {
              ...alertData,
              id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              timestamp: new Date(),
              acknowledged: false
            };
            return {
              alerts: [alert, ...state.alerts].slice(0, 50) // Keep only last 50 alerts
            };
          }),

        acknowledgeAlert: (alertId: string) =>
          set((state) => ({
            alerts: state.alerts.map(alert =>
              alert.id === alertId ? { ...alert, acknowledged: true } : alert
            )
          })),

        clearAlert: (alertId: string) =>
          set((state) => ({
            alerts: state.alerts.filter(alert => alert.id !== alertId)
          })),

        clearAllAlerts: () => set({ alerts: [] }),

        getUnacknowledgedAlerts: () => {
          const state = get();
          return state.alerts.filter(alert => !alert.acknowledged);
        },

        // Extended analytics setters
        setBacktestResults: (results: BacktestResult[]) =>
          set({ backtestResults: results }),

        addBacktestResult: (result: BacktestResult) =>
          set((state) => ({
            backtestResults: [result, ...state.backtestResults].slice(0, 10) // Keep last 10
          })),

        setOptimizationResults: (results: OptimizationResult[]) =>
          set({ optimizationResults: results }),

        addOptimizationResult: (result: OptimizationResult) =>
          set((state) => ({
            optimizationResults: [result, ...state.optimizationResults].slice(0, 5) // Keep last 5
          })),

        setStressTestScenarios: (scenarios: StressTestScenario[]) =>
          set({ stressTestScenarios: scenarios }),

        setMonteCarloAnalysis: (analysis: MonteCarloAnalysis) =>
          set({ monteCarloAnalysis: analysis }),

        // Loading and error states
        setLoading: (loading: boolean) => set({ isLoading: loading }),

        setError: (error: string | null) => set({ error }),

        clearError: () => set({ error: null }),

        // WebSocket message handling
        handleWebSocketMessage: (message: WebSocketMessage) => {
          const { addAlert } = get();
          
          switch (message.type) {
            case 'portfolio_update':
              set({ realTimeData: message.data as RealTimeData });
              break;
              
            case 'market_data':
              // Update real-time data with new market information
              set((state) => {
                if (state.realTimeData && message.data.holdings) {
                  return {
                    realTimeData: {
                      ...state.realTimeData,
                      holdings: state.realTimeData.holdings.map(holding => {
                        const update = message.data.holdings.find((h: any) => h.symbol === holding.symbol);
                        return update ? { ...holding, ...update } : holding;
                      })
                    }
                  };
                }
                return state;
              });
              break;
              
            case 'risk_alert':
              addAlert({
                type: message.data.type || 'risk',
                severity: message.data.severity || 'medium',
                title: message.data.title || 'Risk Alert',
                message: message.data.message || 'Risk threshold exceeded',
                data: message.data
              });
              break;
              
            case 'performance_update':
              if (message.data.portfolioMetrics) {
                set({ portfolioMetrics: message.data.portfolioMetrics });
              }
              if (message.data.riskMetrics) {
                set({ riskMetrics: message.data.riskMetrics });
              }
              break;
          }
        },

        // Data refresh
        refreshData: async () => {
          const { setLoading, setError, filter } = get();
          setLoading(true);
          setError(null);

          try {
            // In a real implementation, you would make API calls here
            // For now, we'll simulate data refresh
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Mock data refresh logic would go here
            set({ lastUpdated: new Date() });
          } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to refresh data');
          } finally {
            setLoading(false);
          }
        },

        setLastUpdated: (date: Date) => set({ lastUpdated: date }),

        // Calculation functions
        calculateSharpeRatio: (returns: number[], riskFreeRate: number = 0.02) => {
          if (returns.length === 0) return 0;
          
          const meanReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
          const variance = returns.reduce((sum, r) => sum + Math.pow(r - meanReturn, 2), 0) / (returns.length - 1);
          const stdDev = Math.sqrt(variance);
          
          return stdDev === 0 ? 0 : (meanReturn - riskFreeRate) / stdDev;
        },

        calculateSortinoRatio: (returns: number[], targetReturn: number = 0) => {
          if (returns.length === 0) return 0;
          
          const meanReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
          const downsideReturns = returns.filter(r => r < targetReturn);
          
          if (downsideReturns.length === 0) return Infinity;
          
          const downsideVariance = downsideReturns.reduce((sum, r) => sum + Math.pow(r - targetReturn, 2), 0) / downsideReturns.length;
          const downsideDeviation = Math.sqrt(downsideVariance);
          
          return downsideDeviation === 0 ? 0 : (meanReturn - targetReturn) / downsideDeviation;
        },

        calculateMaxDrawdown: (values: number[]) => {
          if (values.length === 0) return 0;
          
          let maxDrawdown = 0;
          let peak = values[0];
          
          for (let i = 1; i < values.length; i++) {
            if (values[i] > peak) {
              peak = values[i];
            } else {
              const drawdown = (peak - values[i]) / peak;
              maxDrawdown = Math.max(maxDrawdown, drawdown);
            }
          }
          
          return maxDrawdown * 100; // Return as percentage
        },

        calculateVaR: (returns: number[], confidence: number) => {
          if (returns.length === 0) return 0;
          
          const sortedReturns = [...returns].sort((a, b) => a - b);
          const index = Math.floor(sortedReturns.length * (1 - confidence / 100));
          
          return sortedReturns[index] || 0;
        },

        calculateCorrelation: (series1: number[], series2: number[]) => {
          if (series1.length !== series2.length || series1.length === 0) return 0;
          
          const n = series1.length;
          const mean1 = series1.reduce((sum, val) => sum + val, 0) / n;
          const mean2 = series2.reduce((sum, val) => sum + val, 0) / n;
          
          let numerator = 0;
          let sum1Sq = 0;
          let sum2Sq = 0;
          
          for (let i = 0; i < n; i++) {
            const diff1 = series1[i] - mean1;
            const diff2 = series2[i] - mean2;
            numerator += diff1 * diff2;
            sum1Sq += diff1 * diff1;
            sum2Sq += diff2 * diff2;
          }
          
          const denominator = Math.sqrt(sum1Sq * sum2Sq);
          return denominator === 0 ? 0 : numerator / denominator;
        },

        // Utility functions
        exportData: (format: 'csv' | 'json', dataType?: string) => {
          const state = get();
          
          const data = {
            portfolioMetrics: state.portfolioMetrics,
            riskMetrics: state.riskMetrics,
            performanceAttribution: state.performanceAttribution,
            correlationData: state.correlationData,
            timeSeriesData: state.timeSeriesData,
            alerts: state.alerts,
            filter: state.filter,
            lastUpdated: state.lastUpdated
          };
          
          if (format === 'json') {
            return JSON.stringify(data, null, 2);
          } else {
            // Convert to CSV format
            let csv = '';
            
            if (!dataType || dataType === 'portfolio') {
              csv += 'Portfolio Metrics\n';
              if (state.portfolioMetrics) {
                Object.entries(state.portfolioMetrics).forEach(([key, value]) => {
                  csv += `${key},${value}\n`;
                });
              }
              csv += '\n';
            }
            
            if (!dataType || dataType === 'risk') {
              csv += 'Risk Metrics\n';
              if (state.riskMetrics) {
                Object.entries(state.riskMetrics).forEach(([key, value]) => {
                  csv += `${key},${value}\n`;
                });
              }
              csv += '\n';
            }
            
            return csv;
          }
        },

        resetStore: () =>
          set({
            portfolioMetrics: null,
            riskMetrics: null,
            performanceAttribution: null,
            correlationData: null,
            timeSeriesData: null,
            realTimeData: null,
            filter: defaultFilter,
            isLoading: false,
            error: null,
            lastUpdated: null,
            alerts: [],
            backtestResults: [],
            optimizationResults: [],
            stressTestScenarios: [],
            monteCarloAnalysis: null,
          }),

        getFormattedMetrics: () => {
          const { portfolioMetrics, riskMetrics } = get();
          const formatted: { [key: string]: string } = {};
          
          if (portfolioMetrics) {
            formatted['Total Return'] = `${portfolioMetrics.totalReturn.toFixed(2)}%`;
            formatted['Annualized Return'] = `${portfolioMetrics.annualizedReturn.toFixed(2)}%`;
            formatted['Volatility'] = `${portfolioMetrics.volatility.toFixed(2)}%`;
            formatted['Sharpe Ratio'] = portfolioMetrics.sharpeRatio.toFixed(3);
            formatted['Sortino Ratio'] = portfolioMetrics.sortinoRatio.toFixed(3);
            formatted['Max Drawdown'] = `${portfolioMetrics.maxDrawdown.toFixed(2)}%`;
            formatted['Beta'] = portfolioMetrics.beta.toFixed(3);
            formatted['Alpha'] = `${portfolioMetrics.alpha.toFixed(2)}%`;
          }
          
          if (riskMetrics) {
            formatted['VaR 95%'] = `${riskMetrics.var95.toFixed(2)}%`;
            formatted['VaR 99%'] = `${riskMetrics.var99.toFixed(2)}%`;
            formatted['CVaR 95%'] = `${riskMetrics.cvar95.toFixed(2)}%`;
            formatted['CVaR 99%'] = `${riskMetrics.cvar99.toFixed(2)}%`;
          }
          
          return formatted;
        },
      }),
      {
        name: 'analytics-storage',
        partialize: (state) => ({
          filter: state.filter,
          alerts: state.alerts.slice(0, 10), // Persist only last 10 alerts
          backtestResults: state.backtestResults.slice(0, 3), // Persist only last 3 backtest results
          optimizationResults: state.optimizationResults.slice(0, 2), // Persist only last 2 optimization results
        }),
      }
    ),
    {
      name: 'analytics-store',
    }
  )
);

// Selector hooks for specific data
export const usePortfolioMetrics = () => useAnalyticsStore(state => state.portfolioMetrics);
export const useRiskMetrics = () => useAnalyticsStore(state => state.riskMetrics);
export const usePerformanceAttribution = () => useAnalyticsStore(state => state.performanceAttribution);
export const useCorrelationData = () => useAnalyticsStore(state => state.correlationData);
export const useTimeSeriesData = () => useAnalyticsStore(state => state.timeSeriesData);
export const useRealTimeData = () => useAnalyticsStore(state => state.realTimeData);
export const useAnalyticsFilter = () => useAnalyticsStore(state => state.filter);
export const useAnalyticsAlerts = () => useAnalyticsStore(state => state.alerts);
export const useAnalyticsLoading = () => useAnalyticsStore(state => state.isLoading);
export const useAnalyticsError = () => useAnalyticsStore(state => state.error);

// Combined hooks
export const useAnalyticsData = () => useAnalyticsStore(state => ({
  portfolioMetrics: state.portfolioMetrics,
  riskMetrics: state.riskMetrics,
  performanceAttribution: state.performanceAttribution,
  correlationData: state.correlationData,
  timeSeriesData: state.timeSeriesData,
  realTimeData: state.realTimeData,
  isLoading: state.isLoading,
  error: state.error,
  lastUpdated: state.lastUpdated,
}));

export const useAnalyticsActions = () => useAnalyticsStore(state => ({
  setPortfolioMetrics: state.setPortfolioMetrics,
  setRiskMetrics: state.setRiskMetrics,
  setPerformanceAttribution: state.setPerformanceAttribution,
  setCorrelationData: state.setCorrelationData,
  setTimeSeriesData: state.setTimeSeriesData,
  setRealTimeData: state.setRealTimeData,
  updateFilter: state.updateFilter,
  setDateRange: state.setDateRange,
  setFrequency: state.setFrequency,
  refreshData: state.refreshData,
  addAlert: state.addAlert,
  acknowledgeAlert: state.acknowledgeAlert,
  clearError: state.clearError,
  handleWebSocketMessage: state.handleWebSocketMessage,
}));