import ReactNativeBiometrics, {BiometryTypes} from 'react-native-biometrics';
import {Platform, Alert} from 'react-native';
import {BiometricAuthResult, BiometricType} from '@types/auth';
import {BiometricConfig} from '@types/common';
import {BIOMETRIC_CONFIG} from '@constants/config';
import {HapticService} from './HapticService';

class BiometricServiceClass {
  private rnBiometrics: ReactNativeBiometrics;

  constructor() {
    this.rnBiometrics = new ReactNativeBiometrics({
      allowDeviceCredentials: true,
    });
  }

  /**
   * Initialize biometric service and check availability
   */
  async initialize(): Promise<void> {
    try {
      const {available, biometryType} = await this.rnBiometrics.isSensorAvailable();
      console.log('Biometric sensor available:', available);
      console.log('Biometry type:', biometryType);
    } catch (error) {
      console.warn('Error initializing biometric service:', error);
    }
  }

  /**
   * Check if biometric authentication is available
   */
  async isAvailable(): Promise<{available: boolean; biometryType?: BiometricType}> {
    try {
      const {available, biometryType} = await this.rnBiometrics.isSensorAvailable();
      
      let mappedType: BiometricType = null;
      
      if (available && biometryType) {
        switch (biometryType) {
          case BiometryTypes.TouchID:
            mappedType = 'TouchID';
            break;
          case BiometryTypes.FaceID:
            mappedType = 'FaceID';
            break;
          case BiometryTypes.Biometrics:
            mappedType = 'Biometrics';
            break;
          default:
            mappedType = null;
        }
      }

      return {
        available,
        biometryType: mappedType,
      };
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      return {available: false};
    }
  }

  /**
   * Authenticate user with biometric
   */
  async authenticate(config?: Partial<BiometricConfig>): Promise<BiometricAuthResult> {
    try {
      const biometricConfig = {
        ...BIOMETRIC_CONFIG,
        ...config,
      };

      const {success, error} = await this.rnBiometrics.simplePrompt({
        promptMessage: biometricConfig.title,
        fallbackPromptMessage: biometricConfig.fallbackTitle,
        cancelButtonText: biometricConfig.negativeText,
      });

      if (success) {
        await HapticService.success();
        return {success: true};
      } else {
        await HapticService.error();
        return {
          success: false,
          error: error || 'Biometric authentication failed',
        };
      }
    } catch (error: any) {
      console.error('Biometric authentication error:', error);
      await HapticService.error();
      
      return {
        success: false,
        error: error.message || 'Biometric authentication failed',
      };
    }
  }

  /**
   * Enable biometric authentication
   */
  async enableBiometric(): Promise<{enabled: boolean; type: string}> {
    try {
      const availability = await this.isAvailable();
      
      if (!availability.available) {
        throw new Error('Biometric authentication is not available on this device');
      }

      // Check if biometric is already enrolled
      const hasCredentials = await this.hasEnrolledCredentials();
      
      if (!hasCredentials) {
        this.showEnrollmentAlert();
        throw new Error('No biometric credentials enrolled. Please set up biometric authentication in device settings.');
      }

      // Test authentication to ensure it works
      const authResult = await this.authenticate({
        title: 'Enable Biometric Authentication',
        subtitle: 'Verify your identity to enable biometric login',
      });

      if (!authResult.success) {
        throw new Error(authResult.error || 'Failed to verify biometric authentication');
      }

      return {
        enabled: true,
        type: availability.biometryType || 'Unknown',
      };
    } catch (error: any) {
      console.error('Error enabling biometric:', error);
      throw error;
    }
  }

  /**
   * Disable biometric authentication
   */
  async disableBiometric(): Promise<void> {
    try {
      // In a real app, you might want to require authentication before disabling
      const authResult = await this.authenticate({
        title: 'Disable Biometric Authentication',
        subtitle: 'Verify your identity to disable biometric login',
      });

      if (!authResult.success) {
        throw new Error(authResult.error || 'Authentication required to disable biometric');
      }

      // Biometric is now disabled (handled by the calling code)
      await HapticService.success();
    } catch (error: any) {
      console.error('Error disabling biometric:', error);
      throw error;
    }
  }

  /**
   * Check if user has enrolled biometric credentials
   */
  private async hasEnrolledCredentials(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        // On iOS, we can check if biometry is enrolled
        const {available, biometryType} = await this.rnBiometrics.isSensorAvailable();
        return available && biometryType !== undefined;
      } else {
        // On Android, we assume if biometrics are available, they're enrolled
        // This is a limitation of the current API
        const {available} = await this.rnBiometrics.isSensorAvailable();
        return available;
      }
    } catch (error) {
      console.error('Error checking enrolled credentials:', error);
      return false;
    }
  }

  /**
   * Show alert to guide user to biometric enrollment
   */
  private showEnrollmentAlert(): void {
    const biometricName = Platform.OS === 'ios' ? 'Touch ID/Face ID' : 'Fingerprint/Face Unlock';
    
    Alert.alert(
      'Biometric Authentication Not Set Up',
      `Please set up ${biometricName} in your device settings to use this feature.`,
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Settings',
          onPress: () => {
            // In a real app, you could open device settings
            // Linking.openSettings();
          },
        },
      ]
    );
  }

  /**
   * Get user-friendly biometric type name
   */
  getBiometricTypeName(type: BiometricType): string {
    switch (type) {
      case 'TouchID':
        return 'Touch ID';
      case 'FaceID':
        return 'Face ID';
      case 'Biometrics':
        return Platform.OS === 'ios' ? 'Biometrics' : 'Fingerprint';
      default:
        return 'Biometric Authentication';
    }
  }

  /**
   * Check if biometric authentication is more secure than device passcode
   */
  async isSecureEnrollment(): Promise<boolean> {
    try {
      // This would check if biometric is set up with secure enrollment
      // For now, we assume it's secure if available
      const {available} = await this.isAvailable();
      return available;
    } catch (error) {
      console.error('Error checking secure enrollment:', error);
      return false;
    }
  }
}

export const BiometricService = new BiometricServiceClass();