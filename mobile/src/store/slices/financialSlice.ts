import {createSlice, createAsyncThunk, PayloadAction} from '@reduxjs/toolkit';
import {FinancialState, FinancialProfile, Goal, Simulation} from '@types/financial';
import {ApiError} from '@types/api';

const initialState: FinancialState = {
  profile: null,
  goals: [],
  simulations: [],
  portfolios: [],
  isLoading: false,
  error: null,
};

// Async thunks
export const createGoal = createAsyncThunk<
  Goal,
  Omit<Goal, 'id' | 'userId' | 'createdAt' | 'updatedAt'>,
  {rejectValue: ApiError}
>('financial/createGoal', async (goalData, {rejectWithValue}) => {
  try {
    const response = await fetch('/api/goals', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(goalData),
    });
    
    if (!response.ok) {
      throw new Error('Failed to create goal');
    }
    
    return await response.json();
  } catch (error: any) {
    return rejectWithValue({
      message: error.message,
      status: 500,
    });
  }
});

export const updateGoal = createAsyncThunk<
  Goal,
  {id: string; data: Partial<Goal>},
  {rejectValue: ApiError}
>('financial/updateGoal', async ({id, data}, {rejectWithValue}) => {
  try {
    const response = await fetch(`/api/goals/${id}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update goal');
    }
    
    return await response.json();
  } catch (error: any) {
    return rejectWithValue({
      message: error.message,
      status: 500,
    });
  }
});

const financialSlice = createSlice({
  name: 'financial',
  initialState,
  reducers: {
    setProfile: (state, action: PayloadAction<FinancialProfile>) => {
      state.profile = action.payload;
    },
    setGoals: (state, action: PayloadAction<Goal[]>) => {
      state.goals = action.payload;
    },
    addGoal: (state, action: PayloadAction<Goal>) => {
      state.goals.push(action.payload);
    },
    removeGoal: (state, action: PayloadAction<string>) => {
      state.goals = state.goals.filter(goal => goal.id !== action.payload);
    },
    setSimulations: (state, action: PayloadAction<Simulation[]>) => {
      state.simulations = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetFinancialState: (state) => {
      state.profile = null;
      state.goals = [];
      state.simulations = [];
      state.portfolios = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Create Goal
    builder
      .addCase(createGoal.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createGoal.fulfilled, (state, action) => {
        state.isLoading = false;
        state.goals.push(action.payload);
        state.error = null;
      })
      .addCase(createGoal.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Failed to create goal';
      });

    // Update Goal
    builder
      .addCase(updateGoal.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateGoal.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.goals.findIndex(goal => goal.id === action.payload.id);
        if (index !== -1) {
          state.goals[index] = action.payload;
        }
        state.error = null;
      })
      .addCase(updateGoal.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload?.message || 'Failed to update goal';
      });
  },
});

export const {
  setProfile,
  setGoals,
  addGoal,
  removeGoal,
  setSimulations,
  clearError,
  resetFinancialState,
} = financialSlice.actions;

export default financialSlice.reducer;