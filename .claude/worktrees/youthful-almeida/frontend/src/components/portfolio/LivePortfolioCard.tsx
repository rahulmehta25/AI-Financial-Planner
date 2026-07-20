import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from 'recharts'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity,
  Wifi,
  WifiOff,
  RefreshCw
} from 'lucide-react'
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Inline cn function to avoid import issues
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface LivePortfolioCardProps {
  value?: number
  previousValue?: number
  dayChange?: number
  dayChangePercentage?: number
  isConnected?: boolean
  isLoading?: boolean
  marketStatus?: 'open' | 'closed' | 'pre-market' | 'after-hours'
  sparklineData?: Array<{ time: string; value: number }>
  className?: string
}

const AnimatedNumber = ({ value, duration = 1000, decimals = 0, prefix = '', suffix = '' }: {
  value: number
  duration?: number
  decimals?: number
  prefix?: string
  suffix?: string
}) => {
  const [displayValue, setDisplayValue] = useState(value)
  
  useEffect(() => {
    const startValue = displayValue
    const endValue = value
    const difference = endValue - startValue
    const startTime = Date.now()
    
    if (Math.abs(difference) < 0.01) {
      setDisplayValue(endValue)
      return
    }
    
    const animateValue = () => {
      const currentTime = Date.now()
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      
      // Use easeOutCubic for smooth animation
      const easeOutCubic = 1 - Math.pow(1 - progress, 3)
      const currentValue = startValue + (difference * easeOutCubic)
      
      setDisplayValue(currentValue)
      
      if (progress < 1) {
        requestAnimationFrame(animateValue)
      }
    }
    
    requestAnimationFrame(animateValue)
  }, [value, displayValue, duration])
  
  return (
    <span>
      {prefix}{displayValue.toLocaleString(undefined, { 
        minimumFractionDigits: decimals, 
        maximumFractionDigits: decimals 
      })}{suffix}
    </span>
  )
}

const MarketStatusBadge = ({ status }: { status?: string }) => {
  const getStatusConfig = (status?: string) => {
    switch (status) {
      case 'open':
        return { label: 'Market Open', variant: 'default' as const, color: 'bg-green-100 text-green-800' }
      case 'closed':
        return { label: 'Market Closed', variant: 'secondary' as const, color: 'bg-gray-100 text-gray-800' }
      case 'pre-market':
        return { label: 'Pre-Market', variant: 'outline' as const, color: 'bg-blue-100 text-blue-800' }
      case 'after-hours':
        return { label: 'After Hours', variant: 'outline' as const, color: 'bg-purple-100 text-purple-800' }
      default:
        return { label: 'Unknown', variant: 'secondary' as const, color: 'bg-gray-100 text-gray-600' }
    }
  }
  
  const config = getStatusConfig(status)
  
  return (
    <Badge variant={config.variant} className={cn('text-xs font-medium', config.color)}>
      <Activity className="w-3 h-3 mr-1" />
      {config.label}
    </Badge>
  )
}

const generateMockSparklineData = () => {
  const data = []
  const baseValue = 145000
  const now = new Date()
  
  for (let i = 29; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 30 * 60 * 1000) // 30-minute intervals
    const variation = (Math.random() - 0.5) * 0.02 // ±1% variation
    const value = baseValue * (1 + variation)
    
    data.push({
      time: time.toISOString(),
      value: Math.round(value)
    })
  }
  
  return data
}

export const LivePortfolioCard = ({
  value = 145000,
  previousValue = 143750,
  dayChange = 1250,
  dayChangePercentage = 0.87,
  isConnected = true,
  isLoading = false,
  marketStatus = 'open',
  sparklineData,
  className
}: LivePortfolioCardProps) => {
  const [animationKey, setAnimationKey] = useState(0)
  
  // Generate mock sparkline data if not provided
  const chartData = useMemo(() => 
    sparklineData || generateMockSparklineData(), 
    [sparklineData]
  )
  
  // Trigger animation when value changes
  useEffect(() => {
    setAnimationKey(prev => prev + 1)
  }, [value])
  
  const isPositive = dayChange >= 0
  const changeColor = isPositive ? 'text-green-600' : 'text-red-600'
  const changeIcon = isPositive ? TrendingUp : TrendingDown
  const ChangeIcon = changeIcon
  
  if (isLoading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-5 w-20" />
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-40 mb-4" />
          <div className="flex items-center gap-2 mb-4">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-24" />
          </div>
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    )
  }
  
  return (
    <Card className={cn(
      'w-full relative overflow-hidden transition-all duration-300',
      'hover:shadow-lg border-2',
      isConnected ? 'border-green-200 bg-gradient-to-br from-white to-green-50/30' : 'border-red-200 bg-gradient-to-br from-white to-red-50/30',
      className
    )}>
      {/* Connection indicator */}
      <div className="absolute top-2 right-2 z-10">
        <div className={cn(
          'flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full',
          isConnected ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100'
        )}>
          {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          {isConnected ? 'Live' : 'Offline'}
        </div>
      </div>
      
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg font-semibold">
            <DollarSign className="h-5 w-5 text-blue-600" />
            Portfolio Value
          </CardTitle>
          <MarketStatusBadge status={marketStatus} />
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Main value display */}
        <div className="mb-4">
          <div className={cn(
            'text-3xl font-bold transition-all duration-500 transform',
            `animate-pulse-${animationKey % 2 === 0 ? 'even' : 'odd'}`
          )}>
            <AnimatedNumber 
              value={value} 
              prefix="$" 
              decimals={0}
              duration={800}
            />
          </div>
          
          {/* Day change */}
          <div className={cn('flex items-center gap-2 mt-2', changeColor)}>
            <ChangeIcon className="w-4 h-4" />
            <span className="font-semibold">
              <AnimatedNumber 
                value={dayChange} 
                prefix={isPositive ? '+$' : '-$'} 
                decimals={0}
                duration={600}
              />
            </span>
            <span className="text-sm">
              (<AnimatedNumber 
                value={Math.abs(dayChangePercentage)} 
                prefix={isPositive ? '+' : '-'} 
                suffix="%" 
                decimals={2}
                duration={600}
              />)
            </span>
            <span className="text-xs text-gray-600 ml-1">today</span>
          </div>
        </div>
        
        {/* Mini sparkline chart */}
        <div className="h-16 mt-4 -mx-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis 
                dataKey="time" 
                hide 
                domain={['dataMin', 'dataMax']}
              />
              <YAxis 
                hide 
                domain={['dataMin', 'dataMax']}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={isPositive ? '#059669' : '#DC2626'}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3, fill: isPositive ? '#059669' : '#DC2626' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Data freshness indicator */}
        <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <RefreshCw className={cn(
              'w-3 h-3',
              isConnected ? 'text-green-600' : 'text-gray-400'
            )} />
            {isConnected ? 'Real-time' : 'Last update: 2 min ago'}
          </span>
          <span>
            Based on {chartData.length} data points
          </span>
        </div>
      </CardContent>
      
      {/* Pulsing animation overlay for value updates */}
      <div 
        key={animationKey}
        className={cn(
          'absolute inset-0 pointer-events-none',
          'bg-gradient-to-r opacity-0',
          isPositive ? 'from-green-400/20 to-transparent' : 'from-red-400/20 to-transparent',
          'animate-pulse-overlay'
        )}
      />
      
      <style jsx>{`
        @keyframes pulse-overlay {
          0% { opacity: 0; }
          50% { opacity: 1; }
          100% { opacity: 0; }
        }
        
        .animate-pulse-overlay {
          animation: pulse-overlay 0.6s ease-out;
        }
      `}</style>
    </Card>
  )
}