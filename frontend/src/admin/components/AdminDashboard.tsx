"use client";

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Activity, 
  DollarSign, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  FileText,
  Headphones,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { useAdminAuth } from '../store/adminStore';

/**
 * AdminDashboard Component
 * 
 * Main admin dashboard with overview widgets and key metrics
 * 
 * Features:
 * - System overview cards
 * - Recent activity feed
 * - Quick actions
 * - Performance metrics
 * - Role-based content
 */
export const AdminDashboard: React.FC = () => {
  const { currentAdmin, hasRole } = useAdminAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load dashboard stats
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      // Mock API call - replace with real API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStats({
        totalUsers: 12847,
        activeUsers: 8291,
        systemHealth: 98.5,
        revenue: 245678,
        growth: {
          users: 12.5,
          revenue: 8.3,
          health: -0.2,
        },
        recentActivity: [
          {
            id: 1,
            type: 'user_signup',
            message: 'New user registered: John Doe',
            timestamp: '2 minutes ago',
            severity: 'info'
          },
          {
            id: 2,
            type: 'system_alert',
            message: 'High CPU usage detected on server-01',
            timestamp: '5 minutes ago',
            severity: 'warning'
          },
          {
            id: 3,
            type: 'payment',
            message: 'Payment processed: $299 - Premium Plan',
            timestamp: '8 minutes ago',
            severity: 'success'
          },
          {
            id: 4,
            type: 'support_ticket',
            message: 'New support ticket #1847 created',
            timestamp: '12 minutes ago',
            severity: 'info'
          },
        ],
        quickStats: {
          openTickets: 23,
          systemAlerts: 3,
          pendingUsers: 45,
          monthlyRevenue: 89245,
        }
      });
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'user_signup':
        return <Users className="h-4 w-4 text-blue-600" />;
      case 'system_alert':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'payment':
        return <DollarSign className="h-4 w-4 text-green-600" />;
      case 'support_ticket':
        return <Headphones className="h-4 w-4 text-purple-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'success':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-blue-600 dark:text-blue-400';
    }
  };

  if (loading) {
    return (
      <div id="admin-dashboard-loading" className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div id="admin-dashboard" className="space-y-6">
      {/* Welcome Header */}
      <div id="dashboard-header">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Welcome back, {currentAdmin?.firstName}!
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Here's what's happening with your system today.
        </p>
      </div>

      {/* Key Metrics Cards */}
      <div id="key-metrics" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Users */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Users</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.totalUsers.toLocaleString()}
              </p>
              <div className="flex items-center mt-1">
                {stats.growth.users > 0 ? (
                  <>
                    <ArrowUpRight className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-600">+{stats.growth.users}%</span>
                  </>
                ) : (
                  <>
                    <ArrowDownRight className="h-4 w-4 text-red-600" />
                    <span className="text-sm text-red-600">{stats.growth.users}%</span>
                  </>
                )}
                <span className="text-sm text-gray-500 ml-1">from last month</span>
              </div>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Users className="h-6 w-6 text-blue-600 dark:text-blue-300" />
            </div>
          </div>
        </Card>

        {/* Active Users */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Users</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.activeUsers.toLocaleString()}
              </p>
              <div className="mt-2">
                <Progress 
                  value={(stats.activeUsers / stats.totalUsers) * 100} 
                  className="h-2" 
                />
                <p className="text-xs text-gray-500 mt-1">
                  {((stats.activeUsers / stats.totalUsers) * 100).toFixed(1)}% engagement
                </p>
              </div>
            </div>
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
              <Activity className="h-6 w-6 text-green-600 dark:text-green-300" />
            </div>
          </div>
        </Card>

        {/* Monthly Revenue */}
        {hasRole(['admin']) && (
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Monthly Revenue</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(stats.revenue)}
                </p>
                <div className="flex items-center mt-1">
                  {stats.growth.revenue > 0 ? (
                    <>
                      <ArrowUpRight className="h-4 w-4 text-green-600" />
                      <span className="text-sm text-green-600">+{stats.growth.revenue}%</span>
                    </>
                  ) : (
                    <>
                      <ArrowDownRight className="h-4 w-4 text-red-600" />
                      <span className="text-sm text-red-600">{stats.growth.revenue}%</span>
                    </>
                  )}
                  <span className="text-sm text-gray-500 ml-1">from last month</span>
                </div>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                <DollarSign className="h-6 w-6 text-green-600 dark:text-green-300" />
              </div>
            </div>
          </Card>
        )}

        {/* System Health */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">System Health</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.systemHealth}%
              </p>
              <div className="mt-2">
                <Progress 
                  value={stats.systemHealth} 
                  className="h-2" 
                />
                <div className="flex items-center mt-1">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-600 ml-1">All systems operational</span>
                </div>
              </div>
            </div>
            <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Activity className="h-6 w-6 text-purple-600 dark:text-purple-300" />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Recent Activity
              </h3>
              <Button variant="outline" size="sm">
                View All
              </Button>
            </div>
            <div className="space-y-4">
              {stats.recentActivity.map((activity: any) => (
                <div key={activity.id} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  {getActivityIcon(activity.type)}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${getSeverityColor(activity.severity)}`}>
                      {activity.message}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {activity.timestamp}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Quick Stats & Actions */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Quick Stats
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Headphones className="h-4 w-4 text-blue-600" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Open Tickets</span>
                </div>
                <Badge variant="secondary">{stats.quickStats.openTickets}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">System Alerts</span>
                </div>
                <Badge variant="destructive">{stats.quickStats.systemAlerts}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-purple-600" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">Pending Users</span>
                </div>
                <Badge variant="outline">{stats.quickStats.pendingUsers}</Badge>
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Users className="h-4 w-4 mr-2" />
                Manage Users
              </Button>
              <Button variant="outline" className="w-full justify-start" size="sm">
                <BarChart3 className="h-4 w-4 mr-2" />
                View Analytics
              </Button>
              <Button variant="outline" className="w-full justify-start" size="sm">
                <Activity className="h-4 w-4 mr-2" />
                System Status
              </Button>
              <Button variant="outline" className="w-full justify-start" size="sm">
                <FileText className="h-4 w-4 mr-2" />
                Generate Report
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};