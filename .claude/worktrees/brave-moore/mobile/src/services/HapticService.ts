import ReactNativeHapticFeedback from 'react-native-haptic-feedback';
import {Platform} from 'react-native';
import {HapticFeedbackType} from '@types/common';

class HapticServiceClass {
  private isEnabled: boolean = true;

  /**
   * Initialize haptic feedback service
   */
  initialize(): void {
    // Check if device supports haptic feedback
    if (Platform.OS === 'ios') {
      this.isEnabled = true;
    } else {
      // On Android, haptic feedback availability varies
      this.isEnabled = true;
    }
  }

  /**
   * Enable or disable haptic feedback
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * Check if haptic feedback is enabled
   */
  getEnabled(): boolean {
    return this.isEnabled;
  }

  /**
   * Trigger haptic feedback
   */
  private trigger(type: string, options?: any): void {
    if (!this.isEnabled) {
      return;
    }

    try {
      ReactNativeHapticFeedback.trigger(type, {
        enableVibrateFallback: true,
        ignoreAndroidSystemSettings: false,
        ...options,
      });
    } catch (error) {
      console.warn('Haptic feedback error:', error);
    }
  }

  /**
   * Light impact feedback
   * Use for small UI interactions like button taps
   */
  light(): void {
    this.trigger('impactLight');
  }

  /**
   * Medium impact feedback
   * Use for medium UI interactions like switch toggles
   */
  medium(): void {
    this.trigger('impactMedium');
  }

  /**
   * Heavy impact feedback
   * Use for important interactions like form submissions
   */
  heavy(): void {
    this.trigger('impactHeavy');
  }

  /**
   * Selection feedback
   * Use for picker selections or menu navigation
   */
  selection(): void {
    this.trigger('selection');
  }

  /**
   * Success notification feedback
   * Use for successful operations
   */
  success(): void {
    this.trigger('notificationSuccess');
  }

  /**
   * Warning notification feedback
   * Use for warning states
   */
  warning(): void {
    this.trigger('notificationWarning');
  }

  /**
   * Error notification feedback
   * Use for error states
   */
  error(): void {
    this.trigger('notificationError');
  }

  /**
   * Rigid impact feedback (iOS 13+)
   * Use for precise or rigid interactions
   */
  rigid(): void {
    if (Platform.OS === 'ios') {
      this.trigger('rigid');
    } else {
      this.medium(); // Fallback for Android
    }
  }

  /**
   * Soft impact feedback (iOS 13+)
   * Use for soft or gentle interactions
   */
  soft(): void {
    if (Platform.OS === 'ios') {
      this.trigger('soft');
    } else {
      this.light(); // Fallback for Android
    }
  }

  /**
   * Custom haptic pattern
   */
  custom(pattern: HapticFeedbackType): void {
    switch (pattern.type) {
      case 'impact':
        switch (pattern.intensity) {
          case 'light':
            this.light();
            break;
          case 'medium':
            this.medium();
            break;
          case 'heavy':
            this.heavy();
            break;
          default:
            this.medium();
        }
        break;
      case 'notification':
        switch (pattern.intensity) {
          case 'light':
            this.success();
            break;
          case 'medium':
            this.warning();
            break;
          case 'heavy':
            this.error();
            break;
          default:
            this.warning();
        }
        break;
      case 'selection':
        this.selection();
        break;
      default:
        this.medium();
    }
  }

  /**
   * Haptic feedback for financial interactions
   */
  financial = {
    /**
     * Positive financial change (gains, profits)
     */
    positive: (): void => {
      this.success();
    },

    /**
     * Negative financial change (losses)
     */
    negative: (): void => {
      this.warning();
    },

    /**
     * Goal achievement
     */
    goalAchieved: (): void => {
      // Double success feedback for achievement
      this.success();
      setTimeout(() => this.success(), 100);
    },

    /**
     * Transaction completion
     */
    transaction: (): void => {
      this.medium();
    },

    /**
     * Data synchronization
     */
    sync: (): void => {
      this.light();
    },

    /**
     * Critical financial alert
     */
    alert: (): void => {
      this.error();
    },
  };

  /**
   * Haptic feedback for form interactions
   */
  form = {
    /**
     * Field validation success
     */
    validationSuccess: (): void => {
      this.light();
    },

    /**
     * Field validation error
     */
    validationError: (): void => {
      this.warning();
    },

    /**
     * Form submission
     */
    submit: (): void => {
      this.medium();
    },

    /**
     * Step completion in wizard
     */
    stepComplete: (): void => {
      this.success();
    },

    /**
     * Progress milestone
     */
    milestone: (): void => {
      this.heavy();
    },
  };

  /**
   * Haptic feedback for navigation
   */
  navigation = {
    /**
     * Tab switch
     */
    tabSwitch: (): void => {
      this.selection();
    },

    /**
     * Screen transition
     */
    transition: (): void => {
      this.light();
    },

    /**
     * Drawer open/close
     */
    drawer: (): void => {
      this.medium();
    },

    /**
     * Modal present/dismiss
     */
    modal: (): void => {
      this.light();
    },
  };

  /**
   * Haptic feedback for gestures
   */
  gesture = {
    /**
     * Pull to refresh
     */
    pullToRefresh: (): void => {
      this.medium();
    },

    /**
     * Swipe action
     */
    swipe: (): void => {
      this.light();
    },

    /**
     * Long press
     */
    longPress: (): void => {
      this.heavy();
    },

    /**
     * Pinch zoom
     */
    pinch: (): void => {
      this.selection();
    },
  };
}

export const HapticService = new HapticServiceClass();