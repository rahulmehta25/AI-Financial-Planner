import { API_CONFIG, getApiUrl } from '@/config/api'

interface ApiResponse<T = any> {
  data?: T
  message?: string
  detail?: string
  error?: string
}

interface ApiError {
  status: number
  message: string
  details?: any
}

class ApiService {
  private token: string | null = null
  private refreshPromise: Promise<boolean> | null = null
  private retryQueue: Array<() => Promise<any>> = []
  private backendAvailable: boolean = true
  private lastBackendCheck: number = 0
  private backendCheckInterval: number = 30000 // 30 seconds

  constructor() {
    this.token = localStorage.getItem('auth_token')
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('auth_token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('auth_token')
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    
    return headers
  }

  private async refreshToken(): Promise<boolean> {
    if (this.refreshPromise) {
      return this.refreshPromise
    }

    this.refreshPromise = this._refreshToken()
    
    try {
      const result = await this.refreshPromise
      return result
    } finally {
      this.refreshPromise = null
    }
  }

  private async _refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        return false
      }

      const response = await fetch(getApiUrl(API_CONFIG.endpoints.auth.refresh), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) {
        this.clearToken()
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('current_user')
        return false
      }

      const authData = await response.json()
      
      // Update tokens
      this.setToken(authData.access_token)
      localStorage.setItem('refresh_token', authData.refresh_token)
      
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      this.clearToken()
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      return false
    }
  }

  private createApiError(response: Response, data?: any): ApiError {
    const message = data?.detail || data?.message || data?.error || `${response.status} ${response.statusText}`
    
    return {
      status: response.status,
      message,
      details: data
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.ok) {
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }
      return response.text() as unknown as T
    }

    let errorData: any
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: response.statusText }
    }

    const apiError = this.createApiError(response, errorData)
    throw apiError
  }

  async request<T>(endpoint: string, options: RequestInit = {}, retryCount = 0): Promise<T> {
    const url = getApiUrl(endpoint)
    const maxRetries = API_CONFIG.retryAttempts || 3
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.getHeaders(),
          ...options.headers,
        },
        signal: AbortSignal.timeout(API_CONFIG.timeout || 10000),
      })

      return await this.handleResponse<T>(response)
      
    } catch (error: any) {
      // Mark backend as unavailable on network errors
      if (error.name === 'NetworkError' || error.message?.includes('fetch') || error.code === 'ECONNREFUSED') {
        this.setBackendAvailable(false)
      }

      // Handle 401 unauthorized - try to refresh token
      if (error.status === 401 && retryCount === 0) {
        const refreshSuccessful = await this.refreshToken()
        if (refreshSuccessful) {
          return this.request<T>(endpoint, options, retryCount + 1)
        } else {
          // Don't redirect to login in mock mode
          if (!this.backendAvailable) {
            throw error
          }
          // Redirect to login if refresh fails
          window.location.href = '/login'
          throw error
        }
      }

      // Handle network errors with retry
      if (retryCount < maxRetries && this.shouldRetry(error)) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 5000) // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay))
        return this.request<T>(endpoint, options, retryCount + 1)
      }

      console.error('API Request failed:', error)
      throw error
    }
  }

  private shouldRetry(error: any): boolean {
    // Retry on network errors, timeouts, and 5xx server errors
    return (
      error.name === 'NetworkError' ||
      error.name === 'TimeoutError' ||
      error.message?.includes('fetch') ||
      (error.status >= 500 && error.status < 600)
    )
  }

  private async checkBackendAvailability(): Promise<boolean> {
    const now = Date.now()
    if (now - this.lastBackendCheck < this.backendCheckInterval) {
      return this.backendAvailable
    }

    try {
      const response = await fetch(getApiUrl('/health'), {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout
      })
      
      this.backendAvailable = response.ok
      this.lastBackendCheck = now
      
      if (!this.backendAvailable) {
        console.warn('Backend is not available, switching to mock data mode')
      }
      
      return this.backendAvailable
    } catch (error) {
      console.warn('Backend availability check failed, using mock data:', error)
      this.backendAvailable = false
      this.lastBackendCheck = now
      return false
    }
  }

  public async isBackendAvailable(): Promise<boolean> {
    return await this.checkBackendAvailability()
  }

  public setBackendAvailable(available: boolean): void {
    this.backendAvailable = available
    this.lastBackendCheck = Date.now()
  }

  // Queue requests during token refresh
  private async executeWithRetry<T>(apiCall: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      const execute = async () => {
        try {
          const result = await apiCall()
          resolve(result)
        } catch (error) {
          reject(error)
        }
      }

      if (this.refreshPromise) {
        this.retryQueue.push(execute)
      } else {
        execute()
      }
    })
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

export const apiService = new ApiService()
export default apiService