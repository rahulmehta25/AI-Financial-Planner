import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { PieChart, LineChart } from 'react-native-chart-kit';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useData } from '../../contexts/DataContext';
import { useAuth } from '../../contexts/AuthContext';

const { width: screenWidth } = Dimensions.get('window');

const DashboardScreen: React.FC = () => {
  const { colors, spacing } = useTheme();
  const { user } = useAuth();
  const {
    totalNetWorth,
    monthlyIncome,
    monthlyExpenses,
    portfolio,
    goals,
    refreshData,
    lastSync,
  } = useData();
  
  const [refreshing, setRefreshing] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  React.useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    
    refreshData();
    
    setTimeout(() => {
      setRefreshing(false);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }, 2000);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const portfolioData = portfolio.map((item) => ({
    name: item.symbol,
    population: item.allocation,
    color: item.changePercent > 0 ? colors.success[500] : colors.error[500],
    legendFontColor: colors.text,
    legendFontSize: 12,
  }));

  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        data: [65000, 68000, 72000, 70000, 75000, totalNetWorth],
        color: (opacity = 1) => colors.primary[500],
        strokeWidth: 3,
      },
    ],
  };

  const chartConfig = {
    backgroundGradientFrom: colors.surface,
    backgroundGradientTo: colors.surface,
    color: (opacity = 1) => colors.primary[500],
    strokeWidth: 2,
    barPercentage: 0.5,
    decimalPlaces: 0,
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: colors.primary[500],
    },
    propsForBackgroundLines: {
      stroke: colors.border,
    },
    propsForLabels: {
      fontSize: '12',
      fill: colors.textSecondary,
    },
  };

  const completedGoals = goals.filter(goal => goal.isCompleted).length;
  const totalGoals = goals.length;
  const activeGoals = goals.filter(goal => !goal.isCompleted);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
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
        <Animated.View
          style={[
            styles.content,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          {/* Header */}
          <View style={styles.header}>
            <View>
              <Text style={[styles.greeting, { color: colors.textSecondary }]}>
                Good morning,
              </Text>
              <Text style={[styles.userName, { color: colors.text }]}>
                {user?.name || 'User'}
              </Text>
            </View>
            <View style={[styles.avatarContainer, { backgroundColor: colors.primary[100] }]}>
              <Text style={[styles.avatar, { color: colors.primary[600] }]}>
                {user?.name?.charAt(0) || 'U'}
              </Text>
            </View>
          </View>

          {/* Net Worth Card */}
          <LinearGradient
            colors={colors.gradient.primary}
            style={styles.netWorthCard}
          >
            <View style={styles.netWorthHeader}>
              <Text style={styles.netWorthLabel}>Total Net Worth</Text>
              <TouchableOpacity
                onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
              >
                <Ionicons name="eye-outline" size={20} color="white" />
              </TouchableOpacity>
            </View>
            <Text style={styles.netWorthAmount}>
              {formatCurrency(totalNetWorth)}
            </Text>
            <View style={styles.netWorthChange}>
              <Ionicons name="trending-up" size={16} color="#4ade80" />
              <Text style={styles.changeText}>+12.5% this month</Text>
            </View>
          </LinearGradient>

          {/* Quick Stats */}
          <View style={styles.statsContainer}>
            <View style={[styles.statCard, { backgroundColor: colors.surface }]}>
              <View style={[styles.statIcon, { backgroundColor: colors.success[100] }]}>
                <Ionicons name="arrow-down" size={20} color={colors.success[600]} />
              </View>
              <Text style={[styles.statLabel, { color: colors.textSecondary }]}>
                Income
              </Text>
              <Text style={[styles.statValue, { color: colors.text }]}>
                {formatCurrency(monthlyIncome)}
              </Text>
              <Text style={[styles.statChange, { color: colors.success[600] }]}>
                +5.2%
              </Text>
            </View>

            <View style={[styles.statCard, { backgroundColor: colors.surface }]}>
              <View style={[styles.statIcon, { backgroundColor: colors.error[100] }]}>
                <Ionicons name="arrow-up" size={20} color={colors.error[600]} />
              </View>
              <Text style={[styles.statLabel, { color: colors.textSecondary }]}>
                Expenses
              </Text>
              <Text style={[styles.statValue, { color: colors.text }]}>
                {formatCurrency(monthlyExpenses)}
              </Text>
              <Text style={[styles.statChange, { color: colors.error[600] }]}>
                +2.1%
              </Text>
            </View>
          </View>

          {/* Portfolio Chart */}
          <View style={[styles.chartCard, { backgroundColor: colors.surface }]}>
            <View style={styles.chartHeader}>
              <Text style={[styles.chartTitle, { color: colors.text }]}>
                Portfolio Performance
              </Text>
              <TouchableOpacity>
                <Text style={[styles.viewAllText, { color: colors.primary[600] }]}>
                  View All
                </Text>
              </TouchableOpacity>
            </View>
            
            <LineChart
              data={chartData}
              width={screenWidth - 64}
              height={200}
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
            />
          </View>

          {/* Portfolio Allocation */}
          <View style={[styles.chartCard, { backgroundColor: colors.surface }]}>
            <View style={styles.chartHeader}>
              <Text style={[styles.chartTitle, { color: colors.text }]}>
                Portfolio Allocation
              </Text>
            </View>
            
            <PieChart
              data={portfolioData}
              width={screenWidth - 64}
              height={200}
              chartConfig={chartConfig}
              accessor="population"
              backgroundColor="transparent"
              paddingLeft="15"
            />
          </View>

          {/* Goals Progress */}
          <View style={[styles.goalCard, { backgroundColor: colors.surface }]}>
            <View style={styles.goalHeader}>
              <Text style={[styles.goalTitle, { color: colors.text }]}>
                Financial Goals
              </Text>
              <Text style={[styles.goalStats, { color: colors.textSecondary }]}>
                {completedGoals}/{totalGoals} completed
              </Text>
            </View>
            
            {activeGoals.slice(0, 3).map((goal) => {
              const progress = (goal.currentAmount / goal.targetAmount) * 100;
              return (
                <View key={goal.id} style={styles.goalItem}>
                  <View style={styles.goalInfo}>
                    <Text style={[styles.goalName, { color: colors.text }]}>
                      {goal.title}
                    </Text>
                    <Text style={[styles.goalAmount, { color: colors.textSecondary }]}>
                      {formatCurrency(goal.currentAmount)} / {formatCurrency(goal.targetAmount)}
                    </Text>
                  </View>
                  <View style={[styles.progressBar, { backgroundColor: colors.secondary[200] }]}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width: `${Math.min(progress, 100)}%`,
                          backgroundColor: colors.primary[500],
                        },
                      ]}
                    />
                  </View>
                  <Text style={[styles.progressText, { color: colors.primary[600] }]}>
                    {progress.toFixed(0)}%
                  </Text>
                </View>
              );
            })}
          </View>

          {/* Last Sync Info */}
          <View style={styles.syncInfo}>
            <Ionicons name="sync-outline" size={16} color={colors.textSecondary} />
            <Text style={[styles.syncText, { color: colors.textSecondary }]}>
              Last updated: {lastSync ? lastSync.toLocaleTimeString() : 'Never'}
            </Text>
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  content: {
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  greeting: {
    fontSize: 16,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  avatarContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatar: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  netWorthCard: {
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
  },
  netWorthHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  netWorthLabel: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 16,
  },
  netWorthAmount: {
    color: 'white',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  netWorthChange: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  changeText: {
    color: '#4ade80',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 6,
  },
  statIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statChange: {
    fontSize: 12,
    fontWeight: '600',
  },
  chartCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  viewAllText: {
    fontSize: 14,
    fontWeight: '600',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  goalCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  goalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  goalStats: {
    fontSize: 14,
  },
  goalItem: {
    marginBottom: 16,
  },
  goalInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  goalName: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  goalAmount: {
    fontSize: 14,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    marginBottom: 4,
  },
  progressFill: {
    height: 6,
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'right',
  },
  syncInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 20,
  },
  syncText: {
    fontSize: 12,
    marginLeft: 4,
  },
});

export default DashboardScreen;