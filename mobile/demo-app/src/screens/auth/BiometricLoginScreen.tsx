import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const BiometricLoginScreen: React.FC = () => {
  const { colors } = useTheme();
  const { loginWithBiometric } = useAuth();
  const navigation = useNavigation();
  
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Fade in animation
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();

    // Pulse animation for fingerprint
    const pulse = () => {
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ]).start(pulse);
    };

    pulse();

    // Auto-trigger biometric authentication
    const timer = setTimeout(() => {
      handleBiometricLogin();
    }, 1500);

    return () => {
      clearTimeout(timer);
      pulseAnim.stopAnimation();
    };
  }, []);

  const handleBiometricLogin = async () => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      
      const success = await loginWithBiometric();
      
      if (success) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      } else {
        Alert.alert(
          'Authentication Failed',
          'Biometric authentication was not successful. Please try again or use password.',
          [
            { text: 'Use Password', onPress: () => navigation.navigate('Login' as never) },
            { text: 'Try Again', onPress: handleBiometricLogin },
          ]
        );
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      }
    } catch (error) {
      Alert.alert(
        'Error',
        'An error occurred during biometric authentication.',
        [
          { text: 'Use Password', onPress: () => navigation.navigate('Login' as never) },
        ]
      );
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  };

  const handleUsePassword = () => {
    navigation.navigate('Login' as never);
  };

  return (
    <LinearGradient
      colors={['#667eea', '#764ba2']}
      style={styles.container}
    >
      <Animated.View
        style={[
          styles.content,
          { opacity: fadeAnim },
        ]}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>

        <View style={styles.header}>
          <Text style={styles.title}>Biometric Login</Text>
          <Text style={styles.subtitle}>
            Use your fingerprint or face to access your account
          </Text>
        </View>

        <View style={styles.biometricContainer}>
          <Animated.View
            style={[
              styles.fingerprintContainer,
              {
                transform: [{ scale: pulseAnim }],
              },
            ]}
          >
            <View style={styles.fingerprintOuter}>
              <View style={styles.fingerprintInner}>
                <Ionicons name="finger-print" size={80} color="white" />
              </View>
            </View>
          </Animated.View>

          <Text style={styles.instructionText}>
            Touch the fingerprint sensor or look at your device
          </Text>

          <TouchableOpacity
            style={styles.authenticateButton}
            onPress={handleBiometricLogin}
          >
            <Text style={styles.authenticateButtonText}>
              Authenticate
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <TouchableOpacity
            style={styles.passwordButton}
            onPress={handleUsePassword}
          >
            <Ionicons name="key-outline" size={20} color="white" />
            <Text style={styles.passwordButtonText}>Use Password Instead</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.securityInfo}>
          <View style={styles.securityItem}>
            <Ionicons name="shield-checkmark" size={16} color="rgba(255,255,255,0.8)" />
            <Text style={styles.securityText}>Your biometric data is encrypted</Text>
          </View>
          <View style={styles.securityItem}>
            <Ionicons name="lock-closed" size={16} color="rgba(255,255,255,0.8)" />
            <Text style={styles.securityText}>Stored securely on your device</Text>
          </View>
        </View>
      </Animated.View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 32,
    paddingTop: 60,
    justifyContent: 'space-between',
  },
  backButton: {
    alignSelf: 'flex-start',
    padding: 8,
    marginBottom: 20,
  },
  header: {
    alignItems: 'center',
    marginTop: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  biometricContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  fingerprintContainer: {
    marginBottom: 48,
  },
  fingerprintOuter: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  fingerprintInner: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  instructionText: {
    fontSize: 18,
    color: 'white',
    textAlign: 'center',
    marginBottom: 32,
    paddingHorizontal: 20,
  },
  authenticateButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingVertical: 16,
    paddingHorizontal: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  authenticateButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  passwordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
  },
  passwordButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 8,
  },
  securityInfo: {
    marginBottom: 32,
  },
  securityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    justifyContent: 'center',
  },
  securityText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    marginLeft: 8,
  },
});

export default BiometricLoginScreen;