import React, { useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useNotifications } from '../../contexts/NotificationContext';

const NotificationsScreen: React.FC = () => {
  const { colors } = useTheme();
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotification,
    clearAll,
  } = useNotifications();
  
  const fadeAnim = useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();
  }, []);

  const handleMarkAllRead = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    markAllAsRead();
  };

  const handleClearAll = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    clearAll();
  };

  const handleNotificationPress = (id: string, read: boolean) => {
    if (!read) {
      markAsRead(id);
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleDeleteNotification = (id: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    clearNotification(id);
  };

  const getNotificationIcon = (type: string) => {
    const icons: { [key: string]: keyof typeof Ionicons.glyphMap } = {
      info: 'information-circle-outline',
      success: 'checkmark-circle-outline',
      warning: 'warning-outline',
      error: 'alert-circle-outline',
    };
    return icons[type] || 'notifications-outline';
  };

  const getNotificationColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      info: colors.primary[500],
      success: colors.success[500],
      warning: colors.warning[500],
      error: colors.error[500],
    };
    return colorMap[type] || colors.primary[500];
  };

  const formatTime = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    
    if (diff < 60000) { // Less than 1 minute
      return 'Just now';
    } else if (diff < 3600000) { // Less than 1 hour
      const minutes = Math.floor(diff / 60000);
      return `${minutes}m ago`;
    } else if (diff < 86400000) { // Less than 1 day
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    } else {
      const days = Math.floor(diff / 86400000);
      return `${days}d ago`;
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <View>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            Notifications
          </Text>
          <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
            {unreadCount} unread notifications
          </Text>
        </View>
        
        {notifications.length > 0 && (
          <View style={styles.headerActions}>
            {unreadCount > 0 && (
              <TouchableOpacity
                style={[styles.headerButton, { backgroundColor: colors.primary[500] }]}
                onPress={handleMarkAllRead}
              >
                <Text style={styles.headerButtonText}>Mark All Read</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={[styles.headerButton, { backgroundColor: colors.error[500] }]}
              onPress={handleClearAll}
            >
              <Ionicons name="trash-outline" size={16} color="white" />
            </TouchableOpacity>
          </View>
        )}
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[{ opacity: fadeAnim }, styles.content]}>
          {notifications.length > 0 ? (
            <View style={styles.notificationsList}>
              {notifications.map((notification) => (
                <TouchableOpacity
                  key={notification.id}
                  style={[
                    styles.notificationItem,
                    {
                      backgroundColor: notification.read ? colors.surface : `${colors.primary[50]}`,
                      borderLeftColor: getNotificationColor(notification.type),
                    },
                  ]}
                  onPress={() => handleNotificationPress(notification.id, notification.read)}
                >
                  <View style={styles.notificationContent}>
                    <View style={styles.notificationHeader}>
                      <View style={styles.notificationLeft}>
                        <View
                          style={[
                            styles.iconContainer,
                            { backgroundColor: `${getNotificationColor(notification.type)}15` },
                          ]}
                        >
                          <Ionicons
                            name={getNotificationIcon(notification.type)}
                            size={20}
                            color={getNotificationColor(notification.type)}
                          />
                        </View>
                        <View style={styles.notificationInfo}>
                          <Text
                            style={[
                              styles.notificationTitle,
                              {
                                color: colors.text,
                                fontWeight: notification.read ? '500' : 'bold',
                              },
                            ]}
                          >
                            {notification.title}
                          </Text>
                          <Text style={[styles.notificationTime, { color: colors.textSecondary }]}>
                            {formatTime(notification.timestamp)}
                          </Text>
                        </View>
                      </View>
                      
                      <View style={styles.notificationRight}>
                        {!notification.read && (
                          <View style={[styles.unreadDot, { backgroundColor: colors.primary[500] }]} />
                        )}
                        <TouchableOpacity
                          style={styles.deleteButton}
                          onPress={() => handleDeleteNotification(notification.id)}
                        >
                          <Ionicons name="close" size={16} color={colors.textSecondary} />
                        </TouchableOpacity>
                      </View>
                    </View>
                    
                    <Text style={[styles.notificationBody, { color: colors.textSecondary }]}>
                      {notification.body}
                    </Text>
                    
                    {notification.action && (
                      <TouchableOpacity
                        style={[styles.actionButton, { borderColor: colors.primary[500] }]}
                        onPress={notification.action.onPress}
                      >
                        <Text style={[styles.actionButtonText, { color: colors.primary[500] }]}>
                          {notification.action.label}
                        </Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          ) : (
            <View style={styles.emptyState}>
              <View style={[styles.emptyIconContainer, { backgroundColor: colors.surface }]}>
                <Ionicons name="notifications-outline" size={60} color={colors.textSecondary} />
              </View>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>
                No Notifications Yet
              </Text>
              <Text style={[styles.emptyDescription, { color: colors.textSecondary }]}>
                You're all caught up! We'll notify you about important updates to your financial progress.
              </Text>
              
              <TouchableOpacity
                style={[styles.emptyButton, { backgroundColor: colors.primary[500] }]}
                onPress={() => {
                  // Trigger a demo notification
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                }}
              >
                <Ionicons name="add" size={20} color="white" />
                <Text style={styles.emptyButtonText}>Test Notification</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Notification Settings */}
          <View style={[styles.settingsCard, { backgroundColor: colors.surface }]}>
            <Text style={[styles.settingsTitle, { color: colors.text }]}>
              Notification Settings
            </Text>
            
            <View style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Ionicons name="trending-up" size={20} color={colors.success[500]} />
                <Text style={[styles.settingText, { color: colors.text }]}>
                  Portfolio Updates
                </Text>
              </View>
              <View style={[styles.toggle, { backgroundColor: colors.success[500] }]}>
                <View style={[styles.toggleButton, { backgroundColor: 'white' }]} />
              </View>
            </View>
            
            <View style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Ionicons name="flag" size={20} color={colors.primary[500]} />
                <Text style={[styles.settingText, { color: colors.text }]}>
                  Goal Progress
                </Text>
              </View>
              <View style={[styles.toggle, { backgroundColor: colors.primary[500] }]}>
                <View style={[styles.toggleButton, { backgroundColor: 'white' }]} />
              </View>
            </View>
            
            <View style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Ionicons name="card" size={20} color={colors.warning[500]} />
                <Text style={[styles.settingText, { color: colors.text }]}>
                  Budget Alerts
                </Text>
              </View>
              <View style={[styles.toggle, { backgroundColor: colors.secondary[300] }]}>
                <View style={[styles.toggleButton, { backgroundColor: 'white', marginLeft: 2 }]} />
              </View>
            </View>
          </View>
        </Animated.View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 8,
  },
  headerButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  content: {
    padding: 20,
  },
  notificationsList: {
    marginBottom: 24,
  },
  notificationItem: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  notificationContent: {},
  notificationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  notificationLeft: {
    flexDirection: 'row',
    flex: 1,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  notificationInfo: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 16,
    marginBottom: 2,
  },
  notificationTime: {
    fontSize: 12,
  },
  notificationRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  deleteButton: {
    padding: 4,
  },
  notificationBody: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
    paddingLeft: 52,
  },
  actionButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    alignSelf: 'flex-start',
    marginLeft: 52,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    marginBottom: 40,
  },
  emptyIconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
    paddingHorizontal: 40,
    lineHeight: 24,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
  },
  emptyButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  settingsCard: {
    borderRadius: 16,
    padding: 20,
  },
  settingsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  settingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingText: {
    fontSize: 16,
    marginLeft: 12,
  },
  toggle: {
    width: 44,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    position: 'relative',
  },
  toggleButton: {
    width: 20,
    height: 20,
    borderRadius: 10,
    marginLeft: 20,
  },
});

export default NotificationsScreen;