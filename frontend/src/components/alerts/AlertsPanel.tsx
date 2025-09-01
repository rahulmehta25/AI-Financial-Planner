import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Bell, 
  X, 
  AlertTriangle, 
  Info, 
  CheckCircle,
  TrendingUp,
  Target,
  RefreshCw,
  Calendar,
  DollarSign,
  AlertCircle,
  Filter,
  Settings
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Inline cn function to avoid import issues
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export interface Alert {
  id: string
  type: 'price' | 'news' | 'goal' | 'rebalance' | 'market' | 'tax' | 'risk'
  severity: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: number
  isRead: boolean
  actionable?: boolean
  actionLabel?: string
  onAction?: () => void
  data?: any
}

interface AlertsPanelProps {
  alerts: Alert[]
  onDismiss: (alertId: string) => void
  onDismissAll: () => void
  onMarkAsRead: (alertId: string) => void
  onMarkAllAsRead: () => void
  isLoading?: boolean
  className?: string
}

const AlertIcon = ({ type, severity }: { type: Alert['type'], severity: Alert['severity'] }) => {
  const iconMap = {
    price: TrendingUp,
    news: Info,
    goal: Target,
    rebalance: RefreshCw,
    market: Calendar,
    tax: DollarSign,
    risk: AlertTriangle
  }
  
  const Icon = iconMap[type] || Bell
  
  const colorMap = {
    info: 'text-blue-600',
    success: 'text-green-600',
    warning: 'text-amber-600',
    error: 'text-red-600'
  }
  
  return <Icon className={cn('w-4 h-4', colorMap[severity])} />
}

const AlertItem = ({ alert, onDismiss, onMarkAsRead }: { 
  alert: Alert
  onDismiss: (id: string) => void
  onMarkAsRead: (id: string) => void
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  
  const severityColors = {
    info: 'border-l-blue-500 bg-blue-50/30',
    success: 'border-l-green-500 bg-green-50/30',
    warning: 'border-l-amber-500 bg-amber-50/30',
    error: 'border-l-red-500 bg-red-50/30'
  }
  
  const timeAgo = formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })
  
  return (
    <div 
      className={cn(
        'relative p-4 border-l-4 rounded-r-lg transition-all duration-200',
        'hover:shadow-md cursor-pointer',
        severityColors[alert.severity],
        !alert.isRead && 'ring-2 ring-blue-200 ring-opacity-50'
      )}
      onClick={() => {
        setIsExpanded(!isExpanded)
        if (!alert.isRead) {
          onMarkAsRead(alert.id)
        }
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <AlertIcon type={alert.type} severity={alert.severity} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className={cn(
                'text-sm font-medium truncate',
                !alert.isRead && 'font-semibold'
              )}>
                {alert.title}
              </h4>
              <Badge variant="outline" className="text-xs px-1.5 py-0.5 shrink-0">
                {alert.type}
              </Badge>
              {!alert.isRead && (
                <div className="w-2 h-2 bg-blue-600 rounded-full shrink-0" />
              )}
            </div>
            
            <p className={cn(
              'text-sm text-gray-600 mb-2',
              isExpanded ? 'line-clamp-none' : 'line-clamp-2'
            )}>
              {alert.message}
            </p>
            
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{timeAgo}</span>
              {alert.actionable && (
                <Button
                  variant="link"
                  size="sm"
                  className="h-auto p-0 text-xs text-blue-600 hover:text-blue-700"
                  onClick={(e) => {
                    e.stopPropagation()
                    alert.onAction?.()
                  }}
                >
                  {alert.actionLabel || 'Take Action'}
                </Button>
              )}
            </div>
          </div>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          className="w-8 h-8 p-0 hover:bg-gray-100"
          onClick={(e) => {
            e.stopPropagation()
            onDismiss(alert.id)
          }}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}

const EmptyState = ({ type }: { type: string }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <Bell className="w-12 h-12 text-gray-300 mb-4" />
    <h3 className="text-lg font-medium text-gray-900 mb-2">No {type} alerts</h3>
    <p className="text-sm text-gray-500 max-w-sm">
      {type === 'unread' 
        ? "You're all caught up! No new alerts to review."
        : `No ${type} alerts at the moment. We'll notify you when something important happens.`
      }
    </p>
  </div>
)

export const AlertsPanel = ({
  alerts = [],
  onDismiss,
  onDismissAll,
  onMarkAsRead,
  onMarkAllAsRead,
  isLoading = false,
  className
}: AlertsPanelProps) => {
  const [activeTab, setActiveTab] = useState('all')
  
  const alertStats = useMemo(() => {
    const unreadCount = alerts.filter(alert => !alert.isRead).length
    const severityCounts = alerts.reduce((acc, alert) => {
      acc[alert.severity] = (acc[alert.severity] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    const typeCounts = alerts.reduce((acc, alert) => {
      acc[alert.type] = (acc[alert.type] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    return { unreadCount, severityCounts, typeCounts }
  }, [alerts])
  
  const filteredAlerts = useMemo(() => {
    switch (activeTab) {
      case 'unread':
        return alerts.filter(alert => !alert.isRead)
      case 'critical':
        return alerts.filter(alert => alert.severity === 'error' || alert.severity === 'warning')
      case 'actionable':
        return alerts.filter(alert => alert.actionable)
      default:
        return alerts
    }
  }, [alerts, activeTab])
  
  // Mock alerts for demo
  const mockAlerts: Alert[] = [
    {
      id: '1',
      type: 'price',
      severity: 'warning',
      title: 'AAPL Price Alert',
      message: 'Apple Inc. (AAPL) has dropped 5% from your target price of $175. Consider reviewing your position.',
      timestamp: Date.now() - 300000, // 5 minutes ago
      isRead: false,
      actionable: true,
      actionLabel: 'View Holding',
      onAction: () => console.log('Navigate to AAPL holding')
    },
    {
      id: '2',
      type: 'goal',
      severity: 'success',
      title: 'Emergency Fund Goal Achieved',
      message: 'Congratulations! You\'ve successfully reached your emergency fund goal of $50,000.',
      timestamp: Date.now() - 3600000, // 1 hour ago
      isRead: false,
      actionable: true,
      actionLabel: 'Set New Goal',
      onAction: () => console.log('Create new goal')
    },
    {
      id: '3',
      type: 'rebalance',
      severity: 'info',
      title: 'Portfolio Rebalancing Due',
      message: 'Your portfolio allocation has drifted from targets. Technology sector is overweight by 8%.',
      timestamp: Date.now() - 7200000, // 2 hours ago
      isRead: true,
      actionable: true,
      actionLabel: 'Rebalance Now',
      onAction: () => console.log('Start rebalancing')
    },
    {
      id: '4',
      type: 'market',
      severity: 'info',
      title: 'Market Update',
      message: 'S&P 500 opened 0.8% higher following positive earnings reports from major tech companies.',
      timestamp: Date.now() - 10800000, // 3 hours ago
      isRead: true
    },
    {
      id: '5',
      type: 'tax',
      severity: 'warning',
      title: 'Tax Loss Harvesting Opportunity',
      message: 'You have potential tax loss harvesting opportunities worth $2,300 in realized losses.',
      timestamp: Date.now() - 86400000, // 1 day ago
      isRead: false,
      actionable: true,
      actionLabel: 'Review Opportunities',
      onAction: () => console.log('Open tax harvesting')
    }
  ]
  
  const displayAlerts = alerts.length > 0 ? alerts : mockAlerts
  const displayFilteredAlerts = alerts.length > 0 ? filteredAlerts : mockAlerts.filter(alert => {
    switch (activeTab) {
      case 'unread':
        return !alert.isRead
      case 'critical':
        return alert.severity === 'error' || alert.severity === 'warning'
      case 'actionable':
        return alert.actionable
      default:
        return true
    }
  })
  
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Alerts
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Alerts
            {alertStats.unreadCount > 0 && (
              <Badge variant="destructive" className="ml-2">
                {alertStats.unreadCount}
              </Badge>
            )}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {displayAlerts.length > 0 && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onMarkAllAsRead}
                  className="text-xs"
                >
                  Mark All Read
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onDismissAll}
                  className="text-xs text-red-600 hover:text-red-700"
                >
                  Clear All
                </Button>
              </>
            )}
            <Button variant="ghost" size="sm" className="w-8 h-8 p-0">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all" className="text-xs">
              All ({displayAlerts.length})
            </TabsTrigger>
            <TabsTrigger value="unread" className="text-xs">
              Unread ({displayAlerts.filter(a => !a.isRead).length})
            </TabsTrigger>
            <TabsTrigger value="critical" className="text-xs">
              Critical ({displayAlerts.filter(a => a.severity === 'error' || a.severity === 'warning').length})
            </TabsTrigger>
            <TabsTrigger value="actionable" className="text-xs">
              Actions ({displayAlerts.filter(a => a.actionable).length})
            </TabsTrigger>
          </TabsList>
          
          <div className="mt-4">
            <ScrollArea className="h-96">
              {displayFilteredAlerts.length > 0 ? (
                <div className="space-y-3">
                  {displayFilteredAlerts.map((alert, index) => (
                    <div key={alert.id}>
                      <AlertItem
                        alert={alert}
                        onDismiss={onDismiss}
                        onMarkAsRead={onMarkAsRead}
                      />
                      {index < displayFilteredAlerts.length - 1 && (
                        <Separator className="my-2" />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState type={activeTab} />
              )}
            </ScrollArea>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  )
}