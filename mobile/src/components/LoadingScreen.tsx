import React from 'react';
import {View, ActivityIndicator, Text, StyleSheet} from 'react-native';
import {colors, fonts, spacing, commonStyles} from '@constants/theme';

interface LoadingScreenProps {
  message?: string;
  size?: 'small' | 'large';
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = 'Loading...',
  size = 'large',
}) => {
  return (
    <View style={styles.container}>
      <ActivityIndicator 
        size={size} 
        color={colors.primary}
        style={styles.spinner}
      />
      {message && (
        <Text style={styles.message}>{message}</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...commonStyles.centerContainer,
    backgroundColor: colors.background,
  },
  spinner: {
    marginBottom: spacing.md,
  },
  message: {
    fontFamily: fonts.regular,
    fontSize: 16,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});

export default LoadingScreen;