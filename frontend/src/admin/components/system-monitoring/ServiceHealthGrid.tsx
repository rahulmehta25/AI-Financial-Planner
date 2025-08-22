"use client";

import React from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  Activity,
  Zap,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { ServiceHealth } from '../../types';

interface ServiceHealthGridProps {
  services: ServiceHealth[];
  onRefresh: () => void;
}

/**
 * ServiceHealthGrid Component
 * 
 * Features:
 * - Service status overview
 * - Health checks display
 * - Response time monitoring
 * - Dependency tracking
 */
export const ServiceHealthGrid: React.FC<ServiceHealthGridProps> = ({
  services,
  onRefresh,
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'unhealthy':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const getCheckStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warn':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'fail':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const formatUptime = (uptime: number) => {
    return `${uptime.toFixed(2)}%`;
  };

  const formatResponseTime = (time: number) => {
    return `${time}ms`;
  };

  const formatLastCheck = (timestamp: string) => {
    const now = new Date();
    const lastCheck = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - lastCheck.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    return `${Math.floor(diffInSeconds / 3600)}h ago`;
  };

  const overallHealth = services.reduce((acc, service) => {
    if (service.status === 'unhealthy') acc.unhealthy++;
    else if (service.status === 'degraded') acc.degraded++;
    else acc.healthy++;
    return acc;
  }, { healthy: 0, degraded: 0, unhealthy: 0 });

  return (
    <div id="service-health-grid" className="space-y-6">
      {/* Overview Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Service Health</h2>
          <div className="flex items-center gap-4 mt-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {overallHealth.healthy} Healthy
              </span>
            </div>
            {overallHealth.degraded > 0 && (
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {overallHealth.degraded} Degraded
                </span>
              </div>
            )}
            {overallHealth.unhealthy > 0 && (
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {overallHealth.unhealthy} Unhealthy
                </span>
              </div>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh All
        </Button>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {services.map((service) => (
          <Card key={service.service} id={`service-${service.service.toLowerCase().replace(/\s+/g, '-')}`} className="p-6">
            {/* Service Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {getStatusIcon(service.status)}
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {service.service}
                  </h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    v{service.version}
                  </p>
                </div>
              </div>
              <Badge className={getStatusColor(service.status)}>
                {service.status}
              </Badge>
            </div>

            {/* Service Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 mb-1">
                  <Activity className="h-3 w-3 text-gray-500" />
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Uptime</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formatUptime(service.uptime)}
                </p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 mb-1">
                  <Zap className="h-3 w-3 text-gray-500" />
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Response</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formatResponseTime(service.responseTime)}
                </p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 mb-1">
                  <Clock className="h-3 w-3 text-gray-500" />
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Last Check</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formatLastCheck(service.lastCheck)}
                </p>
              </div>
            </div>

            {/* Uptime Progress */}
            <div className="mb-4">
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                <span>Uptime</span>
                <span>{formatUptime(service.uptime)}</span>
              </div>
              <Progress value={service.uptime} className="h-2" />
            </div>

            {/* Health Checks */}
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Health Checks
              </h4>
              <div className="space-y-2">
                {service.checks.map((check, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      {getCheckStatusIcon(check.status)}
                      <span className="text-gray-900 dark:text-white">{check.name}</span>
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {check.message}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Dependencies */}
            {service.dependencies.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Dependencies
                </h4>
                <div className="space-y-1">
                  {service.dependencies.map((dep, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        {dep.status === 'healthy' ? (
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        ) : (
                          <XCircle className="h-3 w-3 text-red-600" />
                        )}
                        <span className="text-gray-900 dark:text-white">{dep.name}</span>
                      </div>
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {formatResponseTime(dep.responseTime)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};