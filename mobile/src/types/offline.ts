export interface OfflineState {
  isOnline: boolean;
  lastSyncTime: number;
  pendingActions: OfflineAction[];
  syncInProgress: boolean;
  conflictResolution: ConflictResolution[];
}

export interface OfflineAction {
  id: string;
  type: ActionType;
  payload: any;
  timestamp: number;
  retryCount: number;
  maxRetries: number;
}

export type ActionType = 
  | 'CREATE_GOAL'
  | 'UPDATE_GOAL'
  | 'DELETE_GOAL'
  | 'UPDATE_PROFILE'
  | 'CREATE_SIMULATION'
  | 'UPLOAD_DOCUMENT'
  | 'UPDATE_PREFERENCES';

export interface ConflictResolution {
  id: string;
  type: ConflictType;
  localData: any;
  serverData: any;
  resolution: 'local' | 'server' | 'manual';
  timestamp: number;
}

export type ConflictType = 
  | 'data_conflict'
  | 'version_conflict'
  | 'deletion_conflict';

export interface SyncResult {
  success: boolean;
  syncedCount: number;
  failedCount: number;
  conflicts: ConflictResolution[];
  errors: SyncError[];
}

export interface SyncError {
  actionId: string;
  error: string;
  canRetry: boolean;
}

export interface WatermelonDbSchema {
  version: number;
  tables: TableSchema[];
}

export interface TableSchema {
  name: string;
  columns: ColumnSchema[];
}

export interface ColumnSchema {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date';
  isOptional?: boolean;
  isIndexed?: boolean;
}

// WatermelonDB Model Interfaces
export interface GoalModel {
  id: string;
  userId: string;
  name: string;
  description?: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: number; // timestamp
  priority: string;
  category: string;
  isActive: boolean;
  createdAt: number;
  updatedAt: number;
  syncStatus: SyncStatus;
  lastSynced?: number;
}

export interface ProfileModel {
  id: string;
  userId: string;
  currentAge: number;
  retirementAge: number;
  currentIncome: number;
  currentSavings: number;
  monthlyExpenses: number;
  riskTolerance: string;
  createdAt: number;
  updatedAt: number;
  syncStatus: SyncStatus;
  lastSynced?: number;
}

export interface AccountModel {
  id: string;
  profileId: string;
  name: string;
  type: string;
  balance: number;
  interestRate?: number;
  isRetirement: boolean;
  createdAt: number;
  updatedAt: number;
  syncStatus: SyncStatus;
  lastSynced?: number;
}

export interface DocumentModel {
  id: string;
  userId: string;
  name: string;
  type: string;
  uri: string;
  mimeType: string;
  size: number;
  extractedData?: string; // JSON string
  uploadedAt: number;
  syncStatus: SyncStatus;
  lastSynced?: number;
}

export type SyncStatus = 
  | 'synced'
  | 'pending_create'
  | 'pending_update'
  | 'pending_delete'
  | 'conflict'
  | 'error';

export interface OfflineQueue {
  enqueue: (action: OfflineAction) => void;
  dequeue: () => OfflineAction | null;
  peek: () => OfflineAction | null;
  size: () => number;
  clear: () => void;
  getAll: () => OfflineAction[];
}