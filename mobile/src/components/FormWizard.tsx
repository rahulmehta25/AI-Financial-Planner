import React, {useState, useCallback} from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Platform,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  Extrapolate,
} from 'react-native-reanimated';
import Icon from 'react-native-vector-icons/Ionicons';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {colors, fonts, spacing, borderRadius, shadows} from '@constants/theme';
import {HapticService} from '@services/HapticService';
import {FormWizardStep} from '@types/financial';

interface FormWizardProps {
  steps: FormWizardStep[];
  currentStep: number;
  onStepChange: (step: number) => void;
  onNext: () => void;
  onPrevious: () => void;
  onComplete: () => void;
  isLoading?: boolean;
  canGoNext?: boolean;
  canGoPrevious?: boolean;
  showProgress?: boolean;
  children: React.ReactNode;
}

const {width: SCREEN_WIDTH} = Dimensions.get('window');

const FormWizard: React.FC<FormWizardProps> = ({
  steps,
  currentStep,
  onStepChange,
  onNext,
  onPrevious,
  onComplete,
  isLoading = false,
  canGoNext = true,
  canGoPrevious = true,
  showProgress = true,
  children,
}) => {
  const insets = useSafeAreaInsets();
  const progressValue = useSharedValue(0);

  // Update progress animation
  React.useEffect(() => {
    progressValue.value = withTiming((currentStep + 1) / steps.length, {
      duration: 300,
    });
  }, [currentStep, steps.length, progressValue]);

  const progressAnimatedStyle = useAnimatedStyle(() => {
    return {
      width: `${progressValue.value * 100}%`,
    };
  });

  const handleNext = useCallback(() => {
    if (canGoNext && !isLoading) {
      HapticService.form.stepComplete();
      if (currentStep === steps.length - 1) {
        onComplete();
      } else {
        onNext();
      }
    }
  }, [canGoNext, isLoading, currentStep, steps.length, onComplete, onNext]);

  const handlePrevious = useCallback(() => {
    if (canGoPrevious && !isLoading && currentStep > 0) {
      HapticService.navigation.transition();
      onPrevious();
    }
  }, [canGoPrevious, isLoading, currentStep, onPrevious]);

  const handleStepTap = useCallback((stepIndex: number) => {
    if (stepIndex < currentStep || steps[stepIndex].isCompleted) {
      HapticService.navigation.tabSwitch();
      onStepChange(stepIndex);
    }
  }, [currentStep, steps, onStepChange]);

  const renderStepIndicator = () => {
    return (
      <View style={styles.stepIndicatorContainer}>
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = step.isCompleted;
          const isAccessible = index <= currentStep || isCompleted;

          return (
            <TouchableOpacity
              key={step.id}
              style={[
                styles.stepIndicator,
                isActive && styles.stepIndicatorActive,
                isCompleted && styles.stepIndicatorCompleted,
              ]}
              onPress={() => handleStepTap(index)}
              disabled={!isAccessible}
              accessibilityLabel={`Step ${index + 1}: ${step.title}`}
              accessibilityRole="button"
              accessibilityState={{
                selected: isActive,
                disabled: !isAccessible,
              }}>
              {isCompleted ? (
                <Icon name="checkmark" size={16} color={colors.white} />
              ) : (
                <Text style={[
                  styles.stepNumber,
                  isActive && styles.stepNumberActive,
                ]}>
                  {index + 1}
                </Text>
              )}
            </TouchableOpacity>
          );
        })}
      </View>
    );
  };

  const renderProgressBar = () => {
    if (!showProgress) return null;

    return (
      <View style={styles.progressContainer}>
        <View style={styles.progressTrack}>
          <Animated.View 
            style={[styles.progressFill, progressAnimatedStyle]} 
          />
        </View>
        <Text style={styles.progressText}>
          Step {currentStep + 1} of {steps.length}
        </Text>
      </View>
    );
  };

  const renderHeader = () => {
    const currentStepData = steps[currentStep];
    
    return (
      <View style={styles.header}>
        <Text style={styles.stepTitle} numberOfLines={2}>
          {currentStepData.title}
        </Text>
        {currentStepData.subtitle && (
          <Text style={styles.stepSubtitle} numberOfLines={3}>
            {currentStepData.subtitle}
          </Text>
        )}
      </View>
    );
  };

  const renderFooter = () => {
    const isLastStep = currentStep === steps.length - 1;
    
    return (
      <View style={[styles.footer, {paddingBottom: insets.bottom}]}>
        <TouchableOpacity
          style={[
            styles.button,
            styles.secondaryButton,
            (!canGoPrevious || currentStep === 0) && styles.buttonDisabled,
          ]}
          onPress={handlePrevious}
          disabled={!canGoPrevious || currentStep === 0 || isLoading}
          accessibilityLabel="Previous step"
          accessibilityRole="button">
          <Icon 
            name="chevron-back" 
            size={20} 
            color={currentStep === 0 ? colors.grayLight : colors.primary} 
          />
          <Text style={[
            styles.buttonText,
            styles.secondaryButtonText,
            (!canGoPrevious || currentStep === 0) && styles.buttonTextDisabled,
          ]}>
            Previous
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.button,
            styles.primaryButton,
            !canGoNext && styles.buttonDisabled,
          ]}
          onPress={handleNext}
          disabled={!canGoNext || isLoading}
          accessibilityLabel={isLastStep ? 'Complete' : 'Next step'}
          accessibilityRole="button">
          <Text style={[
            styles.buttonText,
            styles.primaryButtonText,
            !canGoNext && styles.buttonTextDisabled,
          ]}>
            {isLastStep ? 'Complete' : 'Next'}
          </Text>
          {!isLastStep && (
            <Icon 
              name="chevron-forward" 
              size={20} 
              color={canGoNext ? colors.white : colors.grayLight} 
            />
          )}
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {renderStepIndicator()}
      {renderProgressBar()}
      {renderHeader()}
      
      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>

      {renderFooter()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  stepIndicatorContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  stepIndicator: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.grayLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: spacing.xs,
    borderWidth: 2,
    borderColor: colors.border,
  },
  stepIndicatorActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  stepIndicatorCompleted: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  stepNumber: {
    fontSize: 14,
    fontFamily: fonts.medium,
    color: colors.gray,
  },
  stepNumberActive: {
    color: colors.white,
  },
  progressContainer: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    backgroundColor: colors.white,
  },
  progressTrack: {
    height: 4,
    backgroundColor: colors.grayLight,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    fontFamily: fonts.regular,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.xs,
  },
  header: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  stepTitle: {
    fontSize: 24,
    fontFamily: fonts.bold,
    color: colors.text,
    marginBottom: spacing.xs,
  },
  stepSubtitle: {
    fontSize: 16,
    fontFamily: fonts.regular,
    color: colors.textSecondary,
    lineHeight: 22,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    ...Platform.select({
      ios: shadows.md,
      android: {elevation: 8},
    }),
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.md,
    minWidth: 100,
  },
  primaryButton: {
    backgroundColor: colors.primary,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.primary,
  },
  buttonDisabled: {
    backgroundColor: colors.grayLight,
    borderColor: colors.grayLight,
  },
  buttonText: {
    fontSize: 16,
    fontFamily: fonts.medium,
    marginHorizontal: spacing.xs,
  },
  primaryButtonText: {
    color: colors.white,
  },
  secondaryButtonText: {
    color: colors.primary,
  },
  buttonTextDisabled: {
    color: colors.gray,
  },
});

export default FormWizard;