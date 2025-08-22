"use client";

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity,
  AlertTriangle,
  BarChart3,
  Clock,
  Database,
  Download,
  Filter,
  Globe,
  HardDrive,
  LineChart,
  Moon,
  MoreHorizontal,
  Pause,
  Play,
  RefreshCw,
  Search,
  Server,
  Settings,
  Shield,
  Sun,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react';

// Types
interface SystemMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  change: number;
  status: 'healthy' | 'warning' | 'critical';
  icon: React.ReactNode;
  description: string;
}

interface ServiceHealth {
  id: string;
  name: string;
  status: 'online' | 'degraded' | 'offline';
  uptime: number;
  responseTime: number;
  lastCheck: string;
  url: string;
}

interface UserData {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'moderator';
  lastActive: string;
  status: 'active' | 'inactive' | 'suspended';
  joinDate: string;
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  service: string;
  message: string;
  userId?: string;
}

interface ConfigItem {
  id: string;
  key: string;
  value: string;
  description: string;
  category: string;
  type: 'string' | 'number' | 'boolean' | 'json';
  lastModified: string;
}

// Mock data generators
const generateSystemMetrics = (): SystemMetric[] => [
  {
    id: 'cpu',
    name: 'CPU Usage',
    value: Math.floor(Math.random() * 100),
    unit: '%',
    change: Math.floor(Math.random() * 20) - 10,
    status: Math.random() > 0.8 ? 'warning' : 'healthy',
    icon: <Zap className="h-4 w-4" />,
    description: 'Current CPU utilization across all cores'
  },
  {
    id: 'memory',
    name: 'Memory Usage',
    value: Math.floor(Math.random() * 100),
    unit: '%',
    change: Math.floor(Math.random() * 15) - 7,
    status: Math.random() > 0.85 ? 'critical' : 'healthy',
    icon: <HardDrive className="h-4 w-4" />,
    description: 'System memory utilization'
  },
  {
    id: 'disk',
    name: 'Disk Usage',
    value: Math.floor(Math.random() * 90) + 10,
    unit: '%',
    change: Math.floor(Math.random() * 5) - 2,
    status: 'healthy',
    icon: <Database className="h-4 w-4" />,
    description: 'Primary disk space utilization'
  },
  {
    id: 'network',
    name: 'Network I/O',
    value: Math.floor(Math.random() * 1000),
    unit: 'MB/s',
    change: Math.floor(Math.random() * 100) - 50,
    status: 'healthy',
    icon: <Globe className="h-4 w-4" />,
    description: 'Network throughput'
  }
];

const generateServices = (): ServiceHealth[] => [
  {
    id: 'api',
    name: 'API Gateway',
    status: Math.random() > 0.9 ? 'degraded' : 'online',
    uptime: 99.9,
    responseTime: Math.floor(Math.random() * 200) + 50,
    lastCheck: new Date(Date.now() - Math.random() * 60000).toISOString(),
    url: 'https://api.example.com'
  },
  {
    id: 'database',
    name: 'PostgreSQL',
    status: Math.random() > 0.95 ? 'offline' : 'online',
    uptime: 99.8,
    responseTime: Math.floor(Math.random() * 100) + 10,
    lastCheck: new Date(Date.now() - Math.random() * 30000).toISOString(),
    url: 'postgres://localhost:5432'
  },
  {
    id: 'redis',
    name: 'Redis Cache',
    status: 'online',
    uptime: 99.95,
    responseTime: Math.floor(Math.random() * 20) + 5,
    lastCheck: new Date(Date.now() - Math.random() * 15000).toISOString(),
    url: 'redis://localhost:6379'
  },
  {
    id: 'elasticsearch',
    name: 'Elasticsearch',
    status: Math.random() > 0.85 ? 'degraded' : 'online',
    uptime: 99.7,
    responseTime: Math.floor(Math.random() * 300) + 100,
    lastCheck: new Date(Date.now() - Math.random() * 45000).toISOString(),
    url: 'http://localhost:9200'
  }
];

const generateUsers = (): UserData[] => {
  const roles: UserData['role'][] = ['admin', 'user', 'moderator'];
  const statuses: UserData['status'][] = ['active', 'inactive', 'suspended'];
  const names = ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson', 'Diana Davis', 'Eve White', 'Frank Miller'];
  
  return names.map((name, index) => ({
    id: `user-${index + 1}`,
    name,
    email: name.toLowerCase().replace(' ', '.') + '@example.com',
    role: roles[Math.floor(Math.random() * roles.length)],
    lastActive: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString(),
    status: statuses[Math.floor(Math.random() * statuses.length)],
    joinDate: new Date(Date.now() - Math.random() * 86400000 * 365).toISOString()
  }));
};

const generateLogs = (): LogEntry[] => {
  const levels: LogEntry['level'][] = ['info', 'warn', 'error', 'debug'];
  const services = ['api-gateway', 'auth-service', 'user-service', 'payment-service', 'notification-service'];
  const messages = [
    'User authentication successful',
    'Database connection pool exhausted',
    'Payment processing completed',
    'Rate limit exceeded for IP',
    'Cache miss for key',
    'Backup completed successfully',
    'SSL certificate expires soon',
    'Memory usage threshold exceeded'
  ];

  return Array.from({ length: 50 }, (_, index) => ({
    id: `log-${index + 1}`,
    timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString(),
    level: levels[Math.floor(Math.random() * levels.length)],
    service: services[Math.floor(Math.random() * services.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
    userId: Math.random() > 0.7 ? `user-${Math.floor(Math.random() * 8) + 1}` : undefined
  }));
};

const generateConfig = (): ConfigItem[] => [
  {
    id: 'max-connections',
    key: 'database.maxConnections',
    value: '100',
    description: 'Maximum number of database connections',
    category: 'Database',
    type: 'number',
    lastModified: new Date(Date.now() - Math.random() * 86400000).toISOString()
  },
  {
    id: 'rate-limit',
    key: 'api.rateLimit',
    value: '1000',
    description: 'API rate limit per minute',
    category: 'API',
    type: 'number',
    lastModified: new Date(Date.now() - Math.random() * 86400000 * 2).toISOString()
  },
  {
    id: 'enable-logging',
    key: 'system.enableDetailedLogging',
    value: 'true',
    description: 'Enable detailed system logging',
    category: 'System',
    type: 'boolean',
    lastModified: new Date(Date.now() - Math.random() * 86400000 * 3).toISOString()
  }
];

// Utility functions
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

const formatUptime = (uptime: number) => {
  return `${uptime.toFixed(2)}%`;
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'online': case 'healthy': case 'active':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
    case 'degraded': case 'warning': case 'inactive':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
    case 'offline': case 'critical': case 'suspended':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
    case 'info':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
    case 'debug':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  }
};

export default function AdminDemoPage() {
  // State
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(true);
  const [metrics, setMetrics] = useState<SystemMetric[]>([]);
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [users, setUsers] = useState<UserData[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [config, setConfig] = useState<ConfigItem[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserData | null>(null);
  const [logFilter, setLogFilter] = useState<string>('');
  const [userFilter, setUserFilter] = useState<string>('');
  const [activeTab, setActiveTab] = useState('monitoring');

  // Initialize data
  useEffect(() => {
    setMetrics(generateSystemMetrics());
    setServices(generateServices());
    setUsers(generateUsers());
    setLogs(generateLogs());
    setConfig(generateConfig());
    
    // Set dark mode class
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Real-time updates
  useEffect(() => {
    if (!isRealTimeEnabled) return;

    const interval = setInterval(() => {
      setMetrics(generateSystemMetrics());
      setServices(generateServices());
      
      // Add new log entry occasionally
      if (Math.random() > 0.7) {
        const newLogs = generateLogs();
        setLogs(prev => [newLogs[0], ...prev.slice(0, 49)]);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [isRealTimeEnabled]);

  // Filtered data
  const filteredLogs = useMemo(() => {
    if (!logFilter) return logs;
    return logs.filter(log => 
      log.message.toLowerCase().includes(logFilter.toLowerCase()) ||
      log.service.toLowerCase().includes(logFilter.toLowerCase()) ||
      log.level.toLowerCase().includes(logFilter.toLowerCase())
    );
  }, [logs, logFilter]);

  const filteredUsers = useMemo(() => {
    if (!userFilter) return users;
    return users.filter(user =>
      user.name.toLowerCase().includes(userFilter.toLowerCase()) ||
      user.email.toLowerCase().includes(userFilter.toLowerCase()) ||
      user.role.toLowerCase().includes(userFilter.toLowerCase())
    );
  }, [users, userFilter]);

  // Handlers
  const toggleTheme = useCallback(() => {
    setIsDarkMode(prev => !prev);
  }, []);

  const toggleRealTime = useCallback(() => {
    setIsRealTimeEnabled(prev => !prev);
  }, []);

  const exportData = useCallback((dataType: string) => {
    let data: any;
    let filename: string;

    switch (dataType) {
      case 'metrics':
        data = metrics;
        filename = 'system-metrics.json';
        break;
      case 'logs':
        data = filteredLogs;
        filename = 'system-logs.json';
        break;
      case 'users':
        data = filteredUsers;
        filename = 'users.json';
        break;
      default:
        return;
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [metrics, filteredLogs, filteredUsers]);

  const updateConfig = useCallback((id: string, newValue: string) => {
    setConfig(prev => prev.map(item => 
      item.id === id 
        ? { ...item, value: newValue, lastModified: new Date().toISOString() }
        : item
    ));
  }, []);

  return (
    <div id="admin-dashboard-container" className="min-h-screen bg-background text-foreground transition-colors duration-300">
      {/* Header */}
      <header id="admin-header" className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div id="header-title" className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Shield className="h-8 w-8 text-primary" />
                <h1 className="text-2xl font-bold">Admin Dashboard</h1>
              </div>
              <Badge variant="secondary" className="text-xs">
                DEMO
              </Badge>
            </div>
            
            <div id="header-controls" className="flex items-center space-x-2">
              <Button
                id="real-time-toggle"
                variant="outline"
                size="sm"
                onClick={toggleRealTime}
                className="flex items-center space-x-2"
              >
                {isRealTimeEnabled ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                <span>{isRealTimeEnabled ? 'Pause' : 'Resume'} Live</span>
              </Button>
              
              <Button
                id="theme-toggle"
                variant="outline"
                size="sm"
                onClick={toggleTheme}
              >
                {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
              
              <Button id="refresh-button" variant="outline" size="sm">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main id="admin-main-content" className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Tab Navigation */}
          <TabsList id="admin-tabs-nav" className="grid w-full grid-cols-4 lg:w-auto lg:grid-cols-none lg:inline-flex">
            <TabsTrigger value="monitoring" className="flex items-center space-x-2">
              <Activity className="h-4 w-4" />
              <span>Monitoring</span>
            </TabsTrigger>
            <TabsTrigger value="users" className="flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>Users</span>
            </TabsTrigger>
            <TabsTrigger value="config" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span>Config</span>
            </TabsTrigger>
            <TabsTrigger value="logs" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Logs</span>
            </TabsTrigger>
          </TabsList>

          {/* Monitoring Tab */}
          <TabsContent value="monitoring" id="monitoring-tab-content" className="space-y-6">
            {/* System Metrics */}
            <div id="system-metrics-section">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">System Metrics</h2>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span>Live</span>
                  </div>
                  <Button
                    id="export-metrics-button"
                    variant="outline"
                    size="sm"
                    onClick={() => exportData('metrics')}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {metrics.map((metric) => (
                  <Card key={metric.id} id={`metric-card-${metric.id}`} className="relative">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {metric.icon}
                          <CardTitle className="text-sm font-medium">
                            {metric.name}
                          </CardTitle>
                        </div>
                        <Badge
                          variant="secondary"
                          className={`text-xs ${getStatusColor(metric.status)}`}
                        >
                          {metric.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-baseline space-x-1">
                          <span className="text-2xl font-bold">
                            {metric.value}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            {metric.unit}
                          </span>
                        </div>
                        
                        {metric.unit === '%' && (
                          <Progress 
                            value={metric.value} 
                            className="h-2" 
                            id={`metric-progress-${metric.id}`}
                          />
                        )}
                        
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>{metric.description}</span>
                          <span className={metric.change >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {metric.change >= 0 ? '+' : ''}{metric.change}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Service Health */}
            <div id="service-health-section">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Service Health</h2>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="text-xs">
                    {services.filter(s => s.status === 'online').length}/{services.length} Online
                  </Badge>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {services.map((service) => (
                  <Card key={service.id} id={`service-card-${service.id}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base font-medium">
                          {service.name}
                        </CardTitle>
                        <Badge
                          variant="secondary"
                          className={`text-xs ${getStatusColor(service.status)}`}
                        >
                          {service.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Uptime</span>
                          <div className="font-medium">{formatUptime(service.uptime)}</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Response</span>
                          <div className="font-medium">{service.responseTime}ms</div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Last Check</span>
                          <div className="font-medium">
                            {new Date(service.lastCheck).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 pt-3 border-t text-xs text-muted-foreground">
                        {service.url}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Analytics Summary */}
            <div id="analytics-summary-section">
              <h2 className="text-lg font-semibold mb-4">Analytics Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card id="total-users-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium flex items-center">
                      <Users className="h-4 w-4 mr-2" />
                      Total Users
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{users.length}</div>
                    <div className="text-sm text-muted-foreground">
                      {users.filter(u => u.status === 'active').length} active
                    </div>
                  </CardContent>
                </Card>
                
                <Card id="system-load-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium flex items-center">
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Avg Load
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {(metrics.reduce((acc, m) => acc + (m.unit === '%' ? m.value : 0), 0) / metrics.filter(m => m.unit === '%').length).toFixed(1)}%
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Last 24 hours
                    </div>
                  </CardContent>
                </Card>
                
                <Card id="alerts-card">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium flex items-center">
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Active Alerts
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {metrics.filter(m => m.status !== 'healthy').length + services.filter(s => s.status !== 'online').length}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Require attention
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" id="users-tab-content" className="space-y-6">
            <div id="users-section">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">User Management</h2>
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                    <input
                      id="user-search-input"
                      type="text"
                      placeholder="Search users..."
                      className="pl-9 pr-4 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      value={userFilter}
                      onChange={(e) => setUserFilter(e.target.value)}
                    />
                  </div>
                  <Button
                    id="export-users-button"
                    variant="outline"
                    size="sm"
                    onClick={() => exportData('users')}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
              
              <Card id="users-table-card">
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="border-b bg-muted/50">
                        <tr>
                          <th className="text-left p-4 font-medium">User</th>
                          <th className="text-left p-4 font-medium">Role</th>
                          <th className="text-left p-4 font-medium">Status</th>
                          <th className="text-left p-4 font-medium">Last Active</th>
                          <th className="text-left p-4 font-medium">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredUsers.map((user) => (
                          <tr key={user.id} id={`user-row-${user.id}`} className="border-b hover:bg-muted/50">
                            <td className="p-4">
                              <div>
                                <div className="font-medium">{user.name}</div>
                                <div className="text-sm text-muted-foreground">{user.email}</div>
                              </div>
                            </td>
                            <td className="p-4">
                              <Badge
                                variant="outline"
                                className={user.role === 'admin' ? 'border-red-200 text-red-800 bg-red-50' : ''}
                              >
                                {user.role}
                              </Badge>
                            </td>
                            <td className="p-4">
                              <Badge
                                variant="secondary"
                                className={`${getStatusColor(user.status)}`}
                              >
                                {user.status}
                              </Badge>
                            </td>
                            <td className="p-4 text-sm text-muted-foreground">
                              {formatDate(user.lastActive)}
                            </td>
                            <td className="p-4">
                              <Button
                                id={`user-actions-${user.id}`}
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedUser(user)}
                              >
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Configuration Tab */}
          <TabsContent value="config" id="config-tab-content" className="space-y-6">
            <div id="config-section">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">System Configuration</h2>
                <Badge variant="outline" className="text-xs">
                  {config.length} Settings
                </Badge>
              </div>
              
              <div className="space-y-4">
                {config.map((item) => (
                  <Card key={item.id} id={`config-item-${item.id}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-base font-medium">{item.key}</CardTitle>
                          <CardDescription className="text-sm">{item.description}</CardDescription>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {item.category}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center space-x-4">
                        <div className="flex-1">
                          <input
                            id={`config-input-${item.id}`}
                            type={item.type === 'number' ? 'number' : 'text'}
                            value={item.value}
                            onChange={(e) => updateConfig(item.id, e.target.value)}
                            className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Modified: {formatDate(item.lastModified)}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Logs Tab */}
          <TabsContent value="logs" id="logs-tab-content" className="space-y-6">
            <div id="logs-section">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">System Logs</h2>
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Filter className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                    <input
                      id="log-filter-input"
                      type="text"
                      placeholder="Filter logs..."
                      className="pl-9 pr-4 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      value={logFilter}
                      onChange={(e) => setLogFilter(e.target.value)}
                    />
                  </div>
                  <Button
                    id="export-logs-button"
                    variant="outline"
                    size="sm"
                    onClick={() => exportData('logs')}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
              
              <Card id="logs-display-card">
                <CardContent className="p-0">
                  <div className="max-h-96 overflow-y-auto">
                    {filteredLogs.map((log) => (
                      <div
                        key={log.id}
                        id={`log-entry-${log.id}`}
                        className="flex items-start space-x-4 p-4 border-b hover:bg-muted/50 font-mono text-sm"
                      >
                        <div className="flex-shrink-0 text-xs text-muted-foreground min-w-[120px]">
                          {formatDate(log.timestamp)}
                        </div>
                        <Badge
                          variant="secondary"
                          className={`flex-shrink-0 text-xs ${getStatusColor(log.level)}`}
                        >
                          {log.level.toUpperCase()}
                        </Badge>
                        <div className="flex-shrink-0 text-xs text-muted-foreground min-w-[100px]">
                          {log.service}
                        </div>
                        <div className="flex-1">{log.message}</div>
                        {log.userId && (
                          <div className="flex-shrink-0 text-xs text-muted-foreground">
                            {log.userId}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>

      {/* User Details Modal */}
      {selectedUser && (
        <div id="user-modal-overlay" className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card id="user-modal-card" className="w-full max-w-md">
            <CardHeader>
              <CardTitle>User Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Name</label>
                <div className="text-sm text-muted-foreground">{selectedUser.name}</div>
              </div>
              <div>
                <label className="text-sm font-medium">Email</label>
                <div className="text-sm text-muted-foreground">{selectedUser.email}</div>
              </div>
              <div>
                <label className="text-sm font-medium">Role</label>
                <Badge variant="outline">{selectedUser.role}</Badge>
              </div>
              <div>
                <label className="text-sm font-medium">Status</label>
                <Badge variant="secondary" className={getStatusColor(selectedUser.status)}>
                  {selectedUser.status}
                </Badge>
              </div>
              <div>
                <label className="text-sm font-medium">Joined</label>
                <div className="text-sm text-muted-foreground">{formatDate(selectedUser.joinDate)}</div>
              </div>
              <div>
                <label className="text-sm font-medium">Last Active</label>
                <div className="text-sm text-muted-foreground">{formatDate(selectedUser.lastActive)}</div>
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                id="close-user-modal-button"
                variant="outline" 
                onClick={() => setSelectedUser(null)}
                className="w-full"
              >
                Close
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}

      {/* Offline Indicator */}
      {!navigator.onLine && (
        <div id="offline-indicator" className="fixed bottom-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-lg shadow-lg">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm font-medium">Offline Mode</span>
          </div>
        </div>
      )}
    </div>
  );
}