import {useEffect, useRef} from 'react';
import {AppState, AppStateStatus} from 'react-native';
import {useDispatch, useSelector} from 'react-redux';
import {RootState} from '@store/store';
import {setAppState} from '@store/slices/uiSlice';
import {SECURITY_CONFIG} from '@constants/config';

export const useAppStateHandler = () => {
  const dispatch = useDispatch();
  const appState = useRef(AppState.currentState);
  const {isAuthenticated, biometricEnabled} = useSelector((state: RootState) => state.auth);
  const lastActiveTime = useRef(Date.now());

  useEffect(() => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      const currentTime = Date.now();

      if (appState.current.match(/inactive|background/) && nextAppState === 'active') {
        // App has come to the foreground
        const timeInBackground = currentTime - lastActiveTime.current;

        // Check if auto-lock should be triggered
        if (
          isAuthenticated &&
          biometricEnabled &&
          timeInBackground > SECURITY_CONFIG.AUTO_LOCK_TIMEOUT
        ) {
          // Trigger biometric authentication
          dispatch({type: 'auth/requireBiometricAuth'});
        }

        dispatch(setAppState({
          appState: nextAppState,
          lastActiveTime: currentTime,
          sessionStartTime: currentTime,
        }));
      } else if (nextAppState === 'background' || nextAppState === 'inactive') {
        // App is going to background
        lastActiveTime.current = currentTime;
        
        dispatch(setAppState({
          appState: nextAppState,
          lastActiveTime: currentTime,
          sessionStartTime: lastActiveTime.current,
        }));
      }

      appState.current = nextAppState;
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);

    return () => {
      subscription?.remove();
    };
  }, [dispatch, isAuthenticated, biometricEnabled]);

  return appState.current;
};