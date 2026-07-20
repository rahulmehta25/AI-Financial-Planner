import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  Switch,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';

const SettingsScreen: React.FC = () => {
  const { colors, toggleTheme, isDark } = useTheme();
  const { user, logout, enableBiometric, checkBiometricSupport } = useAuth();
  
  const [biometricEnabled, setBiometricEnabled] = useState(user?.biometricEnabled || false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [budgetAlerts, setBudgetAlerts] = useState(true);
  const [marketUpdates, setMarketUpdates] = useState(true);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();
  }, []);

  const handleBiometricToggle = async () => {
    if (!biometricEnabled) {
      const supported = await checkBiometricSupport();
      if (!supported) {
        Alert.alert(
          'Biometric Not Available',
          'Biometric authentication is not available on this device.'
        );
        return;
      }
      
      const enabled = await enableBiometric();
      if (enabled) {
        setBiometricEnabled(true);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } else {
      setBiometricEnabled(false);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: () => {
            logout();
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          },
        },
      ]
    );
  };

  const settingSections = [
    {
      title: 'Account',
      items: [
        {
          icon: 'person-outline',
          title: 'Profile',
          subtitle: 'Edit your personal information',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
        {
          icon: 'shield-checkmark-outline',
          title: 'Security',
          subtitle: 'Password, 2FA, and security settings',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
        {
          icon: 'card-outline',
          title: 'Payment Methods',
          subtitle: 'Manage linked accounts and cards',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
      ],
    },
    {
      title: 'Preferences',
      items: [
        {
          icon: 'moon-outline',
          title: 'Dark Mode',
          subtitle: 'Toggle dark/light theme',
          onPress: () => {
            toggleTheme();
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          },
          showSwitch: true,
          switchValue: isDark,
        },
        {
          icon: 'finger-print-outline',
          title: 'Biometric Login',
          subtitle: 'Use Face ID or Touch ID to login',
          onPress: handleBiometricToggle,
          showSwitch: true,
          switchValue: biometricEnabled,
        },
        {
          icon: 'notifications-outline',
          title: 'Push Notifications',
          subtitle: 'Receive app notifications',
          onPress: () => {
            setNotificationsEnabled(!notificationsEnabled);
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          },
          showSwitch: true,
          switchValue: notificationsEnabled,
        },
      ],
    },
    {
      title: 'Alerts & Notifications',
      items: [
        {
          icon: 'trending-up-outline',
          title: 'Market Updates',
          subtitle: 'Get notified about market changes',
          onPress: () => {
            setMarketUpdates(!marketUpdates);
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          },
          showSwitch: true,
          switchValue: marketUpdates,
        },
        {
          icon: 'wallet-outline',
          title: 'Budget Alerts',
          subtitle: 'Notifications when approaching limits',
          onPress: () => {
            setBudgetAlerts(!budgetAlerts);
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          },
          showSwitch: true,
          switchValue: budgetAlerts,
        },
      ],
    },
    {
      title: 'Data & Privacy',
      items: [
        {
          icon: 'download-outline',
          title: 'Export Data',
          subtitle: 'Download your financial data',
          onPress: () => {
            Alert.alert(
              'Export Data',
              'Your data export will be ready shortly. You will receive an email with the download link.',
              [{ text: 'OK' }]
            );
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          },
          showArrow: true,
        },
        {
          icon: 'shield-outline',
          title: 'Privacy Policy',
          subtitle: 'Read our privacy policy',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
        {
          icon: 'document-text-outline',
          title: 'Terms of Service',
          subtitle: 'Review terms and conditions',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
      ],
    },
    {
      title: 'Support',
      items: [
        {
          icon: 'help-circle-outline',
          title: 'Help Center',
          subtitle: 'FAQs and support articles',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
        {
          icon: 'mail-outline',
          title: 'Contact Support',
          subtitle: 'Get help from our team',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
        {
          icon: 'star-outline',
          title: 'Rate App',
          subtitle: 'Rate us on the app store',
          onPress: () => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light),
          showArrow: true,
        },
      ],
    },
  ];

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <View>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            Settings
          </Text>
          <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
            Manage your account and preferences
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[{ opacity: fadeAnim }, styles.content]}>
          {/* User Profile Card */}
          <View style={[styles.profileCard, { backgroundColor: colors.surface }]}>
            <View style={[styles.avatarContainer, { backgroundColor: colors.primary[100] }]}>
              <Text style={[styles.avatar, { color: colors.primary[600] }]}>
                {user?.name?.charAt(0) || 'U'}
              </Text>
            </View>
            <View style={styles.profileInfo}>
              <Text style={[styles.userName, { color: colors.text }]}>
                {user?.name || 'Demo User'}
              </Text>
              <Text style={[styles.userEmail, { color: colors.textSecondary }]}>
                {user?.email || 'demo@example.com'}
              </Text>
            </View>
            <TouchableOpacity
              style={styles.editButton}
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
            >
              <Ionicons name="create-outline" size={20} color={colors.primary[500]} />
            </TouchableOpacity>
          </View>

          {/* Settings Sections */}
          {settingSections.map((section, index) => (
            <View key={index} style={styles.section}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {section.title}
              </Text>
              <View style={[styles.sectionCard, { backgroundColor: colors.surface }]}>
                {section.items.map((item, itemIndex) => (
                  <TouchableOpacity
                    key={itemIndex}
                    style={[
                      styles.settingItem,
                      itemIndex < section.items.length - 1 && {
                        borderBottomWidth: 1,
                        borderBottomColor: colors.border,
                      },
                    ]}
                    onPress={item.onPress}
                  >
                    <View style={styles.settingLeft}>
                      <View style={[styles.settingIcon, { backgroundColor: colors.secondary[100] }]}>
                        <Ionicons
                          name={item.icon as keyof typeof Ionicons.glyphMap}
                          size={20}
                          color={colors.secondary[600]}
                        />
                      </View>
                      <View style={styles.settingInfo}>
                        <Text style={[styles.settingTitle, { color: colors.text }]}>
                          {item.title}
                        </Text>
                        <Text style={[styles.settingSubtitle, { color: colors.textSecondary }]}>
                          {item.subtitle}
                        </Text>
                      </View>
                    </View>
                    
                    <View style={styles.settingRight}>
                      {item.showSwitch && (
                        <Switch
                          value={item.switchValue}
                          onValueChange={item.onPress}
                          trackColor={{
                            false: colors.secondary[300],
                            true: colors.primary[500],
                          }}
                          thumbColor="white"
                        />
                      )}
                      {item.showArrow && (
                        <Ionicons
                          name="chevron-forward"
                          size={16}
                          color={colors.textSecondary}
                        />
                      )}
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          ))}

          {/* App Info */}
          <View style={styles.appInfo}>
            <Text style={[styles.appInfoText, { color: colors.textSecondary }]}>
              Financial Planner Demo v1.0.0
            </Text>
            <Text style={[styles.appInfoText, { color: colors.textSecondary }]}>
              Built with React Native & Expo
            </Text>
          </View>

          {/* Logout Button */}
          <TouchableOpacity
            style={[styles.logoutButton, { backgroundColor: colors.error[500] }]}
            onPress={handleLogout}
          >
            <Ionicons name="log-out-outline" size={20} color="white" />
            <Text style={styles.logoutButtonText}>Logout</Text>
          </TouchableOpacity>
        </Animated.View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  content: {
    padding: 20,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  avatarContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  avatar: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  profileInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
  },
  editButton: {
    padding: 8,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  sectionCard: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 20,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  settingInfo: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 14,
    lineHeight: 18,
  },
  settingRight: {
    marginLeft: 12,
  },
  appInfo: {
    alignItems: 'center',
    paddingVertical: 20,
    marginBottom: 20,
  },
  appInfoText: {
    fontSize: 12,
    marginBottom: 4,
  },
  logoutButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  logoutButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});

export default SettingsScreen;