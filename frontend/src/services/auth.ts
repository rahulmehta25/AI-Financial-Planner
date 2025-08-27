import { API_CONFIG, getApiUrl } from '@/config/api'
import { apiService } from './api'

export interface LoginRequest {
  email: string
  password: string
}

export interface SignupRequest {
  email: string
  password: string
  firstName: string
  lastName: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    email: string
    firstName: string
    lastName: string
    isActive: boolean
    createdAt: string
  }
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  isActive: boolean
  createdAt: string
}

class AuthService {
  private refreshTokenTimeout: NodeJS.Timeout | null = null

  constructor() {
    // Initialize token refresh on service creation
    this.setupTokenRefresh()
  }

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    try {
      // Check if backend is available
      const backendAvailable = await apiService.isBackendAvailable()
      
      if (!backendAvailable) {
        return this.mockLogin(credentials)
      }

      const response = await fetch(getApiUrl(API_CONFIG.endpoints.auth.login), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Login failed: ${response.status}`)
      }

      const authData: AuthResponse = await response.json()
      
      // Store tokens
      this.setTokens(authData.access_token, authData.refresh_token)
      
      // Set token in API service
      apiService.setToken(authData.access_token)
      
      // Setup automatic refresh
      this.scheduleTokenRefresh(authData.expires_in)
      
      return authData
    } catch (error) {
      console.error('Login error, trying mock login:', error)
      // Fallback to mock login if backend fails
      return this.mockLogin(credentials)
    }
  }

  async signup(userData: SignupRequest): Promise<AuthResponse> {
    try {
      // Check if backend is available
      const backendAvailable = await apiService.isBackendAvailable()
      
      if (!backendAvailable) {
        return this.mockSignup(userData)
      }

      const response = await fetch(getApiUrl(API_CONFIG.endpoints.auth.register), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Signup failed: ${response.status}`)
      }

      const authData: AuthResponse = await response.json()
      
      // Store tokens
      this.setTokens(authData.access_token, authData.refresh_token)
      
      // Set token in API service
      apiService.setToken(authData.access_token)
      
      // Setup automatic refresh
      this.scheduleTokenRefresh(authData.expires_in)
      
      return authData
    } catch (error) {
      console.error('Signup error, trying mock signup:', error)
      // Fallback to mock signup if backend fails
      return this.mockSignup(userData)
    }
  }

  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      // Check if backend is available
      const backendAvailable = await apiService.isBackendAvailable()
      
      if (!backendAvailable) {
        // For mock mode, just return true to keep user logged in
        return this.isMockUser()
      }

      const response = await fetch(getApiUrl(API_CONFIG.endpoints.auth.refresh), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) {
        // If refresh fails, logout user
        this.logout()
        return false
      }

      const authData: AuthResponse = await response.json()
      
      // Update tokens
      this.setTokens(authData.access_token, authData.refresh_token)
      
      // Update token in API service
      apiService.setToken(authData.access_token)
      
      // Schedule next refresh
      this.scheduleTokenRefresh(authData.expires_in)
      
      return true
    } catch (error) {
      console.error('Token refresh error:', error)
      // In mock mode, keep user logged in
      if (this.isMockUser()) {
        return true
      }
      this.logout()
      return false
    }
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        // Attempt to logout on server
        await fetch(getApiUrl(API_CONFIG.endpoints.auth.logout), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        }).catch(() => {
          // Ignore logout errors - still clear local data
        })
      }
    } finally {
      // Clear all local data
      this.clearTokens()
      apiService.clearToken()
      this.clearTokenRefreshTimeout()
      
      // Notify other tabs
      window.localStorage.setItem('logout', Date.now().toString())
      window.localStorage.removeItem('logout')
      
      // Redirect to home
      window.location.href = '/'
    }
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem('auth_token')
    const refreshToken = localStorage.getItem('refresh_token')
    return !!(token && refreshToken)
  }

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('current_user')
    if (!userStr) return null
    
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('auth_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  private clearTokens(): void {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('current_user')
  }

  private scheduleTokenRefresh(expiresIn: number): void {
    this.clearTokenRefreshTimeout()
    
    // Refresh 2 minutes before expiry
    const refreshTime = Math.max((expiresIn - 120) * 1000, 60000) // minimum 1 minute
    
    this.refreshTokenTimeout = setTimeout(() => {
      this.refreshToken()
    }, refreshTime)
  }

  private clearTokenRefreshTimeout(): void {
    if (this.refreshTokenTimeout) {
      clearTimeout(this.refreshTokenTimeout)
      this.refreshTokenTimeout = null
    }
  }

  private setupTokenRefresh(): void {
    // Listen for storage events (logout from other tabs)
    window.addEventListener('storage', (e) => {
      if (e.key === 'logout') {
        // Clear local data without redirecting (other tab will handle redirect)
        this.clearTokens()
        apiService.clearToken()
        this.clearTokenRefreshTimeout()
      }
    })

    // Setup refresh if we have tokens
    if (this.isAuthenticated()) {
      // Try to refresh on startup to validate tokens
      this.refreshToken()
    }
  }

  // Mock authentication methods
  private async mockLogin(credentials: LoginRequest): Promise<AuthResponse> {
    console.log('Using mock login - backend unavailable')
    
    // Simulate login validation
    if (!credentials.email || !credentials.password) {
      throw new Error('Email and password are required')
    }

    // Mock successful authentication
    const mockUser = {
      id: 'mock-user-123',
      email: credentials.email,
      firstName: 'Demo',
      lastName: 'User',
      isActive: true,
      createdAt: new Date().toISOString()
    }

    const authData: AuthResponse = {
      access_token: 'mock-access-token-' + Date.now(),
      refresh_token: 'mock-refresh-token-' + Date.now(),
      token_type: 'Bearer',
      expires_in: 3600,
      user: mockUser
    }

    // Store tokens and user data
    this.setTokens(authData.access_token, authData.refresh_token)
    localStorage.setItem('current_user', JSON.stringify(mockUser))
    localStorage.setItem('mock_mode', 'true')
    
    // Set token in API service
    apiService.setToken(authData.access_token)
    apiService.setBackendAvailable(false)
    
    return authData
  }

  private async mockSignup(userData: SignupRequest): Promise<AuthResponse> {
    console.log('Using mock signup - backend unavailable')
    
    // Simulate signup validation
    if (!userData.email || !userData.password || !userData.firstName || !userData.lastName) {
      throw new Error('All fields are required')
    }

    // Mock successful registration
    const mockUser = {
      id: 'mock-user-' + Date.now(),
      email: userData.email,
      firstName: userData.firstName,
      lastName: userData.lastName,
      isActive: true,
      createdAt: new Date().toISOString()
    }

    const authData: AuthResponse = {
      access_token: 'mock-access-token-' + Date.now(),
      refresh_token: 'mock-refresh-token-' + Date.now(),
      token_type: 'Bearer',
      expires_in: 3600,
      user: mockUser
    }

    // Store tokens and user data
    this.setTokens(authData.access_token, authData.refresh_token)
    localStorage.setItem('current_user', JSON.stringify(mockUser))
    localStorage.setItem('mock_mode', 'true')
    
    // Set token in API service
    apiService.setToken(authData.access_token)
    apiService.setBackendAvailable(false)
    
    return authData
  }

  private isMockUser(): boolean {
    return localStorage.getItem('mock_mode') === 'true'
  }

  // Retry logic for API calls
  async retryWithRefresh<T>(apiCall: () => Promise<T>): Promise<T> {
    try {
      return await apiCall()
    } catch (error: any) {
      // If 401, try to refresh and retry once
      if (error.message?.includes('401') || error.status === 401) {
        const refreshSuccessful = await this.refreshToken()
        if (refreshSuccessful) {
          return await apiCall()
        }
      }
      throw error
    }
  }
}

export const authService = new AuthService()
export default authService