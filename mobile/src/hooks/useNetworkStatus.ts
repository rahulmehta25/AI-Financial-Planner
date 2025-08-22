import {useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import NetInfo from '@react-native-community/netinfo';
import {RootState} from '@store/store';
import {setNetworkStatus} from '@store/slices/uiSlice';

export const useNetworkStatus = () => {
  const dispatch = useDispatch();
  const networkStatus = useSelector((state: RootState) => state.ui.networkStatus);

  useEffect(() => {
    // Subscribe to network state updates
    const unsubscribe = NetInfo.addEventListener((state) => {
      dispatch(setNetworkStatus({
        isConnected: state.isConnected ?? false,
        connectionType: state.type as any,
        isInternetReachable: state.isInternetReachable ?? false,
      }));
    });

    return unsubscribe;
  }, [dispatch]);

  return networkStatus;
};