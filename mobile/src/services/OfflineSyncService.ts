import {Database, Q} from '@nozbe/watermelondb';
import SQLiteAdapter from '@nozbe/watermelondb/adapters/sqlite';
import {synchronize} from '@nozbe/watermelondb/sync';
import NetInfo from '@react-native-community/netinfo';

import {OfflineAction, SyncResult, SyncError, ConflictResolution} from '@types/offline';
import {API_CONFIG, OFFLINE_CONFIG} from '@constants/config';
import {HapticService} from './HapticService';
import schema from '../database/schema';
import migrations from '../database/migrations';
import {Goal, Profile, Account, Document} from '../database/models';

class OfflineSyncServiceClass {
  private database: Database;
  private syncInProgress: boolean = false;
  private lastSyncTime: number = 0;
  private pendingActions: OfflineAction[] = [];
  private syncInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Initialize database
    const adapter = new SQLiteAdapter({
      schema,
      migrations,
      jsi: true,
      onSetUpError: (error) => {
        console.error('Database setup error:', error);
      },
    });

    this.database = new Database({
      adapter,
      modelClasses: [Goal, Profile, Account, Document],
    });
  }

  /**
   * Initialize offline sync service
   */
  async initialize(): Promise<void> {
    try {
      // Load pending actions from storage
      await this.loadPendingActions();

      // Set up network listener
      this.setupNetworkListener();

      // Start periodic sync
      this.startPeriodicSync();

      console.log('Offline sync service initialized');
    } catch (error) {
      console.error('Error initializing offline sync service:', error);
    }
  }

  /**
   * Get database instance
   */
  getDatabase(): Database {
    return this.database;
  }

  /**
   * Check if device is online
   */
  async isOnline(): Promise<boolean> {
    const netInfo = await NetInfo.fetch();
    return netInfo.isConnected && netInfo.isInternetReachable;
  }

  /**
   * Add action to offline queue
   */
  async queueAction(action: Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount'>): Promise<void> {
    const offlineAction: OfflineAction = {
      id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      retryCount: 0,
      maxRetries: OFFLINE_CONFIG.MAX_RETRY_ATTEMPTS,
      ...action,
    };

    this.pendingActions.push(offlineAction);
    await this.savePendingActions();

    console.log('Action queued for offline sync:', offlineAction.type);

    // Try to sync immediately if online
    if (await this.isOnline()) {
      this.syncPendingActions();
    }
  }

  /**
   * Perform full synchronization
   */
  async performFullSync(): Promise<SyncResult> {
    if (this.syncInProgress) {
      console.log('Sync already in progress');
      return {
        success: false,
        syncedCount: 0,
        failedCount: 0,
        conflicts: [],
        errors: [{actionId: 'sync', error: 'Sync already in progress', canRetry: false}],
      };
    }

    try {
      this.syncInProgress = true;
      console.log('Starting full synchronization...');

      // Trigger haptic feedback
      HapticService.financial.sync();

      const result = await synchronize({
        database: this.database,
        pullChanges: async ({lastPulledAt, schemaVersion, migration}) => {
          console.log('Pulling changes since:', new Date(lastPulledAt || 0));
          
          const response = await fetch(`${API_CONFIG.BASE_URL}/api/sync/pull`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              // Add auth headers here
            },
            body: JSON.stringify({
              lastPulledAt,
              schemaVersion,
              migration,
            }),
          });

          if (!response.ok) {
            throw new Error(`Pull failed: ${response.status}`);
          }

          return await response.json();
        },
        pushChanges: async ({changes, lastPulledAt}) => {
          console.log('Pushing changes:', changes);
          
          const response = await fetch(`${API_CONFIG.BASE_URL}/api/sync/push`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              // Add auth headers here
            },
            body: JSON.stringify({
              changes,
              lastPulledAt,
            }),
          });

          if (!response.ok) {
            throw new Error(`Push failed: ${response.status}`);
          }

          return await response.json();
        },
        sendCreatedAsUpdated: true,
        log: __DEV__ ? console.log : undefined,
      });

      // Sync pending actions
      await this.syncPendingActions();

      this.lastSyncTime = Date.now();
      
      return {
        success: true,
        syncedCount: result.changes?.created?.length || 0,
        failedCount: 0,
        conflicts: [],
        errors: [],
      };
    } catch (error: any) {
      console.error('Full sync error:', error);
      
      return {
        success: false,
        syncedCount: 0,
        failedCount: 1,
        conflicts: [],
        errors: [{actionId: 'full_sync', error: error.message, canRetry: true}],
      };
    } finally {
      this.syncInProgress = false;
    }
  }

  /**
   * Sync pending actions
   */
  private async syncPendingActions(): Promise<void> {
    if (this.pendingActions.length === 0) {
      return;
    }

    console.log(`Syncing ${this.pendingActions.length} pending actions...`);

    const actionsToRetry: OfflineAction[] = [];

    for (const action of this.pendingActions) {
      try {
        await this.executeAction(action);
        console.log('Action synced successfully:', action.type);
      } catch (error: any) {
        console.error('Action sync failed:', action.type, error);
        
        action.retryCount++;
        
        if (action.retryCount < action.maxRetries) {
          actionsToRetry.push(action);
        } else {
          console.error('Action max retries exceeded:', action.type);
        }
      }
    }

    this.pendingActions = actionsToRetry;
    await this.savePendingActions();
  }

  /**
   * Execute a specific action
   */
  private async executeAction(action: OfflineAction): Promise<void> {
    const url = this.getActionEndpoint(action.type);
    const method = this.getActionMethod(action.type);

    const response = await fetch(`${API_CONFIG.BASE_URL}${url}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        // Add auth headers here
      },
      body: JSON.stringify(action.payload),
    });

    if (!response.ok) {
      throw new Error(`Action failed: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get API endpoint for action type
   */
  private getActionEndpoint(actionType: string): string {
    const endpoints: Record<string, string> = {
      CREATE_GOAL: '/api/goals',
      UPDATE_GOAL: '/api/goals',
      DELETE_GOAL: '/api/goals',
      UPDATE_PROFILE: '/api/profiles',
      CREATE_SIMULATION: '/api/simulations',
      UPLOAD_DOCUMENT: '/api/documents',
      UPDATE_PREFERENCES: '/api/preferences',
    };

    return endpoints[actionType] || '/api/sync';
  }

  /**
   * Get HTTP method for action type
   */
  private getActionMethod(actionType: string): string {
    const methods: Record<string, string> = {
      CREATE_GOAL: 'POST',
      UPDATE_GOAL: 'PUT',
      DELETE_GOAL: 'DELETE',
      UPDATE_PROFILE: 'PUT',
      CREATE_SIMULATION: 'POST',
      UPLOAD_DOCUMENT: 'POST',
      UPDATE_PREFERENCES: 'PUT',
    };

    return methods[actionType] || 'POST';
  }

  /**
   * Setup network status listener
   */
  private setupNetworkListener(): void {
    NetInfo.addEventListener((state) => {
      if (state.isConnected && state.isInternetReachable) {
        console.log('Network reconnected, starting sync...');
        this.performFullSync();
      }
    });
  }

  /**
   * Start periodic sync
   */
  private startPeriodicSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    this.syncInterval = setInterval(async () => {
      if (await this.isOnline() && !this.syncInProgress) {
        this.performFullSync();
      }
    }, OFFLINE_CONFIG.SYNC_INTERVAL);
  }

  /**
   * Stop periodic sync
   */
  stopPeriodicSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  /**
   * Load pending actions from storage
   */
  private async loadPendingActions(): Promise<void> {
    try {
      // In a real app, you would load from AsyncStorage or MMKV
      // For now, initialize empty array
      this.pendingActions = [];
    } catch (error) {
      console.error('Error loading pending actions:', error);
      this.pendingActions = [];
    }
  }

  /**
   * Save pending actions to storage
   */
  private async savePendingActions(): Promise<void> {
    try {
      // In a real app, you would save to AsyncStorage or MMKV
      console.log('Saving pending actions:', this.pendingActions.length);
    } catch (error) {
      console.error('Error saving pending actions:', error);
    }
  }

  /**
   * Get sync status
   */
  getSyncStatus(): {
    inProgress: boolean;
    lastSyncTime: number;
    pendingActionsCount: number;
  } {
    return {
      inProgress: this.syncInProgress,
      lastSyncTime: this.lastSyncTime,
      pendingActionsCount: this.pendingActions.length,
    };
  }

  /**
   * Force sync now
   */
  async forceSyncNow(): Promise<SyncResult> {
    if (!(await this.isOnline())) {
      throw new Error('Device is offline');
    }

    return this.performFullSync();
  }

  /**
   * Clear all offline data
   */
  async clearOfflineData(): Promise<void> {
    try {
      await this.database.write(async () => {
        await this.database.unsafeResetDatabase();
      });
      
      this.pendingActions = [];
      await this.savePendingActions();
      
      console.log('Offline data cleared');
    } catch (error) {
      console.error('Error clearing offline data:', error);
      throw error;
    }
  }

  /**
   * Get database statistics
   */
  async getDatabaseStats(): Promise<{
    goals: number;
    profiles: number;
    accounts: number;
    documents: number;
  }> {
    try {
      const [goals, profiles, accounts, documents] = await Promise.all([
        this.database.get('goals').query().fetchCount(),
        this.database.get('profiles').query().fetchCount(),
        this.database.get('accounts').query().fetchCount(),
        this.database.get('documents').query().fetchCount(),
      ]);

      return {goals, profiles, accounts, documents};
    } catch (error) {
      console.error('Error getting database stats:', error);
      return {goals: 0, profiles: 0, accounts: 0, documents: 0};
    }
  }
}

export const OfflineSyncService = new OfflineSyncServiceClass();