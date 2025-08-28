import React, { useMemo, lazy, Suspense } from 'react';
// Dynamic import for Three.js visualization to avoid build issues
const ThreeVisualization = lazy(() => import('./ThreeVisualization'));
// Dynamic import for plotly to avoid build issues
const Plot = lazy(() => import('react-plotly.js'));
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  TrendingUpIcon, 
  DownloadIcon, 
  BarChart3Icon, 
  Activity,
  Target,
  Shield,
  DollarSign,
  Percent,
  ChevronUp,
  ChevronDown,
  Minus
} from 'lucide-react';
import { SimulationResult } from './ProbabilityChart';

interface SimulationResultsProps {
  results: SimulationResult | null;
  targetAmount?: number;
  onExportResults?: () => void;
  className?: string;
}

const SimulationResults: React.FC<SimulationResultsProps> = ({
  results,
  targetAmount,
  onExportResults,
  className = ""
}) => {


  const pathsData = useMemo(() => {
    if (!results) return [];

    // Show a sample of paths for performance
    const pathsToShow = Math.min(results.paths.length, 50);
    const pathStep = Math.floor(results.paths.length / pathsToShow);
    
    return Array.from({ length: pathsToShow }, (_, i) => {
      const pathIndex = i * pathStep;
      const path = results.paths[pathIndex];
      const finalValue = path[path.length - 1];
      const performance = (finalValue - path[0]) / path[0];
      
      return {
        x: results.timestamps,
        y: path,
        type: 'scatter' as const,
        mode: 'lines' as const,
        line: {
          color: performance > 0 ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)',
          width: 1
        },
        name: `Path ${pathIndex + 1}`,
        showlegend: false,
        hovertemplate: 'Time: %{x}<br>Value: $%{y:,.0f}<extra></extra>'
      };
    });
  }, [results]);

  const confidenceData = useMemo(() => {
    if (!results?.confidenceIntervals) return [];

    return Object.entries(results.confidenceIntervals).map(([percentile, values]) => ({
      x: results.timestamps,
      y: values,
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: `${percentile} Confidence`,
      line: {
        color: percentile === '50%' ? 'rgb(99, 102, 241)' : 'rgba(99, 102, 241, 0.5)',
        width: percentile === '50%' ? 3 : 2
      },
      hovertemplate: `${percentile}: $%{y:,.0f}<extra></extra>`
    }));
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

  const getPerformanceIcon = (value: number) => {
    if (value > 0.05) return <ChevronUp className="h-4 w-4 text-green-500" />;
    if (value < -0.05) return <ChevronDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  if (!results) {
    return (
      <Card className={`w-full ${className}`} id="simulation-results-placeholder">
        <CardHeader id="results-placeholder-header">
          <CardTitle className="flex items-center gap-2" id="results-placeholder-title">
            <BarChart3Icon className="h-5 w-5" />
            Simulation Results
          </CardTitle>
          <CardDescription id="results-placeholder-description">
            Detailed analysis and visualization of Monte Carlo simulation outcomes
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64 text-muted-foreground" id="results-placeholder-content">
          <div className="text-center" id="results-placeholder-message">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No simulation results available</p>
            <p className="text-sm">Run a simulation to see detailed analysis</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const mean = results.finalValues.reduce((a, b) => a + b, 0) / results.finalValues.length;
  const median = [...results.finalValues].sort((a, b) => a - b)[Math.floor(results.finalValues.length / 2)];
  const std = Math.sqrt(results.finalValues.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / results.finalValues.length);

  const plotLayout = {
    autosize: true,
    margin: { l: 60, r: 50, b: 50, t: 30 },
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
    <Card className={`w-full ${className}`} id="simulation-results-card">
      <CardHeader id="simulation-results-header">
        <div className="flex items-center justify-between" id="results-header-content">
          <div id="results-title-section">
            <CardTitle className="flex items-center gap-2" id="results-title">
              <BarChart3Icon className="h-5 w-5" />
              Simulation Results
            </CardTitle>
            <CardDescription id="results-description">
              Comprehensive analysis of {results.finalValues.length.toLocaleString()} simulation paths
            </CardDescription>
          </div>
          <div className="flex gap-2" id="results-actions">
            {onExportResults && (
              <Button variant="outline" onClick={onExportResults} id="export-results-button">
                <DownloadIcon className="h-4 w-4 mr-2" />
                Export
              </Button>
            )}
          </div>
        </div>

        {/* Key Metrics Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4" id="key-metrics-grid">
          <Card className="p-4" id="mean-value-card">
            <div className="flex items-center gap-2" id="mean-value-header">
              <DollarSign className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">Mean Value</span>
            </div>
            <div className="text-2xl font-bold mt-2" id="mean-value">{formatCurrency(mean)}</div>
            <div className="text-xs text-muted-foreground" id="mean-vs-median">
              Median: {formatCurrency(median)}
            </div>
          </Card>

          <Card className="p-4" id="volatility-card">
            <div className="flex items-center gap-2" id="volatility-header">
              <Activity className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-medium">Volatility</span>
            </div>
            <div className="text-2xl font-bold mt-2" id="volatility-value">{formatCurrency(std)}</div>
            <div className="text-xs text-muted-foreground" id="volatility-coefficient">
              CV: {((std / mean) * 100).toFixed(1)}%
            </div>
          </Card>

          <Card className="p-4" id="risk-metrics-card">
            <div className="flex items-center gap-2" id="risk-metrics-header">
              <Shield className="h-4 w-4 text-red-500" />
              <span className="text-sm font-medium">VaR (95%)</span>
            </div>
            <div className="text-2xl font-bold mt-2" id="var-value">
              {formatCurrency(results.riskMetrics['Value at Risk (95%)'])}
            </div>
            <div className="text-xs text-muted-foreground" id="cvar-value">
              CVaR: {formatCurrency(results.riskMetrics['Conditional VaR (95%)'])}
            </div>
          </Card>

          {results.successRate !== undefined && (
            <Card className="p-4" id="success-rate-card">
              <div className="flex items-center gap-2" id="success-rate-header">
                <Target className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium">Success Rate</span>
              </div>
              <div className="text-2xl font-bold mt-2" id="success-rate-value">
                {formatPercent(results.successRate)}
              </div>
              <Progress value={results.successRate * 100} className="mt-2" id="success-rate-progress" />
            </Card>
          )}
        </div>
      </CardHeader>

      <CardContent id="simulation-results-content">
        <Tabs defaultValue="3d" className="w-full" id="results-tabs">
          <TabsList className="grid w-full grid-cols-3" id="results-tabs-list">
            <TabsTrigger value="3d" id="3d-tab">3D Visualization</TabsTrigger>
            <TabsTrigger value="paths" id="paths-tab">Simulation Paths</TabsTrigger>
            <TabsTrigger value="confidence" id="confidence-tab">Confidence Bands</TabsTrigger>
          </TabsList>

          <TabsContent value="3d" id="3d-tab-content">
            <div className="space-y-4" id="3d-visualization-section">
              <div className="flex items-center gap-2" id="3d-title">
                <TrendingUpIcon className="h-5 w-5" />
                <h3 className="text-lg font-semibold">3D Portfolio Evolution</h3>
              </div>
              <Suspense fallback={<div className="w-full h-96 border rounded-lg bg-gray-50 flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
                <ThreeVisualization results={results} />
              </Suspense>
              <div className="text-sm text-muted-foreground text-center" id="3d-description">
                Interactive 3D visualization showing {Math.min(results.paths.length, 100)} simulation paths.
                The scene rotates automatically to provide different perspectives.
              </div>
            </div>
          </TabsContent>

          <TabsContent value="paths" id="paths-tab-content">
            <div className="space-y-4" id="paths-section">
              <div className="flex items-center justify-between" id="paths-header">
                <div className="flex items-center gap-2" id="paths-title">
                  <Activity className="h-5 w-5" />
                  <h3 className="text-lg font-semibold">Sample Simulation Paths</h3>
                </div>
                <Badge variant="outline" id="paths-count">
                  Showing {Math.min(results.paths.length, 50)} of {results.paths.length.toLocaleString()} paths
                </Badge>
              </div>
              <div className="h-96" id="paths-chart">
                <Suspense fallback={<div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
                  <Plot
                    data={pathsData}
                    layout={{
                    ...plotLayout,
                    title: 'Portfolio Value Evolution Over Time',
                    xaxis: { title: 'Time Period' },
                    yaxis: { title: 'Portfolio Value ($)', tickformat: ',.0f' },
                    hovermode: 'closest'
                  }}
                  config={plotConfig}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%' }}
                />
                </Suspense>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="confidence" id="confidence-tab-content">
            <div className="space-y-4" id="confidence-section">
              <div className="flex items-center gap-2" id="confidence-title">
                <Percent className="h-5 w-5" />
                <h3 className="text-lg font-semibold">Confidence Intervals</h3>
              </div>
              <div className="h-96" id="confidence-chart">
                <Suspense fallback={<div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
                  <Plot
                    data={confidenceData}
                    layout={{
                    ...plotLayout,
                    title: 'Portfolio Value Confidence Intervals',
                    xaxis: { title: 'Time Period' },
                    yaxis: { title: 'Portfolio Value ($)', tickformat: ',.0f' },
                    hovermode: 'x unified'
                  }}
                  config={plotConfig}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '100%' }}
                />
                </Suspense>
              </div>
              <div className="text-sm text-muted-foreground" id="confidence-description">
                Confidence intervals show the range of outcomes at different probability levels.
                The 50% line represents the median outcome.
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <Separator className="my-6" id="results-separator" />

        {/* Detailed Risk Metrics */}
        <div className="space-y-4" id="detailed-risk-metrics">
          <h3 className="text-lg font-semibold flex items-center gap-2" id="risk-metrics-title">
            <Shield className="h-5 w-5" />
            Detailed Risk Metrics
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6" id="risk-metrics-grid">
            {Object.entries(results.riskMetrics).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg" id={`metric-detail-${key.replace(/\s+/g, '-').toLowerCase()}`}>
                <div id={`metric-label-${key.replace(/\s+/g, '-').toLowerCase()}`}>
                  <div className="font-medium">{key}</div>
                  <div className="text-sm text-muted-foreground">
                    {key === 'Sharpe Ratio' && 'Risk-adjusted return measure'}
                    {key === 'Maximum Drawdown' && 'Largest peak-to-trough decline'}
                    {key === 'Skewness' && 'Distribution asymmetry'}
                    {key === 'Kurtosis' && 'Tail risk measure'}
                    {key.includes('VaR') && 'Value at risk quantile'}
                  </div>
                </div>
                <div className="flex items-center gap-2" id={`metric-value-${key.replace(/\s+/g, '-').toLowerCase()}`}>
                  {key === 'Sharpe Ratio' && getPerformanceIcon(value)}
                  <span className="font-semibold">
                    {key.includes('Ratio') || key.includes('Skewness') || key.includes('Kurtosis') 
                      ? value.toFixed(2) 
                      : formatCurrency(value)
                    }
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SimulationResults;