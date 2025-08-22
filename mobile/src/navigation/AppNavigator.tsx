import React from 'react';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import {useSelector} from 'react-redux';

import {RootState} from '@store/store';
import AuthNavigator from './AuthNavigator';
import MainNavigator from './MainNavigator';
import OnboardingNavigator from './OnboardingNavigator';
import BiometricAuthScreen from '@screens/auth/BiometricAuthScreen';

export type RootStackParamList = {
  Onboarding: undefined;
  Auth: undefined;
  Main: undefined;
  BiometricAuth: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const AppNavigator: React.FC = () => {
  const {isAuthenticated, hasCompletedOnboarding, biometricEnabled} = useSelector(
    (state: RootState) => ({
      isAuthenticated: state.auth.isAuthenticated,
      hasCompletedOnboarding: state.user.hasCompletedOnboarding,
      biometricEnabled: state.auth.biometricEnabled,
    })
  );

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        gestureEnabled: false,
      }}>
      {!hasCompletedOnboarding ? (
        <Stack.Screen name="Onboarding" component={OnboardingNavigator} />
      ) : !isAuthenticated ? (
        <>
          {biometricEnabled && (
            <Stack.Screen name="BiometricAuth" component={BiometricAuthScreen} />
          )}
          <Stack.Screen name="Auth" component={AuthNavigator} />
        </>
      ) : (
        <Stack.Screen name="Main" component={MainNavigator} />
      )}
    </Stack.Navigator>
  );
};

export default AppNavigator;