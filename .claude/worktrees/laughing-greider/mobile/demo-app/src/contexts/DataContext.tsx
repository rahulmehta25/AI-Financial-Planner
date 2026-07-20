import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface FinancialGoal {
  id: string;
  title: string;
  description: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  category: 'retirement' | 'emergency' | 'travel' | 'home' | 'education' | 'other';
  priority: 'high' | 'medium' | 'low';
  isCompleted: boolean;
}

export interface PortfolioItem {
  id: string;
  name: string;
  symbol: string;
  amount: number;
  value: number;
  change: number;
  changePercent: number;
  allocation: number;
}

export interface Transaction {
  id: string;
  description: string;
  amount: number;
  category: string;
  date: string;
  type: 'income' | 'expense';
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlockedAt: string | null;
  progress: number;
  maxProgress: number;
}

interface DataContextType {
  goals: FinancialGoal[];
  portfolio: PortfolioItem[];
  transactions: Transaction[];
  achievements: Achievement[];
  totalNetWorth: number;
  monthlyIncome: number;
  monthlyExpenses: number;
  addGoal: (goal: Omit<FinancialGoal, 'id'>) => void;
  updateGoal: (id: string, updates: Partial<FinancialGoal>) => void;
  deleteGoal: (id: string) => void;
  addTransaction: (transaction: Omit<Transaction, 'id'>) => void;
  refreshData: () => void;
  isOffline: boolean;
  lastSync: Date | null;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [isOffline, setIsOffline] = useState(false);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      // Try to load from AsyncStorage first
      const storedGoals = await AsyncStorage.getItem('financial_goals');
      const storedPortfolio = await AsyncStorage.getItem('portfolio');
      const storedTransactions = await AsyncStorage.getItem('transactions');
      const storedAchievements = await AsyncStorage.getItem('achievements');

      if (storedGoals) {
        setGoals(JSON.parse(storedGoals));
      } else {
        setGoals(mockGoals);
        await AsyncStorage.setItem('financial_goals', JSON.stringify(mockGoals));
      }

      if (storedPortfolio) {
        setPortfolio(JSON.parse(storedPortfolio));
      } else {
        setPortfolio(mockPortfolio);
        await AsyncStorage.setItem('portfolio', JSON.stringify(mockPortfolio));
      }

      if (storedTransactions) {
        setTransactions(JSON.parse(storedTransactions));
      } else {
        setTransactions(mockTransactions);
        await AsyncStorage.setItem('transactions', JSON.stringify(mockTransactions));
      }

      if (storedAchievements) {
        setAchievements(JSON.parse(storedAchievements));
      } else {
        setAchievements(mockAchievements);
        await AsyncStorage.setItem('achievements', JSON.stringify(mockAchievements));
      }

      setLastSync(new Date());
    } catch (error) {
      console.error('Error loading data:', error);
      setIsOffline(true);
    }
  };

  const addGoal = async (goalData: Omit<FinancialGoal, 'id'>) => {
    try {
      const newGoal: FinancialGoal = {
        ...goalData,
        id: Date.now().toString(),
      };
      const updatedGoals = [...goals, newGoal];
      setGoals(updatedGoals);
      await AsyncStorage.setItem('financial_goals', JSON.stringify(updatedGoals));
    } catch (error) {
      console.error('Error adding goal:', error);
    }
  };

  const updateGoal = async (id: string, updates: Partial<FinancialGoal>) => {
    try {
      const updatedGoals = goals.map(goal =>
        goal.id === id ? { ...goal, ...updates } : goal
      );
      setGoals(updatedGoals);
      await AsyncStorage.setItem('financial_goals', JSON.stringify(updatedGoals));
    } catch (error) {
      console.error('Error updating goal:', error);
    }
  };

  const deleteGoal = async (id: string) => {
    try {
      const updatedGoals = goals.filter(goal => goal.id !== id);
      setGoals(updatedGoals);
      await AsyncStorage.setItem('financial_goals', JSON.stringify(updatedGoals));
    } catch (error) {
      console.error('Error deleting goal:', error);
    }
  };

  const addTransaction = async (transactionData: Omit<Transaction, 'id'>) => {
    try {
      const newTransaction: Transaction = {
        ...transactionData,
        id: Date.now().toString(),
      };
      const updatedTransactions = [newTransaction, ...transactions];
      setTransactions(updatedTransactions);
      await AsyncStorage.setItem('transactions', JSON.stringify(updatedTransactions));
    } catch (error) {
      console.error('Error adding transaction:', error);
    }
  };

  const refreshData = () => {
    // Simulate data refresh
    setLastSync(new Date());
  };

  // Calculate derived values
  const totalNetWorth = portfolio.reduce((sum, item) => sum + item.value, 0);
  const monthlyIncome = transactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);
  const monthlyExpenses = transactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0);

  const value: DataContextType = {
    goals,
    portfolio,
    transactions,
    achievements,
    totalNetWorth,
    monthlyIncome,
    monthlyExpenses,
    addGoal,
    updateGoal,
    deleteGoal,
    addTransaction,
    refreshData,
    isOffline,
    lastSync,
  };

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};

// Mock data
const mockGoals: FinancialGoal[] = [
  {
    id: '1',
    title: 'Emergency Fund',
    description: '6 months of expenses for financial security',
    targetAmount: 25000,
    currentAmount: 15000,
    targetDate: '2024-12-31',
    category: 'emergency',
    priority: 'high',
    isCompleted: false,
  },
  {
    id: '2',
    title: 'Retirement Savings',
    description: 'Build a comfortable retirement nest egg',
    targetAmount: 500000,
    currentAmount: 85000,
    targetDate: '2040-01-01',
    category: 'retirement',
    priority: 'high',
    isCompleted: false,
  },
  {
    id: '3',
    title: 'European Vacation',
    description: 'Two-week trip across Europe',
    targetAmount: 8000,
    currentAmount: 3500,
    targetDate: '2025-06-01',
    category: 'travel',
    priority: 'medium',
    isCompleted: false,
  },
];

const mockPortfolio: PortfolioItem[] = [
  {
    id: '1',
    name: 'Apple Inc.',
    symbol: 'AAPL',
    amount: 50,
    value: 8750,
    change: 125.50,
    changePercent: 1.45,
    allocation: 25.2,
  },
  {
    id: '2',
    name: 'Vanguard S&P 500 ETF',
    symbol: 'VOO',
    amount: 100,
    value: 43000,
    change: -180.25,
    changePercent: -0.42,
    allocation: 35.8,
  },
  {
    id: '3',
    name: 'Tesla Inc.',
    symbol: 'TSLA',
    amount: 25,
    value: 5625,
    change: 45.75,
    changePercent: 0.82,
    allocation: 15.3,
  },
  {
    id: '4',
    name: 'Bitcoin',
    symbol: 'BTC',
    amount: 0.25,
    value: 12500,
    change: 750.00,
    changePercent: 6.38,
    allocation: 23.7,
  },
];

const mockTransactions: Transaction[] = [
  {
    id: '1',
    description: 'Salary Deposit',
    amount: 5500,
    category: 'Salary',
    date: '2024-08-20',
    type: 'income',
  },
  {
    id: '2',
    description: 'Rent Payment',
    amount: 1800,
    category: 'Housing',
    date: '2024-08-18',
    type: 'expense',
  },
  {
    id: '3',
    description: 'Grocery Shopping',
    amount: 245.67,
    category: 'Food',
    date: '2024-08-17',
    type: 'expense',
  },
  {
    id: '4',
    description: 'Investment Contribution',
    amount: 1000,
    category: 'Investment',
    date: '2024-08-15',
    type: 'expense',
  },
];

const mockAchievements: Achievement[] = [
  {
    id: '1',
    title: 'First Goal Created',
    description: 'Created your first financial goal',
    icon: 'target',
    unlockedAt: '2024-08-01T10:00:00Z',
    progress: 1,
    maxProgress: 1,
  },
  {
    id: '2',
    title: 'Savings Streak',
    description: 'Saved money for 7 days in a row',
    icon: 'fire',
    unlockedAt: null,
    progress: 5,
    maxProgress: 7,
  },
  {
    id: '3',
    title: 'Investment Explorer',
    description: 'Made your first investment',
    icon: 'trending-up',
    unlockedAt: '2024-08-10T14:30:00Z',
    progress: 1,
    maxProgress: 1,
  },
];