"use client";

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Activity, Pause, Play } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { SystemMetrics } from '../../types';

interface RealTimeMetricsProps {
  metrics: SystemMetrics;
  history: Record<string, any[]>;
}

interface MetricDataPoint {
  timestamp: string;
  value: number;
}

/**
 * RealTimeMetrics Component
 * 
 * Features:
 * - Live updating charts
 * - Multiple metric streams
 * - Pause/resume functionality
 * - Historical data display
 */
export const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({
  metrics,
  history,
}) => {
  const [isPaused, setIsPaused] = useState(false);
  const [timeRange, setTimeRange] = useState<'1m' | '5m' | '15m' | '1h'>('5m');
  const [metricHistory, setMetricHistory] = useState<Record<string, MetricDataPoint[]>>({
    cpu: [],
    memory: [],
    requests: [],
    responseTime: [],
  });

  // Update metrics history
  useEffect(() => {
    if (!isPaused && metrics) {
      const timestamp = new Date().toLocaleTimeString();
      
      setMetricHistory(prev => {
        const newHistory = { ...prev };
        const maxPoints = getMaxPoints(timeRange);
        
        // Add new data points
        newHistory.cpu = addDataPoint(prev.cpu, { timestamp, value: metrics.server.cpuUsage }, maxPoints);
        newHistory.memory = addDataPoint(prev.memory, { timestamp, value: metrics.server.memoryUsage }, maxPoints);
        newHistory.requests = addDataPoint(prev.requests, { timestamp, value: metrics.api.requestsPerSecond }, maxPoints);
        newHistory.responseTime = addDataPoint(prev.responseTime, { timestamp, value: metrics.api.averageResponseTime }, maxPoints);
        
        return newHistory;
      });
    }
  }, [metrics, isPaused, timeRange]);

  const addDataPoint = (
    currentData: MetricDataPoint[], 
    newPoint: MetricDataPoint, 
    maxPoints: number
  ): MetricDataPoint[] => {
    const updated = [...currentData, newPoint];
    return updated.slice(-maxPoints);
  };

  const getMaxPoints = (range: string): number => {
    switch (range) {
      case '1m': return 12; // 5s intervals
      case '5m': return 30; // 10s intervals  
      case '15m': return 45; // 20s intervals
      case '1h': return 60; // 1m intervals
      default: return 30;
    }
  };

  const formatValue = (value: number, type: 'percentage' | 'number' | 'time') => {
    switch (type) {
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'time':
        return `${value.toFixed(0)}ms`;
      case 'number':
      default:
        return value.toFixed(1);
    }
  };

  const getStatusColor = (value: number, thresholds: { warning: number; critical: number }, type: 'percentage' | 'number' | 'time' = 'percentage') => {
    if (value >= thresholds.critical) return 'text-red-600 dark:text-red-400';
    if (value >= thresholds.warning) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 dark:text-white">{label}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Value: <span className="font-medium">{payload[0].value.toFixed(2)}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  const chartConfig = [
    {
      key: 'cpu',
      title: 'CPU Usage',
      data: metricHistory.cpu,
      color: '#EF4444',
      suffix: '%',
      thresholds: { warning: 70, critical: 90 },
    },
    {
      key: 'memory',
      title: 'Memory Usage',
      data: metricHistory.memory,
      color: '#F59E0B',
      suffix: '%',
      thresholds: { warning: 80, critical: 95 },
    },
    {
      key: 'requests',
      title: 'Requests/sec',
      data: metricHistory.requests,
      color: '#10B981',
      suffix: '',
      thresholds: { warning: 100, critical: 200 },
    },
    {
      key: 'responseTime',
      title: 'Response Time',
      data: metricHistory.responseTime,
      color: '#3B82F6',
      suffix: 'ms',
      thresholds: { warning: 500, critical: 1000 },
    },
  ];

  return (
    <Card id="real-time-metrics" className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Activity className={`h-5 w-5 ${isPaused ? 'text-gray-400' : 'text-green-600 animate-pulse'}`} />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Real-time Metrics
          </h3>
          <Badge variant={isPaused ? 'secondary' : 'default'} className="ml-2">
            {isPaused ? 'Paused' : 'Live'}
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Time Range Selector */}
          <div className="flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden">
            {(['1m', '5m', '15m', '1h'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 text-xs font-medium transition-colors ${
                  timeRange === range
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
          
          {/* Pause/Resume Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsPaused(!isPaused)}
            className="flex items-center gap-2"
          >
            {isPaused ? (
              <>
                <Play className="h-4 w-4" />
                Resume
              </>
            ) : (
              <>
                <Pause className="h-4 w-4" />
                Pause
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Current Values */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">CPU Usage</p>
          <p className={`text-xl font-bold ${getStatusColor(metrics.server.cpuUsage, { warning: 70, critical: 90 })}`}>
            {formatValue(metrics.server.cpuUsage, 'percentage')}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Memory</p>
          <p className={`text-xl font-bold ${getStatusColor(metrics.server.memoryUsage, { warning: 80, critical: 95 })}`}>
            {formatValue(metrics.server.memoryUsage, 'percentage')}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Requests/sec</p>
          <p className={`text-xl font-bold ${getStatusColor(metrics.api.requestsPerSecond, { warning: 100, critical: 200 }, 'number')}`}>
            {formatValue(metrics.api.requestsPerSecond, 'number')}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Response Time</p>
          <p className={`text-xl font-bold ${getStatusColor(metrics.api.averageResponseTime, { warning: 500, critical: 1000 }, 'time')}`}>
            {formatValue(metrics.api.averageResponseTime, 'time')}
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {chartConfig.map((chart) => (
          <div key={chart.key} className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                {chart.title}
              </h4>
              <div className="flex items-center gap-2">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: chart.color }}
                />
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  Last {timeRange}
                </span>
              </div>
            </div>
            
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chart.data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis 
                    dataKey="timestamp" 
                    tick={{ fontSize: 10 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis 
                    tick={{ fontSize: 10 }}
                    width={40}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke={chart.color}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: chart.color }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            {/* Chart Stats */}
            <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
              <span>
                Min: {chart.data.length > 0 ? Math.min(...chart.data.map(d => d.value)).toFixed(1) : '0'}{chart.suffix}
              </span>
              <span>
                Avg: {chart.data.length > 0 ? (chart.data.reduce((sum, d) => sum + d.value, 0) / chart.data.length).toFixed(1) : '0'}{chart.suffix}
              </span>
              <span>
                Max: {chart.data.length > 0 ? Math.max(...chart.data.map(d => d.value)).toFixed(1) : '0'}{chart.suffix}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      {/* Data Points Info */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
          <span>
            Showing last {getMaxPoints(timeRange)} data points ({timeRange} range)
          </span>
          <span>
            Updates every 5 seconds {isPaused && '(paused)'}
          </span>
        </div>
      </div>
    </Card>
  );
};