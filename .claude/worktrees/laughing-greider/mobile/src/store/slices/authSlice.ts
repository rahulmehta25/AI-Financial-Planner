import {createSlice, createAsyncThunk, PayloadAction} from '@reduxjs/toolkit';
import {
  AuthState,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  BiometricAuthResult,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from '@types/auth';
import {ApiError} from '@types/api';
import {AuthService} from '@services/AuthService';
import {BiometricService} from '@services/BiometricService';
import {resetStore} from '../store';

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  refreshToken: null,
  biometricEnabled: false,
  biometricType: null,
  isLoading: false,
  error: null,
};

// Async thunks
export const login = createAsyncThunk<
  AuthResponse,
  LoginRequest,
  {rejectValue: ApiError}
>('auth/login', async (credentials, {rejectWithValue}) => {
  try {
    const response = await AuthService.login(credentials);
    return response;
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

export const register = createAsyncThunk<
  AuthResponse,
  RegisterRequest,
  {rejectValue: ApiError}
>('auth/register', async (userData, {rejectWithValue}) => {
  try {
    const response = await AuthService.register(userData);
    return response;
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

export const forgotPassword = createAsyncThunk<
  {message: string},
  ForgotPasswordRequest,
  {rejectValue: ApiError}
>('auth/forgotPassword', async (data, {rejectWithValue}) => {
  try {
    const response = await AuthService.forgotPassword(data);
    return response;
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

export const resetPassword = createAsyncThunk<
  {message: string},
  ResetPasswordRequest,
  {rejectValue: ApiError}
>('auth/resetPassword', async (data, {rejectWithValue}) => {
  try {
    const response = await AuthService.resetPassword(data);
    return response;
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

export const refreshToken = createAsyncThunk<
  {token: string; refreshToken: string},
  void,
  {rejectValue: ApiError}
>('auth/refreshToken', async (_, {getState, rejectWithValue}) => {
  try {
    const state = getState() as any;
    const currentRefreshToken = state.auth.refreshToken;
    
    if (!currentRefreshToken) {
      throw new Error('No refresh token available');
    }
    
    const response = await AuthService.refreshToken(currentRefreshToken);
    return response;
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

export const authenticateWithBiometric = createAsyncThunk<
  BiometricAuthResult,
  void,
  {rejectValue: ApiError}
>('auth/authenticateWithBiometric', async (_, {rejectWithValue}) => {
  try {
    const result = await BiometricService.authenticate();
    return result;
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

export const enableBiometric = createAsyncThunk<
  {enabled: boolean; type: string},
  void,
  {rejectValue: ApiError}
>('auth/enableBiometric', async (_, {rejectWithValue}) => {
  try {
    const result = await BiometricService.enableBiometric();
    return result;
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

export const disableBiometric = createAsyncThunk<
  void,
  void,
  {rejectValue: ApiError}
>('auth/disableBiometric', async (_, {rejectWithValue}) => {
  try {
    await BiometricService.disableBiometric();
  } catch (error: any) {
    return rejectWithValue(error);
  }
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.error = null;
      // Note: biometricEnabled is preserved
    },
    clearError: (state) => {
      state.error = null;
    },
    setTokens: (state, action: PayloadAction<{token: string; refreshToken: string}>) => {
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
    },
    setBiometricType: (state, action: PayloadAction<string | null>) => {
      state.biometricType = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Login failed';
      });

    // Register
    builder
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Registration failed';
      });

    // Forgot Password
    builder
      .addCase(forgotPassword.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(forgotPassword.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(forgotPassword.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Password reset request failed';
      });

    // Reset Password
    builder
      .addCase(resetPassword.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(resetPassword.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(resetPassword.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Password reset failed';
      });

    // Refresh Token
    builder
      .addCase(refreshToken.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
        state.error = null;
      })
      .addCase(refreshToken.rejected, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
      });

    // Biometric Authentication
    builder
      .addCase(authenticateWithBiometric.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(authenticateWithBiometric.fulfilled, (state, action) => {
        state.isLoading = false;
        if (action.payload.success) {
          state.isAuthenticated = true;
        }
        state.error = null;
      })
      .addCase(authenticateWithBiometric.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Biometric authentication failed';
      });

    // Enable Biometric
    builder
      .addCase(enableBiometric.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(enableBiometric.fulfilled, (state, action) => {
        state.isLoading = false;
        state.biometricEnabled = action.payload.enabled;
        state.biometricType = action.payload.type;
        state.error = null;
      })
      .addCase(enableBiometric.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Failed to enable biometric authentication';
      });

    // Disable Biometric
    builder
      .addCase(disableBiometric.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(disableBiometric.fulfilled, (state) => {
        state.isLoading = false;
        state.biometricEnabled = false;
        state.biometricType = null;
        state.error = null;
      })
      .addCase(disableBiometric.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Failed to disable biometric authentication';
      });
  },
});

export const {logout, clearError, setTokens, setBiometricType} = authSlice.actions;
export default authSlice.reducer;