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
  PerformanceAttribution,
  SectorAttribution,
  DrillDownData,
  ExportOptions,
} from '@/types/analytics';
import { 
  Download, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown
} from 'lucide-react';

interface PerformanceAttributionChartProps {
  id?: string;
  data: PerformanceAttribution[];
  title?: string;
  subtitle?: string;
  height?: number;
  width?: number;
  onExport?: (options: ExportOptions) => void;
  onDrillDown?: (item: PerformanceAttribution) => void;
  className?: string;
}

export const PerformanceAttributionChart: React.FC<PerformanceAttributionChartProps> = ({
  id = 'performance-attribution-chart',
  data,
  title = 'Performance Attribution Analysis',
  subtitle = 'Breakdown of portfolio performance by asset class and selection effects',
  height = 600,
  width,
  onExport,
  onDrillDown,
  className = '',
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewType, setViewType] = useState<'waterfall' | 'bar' | 'tree'>('waterfall');
  const [sortBy, setSortBy] = useState<'contribution' | 'allocation' | 'selection'>('contribution');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [dimensions, setDimensions] = useState({ width: 800, height });

  // Sort and prepare data
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      switch (sortBy) {
        case 'allocation':
          return Math.abs(b.allocationEffect) - Math.abs(a.allocationEffect);
        case 'selection':
          return Math.abs(b.selectionEffect) - Math.abs(a.selectionEffect);
        default:
          return Math.abs(b.totalContribution) - Math.abs(a.totalContribution);
      }
    });
  }, [data, sortBy]);

  // Handle responsive sizing
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        setDimensions({
          width: width || Math.max(containerWidth - 40, 600),
          height
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [width, height]);

  // Render waterfall chart
  const renderWaterfallChart = () => {
    if (!svgRef.current || !sortedData.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 40, right: 60, bottom: 80, left: 100 };
    const chartWidth = dimensions.width - margin.left - margin.right;
    const chartHeight = dimensions.height - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Calculate cumulative values for waterfall
    let cumulative = 0;
    const waterfallData = sortedData.map((d, i) => {
      const start = cumulative;
      cumulative += d.totalContribution;
      return {
        ...d,
        start,
        end: cumulative,
        height: Math.abs(d.totalContribution),
        isPositive: d.totalContribution >= 0
      };
    });

    // Add starting point
    const allData = [
      { assetClass: 'Start', start: 0, end: 0, height: 0, isPositive: true, totalContribution: 0 },
      ...waterfallData,
      { assetClass: 'Total', start: 0, end: cumulative, height: Math.abs(cumulative), isPositive: cumulative >= 0, totalContribution: cumulative }
    ];

    // Scales
    const xScale = d3
      .scaleBand()
      .domain(allData.map(d => d.assetClass))
      .range([0, chartWidth])
      .padding(0.2);

    const maxValue = Math.max(
      ...allData.map(d => Math.max(Math.abs(d.start), Math.abs(d.end)))
    );
    const yScale = d3
      .scaleLinear()
      .domain([-maxValue * 1.2, maxValue * 1.2])
      .range([chartHeight, 0]);

    // Add grid
    g.append('g')
      .attr('class', 'grid')
      .call(
        d3.axisLeft(yScale)
          .tickSize(-chartWidth)
          .tickFormat('' as any)
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3);

    // Add zero line
    g.append('line')
      .attr('x1', 0)
      .attr('x2', chartWidth)
      .attr('y1', yScale(0))
      .attr('y2', yScale(0))
      .attr('stroke', '#374151')
      .attr('stroke-width', 2);

    // Add bars
    const bars = g.selectAll('.bar')
      .data(allData)
      .enter()
      .append('g')
      .attr('class', 'bar')
      .attr('transform', d => `translate(${xScale(d.assetClass)},0)`);

    bars.append('rect')
      .attr('x', 0)
      .attr('width', xScale.bandwidth())
      .attr('y', d => {
        if (d.assetClass === 'Start' || d.assetClass === 'Total') {
          return d.isPositive ? yScale(d.end) : yScale(0);
        }
        return d.isPositive ? yScale(d.end) : yScale(d.start);
      })
      .attr('height', d => {
        if (d.assetClass === 'Start') return 0;
        if (d.assetClass === 'Total') {
          return Math.abs(yScale(d.end) - yScale(0));
        }
        return Math.abs(yScale(d.end) - yScale(d.start));
      })
      .attr('fill', d => {
        if (d.assetClass === 'Start') return 'transparent';
        if (d.assetClass === 'Total') return d.isPositive ? '#059669' : '#dc2626';
        return d.isPositive ? '#10b981' : '#ef4444';
      })
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        if (d.assetClass === 'Start') return;
        
        // Highlight bar
        d3.select(this).attr('opacity', 0.8);
        
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
          .text(d.assetClass);
        
        if (d.assetClass !== 'Total') {
          text.append('tspan')
            .attr('x', 8)
            .attr('y', 32)
            .text(`Contribution: ${d.totalContribution.toFixed(2)}%`);
        } else {
          text.append('tspan')
            .attr('x', 8)
            .attr('y', 32)
            .text(`Total Return: ${d.totalContribution.toFixed(2)}%`);
        }
        
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
        d3.select(this).attr('opacity', 1);
        g.select('.tooltip').remove();
      })
      .on('click', function(event, d) {
        if (d.assetClass !== 'Start' && d.assetClass !== 'Total' && onDrillDown) {
          const originalData = sortedData.find(item => item.assetClass === d.assetClass);
          if (originalData) onDrillDown(originalData);
        }
      });

    // Add connecting lines
    for (let i = 0; i < allData.length - 1; i++) {
      const current = allData[i];
      const next = allData[i + 1];
      
      if (current.assetClass === 'Start') continue;
      
      const currentX = (xScale(current.assetClass) || 0) + xScale.bandwidth();
      const nextX = xScale(next.assetClass) || 0;
      const yPos = yScale(current.end);
      
      g.append('line')
        .attr('x1', currentX)
        .attr('x2', nextX)
        .attr('y1', yPos)
        .attr('y2', yPos)
        .attr('stroke', '#6b7280')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '2,2')
        .style('opacity', 0.6);
    }

    // Add value labels
    bars.append('text')
      .attr('x', xScale.bandwidth() / 2)
      .attr('y', d => {
        if (d.assetClass === 'Start') return yScale(0) - 5;
        const yPos = d.isPositive ? yScale(d.end) - 5 : yScale(d.start) + 15;
        return yPos;
      })
      .attr('text-anchor', 'middle')
      .style('font-size', '10px')
      .style('font-weight', 'bold')
      .style('fill', '#374151')
      .text(d => d.assetClass === 'Start' ? '0.00%' : `${d.totalContribution.toFixed(2)}%`);

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end');

    g.append('g')
      .call(d3.axisLeft(yScale)
        .tickFormat(d => `${(d as number).toFixed(1)}%`));

    // Add axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (chartHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#6b7280')
      .text('Contribution to Return (%)');
  };

  // Render bar chart (allocation vs selection effects)
  const renderBarChart = () => {
    if (!svgRef.current || !sortedData.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 40, right: 60, bottom: 80, left: 100 };
    const chartWidth = dimensions.width - margin.left - margin.right;
    const chartHeight = dimensions.height - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Prepare data for grouped bar chart
    const barData = sortedData.flatMap(d => [
      { assetClass: d.assetClass, type: 'Allocation', value: d.allocationEffect },
      { assetClass: d.assetClass, type: 'Selection', value: d.selectionEffect }
    ]);

    // Scales
    const xScale = d3
      .scaleBand()
      .domain(sortedData.map(d => d.assetClass))
      .range([0, chartWidth])
      .padding(0.2);

    const xSubScale = d3
      .scaleBand()
      .domain(['Allocation', 'Selection'])
      .range([0, xScale.bandwidth()])
      .padding(0.1);

    const maxValue = Math.max(...barData.map(d => Math.abs(d.value)));
    const yScale = d3
      .scaleLinear()
      .domain([-maxValue * 1.2, maxValue * 1.2])
      .range([chartHeight, 0]);

    // Color scale
    const colorScale = d3.scaleOrdinal()
      .domain(['Allocation', 'Selection'])
      .range(['#3b82f6', '#10b981']);

    // Add grid
    g.append('g')
      .attr('class', 'grid')
      .call(
        d3.axisLeft(yScale)
          .tickSize(-chartWidth)
          .tickFormat('' as any)
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3);

    // Add zero line
    g.append('line')
      .attr('x1', 0)
      .attr('x2', chartWidth)
      .attr('y1', yScale(0))
      .attr('y2', yScale(0))
      .attr('stroke', '#374151')
      .attr('stroke-width', 2);

    // Add bars
    g.selectAll('.bar')
      .data(barData)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => (xScale(d.assetClass) || 0) + (xSubScale(d.type) || 0))
      .attr('width', xSubScale.bandwidth())
      .attr('y', d => d.value >= 0 ? yScale(d.value) : yScale(0))
      .attr('height', d => Math.abs(yScale(d.value) - yScale(0)))
      .attr('fill', d => colorScale(d.type) as string)
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        d3.select(this).attr('opacity', 0.8);
        
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
          .text(`${d.assetClass} - ${d.type}`);
        
        text.append('tspan')
          .attr('x', 8)
          .attr('y', 32)
          .text(`Effect: ${d.value.toFixed(3)}%`);
        
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
        d3.select(this).attr('opacity', 1);
        g.select('.tooltip').remove();
      });

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end');

    g.append('g')
      .call(d3.axisLeft(yScale)
        .tickFormat(d => `${(d as number).toFixed(2)}%`));

    // Add legend
    const legend = g.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${chartWidth - 120}, 20)`);

    ['Allocation', 'Selection'].forEach((type, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${i * 20})`);

      legendItem.append('rect')
        .attr('width', 15)
        .attr('height', 15)
        .attr('fill', colorScale(type) as string);

      legendItem.append('text')
        .attr('x', 20)
        .attr('y', 12)
        .text(type)
        .style('font-size', '12px')
        .style('fill', '#374151');
    });
  };

  // Main rendering effect
  useEffect(() => {
    if (viewType === 'waterfall') {
      renderWaterfallChart();
    } else if (viewType === 'bar') {
      renderBarChart();
    }
  }, [sortedData, dimensions, viewType]);

  const handleExport = (format: ExportOptions['format']) => {
    if (onExport) {
      onExport({
        format,
        quality: 'high',
        dimensions,
        includeData: true,
        filename: `performance-attribution-${viewType}`
      });
    }
  };

  const toggleExpanded = (assetClass: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(assetClass)) {
      newExpanded.delete(assetClass);
    } else {
      newExpanded.add(assetClass);
    }
    setExpandedItems(newExpanded);
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
          <Select value={viewType} onValueChange={(value: any) => setViewType(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="waterfall">Waterfall</SelectItem>
              <SelectItem value="bar">Bar Chart</SelectItem>
              <SelectItem value="tree">Tree Map</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="contribution">Total</SelectItem>
              <SelectItem value="allocation">Allocation</SelectItem>
              <SelectItem value="selection">Selection</SelectItem>
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

      {/* Chart Container */}
      <div ref={containerRef} className="w-full">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="border rounded-lg bg-white dark:bg-gray-900"
        />
      </div>

      {/* Data Table */}
      <div className="mt-6">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Asset Class
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Allocation Effect
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Selection Effect
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Total Contribution
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {sortedData.map((item) => (
                <React.Fragment key={item.assetClass}>
                  <tr className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                      {item.assetClass}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className={`flex items-center ${item.allocationEffect >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {item.allocationEffect >= 0 ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                        {item.allocationEffect.toFixed(3)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className={`flex items-center ${item.selectionEffect >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {item.selectionEffect >= 0 ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                        {item.selectionEffect.toFixed(3)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className={`flex items-center font-semibold ${item.totalContribution >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {item.totalContribution >= 0 ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                        {item.totalContribution.toFixed(3)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-2">
                        {item.sectors && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleExpanded(item.assetClass)}
                          >
                            {expandedItems.has(item.assetClass) ? 
                              <ChevronUp className="h-4 w-4" /> : 
                              <ChevronDown className="h-4 w-4" />
                            }
                          </Button>
                        )}
                        {onDrillDown && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onDrillDown(item)}
                          >
                            <ZoomIn className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {/* Sector breakdown */}
                  {expandedItems.has(item.assetClass) && item.sectors && (
                    item.sectors.map((sector) => (
                      <tr key={`${item.assetClass}-${sector.name}`} className="bg-gray-50 dark:bg-gray-800">
                        <td className="px-12 py-2 text-sm text-gray-600 dark:text-gray-400">
                          {sector.name}
                        </td>
                        <td className="px-6 py-2 text-sm text-gray-900 dark:text-gray-100">
                          {sector.weight.toFixed(2)}%
                        </td>
                        <td className="px-6 py-2 text-sm">
                          <span className={sector.return >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {sector.return.toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-6 py-2 text-sm">
                          <span className={sector.contribution >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {sector.contribution.toFixed(3)}%
                          </span>
                        </td>
                        <td></td>
                      </tr>
                    ))
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
};

export default PerformanceAttributionChart;