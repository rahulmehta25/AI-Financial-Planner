import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
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

interface D3EfficientFrontierProps {
  id?: string;
  portfolioData?: PortfolioPoint[];
  currentPortfolio?: PortfolioPoint;
  onPointSelect?: (portfolio: PortfolioPoint) => void;
  onRiskReturnChange?: (risk: number, expectedReturn: number) => void;
}

export const D3EfficientFrontier: React.FC<D3EfficientFrontierProps> = ({
  id = "efficient-frontier",
  portfolioData = [],
  currentPortfolio,
  onPointSelect,
  onRiskReturnChange,
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
        risk,
        return: expectedReturn,
        sharpeRatio,
        volatility: risk,
        expectedReturn
      });
    }
    return points.sort((a, b) => a.risk - b.risk);
  };

  const data = portfolioData.length > 0 ? portfolioData : generateMockData();

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current) {
        const rect = svgRef.current.parentElement?.getBoundingClientRect();
        if (rect) {
          setDimensions({
            width: Math.max(400, rect.width - 20),
            height: 400
          });
        }
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // D3 Scatter Plot Implementation
  useEffect(() => {
    if (!svgRef.current || dimensions.width === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = { top: 20, right: 60, bottom: 60, left: 60 };
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = d3
      .scaleLinear()
      .domain(d3.extent(data, (d) => d.risk) as [number, number])
      .range([0, width])
      .nice();

    const yScale = d3
      .scaleLinear()
      .domain(d3.extent(data, (d) => d.expectedReturn) as [number, number])
      .range([height, 0])
      .nice();

    const colorScale = d3
      .scaleSequential(d3.interpolateViridis)
      .domain(d3.extent(data, (d) => d.sharpeRatio) as [number, number]);

    // Axes
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .append("text")
      .attr("x", width / 2)
      .attr("y", 40)
      .attr("fill", "black")
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .text("Risk (Volatility %)");

    g.append("g")
      .call(d3.axisLeft(yScale))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -40)
      .attr("x", -height / 2)
      .attr("fill", "black")
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .text("Expected Return (%)");

    // Grid lines
    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(
        d3
          .axisBottom(xScale)
          .tickSize(-height)
          .tickFormat(() => "")
      )
      .style("stroke-dasharray", "3,3")
      .style("opacity", 0.3);

    g.append("g")
      .attr("class", "grid")
      .call(
        d3
          .axisLeft(yScale)
          .tickSize(-width)
          .tickFormat(() => "")
      )
      .style("stroke-dasharray", "3,3")
      .style("opacity", 0.3);

    // Efficient frontier line
    const line = d3
      .line<PortfolioPoint>()
      .x((d) => xScale(d.risk))
      .y((d) => yScale(d.expectedReturn))
      .curve(d3.curveCatmullRom);

    g.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 3)
      .attr("d", line);

    // Data points
    const circles = g
      .selectAll(".point")
      .data(data)
      .enter()
      .append("circle")
      .attr("class", "point")
      .attr("cx", (d) => xScale(d.risk))
      .attr("cy", (d) => yScale(d.expectedReturn))
      .attr("r", 4)
      .attr("fill", (d) => colorScale(d.sharpeRatio))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1)
      .style("cursor", "pointer");

    // Interactions
    circles
      .on("mouseover", function (event, d) {
        d3.select(this).attr("r", 6);
        
        // Tooltip
        const tooltip = g
          .append("g")
          .attr("class", "tooltip")
          .attr("transform", `translate(${xScale(d.risk)},${yScale(d.expectedReturn)})`);

        const rect = tooltip
          .append("rect")
          .attr("x", 10)
          .attr("y", -30)
          .attr("width", 140)
          .attr("height", 50)
          .attr("fill", "white")
          .attr("stroke", "#ccc")
          .attr("stroke-width", 1)
          .attr("rx", 4);

        tooltip
          .append("text")
          .attr("x", 15)
          .attr("y", -10)
          .style("font-size", "11px")
          .style("font-weight", "600")
          .text(`Risk: ${d.risk.toFixed(1)}%`);

        tooltip
          .append("text")
          .attr("x", 15)
          .attr("y", 5)
          .style("font-size", "11px")
          .style("font-weight", "600")
          .text(`Return: ${d.expectedReturn.toFixed(1)}%`);

        tooltip
          .append("text")
          .attr("x", 15)
          .attr("y", 20)
          .style("font-size", "11px")
          .style("font-weight", "600")
          .text(`Sharpe: ${d.sharpeRatio.toFixed(2)}`);
      })
      .on("mouseout", function () {
        d3.select(this).attr("r", 4);
        g.selectAll(".tooltip").remove();
      })
      .on("click", function (event, d) {
        setSelectedPoint(d);
        onPointSelect?.(d);
        
        // Highlight selected point
        circles.attr("stroke-width", 1);
        d3.select(this).attr("stroke-width", 3).attr("stroke", "#ef4444");
      });

    // Current portfolio marker
    if (currentPortfolio) {
      g.append("circle")
        .attr("cx", xScale(currentPortfolio.risk))
        .attr("cy", yScale(currentPortfolio.expectedReturn))
        .attr("r", 8)
        .attr("fill", "none")
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 3);

      g.append("text")
        .attr("x", xScale(currentPortfolio.risk))
        .attr("y", yScale(currentPortfolio.expectedReturn) - 15)
        .attr("text-anchor", "middle")
        .style("font-size", "11px")
        .style("font-weight", "600")
        .style("fill", "#ef4444")
        .text("Current");
    }

    // Target risk/return crosshairs
    if (targetRisk[0] && targetReturn[0]) {
      g.append("line")
        .attr("x1", xScale(targetRisk[0]))
        .attr("x2", xScale(targetRisk[0]))
        .attr("y1", 0)
        .attr("y2", height)
        .attr("stroke", "#10b981")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "5,5")
        .style("opacity", 0.7);

      g.append("line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", yScale(targetReturn[0]))
        .attr("y2", yScale(targetReturn[0]))
        .attr("stroke", "#10b981")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "5,5")
        .style("opacity", 0.7);
    }

  }, [data, dimensions, currentPortfolio, selectedPoint, targetRisk, targetReturn]);

  const handleRiskChange = (value: number[]) => {
    setTargetRisk(value);
    onRiskReturnChange?.(value[0], targetReturn[0]);
  };

  const handleReturnChange = (value: number[]) => {
    setTargetReturn(value);
    onRiskReturnChange?.(targetRisk[0], value[0]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="h-5 w-5" />
        <span className="font-medium">Efficient Frontier</span>
        {selectedPoint && (
          <Badge variant="outline">
            Sharpe Ratio: {selectedPoint.sharpeRatio.toFixed(2)}
          </Badge>
        )}
      </div>

      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full border rounded-lg"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            <span className="text-sm font-medium">Target Risk</span>
            <Badge variant="outline">{targetRisk[0]}%</Badge>
          </div>
          <Slider
            value={targetRisk}
            onValueChange={handleRiskChange}
            max={30}
            min={5}
            step={0.5}
            className="w-full"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            <span className="text-sm font-medium">Target Return</span>
            <Badge variant="outline">{targetReturn[0]}%</Badge>
          </div>
          <Slider
            value={targetReturn}
            onValueChange={handleReturnChange}
            max={15}
            min={3}
            step={0.1}
            className="w-full"
          />
        </div>
      </div>

      {selectedPoint && (
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium mb-2">Selected Portfolio</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Risk:</span>
              <div className="font-semibold">{selectedPoint.risk.toFixed(1)}%</div>
            </div>
            <div>
              <span className="text-muted-foreground">Return:</span>
              <div className="font-semibold">{selectedPoint.expectedReturn.toFixed(1)}%</div>
            </div>
            <div>
              <span className="text-muted-foreground">Sharpe Ratio:</span>
              <div className="font-semibold">{selectedPoint.sharpeRatio.toFixed(2)}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Volatility:</span>
              <div className="font-semibold">{selectedPoint.volatility.toFixed(1)}%</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};