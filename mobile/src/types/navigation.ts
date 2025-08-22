import type {
  CompositeScreenProps,
  NavigatorScreenParams,
} from '@react-navigation/native';
import type {NativeStackScreenProps} from '@react-navigation/native-stack';
import type {BottomTabScreenProps} from '@react-navigation/bottom-tabs';
import type {DrawerScreenProps} from '@react-navigation/drawer';

// Root Navigator
export type RootStackParamList = {
  Onboarding: undefined;
  Auth: undefined;
  Main: undefined;
  BiometricAuth: undefined;
};

// Auth Navigator
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  ResetPassword: {token: string};
};

// Onboarding Navigator
export type OnboardingStackParamList = {
  Welcome: undefined;
  Permissions: undefined;
  BiometricSetup: undefined;
  NotificationSetup: undefined;
};

// Main Navigator (Drawer + Tabs)
export type MainDrawerParamList = {
  Dashboard: NavigatorScreenParams<MainTabParamList>;
  Planning: undefined;
  Goals: undefined;
  Settings: undefined;
  Profile: undefined;
  Support: undefined;
  Logout: undefined;
};

export type MainTabParamList = {
  DashboardTab: NavigatorScreenParams<DashboardStackParamList>;
  PlanningTab: NavigatorScreenParams<PlanningStackParamList>;
  GoalsTab: NavigatorScreenParams<GoalsStackParamList>;
  SettingsTab: NavigatorScreenParams<SettingsStackParamList>;
};

// Individual Stack Navigators
export type DashboardStackParamList = {
  DashboardHome: undefined;
  PortfolioDetail: {portfolioId: string};
  SimulationResults: {simulationId: string};
};

export type PlanningStackParamList = {
  PlanningHome: undefined;
  FormWizard: {step?: number};
  DocumentScanner: {documentType: string};
  DataReview: undefined;
};

export type GoalsStackParamList = {
  GoalsHome: undefined;
  CreateGoal: undefined;
  GoalDetail: {goalId: string};
  EditGoal: {goalId: string};
};

export type SettingsStackParamList = {
  SettingsHome: undefined;
  Profile: undefined;
  Security: undefined;
  NotificationSettings: undefined;
  BiometricSettings: undefined;
  DataSync: undefined;
  About: undefined;
};

// Screen Props Types
export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

export type AuthStackScreenProps<T extends keyof AuthStackParamList> =
  NativeStackScreenProps<AuthStackParamList, T>;

export type OnboardingStackScreenProps<T extends keyof OnboardingStackParamList> =
  NativeStackScreenProps<OnboardingStackParamList, T>;

export type MainDrawerScreenProps<T extends keyof MainDrawerParamList> =
  DrawerScreenProps<MainDrawerParamList, T>;

export type MainTabScreenProps<T extends keyof MainTabParamList> =
  CompositeScreenProps<
    BottomTabScreenProps<MainTabParamList, T>,
    DrawerScreenProps<MainDrawerParamList>
  >;

export type DashboardStackScreenProps<T extends keyof DashboardStackParamList> =
  CompositeScreenProps<
    NativeStackScreenProps<DashboardStackParamList, T>,
    MainTabScreenProps<keyof MainTabParamList>
  >;

export type PlanningStackScreenProps<T extends keyof PlanningStackParamList> =
  CompositeScreenProps<
    NativeStackScreenProps<PlanningStackParamList, T>,
    MainTabScreenProps<keyof MainTabParamList>
  >;

export type GoalsStackScreenProps<T extends keyof GoalsStackParamList> =
  CompositeScreenProps<
    NativeStackScreenProps<GoalsStackParamList, T>,
    MainTabScreenProps<keyof MainTabParamList>
  >;

export type SettingsStackScreenProps<T extends keyof SettingsStackParamList> =
  CompositeScreenProps<
    NativeStackScreenProps<SettingsStackParamList, T>,
    MainTabScreenProps<keyof MainTabParamList>
  >;

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}