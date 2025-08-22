'use client';

import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  RiskMetrics,
  PortfolioMetrics,
  TimeSeriesData,
  ExportOptions,
} from '@/types/analytics';
import { 
  Download, 
  AlertTriangle, 
  Shield, 
  TrendingDown,
  Target,
  Activity,
  Info
} from 'lucide-react';

interface RiskMetricsDashboardProps {
  id?: string;
  riskMetrics: RiskMetrics;
  portfolioMetrics: PortfolioMetrics;
  returns?: TimeSeriesData[];
  benchmarkReturns?: TimeSeriesData[];
  title?: string;
  subtitle?: string;
  onExport?: (options: ExportOptions) => void;
  className?: string;
}

export const RiskMetricsDashboard: React.FC<RiskMetricsDashboardProps> = ({
  id = 'risk-metrics-dashboard',
  riskMetrics,
  portfolioMetrics,
  returns = [],
  benchmarkReturns = [],
  title = 'Risk Metrics Dashboard',
  subtitle = 'Comprehensive risk analysis with VaR, Sharpe, Sortino and other risk measures',
  onExport,
  className = '',
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const distributionRef = useRef<SVGSVGElement>(null);
  const [selectedMetric, setSelectedMetric] = useState<'var' | 'drawdown' | 'ratios'>('var');
  const [confidenceLevel, setConfidenceLevel] = useState<95 | 99>(95);

  // Calculate additional risk metrics
  const additionalMetrics = useMemo(() => {
    if (!returns.length) return null;

    const returnValues = returns.map(r => r.value);
    const mean = returnValues.reduce((sum, val) => sum + val, 0) / returnValues.length;
    const variance = returnValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (returnValues.length - 1);
    const standardDeviation = Math.sqrt(variance);
    
    // Calculate skewness
    const skewness = returnValues.reduce((sum, val) => sum + Math.pow((val - mean) / standardDeviation, 3), 0) / returnValues.length;
    
    // Calculate kurtosis
    const kurtosis = returnValues.reduce((sum, val) => sum + Math.pow((val - mean) / standardDeviation, 4), 0) / returnValues.length - 3;
    
    // Calculate downside returns for Sortino ratio calculation
    const downsideReturns = returnValues.filter(ret => ret < 0);
    const downsideVariance = downsideReturns.length > 0 
      ? downsideReturns.reduce((sum, val) => sum + Math.pow(val, 2), 0) / downsideReturns.length
      : 0;
    const downsideDeviation = Math.sqrt(downsideVariance);

    return {
      mean: mean * 100,
      standardDeviation: standardDeviation * 100,
      skewness,
      kurtosis,
      downsideDeviation: downsideDeviation * 100,
      positiveReturns: returnValues.filter(ret => ret > 0).length,
      negativeReturns: returnValues.filter(ret => ret < 0).length,
      winRate: (returnValues.filter(ret => ret > 0).length / returnValues.length) * 100
    };
  }, [returns]);

  // Render VaR visualization
  const renderVaRChart = () => {
    if (!distributionRef.current || !returns.length) return;

    const svg = d3.select(distributionRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 40, bottom: 40, left: 60 };
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Prepare return data
    const returnValues = returns.map(r => r.value);
    const sortedReturns = [...returnValues].sort((a, b) => a - b);
    
    // Calculate VaR thresholds
    const var95Index = Math.floor(sortedReturns.length * 0.05);
    const var99Index = Math.floor(sortedReturns.length * 0.01);
    const var95Value = sortedReturns[var95Index];
    const var99Value = sortedReturns[var99Index];

    // Create histogram
    const histogram = d3.histogram()
      .domain(d3.extent(returnValues) as [number, number])
      .thresholds(30);

    const bins = histogram(returnValues);
    
    const xScale = d3.scaleLinear()
      .domain(d3.extent(returnValues) as [number, number])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(bins, d => d.length) || 0])
      .range([height, 0]);

    // Add bars
    g.selectAll('.bar')
      .data(bins)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => xScale(d.x0 || 0))
      .attr('width', d => Math.max(0, xScale(d.x1 || 0) - xScale(d.x0 || 0) - 1))
      .attr('y', d => yScale(d.length))
      .attr('height', d => height - yScale(d.length))
      .attr('fill', d => {
        const midpoint = ((d.x0 || 0) + (d.x1 || 0)) / 2;
        if (midpoint < var99Value) return '#dc2626'; // Red for extreme losses
        if (midpoint < var95Value) return '#f59e0b'; // Orange for VaR range
        return '#3b82f6'; // Blue for normal range
      })
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 0.5);

    // Add VaR lines
    [
      { value: var95Value, label: '95% VaR', color: '#f59e0b' },
      { value: var99Value, label: '99% VaR', color: '#dc2626' }
    ].forEach(({ value, label, color }) => {
      g.append('line')
        .attr('x1', xScale(value))
        .attr('x2', xScale(value))
        .attr('y1', 0)
        .attr('y2', height)
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5');

      g.append('text')
        .attr('x', xScale(value))
        .attr('y', -5)
        .attr('text-anchor', 'middle')
        .style('font-size', '10px')
        .style('fill', color)
        .style('font-weight', 'bold')
        .text(label);
    });

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d => `${((d as number) * 100).toFixed(1)}%`));

    g.append('g')
      .call(d3.axisLeft(yScale));

    // Add labels
    g.append('text')
      .attr('x', width / 2)
      .attr('y', height + 35)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('Daily Returns');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('Frequency');
  };

  useEffect(() => {
    if (selectedMetric === 'var') {
      renderVaRChart();
    }
  }, [selectedMetric, returns, confidenceLevel]);

  const handleExport = (format: ExportOptions['format']) => {
    if (onExport) {
      onExport({
        format,
        quality: 'high',
        includeData: true,
        filename: `risk-metrics-${selectedMetric}`
      });
    }
  };

  const getRiskLevel = (sharpeRatio: number) => {
    if (sharpeRatio > 2) return { level: 'Excellent', color: 'text-green-600', icon: Shield };
    if (sharpeRatio > 1) return { level: 'Good', color: 'text-blue-600', icon: Target };
    if (sharpeRatio > 0.5) return { level: 'Acceptable', color: 'text-yellow-600', icon: Activity };
    return { level: 'Poor', color: 'text-red-600', icon: AlertTriangle };
  };

  const riskLevel = getRiskLevel(portfolioMetrics.sharpeRatio);
  const RiskIcon = riskLevel.icon;

  return (
    <div className={`space-y-6 ${className}`} id={id}>
      {/* Header */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {title}
            </h3>
            {subtitle && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-2 mt-4 sm:mt-0">
            <Select value={selectedMetric} onValueChange={(value: any) => setSelectedMetric(value)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="var">VaR Analysis</SelectItem>
                <SelectItem value="drawdown">Drawdown</SelectItem>
                <SelectItem value="ratios">Risk Ratios</SelectItem>
              </SelectContent>
            </Select>

            {onExport && (
              <Select onValueChange={(value: any) => handleExport(value)}>
                <SelectTrigger className="w-12">
                  <Download className="h-4 w-4" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="png">PNG</SelectItem>
                  <SelectItem value="svg">SVG</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        {/* Overall Risk Assessment */}
        <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <RiskIcon className={`h-6 w-6 ${riskLevel.color}`} />
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Overall Risk Assessment</div>
            <div className={`text-lg font-semibold ${riskLevel.color}`}>
              {riskLevel.level} (Sharpe Ratio: {portfolioMetrics.sharpeRatio.toFixed(2)})
            </div>
          </div>
        </div>
      </Card>

      {/* Key Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Value at Risk */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Value at Risk (95%)</div>
              <div className="text-2xl font-bold text-red-600">
                {riskMetrics.var95.toFixed(2)}%
              </div>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Expected loss once every 20 days
          </div>
        </Card>

        {/* Conditional VaR */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Conditional VaR (95%)</div>
              <div className="text-2xl font-bold text-red-700">
                {riskMetrics.cvar95.toFixed(2)}%
              </div>
            </div>
            <TrendingDown className="h-8 w-8 text-red-700" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Average loss when VaR is exceeded
          </div>
        </Card>

        {/* Maximum Drawdown */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</div>
              <div className="text-2xl font-bold text-red-600">
                -{riskMetrics.maxDrawdown.toFixed(2)}%
              </div>
            </div>
            <TrendingDown className="h-8 w-8 text-red-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Largest peak-to-trough decline
          </div>
        </Card>

        {/* Sortino Ratio */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Sortino Ratio</div>
              <div className={`text-2xl font-bold ${portfolioMetrics.sortinoRatio > 1 ? 'text-green-600' : 'text-yellow-600'}`}>
                {portfolioMetrics.sortinoRatio.toFixed(2)}
              </div>
            </div>
            <Target className="h-8 w-8 text-blue-600" />
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Risk-adjusted return vs downside
          </div>
        </Card>
      </div>

      {/* Detailed Analysis */}
      {selectedMetric === 'var' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100">
              Value at Risk Distribution
            </h4>
            <Select value={confidenceLevel.toString()} onValueChange={(value: any) => setConfidenceLevel(Number(value))}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="95">95%</SelectItem>
                <SelectItem value="99">99%</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <svg
                ref={distributionRef}
                width={400}
                height={300}
                className="border rounded-lg bg-white dark:bg-gray-900"
              />
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                  <div className="text-sm text-orange-800 dark:text-orange-200">95% VaR</div>
                  <div className="text-lg font-bold text-orange-600">
                    {riskMetrics.var95.toFixed(2)}%
                  </div>
                </div>
                <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div className="text-sm text-red-800 dark:text-red-200">99% VaR</div>
                  <div className="text-lg font-bold text-red-600">
                    {riskMetrics.var99.toFixed(2)}%
                  </div>
                </div>
              </div>
              
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-blue-800 dark:text-blue-200">
                    <p className="font-medium mb-2">VaR Interpretation:</p>
                    <ul className="space-y-1 text-xs">
                      <li>• 95% VaR: Expected loss once every 20 trading days</li>
                      <li>• 99% VaR: Expected loss once every 100 trading days</li>
                      <li>• CVaR shows average loss when VaR threshold is exceeded</li>
                      <li>• Lower (more negative) values indicate higher risk</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Risk Ratios Analysis */}
      {selectedMetric === 'ratios' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Risk-Adjusted Returns
            </h4>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</span>
                <span className={`font-semibold ${portfolioMetrics.sharpeRatio > 1 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {portfolioMetrics.sharpeRatio.toFixed(3)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Sortino Ratio</span>
                <span className={`font-semibold ${portfolioMetrics.sortinoRatio > 1 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {portfolioMetrics.sortinoRatio.toFixed(3)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Calmar Ratio</span>
                <span className={`font-semibold ${riskMetrics.calmarRatio > 0.5 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {riskMetrics.calmarRatio.toFixed(3)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Information Ratio</span>
                <span className={`font-semibold ${portfolioMetrics.informationRatio > 0.5 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {portfolioMetrics.informationRatio.toFixed(3)}
                </span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Risk Measures
            </h4>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Volatility</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {portfolioMetrics.volatility.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Downside Deviation</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {riskMetrics.downsideDeviation.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Tracking Error</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {portfolioMetrics.trackingError.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Ulcer Index</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {riskMetrics.ulcerIndex.toFixed(2)}
                </span>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Additional Statistics */}
      {additionalMetrics && (
        <Card className="p-6">
          <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Return Distribution Statistics
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-600 dark:text-gray-400">Mean Return</div>
              <div className={`text-lg font-semibold ${additionalMetrics.mean >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {additionalMetrics.mean.toFixed(3)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 dark:text-gray-400">Std Deviation</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {additionalMetrics.standardDeviation.toFixed(3)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 dark:text-gray-400">Skewness</div>
              <div className={`text-lg font-semibold ${Math.abs(additionalMetrics.skewness) < 0.5 ? 'text-green-600' : 'text-yellow-600'}`}>
                {additionalMetrics.skewness.toFixed(3)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 dark:text-gray-400">Kurtosis</div>
              <div className={`text-lg font-semibold ${Math.abs(additionalMetrics.kurtosis) < 1 ? 'text-green-600' : 'text-yellow-600'}`}>
                {additionalMetrics.kurtosis.toFixed(3)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 dark:text-gray-400">Win Rate</div>
              <div className={`text-lg font-semibold ${additionalMetrics.winRate > 50 ? 'text-green-600' : 'text-red-600'}`}>
                {additionalMetrics.winRate.toFixed(1)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Periods</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {returns.length}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default RiskMetricsDashboard;