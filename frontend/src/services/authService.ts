import { apiService } from './api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  profileImage?: string;
  createdAt: string;
  lastLogin?: string;
}

export interface AuthResponse {
  token: string;
  user: User;
  refreshToken?: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
}

class AuthService {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await apiService.post<AuthResponse>('/auth/login', credentials);
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Register new user
   */
  async register(userData: RegisterData): Promise<AuthResponse> {
    try {
      const response = await apiService.post<AuthResponse>('/auth/register', userData);
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      await apiService.post('/auth/logout');
    } catch (error) {
      console.error('Logout failed:', error);
      // Don't throw error for logout failures, just clear local state
    } finally {
      apiService.clearToken();
      localStorage.removeItem('refresh_token');
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await apiService.post<AuthResponse>('/auth/refresh', {
        refreshToken,
      });
      return response;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear tokens on refresh failure
      apiService.clearToken();
      localStorage.removeItem('refresh_token');
      throw this.handleAuthError(error);
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiService.get<User>('/auth/me');
      return response;
    } catch (error) {
      console.error('Get current user failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    try {
      const response = await apiService.put<User>('/auth/profile', userData);
      return response;
    } catch (error) {
      console.error('Profile update failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Change password
   */
  async changePassword(passwordData: ChangePasswordData): Promise<void> {
    try {
      await apiService.post('/auth/change-password', passwordData);
    } catch (error) {
      console.error('Password change failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    try {
      await apiService.post('/auth/password-reset', data);
    } catch (error) {
      console.error('Password reset request failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Confirm password reset with token
   */
  async confirmPasswordReset(data: PasswordResetConfirm): Promise<void> {
    try {
      await apiService.post('/auth/password-reset/confirm', data);
    } catch (error) {
      console.error('Password reset confirmation failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Verify email with token
   */
  async verifyEmail(token: string): Promise<void> {
    try {
      await apiService.post('/auth/verify-email', { token });
    } catch (error) {
      console.error('Email verification failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Resend email verification
   */
  async resendEmailVerification(): Promise<void> {
    try {
      await apiService.post('/auth/verify-email/resend');
    } catch (error) {
      console.error('Resend verification failed:', error);
      throw this.handleAuthError(error);
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('auth_token');
    return !!token;
  }

  /**
   * Get stored auth token
   */
  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  /**
   * Get stored refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  /**
   * Handle authentication errors and provide user-friendly messages
   */
  private handleAuthError(error: any): Error {
    if (error?.message) {
      // Check for common API error patterns
      if (error.message.includes('401')) {
        return new Error('Invalid credentials. Please check your email and password.');
      }
      if (error.message.includes('403')) {
        return new Error('Access denied. Please verify your account.');
      }
      if (error.message.includes('409')) {
        return new Error('An account with this email already exists.');
      }
      if (error.message.includes('422')) {
        return new Error('Please provide valid information.');
      }
      if (error.message.includes('429')) {
        return new Error('Too many attempts. Please try again later.');
      }
      if (error.message.includes('500')) {
        return new Error('Server error. Please try again later.');
      }
    }

    return new Error(error?.message || 'An unexpected error occurred. Please try again.');
  }
}

export const authService = new AuthService();
export default authService;