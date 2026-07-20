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
import { PieChart } from 'react-native-chart-kit';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useData } from '../../contexts/DataContext';

const { width: screenWidth } = Dimensions.get('window');

const PortfolioScreen: React.FC = () => {
  const { colors } = useTheme();
  const { portfolio, totalNetWorth, refreshData } = useData();
  
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('1D');
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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const periods = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];
  
  const portfolioData = portfolio.map((item, index) => {
    const colors = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
    return {
      name: item.symbol,
      population: item.allocation,
      color: colors[index % colors.length],
      legendFontColor: '#64748b',
      legendFontSize: 12,
    };
  });

  const chartConfig = {
    color: (opacity = 1) => colors.primary[500],
    backgroundColor: colors.surface,
  };

  const totalChange = portfolio.reduce((sum, item) => sum + item.change, 0);
  const totalChangePercent = (totalChange / totalNetWorth) * 100;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <View>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            Portfolio
          </Text>
          <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
            {portfolio.length} investments
          </Text>
        </View>
        <TouchableOpacity style={styles.menuButton}>
          <Ionicons name="ellipsis-horizontal" size={24} color={colors.text} />
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
          {/* Total Value Card */}
          <LinearGradient
            colors={totalChange >= 0 ? colors.gradient.success : colors.gradient.sunset}
            style={styles.totalCard}
          >
            <Text style={styles.totalLabel}>Total Portfolio Value</Text>
            <Text style={styles.totalValue}>
              {formatCurrency(totalNetWorth)}
            </Text>
            <View style={styles.changeContainer}>
              <Ionicons 
                name={totalChange >= 0 ? "trending-up" : "trending-down"} 
                size={16} 
                color="white" 
              />
              <Text style={styles.changeText}>
                {formatCurrency(Math.abs(totalChange))} ({formatPercentage(totalChangePercent)})
              </Text>
            </View>
            <Text style={styles.periodText}>Today</Text>
          </LinearGradient>

          {/* Time Period Selector */}
          <View style={styles.periodSelector}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {periods.map((period) => (
                <TouchableOpacity
                  key={period}
                  style={[
                    styles.periodButton,
                    {
                      backgroundColor: selectedPeriod === period 
                        ? colors.primary[500] 
                        : colors.surface,
                    },
                  ]}
                  onPress={() => {
                    setSelectedPeriod(period);
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  }}
                >
                  <Text
                    style={[
                      styles.periodButtonText,
                      {
                        color: selectedPeriod === period 
                          ? 'white' 
                          : colors.textSecondary,
                      },
                    ]}
                  >
                    {period}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Portfolio Allocation Chart */}
          <View style={[styles.chartCard, { backgroundColor: colors.surface }]}>
            <Text style={[styles.chartTitle, { color: colors.text }]}>
              Asset Allocation
            </Text>
            <PieChart
              data={portfolioData}
              width={screenWidth - 64}
              height={220}
              chartConfig={chartConfig}
              accessor="population"
              backgroundColor="transparent"
              paddingLeft="15"
              absolute
            />
          </View>

          {/* Holdings List */}
          <View style={[styles.holdingsCard, { backgroundColor: colors.surface }]}>
            <Text style={[styles.holdingsTitle, { color: colors.text }]}>
              Your Holdings
            </Text>
            
            {portfolio.map((item, index) => (
              <TouchableOpacity
                key={item.id}
                style={[
                  styles.holdingItem,
                  index < portfolio.length - 1 && { borderBottomWidth: 1, borderBottomColor: colors.border }
                ]}
                onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
              >
                <View style={styles.holdingLeft}>
                  <View style={[styles.symbolContainer, { backgroundColor: portfolioData[index].color + '20' }]}>
                    <Text style={[styles.symbolText, { color: portfolioData[index].color }]}>
                      {item.symbol.charAt(0)}
                    </Text>
                  </View>
                  <View style={styles.holdingInfo}>
                    <Text style={[styles.holdingName, { color: colors.text }]}>
                      {item.name}
                    </Text>
                    <Text style={[styles.holdingSymbol, { color: colors.textSecondary }]}>
                      {item.symbol} • {item.amount} {item.symbol === 'BTC' ? 'BTC' : 'shares'}
                    </Text>
                  </View>
                </View>
                
                <View style={styles.holdingRight}>
                  <Text style={[styles.holdingValue, { color: colors.text }]}>
                    {formatCurrency(item.value)}
                  </Text>
                  <View style={styles.holdingChange}>
                    <Ionicons 
                      name={item.changePercent >= 0 ? "triangle" : "triangle"} 
                      size={8} 
                      color={item.changePercent >= 0 ? colors.success[500] : colors.error[500]}
                      style={{ 
                        transform: [{ rotate: item.changePercent >= 0 ? '0deg' : '180deg' }] 
                      }}
                    />
                    <Text 
                      style={[
                        styles.holdingChangeText, 
                        { color: item.changePercent >= 0 ? colors.success[500] : colors.error[500] }
                      ]}
                    >
                      {formatPercentage(item.changePercent)}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          {/* Performance Summary */}
          <View style={[styles.summaryCard, { backgroundColor: colors.surface }]}>
            <Text style={[styles.summaryTitle, { color: colors.text }]}>
              Performance Summary
            </Text>
            
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>
                Best Performer
              </Text>
              <View style={styles.summaryValue}>
                <Text style={[styles.summaryText, { color: colors.success[600] }]}>
                  BTC +6.38%
                </Text>
              </View>
            </View>
            
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>
                Worst Performer
              </Text>
              <View style={styles.summaryValue}>
                <Text style={[styles.summaryText, { color: colors.error[600] }]}>
                  VOO -0.42%
                </Text>
              </View>
            </View>
            
            <View style={styles.summaryRow}>
              <Text style={[styles.summaryLabel, { color: colors.textSecondary }]}>
                Total Gain/Loss
              </Text>
              <View style={styles.summaryValue}>
                <Text style={[
                  styles.summaryText, 
                  { color: totalChange >= 0 ? colors.success[600] : colors.error[600] }
                ]}>
                  {formatCurrency(totalChange)}
                </Text>
              </View>
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            <TouchableOpacity 
              style={[styles.actionButton, { backgroundColor: colors.primary[500] }]}
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium)}
            >
              <Ionicons name="add" size={20} color="white" />
              <Text style={styles.actionButtonText}>Buy</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.actionButton, { backgroundColor: colors.error[500] }]}
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium)}
            >
              <Ionicons name="remove" size={20} color="white" />
              <Text style={styles.actionButtonText}>Sell</Text>
            </TouchableOpacity>
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
  menuButton: {
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
  totalCard: {
    borderRadius: 16,
    padding: 24,
    marginBottom: 20,
    alignItems: 'center',
  },
  totalLabel: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 16,
    marginBottom: 8,
  },
  totalValue: {
    color: 'white',
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  changeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  changeText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 4,
  },
  periodText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 14,
  },
  periodSelector: {
    marginBottom: 20,
  },
  periodButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  periodButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  chartCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  holdingsCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  holdingsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  holdingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  holdingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  symbolContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  symbolText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  holdingInfo: {
    flex: 1,
  },
  holdingName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  holdingSymbol: {
    fontSize: 14,
  },
  holdingRight: {
    alignItems: 'flex-end',
  },
  holdingValue: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  holdingChange: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  holdingChangeText: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
  summaryCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  summaryLabel: {
    fontSize: 14,
  },
  summaryValue: {
    alignItems: 'flex-end',
  },
  summaryText: {
    fontSize: 14,
    fontWeight: '600',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
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
});

export default PortfolioScreen;