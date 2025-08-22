import {Platform} from 'react-native';

// API Configuration
export const API_CONFIG = {
  BASE_URL: __DEV__ 
    ? Platform.select({
        ios: 'http://localhost:8000',
        android: 'http://10.0.2.2:8000',
      })
    : 'https://api.financialplanner.com',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// App Configuration
export const APP_CONFIG = {
  NAME: 'Financial Planner',
  VERSION: '1.0.0',
  BUILD_NUMBER: '1',
  BUNDLE_ID: 'com.financialplanner.mobile',
  DEEP_LINK_SCHEME: 'financialplanner',
  STORE_URL: {
    ios: 'https://apps.apple.com/app/financial-planner/id123456789',
    android: 'https://play.google.com/store/apps/details?id=com.financialplanner.mobile',
  },
};

// Storage Keys
export const STORAGE_KEYS = {
  USER_TOKEN: 'userToken',
  REFRESH_TOKEN: 'refreshToken',
  USER_PROFILE: 'userProfile',
  USER_PREFERENCES: 'userPreferences',
  BIOMETRIC_ENABLED: 'biometricEnabled',
  ONBOARDING_COMPLETED: 'onboardingCompleted',
  OFFLINE_QUEUE: 'offlineQueue',
  LAST_SYNC_TIME: 'lastSyncTime',
  THEME_PREFERENCE: 'themePreference',
  LANGUAGE_PREFERENCE: 'languagePreference',
};

// Biometric Configuration
export const BIOMETRIC_CONFIG = {
  TITLE: 'Authenticate',
  SUBTITLE: 'Use your biometric to access the app',
  DESCRIPTION: 'Place your finger on the sensor or look at the camera',
  FALLBACK_TITLE: 'Use Passcode',
  NEGATIVE_TEXT: 'Cancel',
  DISABLE_BACKUP: false,
};

// Camera Configuration
export const CAMERA_CONFIG = {
  QUALITY: 0.8,
  ALLOWS_EDITING: true,
  ASPECT: [4, 3] as [number, number],
  BASE64: false,
  MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
  ALLOWED_TYPES: ['jpg', 'jpeg', 'png', 'pdf'],
};

// Document Scanner Configuration
export const DOCUMENT_SCANNER_CONFIG = {
  QUALITY: 2,
  LETTER_SIZE: false,
  RESPONSE_TYPE: 'imageFilePath' as const,
  CROPPING_ENABLED: true,
  OVERLAY_COLOR: 'rgba(255, 255, 255, 0.3)',
};

// Notification Configuration
export const NOTIFICATION_CONFIG = {
  CHANNEL_ID: 'financial_planner_notifications',
  CHANNEL_NAME: 'Financial Planner',
  CHANNEL_DESCRIPTION: 'Notifications for goal reminders and updates',
  SOUND_NAME: 'default',
  VIBRATION_PATTERN: [1000, 500, 1000],
  LED_COLOR: '#3B82F6',
};

// Push Notification Topics
export const NOTIFICATION_TOPICS = {
  GOAL_REMINDERS: 'goal_reminders',
  MARKET_UPDATES: 'market_updates',
  MONTHLY_REPORTS: 'monthly_reports',
  SECURITY_ALERTS: 'security_alerts',
};

// Form Validation
export const VALIDATION_CONFIG = {
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_REGEX: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE_REGEX: /^\+?[\d\s\-\(\)]+$/,
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 50,
};

// Offline Configuration
export const OFFLINE_CONFIG = {
  MAX_QUEUE_SIZE: 100,
  SYNC_INTERVAL: 5 * 60 * 1000, // 5 minutes
  MAX_RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 2000,
  CONFLICT_RESOLUTION_TIMEOUT: 24 * 60 * 60 * 1000, // 24 hours
};

// Animation Configuration
export const ANIMATION_CONFIG = {
  SPRING: {
    tension: 100,
    friction: 8,
  },
  TIMING: {
    duration: 300,
    useNativeDriver: true,
  },
  GESTURE: {
    enabled: true,
    gestureDirection: 'horizontal' as const,
  },
};

// Security Configuration
export const SECURITY_CONFIG = {
  AUTO_LOCK_TIMEOUT: 5 * 60 * 1000, // 5 minutes
  MAX_LOGIN_ATTEMPTS: 5,
  LOCKOUT_DURATION: 15 * 60 * 1000, // 15 minutes
  SESSION_TIMEOUT: 24 * 60 * 60 * 1000, // 24 hours
  ENCRYPTION_ALGORITHM: 'AES-256-GCM',
};

// Feature Flags
export const FEATURE_FLAGS = {
  BIOMETRIC_AUTH: true,
  PUSH_NOTIFICATIONS: true,
  DOCUMENT_SCANNER: true,
  OFFLINE_MODE: true,
  HAPTIC_FEEDBACK: true,
  DARK_MODE: true,
  ANALYTICS: !__DEV__,
  CRASH_REPORTING: !__DEV__,
};

// Development Configuration
export const DEV_CONFIG = {
  SHOW_PERFORMANCE_MONITOR: __DEV__,
  ENABLE_FLIPPER: __DEV__,
  LOG_LEVEL: __DEV__ ? 'debug' : 'error',
  ENABLE_REDUX_DEVTOOLS: __DEV__,
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection error. Please check your internet connection.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  AUTHENTICATION_ERROR: 'Authentication failed. Please log in again.',
  BIOMETRIC_ERROR: 'Biometric authentication failed. Please try again.',
  CAMERA_ERROR: 'Camera access denied. Please enable camera permissions.',
  LOCATION_ERROR: 'Location access denied. Please enable location permissions.',
  GENERIC_ERROR: 'An unexpected error occurred. Please try again.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Successfully logged in!',
  REGISTRATION_SUCCESS: 'Account created successfully!',
  PROFILE_UPDATED: 'Profile updated successfully!',
  GOAL_CREATED: 'Goal created successfully!',
  GOAL_UPDATED: 'Goal updated successfully!',
  DOCUMENT_UPLOADED: 'Document uploaded successfully!',
  SYNC_SUCCESS: 'Data synchronized successfully!',
};

export default {
  API_CONFIG,
  APP_CONFIG,
  STORAGE_KEYS,
  BIOMETRIC_CONFIG,
  CAMERA_CONFIG,
  DOCUMENT_SCANNER_CONFIG,
  NOTIFICATION_CONFIG,
  NOTIFICATION_TOPICS,
  VALIDATION_CONFIG,
  OFFLINE_CONFIG,
  ANIMATION_CONFIG,
  SECURITY_CONFIG,
  FEATURE_FLAGS,
  DEV_CONFIG,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
};