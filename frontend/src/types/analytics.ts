// Analytics-specific types for portfolio analysis
export interface TimeSeriesData {
  date: Date;
  value: number;
  label?: string;
}

export interface PortfolioMetrics {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  beta: number;
  alpha: number;
  informationRatio: number;
  trackingError: number;
}

export interface RiskMetrics {
  var95: number; // Value at Risk 95%
  var99: number; // Value at Risk 99%
  cvar95: number; // Conditional Value at Risk 95%
  cvar99: number; // Conditional Value at Risk 99%
  expectedShortfall: number;
  downsideDeviation: number;
  maxDrawdown: number;
  ulcerIndex: number;
  calmarRatio: number;
}

export interface PerformanceAttribution {
  assetClass: string;
  allocation: number;
  benchmark: number;
  portfolioReturn: number;
  allocationEffect: number;
  selectionEffect: number;
  totalContribution: number;
  sectors?: SectorAttribution[];
}

export interface SectorAttribution {
  name: string;
  weight: number;
  return: number;
  benchmark: number;
  contribution: number;
}

export interface CorrelationData {
  assets: string[];
  matrix: number[][];
  metadata: {
    period: string;
    frequency: 'daily' | 'weekly' | 'monthly';
    startDate: Date;
    endDate: Date;
  };
}

export interface HeatMapData {
  row: string;
  column: string;
  value: number;
  displayValue?: string;
}

export interface DrillDownData {
  level: number;
  category: string;
  subcategories?: DrillDownData[];
  metrics: {
    value: number;
    weight: number;
    contribution: number;
  };
}

export interface RealTimeData {
  timestamp: Date;
  portfolioValue: number;
  dayChange: number;
  dayChangePercent: number;
  volume: number;
  holdings: {
    symbol: string;
    price: number;
    change: number;
    changePercent: number;
    volume: number;
  }[];
}

export interface ExportOptions {
  format: 'png' | 'svg' | 'pdf' | 'csv' | 'xlsx';
  quality?: 'low' | 'medium' | 'high';
  dimensions?: {
    width: number;
    height: number;
  };
  includeData?: boolean;
  filename?: string;
}

export interface ChartConfiguration {
  id: string;
  type: 'line' | 'area' | 'bar' | 'scatter' | 'heatmap' | 'treemap' | 'sankey';
  title: string;
  subtitle?: string;
  xAxis: AxisConfiguration;
  yAxis: AxisConfiguration;
  legend: LegendConfiguration;
  tooltip: TooltipConfiguration;
  animation: AnimationConfiguration;
  colors: string[];
  responsive: boolean;
}

export interface AxisConfiguration {
  title: string;
  format?: string;
  scale?: 'linear' | 'log' | 'time';
  domain?: [number, number];
  tickCount?: number;
  showGrid?: boolean;
}

export interface LegendConfiguration {
  show: boolean;
  position: 'top' | 'right' | 'bottom' | 'left';
  orientation?: 'horizontal' | 'vertical';
}

export interface TooltipConfiguration {
  show: boolean;
  format?: string;
  crosshair?: boolean;
}

export interface AnimationConfiguration {
  duration: number;
  easing: string;
  delay?: number;
}

export interface AnalyticsFilter {
  dateRange: {
    start: Date;
    end: Date;
  };
  assets?: string[];
  benchmarks?: string[];
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  currency: string;
  adjustments: {
    dividends: boolean;
    splits: boolean;
    inflation: boolean;
  };
}

export interface AnalyticsState {
  portfolioMetrics: PortfolioMetrics | null;
  riskMetrics: RiskMetrics | null;
  performanceAttribution: PerformanceAttribution[] | null;
  correlationData: CorrelationData | null;
  timeSeriesData: TimeSeriesData[] | null;
  realTimeData: RealTimeData | null;
  filter: AnalyticsFilter;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export interface WebSocketMessage {
  type: 'portfolio_update' | 'market_data' | 'risk_alert' | 'performance_update';
  timestamp: Date;
  data: any;
}

export interface AnalyticsAlert {
  id: string;
  type: 'risk' | 'performance' | 'correlation' | 'drawdown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  data?: any;
}

export interface BacktestResult {
  period: {
    start: Date;
    end: Date;
  };
  initialValue: number;
  finalValue: number;
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
  trades: TradeRecord[];
  equity: TimeSeriesData[];
  drawdowns: TimeSeriesData[];
}

export interface TradeRecord {
  date: Date;
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
  price: number;
  value: number;
  commission: number;
}

export interface OptimizationResult {
  weights: { [asset: string]: number };
  expectedReturn: number;
  expectedVolatility: number;
  sharpeRatio: number;
  efficientFrontier: {
    return: number;
    volatility: number;
    sharpeRatio: number;
  }[];
}

export interface StressTestScenario {
  name: string;
  description: string;
  shocks: { [asset: string]: number };
  result: {
    portfolioValue: number;
    loss: number;
    lossPercent: number;
  };
}

export interface MonteCarloAnalysis {
  iterations: number;
  timeHorizon: number;
  confidenceIntervals: {
    percentile5: TimeSeriesData[];
    percentile25: TimeSeriesData[];
    percentile50: TimeSeriesData[];
    percentile75: TimeSeriesData[];
    percentile95: TimeSeriesData[];
  };
  finalValues: {
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
  };
  probabilityOfSuccess: number;
}