import {Platform} from 'react-native';
import {PERMISSIONS, RESULTS, request, check, openSettings} from 'react-native-permissions';

// Platform-specific permission mapping
export const CAMERA_PERMISSION = Platform.select({
  ios: PERMISSIONS.IOS.CAMERA,
  android: PERMISSIONS.ANDROID.CAMERA,
});

export const NOTIFICATION_PERMISSION = Platform.select({
  ios: PERMISSIONS.IOS.NOTIFICATIONS,
  android: PERMISSIONS.ANDROID.POST_NOTIFICATIONS,
});

export const PHOTO_LIBRARY_PERMISSION = Platform.select({
  ios: PERMISSIONS.IOS.PHOTO_LIBRARY,
  android: PERMISSIONS.ANDROID.READ_EXTERNAL_STORAGE,
});

export const WRITE_STORAGE_PERMISSION = Platform.select({
  ios: null, // Not needed on iOS
  android: PERMISSIONS.ANDROID.WRITE_EXTERNAL_STORAGE,
});

export const FACE_ID_PERMISSION = Platform.select({
  ios: PERMISSIONS.IOS.FACE_ID,
  android: null, // Not needed on Android
});

// Permission status types
export type PermissionStatus = 'granted' | 'denied' | 'blocked' | 'unavailable';

// Permission request results
export const PermissionResults = {
  GRANTED: RESULTS.GRANTED,
  DENIED: RESULTS.DENIED,
  BLOCKED: RESULTS.BLOCKED,
  UNAVAILABLE: RESULTS.UNAVAILABLE,
  LIMITED: RESULTS.LIMITED,
};

/**
 * Check if a permission is granted
 */
export const checkPermission = async (permission: any): Promise<PermissionStatus> => {
  if (!permission) {
    return 'unavailable';
  }

  try {
    const result = await check(permission);
    
    switch (result) {
      case RESULTS.GRANTED:
        return 'granted';
      case RESULTS.DENIED:
        return 'denied';
      case RESULTS.BLOCKED:
        return 'blocked';
      case RESULTS.UNAVAILABLE:
        return 'unavailable';
      default:
        return 'denied';
    }
  } catch (error) {
    console.error('Error checking permission:', error);
    return 'denied';
  }
};

/**
 * Request a permission
 */
export const requestPermission = async (permission: any): Promise<PermissionStatus> => {
  if (!permission) {
    return 'unavailable';
  }

  try {
    const result = await request(permission);
    
    switch (result) {
      case RESULTS.GRANTED:
        return 'granted';
      case RESULTS.DENIED:
        return 'denied';
      case RESULTS.BLOCKED:
        return 'blocked';
      case RESULTS.UNAVAILABLE:
        return 'unavailable';
      default:
        return 'denied';
    }
  } catch (error) {
    console.error('Error requesting permission:', error);
    return 'denied';
  }
};

/**
 * Check camera permission
 */
export const checkCameraPermission = (): Promise<PermissionStatus> => {
  return checkPermission(CAMERA_PERMISSION);
};

/**
 * Request camera permission
 */
export const requestCameraPermission = (): Promise<PermissionStatus> => {
  return requestPermission(CAMERA_PERMISSION);
};

/**
 * Check notification permission
 */
export const checkNotificationPermission = (): Promise<PermissionStatus> => {
  return checkPermission(NOTIFICATION_PERMISSION);
};

/**
 * Request notification permission
 */
export const requestNotificationPermission = (): Promise<PermissionStatus> => {
  return requestPermission(NOTIFICATION_PERMISSION);
};

/**
 * Check photo library permission
 */
export const checkPhotoLibraryPermission = (): Promise<PermissionStatus> => {
  return checkPermission(PHOTO_LIBRARY_PERMISSION);
};

/**
 * Request photo library permission
 */
export const requestPhotoLibraryPermission = (): Promise<PermissionStatus> => {
  return requestPermission(PHOTO_LIBRARY_PERMISSION);
};

/**
 * Check Face ID permission (iOS only)
 */
export const checkFaceIDPermission = (): Promise<PermissionStatus> => {
  if (Platform.OS !== 'ios') {
    return Promise.resolve('unavailable');
  }
  return checkPermission(FACE_ID_PERMISSION);
};

/**
 * Request Face ID permission (iOS only)
 */
export const requestFaceIDPermission = (): Promise<PermissionStatus> => {
  if (Platform.OS !== 'ios') {
    return Promise.resolve('unavailable');
  }
  return requestPermission(FACE_ID_PERMISSION);
};

/**
 * Open device settings
 */
export const openDeviceSettings = (): Promise<void> => {
  return openSettings();
};

/**
 * Permission descriptions for user-friendly messages
 */
export const PERMISSION_DESCRIPTIONS = {
  camera: {
    title: 'Camera Access',
    description: 'Allow Financial Planner to access your camera to scan documents and receipts.',
    rationale: 'Camera access is needed to scan financial documents for easier data entry.',
  },
  notifications: {
    title: 'Notifications',
    description: 'Allow Financial Planner to send you notifications about goal reminders and updates.',
    rationale: 'Notifications help you stay on track with your financial goals.',
  },
  photoLibrary: {
    title: 'Photo Library Access',
    description: 'Allow Financial Planner to access your photo library to import financial documents.',
    rationale: 'Photo library access lets you import existing document photos.',
  },
  faceID: {
    title: 'Face ID',
    description: 'Allow Financial Planner to use Face ID for secure authentication.',
    rationale: 'Face ID provides secure and convenient access to your financial data.',
  },
};

/**
 * Check multiple permissions at once
 */
export const checkMultiplePermissions = async (
  permissions: any[]
): Promise<Record<string, PermissionStatus>> => {
  const results: Record<string, PermissionStatus> = {};
  
  for (const permission of permissions) {
    if (permission) {
      results[permission] = await checkPermission(permission);
    }
  }
  
  return results;
};

/**
 * Request multiple permissions at once
 */
export const requestMultiplePermissions = async (
  permissions: any[]
): Promise<Record<string, PermissionStatus>> => {
  const results: Record<string, PermissionStatus> = {};
  
  for (const permission of permissions) {
    if (permission) {
      results[permission] = await requestPermission(permission);
    }
  }
  
  return results;
};

/**
 * Check if all required permissions are granted
 */
export const checkAllRequiredPermissions = async (): Promise<{
  allGranted: boolean;
  permissions: Record<string, PermissionStatus>;
}> => {
  const requiredPermissions = [
    CAMERA_PERMISSION,
    NOTIFICATION_PERMISSION,
  ].filter(Boolean);
  
  const permissions = await checkMultiplePermissions(requiredPermissions);
  const allGranted = Object.values(permissions).every(status => status === 'granted');
  
  return {allGranted, permissions};
};

/**
 * Request all required permissions
 */
export const requestAllRequiredPermissions = async (): Promise<{
  allGranted: boolean;
  permissions: Record<string, PermissionStatus>;
}> => {
  const requiredPermissions = [
    CAMERA_PERMISSION,
    NOTIFICATION_PERMISSION,
  ].filter(Boolean);
  
  const permissions = await requestMultiplePermissions(requiredPermissions);
  const allGranted = Object.values(permissions).every(status => status === 'granted');
  
  return {allGranted, permissions};
};

export default {
  CAMERA_PERMISSION,
  NOTIFICATION_PERMISSION,
  PHOTO_LIBRARY_PERMISSION,
  WRITE_STORAGE_PERMISSION,
  FACE_ID_PERMISSION,
  PermissionResults,
  checkPermission,
  requestPermission,
  checkCameraPermission,
  requestCameraPermission,
  checkNotificationPermission,
  requestNotificationPermission,
  checkPhotoLibraryPermission,
  requestPhotoLibraryPermission,
  checkFaceIDPermission,
  requestFaceIDPermission,
  openDeviceSettings,
  PERMISSION_DESCRIPTIONS,
  checkMultiplePermissions,
  requestMultiplePermissions,
  checkAllRequiredPermissions,
  requestAllRequiredPermissions,
};