import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Animated,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../contexts/ThemeContext';
import { useData } from '../../contexts/DataContext';

const AddGoalScreen: React.FC = () => {
  const { colors } = useTheme();
  const navigation = useNavigation();
  const { addGoal } = useData();
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    targetAmount: '',
    currentAmount: '0',
    targetDate: '',
    category: 'other' as 'retirement' | 'emergency' | 'travel' | 'home' | 'education' | 'other',
    priority: 'medium' as 'high' | 'medium' | 'low',
  });
  
  const fadeAnim = useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();
  }, []);

  const categories = [
    { key: 'retirement', label: 'Retirement', icon: 'time-outline', color: colors.primary[500] },
    { key: 'emergency', label: 'Emergency Fund', icon: 'shield-outline', color: colors.error[500] },
    { key: 'travel', label: 'Travel', icon: 'airplane-outline', color: colors.warning[500] },
    { key: 'home', label: 'Home', icon: 'home-outline', color: colors.success[500] },
    { key: 'education', label: 'Education', icon: 'school-outline', color: colors.secondary[500] },
    { key: 'other', label: 'Other', icon: 'ellipsis-horizontal-outline', color: colors.secondary[400] },
  ];

  const priorities = [
    { key: 'high', label: 'High Priority', color: colors.error[500] },
    { key: 'medium', label: 'Medium Priority', color: colors.warning[500] },
    { key: 'low', label: 'Low Priority', color: colors.success[500] },
  ];

  const updateFormData = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    // Validation
    if (!formData.title.trim()) {
      Alert.alert('Error', 'Please enter a goal title');
      return;
    }
    
    if (!formData.targetAmount || parseFloat(formData.targetAmount) <= 0) {
      Alert.alert('Error', 'Please enter a valid target amount');
      return;
    }
    
    if (!formData.targetDate) {
      Alert.alert('Error', 'Please select a target date');
      return;
    }

    try {
      await addGoal({
        title: formData.title.trim(),
        description: formData.description.trim() || `Save ${formData.targetAmount} for ${formData.title}`,
        targetAmount: parseFloat(formData.targetAmount),
        currentAmount: parseFloat(formData.currentAmount) || 0,
        targetDate: formData.targetDate,
        category: formData.category,
        priority: formData.priority,
        isCompleted: false,
      });

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert(
        'Goal Created!',
        'Your new financial goal has been added successfully.',
        [
          { text: 'OK', onPress: () => navigation.goBack() }
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to create goal. Please try again.');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  };

  const formatCurrency = (amount: string) => {
    const num = parseFloat(amount.replace(/[^0-9.]/g, ''));
    return isNaN(num) ? '' : num.toLocaleString();
  };

  // Generate a default target date (1 year from now)
  const defaultTargetDate = () => {
    const date = new Date();
    date.setFullYear(date.getFullYear() + 1);
    return date.toISOString().split('T')[0];
  };

  React.useEffect(() => {
    if (!formData.targetDate) {
      updateFormData('targetDate', defaultTargetDate());
    }
  }, []);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <LinearGradient
        colors={colors.gradient.primary}
        style={styles.header}
      >
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={24} color="white" />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle}>New Goal</Text>
        
        <TouchableOpacity
          style={styles.saveButton}
          onPress={handleSave}
        >
          <Text style={styles.saveButtonText}>Save</Text>
        </TouchableOpacity>
      </LinearGradient>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[{ opacity: fadeAnim }, styles.content]}>
          {/* Basic Information */}
          <View style={[styles.section, { backgroundColor: colors.surface }]}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Basic Information
            </Text>
            
            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                Goal Title *
              </Text>
              <TextInput
                style={[styles.input, { backgroundColor: colors.background, color: colors.text }]}
                placeholder="e.g., Emergency Fund, Vacation, New Car"
                placeholderTextColor={colors.textSecondary}
                value={formData.title}
                onChangeText={(value) => updateFormData('title', value)}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                Description (Optional)
              </Text>
              <TextInput
                style={[styles.textArea, { backgroundColor: colors.background, color: colors.text }]}
                placeholder="Describe your goal..."
                placeholderTextColor={colors.textSecondary}
                value={formData.description}
                onChangeText={(value) => updateFormData('description', value)}
                multiline
                numberOfLines={3}
              />
            </View>
          </View>

          {/* Financial Details */}
          <View style={[styles.section, { backgroundColor: colors.surface }]}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Financial Details
            </Text>
            
            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                Target Amount *
              </Text>
              <View style={styles.currencyInput}>
                <Text style={[styles.currencySymbol, { color: colors.textSecondary }]}>$</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text }]}
                  placeholder="10,000"
                  placeholderTextColor={colors.textSecondary}
                  value={formData.targetAmount}
                  onChangeText={(value) => updateFormData('targetAmount', formatCurrency(value))}
                  keyboardType="numeric"
                />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                Current Amount
              </Text>
              <View style={styles.currencyInput}>
                <Text style={[styles.currencySymbol, { color: colors.textSecondary }]}>$</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text }]}
                  placeholder="0"
                  placeholderTextColor={colors.textSecondary}
                  value={formData.currentAmount}
                  onChangeText={(value) => updateFormData('currentAmount', formatCurrency(value))}
                  keyboardType="numeric"
                />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={[styles.inputLabel, { color: colors.textSecondary }]}>
                Target Date *
              </Text>
              <TextInput
                style={[styles.input, { backgroundColor: colors.background, color: colors.text }]}
                placeholder="YYYY-MM-DD"
                placeholderTextColor={colors.textSecondary}
                value={formData.targetDate}
                onChangeText={(value) => updateFormData('targetDate', value)}
              />
            </View>
          </View>

          {/* Category Selection */}
          <View style={[styles.section, { backgroundColor: colors.surface }]}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Category
            </Text>
            
            <View style={styles.categoryGrid}>
              {categories.map((category) => (
                <TouchableOpacity
                  key={category.key}
                  style={[
                    styles.categoryItem,
                    {
                      backgroundColor: formData.category === category.key
                        ? `${category.color}15`
                        : colors.background,
                      borderColor: formData.category === category.key
                        ? category.color
                        : colors.border,
                    },
                  ]}
                  onPress={() => {
                    updateFormData('category', category.key);
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  }}
                >
                  <Ionicons
                    name={category.icon as keyof typeof Ionicons.glyphMap}
                    size={24}
                    color={formData.category === category.key ? category.color : colors.textSecondary}
                  />
                  <Text
                    style={[
                      styles.categoryLabel,
                      {
                        color: formData.category === category.key ? category.color : colors.textSecondary,
                        fontWeight: formData.category === category.key ? 'bold' : 'normal',
                      },
                    ]}
                  >
                    {category.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Priority Selection */}
          <View style={[styles.section, { backgroundColor: colors.surface }]}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              Priority Level
            </Text>
            
            <View style={styles.priorityList}>
              {priorities.map((priority) => (
                <TouchableOpacity
                  key={priority.key}
                  style={[
                    styles.priorityItem,
                    {
                      backgroundColor: formData.priority === priority.key
                        ? `${priority.color}15`
                        : colors.background,
                      borderColor: formData.priority === priority.key
                        ? priority.color
                        : colors.border,
                    },
                  ]}
                  onPress={() => {
                    updateFormData('priority', priority.key);
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  }}
                >
                  <View
                    style={[
                      styles.priorityDot,
                      { backgroundColor: priority.color },
                    ]}
                  />
                  <Text
                    style={[
                      styles.priorityLabel,
                      {
                        color: formData.priority === priority.key ? priority.color : colors.text,
                        fontWeight: formData.priority === priority.key ? 'bold' : 'normal',
                      },
                    ]}
                  >
                    {priority.label}
                  </Text>
                  {formData.priority === priority.key && (
                    <Ionicons name="checkmark" size={20} color={priority.color} />
                  )}
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Goal Preview */}
          {formData.title && formData.targetAmount && (
            <View style={[styles.previewCard, { backgroundColor: colors.surface }]}>
              <Text style={[styles.previewTitle, { color: colors.text }]}>
                Goal Preview
              </Text>
              
              <View style={styles.previewContent}>
                <View style={styles.previewHeader}>
                  <View style={[
                    styles.previewIcon,
                    { backgroundColor: `${categories.find(c => c.key === formData.category)?.color}15` }
                  ]}>
                    <Ionicons
                      name={categories.find(c => c.key === formData.category)?.icon as keyof typeof Ionicons.glyphMap}
                      size={24}
                      color={categories.find(c => c.key === formData.category)?.color}
                    />
                  </View>
                  <View style={styles.previewInfo}>
                    <Text style={[styles.previewGoalTitle, { color: colors.text }]}>
                      {formData.title}
                    </Text>
                    <Text style={[styles.previewAmount, { color: colors.textSecondary }]}>
                      ${parseFloat(formData.currentAmount || '0').toLocaleString()} / ${parseFloat(formData.targetAmount || '0').toLocaleString()}
                    </Text>
                  </View>
                </View>
                
                <View style={[styles.previewProgressBar, { backgroundColor: colors.secondary[200] }]}>
                  <View
                    style={[
                      styles.previewProgress,
                      {
                        width: `${Math.min((parseFloat(formData.currentAmount || '0') / parseFloat(formData.targetAmount || '1')) * 100, 100)}%`,
                        backgroundColor: categories.find(c => c.key === formData.category)?.color,
                      },
                    ]}
                  />
                </View>
              </View>
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
  saveButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  saveButtonText: {
    color: 'white',
    fontWeight: 'bold',
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
  section: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  input: {
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  textArea: {
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'transparent',
    minHeight: 80,
    textAlignVertical: 'top',
  },
  currencyInput: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  currencySymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    marginRight: 8,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  categoryItem: {
    width: '48%',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryLabel: {
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
  },
  priorityList: {},
  priorityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    marginBottom: 12,
  },
  priorityDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  priorityLabel: {
    fontSize: 16,
    flex: 1,
  },
  previewCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  previewTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  previewContent: {},
  previewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  previewIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  previewInfo: {
    flex: 1,
  },
  previewGoalTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  previewAmount: {
    fontSize: 14,
  },
  previewProgressBar: {
    height: 8,
    borderRadius: 4,
  },
  previewProgress: {
    height: 8,
    borderRadius: 4,
  },
});

export default AddGoalScreen;