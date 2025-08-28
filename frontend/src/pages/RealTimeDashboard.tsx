import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/hooks/use-toast'
import { LivePortfolioCard } from '@/components/portfolio/LivePortfolioCard'
import { AlertsPanel } from '@/components/alerts/AlertsPanel'
import { usePortfolioWebSocket } from '@/hooks/useWebSocket'
import { portfolioService, Holding } from '@/services/portfolio'
import { Navigation } from '@/components/Navigation'
import { ParticleBackground } from '@/components/ParticleBackground'
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import { 
  TrendingUp, TrendingDown, Activity, RefreshCw, 
  BarChart3, PieChart as PieChartIcon, Target, 
  AlertTriangle, Zap, Timer, ArrowUpRight, ArrowDownRight,
  DollarSign, Percent, Calendar, Globe, Bookmark,
  Settings, Bell
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'

// Mock data generators
const generatePerformanceData = (days: number) => {
  const data = []
  const baseValue = 145000
  const now = new Date()
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    const variation = (Math.random() - 0.5) * 0.03
    const trend = (days - i) / days * 0.15 // Overall upward trend
    const value = baseValue * (1 + trend + variation)
    
    data.push({
      date: date.toISOString().split('T')[0],
      portfolioValue: Math.round(value),
      benchmark: Math.round(baseValue * (1 + trend * 0.8 + variation * 0.7)),
      volume: Math.round(Math.random() * 1000 + 500)
    })
  }
  
  return data
}

const generateRealTimeData = () => {
  const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'SPY', 'QQQ']
  return symbols.map(symbol => ({
    symbol,
    price: Math.round((Math.random() * 200 + 50) * 100) / 100,
    change: Math.round((Math.random() - 0.5) * 10 * 100) / 100,
    changePercent: Math.round((Math.random() - 0.5) * 5 * 100) / 100,
    volume: Math.round(Math.random() * 1000000 + 100000),
    marketCap: Math.round(Math.random() * 1000 + 100),
    lastUpdate: Date.now()
  }))
}

const MetricCard = ({ 
  title, 
  value, 
  change, 
  changePercent, 
  icon: Icon, 
  trend,
  className 
}: {
  title: string
  value: string | number
  change?: number
  changePercent?: number
  icon: any
  trend?: 'up' | 'down' | 'neutral'
  className?: string
}) => {
  const trendColor = trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
  const TrendIcon = trend === 'up' ? ArrowUpRight : trend === 'down' ? ArrowDownRight : Activity
  
  return (
    <Card className={cn('h-full', className)}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <Icon className="w-5 h-5 text-blue-600" />
          <TrendIcon className={cn('w-4 h-4', trendColor)} />
        </div>
        
        <div className="space-y-1">
          <h3 className="text-sm font-medium text-gray-600">{title}</h3>
          <p className="text-2xl font-bold">{value}</p>
          {change !== undefined && changePercent !== undefined && (
            <p className={cn('text-xs', trendColor)}>
              {change >= 0 ? '+' : ''}{change} ({changePercent >= 0 ? '+' : ''}{changePercent}%)
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

const HoldingsTable = ({ holdings, isLoading }: { holdings: any[], isLoading: boolean }) => {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              <Skeleton className="w-8 h-8 rounded" />
              <div>
                <Skeleton className="w-16 h-4 mb-1" />
                <Skeleton className="w-24 h-3" />
              </div>
            </div>
            <div className="text-right">
              <Skeleton className="w-20 h-4 mb-1 ml-auto" />
              <Skeleton className="w-16 h-3 ml-auto" />
            </div>
          </div>
        ))}
      </div>
    )
  }
  
  return (
    <div className="space-y-2">
      {holdings.map((holding) => {
        const isPositive = holding.changePercent >= 0
        return (
          <div key={holding.symbol} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">
                <span className="text-xs font-semibold text-blue-700">
                  {holding.symbol.substring(0, 2)}
                </span>
              </div>
              <div>
                <p className="font-medium text-sm">{holding.symbol}</p>
                <p className="text-xs text-gray-500">
                  {formatDistanceToNow(new Date(holding.lastUpdate), { addSuffix: true })}
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <p className="font-semibold">${holding.price}</p>
              <p className={cn(
                'text-xs font-medium',
                isPositive ? 'text-green-600' : 'text-red-600'
              )}>
                {isPositive ? '+' : ''}{holding.change} ({isPositive ? '+' : ''}{holding.changePercent}%)
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

const QuickActions = () => {
  const actions = [
    { label: 'Rebalance Portfolio', icon: RefreshCw, variant: 'default' as const, action: () => console.log('Rebalance') },
    { label: 'Add Funds', icon: DollarSign, variant: 'secondary' as const, action: () => console.log('Add funds') },
    { label: 'Tax Harvest', icon: Calendar, variant: 'outline' as const, action: () => console.log('Tax harvest') },
    { label: 'Set Alert', icon: Bell, variant: 'ghost' as const, action: () => console.log('Set alert') },
  ]
  
  return (
    <div className="grid grid-cols-2 gap-2">
      {actions.map((action) => (
        <Button
          key={action.label}
          variant={action.variant}
          size="sm"
          className="h-16 flex flex-col gap-1"
          onClick={action.action}
        >
          <action.icon className="w-4 h-4" />
          <span className="text-xs">{action.label}</span>
        </Button>
      ))}
    </div>
  )
}

export const RealTimeDashboard = () => {
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState('overview')
  const [alerts, setAlerts] = useState<any[]>([])
  
  // WebSocket connection for real-time updates
  const {
    isConnected,
    portfolioData,
    subscribeToSymbol,
    clearAlert
  } = usePortfolioWebSocket()
  
  // Portfolio data query
  const { data: portfolioOverview, isLoading: portfolioLoading } = useQuery({
    queryKey: ['portfolio', 'overview'],
    queryFn: () => portfolioService.getPortfolioOverview(),
    refetchInterval: 30000 // Refetch every 30 seconds as fallback
  })
  
  const { data: holdings, isLoading: holdingsLoading } = useQuery({
    queryKey: ['portfolio', 'holdings'],
    queryFn: () => portfolioService.getHoldings(),
    refetchInterval: 60000
  })
  
  const { data: performance } = useQuery({
    queryKey: ['portfolio', 'performance', '1M'],
    queryFn: () => portfolioService.getPerformance('1M'),
    refetchInterval: 300000 // 5 minutes
  })
  
  // Mock real-time data for demo
  const [realTimeHoldings, setRealTimeHoldings] = useState<any[]>([])
  const [performanceData, setPerformanceData] = useState<any[]>([])
  
  useEffect(() => {
    // Initialize mock data
    setRealTimeHoldings(generateRealTimeData())
    setPerformanceData(generatePerformanceData(30))
    
    // Subscribe to symbols
    const symbols = ['AAPL', 'GOOGL', 'MSFT', 'SPY']
    symbols.forEach(subscribeToSymbol)
    
    // Simulate real-time updates
    const interval = setInterval(() => {
      setRealTimeHoldings(generateRealTimeData())
    }, 5000)
    
    return () => clearInterval(interval)
  }, [subscribeToSymbol])
  
  // Handle alerts
  const handleDismissAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId))
    clearAlert(alertId)
  }
  
  const handleDismissAllAlerts = () => {
    setAlerts([])
  }
  
  const handleMarkAsRead = (alertId: string) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId ? { ...alert, isRead: true } : alert
      )
    )
  }
  
  const handleMarkAllAsRead = () => {
    setAlerts(prev => prev.map(alert => ({ ...alert, isRead: true })))
  }
  
  // Calculate metrics
  const currentValue = portfolioData.portfolioValue || portfolioOverview?.totalValue || 145000
  const dayChange = portfolioData.dayChange || portfolioOverview?.dayChange || 1250
  const dayChangePercent = portfolioData.dayChangePercentage || portfolioOverview?.dayChangePercentage || 0.87
  
  const sparklineData = performanceData.slice(-30).map(item => ({
    time: item.date,
    value: item.portfolioValue
  }))
  
  // Portfolio allocation data for pie chart
  const allocationData = [
    { name: 'Technology', value: 53.4, fill: '#3b82f6' },
    { name: 'ETFs', value: 31.0, fill: '#10b981' },
    { name: 'Fixed Income', value: 8.3, fill: '#f59e0b' },
    { name: 'Cash', value: 3.4, fill: '#6b7280' },
    { name: 'Other', value: 3.9, fill: '#8b5cf6' }
  ]
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      <ParticleBackground />
      <Navigation />
      
      <div className="pt-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8 animate-slide-in-bottom">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
                  <Zap className="w-10 h-10 text-yellow-500" />
                  Real-Time Dashboard
                </h1>
                <p className="text-muted-foreground text-lg">
                  Live portfolio monitoring with instant updates
                </p>
              </div>
              
              <div className="flex items-center gap-4">
                <Badge 
                  variant={isConnected ? "default" : "destructive"} 
                  className="px-3 py-1"
                >
                  <Activity className="w-3 h-3 mr-1" />
                  {isConnected ? 'Live' : 'Offline'}
                </Badge>
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Configure
                </Button>
              </div>
            </div>
          </div>
          
          {/* Main Content */}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Left Column - Main Charts and Metrics */}
            <div className="xl:col-span-3 space-y-6">
              {/* Portfolio Value Card */}
              <LivePortfolioCard
                value={currentValue}
                dayChange={dayChange}
                dayChangePercentage={dayChangePercent}
                isConnected={isConnected}
                isLoading={portfolioLoading}
                marketStatus={portfolioData.marketStatus}
                sparklineData={sparklineData}
                className="animate-scale-in"
              />
              
              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-slide-in-right">
                <MetricCard
                  title="Today's Gain"
                  value={`$${Math.abs(dayChange).toLocaleString()}`}
                  change={dayChange}
                  changePercent={dayChangePercent}
                  icon={TrendingUp}
                  trend={dayChange >= 0 ? 'up' : 'down'}
                />
                <MetricCard
                  title="Total Invested"
                  value={`$${(currentValue - 25000).toLocaleString()}`}
                  icon={DollarSign}
                  trend="neutral"
                />
                <MetricCard
                  title="Annual Return"
                  value="23.4%"
                  change={2.1}
                  changePercent={1.2}
                  icon={Percent}
                  trend="up"
                />
                <MetricCard
                  title="Active Holdings"
                  value={realTimeHoldings.length}
                  icon={BarChart3}
                  trend="neutral"
                />
              </div>
              
              {/* Charts Tabs */}
              <Card className="animate-slide-in-bottom">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-600" />
                    Performance Analytics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="overview">Performance</TabsTrigger>
                      <TabsTrigger value="allocation">Allocation</TabsTrigger>
                      <TabsTrigger value="holdings">Holdings</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="overview" className="mt-6">
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={performanceData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip 
                              formatter={(value: any, name: string) => [
                                `$${value.toLocaleString()}`, 
                                name === 'portfolioValue' ? 'Portfolio' : 'Benchmark'
                              ]}
                            />
                            <Legend />
                            <Area 
                              type="monotone" 
                              dataKey="portfolioValue" 
                              stroke="#3b82f6" 
                              fill="#3b82f6" 
                              fillOpacity={0.1}
                              name="Portfolio"
                            />
                            <Line 
                              type="monotone" 
                              dataKey="benchmark" 
                              stroke="#10b981" 
                              strokeDasharray="5 5"
                              name="Benchmark"
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="allocation" className="mt-6">
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={allocationData}
                              cx="50%"
                              cy="50%"
                              outerRadius={100}
                              dataKey="value"
                              label={({ name, value }) => `${name}: ${value}%`}
                            >
                              {allocationData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="holdings" className="mt-6">
                      <HoldingsTable 
                        holdings={realTimeHoldings} 
                        isLoading={holdingsLoading} 
                      />
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </div>
            
            {/* Right Column - Alerts and Actions */}
            <div className="space-y-6">
              {/* Alerts Panel */}
              <div className="animate-slide-in-left">
                <AlertsPanel
                  alerts={alerts}
                  onDismiss={handleDismissAlert}
                  onDismissAll={handleDismissAllAlerts}
                  onMarkAsRead={handleMarkAsRead}
                  onMarkAllAsRead={handleMarkAllAsRead}
                />
              </div>
              
              {/* Quick Actions */}
              <Card className="animate-slide-in-left" style={{ animationDelay: '0.1s' }}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Timer className="w-5 h-5 text-green-600" />
                    Quick Actions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <QuickActions />
                </CardContent>
              </Card>
              
              {/* Market Status */}
              <Card className="animate-slide-in-left" style={{ animationDelay: '0.2s' }}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Globe className="w-5 h-5 text-blue-600" />
                    Market Status
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">NYSE</span>
                      <Badge variant="default" className="bg-green-100 text-green-800">
                        Open
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">NASDAQ</span>
                      <Badge variant="default" className="bg-green-100 text-green-800">
                        Open
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Next Close</span>
                      <span className="text-sm text-gray-600">4:00 PM EST</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              {/* Recent Activity */}
              <Card className="animate-slide-in-left" style={{ animationDelay: '0.3s' }}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Activity className="w-5 h-5 text-purple-600" />
                    Recent Activity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-600 rounded-full" />
                      <span>AAPL dividend received</span>
                      <span className="text-gray-500 ml-auto">2m ago</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full" />
                      <span>Portfolio rebalanced</span>
                      <span className="text-gray-500 ml-auto">1h ago</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-yellow-600 rounded-full" />
                      <span>Goal milestone reached</span>
                      <span className="text-gray-500 ml-auto">3h ago</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}