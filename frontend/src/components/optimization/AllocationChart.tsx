import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { PieChart, Edit3, RotateCcw, Lock, Unlock } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface AssetAllocation {
  id: string;
  name: string;
  symbol: string;
  percentage: number;
  color: string;
  locked?: boolean;
  minAllocation?: number;
  maxAllocation?: number;
  expectedReturn?: number;
  risk?: number;
}

interface AllocationChartProps {
  id?: string;
  allocations: AssetAllocation[];
  onAllocationChange?: (allocations: AssetAllocation[]) => void;
  editable?: boolean;
  showControls?: boolean;
  className?: string;
}

export const AllocationChart: React.FC<AllocationChartProps> = ({
  id = "allocation-chart",
  allocations: initialAllocations = [],
  onAllocationChange,
  editable = true,
  showControls = true,
  className = ""
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [allocations, setAllocations] = useState<AssetAllocation[]>(initialAllocations);
  const [dimensions, setDimensions] = useState({ width: 400, height: 400 });
  const [dragging, setDragging] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const { toast } = useToast();

  // Generate default allocations if none provided
  const defaultAllocations: AssetAllocation[] = [
    { id: '1', name: 'US Stocks', symbol: 'VTI', percentage: 40, color: '#3b82f6', expectedReturn: 8.5, risk: 18 },
    { id: '2', name: 'International Stocks', symbol: 'VTIAX', percentage: 20, color: '#10b981', expectedReturn: 7.2, risk: 20 },
    { id: '3', name: 'Bonds', symbol: 'BND', percentage: 25, color: '#f59e0b', expectedReturn: 4.1, risk: 6 },
    { id: '4', name: 'REITs', symbol: 'VNQ', percentage: 10, color: '#ef4444', expectedReturn: 6.8, risk: 22 },
    { id: '5', name: 'Cash', symbol: 'VMFXX', percentage: 5, color: '#8b5cf6', expectedReturn: 2.1, risk: 1 }
  ];

  useEffect(() => {
    if (initialAllocations.length === 0) {
      setAllocations(defaultAllocations);
    } else {
      setAllocations(initialAllocations);
    }
  }, [initialAllocations]);

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current?.parentElement) {
        const rect = svgRef.current.parentElement.getBoundingClientRect();
        const size = Math.min(rect.width - 40, 400);
        setDimensions({ width: size, height: size });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // D3 pie chart with drag functionality
  useEffect(() => {
    if (!svgRef.current || allocations.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = dimensions.width;
    const height = dimensions.height;
    const radius = Math.min(width, height) / 2 - 30;

    const g = svg.append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    const pie = d3.pie<AssetAllocation>()
      .value(d => d.percentage)
      .sort(null);

    const arc = d3.arc<d3.PieArcDatum<AssetAllocation>>()
      .innerRadius(radius * 0.4)
      .outerRadius(radius);

    const hoverArc = d3.arc<d3.PieArcDatum<AssetAllocation>>()
      .innerRadius(radius * 0.4)
      .outerRadius(radius + 10);

    const pieData = pie(allocations);

    // Create arcs
    const arcs = g.selectAll(".arc")
      .data(pieData)
      .enter()
      .append("g")
      .attr("class", "arc");

    const paths = arcs.append("path")
      .attr("d", arc)
      .attr("fill", d => d.data.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("cursor", editable ? "grab" : "default")
      .style("opacity", 0.8)
      .on("mouseover", function(event, d) {
        if (!dragging) {
          d3.select(this)
            .transition()
            .duration(200)
            .attr("d", hoverArc)
            .style("opacity", 1);
            
          // Show tooltip
          showTooltip(event, d.data);
        }
      })
      .on("mouseout", function() {
        if (!dragging) {
          d3.select(this)
            .transition()
            .duration(200)
            .attr("d", arc)
            .style("opacity", 0.8);
            
          hideTooltip();
        }
      });

    // Add drag behavior for editable mode
    if (editable) {
      const dragHandler = d3.drag<SVGPathElement, d3.PieArcDatum<AssetAllocation>>()
        .on("start", function(event, d) {
          if (d.data.locked) return;
          setDragging(d.data.id);
          d3.select(this).style("cursor", "grabbing");
        })
        .on("drag", function(event, d) {
          if (d.data.locked || !dragging) return;
          
          const center = [width / 2, height / 2];
          const angle = Math.atan2(event.y - center[1], event.x - center[0]);
          let adjustedAngle = angle + Math.PI / 2;
          if (adjustedAngle < 0) adjustedAngle += 2 * Math.PI;
          
          // Calculate new percentage based on angle
          const newPercentage = Math.max(1, Math.min(80, (adjustedAngle / (2 * Math.PI)) * 100));
          
          updateAllocation(d.data.id, newPercentage);
        })
        .on("end", function() {
          setDragging(null);
          d3.select(this).style("cursor", "grab");
        });

      paths.call(dragHandler);
    }

    // Add percentage labels
    arcs.append("text")
      .attr("transform", d => {
        const centroid = arc.centroid(d);
        return `translate(${centroid})`;
      })
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .style("font-size", "12px")
      .style("font-weight", "bold")
      .style("fill", "#fff")
      .style("text-shadow", "1px 1px 2px rgba(0,0,0,0.7)")
      .text(d => d.data.percentage >= 5 ? `${d.data.percentage.toFixed(1)}%` : '');

    // Add asset labels outside the chart
    const labelArc = d3.arc<d3.PieArcDatum<AssetAllocation>>()
      .innerRadius(radius + 20)
      .outerRadius(radius + 20);

    arcs.append("text")
      .attr("transform", d => {
        const centroid = labelArc.centroid(d);
        return `translate(${centroid})`;
      })
      .attr("text-anchor", d => {
        const centroid = labelArc.centroid(d);
        return centroid[0] > 0 ? "start" : "end";
      })
      .attr("dominant-baseline", "middle")
      .style("font-size", "11px")
      .style("fill", "rgba(255,255,255,0.8)")
      .style("font-weight", "500")
      .text(d => d.data.percentage >= 3 ? d.data.symbol : '');

    // Add center text
    g.append("text")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .style("font-size", "14px")
      .style("font-weight", "bold")
      .style("fill", "rgba(255,255,255,0.9)")
      .text("Portfolio");

    g.append("text")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("y", 15)
      .style("font-size", "11px")
      .style("fill", "rgba(255,255,255,0.7)")
      .text("Allocation");

  }, [allocations, dimensions, editable, dragging]);

  const showTooltip = (event: MouseEvent, asset: AssetAllocation) => {
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "allocation-tooltip")
      .style("position", "absolute")
      .style("background", "rgba(0,0,0,0.9)")
      .style("color", "white")
      .style("padding", "10px")
      .style("border-radius", "8px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("opacity", 0)
      .style("z-index", 1000);

    tooltip.transition()
      .duration(200)
      .style("opacity", 1);

    tooltip.html(`
      <div style="border-left: 3px solid ${asset.color}; padding-left: 8px;">
        <strong>${asset.name} (${asset.symbol})</strong><br/>
        <span style="color: #22c55e;">Allocation: ${asset.percentage.toFixed(1)}%</span><br/>
        ${asset.expectedReturn ? `Expected Return: ${asset.expectedReturn.toFixed(1)}%<br/>` : ''}
        ${asset.risk ? `Risk: ${asset.risk.toFixed(1)}%<br/>` : ''}
        ${asset.locked ? '<span style="color: #f59e0b;">🔒 Locked</span>' : ''}
      </div>
    `)
    .style("left", (event.pageX + 10) + "px")
    .style("top", (event.pageY - 10) + "px");
  };

  const hideTooltip = () => {
    d3.selectAll(".allocation-tooltip").remove();
  };

  const updateAllocation = useCallback((assetId: string, newPercentage: number) => {
    setAllocations(prev => {
      const updated = prev.map(asset => 
        asset.id === assetId 
          ? { ...asset, percentage: Math.round(newPercentage * 10) / 10 }
          : asset
      );
      
      // Normalize to ensure total is 100%
      const total = updated.reduce((sum, asset) => sum + asset.percentage, 0);
      const normalized = updated.map(asset => ({
        ...asset,
        percentage: Math.round((asset.percentage / total * 100) * 10) / 10
      }));
      
      onAllocationChange?.(normalized);
      return normalized;
    });
  }, [onAllocationChange]);

  const handleSliderChange = (assetId: string, value: number[]) => {
    updateAllocation(assetId, value[0]);
  };

  const toggleLock = (assetId: string) => {
    setAllocations(prev => prev.map(asset =>
      asset.id === assetId ? { ...asset, locked: !asset.locked } : asset
    ));
  };

  const resetAllocations = () => {
    setAllocations(defaultAllocations);
    onAllocationChange?.(defaultAllocations);
    toast({
      title: "Allocations Reset",
      description: "Portfolio allocations have been reset to defaults.",
    });
  };

  const rebalanceEqually = () => {
    const equalPercentage = Math.round((100 / allocations.length) * 10) / 10;
    const balanced = allocations.map(asset => ({
      ...asset,
      percentage: equalPercentage
    }));
    
    setAllocations(balanced);
    onAllocationChange?.(balanced);
    toast({
      title: "Equal Rebalancing",
      description: "Portfolio has been rebalanced equally across all assets.",
    });
  };

  return (
    <Card id={id} className={`glass border-white/10 ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PieChart className="w-5 h-5 text-primary" />
            Asset Allocation
          </div>
          {showControls && (
            <div className="flex items-center gap-2">
              <Button
                id="edit-mode-btn"
                variant="ghost"
                size="sm"
                onClick={() => setEditMode(!editMode)}
                className="text-xs"
              >
                <Edit3 className="w-4 h-4 mr-1" />
                {editMode ? 'Chart' : 'Edit'}
              </Button>
            </div>
          )}
        </CardTitle>
        <CardDescription>
          {editable ? 'Drag slices to adjust allocation or use controls below' : 'Current portfolio distribution'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {!editMode ? (
          <>
            {/* Chart */}
            <div id="allocation-pie-chart" className="flex justify-center">
              <svg
                ref={svgRef}
                width={dimensions.width}
                height={dimensions.height}
                style={{ background: 'transparent' }}
              />
            </div>

            {/* Legend */}
            <div id="allocation-legend" className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {allocations.map((asset) => (
                <div key={asset.id} className="flex items-center gap-3 p-2 rounded-lg bg-white/5">
                  <div 
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: asset.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">{asset.name}</span>
                      {asset.locked && <Lock className="w-3 h-3 text-warning" />}
                    </div>
                    <span className="text-xs text-muted-foreground">{asset.symbol}</span>
                  </div>
                  <Badge variant="outline" className="text-xs bg-white/10">
                    {asset.percentage.toFixed(1)}%
                  </Badge>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div id="allocation-controls" className="space-y-4">
            {/* Slider Controls */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium">Manual Allocation</h4>
              {allocations.map((asset) => (
                <div key={asset.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: asset.color }}
                      />
                      <span className="text-sm font-medium">{asset.name}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleLock(asset.id)}
                        className="h-6 w-6 p-0"
                      >
                        {asset.locked ? (
                          <Lock className="w-3 h-3 text-warning" />
                        ) : (
                          <Unlock className="w-3 h-3 text-muted-foreground" />
                        )}
                      </Button>
                    </div>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={asset.percentage}
                        onChange={(e) => handleSliderChange(asset.id, [parseFloat(e.target.value) || 0])}
                        className="w-16 h-6 text-xs"
                        min="0"
                        max="100"
                        step="0.1"
                        disabled={asset.locked}
                      />
                      <span className="text-xs text-muted-foreground">%</span>
                    </div>
                  </div>
                  <Slider
                    value={[asset.percentage]}
                    onValueChange={(value) => handleSliderChange(asset.id, value)}
                    max={100}
                    min={0}
                    step={0.1}
                    disabled={asset.locked}
                    className="w-full"
                  />
                </div>
              ))}
            </div>

            {/* Total Check */}
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Total Allocation</span>
                <Badge 
                  variant={Math.abs(allocations.reduce((sum, a) => sum + a.percentage, 0) - 100) < 0.1 ? "default" : "destructive"}
                >
                  {allocations.reduce((sum, a) => sum + a.percentage, 0).toFixed(1)}%
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {showControls && (
          <div id="allocation-actions" className="flex gap-2 justify-center">
            <Button
              id="reset-allocation-btn"
              variant="outline"
              size="sm"
              onClick={resetAllocations}
              className="glass border-white/20"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
            <Button
              id="rebalance-equal-btn"
              variant="outline"
              size="sm"
              onClick={rebalanceEqually}
              className="glass border-white/20"
            >
              Equal Split
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AllocationChart;