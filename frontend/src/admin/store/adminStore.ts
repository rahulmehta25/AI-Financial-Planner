"use client";

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type {
  AdminUser,
  UserRole,
  Permission,
  SystemMetrics,
  ServiceHealth,
  ContentItem,
  Template,
  FAQ,
  AnalyticsData,
  SupportTicket,
  FeatureFlag,
  SystemConfiguration,
  ApiKey,
  Integration,
  ImpersonationSession,
  PaginatedResponse,
  FilterOption,
  SortOption,
  NotificationToast,
} from '../types';

// ========================================
// Admin Authentication State
// ========================================

interface AdminAuthState {
  currentAdmin: AdminUser | null;
  permissions: Permission[];
  isAuthenticated: boolean;
  isLoading: boolean;
  sessionExpiry: string | null;
}

interface AdminAuthActions {
  setCurrentAdmin: (admin: AdminUser | null) => void;
  setPermissions: (permissions: Permission[]) => void;
  updateAdminProfile: (updates: Partial<AdminUser>) => void;
  clearAuth: () => void;
  hasPermission: (resource: string, action: string) => boolean;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
}

// ========================================
// User Management State
// ========================================

interface UserManagementState {
  users: PaginatedResponse<AdminUser> | null;
  selectedUser: AdminUser | null;
  userActivities: Record<string, any[]>;
  filters: FilterOption[];
  sortBy: SortOption;
  searchQuery: string;
  isLoading: boolean;
  lastRefresh: string | null;
}

interface UserManagementActions {
  setUsers: (users: PaginatedResponse<AdminUser>) => void;
  setSelectedUser: (user: AdminUser | null) => void;
  updateUser: (userId: string, updates: Partial<AdminUser>) => void;
  deleteUser: (userId: string) => void;
  setUserActivities: (userId: string, activities: any[]) => void;
  setFilters: (filters: FilterOption[]) => void;
  setSortBy: (sort: SortOption) => void;
  setSearchQuery: (query: string) => void;
  setLoading: (loading: boolean) => void;
  refreshUsers: () => Promise<void>;
}

// ========================================
// System Monitoring State
// ========================================

interface SystemMonitoringState {
  metrics: SystemMetrics | null;
  serviceHealth: ServiceHealth[];
  alerts: any[];
  isRealTimeEnabled: boolean;
  lastUpdate: string | null;
  metricsHistory: Record<string, any[]>;
}

interface SystemMonitoringActions {
  setMetrics: (metrics: SystemMetrics) => void;
  setServiceHealth: (services: ServiceHealth[]) => void;
  addAlert: (alert: any) => void;
  removeAlert: (alertId: string) => void;
  toggleRealTime: () => void;
  updateMetricsHistory: (metric: string, data: any[]) => void;
  clearAlerts: () => void;
}

// ========================================
// Content Management State
// ========================================

interface ContentManagementState {
  articles: PaginatedResponse<ContentItem> | null;
  templates: Template[];
  faqs: FAQ[];
  selectedContent: ContentItem | null;
  contentFilters: FilterOption[];
  isLoading: boolean;
}

interface ContentManagementActions {
  setArticles: (articles: PaginatedResponse<ContentItem>) => void;
  setTemplates: (templates: Template[]) => void;
  setFaqs: (faqs: FAQ[]) => void;
  setSelectedContent: (content: ContentItem | null) => void;
  updateContent: (contentId: string, updates: Partial<ContentItem>) => void;
  deleteContent: (contentId: string) => void;
  setContentFilters: (filters: FilterOption[]) => void;
  setContentLoading: (loading: boolean) => void;
}

// ========================================
// Analytics State
// ========================================

interface AnalyticsState {
  analyticsData: AnalyticsData | null;
  selectedPeriod: string;
  customDateRange: { start: string; end: string } | null;
  dashboardWidgets: string[];
  isLoading: boolean;
}

interface AnalyticsActions {
  setAnalyticsData: (data: AnalyticsData) => void;
  setSelectedPeriod: (period: string) => void;
  setCustomDateRange: (range: { start: string; end: string } | null) => void;
  setDashboardWidgets: (widgets: string[]) => void;
  setAnalyticsLoading: (loading: boolean) => void;
}

// ========================================
// Support Tools State
// ========================================

interface SupportToolsState {
  tickets: PaginatedResponse<SupportTicket> | null;
  selectedTicket: SupportTicket | null;
  featureFlags: FeatureFlag[];
  impersonationSessions: ImpersonationSession[];
  activeImpersonation: ImpersonationSession | null;
  ticketFilters: FilterOption[];
  isLoading: boolean;
}

interface SupportToolsActions {
  setTickets: (tickets: PaginatedResponse<SupportTicket>) => void;
  setSelectedTicket: (ticket: SupportTicket | null) => void;
  updateTicket: (ticketId: string, updates: Partial<SupportTicket>) => void;
  setFeatureFlags: (flags: FeatureFlag[]) => void;
  updateFeatureFlag: (flagId: string, updates: Partial<FeatureFlag>) => void;
  setImpersonationSessions: (sessions: ImpersonationSession[]) => void;
  startImpersonation: (session: ImpersonationSession) => void;
  endImpersonation: () => void;
  setTicketFilters: (filters: FilterOption[]) => void;
  setSupportLoading: (loading: boolean) => void;
}

// ========================================
// Configuration State
// ========================================

interface ConfigurationState {
  systemConfig: SystemConfiguration[];
  apiKeys: ApiKey[];
  integrations: Integration[];
  selectedConfig: SystemConfiguration | null;
  configFilters: FilterOption[];
  isLoading: boolean;
}

interface ConfigurationActions {
  setSystemConfig: (config: SystemConfiguration[]) => void;
  setApiKeys: (keys: ApiKey[]) => void;
  setIntegrations: (integrations: Integration[]) => void;
  setSelectedConfig: (config: SystemConfiguration | null) => void;
  updateConfig: (configId: string, updates: Partial<SystemConfiguration>) => void;
  updateApiKey: (keyId: string, updates: Partial<ApiKey>) => void;
  updateIntegration: (integrationId: string, updates: Partial<Integration>) => void;
  setConfigFilters: (filters: FilterOption[]) => void;
  setConfigLoading: (loading: boolean) => void;
}

// ========================================
// UI State
// ========================================

interface UIState {
  sidebarCollapsed: boolean;
  activeModule: string;
  notifications: NotificationToast[];
  modals: Record<string, boolean>;
  loading: Record<string, boolean>;
  theme: 'light' | 'dark' | 'system';
}

interface UIActions {
  setSidebarCollapsed: (collapsed: boolean) => void;
  setActiveModule: (module: string) => void;
  addNotification: (notification: Omit<NotificationToast, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
  setLoading: (key: string, loading: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

// ========================================
// Combined Store Type
// ========================================

type AdminStore = AdminAuthState &
  AdminAuthActions &
  UserManagementState &
  UserManagementActions &
  SystemMonitoringState &
  SystemMonitoringActions &
  ContentManagementState &
  ContentManagementActions &
  AnalyticsState &
  AnalyticsActions &
  SupportToolsState &
  SupportToolsActions &
  ConfigurationState &
  ConfigurationActions &
  UIState &
  UIActions;

// ========================================
// Store Implementation
// ========================================

export const useAdminStore = create<AdminStore>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        // ========================================
        // Admin Auth State
        // ========================================
        currentAdmin: null,
        permissions: [],
        isAuthenticated: false,
        isLoading: false,
        sessionExpiry: null,

        // Auth Actions
        setCurrentAdmin: (admin) =>
          set((state) => {
            state.currentAdmin = admin;
            state.isAuthenticated = !!admin;
          }),

        setPermissions: (permissions) =>
          set((state) => {
            state.permissions = permissions;
          }),

        updateAdminProfile: (updates) =>
          set((state) => {
            if (state.currentAdmin) {
              Object.assign(state.currentAdmin, updates);
            }
          }),

        clearAuth: () =>
          set((state) => {
            state.currentAdmin = null;
            state.permissions = [];
            state.isAuthenticated = false;
            state.sessionExpiry = null;
          }),

        hasPermission: (resource, action) => {
          const { permissions } = get();
          return permissions.some(
            (permission) =>
              permission.resource === resource && permission.action === action
          );
        },

        hasRole: (roles) => {
          const { currentAdmin } = get();
          if (!currentAdmin) return false;
          const targetRoles = Array.isArray(roles) ? roles : [roles];
          return targetRoles.includes(currentAdmin.role);
        },

        // ========================================
        // User Management State
        // ========================================
        users: null,
        selectedUser: null,
        userActivities: {},
        filters: [],
        sortBy: { field: 'createdAt', direction: 'desc' },
        searchQuery: '',
        lastRefresh: null,

        // User Management Actions
        setUsers: (users) =>
          set((state) => {
            state.users = users;
            state.lastRefresh = new Date().toISOString();
          }),

        setSelectedUser: (user) =>
          set((state) => {
            state.selectedUser = user;
          }),

        updateUser: (userId, updates) =>
          set((state) => {
            if (state.users) {
              const userIndex = state.users.data.findIndex((u) => u.id === userId);
              if (userIndex !== -1) {
                Object.assign(state.users.data[userIndex], updates);
              }
            }
            if (state.selectedUser?.id === userId) {
              Object.assign(state.selectedUser, updates);
            }
          }),

        deleteUser: (userId) =>
          set((state) => {
            if (state.users) {
              state.users.data = state.users.data.filter((u) => u.id !== userId);
            }
            if (state.selectedUser?.id === userId) {
              state.selectedUser = null;
            }
          }),

        setUserActivities: (userId, activities) =>
          set((state) => {
            state.userActivities[userId] = activities;
          }),

        setFilters: (filters) =>
          set((state) => {
            state.filters = filters;
          }),

        setSortBy: (sort) =>
          set((state) => {
            state.sortBy = sort;
          }),

        setSearchQuery: (query) =>
          set((state) => {
            state.searchQuery = query;
          }),

        setLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),

        refreshUsers: async () => {
          // This would be implemented to call the API
          console.log('Refreshing users...');
        },

        // ========================================
        // System Monitoring State
        // ========================================
        metrics: null,
        serviceHealth: [],
        alerts: [],
        isRealTimeEnabled: false,
        lastUpdate: null,
        metricsHistory: {},

        // System Monitoring Actions
        setMetrics: (metrics) =>
          set((state) => {
            state.metrics = metrics;
            state.lastUpdate = new Date().toISOString();
          }),

        setServiceHealth: (services) =>
          set((state) => {
            state.serviceHealth = services;
          }),

        addAlert: (alert) =>
          set((state) => {
            state.alerts.push({ ...alert, id: Date.now().toString() });
          }),

        removeAlert: (alertId) =>
          set((state) => {
            state.alerts = state.alerts.filter((alert) => alert.id !== alertId);
          }),

        toggleRealTime: () =>
          set((state) => {
            state.isRealTimeEnabled = !state.isRealTimeEnabled;
          }),

        updateMetricsHistory: (metric, data) =>
          set((state) => {
            state.metricsHistory[metric] = data;
          }),

        clearAlerts: () =>
          set((state) => {
            state.alerts = [];
          }),

        // ========================================
        // Content Management State
        // ========================================
        articles: null,
        templates: [],
        faqs: [],
        selectedContent: null,
        contentFilters: [],

        // Content Management Actions
        setArticles: (articles) =>
          set((state) => {
            state.articles = articles;
          }),

        setTemplates: (templates) =>
          set((state) => {
            state.templates = templates;
          }),

        setFaqs: (faqs) =>
          set((state) => {
            state.faqs = faqs;
          }),

        setSelectedContent: (content) =>
          set((state) => {
            state.selectedContent = content;
          }),

        updateContent: (contentId, updates) =>
          set((state) => {
            if (state.articles) {
              const contentIndex = state.articles.data.findIndex((c) => c.id === contentId);
              if (contentIndex !== -1) {
                Object.assign(state.articles.data[contentIndex], updates);
              }
            }
            if (state.selectedContent?.id === contentId) {
              Object.assign(state.selectedContent, updates);
            }
          }),

        deleteContent: (contentId) =>
          set((state) => {
            if (state.articles) {
              state.articles.data = state.articles.data.filter((c) => c.id !== contentId);
            }
            if (state.selectedContent?.id === contentId) {
              state.selectedContent = null;
            }
          }),

        setContentFilters: (filters) =>
          set((state) => {
            state.contentFilters = filters;
          }),

        setContentLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),

        // ========================================
        // Analytics State
        // ========================================
        analyticsData: null,
        selectedPeriod: '30d',
        customDateRange: null,
        dashboardWidgets: [
          'userAcquisition',
          'userEngagement',
          'featureUsage',
          'conversionFunnels',
          'revenueMetrics',
        ],

        // Analytics Actions
        setAnalyticsData: (data) =>
          set((state) => {
            state.analyticsData = data;
          }),

        setSelectedPeriod: (period) =>
          set((state) => {
            state.selectedPeriod = period;
          }),

        setCustomDateRange: (range) =>
          set((state) => {
            state.customDateRange = range;
          }),

        setDashboardWidgets: (widgets) =>
          set((state) => {
            state.dashboardWidgets = widgets;
          }),

        setAnalyticsLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),

        // ========================================
        // Support Tools State
        // ========================================
        tickets: null,
        selectedTicket: null,
        featureFlags: [],
        impersonationSessions: [],
        activeImpersonation: null,
        ticketFilters: [],

        // Support Tools Actions
        setTickets: (tickets) =>
          set((state) => {
            state.tickets = tickets;
          }),

        setSelectedTicket: (ticket) =>
          set((state) => {
            state.selectedTicket = ticket;
          }),

        updateTicket: (ticketId, updates) =>
          set((state) => {
            if (state.tickets) {
              const ticketIndex = state.tickets.data.findIndex((t) => t.id === ticketId);
              if (ticketIndex !== -1) {
                Object.assign(state.tickets.data[ticketIndex], updates);
              }
            }
            if (state.selectedTicket?.id === ticketId) {
              Object.assign(state.selectedTicket, updates);
            }
          }),

        setFeatureFlags: (flags) =>
          set((state) => {
            state.featureFlags = flags;
          }),

        updateFeatureFlag: (flagId, updates) =>
          set((state) => {
            const flagIndex = state.featureFlags.findIndex((f) => f.id === flagId);
            if (flagIndex !== -1) {
              Object.assign(state.featureFlags[flagIndex], updates);
            }
          }),

        setImpersonationSessions: (sessions) =>
          set((state) => {
            state.impersonationSessions = sessions;
          }),

        startImpersonation: (session) =>
          set((state) => {
            state.activeImpersonation = session;
          }),

        endImpersonation: () =>
          set((state) => {
            state.activeImpersonation = null;
          }),

        setTicketFilters: (filters) =>
          set((state) => {
            state.ticketFilters = filters;
          }),

        setSupportLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),

        // ========================================
        // Configuration State
        // ========================================
        systemConfig: [],
        apiKeys: [],
        integrations: [],
        selectedConfig: null,
        configFilters: [],

        // Configuration Actions
        setSystemConfig: (config) =>
          set((state) => {
            state.systemConfig = config;
          }),

        setApiKeys: (keys) =>
          set((state) => {
            state.apiKeys = keys;
          }),

        setIntegrations: (integrations) =>
          set((state) => {
            state.integrations = integrations;
          }),

        setSelectedConfig: (config) =>
          set((state) => {
            state.selectedConfig = config;
          }),

        updateConfig: (configId, updates) =>
          set((state) => {
            const configIndex = state.systemConfig.findIndex((c) => c.id === configId);
            if (configIndex !== -1) {
              Object.assign(state.systemConfig[configIndex], updates);
            }
            if (state.selectedConfig?.id === configId) {
              Object.assign(state.selectedConfig, updates);
            }
          }),

        updateApiKey: (keyId, updates) =>
          set((state) => {
            const keyIndex = state.apiKeys.findIndex((k) => k.id === keyId);
            if (keyIndex !== -1) {
              Object.assign(state.apiKeys[keyIndex], updates);
            }
          }),

        updateIntegration: (integrationId, updates) =>
          set((state) => {
            const integrationIndex = state.integrations.findIndex((i) => i.id === integrationId);
            if (integrationIndex !== -1) {
              Object.assign(state.integrations[integrationIndex], updates);
            }
          }),

        setConfigFilters: (filters) =>
          set((state) => {
            state.configFilters = filters;
          }),

        setConfigLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),

        // ========================================
        // UI State
        // ========================================
        sidebarCollapsed: false,
        activeModule: 'dashboard',
        notifications: [],
        modals: {},
        loading: {},
        theme: 'system',

        // UI Actions
        setSidebarCollapsed: (collapsed) =>
          set((state) => {
            state.sidebarCollapsed = collapsed;
          }),

        setActiveModule: (module) =>
          set((state) => {
            state.activeModule = module;
          }),

        addNotification: (notification) =>
          set((state) => {
            const id = Date.now().toString();
            state.notifications.push({ ...notification, id });
          }),

        removeNotification: (id) =>
          set((state) => {
            state.notifications = state.notifications.filter((n) => n.id !== id);
          }),

        clearNotifications: () =>
          set((state) => {
            state.notifications = [];
          }),

        openModal: (modalId) =>
          set((state) => {
            state.modals[modalId] = true;
          }),

        closeModal: (modalId) =>
          set((state) => {
            state.modals[modalId] = false;
          }),

        setLoading: (key, loading) =>
          set((state) => {
            state.loading[key] = loading;
          }),

        setTheme: (theme) =>
          set((state) => {
            state.theme = theme;
          }),
      }))
    ),
    {
      name: 'admin-store',
      partialize: (state) => ({
        // Only persist certain parts of the state
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        dashboardWidgets: state.dashboardWidgets,
        selectedPeriod: state.selectedPeriod,
      }),
    }
  )
);

// ========================================
// Store Hooks
// ========================================

// Auth hooks
export const useAdminAuth = () =>
  useAdminStore((state) => ({
    currentAdmin: state.currentAdmin,
    permissions: state.permissions,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    setCurrentAdmin: state.setCurrentAdmin,
    setPermissions: state.setPermissions,
    updateAdminProfile: state.updateAdminProfile,
    clearAuth: state.clearAuth,
    hasPermission: state.hasPermission,
    hasRole: state.hasRole,
  }));

// User management hooks
export const useUserManagement = () =>
  useAdminStore((state) => ({
    users: state.users,
    selectedUser: state.selectedUser,
    userActivities: state.userActivities,
    filters: state.filters,
    sortBy: state.sortBy,
    searchQuery: state.searchQuery,
    isLoading: state.isLoading,
    lastRefresh: state.lastRefresh,
    setUsers: state.setUsers,
    setSelectedUser: state.setSelectedUser,
    updateUser: state.updateUser,
    deleteUser: state.deleteUser,
    setUserActivities: state.setUserActivities,
    setFilters: state.setFilters,
    setSortBy: state.setSortBy,
    setSearchQuery: state.setSearchQuery,
    setLoading: state.setLoading,
    refreshUsers: state.refreshUsers,
  }));

// System monitoring hooks
export const useSystemMonitoring = () =>
  useAdminStore((state) => ({
    metrics: state.metrics,
    serviceHealth: state.serviceHealth,
    alerts: state.alerts,
    isRealTimeEnabled: state.isRealTimeEnabled,
    lastUpdate: state.lastUpdate,
    metricsHistory: state.metricsHistory,
    setMetrics: state.setMetrics,
    setServiceHealth: state.setServiceHealth,
    addAlert: state.addAlert,
    removeAlert: state.removeAlert,
    toggleRealTime: state.toggleRealTime,
    updateMetricsHistory: state.updateMetricsHistory,
    clearAlerts: state.clearAlerts,
  }));

// Content management hooks
export const useContentManagement = () =>
  useAdminStore((state) => ({
    articles: state.articles,
    templates: state.templates,
    faqs: state.faqs,
    selectedContent: state.selectedContent,
    contentFilters: state.contentFilters,
    isLoading: state.isLoading,
    setArticles: state.setArticles,
    setTemplates: state.setTemplates,
    setFaqs: state.setFaqs,
    setSelectedContent: state.setSelectedContent,
    updateContent: state.updateContent,
    deleteContent: state.deleteContent,
    setContentFilters: state.setContentFilters,
    setContentLoading: state.setContentLoading,
  }));

// Analytics hooks
export const useAdminAnalytics = () =>
  useAdminStore((state) => ({
    analyticsData: state.analyticsData,
    selectedPeriod: state.selectedPeriod,
    customDateRange: state.customDateRange,
    dashboardWidgets: state.dashboardWidgets,
    isLoading: state.isLoading,
    setAnalyticsData: state.setAnalyticsData,
    setSelectedPeriod: state.setSelectedPeriod,
    setCustomDateRange: state.setCustomDateRange,
    setDashboardWidgets: state.setDashboardWidgets,
    setAnalyticsLoading: state.setAnalyticsLoading,
  }));

// Support tools hooks
export const useSupportTools = () =>
  useAdminStore((state) => ({
    tickets: state.tickets,
    selectedTicket: state.selectedTicket,
    featureFlags: state.featureFlags,
    impersonationSessions: state.impersonationSessions,
    activeImpersonation: state.activeImpersonation,
    ticketFilters: state.ticketFilters,
    isLoading: state.isLoading,
    setTickets: state.setTickets,
    setSelectedTicket: state.setSelectedTicket,
    updateTicket: state.updateTicket,
    setFeatureFlags: state.setFeatureFlags,
    updateFeatureFlag: state.updateFeatureFlag,
    setImpersonationSessions: state.setImpersonationSessions,
    startImpersonation: state.startImpersonation,
    endImpersonation: state.endImpersonation,
    setTicketFilters: state.setTicketFilters,
    setSupportLoading: state.setSupportLoading,
  }));

// Configuration hooks
export const useConfiguration = () =>
  useAdminStore((state) => ({
    systemConfig: state.systemConfig,
    apiKeys: state.apiKeys,
    integrations: state.integrations,
    selectedConfig: state.selectedConfig,
    configFilters: state.configFilters,
    isLoading: state.isLoading,
    setSystemConfig: state.setSystemConfig,
    setApiKeys: state.setApiKeys,
    setIntegrations: state.setIntegrations,
    setSelectedConfig: state.setSelectedConfig,
    updateConfig: state.updateConfig,
    updateApiKey: state.updateApiKey,
    updateIntegration: state.updateIntegration,
    setConfigFilters: state.setConfigFilters,
    setConfigLoading: state.setConfigLoading,
  }));

// UI hooks
export const useAdminUI = () =>
  useAdminStore((state) => ({
    sidebarCollapsed: state.sidebarCollapsed,
    activeModule: state.activeModule,
    notifications: state.notifications,
    modals: state.modals,
    loading: state.loading,
    theme: state.theme,
    setSidebarCollapsed: state.setSidebarCollapsed,
    setActiveModule: state.setActiveModule,
    addNotification: state.addNotification,
    removeNotification: state.removeNotification,
    clearNotifications: state.clearNotifications,
    openModal: state.openModal,
    closeModal: state.closeModal,
    setLoading: state.setLoading,
    setTheme: state.setTheme,
  }));