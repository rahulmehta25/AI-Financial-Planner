export interface ApiConfig {
  baseURL: string;
  timeout: number;
  headers: Record<string, string>;
}

export interface RequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  url: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
}

export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: any;
}

export interface RetryConfig {
  retries: number;
  retryDelay: number;
  retryCondition?: (error: any) => boolean;
}

export interface CacheConfig {
  key: string;
  ttl: number; // Time to live in seconds
  staleWhileRevalidate?: boolean;
}

export interface OfflineConfig {
  enabled: boolean;
  queueRequests: boolean;
  retryOnReconnect: boolean;
}

// API Endpoints
export interface AuthEndpoints {
  login: string;
  register: string;
  refresh: string;
  logout: string;
  forgotPassword: string;
  resetPassword: string;
  profile: string;
}

export interface FinancialEndpoints {
  profiles: string;
  goals: string;
  simulations: string;
  portfolios: string;
  accounts: string;
  transactions: string;
}

export interface UserEndpoints {
  profile: string;
  preferences: string;
  avatar: string;
  documents: string;
}

// Request/Response Types
export interface LoginApiRequest {
  email: string;
  password: string;
}

export interface LoginApiResponse {
  user: any;
  token: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RegisterApiRequest {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone?: string;
}

export interface CreateGoalApiRequest {
  name: string;
  description?: string;
  targetAmount: number;
  targetDate: string;
  priority: string;
  category: string;
}

export interface RunSimulationApiRequest {
  profileId: string;
  parameters: any;
}

export interface UploadDocumentApiRequest {
  file: FormData;
  type: string;
  metadata?: any;
}