import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiService } from '@/services/api';

interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  profileImage?: string;
  createdAt: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
}

interface RegisterData {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

interface AuthResponse {
  token: string;
  user: User;
  refreshToken?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Initialize auth state from stored token
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          // Check for demo token first
          if (token === 'demo-token') {
            const demoUser: User = {
              id: 'demo-user-id',
              email: 'demo@financeai.com',
              firstName: 'Demo',
              lastName: 'User',
              createdAt: new Date().toISOString(),
            };
            setUser(demoUser);
            setIsLoading(false);
            return;
          }

          // Verify token and get user data
          const userData = await apiService.get<User>('/auth/me');
          setUser(userData);
        } catch (error) {
          console.error('Token validation failed:', error);
          logout();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!isAuthenticated || localStorage.getItem('auth_token') === 'demo-token') return;

    const refreshInterval = setInterval(() => {
      refreshToken().catch(error => {
        console.error('Token refresh failed:', error);
        logout();
      });
    }, 14 * 60 * 1000); // Refresh every 14 minutes

    return () => clearInterval(refreshInterval);
  }, [isAuthenticated]);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // Check for demo credentials for development/testing
      if (email === 'demo@financeai.com' && password === 'demo123') {
        // Demo login for development
        const demoUser: User = {
          id: 'demo-user-id',
          email: 'demo@financeai.com',
          firstName: 'Demo',
          lastName: 'User',
          createdAt: new Date().toISOString(),
        };
        
        apiService.setToken('demo-token');
        setUser(demoUser);
        setIsLoading(false);
        return;
      }

      const response = await apiService.post<AuthResponse>('/auth/login', {
        email,
        password,
      });

      apiService.setToken(response.token);
      
      if (response.refreshToken) {
        localStorage.setItem('refresh_token', response.refreshToken);
      }
      
      setUser(response.user);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (userData: RegisterData) => {
    setIsLoading(true);
    try {
      const response = await apiService.post<AuthResponse>('/auth/register', userData);

      apiService.setToken(response.token);
      
      if (response.refreshToken) {
        localStorage.setItem('refresh_token', response.refreshToken);
      }
      
      setUser(response.user);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    apiService.clearToken();
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  const refreshToken = useCallback(async () => {
    const refreshTokenValue = localStorage.getItem('refresh_token');
    if (!refreshTokenValue) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await apiService.post<AuthResponse>('/auth/refresh', {
        refreshToken: refreshTokenValue,
      });

      apiService.setToken(response.token);
      
      if (response.refreshToken) {
        localStorage.setItem('refresh_token', response.refreshToken);
      }
      
      if (response.user) {
        setUser(response.user);
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  }, [logout]);

  const updateProfile = useCallback(async (userData: Partial<User>) => {
    try {
      const updatedUser = await apiService.put<User>('/auth/profile', userData);
      setUser(updatedUser);
    } catch (error) {
      console.error('Profile update failed:', error);
      throw error;
    }
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;