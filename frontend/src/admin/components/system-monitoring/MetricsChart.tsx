"use client";

import React from 'react';
import { Card } from '@/components/ui/card';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

interface MetricsChartProps {
  title: string;
  data: ChartDataPoint[];
  type: 'bar' | 'line';
  height?: number;
}

/**
 * MetricsChart Component
 * 
 * Features:
 * - Bar and line chart support
 * - Responsive design
 * - Custom colors
 * - Tooltips
 */
export const MetricsChart: React.FC<MetricsChartProps> = ({
  title,
  data,
  type,
  height = 300,
}) => {
  const formatValue = (value: number) => {
    if (title.toLowerCase().includes('response') || title.toLowerCase().includes('time')) {
      return `${value.toFixed(0)}ms`;
    }
    if (title.toLowerCase().includes('performance')) {
      return `${value.toFixed(1)}%`;
    }
    return value.toString();
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 dark:text-white">{label}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Value: <span className="font-medium">{formatValue(payload[0].value)}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card id={`metrics-chart-${title.toLowerCase().replace(/\s+/g, '-')}`} className="p-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">{title}</h3>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          {type === 'bar' ? (
            <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="name" 
                className="text-xs"
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                className="text-xs"
                tick={{ fontSize: 12 }}
                tickFormatter={formatValue}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="value" 
                fill="#3B82F6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          ) : (
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="name" 
                className="text-xs"
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                className="text-xs"
                tick={{ fontSize: 12 }}
                tickFormatter={formatValue}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3B82F6" 
                strokeWidth={2}
                dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
      
      {/* Data Summary */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400">Min</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {formatValue(Math.min(...data.map(d => d.value)))}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400">Avg</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {formatValue(data.reduce((sum, d) => sum + d.value, 0) / data.length)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400">Max</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {formatValue(Math.max(...data.map(d => d.value)))}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};