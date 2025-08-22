import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  FormData,
  FormStep,
  SimulationResult,
  LoadingState,
  UIState,
  Notification,
  PersonalInfo,
  FinancialSnapshot,
  AccountBuckets,
  RiskPreference,
  RetirementGoals,
} from '@/types';

interface FinancialPlanningState {
  // Form data
  formData: Partial<FormData>;
  currentStep: FormStep;
  completedSteps: FormStep[];
  
  // Simulation results
  simulationResult: SimulationResult | null;
  
  // UI state
  loadingState: LoadingState;
  uiState: UIState;
  
  // Actions
  setPersonalInfo: (data: PersonalInfo) => void;
  setFinancialSnapshot: (data: FinancialSnapshot) => void;
  setAccountBuckets: (data: AccountBuckets) => void;
  setRiskPreference: (data: RiskPreference) => void;
  setRetirementGoals: (data: RetirementGoals) => void;
  
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: FormStep) => void;
  
  setSimulationResult: (result: SimulationResult) => void;
  clearSimulationResult: () => void;
  
  setLoading: (key: keyof LoadingState, value: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  
  resetForm: () => void;
  getFormProgress: () => number;
}

const FORM_STEPS: FormStep[] = [
  'personal-info',
  'financial-snapshot',
  'account-buckets',
  'risk-preference',
  'retirement-goals',
  'review',
];

const initialFormData: Partial<FormData> = {
  personalInfo: {
    age: 30,
    retirementAge: 65,
    maritalStatus: 'single',
    dependents: 0,
    state: '',
    zipCode: '',
  },
  financialSnapshot: {
    annualIncome: 0,
    monthlyExpenses: 0,
    totalSavings: 0,
    totalDebt: 0,
    monthlyDebtPayments: 0,
    emergencyFund: 0,
    expectedSocialSecurity: 0,
    pensionValue: 0,
  },
  accountBuckets: {
    taxable: {
      balance: 0,
      monthlyContribution: 0,
    },
    traditional401k: {
      balance: 0,
      monthlyContribution: 0,
      employerMatch: 0,
      employerMatchPercent: 0,
    },
    roth401k: {
      balance: 0,
      monthlyContribution: 0,
    },
    traditionalIRA: {
      balance: 0,
      monthlyContribution: 0,
    },
    rothIRA: {
      balance: 0,
      monthlyContribution: 0,
    },
    hsa: {
      balance: 0,
      monthlyContribution: 0,
    },
  },
  riskPreference: {
    riskTolerance: 'moderate',
    timeHorizon: 30,
    volatilityComfort: 3,
    marketDownturnReaction: 'hold',
    investmentExperience: 'beginner',
  },
  retirementGoals: {
    desiredMonthlyIncome: 0,
    inflationAssumption: 2.5,
    majorExpenses: [],
    legacyGoal: 0,
    healthcareCosts: 0,
    retirementLocation: 'current',
  },
};

export const useFinancialPlanningStore = create<FinancialPlanningState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        formData: initialFormData,
        currentStep: 'personal-info',
        completedSteps: [],
        simulationResult: null,
        loadingState: {
          isSubmitting: false,
          isGeneratingReport: false,
          isExportingPDF: false,
          currentStep: 'personal-info',
        },
        uiState: {
          sidebarOpen: false,
          theme: 'light',
          notifications: [],
        },

        // Form data setters
        setPersonalInfo: (data: PersonalInfo) =>
          set((state) => ({
            formData: {
              ...state.formData,
              personalInfo: data,
            },
            completedSteps: Array.from(
              new Set([...state.completedSteps, 'personal-info'])
            ),
          })),

        setFinancialSnapshot: (data: FinancialSnapshot) =>
          set((state) => ({
            formData: {
              ...state.formData,
              financialSnapshot: data,
            },
            completedSteps: Array.from(
              new Set([...state.completedSteps, 'financial-snapshot'])
            ),
          })),

        setAccountBuckets: (data: AccountBuckets) =>
          set((state) => ({
            formData: {
              ...state.formData,
              accountBuckets: data,
            },
            completedSteps: Array.from(
              new Set([...state.completedSteps, 'account-buckets'])
            ),
          })),

        setRiskPreference: (data: RiskPreference) =>
          set((state) => ({
            formData: {
              ...state.formData,
              riskPreference: data,
            },
            completedSteps: Array.from(
              new Set([...state.completedSteps, 'risk-preference'])
            ),
          })),

        setRetirementGoals: (data: RetirementGoals) =>
          set((state) => ({
            formData: {
              ...state.formData,
              retirementGoals: data,
            },
            completedSteps: Array.from(
              new Set([...state.completedSteps, 'retirement-goals'])
            ),
          })),

        // Navigation
        nextStep: () =>
          set((state) => {
            const currentIndex = FORM_STEPS.indexOf(state.currentStep);
            const nextIndex = Math.min(currentIndex + 1, FORM_STEPS.length - 1);
            return {
              currentStep: FORM_STEPS[nextIndex],
              loadingState: {
                ...state.loadingState,
                currentStep: FORM_STEPS[nextIndex],
              },
            };
          }),

        prevStep: () =>
          set((state) => {
            const currentIndex = FORM_STEPS.indexOf(state.currentStep);
            const prevIndex = Math.max(currentIndex - 1, 0);
            return {
              currentStep: FORM_STEPS[prevIndex],
              loadingState: {
                ...state.loadingState,
                currentStep: FORM_STEPS[prevIndex],
              },
            };
          }),

        goToStep: (step: FormStep) =>
          set((state) => ({
            currentStep: step,
            loadingState: {
              ...state.loadingState,
              currentStep: step,
            },
          })),

        // Simulation results
        setSimulationResult: (result: SimulationResult) =>
          set(() => ({ simulationResult: result })),

        clearSimulationResult: () =>
          set(() => ({ simulationResult: null })),

        // Loading state
        setLoading: (key: keyof LoadingState, value: boolean) =>
          set((state) => ({
            loadingState: {
              ...state.loadingState,
              [key]: value,
            },
          })),

        // UI state
        toggleSidebar: () =>
          set((state) => ({
            uiState: {
              ...state.uiState,
              sidebarOpen: !state.uiState.sidebarOpen,
            },
          })),

        setTheme: (theme: 'light' | 'dark') =>
          set((state) => ({
            uiState: {
              ...state.uiState,
              theme,
            },
          })),

        // Notifications
        addNotification: (notification) =>
          set((state) => {
            const newNotification: Notification = {
              ...notification,
              id: Math.random().toString(36).substr(2, 9),
              timestamp: new Date(),
              autoClose: notification.autoClose ?? true,
            };
            return {
              uiState: {
                ...state.uiState,
                notifications: [...state.uiState.notifications, newNotification],
              },
            };
          }),

        removeNotification: (id: string) =>
          set((state) => ({
            uiState: {
              ...state.uiState,
              notifications: state.uiState.notifications.filter(n => n.id !== id),
            },
          })),

        clearNotifications: () =>
          set((state) => ({
            uiState: {
              ...state.uiState,
              notifications: [],
            },
          })),

        // Utility functions
        resetForm: () =>
          set(() => ({
            formData: initialFormData,
            currentStep: 'personal-info',
            completedSteps: [],
            simulationResult: null,
            loadingState: {
              isSubmitting: false,
              isGeneratingReport: false,
              isExportingPDF: false,
              currentStep: 'personal-info',
            },
          })),

        getFormProgress: () => {
          const { completedSteps } = get();
          return Math.round((completedSteps.length / (FORM_STEPS.length - 1)) * 100);
        },
      }),
      {
        name: 'financial-planning-storage',
        partialize: (state) => ({
          formData: state.formData,
          currentStep: state.currentStep,
          completedSteps: state.completedSteps,
          uiState: {
            theme: state.uiState.theme,
          },
        }),
      }
    ),
    {
      name: 'financial-planning-store',
    }
  )
);