"use client";

import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PortfolioAllocation } from '@/types';
import { formatPercent } from '@/lib/utils';

interface PortfolioAllocationChartProps {
  allocation: PortfolioAllocation;
}

const COLORS = {
  stocks: '#10b981',      // green
  bonds: '#3b82f6',       // blue
  international: '#8b5cf6', // purple
  realEstate: '#f59e0b',  // amber
  commodities: '#ef4444', // red
  cash: '#6b7280',        // gray
};

const ASSET_LABELS = {
  stocks: 'US Stocks',
  bonds: 'Bonds',
  international: 'International',
  realEstate: 'Real Estate',
  commodities: 'Commodities',
  cash: 'Cash',
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="bg-white dark:bg-gray-800 p-3 border rounded-lg shadow-lg">
        <p className="font-semibold">{data.payload.name}</p>
        <p className="text-sm" style={{ color: data.color }}>
          {`${formatPercent(data.value)}`}
        </p>
      </div>
    );
  }
  return null;
};

const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
  if (percent < 0.05) return null; // Don't show labels for very small slices
  
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="font-semibold text-sm"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export default function PortfolioAllocationChart({ allocation }: PortfolioAllocationChartProps) {
  // Convert allocation object to array for chart
  const chartData = Object.entries(allocation)
    .filter(([_, value]) => value > 0)
    .map(([key, value]) => ({
      name: ASSET_LABELS[key as keyof PortfolioAllocation],
      value: value,
      color: COLORS[key as keyof PortfolioAllocation],
    }))
    .sort((a, b) => b.value - a.value);

  // Calculate risk metrics
  const getRiskLevel = () => {
    const stockPercent = allocation.stocks + allocation.international;
    if (stockPercent >= 80) return { level: 'Aggressive', color: 'text-red-600' };
    if (stockPercent >= 60) return { level: 'Moderate-Aggressive', color: 'text-orange-600' };
    if (stockPercent >= 40) return { level: 'Moderate', color: 'text-yellow-600' };
    if (stockPercent >= 20) return { level: 'Conservative', color: 'text-blue-600' };
    return { level: 'Very Conservative', color: 'text-gray-600' };
  };

  const riskLevel = getRiskLevel();

  return (
    <Card id="portfolio-allocation-chart-card">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>Recommended Portfolio Allocation</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Diversified allocation based on your risk profile
            </p>
          </div>
          <div className="text-right">
            <div className={`text-lg font-semibold ${riskLevel.color}`}>
              {riskLevel.level}
            </div>
            <p className="text-sm text-muted-foreground">
              Risk Profile
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pie Chart */}
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={CustomLabel}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Allocation Details */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Allocation Breakdown</h3>
            <div className="space-y-3">
              {chartData.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: item.color }}
                    ></div>
                    <span className="font-medium">{item.name}</span>
                  </div>
                  <span className="font-semibold">
                    {formatPercent(item.value)}
                  </span>
                </div>
              ))}
            </div>

            {/* Risk Characteristics */}
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h4 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Portfolio Characteristics
              </h4>
              <div className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                <div className="flex justify-between">
                  <span>Equity Allocation:</span>
                  <span className="font-medium">
                    {formatPercent(allocation.stocks + allocation.international)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Fixed Income:</span>
                  <span className="font-medium">
                    {formatPercent(allocation.bonds)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Alternative Assets:</span>
                  <span className="font-medium">
                    {formatPercent(allocation.realEstate + allocation.commodities)}
                  </span>
                </div>
                {allocation.cash > 0 && (
                  <div className="flex justify-between">
                    <span>Cash Position:</span>
                    <span className="font-medium">
                      {formatPercent(allocation.cash)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}