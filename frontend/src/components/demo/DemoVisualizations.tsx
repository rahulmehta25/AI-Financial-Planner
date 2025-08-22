"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { TrendingUp, TrendingDown, Target, AlertTriangle, CheckCircle } from 'lucide-react';

interface DemoVisualizationsProps {
  profile: string;
  data: any;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

export function MonteCarloSimulationChart({ data }: { data: any }) {
  const [animationProgress, setAnimationProgress] = useState(0);
  
  useEffect(() => {
    const timer = setTimeout(() => setAnimationProgress(100), 500);
    return () => clearTimeout(timer);
  }, []);

  const simulationData = Array.from({ length: 30 }, (_, i) => {
    const year = new Date().getFullYear() + i;
    const baseValue = data.profile.currentSavings * Math.pow(1.068, i);
    return {
      year,
      optimistic: baseValue * 1.3,
      realistic: baseValue,
      pessimistic: baseValue * 0.7,
      median: baseValue,
    };
  });

  return (
    <Card id="monte-carlo-chart" className="col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Monte Carlo Simulation Results
          </CardTitle>
          <Badge className="bg-blue-100 text-blue-800">
            10,000 Scenarios
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={simulationData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="year" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `'${value.toString().slice(-2)}`}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip
                formatter={(value: number, name: string) => [
                  formatCurrency(value),
                  name.charAt(0).toUpperCase() + name.slice(1)
                ]}
                labelFormatter={(label) => `Year ${label}`}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                }}
              />
              <Area
                type="monotone"
                dataKey="optimistic"
                stackId="1"
                stroke="#10B981"
                fill="#10B981"
                fillOpacity={0.1}
                strokeWidth={1}
              />
              <Area
                type="monotone"
                dataKey="pessimistic"
                stackId="2"
                stroke="#EF4444"
                fill="#EF4444"
                fillOpacity={0.1}
                strokeWidth={1}
              />
              <Line
                type="monotone"
                dataKey="realistic"
                stroke="#3B82F6"
                strokeWidth={3}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="text-lg font-bold text-green-700 dark:text-green-300">
              {data.simulation.scenarios.optimistic.probability}%
            </div>
            <div className="text-sm text-green-600 dark:text-green-400">Optimistic</div>
          </div>
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="text-lg font-bold text-blue-700 dark:text-blue-300">
              {data.simulation.scenarios.realistic.probability}%
            </div>
            <div className="text-sm text-blue-600 dark:text-blue-400">Realistic</div>
          </div>
          <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <div className="text-lg font-bold text-red-700 dark:text-red-300">
              {data.simulation.scenarios.pessimistic.probability}%
            </div>
            <div className="text-sm text-red-600 dark:text-red-400">Pessimistic</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function PortfolioAllocationChart({ data }: { data: any }) {
  const portfolioData = [
    { name: 'Domestic Equity', value: data.portfolio.breakdown.domesticEquity, color: '#3B82F6' },
    { name: 'International Equity', value: data.portfolio.breakdown.internationalEquity, color: '#10B981' },
    { name: 'Bond Index', value: data.portfolio.breakdown.bondIndex, color: '#F59E0B' },
    { name: 'Real Estate', value: data.portfolio.breakdown.realEstate, color: '#EF4444' },
    { name: 'Cash', value: data.portfolio.breakdown.cash, color: '#8B5CF6' }
  ];

  return (
    <Card id="portfolio-chart" className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="w-5 h-5 text-green-600" />
          Portfolio Allocation
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={portfolioData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${value}%`}
                labelLine={false}
              >
                {portfolioData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, name: string) => [`${value}%`, name]}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        <div className="space-y-2 mt-4">
          {portfolioData.map((item, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm">{item.name}</span>
              </div>
              <span className="text-sm font-medium">{item.value}%</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function GoalProgressChart({ data }: { data: any }) {
  return (
    <Card id="goals-section" className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="w-5 h-5 text-purple-600" />
          Goal Progress Tracking
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {data.goals.map((goal: any, index: number) => {
            const progressPercent = (goal.currentAmount / goal.targetAmount) * 100;
            const isOnTrack = progressPercent >= 50;
            
            return (
              <motion.div
                key={goal.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {isOnTrack ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-yellow-500" />
                    )}
                    <div>
                      <h3 className="font-medium">{goal.title}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Target: {formatCurrency(goal.targetAmount)} by {new Date(goal.targetDate).getFullYear()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(goal.currentAmount)}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {progressPercent.toFixed(0)}% complete
                    </div>
                  </div>
                </div>
                
                <Progress value={progressPercent} className="h-2" />
                
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>Monthly: {formatCurrency(goal.monthlyContribution)}</span>
                  <span className={isOnTrack ? 'text-green-600' : 'text-yellow-600'}>
                    {isOnTrack ? 'On Track' : 'Needs Attention'}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export function RiskAnalysisChart({ data }: { data: any }) {
  const riskData = [
    { name: 'Volatility', value: data.simulation.riskMetrics.volatility, target: 15, color: '#EF4444' },
    { name: 'Sharpe Ratio', value: data.simulation.riskMetrics.sharpeRatio * 10, target: 12, color: '#10B981' },
    { name: 'Beta', value: data.simulation.riskMetrics.beta * 20, target: 20, color: '#3B82F6' },
    { name: 'Max Drawdown', value: Math.abs(data.simulation.riskMetrics.maxDrawdown), target: 20, color: '#F59E0B' }
  ];

  return (
    <Card id="risk-analysis" className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-600" />
          Risk Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={riskData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 12 }}
                interval={0}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  name === 'Sharpe Ratio' ? (value / 10).toFixed(2) :
                  name === 'Beta' ? (value / 20).toFixed(2) :
                  `${value.toFixed(1)}%`,
                  name
                ]}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {riskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Overall Risk Score</span>
            <Badge className="bg-orange-100 text-orange-800">
              Moderate
            </Badge>
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400">
            Based on portfolio volatility and risk metrics
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function MarketIntelligenceChart({ data }: { data: any }) {
  return (
    <Card id="market-intelligence" className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          Market Intelligence
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.marketData.historical.slice(-30)}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                domain={['dataMin - 5', 'dataMax + 5']}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Portfolio Value']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#3B82F6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mt-4">
          {data.marketData.sectors.slice(0, 3).map((sector: any, index: number) => (
            <div key={index} className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="font-medium text-sm">{sector.name}</div>
              <div className={`text-lg font-bold ${
                sector.change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {sector.change >= 0 ? '+' : ''}{sector.change}%
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                {sector.allocation}% allocation
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function DemoVisualizations({ profile, data }: DemoVisualizationsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <MonteCarloSimulationChart data={data} />
      <PortfolioAllocationChart data={data} />
      <GoalProgressChart data={data} />
      <RiskAnalysisChart data={data} />
      <MarketIntelligenceChart data={data} />
    </div>
  );
}