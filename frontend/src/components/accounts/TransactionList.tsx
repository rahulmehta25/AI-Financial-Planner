import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Search,
  Filter,
  Download,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  DollarSign,
  Tag,
  MoreHorizontal,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  FileText,
  CreditCard,
  Banknote,
  Gift,
  Zap
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { 
  Transaction, 
  TransactionListProps, 
  TransactionFilters 
} from '@/types/accounts';

const getTransactionIcon = (type: string) => {
  const icons = {
    contribution: CreditCard,
    distribution: Banknote,
    transfer: ArrowUpRight,
    dividend: Gift,
    fee: Zap,
    default: FileText
  };
  
  return icons[type as keyof typeof icons] || icons.default;
};

const getTransactionColor = (type: string, amount: number) => {
  if (type === 'contribution' || type === 'dividend') {
    return 'text-green-600';
  } else if (type === 'distribution' || type === 'fee') {
    return 'text-red-600';
  } else if (amount >= 0) {
    return 'text-green-600';
  } else {
    return 'text-red-600';
  }
};

const getTransactionBadgeColor = (type: string) => {
  const colors = {
    contribution: 'bg-green-100 text-green-800',
    distribution: 'bg-red-100 text-red-800',
    transfer: 'bg-blue-100 text-blue-800',
    dividend: 'bg-purple-100 text-purple-800',
    fee: 'bg-orange-100 text-orange-800'
  };
  
  return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
};

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(Math.abs(amount));
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
};

const TransactionRow: React.FC<{
  transaction: Transaction;
  onCategorize?: (transactionId: string, category: string) => void;
}> = ({ transaction, onCategorize }) => {
  const IconComponent = getTransactionIcon(transaction.type);
  const textColor = getTransactionColor(transaction.type, transaction.amount);
  const badgeColor = getTransactionBadgeColor(transaction.type);
  const isPositive = transaction.amount >= 0;

  return (
    <div 
      id={`transaction-row-${transaction.id}`}
      className="flex items-center justify-between p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors"
    >
      <div id={`transaction-info-${transaction.id}`} className="flex items-center space-x-4 flex-1">
        <div className={`p-2 rounded-lg ${badgeColor}`}>
          <IconComponent className="h-4 w-4" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <p className="text-sm font-medium text-gray-900 truncate">
              {transaction.description}
            </p>
            <Badge className={badgeColor}>
              {transaction.type}
            </Badge>
          </div>
          
          <div className="flex items-center space-x-4 text-xs text-gray-500">
            <div className="flex items-center space-x-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(transaction.transaction_date)}</span>
            </div>
            
            {transaction.category && (
              <div className="flex items-center space-x-1">
                <Tag className="h-3 w-3" />
                <span>{transaction.category}</span>
              </div>
            )}
            
            {transaction.tags && transaction.tags.length > 0 && (
              <div className="flex space-x-1">
                {transaction.tags.slice(0, 2).map((tag, index) => (
                  <span
                    key={index}
                    className="px-1.5 py-0.5 bg-gray-200 rounded text-xs"
                  >
                    {tag}
                  </span>
                ))}
                {transaction.tags.length > 2 && (
                  <span className="text-gray-400">+{transaction.tags.length - 2}</span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div id={`transaction-amount-${transaction.id}`} className="flex items-center space-x-3">
        <div className="text-right">
          <div className={`flex items-center space-x-1 ${textColor}`}>
            {isPositive ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            <span className="text-lg font-semibold">
              {isPositive ? '+' : '-'}{formatCurrency(transaction.amount)}
            </span>
          </div>
          
          {transaction.balance_after && (
            <p className="text-xs text-gray-500 mt-1">
              Balance: {formatCurrency(transaction.balance_after)}
            </p>
          )}
        </div>
        
        {onCategorize && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onCategorize(transaction.id, 'investment')}>
                Categorize as Investment
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onCategorize(transaction.id, 'fee')}>
                Categorize as Fee
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onCategorize(transaction.id, 'dividend')}>
                Categorize as Dividend
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onCategorize(transaction.id, 'other')}>
                Other Category
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </div>
  );
};

const TransactionFilters: React.FC<{
  filters: TransactionFilters;
  onFilterChange: (filters: TransactionFilters) => void;
  availableCategories: string[];
  availableTypes: string[];
}> = ({ filters, onFilterChange, availableCategories, availableTypes }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button id="filters-toggle" variant="outline" className="w-full justify-between">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4" />
            <span>Filters</span>
          </div>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </CollapsibleTrigger>
      
      <CollapsibleContent className="space-y-4 pt-4">
        <div id="search-filter" className="space-y-2">
          <Label htmlFor="transaction-search">Search</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="transaction-search"
              placeholder="Search transactions..."
              value={filters.search || ''}
              onChange={(e) => onFilterChange({
                ...filters,
                search: e.target.value
              })}
              className="pl-10"
            />
          </div>
        </div>
        
        <div id="type-filter" className="space-y-2">
          <Label htmlFor="transaction-type">Transaction Type</Label>
          <Select
            value={filters.types?.[0] || ''}
            onValueChange={(value) => onFilterChange({
              ...filters,
              types: value ? [value] : undefined
            })}
          >
            <SelectTrigger>
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All types</SelectItem>
              {availableTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div id="category-filter" className="space-y-2">
          <Label htmlFor="transaction-category">Category</Label>
          <Select
            value={filters.categories?.[0] || ''}
            onValueChange={(value) => onFilterChange({
              ...filters,
              categories: value ? [value] : undefined
            })}
          >
            <SelectTrigger>
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All categories</SelectItem>
              {availableCategories.map((category) => (
                <SelectItem key={category} value={category}>
                  {category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div id="date-range-filter" className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start-date">Start Date</Label>
            <Input
              id="start-date"
              type="date"
              value={filters.dateRange?.start || ''}
              onChange={(e) => onFilterChange({
                ...filters,
                dateRange: {
                  ...filters.dateRange,
                  start: e.target.value,
                  end: filters.dateRange?.end || ''
                }
              })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="end-date">End Date</Label>
            <Input
              id="end-date"
              type="date"
              value={filters.dateRange?.end || ''}
              onChange={(e) => onFilterChange({
                ...filters,
                dateRange: {
                  start: filters.dateRange?.start || '',
                  end: e.target.value
                }
              })}
            />
          </div>
        </div>
        
        <div id="amount-range-filter" className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="min-amount">Min Amount</Label>
            <Input
              id="min-amount"
              type="number"
              placeholder="0.00"
              value={filters.amountRange?.min || ''}
              onChange={(e) => onFilterChange({
                ...filters,
                amountRange: {
                  ...filters.amountRange,
                  min: e.target.value ? parseFloat(e.target.value) : undefined,
                  max: filters.amountRange?.max
                }
              })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="max-amount">Max Amount</Label>
            <Input
              id="max-amount"
              type="number"
              placeholder="1000.00"
              value={filters.amountRange?.max || ''}
              onChange={(e) => onFilterChange({
                ...filters,
                amountRange: {
                  min: filters.amountRange?.min,
                  max: e.target.value ? parseFloat(e.target.value) : undefined
                }
              })}
            />
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

const TransactionList: React.FC<TransactionListProps> = ({
  accountId,
  transactions,
  loading = false,
  onLoadMore,
  hasMore = false,
  onCategorize,
  filters = {},
  onFilterChange
}) => {
  const [localFilters, setLocalFilters] = useState<TransactionFilters>(filters);

  const filteredTransactions = useMemo(() => {
    let filtered = [...transactions];

    // Search filter
    if (localFilters.search) {
      const searchTerm = localFilters.search.toLowerCase();
      filtered = filtered.filter(transaction =>
        transaction.description.toLowerCase().includes(searchTerm) ||
        transaction.category?.toLowerCase().includes(searchTerm)
      );
    }

    // Type filter
    if (localFilters.types && localFilters.types.length > 0) {
      filtered = filtered.filter(transaction =>
        localFilters.types!.includes(transaction.type)
      );
    }

    // Category filter
    if (localFilters.categories && localFilters.categories.length > 0) {
      filtered = filtered.filter(transaction =>
        transaction.category && localFilters.categories!.includes(transaction.category)
      );
    }

    // Date range filter
    if (localFilters.dateRange?.start && localFilters.dateRange?.end) {
      filtered = filtered.filter(transaction => {
        const transactionDate = new Date(transaction.transaction_date);
        const startDate = new Date(localFilters.dateRange!.start);
        const endDate = new Date(localFilters.dateRange!.end);
        return transactionDate >= startDate && transactionDate <= endDate;
      });
    }

    // Amount range filter
    if (localFilters.amountRange) {
      filtered = filtered.filter(transaction => {
        const amount = Math.abs(transaction.amount);
        const min = localFilters.amountRange!.min;
        const max = localFilters.amountRange!.max;
        
        if (min !== undefined && amount < min) return false;
        if (max !== undefined && amount > max) return false;
        return true;
      });
    }

    return filtered;
  }, [transactions, localFilters]);

  const availableCategories = useMemo(() => {
    const categories = new Set<string>();
    transactions.forEach(transaction => {
      if (transaction.category) {
        categories.add(transaction.category);
      }
    });
    return Array.from(categories).sort();
  }, [transactions]);

  const availableTypes = useMemo(() => {
    const types = new Set<string>();
    transactions.forEach(transaction => types.add(transaction.type));
    return Array.from(types).sort();
  }, [transactions]);

  const handleFilterChange = (newFilters: TransactionFilters) => {
    setLocalFilters(newFilters);
    onFilterChange?.(newFilters);
  };

  const transactionSummary = useMemo(() => {
    const summary = filteredTransactions.reduce(
      (acc, transaction) => {
        if (transaction.amount >= 0) {
          acc.totalInflows += transaction.amount;
          acc.inflowCount += 1;
        } else {
          acc.totalOutflows += Math.abs(transaction.amount);
          acc.outflowCount += 1;
        }
        return acc;
      },
      { totalInflows: 0, totalOutflows: 0, inflowCount: 0, outflowCount: 0 }
    );

    return {
      ...summary,
      netAmount: summary.totalInflows - summary.totalOutflows,
      totalTransactions: filteredTransactions.length
    };
  }, [filteredTransactions]);

  return (
    <Card id="transaction-list-main">
      <CardHeader id="transaction-list-header">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-semibold">
            Transaction History
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Transaction Summary */}
        <div id="transaction-summary" className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-xs font-medium text-green-700">Inflows</p>
                <p className="text-lg font-bold text-green-800">
                  {formatCurrency(transactionSummary.totalInflows)}
                </p>
                <p className="text-xs text-green-600">
                  {transactionSummary.inflowCount} transactions
                </p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <TrendingDown className="h-4 w-4 text-red-600" />
              <div>
                <p className="text-xs font-medium text-red-700">Outflows</p>
                <p className="text-lg font-bold text-red-800">
                  {formatCurrency(transactionSummary.totalOutflows)}
                </p>
                <p className="text-xs text-red-600">
                  {transactionSummary.outflowCount} transactions
                </p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-xs font-medium text-blue-700">Net Amount</p>
                <p className={`text-lg font-bold ${
                  transactionSummary.netAmount >= 0 ? 'text-green-800' : 'text-red-800'
                }`}>
                  {transactionSummary.netAmount >= 0 ? '+' : '-'}
                  {formatCurrency(transactionSummary.netAmount)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-gray-600" />
              <div>
                <p className="text-xs font-medium text-gray-700">Total</p>
                <p className="text-lg font-bold text-gray-800">
                  {transactionSummary.totalTransactions}
                </p>
                <p className="text-xs text-gray-600">transactions</p>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent id="transaction-list-content">
        {onFilterChange && (
          <div id="transaction-filters-section" className="mb-6">
            <TransactionFilters
              filters={localFilters}
              onFilterChange={handleFilterChange}
              availableCategories={availableCategories}
              availableTypes={availableTypes}
            />
          </div>
        )}

        <div id="transaction-list-container">
          {loading && filteredTransactions.length === 0 ? (
            <div id="transaction-loading" className="space-y-4">
              {[...Array(5)].map((_, index) => (
                <div key={index} className="flex items-center space-x-4 p-4">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                  <Skeleton className="h-6 w-20" />
                </div>
              ))}
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div id="no-transactions" className="text-center py-8">
              <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No transactions found
              </h3>
              <p className="text-gray-500">
                {transactions.length === 0 
                  ? "No transactions have been recorded for this account yet."
                  : "No transactions match your current filters."
                }
              </p>
            </div>
          ) : (
            <>
              <div id="transaction-rows">
                {filteredTransactions.map((transaction) => (
                  <TransactionRow
                    key={transaction.id}
                    transaction={transaction}
                    onCategorize={onCategorize}
                  />
                ))}
              </div>

              {hasMore && (
                <div id="load-more-section" className="mt-6 text-center">
                  <Button 
                    onClick={onLoadMore}
                    disabled={loading}
                    variant="outline"
                  >
                    {loading ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : null}
                    Load More Transactions
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default TransactionList;