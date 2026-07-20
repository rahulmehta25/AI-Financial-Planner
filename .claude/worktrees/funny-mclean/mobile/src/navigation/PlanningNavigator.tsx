import React from 'react';
import {createNativeStackNavigator} from '@react-navigation/native-stack';

import PlanningHomeScreen from '@screens/planning/PlanningHomeScreen';
import FormWizardScreen from '@screens/planning/FormWizardScreen';
import DocumentScannerScreen from '@screens/planning/DocumentScannerScreen';
import DataReviewScreen from '@screens/planning/DataReviewScreen';

export type PlanningStackParamList = {
  PlanningHome: undefined;
  FormWizard: {step?: number};
  DocumentScanner: {documentType: string};
  DataReview: undefined;
};

const Stack = createNativeStackNavigator<PlanningStackParamList>();

const PlanningNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: true,
        headerBackTitleVisible: false,
      }}>
      <Stack.Screen
        name="PlanningHome"
        component={PlanningHomeScreen}
        options={{title: 'Financial Planning'}}
      />
      <Stack.Screen
        name="FormWizard"
        component={FormWizardScreen}
        options={{title: 'Planning Wizard'}}
      />
      <Stack.Screen
        name="DocumentScanner"
        component={DocumentScannerScreen}
        options={{title: 'Document Scanner'}}
      />
      <Stack.Screen
        name="DataReview"
        component={DataReviewScreen}
        options={{title: 'Review Your Data'}}
      />
    </Stack.Navigator>
  );
};

export default PlanningNavigator;