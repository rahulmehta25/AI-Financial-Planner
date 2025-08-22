"use client";

import React from 'react';
import { 
  AlertTriangle, 
  XCircle, 
  Info, 
  X,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Alert {
  id: string;
  type: 'info' | 'warning' | 'critical' | 'success';
  title: string;
  message: string;
  timestamp: string;
}

interface AlertsPanelProps {
  alerts: Alert[];
  onDismiss: (alertId: string) => void;
  onClearAll: () => void;
}

/**
 * AlertsPanel Component
 * 
 * Features:
 * - Different alert types
 * - Dismissible alerts
 * - Timestamp display
 * - Clear all functionality
 */
export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  alerts,
  onDismiss,
  onClearAll,
}) => {
  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'info':
      default:
        return <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />;
    }
  };

  const getAlertStyles = (type: string) => {
    switch (type) {
      case 'critical':
        return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20';
      case 'success':
        return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20';
      case 'info':
      default:
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20';
    }
  };

  const getBadgeStyles = (type: string) => {
    switch (type) {
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'success':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'info':
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const now = new Date();
    const alertTime = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - alertTime.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return alertTime.toLocaleDateString();
  };

  const criticalAlerts = alerts.filter(alert => alert.type === 'critical');
  const warningAlerts = alerts.filter(alert => alert.type === 'warning');
  const infoAlerts = alerts.filter(alert => alert.type === 'info');
  const successAlerts = alerts.filter(alert => alert.type === 'success');

  if (alerts.length === 0) {
    return null;
  }

  return (
    <Card id="alerts-panel" className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            System Alerts
          </h3>
          <Badge variant="destructive">
            {alerts.length}
          </Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onClearAll}
          className="text-sm"
        >
          Clear All
        </Button>
      </div>

      {/* Alert Summary */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        {criticalAlerts.length > 0 && (
          <div className="flex items-center gap-1">
            <XCircle className="h-4 w-4 text-red-600" />
            <span className="text-red-600 font-medium">{criticalAlerts.length} Critical</span>
          </div>
        )}
        {warningAlerts.length > 0 && (
          <div className="flex items-center gap-1">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <span className="text-yellow-600 font-medium">{warningAlerts.length} Warning</span>
          </div>
        )}
        {infoAlerts.length > 0 && (
          <div className="flex items-center gap-1">
            <Info className="h-4 w-4 text-blue-600" />
            <span className="text-blue-600 font-medium">{infoAlerts.length} Info</span>
          </div>
        )}
        {successAlerts.length > 0 && (
          <div className="flex items-center gap-1">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="text-green-600 font-medium">{successAlerts.length} Success</span>
          </div>
        )}
      </div>

      {/* Alerts List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            id={`alert-${alert.id}`}
            className={`p-3 rounded-lg border ${getAlertStyles(alert.type)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                {getAlertIcon(alert.type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {alert.title}
                    </h4>
                    <Badge className={getBadgeStyles(alert.type)}>
                      {alert.type}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                    {alert.message}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatTimestamp(alert.timestamp)}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDismiss(alert.id)}
                className="ml-2 h-8 w-8 p-0 shrink-0"
                aria-label={`Dismiss ${alert.title} alert`}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Alert Actions */}
      {alerts.length > 3 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            {alerts.length > 10 ? `Showing first 10 of ${alerts.length} alerts` : `${alerts.length} total alerts`}
          </p>
        </div>
      )}
    </Card>
  );
};