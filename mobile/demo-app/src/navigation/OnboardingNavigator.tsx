import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useTheme } from '../contexts/ThemeContext';

import OnboardingScreen from '../screens/onboarding/OnboardingScreen';

export type OnboardingStackParamList = {
  OnboardingFlow: undefined;
};

const Stack = createStackNavigator<OnboardingStackParamList>();

const OnboardingNavigator: React.FC = () => {
  const { colors } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="OnboardingFlow" component={OnboardingScreen} />
    </Stack.Navigator>
  );
};

export default OnboardingNavigator;