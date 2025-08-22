import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useData } from '../../contexts/DataContext';

const GoalsScreen: React.FC = () => {
  const { colors } = useTheme();
  const navigation = useNavigation();
  const { goals, updateGoal, refreshData } = useData();
  
  const [refreshing, setRefreshing] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    refreshData();
    setTimeout(() => setRefreshing(false), 2000);
  };

  const handleGoalPress = (goalId: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    navigation.navigate('GoalDetail' as never, { goalId } as never);
  };

  const handleAddGoal = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    navigation.navigate('AddGoal' as never);
  };

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
    const colorMap: { [key: string]: string } = {
      retirement: colors.primary[500],
      emergency: colors.error[500],
      travel: colors.warning[500],
      home: colors.success[500],
      education: colors.secondary[500],
      other: colors.secondary[400],
    };
    return colorMap[category] || colors.primary[500];
  };

  const getPriorityColor = (priority: string) => {
    const priorityMap: { [key: string]: string } = {
      high: colors.error[500],
      medium: colors.warning[500],
      low: colors.success[500],
    };
    return priorityMap[priority] || colors.secondary[400];
  };

  const activeGoals = goals.filter(goal => !goal.isCompleted);
  const completedGoals = goals.filter(goal => goal.isCompleted);
  const totalProgress = goals.reduce((sum, goal) => 
    sum + (goal.currentAmount / goal.targetAmount), 0
  ) / goals.length * 100;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <View>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            Financial Goals
          </Text>
          <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
            {activeGoals.length} active • {completedGoals.length} completed
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.addButton, { backgroundColor: colors.primary[500] }]}
          onPress={handleAddGoal}
        >
          <Ionicons name="add" size={24} color="white" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary[500]}
            colors={[colors.primary[500]]}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[{ opacity: fadeAnim }, styles.content]}>
          {/* Overview Card */}
          <LinearGradient
            colors={colors.gradient.primary}
            style={styles.overviewCard}
          >
            <View style={styles.overviewContent}>
              <Text style={styles.overviewTitle}>Overall Progress</Text>
              <Text style={styles.overviewPercentage}>
                {totalProgress.toFixed(0)}%
              </Text>
              <Text style={styles.overviewSubtitle}>
                Keep up the great work!
              </Text>
            </View>
            <View style={styles.overviewIcon}>
              <Ionicons name="trophy" size={40} color="rgba(255,255,255,0.8)" />
            </View>
          </LinearGradient>

          {/* Active Goals */}
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Active Goals ({activeGoals.length})
            </Text>
            
            {activeGoals.map((goal) => {
              const progress = (goal.currentAmount / goal.targetAmount) * 100;
              const remaining = goal.targetAmount - goal.currentAmount;
              
              return (
                <TouchableOpacity
                  key={goal.id}
                  style={[styles.goalCard, { backgroundColor: colors.surface }]}
                  onPress={() => handleGoalPress(goal.id)}
                >
                  <View style={styles.goalHeader}>
                    <View style={styles.goalInfo}>
                      <View style={[styles.categoryIcon, { backgroundColor: `${getCategoryColor(goal.category)}20` }]}>
                        <Ionicons
                          name={getCategoryIcon(goal.category)}
                          size={20}
                          color={getCategoryColor(goal.category)}
                        />
                      </View>
                      <View style={styles.goalDetails}>
                        <Text style={[styles.goalTitle, { color: colors.text }]}>
                          {goal.title}
                        </Text>
                        <Text style={[styles.goalDescription, { color: colors.textSecondary }]}>
                          {goal.description}
                        </Text>
                      </View>
                    </View>
                    <View style={[styles.priorityBadge, { borderColor: getPriorityColor(goal.priority) }]}>
                      <Text style={[styles.priorityText, { color: getPriorityColor(goal.priority) }]}>
                        {goal.priority.toUpperCase()}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.goalProgress}>
                    <View style={styles.progressInfo}>
                      <Text style={[styles.progressText, { color: colors.text }]}>
                        {formatCurrency(goal.currentAmount)} / {formatCurrency(goal.targetAmount)}
                      </Text>
                      <Text style={[styles.remainingText, { color: colors.textSecondary }]}>
                        {formatCurrency(remaining)} remaining
                      </Text>
                    </View>
                    
                    <View style={[styles.progressBarContainer, { backgroundColor: colors.secondary[200] }]}>
                      <Animated.View
                        style={[
                          styles.progressBar,
                          {
                            width: `${Math.min(progress, 100)}%`,
                            backgroundColor: getCategoryColor(goal.category),
                          },
                        ]}
                      />
                    </View>
                    
                    <Text style={[styles.progressPercentage, { color: getCategoryColor(goal.category) }]}>
                      {progress.toFixed(1)}%
                    </Text>
                  </View>

                  <View style={styles.goalFooter}>
                    <View style={styles.targetDate}>
                      <Ionicons name="calendar-outline" size={14} color={colors.textSecondary} />
                      <Text style={[styles.targetDateText, { color: colors.textSecondary }]}>
                        Target: {new Date(goal.targetDate).toLocaleDateString()}
                      </Text>
                    </View>
                    <TouchableOpacity style={styles.actionButton}>
                      <Ionicons name="chevron-forward" size={16} color={colors.primary[500]} />
                    </TouchableOpacity>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Completed Goals */}
          {completedGoals.length > 0 && (
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                Completed Goals ({completedGoals.length})
              </Text>
              
              {completedGoals.map((goal) => (
                <TouchableOpacity
                  key={goal.id}
                  style={[
                    styles.goalCard,
                    styles.completedGoalCard,
                    { backgroundColor: colors.surface, borderColor: colors.success[200] }
                  ]}
                  onPress={() => handleGoalPress(goal.id)}
                >
                  <View style={styles.goalHeader}>
                    <View style={styles.goalInfo}>
                      <View style={[styles.categoryIcon, { backgroundColor: `${colors.success[500]}20` }]}>
                        <Ionicons name="checkmark" size={20} color={colors.success[500]} />
                      </View>
                      <View style={styles.goalDetails}>
                        <Text style={[styles.goalTitle, { color: colors.text }]}>
                          {goal.title}
                        </Text>
                        <Text style={[styles.completedText, { color: colors.success[600] }]}>
                          Goal completed! 🎉
                        </Text>
                      </View>
                    </View>
                  </View>
                  
                  <View style={styles.completedAmount}>
                    <Text style={[styles.completedAmountText, { color: colors.success[600] }]}>
                      {formatCurrency(goal.targetAmount)}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Empty State */}
          {goals.length === 0 && (
            <View style={styles.emptyState}>
              <Ionicons name="flag-outline" size={80} color={colors.textSecondary} />
              <Text style={[styles.emptyTitle, { color: colors.text }]}>
                No Goals Yet
              </Text>
              <Text style={[styles.emptyDescription, { color: colors.textSecondary }]}>
                Set your first financial goal to start tracking your progress
              </Text>
              <TouchableOpacity
                style={[styles.emptyButton, { backgroundColor: colors.primary[500] }]}
                onPress={handleAddGoal}
              >
                <Text style={styles.emptyButtonText}>Create Your First Goal</Text>
              </TouchableOpacity>
            </View>
          )}
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
    justifyContent: 'space-between',
    alignItems: 'center',
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
  addButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
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
  overviewCard: {
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  overviewContent: {
    flex: 1,
  },
  overviewTitle: {
    color: 'white',
    fontSize: 16,
    marginBottom: 8,
  },
  overviewPercentage: {
    color: 'white',
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  overviewSubtitle: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
  },
  overviewIcon: {
    marginLeft: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  goalCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  completedGoalCard: {
    borderWidth: 1,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  goalInfo: {
    flexDirection: 'row',
    flex: 1,
  },
  categoryIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  goalDetails: {
    flex: 1,
  },
  goalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  goalDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  priorityBadge: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: 'bold',
  },
  goalProgress: {
    marginBottom: 16,
  },
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressText: {
    fontSize: 16,
    fontWeight: '600',
  },
  remainingText: {
    fontSize: 14,
  },
  progressBarContainer: {
    height: 8,
    borderRadius: 4,
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
  },
  progressPercentage: {
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'right',
  },
  goalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  targetDate: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  targetDateText: {
    fontSize: 12,
    marginLeft: 4,
  },
  actionButton: {
    padding: 4,
  },
  completedText: {
    fontSize: 14,
    fontWeight: '600',
  },
  completedAmount: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  completedAmountText: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 24,
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
    paddingHorizontal: 40,
  },
  emptyButton: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  emptyButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default GoalsScreen;