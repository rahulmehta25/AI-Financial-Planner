"use client";

import React, { useState, useEffect } from 'react';
import { 
  X, 
  User, 
  Mail, 
  Calendar, 
  Shield, 
  Activity, 
  CreditCard, 
  Settings,
  Edit,
  Save,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { AdminUser, UserRole, UserStatus, AccountType } from '../../types';

interface UserDetailsModalProps {
  user: AdminUser;
  isOpen: boolean;
  onClose: () => void;
  onUserUpdate: (userId: string, updates: Partial<AdminUser>) => void;
  permissions: {
    canEdit: boolean;
    canDelete: boolean;
  };
}

/**
 * UserDetailsModal Component
 * 
 * Features:
 * - User profile editing
 * - Activity history
 * - Permission management
 * - Subscription details
 */
export const UserDetailsModal: React.FC<UserDetailsModalProps> = ({
  user,
  isOpen,
  onClose,
  onUserUpdate,
  permissions,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedUser, setEditedUser] = useState(user);
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setEditedUser(user);
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    try {
      onUserUpdate(user.id, editedUser);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditedUser(user);
    setIsEditing(false);
  };

  const updateField = (field: keyof AdminUser, value: any) => {
    setEditedUser(prev => ({ ...prev, [field]: value }));
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                <User className="h-5 w-5 text-blue-600 dark:text-blue-300" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">
                  {user.firstName} {user.lastName}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {user.email}
                </p>
              </div>
            </DialogTitle>
            <div className="flex items-center gap-2">
              {permissions.canEdit && !isEditing && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(true)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              )}
              {isEditing && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancel}
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSave}
                    disabled={loading}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                </>
              )}
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
            <TabsTrigger value="permissions">Permissions</TabsTrigger>
            <TabsTrigger value="subscription">Subscription</TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <Card className="p-6">
                <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Basic Information
                </h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        First Name
                      </label>
                      {isEditing ? (
                        <Input
                          value={editedUser.firstName}
                          onChange={(e) => updateField('firstName', e.target.value)}
                          className="mt-1"
                        />
                      ) : (
                        <p className="mt-1 text-sm text-gray-900 dark:text-white">
                          {user.firstName}
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Last Name
                      </label>
                      {isEditing ? (
                        <Input
                          value={editedUser.lastName}
                          onChange={(e) => updateField('lastName', e.target.value)}
                          className="mt-1"
                        />
                      ) : (
                        <p className="mt-1 text-sm text-gray-900 dark:text-white">
                          {user.lastName}
                        </p>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Email
                    </label>
                    {isEditing ? (
                      <Input
                        value={editedUser.email}
                        onChange={(e) => updateField('email', e.target.value)}
                        className="mt-1"
                        type="email"
                      />
                    ) : (
                      <div className="mt-1 flex items-center gap-2">
                        <p className="text-sm text-gray-900 dark:text-white">
                          {user.email}
                        </p>
                        {user.emailVerified && (
                          <Badge variant="secondary" className="text-xs">
                            <Mail className="h-3 w-3 mr-1" />
                            Verified
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      User ID
                    </label>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white font-mono">
                      {user.id}
                    </p>
                  </div>
                </div>
              </Card>

              {/* Account Status */}
              <Card className="p-6">
                <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Account Status
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Role
                    </label>
                    {isEditing ? (
                      <Select
                        value={editedUser.role}
                        onValueChange={(value) => updateField('role', value as UserRole)}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">User</SelectItem>
                          <SelectItem value="premium">Premium</SelectItem>
                          <SelectItem value="enterprise">Enterprise</SelectItem>
                          <SelectItem value="support">Support</SelectItem>
                          <SelectItem value="moderator">Moderator</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <div className="mt-1">
                        <Badge className={getRoleBadgeColor(user.role)}>
                          {user.role}
                        </Badge>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Status
                    </label>
                    {isEditing ? (
                      <Select
                        value={editedUser.status}
                        onValueChange={(value) => updateField('status', value as UserStatus)}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="inactive">Inactive</SelectItem>
                          <SelectItem value="suspended">Suspended</SelectItem>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="banned">Banned</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <div className="mt-1">
                        <Badge className={getStatusBadgeColor(user.status)}>
                          {user.status}
                        </Badge>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Account Type
                    </label>
                    {isEditing ? (
                      <Select
                        value={editedUser.accountType}
                        onValueChange={(value) => updateField('accountType', value as AccountType)}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="free">Free</SelectItem>
                          <SelectItem value="trial">Trial</SelectItem>
                          <SelectItem value="premium">Premium</SelectItem>
                          <SelectItem value="enterprise">Enterprise</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <p className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                        {user.accountType}
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Created
                      </label>
                      <p className="mt-1 text-sm text-gray-900 dark:text-white">
                        <Calendar className="h-3 w-3 inline mr-1" />
                        {formatDate(user.createdAt)}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Last Login
                      </label>
                      <p className="mt-1 text-sm text-gray-900 dark:text-white">
                        <Activity className="h-3 w-3 inline mr-1" />
                        {formatDate(user.lastLoginAt)}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* User Metrics */}
            {user.metrics && (
              <Card className="p-6">
                <h3 className="text-lg font-medium mb-4">User Metrics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Logins</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {user.metrics.totalLogins.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Sessions This Month</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {user.metrics.sessionsThisMonth}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Engagement Score</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {user.metrics.engagementScore}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Plan Completion</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {user.metrics.planCompletionRate}%
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </TabsContent>

          {/* Activity Tab */}
          <TabsContent value="activity" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Recent Activity
              </h3>
              <div className="space-y-4">
                {/* Mock activity data */}
                {[
                  { action: 'Login', time: '2 hours ago', details: 'Web application login' },
                  { action: 'Profile Update', time: '1 day ago', details: 'Updated contact information' },
                  { action: 'Plan Creation', time: '3 days ago', details: 'Created retirement plan' },
                  { action: 'Report Download', time: '1 week ago', details: 'Downloaded financial report' },
                ].map((activity, index) => (
                  <div key={index} className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{activity.action}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{activity.details}</p>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{activity.time}</p>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Permissions Tab */}
          <TabsContent value="permissions" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5" />
                User Permissions
              </h3>
              <div className="space-y-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Permissions are based on the user's role: <Badge className={getRoleBadgeColor(user.role)}>{user.role}</Badge>
                </p>
                
                {/* Mock permissions based on role */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {user.role === 'admin' ? (
                    <>
                      <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <span className="text-sm font-medium">Full System Access</span>
                        <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                          Granted
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <span className="text-sm font-medium">User Management</span>
                        <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                          Granted
                        </Badge>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <span className="text-sm font-medium">Financial Planning</span>
                        <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                          Granted
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <span className="text-sm font-medium">Admin Panel Access</span>
                        <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                          Denied
                        </Badge>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* Subscription Tab */}
          <TabsContent value="subscription" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Subscription Details
              </h3>
              <div className="space-y-4">
                {user.subscription ? (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Plan</label>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                          {user.subscription.plan}
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Status</label>
                        <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                          {user.subscription.status}
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Current Period Start</label>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {formatDate(user.subscription.currentPeriodStart)}
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Current Period End</label>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {formatDate(user.subscription.currentPeriodEnd)}
                        </p>
                      </div>
                    </div>
                    {user.subscription.trialEnd && (
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Trial End</label>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {formatDate(user.subscription.trialEnd)}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <AlertTriangle className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      No Active Subscription
                    </h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      This user does not have an active subscription.
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};