import React, { useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRoute } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useData } from '../../contexts/DataContext';

const GoalDetailScreen: React.FC = () => {
  const { colors } = useTheme();
  const navigation = useNavigation();
  const route = useRoute();
  const { goals, updateGoal } = useData();
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;

  // Get goal from route params
  const goalId = (route.params as any)?.goalId;
  const goal = goals.find(g => g.id === goalId);

  React.useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(progressAnim, {
        toValue: goal ? (goal.currentAmount / goal.targetAmount) : 0,
        duration: 1200,
        useNativeDriver: false,
      }),
    ]).start();
  }, [goal]);

  if (!goal) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text>Goal not found</Text>
      </View>
    );
  }

  const progress = (goal.currentAmount / goal.targetAmount) * 100;
  const remaining = goal.targetAmount - goal.currentAmount;
  const daysRemaining = Math.max(0, Math.ceil((new Date(goal.targetDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)));

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: keyof typeof Ionicons.glyphMap } = {
      retirement: 'time-outline',
      emergency: 'shield-outline',
      travel: 'airplane-outline',
      home: 'home-outline',
      education: 'school-outline',
      other: 'ellipsis-horizontal-outline',
    };
    return icons[category] || 'flag-outline';
  };

  const getCategoryColor = (category: string) => {
    const colorMap: { [key: string]: string[] } = {
      retirement: colors.gradient.primary,
      emergency: ['#ef4444', '#dc2626'],
      travel: ['#f59e0b', '#d97706'],
      home: colors.gradient.success,
      education: ['#8b5cf6', '#7c3aed'],
      other: ['#64748b', '#475569'],
    };
    return colorMap[category] || colors.gradient.primary;
  };

  const handleAddFunds = () => {
    const addAmount = 500; // Demo amount
    const newAmount = Math.min(goal.currentAmount + addAmount, goal.targetAmount);
    updateGoal(goal.id, { currentAmount: newAmount });
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <LinearGradient
        colors={getCategoryColor(goal.category)}
        style={styles.header}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle}>{goal.title}</Text>
        
        <TouchableOpacity style={styles.menuButton}>
          <Ionicons name="ellipsis-horizontal" size={24} color="white" />
        </TouchableOpacity>
      </LinearGradient>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[{ opacity: fadeAnim }, styles.content]}>
          {/* Progress Card */}
          <View style={[styles.progressCard, { backgroundColor: colors.surface }]}>
            <View style={styles.progressHeader}>
              <View style={[styles.categoryIcon, { backgroundColor: `${getCategoryColor(goal.category)[0]}20` }]}>
                <Ionicons
                  name={getCategoryIcon(goal.category)}
                  size={32}
                  color={getCategoryColor(goal.category)[0]}
                />
              </View>
              <View style={styles.progressInfo}>
                <Text style={[styles.currentAmount, { color: colors.text }]}>
                  {formatCurrency(goal.currentAmount)}
                </Text>
                <Text style={[styles.targetAmount, { color: colors.textSecondary }]}>
                  of {formatCurrency(goal.targetAmount)}
                </Text>
              </View>
            </View>

            <View style={[styles.progressBarContainer, { backgroundColor: colors.secondary[200] }]}>
              <Animated.View
                style={[
                  styles.progressBar,
                  {
                    width: progressAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: ['0%', '100%'],
                    }),
                    backgroundColor: getCategoryColor(goal.category)[0],
                  },
                ]}
              />
            </View>

            <View style={styles.progressStats}>
              <Text style={[styles.progressPercentage, { color: getCategoryColor(goal.category)[0] }]}>
                {progress.toFixed(1)}% Complete
              </Text>
              <Text style={[styles.remainingAmount, { color: colors.textSecondary }]}>
                {formatCurrency(remaining)} remaining
              </Text>
            </View>
          </View>

          {/* Goal Details */}
          <View style={[styles.detailsCard, { backgroundColor: colors.surface }]}>
            <Text style={[styles.detailsTitle, { color: colors.text }]}>
              Goal Details
            </Text>
            
            <View style={styles.detailItem}>
              <Ionicons name="document-text-outline" size={20} color={colors.textSecondary} />
              <View style={styles.detailContent}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
                  Description
                </Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>
                  {goal.description}
                </Text>
              </View>
            </View>

            <View style={styles.detailItem}>
              <Ionicons name="calendar-outline" size={20} color={colors.textSecondary} />
              <View style={styles.detailContent}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
                  Target Date
                </Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>
                  {new Date(goal.targetDate).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </Text>
              </View>
            </View>

            <View style={styles.detailItem}>
              <Ionicons name="time-outline" size={20} color={colors.textSecondary} />
              <View style={styles.detailContent}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
                  Days Remaining
                </Text>
                <Text style={[styles.detailValue, { color: colors.text }]}>
                  {daysRemaining} days
                </Text>
              </View>
            </View>

            <View style={styles.detailItem}>
              <Ionicons name="flag-outline" size={20} color={colors.textSecondary} />
              <View style={styles.detailContent}>
                <Text style={[styles.detailLabel, { color: colors.textSecondary }]}>
                  Priority
                </Text>
                <Text style={[
                  styles.detailValue, 
                  { 
                    color: goal.priority === 'high' 
                      ? colors.error[500] 
                      : goal.priority === 'medium' 
                        ? colors.warning[500] 
                        : colors.success[500] 
                  }
                ]}>
                  {goal.priority.toUpperCase()}
                </Text>
              </View>
            </View>
          </View>

          {/* Monthly Savings Suggestion */}
          <View style={[styles.suggestionCard, { backgroundColor: colors.surface }]}>
            <Text style={[styles.suggestionTitle, { color: colors.text }]}>
              Monthly Savings Needed
            </Text>
            <Text style={[styles.suggestionSubtitle, { color: colors.textSecondary }]}>
              To reach your goal on time
            </Text>
            
            <View style={styles.suggestionAmount}>
              <Text style={[styles.suggestionValue, { color: colors.primary[600] }]}>
                {formatCurrency(remaining / Math.max(1, daysRemaining / 30))}
              </Text>
              <Text style={[styles.suggestionLabel, { color: colors.textSecondary }]}>
                per month
              </Text>
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.primary[500] }]}
              onPress={handleAddFunds}
            >
              <Ionicons name="add-circle" size={20} color="white" />
              <Text style={styles.actionButtonText}>Add $500</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.success[500] }]}
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
            >
              <Ionicons name="card" size={20} color="white" />
              <Text style={styles.actionButtonText}>Auto-Save</Text>
            </TouchableOpacity>
          </View>

          {/* Milestone Timeline */}
          <View style={[styles.timelineCard, { backgroundColor: colors.surface }]}>
            <Text style={[styles.timelineTitle, { color: colors.text }]}>
              Progress Milestones
            </Text>
            
            <View style={styles.timeline}>
              <View style={styles.timelineItem}>
                <View style={[styles.timelineDot, { backgroundColor: colors.success[500] }]} />
                <View style={styles.timelineContent}>
                  <Text style={[styles.timelineItemTitle, { color: colors.text }]}>
                    25% Complete
                  </Text>
                  <Text style={[styles.timelineItemDate, { color: colors.textSecondary }]}>
                    Completed 2 months ago
                  </Text>
                </View>
              </View>

              <View style={styles.timelineItem}>
                <View style={[styles.timelineDot, { backgroundColor: colors.success[500] }]} />
                <View style={styles.timelineContent}>
                  <Text style={[styles.timelineItemTitle, { color: colors.text }]}>
                    50% Complete
                  </Text>
                  <Text style={[styles.timelineItemDate, { color: colors.textSecondary }]}>
                    Completed 1 month ago
                  </Text>
                </View>
              </View>

              <View style={styles.timelineItem}>
                <View style={[styles.timelineDot, { backgroundColor: colors.primary[500] }]} />
                <View style={styles.timelineContent}>
                  <Text style={[styles.timelineItemTitle, { color: colors.text }]}>
                    {progress.toFixed(0)}% Complete
                  </Text>
                  <Text style={[styles.timelineItemDate, { color: colors.primary[600] }]}>
                    Current progress
                  </Text>
                </View>
              </View>

              <View style={styles.timelineItem}>
                <View style={[styles.timelineDot, { backgroundColor: colors.secondary[300] }]} />
                <View style={styles.timelineContent}>
                  <Text style={[styles.timelineItemTitle, { color: colors.textSecondary }]}>
                    100% Complete
                  </Text>
                  <Text style={[styles.timelineItemDate, { color: colors.textSecondary }]}>
                    Goal achievement
                  </Text>
                </View>
              </View>
            </View>
          </View>
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
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  menuButton: {
    padding: 8,
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
  progressCard: {
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
  },
  progressHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  categoryIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  progressInfo: {
    flex: 1,
  },
  currentAmount: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  targetAmount: {
    fontSize: 16,
  },
  progressBarContainer: {
    height: 12,
    borderRadius: 6,
    marginBottom: 16,
  },
  progressBar: {
    height: 12,
    borderRadius: 6,
  },
  progressStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressPercentage: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  remainingAmount: {
    fontSize: 14,
  },
  detailsCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  detailsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  detailContent: {
    marginLeft: 12,
    flex: 1,
  },
  detailLabel: {
    fontSize: 14,
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  suggestionCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    alignItems: 'center',
  },
  suggestionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  suggestionSubtitle: {
    fontSize: 14,
    marginBottom: 16,
  },
  suggestionAmount: {
    alignItems: 'center',
  },
  suggestionValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  suggestionLabel: {
    fontSize: 14,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    marginHorizontal: 6,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  timelineCard: {
    borderRadius: 16,
    padding: 20,
  },
  timelineTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  timeline: {},
  timelineItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  timelineDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 16,
  },
  timelineContent: {
    flex: 1,
  },
  timelineItemTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  timelineItemDate: {
    fontSize: 14,
  },
});

export default GoalDetailScreen;