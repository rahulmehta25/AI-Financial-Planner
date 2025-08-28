import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
}

export interface UseWebSocketOptions {
  url?: string
  protocols?: string[]
  onMessage?: (data: any, type: string) => void
  onError?: (error: Event) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
  debug?: boolean
}

export interface WebSocketHookReturn {
  status: WebSocketStatus
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  sendMessage: (type: string, data: any) => void
  connect: () => void
  disconnect: () => void
  reconnect: () => void
  connectionAttempts: number
}

const DEFAULT_OPTIONS: Required<UseWebSocketOptions> = {
  url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws`,
  protocols: [],
  onMessage: () => {},
  onError: () => {},
  onConnect: () => {},
  onDisconnect: () => {},
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
  debug: false
}

export const useWebSocket = (options: UseWebSocketOptions = {}): WebSocketHookReturn => {
  const { isAuthenticated, token } = useAuth()
  const opts = { ...DEFAULT_OPTIONS, ...options }
  
  const [status, setStatus] = useState<WebSocketStatus>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionAttempts, setConnectionAttempts] = useState(0)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const isManualDisconnectRef = useRef(false)

  const log = useCallback((message: string, data?: any) => {
    if (opts.debug) {
      console.log(`[WebSocket] ${message}`, data)
    }
  }, [opts.debug])

  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
  }, [])

  const startHeartbeat = useCallback(() => {
    clearTimeouts()
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }))
        log('Heartbeat sent')
      }
    }, opts.heartbeatInterval)
  }, [opts.heartbeatInterval, log, clearTimeouts])

  const connect = useCallback(() => {
    if (!isAuthenticated) {
      log('Not authenticated, skipping WebSocket connection')
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      log('WebSocket already connected or connecting')
      return
    }

    try {
      isManualDisconnectRef.current = false
      setStatus('connecting')
      log('Connecting to WebSocket...')

      // Construct WebSocket URL with auth token
      const wsUrl = new URL(opts.url)
      if (token) {
        wsUrl.searchParams.set('token', token)
      }

      wsRef.current = new WebSocket(wsUrl.toString(), opts.protocols)

      wsRef.current.onopen = (event) => {
        log('WebSocket connected', event)
        setStatus('connected')
        setConnectionAttempts(0)
        startHeartbeat()
        opts.onConnect()
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          log('Message received', message)
          
          // Handle pong response
          if (message.type === 'pong') {
            log('Pong received')
            return
          }
          
          setLastMessage(message)
          opts.onMessage(message.data, message.type)
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error)
          log('Failed to parse message', { error, data: event.data })
        }
      }

      wsRef.current.onclose = (event) => {
        log('WebSocket closed', { code: event.code, reason: event.reason })
        clearTimeouts()
        
        if (!isManualDisconnectRef.current && connectionAttempts < opts.maxReconnectAttempts) {
          setStatus('reconnecting')
          setConnectionAttempts(prev => prev + 1)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            log('Attempting to reconnect...', { attempt: connectionAttempts + 1 })
            connect()
          }, opts.reconnectInterval)
        } else {
          setStatus('disconnected')
          opts.onDisconnect()
        }
      }

      wsRef.current.onerror = (error) => {
        log('WebSocket error', error)
        setStatus('error')
        opts.onError(error)
      }

    } catch (error) {
      log('Failed to create WebSocket connection', error)
      setStatus('error')
      opts.onError(error as Event)
    }
  }, [isAuthenticated, token, opts, connectionAttempts, log, startHeartbeat, clearTimeouts])

  const disconnect = useCallback(() => {
    log('Manually disconnecting WebSocket')
    isManualDisconnectRef.current = true
    clearTimeouts()
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
    
    setStatus('disconnected')
    setConnectionAttempts(0)
  }, [log, clearTimeouts])

  const reconnect = useCallback(() => {
    log('Manual reconnect requested')
    disconnect()
    setTimeout(() => {
      setConnectionAttempts(0)
      connect()
    }, 100)
  }, [disconnect, connect, log])

  const sendMessage = useCallback((type: string, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: Date.now()
      }
      wsRef.current.send(JSON.stringify(message))
      log('Message sent', message)
    } else {
      console.warn('[WebSocket] Cannot send message - connection not open', { status })
    }
  }, [status, log])

  // Auto-connect when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [isAuthenticated, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeouts()
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [clearTimeouts])

  const isConnected = status === 'connected'

  return {
    status,
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    reconnect,
    connectionAttempts
  }
}

// Specialized hook for portfolio real-time data
export interface PortfolioWebSocketData {
  portfolioValue?: number
  dayChange?: number
  dayChangePercentage?: number
  holdings?: Array<{
    symbol: string
    currentPrice: number
    dayChange: number
    dayChangePercentage: number
  }>
  marketStatus?: 'open' | 'closed' | 'pre-market' | 'after-hours'
  alerts?: Array<{
    id: string
    type: 'price' | 'news' | 'goal' | 'rebalance'
    message: string
    severity: 'info' | 'warning' | 'error'
    timestamp: number
  }>
}

export const usePortfolioWebSocket = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioWebSocketData>({})
  
  const websocket = useWebSocket({
    onMessage: (data, type) => {
      switch (type) {
        case 'portfolio_update':
          setPortfolioData(prev => ({ ...prev, ...data }))
          break
        case 'holding_update':
          setPortfolioData(prev => ({
            ...prev,
            holdings: prev.holdings?.map(h => 
              h.symbol === data.symbol ? { ...h, ...data } : h
            ) || []
          }))
          break
        case 'alert':
          setPortfolioData(prev => ({
            ...prev,
            alerts: [...(prev.alerts || []), data]
          }))
          break
        case 'market_status':
          setPortfolioData(prev => ({ ...prev, marketStatus: data.status }))
          break
        default:
          console.log('[Portfolio WebSocket] Unhandled message type:', type, data)
      }
    },
    debug: true
  })

  const subscribeToSymbol = useCallback((symbol: string) => {
    websocket.sendMessage('subscribe', { symbol })
  }, [websocket])

  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    websocket.sendMessage('unsubscribe', { symbol })
  }, [websocket])

  const clearAlert = useCallback((alertId: string) => {
    setPortfolioData(prev => ({
      ...prev,
      alerts: prev.alerts?.filter(alert => alert.id !== alertId) || []
    }))
  }, [])

  return {
    ...websocket,
    portfolioData,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    clearAlert
  }
}