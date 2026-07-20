import React, { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Sector } from "recharts";

const ALLOCATION_DATA = [
  { name: "US Equities",    value: 42, color: "#1a7dff" },
  { name: "Int'l Equities", value: 18, color: "#7c3aed" },
  { name: "Bonds",          value: 20, color: "#f9b820" },
  { name: "Real Estate",    value: 10, color: "#10d077" },
  { name: "Alternatives",   value: 6,  color: "#06b6d4" },
  { name: "Cash",           value: 4,  color: "#64748b" },
];

const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
  return (
    <g>
      <text x={cx} y={cy - 10} textAnchor="middle" fill="#dde4ee" className="text-sm" fontSize={13} fontWeight={600}>
        {payload.name}
      </text>
      <text x={cx} y={cy + 10} textAnchor="middle" fill="#dde4ee" fontSize={20} fontWeight={700}>
        {value}%
      </text>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius + 8} startAngle={startAngle} endAngle={endAngle} fill={fill} />
      <Sector cx={cx} cy={cy} innerRadius={outerRadius + 10} outerRadius={outerRadius + 14} startAngle={startAngle} endAngle={endAngle} fill={fill} opacity={0.4} />
    </g>
  );
};

const AssetAllocationDonut: React.FC = () => {
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <div id="asset-allocation-card" className="metric-card metric-card-gold">
      <div id="asset-allocation-header" className="mb-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Asset Allocation</p>
        <h3 className="text-lg font-bold text-foreground">Portfolio Mix</h3>
      </div>

      {/* Donut chart */}
      <div id="asset-allocation-chart" className="h-44 -mx-2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              activeIndex={activeIndex}
              activeShape={renderActiveShape}
              data={ALLOCATION_DATA}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={72}
              dataKey="value"
              onMouseEnter={(_, index) => setActiveIndex(index)}
            >
              {ALLOCATION_DATA.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div id="asset-allocation-legend" className="grid grid-cols-2 gap-x-4 gap-y-2 mt-2">
        {ALLOCATION_DATA.map((entry, i) => (
          <button
            key={entry.name}
            id={`allocation-item-${i}`}
            className="flex items-center gap-2 text-left group hover:opacity-80 transition-opacity"
            onMouseEnter={() => setActiveIndex(i)}
          >
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: entry.color }} />
            <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors truncate">{entry.name}</span>
            <span className="text-xs font-semibold text-foreground ml-auto">{entry.value}%</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AssetAllocationDonut;
