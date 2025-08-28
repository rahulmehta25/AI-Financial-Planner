import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TrendingUp, Target, BarChart3 } from 'lucide-react';

interface PortfolioPoint {
  risk: number;
  return: number;
  sharpeRatio: number;
  volatility: number;
  expectedReturn: number;
  weights?: { [key: string]: number };
}

interface EfficientFrontierProps {
  id?: string;
  portfolioData?: PortfolioPoint[];
  currentPortfolio?: PortfolioPoint;
  onPointSelect?: (portfolio: PortfolioPoint) => void;
  onRiskReturnChange?: (risk: number, expectedReturn: number) => void;
  className?: string;
}

export const EfficientFrontier: React.FC<EfficientFrontierProps> = ({
  id = "efficient-frontier",
  portfolioData = [],
  currentPortfolio,
  onPointSelect,
  onRiskReturnChange,
  className = ""
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedPoint, setSelectedPoint] = useState<PortfolioPoint | null>(null);
  const [targetRisk, setTargetRisk] = useState<number[]>([15]);
  const [targetReturn, setTargetReturn] = useState<number[]>([8]);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Generate mock efficient frontier data if none provided
  const generateMockData = (): PortfolioPoint[] => {
    const points: PortfolioPoint[] = [];
    for (let i = 0; i <= 100; i++) {
      const risk = (i / 100) * 25 + 5; // Risk from 5% to 30%
      const baseReturn = Math.sqrt(risk - 5) * 2.5 + 3; // Curved relationship
      const noise = (Math.random() - 0.5) * 0.5;
      const expectedReturn = baseReturn + noise;
      const sharpeRatio = (expectedReturn - 2) / risk; // Assuming 2% risk-free rate
      
      points.push({
        risk: Number(risk.toFixed(2)),
        return: Number(expectedReturn.toFixed(2)),
        sharpeRatio: Number(sharpeRatio.toFixed(3)),
        volatility: risk,
        expectedReturn,
        weights: {
          'Stocks': Math.random() * 0.8,
          'Bonds': Math.random() * 0.3,
          'REITs': Math.random() * 0.1,
          'Cash': Math.random() * 0.05
        }
      });
    }
    return points.sort((a, b) => a.risk - b.risk);
  };

  const frontierData = portfolioData.length > 0 ? portfolioData : generateMockData();

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current?.parentElement) {
        const rect = svgRef.current.parentElement.getBoundingClientRect();
        setDimensions({ width: rect.width - 40, height: 400 });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // D3 visualization
  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = { top: 20, right: 30, bottom: 50, left: 60 };
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;

    // Create scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(frontierData, d => d.risk) as [number, number])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain(d3.extent(frontierData, d => d.return) as [number, number])
      .range([height, 0]);

    const colorScale = d3.scaleSequential(d3.interpolateViridis)
      .domain(d3.extent(frontierData, d => d.sharpeRatio) as [number, number]);

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Add grid lines
    const xAxisGrid = d3.axisBottom(xScale)
      .tickSize(-height)
      .tickFormat("" as any);

    const yAxisGrid = d3.axisLeft(yScale)
      .tickSize(-width)
      .tickFormat("" as any);

    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(xAxisGrid)
      .selectAll("line")
      .style("stroke", "rgba(255,255,255,0.1)")
      .style("stroke-width", 0.5);

    g.append("g")
      .attr("class", "grid")
      .call(yAxisGrid)
      .selectAll("line")
      .style("stroke", "rgba(255,255,255,0.1)")
      .style("stroke-width", 0.5);

    // Draw efficient frontier line
    const line = d3.line<PortfolioPoint>()
      .x(d => xScale(d.risk))
      .y(d => yScale(d.return))
      .curve(d3.curveCardinal);

    g.append("path")
      .datum(frontierData)
      .attr("d", line)
      .style("fill", "none")
      .style("stroke", "url(#gradient)")
      .style("stroke-width", 3)
      .style("opacity", 0.8);

    // Create gradient definition
    const gradient = svg.append("defs")
      .append("linearGradient")
      .attr("id", "gradient")
      .attr("gradientUnits", "userSpaceOnUse")
      .attr("x1", xScale(d3.min(frontierData, d => d.risk) || 0)).attr("y1", 0)
      .attr("x2", xScale(d3.max(frontierData, d => d.risk) || 0)).attr("y2", 0);

    gradient.selectAll("stop")
      .data(frontierData.filter((_, i) => i % 10 === 0))
      .enter().append("stop")
      .attr("offset", d => `${((d.risk - d3.min(frontierData, d => d.risk)!) / (d3.max(frontierData, d => d.risk)! - d3.min(frontierData, d => d.risk)!)) * 100}%`)
      .attr("stop-color", d => colorScale(d.sharpeRatio));

    // Add points
    const points = g.selectAll(".frontier-point")
      .data(frontierData.filter((_, i) => i % 5 === 0)) // Show every 5th point
      .enter()
      .append("circle")
      .attr("class", "frontier-point")
      .attr("cx", d => xScale(d.risk))
      .attr("cy", d => yScale(d.return))
      .attr("r", 4)
      .style("fill", d => colorScale(d.sharpeRatio))
      .style("stroke", "#fff")
      .style("stroke-width", 1)
      .style("cursor", "pointer")
      .style("opacity", 0.8)
      .on("mouseover", function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 6)
          .style("stroke-width", 2);

        // Show tooltip
        const tooltip = d3.select("body").append("div")
          .attr("class", "tooltip")
          .style("position", "absolute")
          .style("background", "rgba(0,0,0,0.9)")
          .style("color", "white")
          .style("padding", "10px")
          .style("border-radius", "5px")
          .style("font-size", "12px")
          .style("pointer-events", "none")
          .style("opacity", 0)
          .style("z-index", 1000);

        tooltip.transition()
          .duration(200)
          .style("opacity", 1);

        tooltip.html(`
          <strong>Portfolio Point</strong><br/>
          Risk: ${d.risk.toFixed(1)}%<br/>
          Return: ${d.return.toFixed(1)}%<br/>
          Sharpe: ${d.sharpeRatio.toFixed(2)}
        `)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 10) + "px");
      })
      .on("mouseout", function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 4)
          .style("stroke-width", 1);

        d3.selectAll(".tooltip").remove();
      })
      .on("click", function(event, d) {
        setSelectedPoint(d);
        onPointSelect?.(d);
      });

    // Add current portfolio point if provided
    if (currentPortfolio) {
      g.append("circle")
        .attr("class", "current-portfolio")
        .attr("cx", xScale(currentPortfolio.risk))
        .attr("cy", yScale(currentPortfolio.return))
        .attr("r", 8)
        .style("fill", "#22c55e")
        .style("stroke", "#fff")
        .style("stroke-width", 3)
        .style("opacity", 0.9);

      g.append("text")
        .attr("x", xScale(currentPortfolio.risk))
        .attr("y", yScale(currentPortfolio.return) - 15)
        .attr("text-anchor", "middle")
        .style("fill", "#22c55e")
        .style("font-size", "12px")
        .style("font-weight", "bold")
        .text("Current");
    }

    // Add target point
    const targetRiskValue = targetRisk[0];
    const targetReturnValue = targetReturn[0];
    
    g.append("circle")
      .attr("class", "target-portfolio")
      .attr("cx", xScale(targetRiskValue))
      .attr("cy", yScale(targetReturnValue))
      .attr("r", 6)
      .style("fill", "#3b82f6")
      .style("stroke", "#fff")
      .style("stroke-width", 2)
      .style("opacity", 0.9);

    g.append("text")
      .attr("x", xScale(targetRiskValue))
      .attr("y", yScale(targetReturnValue) - 12)
      .attr("text-anchor", "middle")
      .style("fill", "#3b82f6")
      .style("font-size", "11px")
      .style("font-weight", "bold")
      .text("Target");

    // Add axes
    const xAxis = d3.axisBottom(xScale).tickFormat(d => `${d}%`);
    const yAxis = d3.axisLeft(yScale).tickFormat(d => `${d}%`);

    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis)
      .selectAll("text")
      .style("fill", "rgba(255,255,255,0.7)");

    g.append("g")
      .call(yAxis)
      .selectAll("text")
      .style("fill", "rgba(255,255,255,0.7)");

    // Add axis labels
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left)
      .attr("x", 0 - (height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .style("fill", "rgba(255,255,255,0.7)")
      .style("font-size", "14px")
      .text("Expected Return (%)");

    g.append("text")
      .attr("transform", `translate(${width / 2}, ${height + margin.bottom - 5})`)
      .style("text-anchor", "middle")
      .style("fill", "rgba(255,255,255,0.7)")
      .style("font-size", "14px")
      .text("Risk (Volatility %)");

  }, [frontierData, currentPortfolio, targetRisk, targetReturn, dimensions]);

  const handleRiskChange = (value: number[]) => {
    setTargetRisk(value);
    onRiskReturnChange?.(value[0], targetReturn[0]);
  };

  const handleReturnChange = (value: number[]) => {
    setTargetReturn(value);
    onRiskReturnChange?.(targetRisk[0], value[0]);
  };

  const findOptimalPortfolio = () => {
    const optimal = frontierData.reduce((best, current) => 
      current.sharpeRatio > best.sharpeRatio ? current : best
    );
    setSelectedPoint(optimal);
    onPointSelect?.(optimal);
  };

  return (
    <Card id={id} className={`glass border-white/10 ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          Efficient Frontier
        </CardTitle>
        <CardDescription>
          Optimal risk-return combinations for your portfolio
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Risk/Return Controls */}
        <div id="risk-return-controls" className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div id="risk-slider-container" className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Target Risk: {targetRisk[0]}%
            </label>
            <Slider
              id="risk-slider"
              value={targetRisk}
              onValueChange={handleRiskChange}
              max={30}
              min={5}
              step={0.5}
              className="w-full"
            />
          </div>
          
          <div id="return-slider-container" className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Target className="w-4 h-4" />
              Target Return: {targetReturn[0]}%
            </label>
            <Slider
              id="return-slider"
              value={targetReturn}
              onValueChange={handleReturnChange}
              max={15}
              min={3}
              step={0.1}
              className="w-full"
            />
          </div>
        </div>

        {/* Chart */}
        <div id="efficient-frontier-chart" className="w-full">
          <svg
            ref={svgRef}
            width={dimensions.width}
            height={dimensions.height}
            style={{ background: 'transparent' }}
          />
        </div>

        {/* Selected Point Info */}
        {selectedPoint && (
          <div id="selected-point-info" className="p-4 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold">Selected Portfolio</h4>
              <Badge variant="secondary" className="bg-primary/20 text-primary border-primary/30">
                Sharpe: {selectedPoint.sharpeRatio.toFixed(2)}
              </Badge>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Expected Return</p>
                <p className="font-semibold text-success">{selectedPoint.return.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Risk (Volatility)</p>
                <p className="font-semibold text-warning">{selectedPoint.risk.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div id="frontier-actions" className="flex gap-2">
          <Button
            id="find-optimal-btn"
            variant="outline"
            size="sm"
            onClick={findOptimalPortfolio}
            className="glass border-white/20"
          >
            <Target className="w-4 h-4 mr-2" />
            Find Optimal
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default EfficientFrontier;