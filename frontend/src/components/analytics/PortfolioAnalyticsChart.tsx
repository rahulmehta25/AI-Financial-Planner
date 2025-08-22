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
  TimeSeriesData,
  PortfolioMetrics,
  ChartConfiguration,
  ExportOptions,
} from '@/types/analytics';
import { Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface PortfolioAnalyticsChartProps {
  id?: string;
  data: TimeSeriesData[];
  metrics?: PortfolioMetrics;
  benchmarkData?: TimeSeriesData[];
  title?: string;
  subtitle?: string;
  height?: number;
  width?: number;
  onExport?: (options: ExportOptions) => void;
  className?: string;
}

export const PortfolioAnalyticsChart: React.FC<PortfolioAnalyticsChartProps> = ({
  id = 'portfolio-analytics-chart',
  data,
  metrics,
  benchmarkData,
  title = 'Portfolio Performance Analysis',
  subtitle = 'Portfolio value over time with key metrics',
  height = 500,
  width,
  onExport,
  className = '',
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [chartType, setChartType] = useState<'line' | 'area'>('area');
  const [timeFrame, setTimeFrame] = useState<'1M' | '3M' | '6M' | '1Y' | 'ALL'>('1Y');
  const [isZoomed, setIsZoomed] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 800, height });

  // Filter data based on time frame
  const filteredData = useMemo(() => {
    if (timeFrame === 'ALL') return data;
    
    const now = new Date();
    const monthsBack = timeFrame === '1M' ? 1 : timeFrame === '3M' ? 3 : timeFrame === '6M' ? 6 : 12;
    const cutoffDate = new Date(now.getFullYear(), now.getMonth() - monthsBack, now.getDate());
    
    return data.filter(d => d.date >= cutoffDate);
  }, [data, timeFrame]);

  const filteredBenchmarkData = useMemo(() => {
    if (!benchmarkData || timeFrame === 'ALL') return benchmarkData;
    
    const now = new Date();
    const monthsBack = timeFrame === '1M' ? 1 : timeFrame === '3M' ? 3 : timeFrame === '6M' ? 6 : 12;
    const cutoffDate = new Date(now.getFullYear(), now.getMonth() - monthsBack, now.getDate());
    
    return benchmarkData.filter(d => d.date >= cutoffDate);
  }, [benchmarkData, timeFrame]);

  // Handle responsive sizing
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        setDimensions({
          width: width || Math.max(containerWidth - 40, 400),
          height
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [width, height]);

  // D3.js chart rendering
  useEffect(() => {
    if (!svgRef.current || !filteredData.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous chart

    const margin = { top: 20, right: 60, bottom: 60, left: 80 };
    const chartWidth = dimensions.width - margin.left - margin.right;
    const chartHeight = dimensions.height - margin.top - margin.bottom;

    // Create main group
    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create scales
    const xScale = d3
      .scaleTime()
      .domain(d3.extent(filteredData, d => d.date) as [Date, Date])
      .range([0, chartWidth]);

    const yExtent = d3.extent([
      ...filteredData.map(d => d.value),
      ...(filteredBenchmarkData?.map(d => d.value) || [])
    ]) as [number, number];
    
    const yPadding = (yExtent[1] - yExtent[0]) * 0.1;
    const yScale = d3
      .scaleLinear()
      .domain([yExtent[0] - yPadding, yExtent[1] + yPadding])
      .range([chartHeight, 0]);

    // Create line generator
    const line = d3
      .line<TimeSeriesData>()
      .x(d => xScale(d.date))
      .y(d => yScale(d.value))
      .curve(d3.curveMonotoneX);

    // Create area generator (for area chart)
    const area = d3
      .area<TimeSeriesData>()
      .x(d => xScale(d.date))
      .y0(chartHeight)
      .y1(d => yScale(d.value))
      .curve(d3.curveMonotoneX);

    // Add gradient definition for area chart
    if (chartType === 'area') {
      const gradient = svg
        .append('defs')
        .append('linearGradient')
        .attr('id', `${id}-gradient`)
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', 0).attr('y1', 0)
        .attr('x2', 0).attr('y2', chartHeight);

      gradient
        .append('stop')
        .attr('offset', '0%')
        .attr('stop-color', '#3b82f6')
        .attr('stop-opacity', 0.6);

      gradient
        .append('stop')
        .attr('offset', '100%')
        .attr('stop-color', '#3b82f6')
        .attr('stop-opacity', 0.1);
    }

    // Add grid lines
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(
        d3.axisBottom(xScale)
          .tickSize(-chartHeight)
          .tickFormat('' as any)
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3);

    g.append('g')
      .attr('class', 'grid')
      .call(
        d3.axisLeft(yScale)
          .tickSize(-chartWidth)
          .tickFormat('' as any)
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3);

    // Add benchmark line if available
    if (filteredBenchmarkData && filteredBenchmarkData.length > 0) {
      g.append('path')
        .datum(filteredBenchmarkData)
        .attr('class', 'benchmark-line')
        .attr('fill', 'none')
        .attr('stroke', '#64748b')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5')
        .attr('d', line);
    }

    // Add main chart (area or line)
    if (chartType === 'area') {
      g.append('path')
        .datum(filteredData)
        .attr('class', 'portfolio-area')
        .attr('fill', `url(#${id}-gradient)`)
        .attr('d', area);
    }

    g.append('path')
      .datum(filteredData)
      .attr('class', 'portfolio-line')
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 3)
      .attr('d', line);

    // Add data points
    g.selectAll('.data-point')
      .data(filteredData)
      .enter()
      .append('circle')
      .attr('class', 'data-point')
      .attr('cx', d => xScale(d.date))
      .attr('cy', d => yScale(d.value))
      .attr('r', 0)
      .attr('fill', '#3b82f6')
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 2)
      .on('mouseover', function(event, d) {
        d3.select(this).attr('r', 6);
        
        // Show tooltip
        const tooltip = g.append('g').attr('class', 'tooltip');
        const rect = tooltip.append('rect')
          .attr('fill', '#1f2937')
          .attr('stroke', '#374151')
          .attr('rx', 4);
        
        const text = tooltip.append('text')
          .attr('fill', 'white')
          .attr('font-size', '12px')
          .attr('text-anchor', 'start');
        
        text.append('tspan')
          .attr('x', 8)
          .attr('y', 16)
          .text(`Date: ${d.date.toLocaleDateString()}`);
        
        text.append('tspan')
          .attr('x', 8)
          .attr('y', 32)
          .text(`Value: $${d.value.toLocaleString()}`);
        
        const bbox = text.node()?.getBBox();
        if (bbox) {
          rect
            .attr('width', bbox.width + 16)
            .attr('height', bbox.height + 8);
        }
        
        const [mouseX, mouseY] = d3.pointer(event, g.node());
        tooltip.attr('transform', `translate(${mouseX + 10},${mouseY - 40})`);
      })
      .on('mouseout', function() {
        d3.select(this).attr('r', 0);
        g.select('.tooltip').remove();
      });

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d3.timeFormat('%b %Y') as any));

    g.append('g')
      .call(d3.axisLeft(yScale)
        .tickFormat(d => `$${(d as number).toLocaleString()}`));

    // Add axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (chartHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('Portfolio Value');

    g.append('text')
      .attr('transform', `translate(${chartWidth / 2}, ${chartHeight + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('Date');

    // Add legend
    if (filteredBenchmarkData) {
      const legend = g.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${chartWidth - 120}, 20)`);

      legend.append('line')
        .attr('x1', 0)
        .attr('x2', 15)
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 3);

      legend.append('text')
        .attr('x', 20)
        .attr('y', 4)
        .text('Portfolio')
        .style('font-size', '12px')
        .style('fill', '#374151');

      legend.append('line')
        .attr('x1', 0)
        .attr('x2', 15)
        .attr('y1', 20)
        .attr('y2', 20)
        .attr('stroke', '#64748b')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5');

      legend.append('text')
        .attr('x', 20)
        .attr('y', 24)
        .text('Benchmark')
        .style('font-size', '12px')
        .style('fill', '#374151');
    }

  }, [filteredData, filteredBenchmarkData, dimensions, chartType, id]);

  const handleExport = (format: ExportOptions['format']) => {
    if (onExport) {
      onExport({
        format,
        quality: 'high',
        dimensions,
        includeData: true,
        filename: `portfolio-analytics-${timeFrame.toLowerCase()}`
      });
    }
  };

  const handleZoom = () => {
    setIsZoomed(!isZoomed);
    // Implement zoom logic here
  };

  const handleReset = () => {
    setTimeFrame('1Y');
    setChartType('area');
    setIsZoomed(false);
  };

  return (
    <Card className={`p-6 ${className}`} id={id}>
      {/* Header */}
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
        
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2 mt-4 sm:mt-0">
          <Select value={timeFrame} onValueChange={(value: any) => setTimeFrame(value)}>
            <SelectTrigger className="w-20">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1M">1M</SelectItem>
              <SelectItem value="3M">3M</SelectItem>
              <SelectItem value="6M">6M</SelectItem>
              <SelectItem value="1Y">1Y</SelectItem>
              <SelectItem value="ALL">ALL</SelectItem>
            </SelectContent>
          </Select>

          <Select value={chartType} onValueChange={(value: any) => setChartType(value)}>
            <SelectTrigger className="w-20">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="line">Line</SelectItem>
              <SelectItem value="area">Area</SelectItem>
            </SelectContent>
          </Select>

          <Button variant="outline" size="sm" onClick={handleZoom}>
            {isZoomed ? <ZoomOut className="h-4 w-4" /> : <ZoomIn className="h-4 w-4" />}
          </Button>

          <Button variant="outline" size="sm" onClick={handleReset}>
            <RotateCcw className="h-4 w-4" />
          </Button>

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

      {/* Metrics Summary */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Return</div>
            <div className={`text-lg font-semibold ${metrics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {metrics.totalReturn >= 0 ? '+' : ''}{metrics.totalReturn.toFixed(2)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Ann. Return</div>
            <div className={`text-lg font-semibold ${metrics.annualizedReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {metrics.annualizedReturn >= 0 ? '+' : ''}{metrics.annualizedReturn.toFixed(2)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Volatility</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metrics.volatility.toFixed(2)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metrics.sharpeRatio.toFixed(2)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</div>
            <div className="text-lg font-semibold text-red-600">
              -{metrics.maxDrawdown.toFixed(2)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-600 dark:text-gray-400">Beta</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metrics.beta.toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* Chart Container */}
      <div ref={containerRef} className="w-full">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="border rounded-lg bg-white dark:bg-gray-900"
        />
      </div>
    </Card>
  );
};

export default PortfolioAnalyticsChart;