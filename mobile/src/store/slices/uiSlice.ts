import {createSlice, PayloadAction} from '@reduxjs/toolkit';
import {NetworkState, AppState} from '@types/common';

interface UIState {
  networkStatus: NetworkState;
  appState: AppState;
  theme: 'light' | 'dark' | 'system';
  isLoading: boolean;
  loadingMessage: string;
  toasts: Toast[];
  modals: Modal[];
}

interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  autoClose?: boolean;
}

interface Modal {
  id: string;
  type: string;
  props: any;
  isVisible: boolean;
}

const initialState: UIState = {
  networkStatus: {
    isConnected: true,
    connectionType: 'unknown',
    isInternetReachable: true,
  },
  appState: {
    appState: 'active',
    lastActiveTime: Date.now(),
    sessionStartTime: Date.now(),
  },
  theme: 'system',
  isLoading: false,
  loadingMessage: '',
  toasts: [],
  modals: [],
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setNetworkStatus: (state, action: PayloadAction<NetworkState>) => {
      state.networkStatus = action.payload;
    },
    setAppState: (state, action: PayloadAction<AppState>) => {
      state.appState = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'system'>) => {
      state.theme = action.payload;
    },
    setLoading: (state, action: PayloadAction<{isLoading: boolean; message?: string}>) => {
      state.isLoading = action.payload.isLoading;
      state.loadingMessage = action.payload.message || '';
    },
    showToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const toast: Toast = {
        id: `toast_${Date.now()}`,
        ...action.payload,
        duration: action.payload.duration || 3000,
        autoClose: action.payload.autoClose !== false,
      };
      state.toasts.push(toast);
    },
    hideToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload);
    },
    clearToasts: (state) => {
      state.toasts = [];
    },
    showModal: (state, action: PayloadAction<Omit<Modal, 'id' | 'isVisible'>>) => {
      const modal: Modal = {
        id: `modal_${Date.now()}`,
        isVisible: true,
        ...action.payload,
      };
      state.modals.push(modal);
    },
    hideModal: (state, action: PayloadAction<string>) => {
      const modal = state.modals.find(m => m.id === action.payload);
      if (modal) {
        modal.isVisible = false;
      }
    },
    removeModal: (state, action: PayloadAction<string>) => {
      state.modals = state.modals.filter(modal => modal.id !== action.payload);
    },
    clearModals: (state) => {
      state.modals = [];
    },
  },
});

export const {
  setNetworkStatus,
  setAppState,
  setTheme,
  setLoading,
  showToast,
  hideToast,
  clearToasts,
  showModal,
  hideModal,
  removeModal,
  clearModals,
} = uiSlice.actions;

export default uiSlice.reducer;