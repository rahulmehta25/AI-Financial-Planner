export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface ValidationError {
  field: string;
  message: string;
}

export interface FormState<T = any> {
  data: T;
  errors: ValidationError[];
  isValid: boolean;
  isDirty: boolean;
  isSubmitting: boolean;
}

export interface NetworkState {
  isConnected: boolean;
  connectionType: ConnectionType;
  isInternetReachable: boolean;
}

export type ConnectionType = 
  | 'none'
  | 'wifi'
  | 'cellular'
  | 'ethernet'
  | 'unknown';

export interface AppState {
  appState: 'active' | 'background' | 'inactive';
  lastActiveTime: number;
  sessionStartTime: number;
}

export interface Document {
  id: string;
  name: string;
  type: DocumentType;
  uri: string;
  mimeType: string;
  size: number;
  uploadedAt: string;
  extractedData?: any;
}

export type DocumentType = 
  | 'bank_statement'
  | 'pay_stub'
  | 'tax_document'
  | 'investment_statement'
  | 'insurance_policy'
  | 'receipt'
  | 'other';

export interface NotificationPayload {
  title: string;
  body: string;
  data?: Record<string, any>;
  sound?: string;
  badge?: number;
  category?: string;
}

export interface HapticFeedbackType {
  type: 'impact' | 'notification' | 'selection';
  intensity?: 'light' | 'medium' | 'heavy';
}

export interface BiometricConfig {
  title: string;
  subtitle?: string;
  description?: string;
  fallbackTitle?: string;
  negativeText?: string;
}

export interface CameraConfig {
  quality: number;
  allowsEditing: boolean;
  aspect: [number, number];
  base64: boolean;
}

export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  fonts: {
    regular: string;
    medium: string;
    bold: string;
    light: string;
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
}