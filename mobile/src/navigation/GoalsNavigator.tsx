import React from 'react';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import GoalsHomeScreen from '@screens/goals/GoalsHomeScreen';
import CreateGoalScreen from '@screens/goals/CreateGoalScreen';
import GoalDetailScreen from '@screens/goals/GoalDetailScreen';
import EditGoalScreen from '@screens/goals/EditGoalScreen';

export type GoalsStackParamList = {
  GoalsHome: undefined;
  CreateGoal: undefined;
  GoalDetail: {goalId: string};
  EditGoal: {goalId: string};
};

const Stack = createNativeStackNavigator<GoalsStackParamList>();

const GoalsNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: true,
        headerBackTitleVisible: false,
      }}>
      <Stack.Screen
        name="GoalsHome"
        component={GoalsHomeScreen}
        options={{title: 'Financial Goals'}}
      />
      <Stack.Screen
        name="CreateGoal"
        component={CreateGoalScreen}
        options={{title: 'Create Goal'}}
      />
      <Stack.Screen
        name="GoalDetail"
        component={GoalDetailScreen}
        options={{title: 'Goal Details'}}
      />
      <Stack.Screen
        name="EditGoal"
        component={EditGoalScreen}
        options={{title: 'Edit Goal'}}
      />
    </Stack.Navigator>
  );
};

export default GoalsNavigator;