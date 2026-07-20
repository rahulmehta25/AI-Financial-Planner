import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createDrawerNavigator} from '@react-navigation/drawer';
import {Platform} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

import DashboardNavigator from './DashboardNavigator';
import PlanningNavigator from './PlanningNavigator';
import GoalsNavigator from './GoalsNavigator';
import SettingsNavigator from './SettingsNavigator';
import {colors, fonts} from '@constants/theme';

export type MainTabParamList = {
  DashboardTab: undefined;
  PlanningTab: undefined;
  GoalsTab: undefined;
  SettingsTab: undefined;
};

export type MainDrawerParamList = {
  Dashboard: undefined;
  Planning: undefined;
  Goals: undefined;
  Settings: undefined;
  Profile: undefined;
  Support: undefined;
  Logout: undefined;
};

const Tab = createBottomTabNavigator<MainTabParamList>();
const Drawer = createDrawerNavigator<MainDrawerParamList>();

const TabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        headerShown: false,
        tabBarIcon: ({focused, color, size}) => {
          let iconName: string;

          switch (route.name) {
            case 'DashboardTab':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'PlanningTab':
              iconName = focused ? 'calculator' : 'calculator-outline';
              break;
            case 'GoalsTab':
              iconName = focused ? 'flag' : 'flag-outline';
              break;
            case 'SettingsTab':
              iconName = focused ? 'settings' : 'settings-outline';
              break;
            default:
              iconName = 'circle';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.gray,
        tabBarLabelStyle: {
          fontFamily: fonts.medium,
          fontSize: 12,
        },
        tabBarStyle: {
          backgroundColor: colors.white,
          borderTopWidth: 1,
          borderTopColor: colors.lightGray,
          paddingBottom: Platform.OS === 'ios' ? 20 : 10,
          height: Platform.OS === 'ios' ? 90 : 70,
        },
      })}>
      <Tab.Screen
        name="DashboardTab"
        component={DashboardNavigator}
        options={{tabBarLabel: 'Dashboard'}}
      />
      <Tab.Screen
        name="PlanningTab"
        component={PlanningNavigator}
        options={{tabBarLabel: 'Planning'}}
      />
      <Tab.Screen
        name="GoalsTab"
        component={GoalsNavigator}
        options={{tabBarLabel: 'Goals'}}
      />
      <Tab.Screen
        name="SettingsTab"
        component={SettingsNavigator}
        options={{tabBarLabel: 'Settings'}}
      />
    </Tab.Navigator>
  );
};

const MainNavigator: React.FC = () => {
  return (
    <Drawer.Navigator
      screenOptions={{
        headerShown: false,
        drawerStyle: {
          backgroundColor: colors.white,
          width: 280,
        },
        drawerActiveTintColor: colors.primary,
        drawerInactiveTintColor: colors.gray,
        drawerLabelStyle: {
          fontFamily: fonts.medium,
          fontSize: 16,
        },
      }}>
      <Drawer.Screen
        name="Dashboard"
        component={TabNavigator}
        options={{
          drawerIcon: ({color, size}) => (
            <Icon name="home-outline" size={size} color={color} />
          ),
        }}
      />
    </Drawer.Navigator>
  );
};

export default MainNavigator;