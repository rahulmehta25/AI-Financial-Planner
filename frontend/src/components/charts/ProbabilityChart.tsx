"use client";

import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatPercent } from '@/lib/utils';

interface ProbabilityChartProps {
  data: Array<{
    year: number;
    median: number;
    percentile10: number;
    percentile90: number;
    targetIncome: number;
  }>;
  probabilityOfSuccess: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 p-3 border rounded-lg shadow-lg">
        <p className="font-semibold">{`Year: ${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {`${entry.name}: ${formatCurrency(entry.value)}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function ProbabilityChart({ data, probabilityOfSuccess }: ProbabilityChartProps) {
  const getSuccessColor = (probability: number) => {
    if (probability >= 80) return 'text-green-600';
    if (probability >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSuccessMessage = (probability: number) => {
    if (probability >= 90) return 'Excellent probability of meeting your goals';
    if (probability >= 80) return 'Very good probability of meeting your goals';
    if (probability >= 70) return 'Good probability of meeting your goals';
    if (probability >= 60) return 'Moderate probability of meeting your goals';
    if (probability >= 40) return 'Some risk of not meeting your goals';
    return 'High risk of not meeting your goals';
  };

  return (
    <Card id="probability-chart-card">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle>Probability of Success</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Monte Carlo simulation showing potential outcomes
            </p>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${getSuccessColor(probabilityOfSuccess)}`}>
              {formatPercent(probabilityOfSuccess)}
            </div>
            <p className="text-sm text-muted-foreground">
              Success Rate
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <div className={`p-3 rounded-lg ${probabilityOfSuccess >= 70 ? 'bg-green-50 dark:bg-green-900/20' : probabilityOfSuccess >= 40 ? 'bg-yellow-50 dark:bg-yellow-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}>
            <p className={`text-sm font-medium ${getSuccessColor(probabilityOfSuccess)}`}>
              {getSuccessMessage(probabilityOfSuccess)}
            </p>
          </div>
        </div>

        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis 
                dataKey="year" 
                stroke="#666"
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="#666"
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* 10th-90th percentile range */}
              <Area
                type="monotone"
                dataKey="percentile90"
                stackId="1"
                stroke="transparent"
                fill="#dbeafe"
                fillOpacity={0.6}
                name="90th Percentile"
              />
              <Area
                type="monotone"
                dataKey="percentile10"
                stackId="1"
                stroke="transparent"
                fill="#ffffff"
                fillOpacity={1}
                name="10th Percentile"
              />
              
              {/* Median line */}
              <Area
                type="monotone"
                dataKey="median"
                stroke="#3b82f6"
                strokeWidth={3}
                fill="transparent"
                name="Median Outcome"
                dot={{ r: 0 }}
                activeDot={{ r: 4, fill: '#3b82f6' }}
              />
              
              {/* Target income line */}
              <Area
                type="monotone"
                dataKey="targetIncome"
                stroke="#ef4444"
                strokeWidth={2}
                strokeDasharray="5 5"
                fill="transparent"
                name="Target Income Need"
                dot={{ r: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-200 rounded"></div>
            <span>10th - 90th Percentile Range</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-blue-500"></div>
            <span>Median Outcome</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-red-500 border-dashed border-t-2 border-red-500"></div>
            <span>Target Income Need</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}