export interface UserState {
  profile: UserProfile | null;
  preferences: UserPreferences;
  hasCompletedOnboarding: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface UserProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  phone?: string;
  dateOfBirth?: string;
  address?: Address;
  occupation?: string;
  income?: number;
  createdAt: string;
  updatedAt: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface UserPreferences {
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  appearance: AppearancePreferences;
  language: string;
  currency: string;
  timezone: string;
}

export interface NotificationPreferences {
  pushEnabled: boolean;
  emailEnabled: boolean;
  goalReminders: boolean;
  marketUpdates: boolean;
  monthlyReports: boolean;
  securityAlerts: boolean;
  reminderTime: string; // HH:mm format
}

export interface PrivacyPreferences {
  shareDataForResearch: boolean;
  allowAnalytics: boolean;
  biometricEnabled: boolean;
  autoLockEnabled: boolean;
  autoLockTimeout: number; // minutes
}

export interface AppearancePreferences {
  theme: 'light' | 'dark' | 'system';
  fontSize: 'small' | 'medium' | 'large';
  reducedMotion: boolean;
}

export interface UpdateProfileRequest {
  firstName?: string;
  lastName?: string;
  phone?: string;
  dateOfBirth?: string;
  address?: Address;
  occupation?: string;
  income?: number;
}

export interface UpdatePreferencesRequest {
  notifications?: Partial<NotificationPreferences>;
  privacy?: Partial<PrivacyPreferences>;
  appearance?: Partial<AppearancePreferences>;
  language?: string;
  currency?: string;
  timezone?: string;
}