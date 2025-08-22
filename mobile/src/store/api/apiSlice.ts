import {createApi, fetchBaseQuery} from '@reduxjs/toolkit/query/react';
import {RootState} from '../store';
import {API_CONFIG} from '@constants/config';

// Base query with authentication
const baseQuery = fetchBaseQuery({
  baseUrl: API_CONFIG.BASE_URL + '/api/v1',
  timeout: API_CONFIG.TIMEOUT,
  prepareHeaders: (headers, {getState}) => {
    const token = (getState() as RootState).auth.token;
    
    // Set default headers
    headers.set('Content-Type', 'application/json');
    headers.set('Accept', 'application/json');
    
    // Add auth token if available
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    
    return headers;
  },
});

// Base query with retry and token refresh
const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  let result = await baseQuery(args, api, extraOptions);
  
  // If we get a 401, try to refresh the token
  if (result.error && result.error.status === 401) {
    // Try to refresh token
    const refreshResult = await baseQuery(
      {
        url: '/auth/refresh',
        method: 'POST',
        body: {
          refreshToken: (api.getState() as RootState).auth.refreshToken,
        },
      },
      api,
      extraOptions
    );
    
    if (refreshResult.data) {
      // Store the new tokens
      api.dispatch({
        type: 'auth/setTokens',
        payload: refreshResult.data,
      });
      
      // Retry the original query
      result = await baseQuery(args, api, extraOptions);
    } else {
      // Refresh failed, logout user
      api.dispatch({type: 'auth/logout'});
    }
  }
  
  return result;
};

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'User',
    'Profile',
    'Goal',
    'Simulation',
    'Portfolio',
    'Account',
    'Document',
    'Preference',
  ],
  endpoints: (builder) => ({
    // Auth endpoints
    getCurrentUser: builder.query<any, void>({
      query: () => '/users/me',
      providesTags: ['User'],
    }),
    
    updateProfile: builder.mutation<any, any>({
      query: (data) => ({
        url: '/users/me',
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['User', 'Profile'],
    }),
    
    // Financial Profile endpoints
    getFinancialProfile: builder.query<any, void>({
      query: () => '/financial-profiles/me',
      providesTags: ['Profile'],
    }),
    
    createFinancialProfile: builder.mutation<any, any>({
      query: (data) => ({
        url: '/financial-profiles',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Profile'],
    }),
    
    updateFinancialProfile: builder.mutation<any, {id: string; data: any}>({
      query: ({id, data}) => ({
        url: `/financial-profiles/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Profile'],
    }),
    
    // Goals endpoints
    getGoals: builder.query<any, void>({
      query: () => '/goals',
      providesTags: ['Goal'],
    }),
    
    createGoal: builder.mutation<any, any>({
      query: (data) => ({
        url: '/goals',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Goal'],
    }),
    
    updateGoal: builder.mutation<any, {id: string; data: any}>({
      query: ({id, data}) => ({
        url: `/goals/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Goal'],
    }),
    
    deleteGoal: builder.mutation<any, string>({
      query: (id) => ({
        url: `/goals/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Goal'],
    }),
    
    // Simulations endpoints
    getSimulations: builder.query<any, void>({
      query: () => '/simulations',
      providesTags: ['Simulation'],
    }),
    
    runSimulation: builder.mutation<any, any>({
      query: (data) => ({
        url: '/simulations/run',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Simulation'],
    }),
    
    getSimulationResult: builder.query<any, string>({
      query: (id) => `/simulations/${id}`,
      providesTags: ['Simulation'],
    }),
    
    // Portfolios endpoints
    getPortfolios: builder.query<any, void>({
      query: () => '/portfolios',
      providesTags: ['Portfolio'],
    }),
    
    getPortfolio: builder.query<any, string>({
      query: (id) => `/portfolios/${id}`,
      providesTags: ['Portfolio'],
    }),
    
    // Documents endpoints
    uploadDocument: builder.mutation<any, FormData>({
      query: (formData) => ({
        url: '/documents/upload',
        method: 'POST',
        body: formData,
        formData: true,
      }),
      invalidatesTags: ['Document'],
    }),
    
    getDocuments: builder.query<any, void>({
      query: () => '/documents',
      providesTags: ['Document'],
    }),
    
    deleteDocument: builder.mutation<any, string>({
      query: (id) => ({
        url: `/documents/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Document'],
    }),
    
    // Preferences endpoints
    getPreferences: builder.query<any, void>({
      query: () => '/users/me/preferences',
      providesTags: ['Preference'],
    }),
    
    updatePreferences: builder.mutation<any, any>({
      query: (data) => ({
        url: '/users/me/preferences',
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Preference'],
    }),
  }),
});

export const {
  // User
  useGetCurrentUserQuery,
  useUpdateProfileMutation,
  
  // Financial Profile
  useGetFinancialProfileQuery,
  useCreateFinancialProfileMutation,
  useUpdateFinancialProfileMutation,
  
  // Goals
  useGetGoalsQuery,
  useCreateGoalMutation,
  useUpdateGoalMutation,
  useDeleteGoalMutation,
  
  // Simulations
  useGetSimulationsQuery,
  useRunSimulationMutation,
  useGetSimulationResultQuery,
  
  // Portfolios
  useGetPortfoliosQuery,
  useGetPortfolioQuery,
  
  // Documents
  useUploadDocumentMutation,
  useGetDocumentsQuery,
  useDeleteDocumentMutation,
  
  // Preferences
  useGetPreferencesQuery,
  useUpdatePreferencesMutation,
} = apiSlice;