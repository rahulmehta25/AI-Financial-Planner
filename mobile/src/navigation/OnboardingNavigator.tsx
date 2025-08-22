import React from 'react';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import WelcomeScreen from '@screens/onboarding/WelcomeScreen';
import PermissionsScreen from '@screens/onboarding/PermissionsScreen';
import BiometricSetupScreen from '@screens/onboarding/BiometricSetupScreen';
import NotificationSetupScreen from '@screens/onboarding/NotificationSetupScreen';

export type OnboardingStackParamList = {
  Welcome: undefined;
  Permissions: undefined;
  BiometricSetup: undefined;
  NotificationSetup: undefined;
};

const Stack = createNativeStackNavigator<OnboardingStackParamList>();

const OnboardingNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        gestureEnabled: true,
      }}>
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="Permissions" component={PermissionsScreen} />
      <Stack.Screen name="BiometricSetup" component={BiometricSetupScreen} />
      <Stack.Screen name="NotificationSetup" component={NotificationSetupScreen} />
    </Stack.Navigator>
  );
};

export default OnboardingNavigator;