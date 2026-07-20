import React, {useEffect} from 'react';
import {StatusBar, Platform} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {Provider} from 'react-redux';
import {PersistGate} from 'redux-persist/integration/react';
import SplashScreen from 'react-native-splash-screen';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import {SafeAreaProvider} from 'react-native-safe-area-context';

import {store, persistor} from '@store/store';
import AppNavigator from '@navigation/AppNavigator';
import LoadingScreen from '@components/LoadingScreen';
import {NotificationService} from '@services/NotificationService';
import {BiometricService} from '@services/BiometricService';
import {useNetworkStatus} from '@hooks/useNetworkStatus';
import {useAppStateHandler} from '@hooks/useAppStateHandler';

const App: React.FC = () => {
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Initialize services
        await NotificationService.initialize();
        await BiometricService.initialize();
        
        // Hide splash screen after initialization
        setTimeout(() => {
          SplashScreen.hide();
        }, 1000);
      } catch (error) {
        console.error('App initialization error:', error);
        SplashScreen.hide();
      }
    };

    initializeApp();
  }, []);

  return (
    <GestureHandlerRootView style={{flex: 1}}>
      <SafeAreaProvider>
        <Provider store={store}>
          <PersistGate loading={<LoadingScreen />} persistor={persistor}>
            <StatusBar
              barStyle={Platform.OS === 'ios' ? 'dark-content' : 'light-content'}
              backgroundColor="transparent"
              translucent
            />
            <NavigationContainer>
              <AppStateHandler />
              <NetworkStatusHandler />
              <AppNavigator />
            </NavigationContainer>
          </PersistGate>
        </Provider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
};

// Component to handle app state changes
const AppStateHandler: React.FC = () => {
  useAppStateHandler();
  return null;
};

// Component to handle network status changes
const NetworkStatusHandler: React.FC = () => {
  useNetworkStatus();
  return null;
};

export default App;