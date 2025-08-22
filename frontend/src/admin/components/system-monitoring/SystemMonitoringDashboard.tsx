"use client";

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Monitor,
  HardDrive,
  Cpu,
  MemoryStick
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useSystemMonitoring } from '../../store/adminStore';
import { MetricsChart } from './MetricsChart';
import { ServiceHealthGrid } from './ServiceHealthGrid';
import { AlertsPanel } from './AlertsPanel';
import { RealTimeMetrics } from './RealTimeMetrics';
import type { SystemMetrics, ServiceHealth } from '../../types';

/**
 * SystemMonitoringDashboard Component
 * 
 * Features:
 * - Real-time system metrics
 * - Service health monitoring
 * - Performance charts
 * - Alert management
 * - Resource usage tracking
 */
export const SystemMonitoringDashboard: React.FC = () => {
  const {
    metrics,
    serviceHealth,
    alerts,
    isRealTimeEnabled,
    lastUpdate,
    metricsHistory,
    setMetrics,
    setServiceHealth,
    addAlert,
    removeAlert,
    toggleRealTime,
    updateMetricsHistory,
    clearAlerts,
  } = useSystemMonitoring();

  const [refreshing, setRefreshing] = useState(false);

  // Mock data generation for development
  const generateMockMetrics = (): SystemMetrics => ({
    server: {
      cpuUsage: Math.random() * 100,
      memoryUsage: 60 + Math.random() * 30,
      diskUsage: 45 + Math.random() * 20,
      networkIn: Math.random() * 1000,
      networkOut: Math.random() * 800,
      uptime: 2847392, // ~33 days
      loadAverage: [1.2, 1.5, 1.8],
    },
    database: {
      connectionCount: 45 + Math.floor(Math.random() * 20),
      queryTime: 50 + Math.random() * 100,
      slowQueries: Math.floor(Math.random() * 5),
      lockWaits: Math.floor(Math.random() * 3),
      deadlocks: 0,
      cacheHitRatio: 85 + Math.random() * 10,
      tableSize: 1024 * 1024 * 500, // 500MB
      indexUsage: 90 + Math.random() * 8,
    },
    cache: {
      hitRate: 92 + Math.random() * 6,
      missRate: 2 + Math.random() * 6,
      memoryUsage: 70 + Math.random() * 20,
      evictions: Math.floor(Math.random() * 10),
      operations: 1000 + Math.floor(Math.random() * 500),
      avgResponseTime: 1 + Math.random() * 3,
    },
    api: {
      requestsPerSecond: 50 + Math.random() * 100,
      averageResponseTime: 200 + Math.random() * 300,
      errorRate: Math.random() * 2,
      status2xx: 950 + Math.floor(Math.random() * 40),
      status4xx: Math.floor(Math.random() * 30),
      status5xx: Math.floor(Math.random() * 10),
      activeConnections: 100 + Math.floor(Math.random() * 50),
      endpointStats: [
        {
          endpoint: '/api/users',
          method: 'GET',
          requests: 1250,
          avgResponseTime: 180,
          errorRate: 0.5,
          status: { '200': 1243, '404': 7 },
        },
        {
          endpoint: '/api/financial-plans',
          method: 'POST',
          requests: 834,
          avgResponseTime: 450,
          errorRate: 1.2,
          status: { '200': 824, '400': 8, '500': 2 },
        },
      ],
    },
    application: {
      activeUsers: 1250 + Math.floor(Math.random() * 200),
      sessionsCount: 890 + Math.floor(Math.random() * 100),
      featuresUsage: {
        'financial-planning': 450,
        'portfolio-analysis': 320,
        'goal-tracking': 280,
        'reports': 190,
      },
      errorCount: Math.floor(Math.random() * 5),
      warningCount: Math.floor(Math.random() * 15),
      performanceScore: 85 + Math.random() * 10,
    },
    timestamp: new Date().toISOString(),
  });

  const generateMockServiceHealth = (): ServiceHealth[] => [
    {
      service: 'API Gateway',
      status: 'healthy',
      lastCheck: new Date().toISOString(),
      responseTime: 45,
      uptime: 99.9,
      version: '1.2.3',
      dependencies: [
        { name: 'Database', status: 'healthy', responseTime: 12 },
        { name: 'Cache', status: 'healthy', responseTime: 3 },
      ],
      checks: [
        { name: 'HTTP Health', status: 'pass', message: 'All endpoints responding', timestamp: new Date().toISOString() },
        { name: 'Database Connection', status: 'pass', message: 'Connected successfully', timestamp: new Date().toISOString() },
      ],
    },
    {
      service: 'Database',
      status: 'healthy',
      lastCheck: new Date().toISOString(),
      responseTime: 12,
      uptime: 99.95,
      version: '14.2',
      dependencies: [],
      checks: [
        { name: 'Connection Pool', status: 'pass', message: '45/100 connections active', timestamp: new Date().toISOString() },
        { name: 'Disk Space', status: 'pass', message: '65% used', timestamp: new Date().toISOString() },
      ],
    },
    {
      service: 'Cache (Redis)',
      status: 'healthy',
      lastCheck: new Date().toISOString(),
      responseTime: 3,
      uptime: 99.8,
      version: '6.2',
      dependencies: [],
      checks: [
        { name: 'Memory Usage', status: 'pass', message: '2.1GB / 4GB used', timestamp: new Date().toISOString() },
        { name: 'Hit Rate', status: 'pass', message: '94.2% hit rate', timestamp: new Date().toISOString() },
      ],
    },
    {
      service: 'Background Jobs',
      status: Math.random() > 0.8 ? 'degraded' : 'healthy',
      lastCheck: new Date().toISOString(),
      responseTime: 150,
      uptime: 98.5,
      version: '2.1.0',
      dependencies: [
        { name: 'Database', status: 'healthy', responseTime: 12 },
      ],
      checks: [
        { name: 'Queue Length', status: 'pass', message: '12 jobs pending', timestamp: new Date().toISOString() },
        { name: 'Processing Rate', status: 'warn', message: 'Slightly below target', timestamp: new Date().toISOString() },
      ],
    },
  ];

  // Load initial data
  useEffect(() => {
    refreshMetrics();
    const interval = setInterval(() => {
      if (isRealTimeEnabled) {
        refreshMetrics();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isRealTimeEnabled]);

  const refreshMetrics = async () => {
    setRefreshing(true);
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const newMetrics = generateMockMetrics();
      const newServiceHealth = generateMockServiceHealth();
      
      setMetrics(newMetrics);
      setServiceHealth(newServiceHealth);

      // Check for alerts
      checkForAlerts(newMetrics, newServiceHealth);
    } catch (error) {
      console.error('Failed to refresh metrics:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const checkForAlerts = (metrics: SystemMetrics, services: ServiceHealth[]) => {
    // CPU Alert
    if (metrics.server.cpuUsage > 90) {
      addAlert({
        type: 'critical',
        title: 'High CPU Usage',
        message: `CPU usage is at ${metrics.server.cpuUsage.toFixed(1)}%`,
        timestamp: new Date().toISOString(),
      });
    }

    // Memory Alert
    if (metrics.server.memoryUsage > 85) {
      addAlert({
        type: 'warning',
        title: 'High Memory Usage',
        message: `Memory usage is at ${metrics.server.memoryUsage.toFixed(1)}%`,
        timestamp: new Date().toISOString(),
      });
    }

    // Service Health Alerts
    services.forEach(service => {
      if (service.status === 'unhealthy') {
        addAlert({
          type: 'critical',
          title: `Service Down: ${service.service}`,
          message: `${service.service} is not responding`,
          timestamp: new Date().toISOString(),
        });
      } else if (service.status === 'degraded') {
        addAlert({
          type: 'warning',
          title: `Service Degraded: ${service.service}`,
          message: `${service.service} is experiencing issues`,
          timestamp: new Date().toISOString(),
        });
      }
    });
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 dark:text-green-400';
      case 'degraded': return 'text-yellow-600 dark:text-yellow-400';
      case 'unhealthy': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getHealthBadgeColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'degraded': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'unhealthy': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  return (
    <div id="system-monitoring-dashboard" className="space-y-6">
      {/* Header */}
      <div id="monitoring-header" className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">System Monitoring</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Real-time system health and performance metrics
            {lastUpdate && (
              <span className="ml-2">
                Last updated: {new Date(lastUpdate).toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div id="monitoring-actions" className="flex items-center gap-2">
          <Button
            variant={isRealTimeEnabled ? "default" : "outline"}
            size="sm"
            onClick={toggleRealTime}
            className="flex items-center gap-2"
          >
            <Activity className={`h-4 w-4 ${isRealTimeEnabled ? 'animate-pulse' : ''}`} />
            {isRealTimeEnabled ? 'Real-time On' : 'Real-time Off'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={refreshMetrics}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <AlertsPanel
          alerts={alerts}
          onDismiss={removeAlert}
          onClearAll={clearAlerts}
        />
      )}

      {/* System Overview Cards */}
      {metrics && (
        <div id="system-overview" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Server Metrics */}
          <Card id="server-metrics-card" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Server className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <h3 className="font-medium">Server</h3>
              </div>
              <Badge className={getHealthBadgeColor('healthy')}>
                Healthy
              </Badge>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>CPU Usage</span>
                  <span>{metrics.server.cpuUsage.toFixed(1)}%</span>
                </div>
                <Progress value={metrics.server.cpuUsage} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Memory</span>
                  <span>{metrics.server.memoryUsage.toFixed(1)}%</span>
                </div>
                <Progress value={metrics.server.memoryUsage} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Disk Usage</span>
                  <span>{metrics.server.diskUsage.toFixed(1)}%</span>
                </div>
                <Progress value={metrics.server.diskUsage} className="h-2" />
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                Uptime: {formatUptime(metrics.server.uptime)}
              </div>
            </div>
          </Card>

          {/* Database Metrics */}
          <Card id="database-metrics-card" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-green-600 dark:text-green-400" />
                <h3 className="font-medium">Database</h3>
              </div>
              <Badge className={getHealthBadgeColor('healthy')}>
                Healthy
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Connections</span>
                <span>{metrics.database.connectionCount}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Avg Query Time</span>
                <span>{metrics.database.queryTime.toFixed(0)}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Cache Hit Ratio</span>
                <span>{metrics.database.cacheHitRatio.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Slow Queries</span>
                <span className={metrics.database.slowQueries > 0 ? 'text-yellow-600' : 'text-green-600'}>
                  {metrics.database.slowQueries}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Table Size</span>
                <span>{formatBytes(metrics.database.tableSize)}</span>
              </div>
            </div>
          </Card>

          {/* Cache Metrics */}
          <Card id="cache-metrics-card" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                <h3 className="font-medium">Cache</h3>
              </div>
              <Badge className={getHealthBadgeColor('healthy')}>
                Healthy
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Hit Rate</span>
                <span className="text-green-600">{metrics.cache.hitRate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Miss Rate</span>
                <span className="text-red-600">{metrics.cache.missRate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Memory Usage</span>
                <span>{metrics.cache.memoryUsage.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Operations</span>
                <span>{metrics.cache.operations.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Avg Response</span>
                <span>{metrics.cache.avgResponseTime.toFixed(1)}ms</span>
              </div>
            </div>
          </Card>

          {/* API Metrics */}
          <Card id="api-metrics-card" className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Monitor className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                <h3 className="font-medium">API</h3>
              </div>
              <Badge className={getHealthBadgeColor(metrics.api.errorRate > 5 ? 'degraded' : 'healthy')}>
                {metrics.api.errorRate > 5 ? 'Degraded' : 'Healthy'}
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Requests/sec</span>
                <span>{metrics.api.requestsPerSecond.toFixed(0)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Avg Response</span>
                <span>{metrics.api.averageResponseTime.toFixed(0)}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Error Rate</span>
                <span className={metrics.api.errorRate > 5 ? 'text-red-600' : 'text-green-600'}>
                  {metrics.api.errorRate.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Active Connections</span>
                <span>{metrics.api.activeConnections}</span>
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                2xx: {metrics.api.status2xx} | 4xx: {metrics.api.status4xx} | 5xx: {metrics.api.status5xx}
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Service Health Grid */}
      {serviceHealth.length > 0 && (
        <ServiceHealthGrid
          services={serviceHealth}
          onRefresh={refreshMetrics}
        />
      )}

      {/* Real-time Metrics */}
      {isRealTimeEnabled && metrics && (
        <RealTimeMetrics
          metrics={metrics}
          history={metricsHistory}
        />
      )}

      {/* Charts Section */}
      {metrics && (
        <div id="charts-section" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MetricsChart
            title="System Performance"
            data={[
              { name: 'CPU', value: metrics.server.cpuUsage, color: '#3B82F6' },
              { name: 'Memory', value: metrics.server.memoryUsage, color: '#10B981' },
              { name: 'Disk', value: metrics.server.diskUsage, color: '#F59E0B' },
            ]}
            type="bar"
          />
          <MetricsChart
            title="API Response Times"
            data={metrics.api.endpointStats.map(stat => ({
              name: stat.endpoint,
              value: stat.avgResponseTime,
              color: stat.avgResponseTime > 500 ? '#EF4444' : '#10B981',
            }))}
            type="line"
          />
        </div>
      )}
    </div>
  );
};