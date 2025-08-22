"use client";

import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TradeOffScenario } from '@/types';
import { formatPercent, formatCurrency } from '@/lib/utils';
import { TrendingUp, TrendingDown, Calendar, DollarSign } from 'lucide-react';

interface TradeOffChartProps {
  scenarios: TradeOffScenario[];
  baselineProbability: number;
  onScenarioSelect?: (scenario: TradeOffScenario) => void;
}

const SCENARIO_ICONS = {
  save_more: DollarSign,
  retire_later: Calendar,
  spend_less: TrendingDown,
};

const SCENARIO_COLORS = {
  save_more: '#10b981',      // green
  retire_later: '#3b82f6',   // blue
  spend_less: '#f59e0b',     // amber
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-gray-800 p-4 border rounded-lg shadow-lg max-w-sm">
        <p className="font-semibold mb-2">{data.title}</p>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          {data.description}
        </p>
        <div className="space-y-1">
          <p className="text-sm">
            <span className="font-medium">Original:</span> {formatCurrency(data.originalValue)}
          </p>
          <p className="text-sm">
            <span className="font-medium">Adjusted:</span> {formatCurrency(data.adjustedValue)}
          </p>
          <p className="text-sm">
            <span className="font-medium">Success Rate:</span> 
            <span style={{ color: payload[0].color }}>
              {' '}{formatPercent(data.impactOnSuccess)}
            </span>
          </p>
        </div>
      </div>
    );
  }
  return null;
};

export default function TradeOffChart({ 
  scenarios, 
  baselineProbability, 
  onScenarioSelect 
}: TradeOffChartProps) {
  const chartData = scenarios.map(scenario => ({
    ...scenario,
    color: SCENARIO_COLORS[scenario.type],
    improvement: scenario.impactOnSuccess - baselineProbability,
  }));

  const ScenarioCard = ({ scenario }: { scenario: TradeOffScenario }) => {
    const Icon = SCENARIO_ICONS[scenario.type];
    const improvement = scenario.impactOnSuccess - baselineProbability;
    const isPositive = improvement > 0;

    return (
      <Card className="cursor-pointer hover:shadow-lg transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <div
                className="p-2 rounded-lg"
                style={{ backgroundColor: `${SCENARIO_COLORS[scenario.type]}20` }}
              >
                <Icon 
                  className="w-4 h-4" 
                  style={{ color: SCENARIO_COLORS[scenario.type] }}
                />
              </div>
              <h3 className="font-semibold text-sm">{scenario.title}</h3>
            </div>
            <div className="text-right">
              <div className={`text-lg font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '+' : ''}{formatPercent(improvement)}
              </div>
              <p className="text-xs text-muted-foreground">Improvement</p>
            </div>
          </div>
          
          <p className="text-sm text-muted-foreground mb-3">
            {scenario.description}
          </p>
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <p className="text-muted-foreground">From:</p>
              <p className="font-medium">{formatCurrency(scenario.originalValue)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">To:</p>
              <p className="font-medium">{formatCurrency(scenario.adjustedValue)}</p>
            </div>
          </div>
          
          <div className="mt-3">
            <p className="text-xs text-muted-foreground mb-1">New Success Rate:</p>
            <div className="flex items-center justify-between">
              <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
                <div
                  className="h-2 rounded-full"
                  style={{ 
                    width: `${Math.min(scenario.impactOnSuccess, 100)}%`,
                    backgroundColor: SCENARIO_COLORS[scenario.type]
                  }}
                />
              </div>
              <span className="font-semibold text-sm">
                {formatPercent(scenario.impactOnSuccess)}
              </span>
            </div>
          </div>

          {scenario.recommendation && (
            <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
              <p className="text-xs text-blue-800 dark:text-blue-200">
                <span className="font-medium">Tip:</span> {scenario.recommendation}
              </p>
            </div>
          )}
          
          {onScenarioSelect && (
            <Button
              onClick={() => onScenarioSelect(scenario)}
              className="w-full mt-3"
              variant="outline"
              size="sm"
            >
              Apply This Scenario
            </Button>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div id="trade-off-scenarios" className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Trade-Off Scenarios
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Explore how different adjustments could improve your probability of success
          </p>
        </CardHeader>
        <CardContent>
          {/* Current Baseline */}
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">Current Plan</h3>
                <p className="text-sm text-muted-foreground">Your baseline probability of success</p>
              </div>
              <div className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                {formatPercent(baselineProbability)}
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="h-64 mb-6">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis 
                  dataKey="title" 
                  stroke="#666"
                  fontSize={12}
                  tickLine={false}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  stroke="#666"
                  fontSize={12}
                  tickLine={false}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="impactOnSuccess" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Scenario Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scenarios.map((scenario, index) => (
              <ScenarioCard key={index} scenario={scenario} />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}