"use client";

import React, { useState } from 'react';
import { X, Users, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import type { UserRole, UserStatus, AccountType } from '../../types';

interface BulkActionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedUserIds: string[];
  onActionComplete: () => void;
}

type BulkActionType = 
  | 'activate' 
  | 'deactivate' 
  | 'suspend' 
  | 'delete' 
  | 'changeRole' 
  | 'changeAccountType' 
  | 'export';

interface BulkAction {
  type: BulkActionType;
  label: string;
  description: string;
  icon: React.ReactNode;
  variant: 'default' | 'destructive' | 'warning';
  requiresConfirmation: boolean;
  additionalFields?: Array<{
    name: string;
    label: string;
    type: 'select';
    options: Array<{ value: string; label: string }>;
  }>;
}

/**
 * BulkActionsModal Component
 * 
 * Features:
 * - Multiple bulk operations
 * - Confirmation dialogs
 * - Progress tracking
 * - Error handling
 */
export const BulkActionsModal: React.FC<BulkActionsModalProps> = ({
  isOpen,
  onClose,
  selectedUserIds,
  onActionComplete,
}) => {
  const [selectedAction, setSelectedAction] = useState<BulkActionType | null>(null);
  const [actionParams, setActionParams] = useState<Record<string, any>>({});
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const bulkActions: BulkAction[] = [
    {
      type: 'activate',
      label: 'Activate Users',
      description: 'Set selected users status to active',
      icon: <CheckCircle className="h-4 w-4" />,
      variant: 'default',
      requiresConfirmation: true,
    },
    {
      type: 'deactivate',
      label: 'Deactivate Users',
      description: 'Set selected users status to inactive',
      icon: <Users className="h-4 w-4" />,
      variant: 'warning',
      requiresConfirmation: true,
    },
    {
      type: 'suspend',
      label: 'Suspend Users',
      description: 'Suspend selected users temporarily',
      icon: <AlertTriangle className="h-4 w-4" />,
      variant: 'destructive',
      requiresConfirmation: true,
    },
    {
      type: 'changeRole',
      label: 'Change Role',
      description: 'Update the role for selected users',
      icon: <Users className="h-4 w-4" />,
      variant: 'default',
      requiresConfirmation: true,
      additionalFields: [
        {
          name: 'newRole',
          label: 'New Role',
          type: 'select',
          options: [
            { value: 'user', label: 'User' },
            { value: 'premium', label: 'Premium' },
            { value: 'enterprise', label: 'Enterprise' },
            { value: 'support', label: 'Support' },
            { value: 'moderator', label: 'Moderator' },
            { value: 'admin', label: 'Admin' },
          ],
        },
      ],
    },
    {
      type: 'changeAccountType',
      label: 'Change Account Type',
      description: 'Update the account type for selected users',
      icon: <Users className="h-4 w-4" />,
      variant: 'default',
      requiresConfirmation: true,
      additionalFields: [
        {
          name: 'newAccountType',
          label: 'New Account Type',
          type: 'select',
          options: [
            { value: 'free', label: 'Free' },
            { value: 'trial', label: 'Trial' },
            { value: 'premium', label: 'Premium' },
            { value: 'enterprise', label: 'Enterprise' },
          ],
        },
      ],
    },
    {
      type: 'export',
      label: 'Export Users',
      description: 'Export selected users data to CSV',
      icon: <Users className="h-4 w-4" />,
      variant: 'default',
      requiresConfirmation: false,
    },
    {
      type: 'delete',
      label: 'Delete Users',
      description: 'Permanently delete selected users (cannot be undone)',
      icon: <AlertTriangle className="h-4 w-4" />,
      variant: 'destructive',
      requiresConfirmation: true,
    },
  ];

  const currentAction = bulkActions.find(action => action.type === selectedAction);

  const handleActionSelect = (actionType: BulkActionType) => {
    setSelectedAction(actionType);
    setActionParams({});
    const action = bulkActions.find(a => a.type === actionType);
    if (action?.requiresConfirmation) {
      setShowConfirmation(true);
    } else {
      executeAction(actionType);
    }
  };

  const executeAction = async (actionType: BulkActionType) => {
    setLoading(true);
    setProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      clearInterval(progressInterval);
      setProgress(100);

      // Simulate specific action logic
      switch (actionType) {
        case 'activate':
          console.log('Activating users:', selectedUserIds);
          break;
        case 'deactivate':
          console.log('Deactivating users:', selectedUserIds);
          break;
        case 'suspend':
          console.log('Suspending users:', selectedUserIds);
          break;
        case 'changeRole':
          console.log('Changing role to', actionParams.newRole, 'for users:', selectedUserIds);
          break;
        case 'changeAccountType':
          console.log('Changing account type to', actionParams.newAccountType, 'for users:', selectedUserIds);
          break;
        case 'export':
          console.log('Exporting users:', selectedUserIds);
          // In real app, this would trigger a download
          break;
        case 'delete':
          console.log('Deleting users:', selectedUserIds);
          break;
      }

      // Wait a moment to show 100% progress
      setTimeout(() => {
        onActionComplete();
        handleClose();
      }, 500);

    } catch (error) {
      console.error('Bulk action failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (selectedAction) {
      executeAction(selectedAction);
      setShowConfirmation(false);
    }
  };

  const handleClose = () => {
    setSelectedAction(null);
    setActionParams({});
    setShowConfirmation(false);
    setLoading(false);
    setProgress(0);
    onClose();
  };

  const updateActionParam = (name: string, value: any) => {
    setActionParams(prev => ({ ...prev, [name]: value }));
  };

  const isActionValid = () => {
    if (!currentAction) return false;
    
    if (currentAction.additionalFields) {
      return currentAction.additionalFields.every(field => 
        actionParams[field.name] !== undefined && actionParams[field.name] !== ''
      );
    }
    
    return true;
  };

  if (loading) {
    return (
      <Dialog open={isOpen} onOpenChange={() => {}}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Processing {currentAction?.label}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="text-center">
              <div className="mb-4">
                <div className="w-16 h-16 mx-auto bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                  {currentAction?.icon}
                </div>
              </div>
              <h3 className="text-lg font-medium mb-2">
                {currentAction?.label}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Processing {selectedUserIds.length} user{selectedUserIds.length === 1 ? '' : 's'}...
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (showConfirmation && currentAction) {
    return (
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              Confirm {currentAction.label}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="text-center">
              <div className="mb-4">
                <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center ${
                  currentAction.variant === 'destructive' 
                    ? 'bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300'
                    : currentAction.variant === 'warning'
                    ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-300'
                    : 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300'
                }`}>
                  {currentAction.icon}
                </div>
              </div>
              <h3 className="text-lg font-medium mb-2">
                {currentAction.label}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {currentAction.description}
              </p>
              
              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                <p className="font-medium text-gray-900 dark:text-white">
                  Selected Users: <Badge variant="secondary">{selectedUserIds.length}</Badge>
                </p>
              </div>
            </div>

            {/* Additional Fields */}
            {currentAction.additionalFields && (
              <div className="space-y-3">
                {currentAction.additionalFields.map((field) => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {field.label}
                    </label>
                    {field.type === 'select' && (
                      <Select
                        value={actionParams[field.name] || ''}
                        onValueChange={(value) => updateActionParam(field.name, value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
                        </SelectTrigger>
                        <SelectContent>
                          {field.options.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                ))}
              </div>
            )}

            {currentAction.variant === 'destructive' && (
              <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
                  <AlertTriangle className="h-4 w-4" />
                  <p className="text-sm font-medium">Warning</p>
                </div>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  This action cannot be undone. Please confirm you want to proceed.
                </p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              variant={currentAction.variant === 'destructive' ? 'destructive' : 'default'}
              onClick={handleConfirm}
              disabled={!isActionValid()}
            >
              {currentAction.variant === 'destructive' ? 'Delete' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Bulk Actions
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              You have selected <Badge variant="secondary">{selectedUserIds.length}</Badge> user{selectedUserIds.length === 1 ? '' : 's'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {bulkActions.map((action) => (
              <button
                key={action.type}
                onClick={() => handleActionSelect(action.type)}
                className={`p-4 rounded-lg border-2 text-left transition-all hover:scale-105 ${
                  action.variant === 'destructive'
                    ? 'border-red-200 hover:border-red-300 hover:bg-red-50 dark:border-red-800 dark:hover:border-red-700 dark:hover:bg-red-900/20'
                    : action.variant === 'warning'
                    ? 'border-yellow-200 hover:border-yellow-300 hover:bg-yellow-50 dark:border-yellow-800 dark:hover:border-yellow-700 dark:hover:bg-yellow-900/20'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50 dark:border-gray-700 dark:hover:border-blue-600 dark:hover:bg-blue-900/20'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${
                    action.variant === 'destructive'
                      ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300'
                      : action.variant === 'warning'
                      ? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-300'
                      : 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300'
                  }`}>
                    {action.icon}
                  </div>
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {action.label}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {action.description}
                </p>
              </button>
            ))}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};