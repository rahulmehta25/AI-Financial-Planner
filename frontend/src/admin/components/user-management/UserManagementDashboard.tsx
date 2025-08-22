"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Search, Filter, Download, RefreshCw, Plus, MoreHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { useUserManagement, useAdminAuth } from '../../store/adminStore';
import { UserTable } from './UserTable';
import { UserFilters } from './UserFilters';
import { UserDetailsModal } from './UserDetailsModal';
import { CreateUserModal } from './CreateUserModal';
import { BulkActionsModal } from './BulkActionsModal';
import type { AdminUser, UserFilters as UserFilterType } from '../../types';

/**
 * Main User Management Dashboard Component
 * 
 * Features:
 * - User search and filtering
 * - Bulk actions
 * - User details management
 * - Activity monitoring
 * - Export capabilities
 */
export const UserManagementDashboard: React.FC = () => {
  const {
    users,
    selectedUser,
    filters,
    sortBy,
    searchQuery,
    isLoading,
    lastRefresh,
    setUsers,
    setSelectedUser,
    updateUser,
    deleteUser,
    setFilters,
    setSortBy,
    setSearchQuery,
    setLoading,
    refreshUsers,
  } = useUserManagement();

  const { hasPermission } = useAdminAuth();

  // Local state
  const [showFilters, setShowFilters] = useState(false);
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);

  // Permissions
  const canCreateUsers = hasPermission('users', 'create');
  const canEditUsers = hasPermission('users', 'update');
  const canDeleteUsers = hasPermission('users', 'delete');
  const canViewUserDetails = hasPermission('users', 'read');
  const canExportUsers = hasPermission('users', 'export');

  // Load users on component mount
  useEffect(() => {
    loadUsers();
  }, [filters, sortBy, searchQuery, currentPage]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      // This would be replaced with actual API call
      const mockUsers = generateMockUsers();
      setUsers(mockUsers);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  // Statistics derived from users data
  const userStats = useMemo(() => {
    if (!users?.data) return null;

    const totalUsers = users.data.length;
    const activeUsers = users.data.filter(u => u.status === 'active').length;
    const premiumUsers = users.data.filter(u => u.accountType === 'premium' || u.accountType === 'enterprise').length;
    const newThisMonth = users.data.filter(u => {
      const createdDate = new Date(u.createdAt);
      const now = new Date();
      return createdDate.getMonth() === now.getMonth() && createdDate.getFullYear() === now.getFullYear();
    }).length;

    return {
      total: totalUsers,
      active: activeUsers,
      premium: premiumUsers,
      newThisMonth,
      activePercentage: totalUsers > 0 ? Math.round((activeUsers / totalUsers) * 100) : 0,
      premiumPercentage: totalUsers > 0 ? Math.round((premiumUsers / totalUsers) * 100) : 0,
    };
  }, [users]);

  const handleUserSelect = (user: AdminUser) => {
    setSelectedUser(user);
    setShowUserDetails(true);
  };

  const handleBulkAction = (action: string) => {
    setShowBulkActions(true);
  };

  const handleExport = async () => {
    if (!canExportUsers) return;
    
    try {
      // This would be replaced with actual export logic
      console.log('Exporting users...', { filters, searchQuery });
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleFilterChange = (newFilters: UserFilterType) => {
    setFilters(Object.entries(newFilters).map(([field, value]) => ({
      field,
      operator: Array.isArray(value) ? 'in' : 'equals',
      value
    })));
    setCurrentPage(1);
  };

  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  return (
    <div id="admin-user-management-dashboard" className="space-y-6">
      {/* Header */}
      <div id="user-management-header" className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div id="header-content">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">User Management</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Manage user accounts, permissions, and activity
            {lastRefresh && (
              <span className="ml-2">
                Last updated: {new Date(lastRefresh).toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div id="header-actions" className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            Filters
          </Button>
          {canExportUsers && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={refreshUsers}
            disabled={isLoading}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {canCreateUsers && (
            <Button
              size="sm"
              onClick={() => setShowCreateUser(true)}
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add User
            </Button>
          )}
        </div>
      </div>

      {/* Statistics Cards */}
      {userStats && (
        <div id="user-stats-grid" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card id="total-users-card" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Users</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{userStats.total.toLocaleString()}</p>
              </div>
              <div className="text-blue-600 dark:text-blue-400">
                <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card id="active-users-card" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Users</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{userStats.active.toLocaleString()}</p>
                <p className="text-xs text-green-600 dark:text-green-400">{userStats.activePercentage}% of total</p>
              </div>
              <div className="text-green-600 dark:text-green-400">
                <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </Card>

          <Card id="premium-users-card" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Premium Users</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{userStats.premium.toLocaleString()}</p>
                <p className="text-xs text-purple-600 dark:text-purple-400">{userStats.premiumPercentage}% of total</p>
              </div>
              <div className="text-purple-600 dark:text-purple-400">
                <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
            </div>
          </Card>

          <Card id="new-users-card" className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">New This Month</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{userStats.newThisMonth.toLocaleString()}</p>
              </div>
              <div className="text-orange-600 dark:text-orange-400">
                <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Search and Bulk Actions */}
      <div id="search-and-actions" className="flex flex-col sm:flex-row gap-4">
        <div id="search-container" className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search users by name, email, or ID..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        {selectedUsers.length > 0 && (
          <div id="bulk-actions" className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {selectedUsers.length} selected
            </span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                  Actions
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => handleBulkAction('activate')}>
                  Activate Users
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleBulkAction('deactivate')}>
                  Deactivate Users
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleBulkAction('export')}>
                  Export Selected
                </DropdownMenuItem>
                {canDeleteUsers && (
                  <DropdownMenuItem 
                    onClick={() => handleBulkAction('delete')}
                    className="text-red-600 dark:text-red-400"
                  >
                    Delete Users
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <Card id="filters-panel" className="p-4">
          <UserFilters
            onFiltersChange={handleFilterChange}
            onClose={() => setShowFilters(false)}
          />
        </Card>
      )}

      {/* Users Table */}
      <Card id="users-table-card" className="p-6">
        <UserTable
          users={users?.data || []}
          loading={isLoading}
          onUserSelect={handleUserSelect}
          onSelectedUsersChange={setSelectedUsers}
          selectedUsers={selectedUsers}
          sortBy={sortBy}
          onSortChange={setSortBy}
          permissions={{
            canEdit: canEditUsers,
            canDelete: canDeleteUsers,
            canViewDetails: canViewUserDetails,
          }}
        />

        {/* Pagination */}
        {users && users.pagination.totalPages > 1 && (
          <div id="pagination" className="flex items-center justify-between mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Showing {((users.pagination.page - 1) * users.pagination.limit) + 1} to{' '}
              {Math.min(users.pagination.page * users.pagination.limit, users.pagination.total)} of{' '}
              {users.pagination.total} results
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={!users.pagination.hasPrev}
              >
                Previous
              </Button>
              <span className="text-sm">
                Page {users.pagination.page} of {users.pagination.totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(Math.min(users.pagination.totalPages, currentPage + 1))}
                disabled={!users.pagination.hasNext}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Modals */}
      {showUserDetails && selectedUser && (
        <UserDetailsModal
          user={selectedUser}
          isOpen={showUserDetails}
          onClose={() => {
            setShowUserDetails(false);
            setSelectedUser(null);
          }}
          onUserUpdate={updateUser}
          permissions={{
            canEdit: canEditUsers,
            canDelete: canDeleteUsers,
          }}
        />
      )}

      {showCreateUser && (
        <CreateUserModal
          isOpen={showCreateUser}
          onClose={() => setShowCreateUser(false)}
          onUserCreated={(user) => {
            // Refresh users list
            refreshUsers();
            setShowCreateUser(false);
          }}
        />
      )}

      {showBulkActions && (
        <BulkActionsModal
          isOpen={showBulkActions}
          onClose={() => setShowBulkActions(false)}
          selectedUserIds={selectedUsers}
          onActionComplete={() => {
            setSelectedUsers([]);
            setShowBulkActions(false);
            refreshUsers();
          }}
        />
      )}
    </div>
  );
};

// Mock data generator for development
function generateMockUsers() {
  const roles = ['user', 'premium', 'admin', 'moderator'] as const;
  const statuses = ['active', 'inactive', 'suspended', 'pending'] as const;
  const accountTypes = ['free', 'premium', 'enterprise', 'trial'] as const;

  const users: AdminUser[] = Array.from({ length: 50 }, (_, i) => ({
    id: `user-${i + 1}`,
    email: `user${i + 1}@example.com`,
    firstName: `User`,
    lastName: `${i + 1}`,
    role: roles[Math.floor(Math.random() * roles.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    accountType: accountTypes[Math.floor(Math.random() * accountTypes.length)],
    createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
    lastLoginAt: Math.random() > 0.3 ? new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString() : null,
    emailVerified: Math.random() > 0.2,
    isActive: Math.random() > 0.3,
    permissions: [],
  }));

  return {
    data: users,
    pagination: {
      page: 1,
      limit: 20,
      total: users.length,
      totalPages: Math.ceil(users.length / 20),
      hasNext: false,
      hasPrev: false,
    },
  };
}