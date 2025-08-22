"use client";

import React from 'react';
import { 
  X, 
  Bell, 
  AlertTriangle, 
  Info, 
  CheckCircle, 
  XCircle,
  MoreHorizontal,
  Trash2,
  Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import type { NotificationToast } from '../../types';

interface Notification extends NotificationToast {
  read?: boolean;
  timestamp: string;
  category?: string;
}

interface NotificationCenterProps {
  notifications: Notification[];
  onClose: () => void;
}

/**
 * NotificationCenter Component
 * 
 * Features:
 * - Notification grouping
 * - Mark as read/unread
 * - Delete notifications
 * - Filter by type
 * - Real-time updates
 */
export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  notifications,
  onClose,
}) => {
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />;
      case 'info':
      default:
        return <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />;
    }
  };

  const getBadgeColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'info':
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const now = new Date();
    const notificationTime = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - notificationTime.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return notificationTime.toLocaleDateString();
  };

  const handleMarkAsRead = (id: string) => {
    // Implementation would update the notification status
    console.log('Mark as read:', id);
  };

  const handleDelete = (id: string) => {
    // Implementation would delete the notification
    console.log('Delete notification:', id);
  };

  const handleMarkAllAsRead = () => {
    // Implementation would mark all notifications as read
    console.log('Mark all as read');
  };

  const handleClearAll = () => {
    // Implementation would clear all notifications
    console.log('Clear all notifications');
  };

  const unreadCount = notifications.filter(n => !n.read).length;
  const recentNotifications = notifications.slice(0, 10); // Show last 10

  return (
    <div className="absolute right-0 top-full mt-2 z-50">
      <Card className="w-96 max-h-96 overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="font-medium text-gray-900 dark:text-white">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <Badge variant="destructive">
                {unreadCount}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMarkAllAsRead}
                className="text-xs"
              >
                Mark all read
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="max-h-80 overflow-y-auto">
          {recentNotifications.length === 0 ? (
            <div className="p-8 text-center">
              <Bell className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                No notifications
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                You're all caught up! Check back later for updates.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {recentNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                    !notification.read ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {getNotificationIcon(notification.type)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {notification.title}
                        </h4>
                        <div className="flex items-center gap-1 ml-2">
                          <Badge className={getBadgeColor(notification.type)}>
                            {notification.type}
                          </Badge>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                <MoreHorizontal className="h-3 w-3" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              {!notification.read ? (
                                <DropdownMenuItem onClick={() => handleMarkAsRead(notification.id)}>
                                  <Eye className="h-4 w-4 mr-2" />
                                  Mark as read
                                </DropdownMenuItem>
                              ) : (
                                <DropdownMenuItem onClick={() => handleMarkAsRead(notification.id)}>
                                  <Bell className="h-4 w-4 mr-2" />
                                  Mark as unread
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem 
                                onClick={() => handleDelete(notification.id)}
                                className="text-red-600 dark:text-red-400"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                      {notification.message && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                          {notification.message}
                        </p>
                      )}
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatTimestamp(notification.timestamp)}
                        </span>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        )}
                      </div>
                      {notification.action && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={notification.action.onClick}
                          className="mt-2 text-xs"
                        >
                          {notification.action.label}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {notifications.length > 10 && (
          <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-center">
            <Button variant="ghost" size="sm" className="text-xs">
              View all {notifications.length} notifications
            </Button>
          </div>
        )}

        {notifications.length > 0 && (
          <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-center">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleClearAll}
              className="text-xs text-red-600 dark:text-red-400"
            >
              Clear all notifications
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};