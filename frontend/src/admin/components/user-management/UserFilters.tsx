"use client";

import React, { useState, useEffect } from 'react';
import { X, Calendar, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { UserFilters as UserFilterType, UserRole, UserStatus, AccountType, SubscriptionPlan } from '../../types';

interface UserFiltersProps {
  onFiltersChange: (filters: UserFilterType) => void;
  onClose: () => void;
}

/**
 * UserFilters Component
 * 
 * Features:
 * - Multiple filter types
 * - Date range filtering
 * - Quick filter presets
 * - Filter clearing
 */
export const UserFilters: React.FC<UserFiltersProps> = ({ onFiltersChange, onClose }) => {
  const [filters, setFilters] = useState<UserFilterType>({});
  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  // Filter options
  const roleOptions: UserRole[] = ['admin', 'moderator', 'support', 'user', 'premium', 'enterprise'];
  const statusOptions: UserStatus[] = ['active', 'inactive', 'suspended', 'pending', 'banned'];
  const accountTypeOptions: AccountType[] = ['free', 'premium', 'enterprise', 'trial'];
  const planTypeOptions: SubscriptionPlan[] = ['free', 'basic', 'premium', 'enterprise'];

  // Quick filter presets
  const quickFilters = [
    {
      label: 'Active Users',
      filters: { status: ['active'] },
    },
    {
      label: 'Premium Users',
      filters: { accountType: ['premium', 'enterprise'] },
    },
    {
      label: 'New This Week',
      filters: { 
        createdAfter: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      },
    },
    {
      label: 'Inactive Users',
      filters: { status: ['inactive', 'suspended'] },
    },
    {
      label: 'Admin Users',
      filters: { role: ['admin', 'moderator'] },
    },
  ];

  useEffect(() => {
    updateActiveFilters();
  }, [filters]);

  const updateActiveFilters = () => {
    const active: string[] = [];
    Object.entries(filters).forEach(([key, value]) => {
      if (value && (Array.isArray(value) ? value.length > 0 : true)) {
        active.push(key);
      }
    });
    setActiveFilters(active);
  };

  const handleFilterChange = (key: keyof UserFilterType, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleArrayFilterChange = (key: keyof UserFilterType, value: string, checked: boolean) => {
    const currentArray = filters[key] as string[] || [];
    let newArray: string[];
    
    if (checked) {
      newArray = [...currentArray, value];
    } else {
      newArray = currentArray.filter(item => item !== value);
    }
    
    handleFilterChange(key, newArray.length > 0 ? newArray : undefined);
  };

  const applyQuickFilter = (quickFilter: typeof quickFilters[0]) => {
    const newFilters = { ...filters, ...quickFilter.filters };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilter = (key: keyof UserFilterType) => {
    const newFilters = { ...filters };
    delete newFilters[key];
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearAllFilters = () => {
    setFilters({});
    onFiltersChange({});
  };

  const getFilterDisplayValue = (key: string, value: any) => {
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (key.includes('Date')) {
      return new Date(value).toLocaleDateString();
    }
    return String(value);
  };

  return (
    <div id="user-filters-panel" className="space-y-6">
      {/* Header */}
      <div id="filters-header" className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Filters</h3>
          {activeFilters.length > 0 && (
            <Badge variant="secondary">
              {activeFilters.length} active
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activeFilters.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearAllFilters}>
              Clear All
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Quick Filters */}
      <div id="quick-filters" className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Quick Filters</h4>
        <div className="flex flex-wrap gap-2">
          {quickFilters.map((quickFilter) => (
            <Button
              key={quickFilter.label}
              variant="outline"
              size="sm"
              onClick={() => applyQuickFilter(quickFilter)}
              className="text-xs"
            >
              {quickFilter.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Active Filters */}
      {activeFilters.length > 0 && (
        <div id="active-filters" className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Active Filters</h4>
          <div className="flex flex-wrap gap-2">
            {activeFilters.map((filterKey) => (
              <Badge key={filterKey} variant="secondary" className="flex items-center gap-1">
                <span className="capitalize">{filterKey}:</span>
                <span>{getFilterDisplayValue(filterKey, filters[filterKey as keyof UserFilterType])}</span>
                <button
                  onClick={() => clearFilter(filterKey as keyof UserFilterType)}
                  className="ml-1 hover:text-red-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Filter Controls */}
      <div id="filter-controls" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Role Filter */}
        <div id="role-filter" className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Role</label>
          <div className="space-y-1">
            {roleOptions.map((role) => (
              <label key={role} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={(filters.role || []).includes(role)}
                  onChange={(e) => handleArrayFilterChange('role', role, e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="capitalize">{role}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Status Filter */}
        <div id="status-filter" className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Status</label>
          <div className="space-y-1">
            {statusOptions.map((status) => (
              <label key={status} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={(filters.status || []).includes(status)}
                  onChange={(e) => handleArrayFilterChange('status', status, e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="capitalize">{status}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Account Type Filter */}
        <div id="account-type-filter" className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Account Type</label>
          <div className="space-y-1">
            {accountTypeOptions.map((accountType) => (
              <label key={accountType} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={(filters.accountType || []).includes(accountType)}
                  onChange={(e) => handleArrayFilterChange('accountType', accountType, e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="capitalize">{accountType}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Plan Type Filter */}
        <div id="plan-type-filter" className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Plan Type</label>
          <div className="space-y-1">
            {planTypeOptions.map((planType) => (
              <label key={planType} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={(filters.planType || []).includes(planType)}
                  onChange={(e) => handleArrayFilterChange('planType', planType, e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="capitalize">{planType}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Created Date Range */}
        <div id="created-date-filter" className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Created Date Range</label>
          <div className="space-y-2">
            <Input
              type="date"
              placeholder="From"
              value={filters.createdAfter || ''}
              onChange={(e) => handleFilterChange('createdAfter', e.target.value || undefined)}
            />
            <Input
              type="date"
              placeholder="To"
              value={filters.createdBefore || ''}
              onChange={(e) => handleFilterChange('createdBefore', e.target.value || undefined)}
            />
          </div>
        </div>

        {/* Last Login Date Range */}
        <div id="last-login-filter" className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Last Login Range</label>
          <div className="space-y-2">
            <Input
              type="date"
              placeholder="From"
              value={filters.lastLoginAfter || ''}
              onChange={(e) => handleFilterChange('lastLoginAfter', e.target.value || undefined)}
            />
            <Input
              type="date"
              placeholder="To"
              value={filters.lastLoginBefore || ''}
              onChange={(e) => handleFilterChange('lastLoginBefore', e.target.value || undefined)}
            />
          </div>
        </div>

        {/* Has Subscription */}
        <div id="subscription-filter" className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Subscription Status</label>
          <Select
            value={filters.hasSubscription?.toString() || ''}
            onValueChange={(value) => 
              handleFilterChange('hasSubscription', value === '' ? undefined : value === 'true')
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Any" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Any</SelectItem>
              <SelectItem value="true">Has Subscription</SelectItem>
              <SelectItem value="false">No Subscription</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Actions */}
      <div id="filter-actions" className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {activeFilters.length === 0 ? 'No filters applied' : `${activeFilters.length} filter${activeFilters.length === 1 ? '' : 's'} applied`}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={clearAllFilters} disabled={activeFilters.length === 0}>
            Clear All
          </Button>
          <Button size="sm" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
};