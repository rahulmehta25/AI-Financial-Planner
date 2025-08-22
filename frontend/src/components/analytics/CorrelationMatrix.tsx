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
  CorrelationData,
  HeatMapData,
  ExportOptions,
} from '@/types/analytics';
import { Download, Info, Eye, EyeOff } from 'lucide-react';

interface CorrelationMatrixProps {
  id?: string;
  data: CorrelationData;
  title?: string;
  subtitle?: string;
  height?: number;
  width?: number;
  onExport?: (options: ExportOptions) => void;
  onCellClick?: (asset1: string, asset2: string, correlation: number) => void;
  className?: string;
}

export const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({
  id = 'correlation-matrix',
  data,
  title = 'Asset Correlation Matrix',
  subtitle = 'Correlation coefficients between portfolio assets',
  height = 500,
  width,
  onExport,
  onCellClick,
  className = '',
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [colorScheme, setColorScheme] = useState<'RdBu' | 'viridis' | 'plasma'>('RdBu');
  const [showValues, setShowValues] = useState(true);
  const [highlightedAsset, setHighlightedAsset] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height });

  // Convert correlation matrix to heat map data
  const heatMapData = useMemo(() => {
    const result: HeatMapData[] = [];
    for (let i = 0; i < data.assets.length; i++) {
      for (let j = 0; j < data.assets.length; j++) {
        result.push({
          row: data.assets[i],
          column: data.assets[j],
          value: data.matrix[i][j],
          displayValue: data.matrix[i][j].toFixed(3)
        });
      }
    }
    return result;
  }, [data]);

  // Handle responsive sizing
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        const size = width || Math.min(containerWidth - 40, 600);
        setDimensions({
          width: size,
          height: size
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [width]);

  // D3.js heat map rendering
  useEffect(() => {
    if (!svgRef.current || !data.assets.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous chart

    const margin = { top: 80, right: 80, bottom: 120, left: 120 };
    const chartWidth = dimensions.width - margin.left - margin.right;
    const chartHeight = dimensions.height - margin.top - margin.bottom;

    // Create main group
    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Calculate cell size
    const cellSize = Math.min(chartWidth, chartHeight) / data.assets.length;

    // Create scales
    const xScale = d3
      .scaleBand()
      .domain(data.assets)
      .range([0, data.assets.length * cellSize])
      .padding(0.05);

    const yScale = d3
      .scaleBand()
      .domain(data.assets)
      .range([0, data.assets.length * cellSize])
      .padding(0.05);

    // Color scale based on selected scheme
    let colorScale: d3.ScaleSequential<string>;
    switch (colorScheme) {
      case 'viridis':
        colorScale = d3.scaleSequential(d3.interpolateViridis).domain([-1, 1]);
        break;
      case 'plasma':
        colorScale = d3.scaleSequential(d3.interpolatePlasma).domain([-1, 1]);
        break;
      default:
        colorScale = d3.scaleSequential(d3.interpolateRdBu).domain([1, -1]);
    }

    // Create cells
    const cells = g.selectAll('.cell')
      .data(heatMapData)
      .enter()
      .append('g')
      .attr('class', 'cell')
      .attr('transform', d => `translate(${xScale(d.column)},${yScale(d.row)})`);

    // Add rectangles
    cells.append('rect')
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', d => colorScale(d.value))
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 1)
      .attr('rx', 2)
      .style('cursor', 'pointer')
      .style('opacity', d => {
        if (!highlightedAsset) return 1;
        return d.row === highlightedAsset || d.column === highlightedAsset ? 1 : 0.3;
      })
      .on('mouseover', function(event, d) {
        // Highlight row and column
        g.selectAll('.cell rect')
          .style('opacity', cell => 
            cell.row === d.row || cell.column === d.column ? 1 : 0.3
          );

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
          .text(`${d.row} vs ${d.column}`);
        
        text.append('tspan')
          .attr('x', 8)
          .attr('y', 32)
          .text(`Correlation: ${d.value.toFixed(3)}`);

        const interpretation = Math.abs(d.value) > 0.7 ? 'Strong' : 
                              Math.abs(d.value) > 0.3 ? 'Moderate' : 'Weak';
        const direction = d.value > 0 ? 'Positive' : 'Negative';
        
        text.append('tspan')
          .attr('x', 8)
          .attr('y', 48)
          .text(`${interpretation} ${direction}`);
        
        const bbox = text.node()?.getBBox();
        if (bbox) {
          rect
            .attr('width', bbox.width + 16)
            .attr('height', bbox.height + 8);
        }
        
        const [mouseX, mouseY] = d3.pointer(event, g.node());
        tooltip.attr('transform', `translate(${mouseX + 10},${mouseY - 60})`);
      })
      .on('mouseout', function() {
        g.selectAll('.cell rect')
          .style('opacity', d => {
            if (!highlightedAsset) return 1;
            return d.row === highlightedAsset || d.column === highlightedAsset ? 1 : 0.3;
          });
        g.select('.tooltip').remove();
      })
      .on('click', function(event, d) {
        if (onCellClick) {
          onCellClick(d.row, d.column, d.value);
        }
      });

    // Add correlation values (if enabled)
    if (showValues) {
      cells.append('text')
        .attr('x', xScale.bandwidth() / 2)
        .attr('y', yScale.bandwidth() / 2)
        .attr('dy', '.35em')
        .attr('text-anchor', 'middle')
        .attr('fill', d => {
          // Choose text color based on background
          const luminance = d3.color(colorScale(d.value))?.rgb();
          if (!luminance) return '#000';
          const brightness = (luminance.r * 299 + luminance.g * 587 + luminance.b * 114) / 1000;
          return brightness > 128 ? '#000' : '#fff';
        })
        .style('font-size', `${Math.min(xScale.bandwidth() / 6, 12)}px`)
        .style('font-weight', 'bold')
        .style('pointer-events', 'none')
        .text(d => Math.abs(d.value) < 0.001 ? '0' : d.value.toFixed(2));
    }

    // Add row labels
    g.selectAll('.row-label')
      .data(data.assets)
      .enter()
      .append('text')
      .attr('class', 'row-label')
      .attr('x', -10)
      .attr('y', d => (yScale(d) || 0) + yScale.bandwidth() / 2)
      .attr('dy', '.35em')
      .attr('text-anchor', 'end')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', '#374151')
      .style('cursor', 'pointer')
      .text(d => d)
      .on('click', function(event, d) {
        setHighlightedAsset(highlightedAsset === d ? null : d);
      });

    // Add column labels
    g.selectAll('.column-label')
      .data(data.assets)
      .enter()
      .append('text')
      .attr('class', 'column-label')
      .attr('x', d => (xScale(d) || 0) + xScale.bandwidth() / 2)
      .attr('y', -10)
      .attr('text-anchor', 'start')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('fill', '#374151')
      .style('cursor', 'pointer')
      .attr('transform', d => {
        const x = (xScale(d) || 0) + xScale.bandwidth() / 2;
        return `rotate(-45, ${x}, -10)`;
      })
      .text(d => d)
      .on('click', function(event, d) {
        setHighlightedAsset(highlightedAsset === d ? null : d);
      });

    // Add color legend
    const legendWidth = 200;
    const legendHeight = 20;
    const legendX = chartWidth - legendWidth;
    const legendY = chartHeight + 60;

    const legendScale = d3.scaleLinear()
      .domain([-1, 1])
      .range([0, legendWidth]);

    const legendAxis = d3.axisBottom(legendScale)
      .tickValues([-1, -0.5, 0, 0.5, 1])
      .tickFormat(d => d.toString());

    const legend = g.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${legendX},${legendY})`);

    // Create gradient for legend
    const legendGradient = svg
      .append('defs')
      .append('linearGradient')
      .attr('id', `${id}-legend-gradient`)
      .attr('x1', '0%')
      .attr('x2', '100%');

    const numStops = 10;
    for (let i = 0; i <= numStops; i++) {
      const offset = (i / numStops) * 100;
      const value = -1 + (i / numStops) * 2;
      legendGradient
        .append('stop')
        .attr('offset', `${offset}%`)
        .attr('stop-color', colorScale(value));
    }

    legend.append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .style('fill', `url(#${id}-legend-gradient)`)
      .style('stroke', '#ccc');

    legend.append('g')
      .attr('transform', `translate(0,${legendHeight})`)
      .call(legendAxis);

    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', -8)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#374151')
      .text('Correlation Coefficient');

  }, [data, dimensions, colorScheme, showValues, highlightedAsset, id]);

  const handleExport = (format: ExportOptions['format']) => {
    if (onExport) {
      onExport({
        format,
        quality: 'high',
        dimensions,
        includeData: true,
        filename: `correlation-matrix-${data.metadata.period}`
      });
    }
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
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>Period: {data.metadata.period}</span>
            <span>Frequency: {data.metadata.frequency}</span>
            <span>Assets: {data.assets.length}</span>
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2 mt-4 sm:mt-0">
          <Select value={colorScheme} onValueChange={(value: any) => setColorScheme(value)}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="RdBu">Red-Blue</SelectItem>
              <SelectItem value="viridis">Viridis</SelectItem>
              <SelectItem value="plasma">Plasma</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowValues(!showValues)}
          >
            {showValues ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setHighlightedAsset(null)}
            disabled={!highlightedAsset}
          >
            Clear
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

      {/* Info Panel */}
      <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg mb-6">
        <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-800 dark:text-blue-200">
          <p className="font-medium mb-1">How to interpret correlations:</p>
          <ul className="space-y-1 text-xs">
            <li><strong>+1.0:</strong> Perfect positive correlation</li>
            <li><strong>+0.7 to +1.0:</strong> Strong positive correlation</li>
            <li><strong>+0.3 to +0.7:</strong> Moderate positive correlation</li>
            <li><strong>-0.3 to +0.3:</strong> Weak or no correlation</li>
            <li><strong>-0.7 to -0.3:</strong> Moderate negative correlation</li>
            <li><strong>-1.0 to -0.7:</strong> Strong negative correlation</li>
            <li><strong>-1.0:</strong> Perfect negative correlation</li>
          </ul>
        </div>
      </div>

      {/* Chart Container */}
      <div ref={containerRef} className="w-full flex justify-center">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="border rounded-lg bg-white dark:bg-gray-900"
        />
      </div>

      {/* Summary Statistics */}
      <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-sm text-gray-600 dark:text-gray-400">Avg Correlation</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {(heatMapData
              .filter(d => d.row !== d.column)
              .reduce((sum, d) => sum + d.value, 0) / heatMapData.filter(d => d.row !== d.column).length
            ).toFixed(3)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-600 dark:text-gray-400">Max Correlation</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {Math.max(...heatMapData.filter(d => d.row !== d.column).map(d => d.value)).toFixed(3)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-600 dark:text-gray-400">Min Correlation</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {Math.min(...heatMapData.filter(d => d.row !== d.column).map(d => d.value)).toFixed(3)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-600 dark:text-gray-400">Diversification</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {(heatMapData.filter(d => d.row !== d.column && Math.abs(d.value) < 0.3).length / 
              heatMapData.filter(d => d.row !== d.column).length * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </Card>
  );
};

export default CorrelationMatrix;