'use client';

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage, RealTimeData, AnalyticsAlert } from '@/types/analytics';

interface WebSocketContextType {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastMessage: WebSocketMessage | null;
  realTimeData: RealTimeData | null;
  alerts: AnalyticsAlert[];
  connect: (url: string) => void;
  disconnect: () => void;
  sendMessage: (message: any) => void;
  subscribe: (messageType: string, callback: (data: any) => void) => () => void;
  acknowledgAlert: (alertId: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: React.ReactNode;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  url?: string;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  autoConnect = false,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5,
  url: defaultUrl = 'ws://localhost:8000/ws/portfolio'
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [realTimeData, setRealTimeData] = useState<RealTimeData | null>(null);
  const [alerts, setAlerts] = useState<AnalyticsAlert[]>([]);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const subscribers = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const heartbeatInterval = useRef<NodeJS.Timeout | null>(null);

  // Subscribe to message types
  const subscribe = useCallback((messageType: string, callback: (data: any) => void) => {
    if (!subscribers.current.has(messageType)) {
      subscribers.current.set(messageType, new Set());
    }
    subscribers.current.get(messageType)?.add(callback);

    // Return unsubscribe function
    return () => {
      subscribers.current.get(messageType)?.delete(callback);
      if (subscribers.current.get(messageType)?.size === 0) {
        subscribers.current.delete(messageType);
      }
    };
  }, []);

  // Notify subscribers
  const notifySubscribers = useCallback((messageType: string, data: any) => {
    const typeSubscribers = subscribers.current.get(messageType);
    if (typeSubscribers) {
      typeSubscribers.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket subscriber:', error);
        }
      });
    }
  }, []);

  // Process incoming messages
  const processMessage = useCallback((message: WebSocketMessage) => {
    setLastMessage(message);
    
    switch (message.type) {
      case 'portfolio_update':
        setRealTimeData(message.data as RealTimeData);
        notifySubscribers('portfolio_update', message.data);
        break;
        
      case 'market_data':
        // Update holdings prices in real-time data
        if (realTimeData && message.data.holdings) {
          setRealTimeData(prev => prev ? {
            ...prev,
            holdings: prev.holdings.map(holding => {
              const update = message.data.holdings.find((h: any) => h.symbol === holding.symbol);
              return update ? { ...holding, ...update } : holding;
            })
          } : null);
        }
        notifySubscribers('market_data', message.data);
        break;
        
      case 'risk_alert':
        const alert: AnalyticsAlert = {
          id: `alert-${Date.now()}`,
          ...message.data,
          timestamp: new Date(message.timestamp),
          acknowledged: false
        };
        setAlerts(prev => [alert, ...prev].slice(0, 20)); // Keep only last 20 alerts
        notifySubscribers('risk_alert', alert);
        break;
        
      case 'performance_update':
        notifySubscribers('performance_update', message.data);
        break;
        
      default:
        console.warn('Unknown message type:', message.type);
    }
  }, [realTimeData, notifySubscribers]);

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
    }
    
    heartbeatInterval.current = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: 'ping', timestamp: new Date() }));
      }
    }, 30000); // Send ping every 30 seconds
  }, []);

  // Stop heartbeat
  const stopHeartbeat = useCallback(() => {
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
      heartbeatInterval.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback((url: string = defaultUrl) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionStatus('connecting');
    
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttempts.current = 0;
        startHeartbeat();
        
        // Send initial subscription message
        if (ws.current) {
          ws.current.send(JSON.stringify({
            type: 'subscribe',
            channels: ['portfolio_updates', 'market_data', 'risk_alerts', 'performance_updates']
          }));
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Handle pong responses
          if (message.type === 'pong') {
            return;
          }
          
          processMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        stopHeartbeat();
        
        // Attempt to reconnect if not manually closed
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          console.log(`Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})`);
          
          reconnectTimeout.current = setTimeout(() => {
            connect(url);
          }, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [defaultUrl, maxReconnectAttempts, reconnectInterval, processMessage, startHeartbeat, stopHeartbeat]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    
    stopHeartbeat();
    
    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
    reconnectAttempts.current = 0;
  }, [stopHeartbeat]);

  // Send message
  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Acknowledge alert
  const acknowledgeAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ));
    
    // Send acknowledgment to server
    sendMessage({
      type: 'acknowledge_alert',
      alertId,
      timestamp: new Date()
    });
  }, [sendMessage]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, consider reducing update frequency
        sendMessage({ type: 'set_update_frequency', frequency: 'low' });
      } else {
        // Page is visible, resume normal updates
        sendMessage({ type: 'set_update_frequency', frequency: 'normal' });
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [sendMessage]);

  const value: WebSocketContextType = {
    isConnected,
    connectionStatus,
    lastMessage,
    realTimeData,
    alerts,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    acknowledgAlert: acknowledgeAlert
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Hook for real-time portfolio data
export const useRealTimePortfolio = () => {
  const { realTimeData, subscribe } = useWebSocket();
  const [data, setData] = useState<RealTimeData | null>(realTimeData);

  useEffect(() => {
    const unsubscribe = subscribe('portfolio_update', (portfolioData: RealTimeData) => {
      setData(portfolioData);
    });

    return unsubscribe;
  }, [subscribe]);

  return data;
};

// Hook for real-time market data
export const useRealTimeMarket = () => {
  const { subscribe } = useWebSocket();
  const [marketData, setMarketData] = useState<any>(null);

  useEffect(() => {
    const unsubscribe = subscribe('market_data', (data: any) => {
      setMarketData(data);
    });

    return unsubscribe;
  }, [subscribe]);

  return marketData;
};

// Hook for risk alerts
export const useRiskAlerts = () => {
  const { alerts, acknowledgAlert } = useWebSocket();
  const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged);

  return {
    alerts,
    unacknowledgedAlerts,
    acknowledgAlert
  };
};

// Connection status indicator component
export const ConnectionStatus: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { connectionStatus, isConnected } = useWebSocket();

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Connection Error';
      default: return 'Disconnected';
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
      <span className="text-xs text-gray-600 dark:text-gray-400">
        {getStatusText()}
      </span>
    </div>
  );
};

export default WebSocketProvider;