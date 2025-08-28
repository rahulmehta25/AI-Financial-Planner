import React, { useMemo, lazy, Suspense } from 'react';
// Dynamic import for plotly to avoid build issues
const Plot = lazy(() => import('react-plotly.js'));
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUpIcon, BarChart3Icon, PieChartIcon, ActivityIcon } from 'lucide-react';

export interface SimulationResult {
  finalValues: number[];
  paths: number[][];
  timestamps: number[];
  riskMetrics: {
    'Value at Risk (95%)': number;
    'Conditional VaR (95%)': number;
    'Maximum Drawdown': number;
    'Sharpe Ratio': number;
    'Skewness': number;
    'Kurtosis': number;
  };
  successRate?: number;
  confidenceIntervals: {
    '10%': number[];
    '25%': number[];
    '50%': number[];
    '75%': number[];
    '90%': number[];
  };
}

interface ProbabilityChartProps {
  results: SimulationResult | null;
  targetAmount?: number;
  className?: string;
}

const ProbabilityChart: React.FC<ProbabilityChartProps> = ({
  results,
  targetAmount,
  className = ""
}) => {
  const histogramData = useMemo(() => {
    if (!results) return null;

    return [{
      x: results.finalValues,
      type: 'histogram' as const,
      nbinsx: 50,
      name: 'Final Portfolio Values',
      marker: {
        color: 'rgba(99, 102, 241, 0.7)',
        line: {
          color: 'rgb(99, 102, 241)',
          width: 1
        }
      },
      hovertemplate: 'Value: $%{x:,.0f}<br>Count: %{y}<extra></extra>'
    }];
  }, [results]);

  const densityData = useMemo(() => {
    if (!results) return null;

    const values = results.finalValues.sort((a, b) => a - b);
    const n = values.length;
    const bandwidth = (Math.max(...values) - Math.min(...values)) / 50;
    
    // Simple kernel density estimation
    const x: number[] = [];
    const y: number[] = [];
    const min = Math.min(...values);
    const max = Math.max(...values);
    
    for (let i = min; i <= max; i += bandwidth) {
      x.push(i);
      let density = 0;
      for (const value of values) {
        density += Math.exp(-0.5 * Math.pow((i - value) / bandwidth, 2));
      }
      y.push(density / (n * bandwidth * Math.sqrt(2 * Math.PI)));
    }

    return [{
      x,
      y,
      type: 'scatter' as const,
      mode: 'lines' as const,
      fill: 'tonexty',
      name: 'Probability Density',
      line: {
        color: 'rgb(99, 102, 241)',
        width: 2
      },
      fillcolor: 'rgba(99, 102, 241, 0.2)',
      hovertemplate: 'Value: $%{x:,.0f}<br>Density: %{y:.6f}<extra></extra>'
    }];
  }, [results]);

  const cumulativeData = useMemo(() => {
    if (!results) return null;

    const sortedValues = [...results.finalValues].sort((a, b) => a - b);
    const cumulative = sortedValues.map((_, index) => (index + 1) / sortedValues.length);

    return [{
      x: sortedValues,
      y: cumulative,
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: 'Cumulative Distribution',
      line: {
        color: 'rgb(16, 185, 129)',
        width: 3
      },
      hovertemplate: 'Value: $%{x:,.0f}<br>Probability: %{y:.1%}<extra></extra>'
    }];
  }, [results]);

  const riskMetricsData = useMemo(() => {
    if (!results) return null;

    const percentiles = [5, 10, 25, 50, 75, 90, 95].map(p => ({
      percentile: p,
      value: results.finalValues[Math.floor((p / 100) * results.finalValues.length)]
    }));

    return [{
      x: percentiles.map(p => `${p.percentile}%`),
      y: percentiles.map(p => p.value),
      type: 'bar' as const,
      name: 'Percentile Values',
      marker: {
        color: percentiles.map(p => 
          p.percentile <= 25 ? 'rgba(239, 68, 68, 0.7)' :
          p.percentile <= 75 ? 'rgba(245, 158, 11, 0.7)' : 
          'rgba(34, 197, 94, 0.7)'
        ),
        line: {
          color: 'rgba(0, 0, 0, 0.2)',
          width: 1
        }
      },
      hovertemplate: '%{x}: $%{y:,.0f}<extra></extra>'
    }];
  }, [results]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (!results) {
    return (
      <Card className={`w-full ${className}`} id="probability-chart-placeholder">
        <CardHeader id="placeholder-header">
          <CardTitle className="flex items-center gap-2" id="placeholder-title">
            <BarChart3Icon className="h-5 w-5" />
            Probability Analysis
          </CardTitle>
          <CardDescription id="placeholder-description">
            Run a simulation to view probability distributions and risk metrics
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64 text-muted-foreground" id="placeholder-content">
          <div className="text-center" id="placeholder-message">
            <ActivityIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No simulation results available</p>
            <p className="text-sm">Configure parameters and run simulation</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const plotLayout = {
    autosize: true,
    margin: { l: 50, r: 50, b: 50, t: 30 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#374151', size: 12 },
    showlegend: true,
    legend: { orientation: 'h', x: 0, y: -0.2 }
  };

  const plotConfig = {
    displayModeBar: true,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
    responsive: true
  };

  return (
    <Card className={`w-full ${className}`} id="probability-chart-card">
      <CardHeader id="probability-chart-header">
        <div className="flex items-center justify-between" id="chart-header-content">
          <div id="chart-title-section">
            <CardTitle className="flex items-center gap-2" id="chart-title">
              <BarChart3Icon className="h-5 w-5" />
              Probability Analysis
            </CardTitle>
            <CardDescription id="chart-description">
              Statistical distribution of simulation outcomes and risk metrics
            </CardDescription>
          </div>
          <div className="flex gap-2" id="summary-badges">
            <Badge variant="outline" className="flex items-center gap-1" id="simulations-badge">
              <PieChartIcon className="h-3 w-3" />
              {results.finalValues.length.toLocaleString()} simulations
            </Badge>
            {results.successRate !== undefined && (
              <Badge 
                variant={results.successRate >= 0.8 ? "default" : results.successRate >= 0.6 ? "secondary" : "destructive"} 
                id="success-rate-badge"
              >
                {formatPercent(results.successRate)} success rate
              </Badge>
            )}
          </div>
        </div>

        {/* Risk Metrics Summary */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 mt-4" id="risk-metrics-summary">
          {Object.entries(results.riskMetrics).map(([key, value]) => (
            <div key={key} className="text-center" id={`metric-${key.replace(/\s+/g, '-').toLowerCase()}`}>
              <div className="text-xs text-muted-foreground">{key}</div>
              <div className="text-sm font-semibold">
                {key.includes('Ratio') || key.includes('Skewness') || key.includes('Kurtosis') 
                  ? value.toFixed(2) 
                  : formatCurrency(value)
                }
              </div>
            </div>
          ))}
        </div>
      </CardHeader>
      
      <CardContent id="probability-chart-content">
        <Tabs defaultValue="histogram" className="w-full" id="probability-tabs">
          <TabsList className="grid w-full grid-cols-4" id="probability-tabs-list">
            <TabsTrigger value="histogram" id="histogram-tab">Distribution</TabsTrigger>
            <TabsTrigger value="density" id="density-tab">Density</TabsTrigger>
            <TabsTrigger value="cumulative" id="cumulative-tab">Cumulative</TabsTrigger>
            <TabsTrigger value="percentiles" id="percentiles-tab">Percentiles</TabsTrigger>
          </TabsList>
          
          <TabsContent value="histogram" id="histogram-content">
            <div className="h-96" id="histogram-chart">
              <Suspense fallback={<div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
                <Plot
                data={histogramData || []}
                layout={{
                  ...plotLayout,
                  title: 'Final Portfolio Value Distribution',
                  xaxis: { title: 'Portfolio Value ($)', tickformat: ',.0f' },
                  yaxis: { title: 'Frequency' },
                  shapes: targetAmount ? [{
                    type: 'line',
                    x0: targetAmount,
                    x1: targetAmount,
                    y0: 0,
                    y1: 1,
                    yref: 'paper',
                    line: { color: 'red', width: 2, dash: 'dash' }
                  }] : []
                }}
                config={plotConfig}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
              </Suspense>
            </div>
          </TabsContent>
          
          <TabsContent value="density" id="density-content">
            <div className="h-96" id="density-chart">
              <Suspense fallback={<div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
                <Plot
                data={densityData || []}
                layout={{
                  ...plotLayout,
                  title: 'Probability Density Function',
                  xaxis: { title: 'Portfolio Value ($)', tickformat: ',.0f' },
                  yaxis: { title: 'Probability Density' },
                  shapes: targetAmount ? [{
                    type: 'line',
                    x0: targetAmount,
                    x1: targetAmount,
                    y0: 0,
                    y1: 1,
                    yref: 'paper',
                    line: { color: 'red', width: 2, dash: 'dash' }
                  }] : []
                }}
                config={plotConfig}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
              </Suspense>
            </div>
          </TabsContent>
          
          <TabsContent value="cumulative" id="cumulative-content">
            <div className="h-96" id="cumulative-chart">
              <Suspense fallback={<div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
                <Plot
                data={cumulativeData || []}
                layout={{
                  ...plotLayout,
                  title: 'Cumulative Distribution Function',
                  xaxis: { title: 'Portfolio Value ($)', tickformat: ',.0f' },
                  yaxis: { title: 'Probability', tickformat: '.0%' },
                  shapes: targetAmount ? [{
                    type: 'line',
                    x0: targetAmount,
                    x1: targetAmount,
                    y0: 0,
                    y1: 1,
                    yref: 'paper',
                    line: { color: 'red', width: 2, dash: 'dash' }
                  }] : []
                }}
                config={plotConfig}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
              </Suspense>
            </div>
          </TabsContent>
          
          <TabsContent value="percentiles" id="percentiles-content">
            <div className="h-96" id="percentiles-chart">
              <Suspense fallback={<div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
                <Plot
                data={riskMetricsData || []}
                layout={{
                  ...plotLayout,
                  title: 'Value at Risk Percentiles',
                  xaxis: { title: 'Percentile' },
                  yaxis: { title: 'Portfolio Value ($)', tickformat: ',.0f' },
                  shapes: targetAmount ? [{
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    xref: 'paper',
                    y0: targetAmount,
                    y1: targetAmount,
                    line: { color: 'red', width: 2, dash: 'dash' }
                  }] : []
                }}
                config={plotConfig}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
              />
              </Suspense>
            </div>
          </TabsContent>
        </Tabs>

        {targetAmount && results.successRate !== undefined && (
          <div className="mt-4 p-4 bg-muted/50 rounded-lg" id="target-analysis">
            <div className="flex items-center gap-2 mb-2" id="target-header">
              <TrendingUpIcon className="h-4 w-4" />
              <span className="font-medium">Target Analysis</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm" id="target-metrics">
              <div id="target-amount-display">
                <span className="text-muted-foreground">Target Amount:</span>
                <div className="font-semibold">{formatCurrency(targetAmount)}</div>
              </div>
              <div id="success-probability">
                <span className="text-muted-foreground">Success Probability:</span>
                <div className={`font-semibold ${results.successRate >= 0.8 ? 'text-green-600' : results.successRate >= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {formatPercent(results.successRate)}
                </div>
              </div>
              <div id="shortfall-risk">
                <span className="text-muted-foreground">Shortfall Risk:</span>
                <div className={`font-semibold ${results.successRate >= 0.8 ? 'text-green-600' : results.successRate >= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {formatPercent(1 - results.successRate)}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ProbabilityChart;