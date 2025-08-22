import React, { createContext, useContext, useState, useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import * as Haptics from 'expo-haptics';

export interface AppNotification {
  id: string;
  title: string;
  body: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: Date;
  read: boolean;
  action?: {
    label: string;
    onPress: () => void;
  };
}

interface NotificationContextType {
  notifications: AppNotification[];
  unreadCount: number;
  showNotification: (notification: Omit<AppNotification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotification: (id: string) => void;
  clearAll: () => void;
  scheduleDemoNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  useEffect(() => {
    // Schedule demo notifications when the app starts
    scheduleDemoNotifications();
    
    // Set up notification listeners
    const subscription = Notifications.addNotificationReceivedListener(notification => {
      showNotification({
        title: notification.request.content.title || 'Notification',
        body: notification.request.content.body || '',
        type: 'info',
      });
    });

    return () => subscription.remove();
  }, []);

  const showNotification = (notificationData: Omit<AppNotification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: AppNotification = {
      ...notificationData,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false,
    };

    setNotifications(prev => [newNotification, ...prev]);
    
    // Provide haptic feedback
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    );
  };

  const clearNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const scheduleDemoNotifications = async () => {
    try {
      // Cancel all existing notifications
      await Notifications.cancelAllScheduledNotificationsAsync();

      // Schedule goal progress notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Goal Progress Update',
          body: "You're 60% closer to your Emergency Fund goal! Keep it up!",
          data: { type: 'goal_progress' },
        },
        trigger: { seconds: 10 },
      });

      // Schedule market alert notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Market Alert',
          body: 'Your portfolio is up 2.3% today. Great job on your investments!',
          data: { type: 'market_alert' },
        },
        trigger: { seconds: 30 },
      });

      // Schedule spending reminder
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Budget Reminder',
          body: "You've spent 75% of your dining budget this month. Consider cooking at home!",
          data: { type: 'budget_reminder' },
        },
        trigger: { seconds: 50 },
      });

      // Schedule achievement notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Achievement Unlocked!',
          body: 'Congratulations! You completed the "Savings Streak" challenge!',
          data: { type: 'achievement' },
        },
        trigger: { seconds: 70 },
      });

      // Add some initial notifications
      const initialNotifications: AppNotification[] = [
        {
          id: '1',
          title: 'Welcome to Financial Planner!',
          body: 'Explore the app and set up your first financial goal.',
          type: 'info',
          timestamp: new Date(Date.now() - 3600000), // 1 hour ago
          read: false,
        },
        {
          id: '2',
          title: 'Market Update',
          body: 'S&P 500 is up 0.8% today. Your diversified portfolio is performing well.',
          type: 'success',
          timestamp: new Date(Date.now() - 7200000), // 2 hours ago
          read: true,
        },
        {
          id: '3',
          title: 'Bill Reminder',
          body: 'Your credit card payment is due in 3 days.',
          type: 'warning',
          timestamp: new Date(Date.now() - 86400000), // 1 day ago
          read: false,
        },
      ];

      setNotifications(initialNotifications);
    } catch (error) {
      console.error('Error scheduling demo notifications:', error);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const value: NotificationContextType = {
    notifications,
    unreadCount,
    showNotification,
    markAsRead,
    markAllAsRead,
    clearNotification,
    clearAll,
    scheduleDemoNotifications,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};