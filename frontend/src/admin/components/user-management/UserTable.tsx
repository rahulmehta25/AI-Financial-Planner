"use client";

import React, { useState } from 'react';
import { 
  ChevronUp, 
  ChevronDown, 
  MoreHorizontal, 
  Eye, 
  Edit, 
  Trash2, 
  Shield, 
  Activity,
  Mail,
  Calendar
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import { Checkbox } from '@/components/ui/checkbox';
import type { AdminUser, SortOption } from '../../types';

interface UserTableProps {
  users: AdminUser[];
  loading: boolean;
  onUserSelect: (user: AdminUser) => void;
  onSelectedUsersChange: (userIds: string[]) => void;
  selectedUsers: string[];
  sortBy: SortOption;
  onSortChange: (sort: SortOption) => void;
  permissions: {
    canEdit: boolean;
    canDelete: boolean;
    canViewDetails: boolean;
  };
}

interface Column {
  key: keyof AdminUser | 'actions' | 'select';
  label: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

/**
 * UserTable Component
 * 
 * Features:
 * - Sortable columns
 * - Row selection
 * - Action menus
 * - Responsive design
 * - Status badges
 */
export const UserTable: React.FC<UserTableProps> = ({
  users,
  loading,
  onUserSelect,
  onSelectedUsersChange,
  selectedUsers,
  sortBy,
  onSortChange,
  permissions,
}) => {
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const columns: Column[] = [
    { key: 'select', label: '', width: '50px', align: 'center' },
    { key: 'firstName', label: 'User', sortable: true, width: '250px' },
    { key: 'email', label: 'Email', sortable: true, width: '200px' },
    { key: 'role', label: 'Role', sortable: true, width: '120px' },
    { key: 'status', label: 'Status', sortable: true, width: '120px' },
    { key: 'accountType', label: 'Plan', sortable: true, width: '120px' },
    { key: 'createdAt', label: 'Created', sortable: true, width: '140px' },
    { key: 'lastLoginAt', label: 'Last Login', sortable: true, width: '140px' },
    { key: 'actions', label: 'Actions', width: '80px', align: 'center' },
  ];

  const handleSort = (column: keyof AdminUser) => {
    if (sortBy.field === column) {
      onSortChange({
        field: column,
        direction: sortBy.direction === 'asc' ? 'desc' : 'asc',
      });
    } else {
      onSortChange({
        field: column,
        direction: 'asc',
      });
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectedUsersChange(users.map(user => user.id));
    } else {
      onSelectedUsersChange([]);
    }
  };

  const handleSelectUser = (userId: string, checked: boolean) => {
    if (checked) {
      onSelectedUsersChange([...selectedUsers, userId]);
    } else {
      onSelectedUsersChange(selectedUsers.filter(id => id !== userId));
    }
  };

  const isAllSelected = users.length > 0 && selectedUsers.length === users.length;
  const isPartiallySelected = selectedUsers.length > 0 && selectedUsers.length < users.length;

  const getRoleBadgeColor = (role: string) => {
    const colors = {
      admin: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      moderator: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      support: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      premium: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      enterprise: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
      user: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
    };
    return colors[role as keyof typeof colors] || colors.user;
  };

  const getStatusBadgeColor = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
      suspended: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      banned: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return colors[status as keyof typeof colors] || colors.inactive;
  };

  const getAccountTypeBadgeColor = (accountType: string) => {
    const colors = {
      free: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
      premium: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      enterprise: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
      trial: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    };
    return colors[accountType as keyof typeof colors] || colors.free;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatRelativeTime = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
    if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`;
    return `${Math.floor(diffInDays / 365)} years ago`;
  };

  const getUserInitials = (firstName: string, lastName: string) => {
    return `${firstName[0] || ''}${lastName[0] || ''}`.toUpperCase();
  };

  if (loading) {
    return (
      <div id="user-table-loading" className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600 dark:text-gray-400">Loading users...</span>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div id="user-table-empty" className="text-center py-12">
        <div className="text-gray-400 dark:text-gray-500 mb-2">
          <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">No users found</h3>
        <p className="text-gray-600 dark:text-gray-400">Try adjusting your search or filter criteria.</p>
      </div>
    );
  }

  return (
    <div id="user-table-container" className="overflow-x-auto">
      <table className="w-full table-auto">
        <thead>
          <tr id="table-header" className="border-b border-gray-200 dark:border-gray-700">
            {columns.map((column) => (
              <th
                key={column.key}
                className={`py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : ''}`}
                style={{ width: column.width }}
              >
                {column.key === 'select' ? (
                  <Checkbox
                    checked={isAllSelected}
                    indeterminate={isPartiallySelected}
                    onCheckedChange={handleSelectAll}
                    aria-label="Select all users"
                  />
                ) : column.sortable ? (
                  <button
                    onClick={() => handleSort(column.key as keyof AdminUser)}
                    className="flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    {column.label}
                    {sortBy.field === column.key && (
                      sortBy.direction === 'asc' ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )
                    )}
                  </button>
                ) : (
                  column.label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr
              key={user.id}
              id={`user-row-${user.id}`}
              className={`border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${selectedUsers.includes(user.id) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}
              onMouseEnter={() => setHoveredRow(user.id)}
              onMouseLeave={() => setHoveredRow(null)}
            >
              {/* Select */}
              <td className="py-4 px-4 text-center">
                <Checkbox
                  checked={selectedUsers.includes(user.id)}
                  onCheckedChange={(checked) => handleSelectUser(user.id, checked as boolean)}
                  aria-label={`Select user ${user.firstName} ${user.lastName}`}
                />
              </td>

              {/* User Info */}
              <td className="py-4 px-4">
                <div className="flex items-center gap-3">
                  <Avatar className="h-8 w-8">
                    <div className="flex items-center justify-center h-full w-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 text-sm font-medium">
                      {getUserInitials(user.firstName, user.lastName)}
                    </div>
                  </Avatar>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {user.firstName} {user.lastName}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>ID: {user.id}</span>
                      {user.emailVerified && (
                        <Badge variant="secondary" className="text-xs">
                          <Mail className="h-3 w-3 mr-1" />
                          Verified
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </td>

              {/* Email */}
              <td className="py-4 px-4">
                <div className="text-sm text-gray-900 dark:text-white">{user.email}</div>
                {user.lastLoginAt && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    <Activity className="h-3 w-3 inline mr-1" />
                    {formatRelativeTime(user.lastLoginAt)}
                  </div>
                )}
              </td>

              {/* Role */}
              <td className="py-4 px-4">
                <Badge className={getRoleBadgeColor(user.role)}>
                  <Shield className="h-3 w-3 mr-1" />
                  {user.role}
                </Badge>
              </td>

              {/* Status */}
              <td className="py-4 px-4">
                <Badge className={getStatusBadgeColor(user.status)}>
                  {user.status}
                </Badge>
              </td>

              {/* Account Type */}
              <td className="py-4 px-4">
                <Badge className={getAccountTypeBadgeColor(user.accountType)}>
                  {user.accountType}
                </Badge>
              </td>

              {/* Created Date */}
              <td className="py-4 px-4">
                <div className="text-sm text-gray-900 dark:text-white">
                  <Calendar className="h-3 w-3 inline mr-1" />
                  {formatDate(user.createdAt)}
                </div>
              </td>

              {/* Last Login */}
              <td className="py-4 px-4">
                <div className="text-sm text-gray-900 dark:text-white">
                  {formatDate(user.lastLoginAt)}
                </div>
              </td>

              {/* Actions */}
              <td className="py-4 px-4 text-center">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      aria-label={`Actions for ${user.firstName} ${user.lastName}`}
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    {permissions.canViewDetails && (
                      <DropdownMenuItem onClick={() => onUserSelect(user)}>
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                    )}
                    {permissions.canEdit && (
                      <DropdownMenuItem onClick={() => onUserSelect(user)}>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit User
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem>
                      <Mail className="h-4 w-4 mr-2" />
                      Send Email
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Activity className="h-4 w-4 mr-2" />
                      View Activity
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {user.status === 'active' ? (
                      <DropdownMenuItem className="text-orange-600 dark:text-orange-400">
                        Suspend User
                      </DropdownMenuItem>
                    ) : (
                      <DropdownMenuItem className="text-green-600 dark:text-green-400">
                        Activate User
                      </DropdownMenuItem>
                    )}
                    {permissions.canDelete && (
                      <DropdownMenuItem className="text-red-600 dark:text-red-400">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete User
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};