import messaging, {FirebaseMessagingTypes} from '@react-native-firebase/messaging';
import PushNotification from 'react-native-push-notification';
import {Platform, Alert, Linking} from 'react-native';
import {NotificationPayload} from '@types/common';
import {NOTIFICATION_CONFIG, NOTIFICATION_TOPICS} from '@constants/config';
import {HapticService} from './HapticService';

class NotificationServiceClass {
  private isInitialized: boolean = false;
  private fcmToken: string | null = null;

  /**
   * Initialize notification service
   */
  async initialize(): Promise<void> {
    try {
      // Request permissions
      await this.requestPermissions();

      // Configure push notifications
      this.configurePushNotification();

      // Initialize Firebase messaging
      await this.initializeFirebaseMessaging();

      // Set up notification handlers
      this.setupNotificationHandlers();

      this.isInitialized = true;
      console.log('Notification service initialized successfully');
    } catch (error) {
      console.error('Error initializing notification service:', error);
    }
  }

  /**
   * Request notification permissions
   */
  async requestPermissions(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        const authStatus = await messaging().requestPermission();
        const enabled =
          authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
          authStatus === messaging.AuthorizationStatus.PROVISIONAL;

        if (!enabled) {
          this.showPermissionAlert();
        }

        return enabled;
      } else {
        // Android permissions are handled in the manifest
        return true;
      }
    } catch (error) {
      console.error('Error requesting notification permissions:', error);
      return false;
    }
  }

  /**
   * Check notification permissions
   */
  async checkPermissions(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        const authStatus = await messaging().hasPermission();
        return (
          authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
          authStatus === messaging.AuthorizationStatus.PROVISIONAL
        );
      } else {
        // On Android, check if notifications are enabled
        return new Promise((resolve) => {
          PushNotification.checkPermissions((permissions) => {
            resolve(permissions.alert || permissions.badge || permissions.sound);
          });
        });
      }
    } catch (error) {
      console.error('Error checking notification permissions:', error);
      return false;
    }
  }

  /**
   * Configure push notification library
   */
  private configurePushNotification(): void {
    PushNotification.configure({
      onRegister: (token) => {
        console.log('Device registered for push notifications:', token);
      },

      onNotification: (notification) => {
        console.log('Local notification received:', notification);
        
        // Handle notification tap
        if (notification.userInteraction) {
          this.handleNotificationTap(notification);
        }

        // Trigger haptic feedback
        HapticService.light();

        // Required on iOS only
        if (Platform.OS === 'ios') {
          notification.finish(PushNotification.FetchResult.NoData);
        }
      },

      onAction: (notification) => {
        console.log('Notification action received:', notification);
      },

      onRegistrationError: (err) => {
        console.error('Push notification registration error:', err);
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });

    // Create notification channel for Android
    if (Platform.OS === 'android') {
      PushNotification.createChannel(
        {
          channelId: NOTIFICATION_CONFIG.CHANNEL_ID,
          channelName: NOTIFICATION_CONFIG.CHANNEL_NAME,
          channelDescription: NOTIFICATION_CONFIG.CHANNEL_DESCRIPTION,
          playSound: true,
          soundName: NOTIFICATION_CONFIG.SOUND_NAME,
          importance: 4,
          vibrate: true,
          vibration: NOTIFICATION_CONFIG.VIBRATION_PATTERN[0],
          ledColor: NOTIFICATION_CONFIG.LED_COLOR,
        },
        (created) => {
          console.log('Notification channel created:', created);
        }
      );
    }
  }

  /**
   * Initialize Firebase messaging
   */
  private async initializeFirebaseMessaging(): Promise<void> {
    try {
      // Get FCM token
      this.fcmToken = await messaging().getToken();
      console.log('FCM Token:', this.fcmToken);

      // Listen for token refresh
      messaging().onTokenRefresh((token) => {
        console.log('FCM Token refreshed:', token);
        this.fcmToken = token;
        // Send updated token to server
        this.sendTokenToServer(token);
      });

      // Send token to server
      if (this.fcmToken) {
        this.sendTokenToServer(this.fcmToken);
      }
    } catch (error) {
      console.error('Error initializing Firebase messaging:', error);
    }
  }

  /**
   * Set up notification message handlers
   */
  private setupNotificationHandlers(): void {
    // Handle messages when app is in foreground
    messaging().onMessage(async (remoteMessage) => {
      console.log('Foreground message received:', remoteMessage);
      this.handleForegroundMessage(remoteMessage);
    });

    // Handle messages when app is opened from background
    messaging().onNotificationOpenedApp((remoteMessage) => {
      console.log('Background message opened app:', remoteMessage);
      this.handleNotificationTap(remoteMessage);
    });

    // Handle messages when app is opened from quit state
    messaging()
      .getInitialNotification()
      .then((remoteMessage) => {
        if (remoteMessage) {
          console.log('Quit state message opened app:', remoteMessage);
          this.handleNotificationTap(remoteMessage);
        }
      });

    // Handle background messages
    messaging().setBackgroundMessageHandler(async (remoteMessage) => {
      console.log('Background message received:', remoteMessage);
    });
  }

  /**
   * Handle foreground messages
   */
  private handleForegroundMessage(remoteMessage: FirebaseMessagingTypes.RemoteMessage): void {
    if (remoteMessage.notification) {
      // Show local notification when app is in foreground
      this.showLocalNotification({
        title: remoteMessage.notification.title || 'Financial Planner',
        body: remoteMessage.notification.body || 'You have a new notification',
        data: remoteMessage.data,
      });
    }
  }

  /**
   * Handle notification tap
   */
  private handleNotificationTap(notification: any): void {
    try {
      const data = notification.data || {};
      
      // Navigate based on notification type
      switch (data.type) {
        case 'goal_reminder':
          // Navigate to goals screen
          this.navigateToScreen('Goals', {goalId: data.goalId});
          break;
        case 'market_update':
          // Navigate to dashboard
          this.navigateToScreen('Dashboard');
          break;
        case 'monthly_report':
          // Navigate to reports
          this.navigateToScreen('Reports');
          break;
        case 'security_alert':
          // Navigate to security settings
          this.navigateToScreen('Security');
          break;
        default:
          // Navigate to main screen
          this.navigateToScreen('Dashboard');
      }

      // Trigger haptic feedback
      HapticService.medium();
    } catch (error) {
      console.error('Error handling notification tap:', error);
    }
  }

  /**
   * Navigate to screen (to be implemented with navigation service)
   */
  private navigateToScreen(screen: string, params?: any): void {
    // This would use a navigation service to navigate
    // For now, just log the navigation intent
    console.log('Navigate to:', screen, 'with params:', params);
  }

  /**
   * Send FCM token to server
   */
  private async sendTokenToServer(token: string): Promise<void> {
    try {
      // This would send the token to your backend API
      console.log('Sending token to server:', token);
      
      // Example API call:
      // await ApiService.updateDeviceToken(token);
    } catch (error) {
      console.error('Error sending token to server:', error);
    }
  }

  /**
   * Show local notification
   */
  showLocalNotification(payload: NotificationPayload): void {
    try {
      PushNotification.localNotification({
        channelId: NOTIFICATION_CONFIG.CHANNEL_ID,
        title: payload.title,
        message: payload.body,
        userInfo: payload.data,
        playSound: true,
        soundName: payload.sound || NOTIFICATION_CONFIG.SOUND_NAME,
        number: payload.badge,
        category: payload.category,
        vibrate: true,
        vibration: NOTIFICATION_CONFIG.VIBRATION_PATTERN[0],
        ongoing: false,
        priority: 'high',
        visibility: 'public',
        importance: 'high',
        allowWhileIdle: true,
      });

      // Trigger haptic feedback
      HapticService.light();
    } catch (error) {
      console.error('Error showing local notification:', error);
    }
  }

  /**
   * Schedule goal reminder notification
   */
  scheduleGoalReminder(goalId: string, goalName: string, reminderTime: Date): void {
    try {
      PushNotification.localNotificationSchedule({
        channelId: NOTIFICATION_CONFIG.CHANNEL_ID,
        id: `goal_reminder_${goalId}`,
        title: 'Goal Reminder',
        message: `Don't forget to work on your goal: ${goalName}`,
        date: reminderTime,
        userInfo: {
          type: 'goal_reminder',
          goalId,
        },
        repeatType: 'day', // Daily reminder
        playSound: true,
        soundName: NOTIFICATION_CONFIG.SOUND_NAME,
        vibrate: true,
        allowWhileIdle: true,
      });

      console.log('Goal reminder scheduled for:', reminderTime);
    } catch (error) {
      console.error('Error scheduling goal reminder:', error);
    }
  }

  /**
   * Cancel scheduled notification
   */
  cancelScheduledNotification(notificationId: string): void {
    try {
      PushNotification.cancelLocalNotifications({id: notificationId});
      console.log('Cancelled notification:', notificationId);
    } catch (error) {
      console.error('Error cancelling notification:', error);
    }
  }

  /**
   * Cancel all notifications
   */
  cancelAllNotifications(): void {
    try {
      PushNotification.cancelAllLocalNotifications();
      console.log('Cancelled all notifications');
    } catch (error) {
      console.error('Error cancelling all notifications:', error);
    }
  }

  /**
   * Subscribe to notification topic
   */
  async subscribeToTopic(topic: string): Promise<void> {
    try {
      await messaging().subscribeToTopic(topic);
      console.log('Subscribed to topic:', topic);
    } catch (error) {
      console.error('Error subscribing to topic:', error);
    }
  }

  /**
   * Unsubscribe from notification topic
   */
  async unsubscribeFromTopic(topic: string): Promise<void> {
    try {
      await messaging().unsubscribeFromTopic(topic);
      console.log('Unsubscribed from topic:', topic);
    } catch (error) {
      console.error('Error unsubscribing from topic:', error);
    }
  }

  /**
   * Subscribe to goal reminders
   */
  async enableGoalReminders(): Promise<void> {
    await this.subscribeToTopic(NOTIFICATION_TOPICS.GOAL_REMINDERS);
  }

  /**
   * Unsubscribe from goal reminders
   */
  async disableGoalReminders(): Promise<void> {
    await this.unsubscribeFromTopic(NOTIFICATION_TOPICS.GOAL_REMINDERS);
  }

  /**
   * Subscribe to market updates
   */
  async enableMarketUpdates(): Promise<void> {
    await this.subscribeToTopic(NOTIFICATION_TOPICS.MARKET_UPDATES);
  }

  /**
   * Unsubscribe from market updates
   */
  async disableMarketUpdates(): Promise<void> {
    await this.unsubscribeFromTopic(NOTIFICATION_TOPICS.MARKET_UPDATES);
  }

  /**
   * Get FCM token
   */
  getFCMToken(): string | null {
    return this.fcmToken;
  }

  /**
   * Check if service is initialized
   */
  getInitialized(): boolean {
    return this.isInitialized;
  }

  /**
   * Show permission alert
   */
  private showPermissionAlert(): void {
    Alert.alert(
      'Notification Permission Required',
      'Enable notifications to receive goal reminders and important updates.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Settings',
          onPress: () => {
            Linking.openSettings();
          },
        },
      ]
    );
  }

  /**
   * Test notification (for development)
   */
  testNotification(): void {
    this.showLocalNotification({
      title: 'Test Notification',
      body: 'This is a test notification from Financial Planner',
      data: {type: 'test'},
    });
  }
}

export const NotificationService = new NotificationServiceClass();