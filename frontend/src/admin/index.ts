// Admin Module Exports

// Main Components
export { AdminDashboard } from './components/AdminDashboard';

// Layout Components
export { AdminLayout } from './components/layout';

// Feature Components
export { UserManagementDashboard } from './components/user-management';
export { SystemMonitoringDashboard } from './components/system-monitoring';

// Store
export { useAdminStore, useAdminAuth, useAdminUI } from './store/adminStore';

// Types
export type * from './types';