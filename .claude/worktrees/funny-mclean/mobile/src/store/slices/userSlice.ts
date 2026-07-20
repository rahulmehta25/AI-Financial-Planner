import {createSlice, createAsyncThunk, PayloadAction} from '@reduxjs/toolkit';
import {UserState, UserProfile, UserPreferences, UpdateProfileRequest, UpdatePreferencesRequest} from '@types/user';
import {ApiError} from '@types/api';

const initialState: UserState = {
  profile: null,
  preferences: {
    notifications: {
      pushEnabled: true,
      emailEnabled: true,
      goalReminders: true,
      marketUpdates: false,
      monthlyReports: true,
      securityAlerts: true,
      reminderTime: '09:00',
    },
    privacy: {
      shareDataForResearch: false,
      allowAnalytics: true,
      biometricEnabled: false,
      autoLockEnabled: true,
      autoLockTimeout: 5,
    },
    appearance: {
      theme: 'system',
      fontSize: 'medium',
      reducedMotion: false,
    },
    language: 'en',
    currency: 'USD',
    timezone: 'America/New_York',
  },
  hasCompletedOnboarding: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const updateProfile = createAsyncThunk<
  UserProfile,
  UpdateProfileRequest,
  {rejectValue: ApiError}
>('user/updateProfile', async (profileData, {rejectWithValue}) => {
  try {
    // This would call the API service
    const response = await fetch('/api/users/profile', {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(profileData),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update profile');
    }
    
    return await response.json();
  } catch (error: any) {
    return rejectWithValue({
      message: error.message,
      status: 500,
    });
  }
});

export const updatePreferences = createAsyncThunk<
  UserPreferences,
  UpdatePreferencesRequest,
  {rejectValue: ApiError}
>('user/updatePreferences', async (preferences, {rejectWithValue}) => {
  try {
    // This would call the API service
    const response = await fetch('/api/users/preferences', {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(preferences),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update preferences');
    }
    
    return await response.json();
  } catch (error: any) {
    return rejectWithValue({
      message: error.message,
      status: 500,
    });
  }
});

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setProfile: (state, action: PayloadAction<UserProfile>) => {
      state.profile = action.payload;
    },
    setPreferences: (state, action: PayloadAction<UserPreferences>) => {
      state.preferences = action.payload;
    },
    updateNotificationPreferences: (state, action: PayloadAction<Partial<UserState['preferences']['notifications']>>) => {
      state.preferences.notifications = {
        ...state.preferences.notifications,
        ...action.payload,
      };
    },
    updatePrivacyPreferences: (state, action: PayloadAction<Partial<UserState['preferences']['privacy']>>) => {
      state.preferences.privacy = {
        ...state.preferences.privacy,
        ...action.payload,
      };
    },
    updateAppearancePreferences: (state, action: PayloadAction<Partial<UserState['preferences']['appearance']>>) => {
      state.preferences.appearance = {
        ...state.preferences.appearance,
        ...action.payload,
      };
    },
    setHasCompletedOnboarding: (state, action: PayloadAction<boolean>) => {
      state.hasCompletedOnboarding = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetUserState: (state) => {
      state.profile = null;
      state.hasCompletedOnboarding = false;
      state.error = null;
      // Keep preferences as they might be device-specific
    },
  },
  extraReducers: (builder) => {
    // Update Profile
    builder
      .addCase(updateProfile.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.isLoading = false;
        state.profile = action.payload;
        state.error = null;
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Failed to update profile';
      });

    // Update Preferences
    builder
      .addCase(updatePreferences.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updatePreferences.fulfilled, (state, action) => {
        state.isLoading = false;
        state.preferences = action.payload;
        state.error = null;
      })
      .addCase(updatePreferences.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Failed to update preferences';
      });
  },
});

export const {
  setProfile,
  setPreferences,
  updateNotificationPreferences,
  updatePrivacyPreferences,
  updateAppearancePreferences,
  setHasCompletedOnboarding,
  clearError,
  resetUserState,
} = userSlice.actions;

export default userSlice.reducer;