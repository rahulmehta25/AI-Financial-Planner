import {configureStore, combineReducers} from '@reduxjs/toolkit';
import {persistStore, persistReducer, createTransform} from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';

import authSlice from './slices/authSlice';
import userSlice from './slices/userSlice';
import financialSlice from './slices/financialSlice';
import offlineSlice from './slices/offlineSlice';
import uiSlice from './slices/uiSlice';
import {apiSlice} from './api/apiSlice';

// Transform to exclude sensitive data from persistence
const sensitiveDataTransform = createTransform(
  // Transform state on its way to being serialized and persisted
  (inboundState: any, key) => {
    if (key === 'auth') {
      // Don't persist sensitive auth data
      const {token, refreshToken, ...rest} = inboundState;
      return rest;
    }
    return inboundState;
  },
  // Transform state being rehydrated
  (outboundState: any, key) => {
    if (key === 'auth') {
      return {
        ...outboundState,
        token: null,
        refreshToken: null,
        isLoading: false,
        error: null,
      };
    }
    return outboundState;
  },
  {whitelist: ['auth']}
);

const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['user', 'financial', 'ui'], // Only persist these reducers
  blacklist: ['auth', 'offline', 'api'], // Don't persist these
  transforms: [sensitiveDataTransform],
  timeout: 10000, // 10 seconds timeout
};

const authPersistConfig = {
  key: 'auth',
  storage: AsyncStorage,
  whitelist: ['biometricEnabled', 'isAuthenticated'], // Only persist these fields
  blacklist: ['token', 'refreshToken', 'isLoading', 'error'],
  timeout: 5000,
};

const rootReducer = combineReducers({
  auth: persistReducer(authPersistConfig, authSlice),
  user: userSlice,
  financial: financialSlice,
  offline: offlineSlice,
  ui: uiSlice,
  api: apiSlice.reducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        ignoredActionsPaths: ['meta.arg', 'payload.timestamp'],
        ignoredPaths: ['items.dates'],
      },
      immutableCheck: {
        ignoredPaths: ['api.mutations', 'api.queries'],
      },
    }).concat(apiSlice.middleware),
  devTools: __DEV__,
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Reset store helper
export const resetStore = () => {
  persistor.purge();
  store.dispatch({type: 'RESET_STORE'});
};

export default store;