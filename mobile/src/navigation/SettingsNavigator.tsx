import React from 'react';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import SettingsHomeScreen from '@screens/settings/SettingsHomeScreen';
import ProfileScreen from '@screens/settings/ProfileScreen';
import SecurityScreen from '@screens/settings/SecurityScreen';
import NotificationSettingsScreen from '@screens/settings/NotificationSettingsScreen';
import BiometricSettingsScreen from '@screens/settings/BiometricSettingsScreen';
import DataSyncScreen from '@screens/settings/DataSyncScreen';
import AboutScreen from '@screens/settings/AboutScreen';

export type SettingsStackParamList = {
  SettingsHome: undefined;
  Profile: undefined;
  Security: undefined;
  NotificationSettings: undefined;
  BiometricSettings: undefined;
  DataSync: undefined;
  About: undefined;
};

const Stack = createNativeStackNavigator<SettingsStackParamList>();

const SettingsNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: true,
        headerBackTitleVisible: false,
      }}>
      <Stack.Screen
        name="SettingsHome"
        component={SettingsHomeScreen}
        options={{title: 'Settings'}}
      />
      <Stack.Screen
        name="Profile"
        component={ProfileScreen}
        options={{title: 'Profile'}}
      />
      <Stack.Screen
        name="Security"
        component={SecurityScreen}
        options={{title: 'Security'}}
      />
      <Stack.Screen
        name="NotificationSettings"
        component={NotificationSettingsScreen}
        options={{title: 'Notifications'}}
      />
      <Stack.Screen
        name="BiometricSettings"
        component={BiometricSettingsScreen}
        options={{title: 'Biometric Settings'}}
      />
      <Stack.Screen
        name="DataSync"
        component={DataSyncScreen}
        options={{title: 'Data Synchronization'}}
      />
      <Stack.Screen
        name="About"
        component={AboutScreen}
        options={{title: 'About'}}
      />
    </Stack.Navigator>
  );
};

export default SettingsNavigator;