"use client";

import React from 'react';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbNavigationProps {
  activeModule: string;
}

/**
 * BreadcrumbNavigation Component
 * 
 * Features:
 * - Dynamic breadcrumb generation
 * - Module hierarchy display
 * - Navigation links
 */
export const BreadcrumbNavigation: React.FC<BreadcrumbNavigationProps> = ({
  activeModule,
}) => {
  const getBreadcrumbs = (module: string) => {
    const breadcrumbs = [
      { label: 'Admin', href: '/admin', icon: <Home className="h-4 w-4" /> },
    ];

    const moduleMap: Record<string, { label: string; parent?: string }> = {
      'dashboard': { label: 'Dashboard' },
      'users': { label: 'User Management' },
      'users-list': { label: 'All Users', parent: 'users' },
      'users-roles': { label: 'Roles & Permissions', parent: 'users' },
      'monitoring': { label: 'System Monitoring' },
      'monitoring-overview': { label: 'System Overview', parent: 'monitoring' },
      'monitoring-services': { label: 'Service Health', parent: 'monitoring' },
      'monitoring-performance': { label: 'Performance', parent: 'monitoring' },
      'content': { label: 'Content Management' },
      'content-articles': { label: 'Articles', parent: 'content' },
      'content-templates': { label: 'Templates', parent: 'content' },
      'content-faqs': { label: 'FAQs', parent: 'content' },
      'analytics': { label: 'Analytics' },
      'analytics-overview': { label: 'Overview', parent: 'analytics' },
      'analytics-users': { label: 'User Analytics', parent: 'analytics' },
      'analytics-revenue': { label: 'Revenue', parent: 'analytics' },
      'support': { label: 'Support Tools' },
      'support-tickets': { label: 'Tickets', parent: 'support' },
      'support-flags': { label: 'Feature Flags', parent: 'support' },
      'support-impersonation': { label: 'User Impersonation', parent: 'support' },
      'settings': { label: 'Configuration' },
      'settings-system': { label: 'System Settings', parent: 'settings' },
      'settings-api': { label: 'API Keys', parent: 'settings' },
      'settings-integrations': { label: 'Integrations', parent: 'settings' },
    };

    const current = moduleMap[module];
    if (current) {
      // Add parent if exists
      if (current.parent && moduleMap[current.parent]) {
        breadcrumbs.push({
          label: moduleMap[current.parent].label,
          href: `/admin/${current.parent}`,
        });
      }
      
      // Add current module
      breadcrumbs.push({
        label: current.label,
        href: `/admin/${module}`,
      });
    }

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs(activeModule);

  return (
    <nav id="breadcrumb-navigation" className="flex items-center space-x-1 text-sm">
      {breadcrumbs.map((breadcrumb, index) => (
        <div key={breadcrumb.href} className="flex items-center">
          {index > 0 && (
            <ChevronRight className="h-4 w-4 text-gray-400 mx-2" />
          )}
          <div className="flex items-center gap-1">
            {breadcrumb.icon}
            <span
              className={
                index === breadcrumbs.length - 1
                  ? 'font-medium text-gray-900 dark:text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white cursor-pointer'
              }
            >
              {breadcrumb.label}
            </span>
          </div>
        </div>
      ))}
    </nav>
  );
};