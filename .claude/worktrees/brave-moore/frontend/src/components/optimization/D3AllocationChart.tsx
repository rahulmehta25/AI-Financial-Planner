import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
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

interface D3AllocationChartProps {
  id?: string;
  allocations: AssetAllocation[];
  onAllocationChange?: (allocations: AssetAllocation[]) => void;
  editable?: boolean;
  showControls?: boolean;
}

export const D3AllocationChart: React.FC<D3AllocationChartProps> = ({
  id = "allocation-chart",
  allocations: initialAllocations = [],
  onAllocationChange,
  editable = true,
  showControls = true,
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
    { id: '2', name: 'International', symbol: 'VTIAX', percentage: 25, color: '#10b981', expectedReturn: 7.2, risk: 20 },
    { id: '3', name: 'Bonds', symbol: 'BND', percentage: 20, color: '#f59e0b', expectedReturn: 4.5, risk: 6 },
    { id: '4', name: 'REITs', symbol: 'VNQ', percentage: 10, color: '#ef4444', expectedReturn: 6.8, risk: 22 },
    { id: '5', name: 'Cash', symbol: 'CASH', percentage: 5, color: '#6b7280', expectedReturn: 2.0, risk: 1 },
  ];

  // Use provided allocations or defaults
  useEffect(() => {
    if (initialAllocations.length === 0) {
      setAllocations(defaultAllocations);
    } else {
      setAllocations(initialAllocations);
    }
  }, [initialAllocations]);

  // D3 Pie Chart Implementation
  useEffect(() => {
    if (!svgRef.current || allocations.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render

    const { width, height } = dimensions;
    const radius = Math.min(width, height) / 2 - 20;
    const innerRadius = editable ? radius * 0.3 : 0; // Donut chart if editable

    const g = svg
      .append("g")
      .attr("transform", `translate(${width / 2}, ${height / 2})`);

    const pie = d3
      .pie<AssetAllocation>()
      .value((d) => d.percentage)
      .sort(null);

    const arc = d3
      .arc<d3.PieArcDatum<AssetAllocation>>()
      .innerRadius(innerRadius)
      .outerRadius(radius);

    const arcs = g
      .selectAll(".arc")
      .data(pie(allocations))
      .enter()
      .append("g")
      .attr("class", "arc");

    arcs
      .append("path")
      .attr("d", arc)
      .attr("fill", (d) => d.data.color)
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("cursor", editable ? "pointer" : "default")
      .on("mouseover", function(event, d) {
        if (editable) {
          d3.select(this)
            .transition()
            .duration(100)
            .attr("transform", function() {
              const centroid = arc.centroid(d);
              const x = centroid[0] * 0.1;
              const y = centroid[1] * 0.1;
              return `translate(${x}, ${y})`;
            });
        }
      })
      .on("mouseout", function() {
        if (editable) {
          d3.select(this)
            .transition()
            .duration(100)
            .attr("transform", "translate(0, 0)");
        }
      });

    // Add percentage labels
    arcs
      .append("text")
      .attr("transform", (d) => `translate(${arc.centroid(d)})`)
      .attr("dy", "0.35em")
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .style("font-weight", "500")
      .style("fill", "white")
      .style("text-shadow", "0 1px 2px rgba(0,0,0,0.6)")
      .text((d) => d.data.percentage > 5 ? `${d.data.percentage}%` : '');

    // Add center text for donut chart
    if (editable && innerRadius > 0) {
      g.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "-0.5em")
        .style("font-size", "14px")
        .style("font-weight", "600")
        .style("fill", "#374151")
        .text("Portfolio");

      g.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "1em")
        .style("font-size", "12px")
        .style("fill", "#6b7280")
        .text("Allocation");
    }

  }, [allocations, dimensions, editable]);

  const handleAllocationChange = useCallback((id: string, newPercentage: number) => {
    const updatedAllocations = allocations.map(allocation => 
      allocation.id === id ? { ...allocation, percentage: newPercentage } : allocation
    );
    
    // Ensure total doesn't exceed 100%
    const total = updatedAllocations.reduce((sum, a) => sum + a.percentage, 0);
    if (total <= 100) {
      setAllocations(updatedAllocations);
      onAllocationChange?.(updatedAllocations);
    }
  }, [allocations, onAllocationChange]);

  const resetAllocations = () => {
    setAllocations(defaultAllocations);
    onAllocationChange?.(defaultAllocations);
    toast({
      title: "Allocations Reset",
      description: "Portfolio allocations have been reset to default values.",
    });
  };

  const toggleLock = (id: string) => {
    const updatedAllocations = allocations.map(allocation => 
      allocation.id === id ? { ...allocation, locked: !allocation.locked } : allocation
    );
    setAllocations(updatedAllocations);
    onAllocationChange?.(updatedAllocations);
  };

  const totalAllocation = allocations.reduce((sum, allocation) => sum + allocation.percentage, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <PieChart className="h-5 w-5" />
          <span className="font-medium">Asset Allocation</span>
          <Badge variant={totalAllocation === 100 ? "default" : "destructive"}>
            {totalAllocation}%
          </Badge>
        </div>
        {showControls && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditMode(!editMode)}
            >
              <Edit3 className="h-4 w-4 mr-1" />
              {editMode ? "View" : "Edit"}
            </Button>
            <Button variant="outline" size="sm" onClick={resetAllocations}>
              <RotateCcw className="h-4 w-4 mr-1" />
              Reset
            </Button>
          </div>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Chart */}
        <div className="flex-1">
          <svg
            ref={svgRef}
            width={dimensions.width}
            height={dimensions.height}
            className="w-full h-auto"
          />
        </div>

        {/* Controls */}
        {editMode && showControls && (
          <div className="lg:w-80 space-y-3">
            <h4 className="font-medium text-sm">Allocation Controls</h4>
            {allocations.map((allocation) => (
              <div key={allocation.id} className="space-y-2 p-3 border rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: allocation.color }}
                    />
                    <span className="font-medium text-sm">{allocation.name}</span>
                    <Badge variant="outline" className="text-xs">
                      {allocation.symbol}
                    </Badge>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleLock(allocation.id)}
                    className="h-6 w-6 p-0"
                  >
                    {allocation.locked ? (
                      <Lock className="h-3 w-3" />
                    ) : (
                      <Unlock className="h-3 w-3" />
                    )}
                  </Button>
                </div>
                
                {!allocation.locked && (
                  <>
                    <Slider
                      value={[allocation.percentage]}
                      onValueChange={([value]) => handleAllocationChange(allocation.id, value)}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={allocation.percentage}
                        onChange={(e) => handleAllocationChange(allocation.id, Number(e.target.value))}
                        className="w-20 h-8"
                      />
                      <span className="text-sm text-muted-foreground">%</span>
                    </div>
                  </>
                )}
                
                {allocation.expectedReturn && (
                  <div className="text-xs text-muted-foreground">
                    Expected Return: {allocation.expectedReturn}% | Risk: {allocation.risk}%
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Legend for non-edit mode */}
      {!editMode && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
          {allocations.map((allocation) => (
            <div key={allocation.id} className="flex items-center gap-2 text-sm">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: allocation.color }}
              />
              <span className="truncate">{allocation.name}</span>
              <span className="font-medium">{allocation.percentage}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};