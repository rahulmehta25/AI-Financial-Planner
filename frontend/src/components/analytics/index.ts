// Export all analytics components
export { default as AnalyticsDashboard } from './AnalyticsDashboard';
export { default as PortfolioAnalyticsChart } from './PortfolioAnalyticsChart';
export { default as CorrelationMatrix } from './CorrelationMatrix';
export { default as PerformanceAttributionChart } from './PerformanceAttributionChart';
export { default as RiskMetricsDashboard } from './RiskMetricsDashboard';
export { default as ExportManager } from './ExportManager';
export { 
  default as WebSocketProvider,
  useWebSocket,
  useRealTimePortfolio,
  useRealTimeMarket,
  useRiskAlerts,
  ConnectionStatus
} from './WebSocketProvider';

// Re-export types for convenience
export type {
  PortfolioMetrics,
  RiskMetrics,
  PerformanceAttribution,
  SectorAttribution,
  CorrelationData,
  HeatMapData,
  DrillDownData,
  TimeSeriesData,
  RealTimeData,
  ExportOptions,
  ChartConfiguration,
  AxisConfiguration,
  LegendConfiguration,
  TooltipConfiguration,
  AnimationConfiguration,
  AnalyticsFilter,
  AnalyticsState,
  WebSocketMessage,
  AnalyticsAlert,
  BacktestResult,
  TradeRecord,
  OptimizationResult,
  StressTestScenario,
  MonteCarloAnalysis,
} from '@/types/analytics';