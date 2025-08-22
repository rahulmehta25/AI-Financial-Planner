"use client";

import React from 'react';
import { 
  Home, 
  Users, 
  Activity, 
  FileText, 
  BarChart3, 
  Headphones, 
  Settings,
  Shield,
  Database,
  Zap,
  MessageSquare,
  Flag,
  Key,
  Palette
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import type { UserRole } from '../../types';

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  badge?: string;
  roles: UserRole[];
  subItems?: NavigationItem[];
}

interface AdminNavigationProps {
  collapsed: boolean;
  activeModule: string;
  onModuleChange: (module: string) => void;
  userRole: UserRole;
}

/**
 * AdminNavigation Component
 * 
 * Features:
 * - Role-based menu filtering
 * - Collapsible sidebar
 * - Sub-navigation support
 * - Tooltips for collapsed state
 * - Badge indicators
 */
export const AdminNavigation: React.FC<AdminNavigationProps> = ({
  collapsed,
  activeModule,
  onModuleChange,
  userRole,
}) => {
  const navigationItems: NavigationItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <Home className="h-5 w-5" />,
      roles: ['admin', 'moderator', 'support'],
    },
    {
      id: 'users',
      label: 'User Management',
      icon: <Users className="h-5 w-5" />,
      roles: ['admin', 'moderator'],
      subItems: [
        {
          id: 'users-list',
          label: 'All Users',
          icon: <Users className="h-4 w-4" />,
          roles: ['admin', 'moderator'],
        },
        {
          id: 'users-roles',
          label: 'Roles & Permissions',
          icon: <Shield className="h-4 w-4" />,
          roles: ['admin'],
        },
      ],
    },
    {
      id: 'monitoring',
      label: 'System Monitoring',
      icon: <Activity className="h-5 w-5" />,
      roles: ['admin', 'moderator'],
      subItems: [
        {
          id: 'monitoring-overview',
          label: 'System Overview',
          icon: <Activity className="h-4 w-4" />,
          roles: ['admin', 'moderator'],
        },
        {
          id: 'monitoring-services',
          label: 'Service Health',
          icon: <Database className="h-4 w-4" />,
          roles: ['admin'],
        },
        {
          id: 'monitoring-performance',
          label: 'Performance',
          icon: <Zap className="h-4 w-4" />,
          roles: ['admin'],
        },
      ],
    },
    {
      id: 'content',
      label: 'Content Management',
      icon: <FileText className="h-5 w-5" />,
      roles: ['admin', 'moderator'],
      subItems: [
        {
          id: 'content-articles',
          label: 'Articles',
          icon: <FileText className="h-4 w-4" />,
          roles: ['admin', 'moderator'],
        },
        {
          id: 'content-templates',
          label: 'Templates',
          icon: <Palette className="h-4 w-4" />,
          roles: ['admin', 'moderator'],
        },
        {
          id: 'content-faqs',
          label: 'FAQs',
          icon: <MessageSquare className="h-4 w-4" />,
          roles: ['admin', 'moderator'],
        },
      ],
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: <BarChart3 className="h-5 w-5" />,
      roles: ['admin', 'moderator'],
      subItems: [
        {
          id: 'analytics-overview',
          label: 'Overview',
          icon: <BarChart3 className="h-4 w-4" />,
          roles: ['admin', 'moderator'],
        },
        {
          id: 'analytics-users',
          label: 'User Analytics',
          icon: <Users className="h-4 w-4" />,
          roles: ['admin', 'moderator'],
        },
        {
          id: 'analytics-revenue',
          label: 'Revenue',
          icon: <BarChart3 className="h-4 w-4" />,
          roles: ['admin'],
        },
      ],
    },
    {
      id: 'support',
      label: 'Support Tools',
      icon: <Headphones className="h-5 w-5" />,
      badge: '3',
      roles: ['admin', 'moderator', 'support'],
      subItems: [
        {
          id: 'support-tickets',
          label: 'Tickets',
          icon: <Headphones className="h-4 w-4" />,
          badge: '3',
          roles: ['admin', 'moderator', 'support'],
        },
        {
          id: 'support-flags',
          label: 'Feature Flags',
          icon: <Flag className="h-4 w-4" />,
          roles: ['admin'],
        },
        {
          id: 'support-impersonation',
          label: 'User Impersonation',
          icon: <Users className="h-4 w-4" />,
          roles: ['admin', 'support'],
        },
      ],
    },
    {
      id: 'settings',
      label: 'Configuration',
      icon: <Settings className="h-5 w-5" />,
      roles: ['admin'],
      subItems: [
        {
          id: 'settings-system',
          label: 'System Settings',
          icon: <Settings className="h-4 w-4" />,
          roles: ['admin'],
        },
        {
          id: 'settings-api',
          label: 'API Keys',
          icon: <Key className="h-4 w-4" />,
          roles: ['admin'],
        },
        {
          id: 'settings-integrations',
          label: 'Integrations',
          icon: <Zap className="h-4 w-4" />,
          roles: ['admin'],
        },
      ],
    },
  ];

  // Filter navigation items based on user role
  const filteredItems = navigationItems.filter(item => 
    item.roles.includes(userRole)
  );

  const handleItemClick = (itemId: string) => {
    onModuleChange(itemId);
  };

  const isActive = (itemId: string) => {
    return activeModule === itemId || activeModule.startsWith(`${itemId}-`);
  };

  const NavigationButton = ({ item, isSubItem = false }: { item: NavigationItem; isSubItem?: boolean }) => {
    const active = isActive(item.id);
    
    if (collapsed && !isSubItem) {
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={active ? "default" : "ghost"}
                size="sm"
                onClick={() => handleItemClick(item.id)}
                className={`w-full justify-center relative ${
                  active ? 'bg-blue-600 text-white' : 'text-gray-700 dark:text-gray-300'
                }`}
              >
                {item.icon}
                {item.badge && (
                  <Badge 
                    variant="destructive" 
                    className="absolute -top-1 -right-1 h-5 w-5 text-xs flex items-center justify-center p-0"
                  >
                    {item.badge}
                  </Badge>
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>{item.label}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    return (
      <Button
        variant={active ? "default" : "ghost"}
        size="sm"
        onClick={() => handleItemClick(item.id)}
        className={`w-full justify-start gap-3 relative ${
          isSubItem ? 'ml-4 text-sm' : ''
        } ${
          active ? 'bg-blue-600 text-white' : 'text-gray-700 dark:text-gray-300'
        }`}
      >
        {item.icon}
        <span className="flex-1 text-left">{item.label}</span>
        {item.badge && (
          <Badge 
            variant="destructive" 
            className="h-5 text-xs"
          >
            {item.badge}
          </Badge>
        )}
      </Button>
    );
  };

  return (
    <nav id="admin-navigation" className="flex-1 overflow-y-auto py-4">
      <div className="space-y-1 px-3">
        {filteredItems.map((item) => (
          <div key={item.id}>
            <NavigationButton item={item} />
            
            {/* Sub-items */}
            {!collapsed && item.subItems && isActive(item.id) && (
              <div className="mt-1 space-y-1">
                {item.subItems
                  .filter(subItem => subItem.roles.includes(userRole))
                  .map((subItem) => (
                    <NavigationButton 
                      key={subItem.id} 
                      item={subItem} 
                      isSubItem 
                    />
                  ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </nav>
  );
};