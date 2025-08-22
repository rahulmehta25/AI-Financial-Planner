import React from 'react';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import DashboardScreen from '@screens/dashboard/DashboardScreen';
import PortfolioDetailScreen from '@screens/dashboard/PortfolioDetailScreen';
import SimulationResultsScreen from '@screens/dashboard/SimulationResultsScreen';

export type DashboardStackParamList = {
  DashboardHome: undefined;
  PortfolioDetail: {portfolioId: string};
  SimulationResults: {simulationId: string};
};

const Stack = createNativeStackNavigator<DashboardStackParamList>();

const DashboardNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: true,
        headerBackTitleVisible: false,
      }}>
      <Stack.Screen
        name="DashboardHome"
        component={DashboardScreen}
        options={{title: 'Dashboard'}}
      />
      <Stack.Screen
        name="PortfolioDetail"
        component={PortfolioDetailScreen}
        options={{title: 'Portfolio Details'}}
      />
      <Stack.Screen
        name="SimulationResults"
        component={SimulationResultsScreen}
        options={{title: 'Simulation Results'}}
      />
    </Stack.Navigator>
  );
};

export default DashboardNavigator;