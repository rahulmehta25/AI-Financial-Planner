// Admin Dashboard Type Definitions

// ========================================
// User Management Types
// ========================================

export interface AdminUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  status: UserStatus;
  accountType: AccountType;
  createdAt: string;
  lastLoginAt: string | null;
  emailVerified: boolean;
  isActive: boolean;
  permissions: Permission[];
  profile?: UserProfile;
  subscription?: UserSubscription;
  metrics?: UserMetrics;
}

export interface UserProfile {
  id: string;
  userId: string;
  phone?: string;
  address?: Address;
  dateOfBirth?: string;
  profilePicture?: string;
  preferences: UserPreferences;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  notifications: NotificationSettings;
  privacy: PrivacySettings;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  sms: boolean;
  marketingEmails: boolean;
  systemAlerts: boolean;
}

export interface PrivacySettings {
  profileVisibility: 'public' | 'private' | 'friends';
  dataSharing: boolean;
  analyticsTracking: boolean;
}

export interface UserSubscription {
  id: string;
  userId: string;
  plan: SubscriptionPlan;
  status: 'active' | 'inactive' | 'cancelled' | 'expired';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  trialEnd?: string;
}

export interface UserMetrics {
  totalLogins: number;
  lastActivityAt: string;
  sessionsThisMonth: number;
  featuresUsed: string[];
  completedOnboarding: boolean;
  planCompletionRate: number;
  engagementScore: number;
}

export type UserRole = 'admin' | 'moderator' | 'support' | 'user' | 'premium' | 'enterprise';
export type UserStatus = 'active' | 'inactive' | 'suspended' | 'pending' | 'banned';
export type AccountType = 'free' | 'premium' | 'enterprise' | 'trial';
export type SubscriptionPlan = 'free' | 'basic' | 'premium' | 'enterprise';

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  conditions?: Record<string, any>;
}

export interface UserFilters {
  search?: string;
  role?: UserRole[];
  status?: UserStatus[];
  accountType?: AccountType[];
  createdAfter?: string;
  createdBefore?: string;
  lastLoginAfter?: string;
  lastLoginBefore?: string;
  hasSubscription?: boolean;
  planType?: SubscriptionPlan[];
}

export interface UserActivity {
  id: string;
  userId: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
  sessionId: string;
}

// ========================================
// System Monitoring Types
// ========================================

export interface SystemMetrics {
  server: ServerMetrics;
  database: DatabaseMetrics;
  cache: CacheMetrics;
  api: ApiMetrics;
  application: ApplicationMetrics;
  timestamp: string;
}

export interface ServerMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkIn: number;
  networkOut: number;
  uptime: number;
  loadAverage: number[];
}

export interface DatabaseMetrics {
  connectionCount: number;
  queryTime: number;
  slowQueries: number;
  lockWaits: number;
  deadlocks: number;
  cacheHitRatio: number;
  tableSize: number;
  indexUsage: number;
}

export interface CacheMetrics {
  hitRate: number;
  missRate: number;
  memoryUsage: number;
  evictions: number;
  operations: number;
  avgResponseTime: number;
}

export interface ApiMetrics {
  requestsPerSecond: number;
  averageResponseTime: number;
  errorRate: number;
  status2xx: number;
  status4xx: number;
  status5xx: number;
  activeConnections: number;
  endpointStats: EndpointStats[];
}

export interface EndpointStats {
  endpoint: string;
  method: string;
  requests: number;
  avgResponseTime: number;
  errorRate: number;
  status: Record<string, number>;
}

export interface ApplicationMetrics {
  activeUsers: number;
  sessionsCount: number;
  featuresUsage: Record<string, number>;
  errorCount: number;
  warningCount: number;
  performanceScore: number;
}

export interface ServiceHealth {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  lastCheck: string;
  responseTime: number;
  uptime: number;
  version: string;
  dependencies: ServiceDependency[];
  checks: HealthCheck[];
}

export interface ServiceDependency {
  name: string;
  status: 'healthy' | 'unhealthy';
  responseTime: number;
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message: string;
  timestamp: string;
}

// ========================================
// Content Management Types
// ========================================

export interface ContentItem {
  id: string;
  type: ContentType;
  title: string;
  content: string;
  status: ContentStatus;
  authorId: string;
  author: AdminUser;
  categories: string[];
  tags: string[];
  metadata: ContentMetadata;
  createdAt: string;
  updatedAt: string;
  publishedAt?: string;
  expiresAt?: string;
  version: number;
  parentId?: string;
}

export interface ContentMetadata {
  description?: string;
  keywords?: string[];
  slug?: string;
  seoTitle?: string;
  seoDescription?: string;
  featuredImage?: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  estimatedReadTime?: number;
  language: string;
  targetAudience?: string[];
}

export type ContentType = 'article' | 'faq' | 'template' | 'guide' | 'tutorial' | 'policy' | 'announcement';
export type ContentStatus = 'draft' | 'review' | 'published' | 'archived' | 'deleted';

export interface Template {
  id: string;
  name: string;
  type: TemplateType;
  content: string;
  variables: TemplateVariable[];
  category: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  usageCount: number;
}

export type TemplateType = 'email' | 'report' | 'document' | 'notification' | 'pdf';

export interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'array' | 'object';
  required: boolean;
  defaultValue?: any;
  description: string;
}

export interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
  order: number;
  isPublished: boolean;
  viewCount: number;
  helpfulCount: number;
  notHelpfulCount: number;
  createdAt: string;
  updatedAt: string;
}

// ========================================
// Analytics Types
// ========================================

export interface AnalyticsData {
  userAcquisition: UserAcquisitionMetrics;
  userEngagement: UserEngagementMetrics;
  featureUsage: FeatureUsageMetrics;
  conversionFunnels: ConversionFunnel[];
  revenueMetrics: RevenueMetrics;
  retentionMetrics: RetentionMetrics;
  period: AnalyticsPeriod;
}

export interface UserAcquisitionMetrics {
  totalUsers: number;
  newUsers: number;
  growth: number;
  acquisitionChannels: AcquisitionChannel[];
  geographicDistribution: GeographicData[];
  deviceBreakdown: DeviceData[];
}

export interface AcquisitionChannel {
  source: string;
  users: number;
  conversions: number;
  cost: number;
  roi: number;
}

export interface GeographicData {
  country: string;
  users: number;
  percentage: number;
}

export interface DeviceData {
  device: string;
  users: number;
  percentage: number;
}

export interface UserEngagementMetrics {
  dailyActiveUsers: number;
  weeklyActiveUsers: number;
  monthlyActiveUsers: number;
  averageSessionDuration: number;
  bounceRate: number;
  pagesPerSession: number;
  sessionsByTime: TimeSeriesData[];
}

export interface FeatureUsageMetrics {
  features: FeatureUsage[];
  adoptionRates: FeatureAdoption[];
  usageByUserType: UsageByType[];
}

export interface FeatureUsage {
  feature: string;
  usage: number;
  uniqueUsers: number;
  avgUsagePerUser: number;
  trend: number;
}

export interface FeatureAdoption {
  feature: string;
  adoptionRate: number;
  timeToAdopt: number;
  dropoffRate: number;
}

export interface UsageByType {
  userType: string;
  features: Record<string, number>;
}

export interface ConversionFunnel {
  name: string;
  steps: FunnelStep[];
  conversionRate: number;
  dropoffPoints: DropoffPoint[];
}

export interface FunnelStep {
  name: string;
  users: number;
  conversionRate: number;
  avgTimeToNext: number;
}

export interface DropoffPoint {
  step: string;
  dropoffRate: number;
  reasons: string[];
}

export interface RevenueMetrics {
  totalRevenue: number;
  recurringRevenue: number;
  oneTimeRevenue: number;
  averageRevenuePerUser: number;
  customerLifetimeValue: number;
  churnRate: number;
  revenueGrowth: number;
  revenueByPlan: RevenuePlan[];
}

export interface RevenuePlan {
  plan: string;
  revenue: number;
  users: number;
  avgRevenuePerUser: number;
}

export interface RetentionMetrics {
  dayRetention: number[];
  weekRetention: number[];
  monthRetention: number[];
  cohortAnalysis: CohortData[];
}

export interface CohortData {
  cohort: string;
  size: number;
  retention: number[];
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
}

export type AnalyticsPeriod = '1d' | '7d' | '30d' | '90d' | '1y' | 'custom';

// ========================================
// Support Tools Types
// ========================================

export interface SupportTicket {
  id: string;
  ticketNumber: string;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: TicketCategory;
  userId: string;
  user: AdminUser;
  assignedToId?: string;
  assignedTo?: AdminUser;
  messages: TicketMessage[];
  tags: string[];
  metadata: TicketMetadata;
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
  closedAt?: string;
}

export interface TicketMessage {
  id: string;
  ticketId: string;
  authorId: string;
  author: AdminUser;
  content: string;
  type: 'user' | 'agent' | 'system';
  attachments: TicketAttachment[];
  isInternal: boolean;
  createdAt: string;
}

export interface TicketAttachment {
  id: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  url: string;
  uploadedAt: string;
}

export interface TicketMetadata {
  source: 'email' | 'chat' | 'phone' | 'form' | 'api';
  userAgent?: string;
  ipAddress?: string;
  referer?: string;
  sessionId?: string;
  customFields: Record<string, any>;
}

export type TicketStatus = 'open' | 'pending' | 'resolved' | 'closed' | 'escalated';
export type TicketPriority = 'low' | 'normal' | 'high' | 'urgent' | 'critical';
export type TicketCategory = 'technical' | 'billing' | 'feature' | 'bug' | 'account' | 'general';

export interface ImpersonationSession {
  id: string;
  adminId: string;
  admin: AdminUser;
  targetUserId: string;
  targetUser: AdminUser;
  reason: string;
  startedAt: string;
  endedAt?: string;
  duration?: number;
  actions: ImpersonationAction[];
  ipAddress: string;
  userAgent: string;
}

export interface ImpersonationAction {
  id: string;
  sessionId: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface FeatureFlag {
  id: string;
  name: string;
  key: string;
  description: string;
  type: 'boolean' | 'string' | 'number' | 'json';
  defaultValue: any;
  isActive: boolean;
  rules: FeatureFlagRule[];
  rolloutPercentage: number;
  environments: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface FeatureFlagRule {
  id: string;
  conditions: FeatureFlagCondition[];
  value: any;
  rolloutPercentage: number;
  description?: string;
}

export interface FeatureFlagCondition {
  attribute: string;
  operator: 'equals' | 'not_equals' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'contains';
  value: any;
}

// ========================================
// Configuration Types
// ========================================

export interface SystemConfiguration {
  id: string;
  category: ConfigCategory;
  key: string;
  value: any;
  type: 'string' | 'number' | 'boolean' | 'json' | 'encrypted';
  description: string;
  isRequired: boolean;
  isPublic: boolean;
  validationRules?: ValidationRule[];
  updatedAt: string;
  updatedBy: string;
}

export type ConfigCategory = 'general' | 'security' | 'email' | 'payment' | 'api' | 'features' | 'ui';

export interface ValidationRule {
  type: 'regex' | 'range' | 'enum' | 'custom';
  value: any;
  message: string;
}

export interface ApiKey {
  id: string;
  name: string;
  service: string;
  keyPrefix: string;
  maskedKey: string;
  isActive: boolean;
  environment: 'development' | 'staging' | 'production';
  permissions: string[];
  rateLimit?: RateLimit;
  expiresAt?: string;
  lastUsedAt?: string;
  createdAt: string;
  createdBy: string;
}

export interface RateLimit {
  requests: number;
  period: string;
  burst?: number;
}

export interface Integration {
  id: string;
  name: string;
  type: IntegrationType;
  status: 'active' | 'inactive' | 'error' | 'pending';
  configuration: Record<string, any>;
  credentials: Record<string, string>;
  webhook?: WebhookConfig;
  lastSync?: string;
  syncStatus?: SyncStatus;
  healthCheck?: HealthCheck;
  createdAt: string;
  updatedAt: string;
}

export type IntegrationType = 'plaid' | 'yodlee' | 'stripe' | 'mailgun' | 'twilio' | 'slack' | 'analytics';

export interface WebhookConfig {
  url: string;
  secret: string;
  events: string[];
  headers?: Record<string, string>;
  retryPolicy: RetryPolicy;
}

export interface RetryPolicy {
  maxRetries: number;
  retryDelays: number[];
  backoffStrategy: 'linear' | 'exponential';
}

export interface SyncStatus {
  lastAttempt: string;
  status: 'success' | 'failed' | 'partial';
  recordsProcessed: number;
  errors: string[];
}

export interface DeploymentInfo {
  version: string;
  buildNumber: string;
  deployedAt: string;
  deployedBy: string;
  environment: string;
  gitCommit: string;
  gitBranch: string;
  status: 'active' | 'inactive' | 'maintenance';
}

// ========================================
// Common Types
// ========================================

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

export interface SortOption {
  field: string;
  direction: 'asc' | 'desc';
}

export interface FilterOption {
  field: string;
  operator: 'equals' | 'not_equals' | 'in' | 'not_in' | 'like' | 'greater_than' | 'less_than' | 'between';
  value: any;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface ChartData {
  label: string;
  value: number;
  color?: string;
  metadata?: Record<string, any>;
}

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, row: any) => React.ReactNode;
}

export interface ExportOptions {
  format: 'csv' | 'xlsx' | 'pdf' | 'json';
  columns?: string[];
  filters?: FilterOption[];
  dateRange?: DateRange;
}

export interface NotificationToast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// ========================================
// API Response Types
// ========================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  meta?: {
    requestId: string;
    timestamp: string;
    version: string;
  };
}

export interface AsyncOperation {
  id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
  startedAt: string;
  completedAt?: string;
  estimatedDuration?: number;
}