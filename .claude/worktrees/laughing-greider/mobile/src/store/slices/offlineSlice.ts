import {createSlice, PayloadAction} from '@reduxjs/toolkit';
import {OfflineState, OfflineAction, ConflictResolution} from '@types/offline';

const initialState: OfflineState = {
  isOnline: true,
  lastSyncTime: 0,
  pendingActions: [],
  syncInProgress: false,
  conflictResolution: [],
};

const offlineSlice = createSlice({
  name: 'offline',
  initialState,
  reducers: {
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    setSyncInProgress: (state, action: PayloadAction<boolean>) => {
      state.syncInProgress = action.payload;
    },
    setLastSyncTime: (state, action: PayloadAction<number>) => {
      state.lastSyncTime = action.payload;
    },
    addPendingAction: (state, action: PayloadAction<OfflineAction>) => {
      state.pendingActions.push(action.payload);
    },
    removePendingAction: (state, action: PayloadAction<string>) => {
      state.pendingActions = state.pendingActions.filter(
        action => action.id !== action.payload
      );
    },
    clearPendingActions: (state) => {
      state.pendingActions = [];
    },
    addConflictResolution: (state, action: PayloadAction<ConflictResolution>) => {
      state.conflictResolution.push(action.payload);
    },
    removeConflictResolution: (state, action: PayloadAction<string>) => {
      state.conflictResolution = state.conflictResolution.filter(
        conflict => conflict.id !== action.payload
      );
    },
    clearConflictResolutions: (state) => {
      state.conflictResolution = [];
    },
  },
});

export const {
  setOnlineStatus,
  setSyncInProgress,
  setLastSyncTime,
  addPendingAction,
  removePendingAction,
  clearPendingActions,
  addConflictResolution,
  removeConflictResolution,
  clearConflictResolutions,
} = offlineSlice.actions;

export default offlineSlice.reducer;