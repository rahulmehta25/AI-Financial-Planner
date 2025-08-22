import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  ScrollView,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface OnboardingStep {
  id: number;
  title: string;
  description: string;
  icon: keyof typeof Ionicons.glyphMap;
  gradient: string[];
}

const onboardingSteps: OnboardingStep[] = [
  {
    id: 1,
    title: 'Track Your Goals',
    description: 'Set financial goals and track your progress with beautiful visualizations and smart insights.',
    icon: 'flag-outline',
    gradient: ['#667eea', '#764ba2'],
  },
  {
    id: 2,
    title: 'Manage Portfolio',
    description: 'Monitor your investments with real-time data, advanced charts, and performance analytics.',
    icon: 'pie-chart-outline',
    gradient: ['#f093fb', '#f5576c'],
  },
  {
    id: 3,
    title: 'Smart Notifications',
    description: 'Get personalized alerts about your financial progress, market changes, and goal milestones.',
    icon: 'notifications-outline',
    gradient: ['#4facfe', '#00f2fe'],
  },
  {
    id: 4,
    title: 'Secure Access',
    description: 'Protect your financial data with biometric authentication and bank-level security.',
    icon: 'shield-checkmark-outline',
    gradient: ['#43e97b', '#38f9d7'],
  },
];

const OnboardingScreen: React.FC = () => {
  const { colors, spacing } = useTheme();
  const { completeOnboarding } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;

  const handleNext = () => {
    if (currentStep < onboardingSteps.length - 1) {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: -50,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start(() => {
        const nextStep = currentStep + 1;
        setCurrentStep(nextStep);
        scrollViewRef.current?.scrollTo({
          x: nextStep * screenWidth,
          animated: true,
        });
        
        slideAnim.setValue(50);
        Animated.parallel([
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 300,
            useNativeDriver: true,
          }),
          Animated.timing(slideAnim, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
          }),
        ]).start();
      });
    } else {
      completeOnboarding();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 50,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start(() => {
        const prevStep = currentStep - 1;
        setCurrentStep(prevStep);
        scrollViewRef.current?.scrollTo({
          x: prevStep * screenWidth,
          animated: true,
        });
        
        slideAnim.setValue(-50);
        Animated.parallel([
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 300,
            useNativeDriver: true,
          }),
          Animated.timing(slideAnim, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
          }),
        ]).start();
      });
    }
  };

  const handleSkip = () => {
    completeOnboarding();
  };

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollViewRef}
        horizontal
        pagingEnabled
        scrollEnabled={false}
        showsHorizontalScrollIndicator={false}
        style={styles.scrollView}
      >
        {onboardingSteps.map((step, index) => (
          <LinearGradient
            key={step.id}
            colors={step.gradient}
            style={styles.stepContainer}
          >
            <View style={styles.header}>
              <TouchableOpacity
                style={styles.skipButton}
                onPress={handleSkip}
              >
                <Text style={styles.skipText}>Skip</Text>
              </TouchableOpacity>
            </View>

            <Animated.View
              style={[
                styles.content,
                {
                  opacity: currentStep === index ? fadeAnim : 0.3,
                  transform: [
                    {
                      translateY: currentStep === index ? slideAnim : 0,
                    },
                  ],
                },
              ]}
            >
              <View style={styles.iconContainer}>
                <Ionicons
                  name={step.icon}
                  size={80}
                  color="white"
                />
              </View>

              <Text style={styles.title}>{step.title}</Text>
              <Text style={styles.description}>{step.description}</Text>
            </Animated.View>

            <View style={styles.footer}>
              <View style={styles.pagination}>
                {onboardingSteps.map((_, dotIndex) => (
                  <View
                    key={dotIndex}
                    style={[
                      styles.dot,
                      {
                        backgroundColor:
                          dotIndex === currentStep
                            ? 'white'
                            : 'rgba(255, 255, 255, 0.3)',
                        width: dotIndex === currentStep ? 24 : 8,
                      },
                    ]}
                  />
                ))}
              </View>

              <View style={styles.navigationButtons}>
                {currentStep > 0 && (
                  <TouchableOpacity
                    style={[styles.button, styles.previousButton]}
                    onPress={handlePrevious}
                  >
                    <Ionicons name="arrow-back" size={20} color="white" />
                    <Text style={styles.buttonText}>Previous</Text>
                  </TouchableOpacity>
                )}

                <TouchableOpacity
                  style={[
                    styles.button,
                    styles.nextButton,
                    currentStep === 0 && styles.singleButton,
                  ]}
                  onPress={handleNext}
                >
                  <Text style={styles.buttonText}>
                    {currentStep === onboardingSteps.length - 1
                      ? 'Get Started'
                      : 'Next'}
                  </Text>
                  <Ionicons name="arrow-forward" size={20} color="white" />
                </TouchableOpacity>
              </View>
            </View>
          </LinearGradient>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  stepContainer: {
    width: screenWidth,
    height: screenHeight,
    justifyContent: 'space-between',
    paddingVertical: 60,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingHorizontal: 24,
  },
  skipButton: {
    padding: 12,
  },
  skipText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  iconContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 48,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
    marginBottom: 16,
  },
  description: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 26,
    paddingHorizontal: 16,
  },
  footer: {
    paddingHorizontal: 24,
  },
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 32,
  },
  dot: {
    height: 8,
    borderRadius: 4,
    marginHorizontal: 4,
  },
  navigationButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    minWidth: 120,
    justifyContent: 'center',
  },
  previousButton: {
    marginRight: 16,
  },
  nextButton: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  singleButton: {
    marginLeft: 0,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginHorizontal: 8,
  },
});

export default OnboardingScreen;