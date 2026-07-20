import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { 
  Plus, 
  Edit3, 
  Trash2, 
  MoreHorizontal, 
  Building, 
  TrendingUp,
  DollarSign,
  Calendar,
  Eye,
  EyeOff
} from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';

interface RetirementAccount {
  id: string;
  account_type: string;
  account_name: string;
  current_balance: number;
  tax_treatment: string;
  is_active: boolean;
  financial_institution?: string;
  employer_name?: string;
  date_opened?: string;
  vested_balance?: number;
}

interface RetirementAccountsListProps {
  accounts: RetirementAccount[];
  onAccountsChange: () => void;
}

interface NewAccountFormData {
  account_type: string;
  account_name: string;
  financial_institution: string;
  current_balance: string;
  employer_name?: string;
  date_opened?: string;
}

const ACCOUNT_TYPES = [
  { value: 'traditional_401k', label: '401(k) - Traditional', tax_treatment: 'tax_deferred' },
  { value: 'roth_401k', label: '401(k) - Roth', tax_treatment: 'tax_free' },
  { value: 'traditional_ira', label: 'Traditional IRA', tax_treatment: 'tax_deferred' },
  { value: 'roth_ira', label: 'Roth IRA', tax_treatment: 'tax_free' },
  { value: 'simple_ira', label: 'SIMPLE IRA', tax_treatment: 'tax_deferred' },
  { value: 'sep_ira', label: 'SEP-IRA', tax_treatment: 'tax_deferred' },
  { value: 'education_529', label: '529 Education Plan', tax_treatment: 'after_tax' },
  { value: 'hsa', label: 'Health Savings Account', tax_treatment: 'triple_tax_advantage' },
  { value: 'pension', label: 'Pension Plan', tax_treatment: 'tax_deferred' },
];

export const RetirementAccountsList: React.FC<RetirementAccountsListProps> = ({
  accounts,
  onAccountsChange,
}) => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<RetirementAccount | null>(null);
  const [hideBalances, setHideBalances] = useState(false);
  const [formData, setFormData] = useState<NewAccountFormData>({
    account_type: '',
    account_name: '',
    financial_institution: '',
    current_balance: '',
    employer_name: '',
    date_opened: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getAccountTypeLabel = (type: string) => {
    const accountType = ACCOUNT_TYPES.find(t => t.value === type);
    return accountType?.label || type;
  };

  const getTaxTreatmentBadge = (treatment: string) => {
    const badgeMap = {
      'tax_deferred': { variant: 'secondary' as const, label: 'Tax-Deferred' },
      'tax_free': { variant: 'default' as const, label: 'Tax-Free' },
      'triple_tax_advantage': { variant: 'destructive' as const, label: 'Triple Tax Advantage' },
      'after_tax': { variant: 'outline' as const, label: 'After-Tax' },
    };
    const config = badgeMap[treatment as keyof typeof badgeMap] || { variant: 'outline' as const, label: treatment };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const selectedType = ACCOUNT_TYPES.find(t => t.value === formData.account_type);
      if (!selectedType) {
        throw new Error('Invalid account type selected');
      }

      const payload = {
        account_type: formData.account_type,
        account_name: formData.account_name,
        financial_institution: formData.financial_institution,
        current_balance: parseFloat(formData.current_balance),
        tax_treatment: selectedType.tax_treatment,
        employer_name: formData.employer_name || undefined,
        date_opened: formData.date_opened ? new Date(formData.date_opened).toISOString() : undefined,
      };

      const url = editingAccount 
        ? `/api/v1/retirement/accounts/${editingAccount.id}`
        : '/api/v1/retirement/accounts';
      
      const method = editingAccount ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save account');
      }

      // Reset form and close dialog
      setFormData({
        account_type: '',
        account_name: '',
        financial_institution: '',
        current_balance: '',
        employer_name: '',
        date_opened: '',
      });
      setIsAddDialogOpen(false);
      setEditingAccount(null);
      onAccountsChange();

    } catch (error) {
      console.error('Error saving account:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (account: RetirementAccount) => {
    setEditingAccount(account);
    setFormData({
      account_type: account.account_type,
      account_name: account.account_name,
      financial_institution: account.financial_institution || '',
      current_balance: account.current_balance.toString(),
      employer_name: account.employer_name || '',
      date_opened: account.date_opened ? account.date_opened.split('T')[0] : '',
    });
    setIsAddDialogOpen(true);
  };

  const handleDelete = async (accountId: string) => {
    if (!window.confirm('Are you sure you want to delete this account? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/retirement/accounts/${accountId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete account');
      }

      onAccountsChange();
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('Failed to delete account. Please try again.');
    }
  };

  const handleDialogClose = () => {
    setIsAddDialogOpen(false);
    setEditingAccount(null);
    setFormData({
      account_type: '',
      account_name: '',
      financial_institution: '',
      current_balance: '',
      employer_name: '',
      date_opened: '',
    });
    setError(null);
  };

  const totalBalance = accounts.reduce((sum, account) => sum + account.current_balance, 0);
  const activeAccounts = accounts.filter(account => account.is_active);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Retirement Accounts</h2>
          <p className="text-muted-foreground">
            Manage your {activeAccounts.length} retirement accounts with a total balance of {formatCurrency(totalBalance)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setHideBalances(!hideBalances)}
            className="flex items-center gap-2"
          >
            {hideBalances ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            {hideBalances ? 'Show' : 'Hide'} Balances
          </Button>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Add Account
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>
                  {editingAccount ? 'Edit Account' : 'Add Retirement Account'}
                </DialogTitle>
                <DialogDescription>
                  {editingAccount 
                    ? 'Update your account information below.'
                    : 'Add a new retirement account to track your savings progress.'
                  }
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="account_type">Account Type</Label>
                  <Select
                    value={formData.account_type}
                    onValueChange={(value) => setFormData({ ...formData, account_type: value })}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select account type" />
                    </SelectTrigger>
                    <SelectContent>
                      {ACCOUNT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="account_name">Account Name</Label>
                  <Input
                    id="account_name"
                    value={formData.account_name}
                    onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                    placeholder="e.g., Company 401(k), Personal IRA"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="financial_institution">Financial Institution</Label>
                  <Input
                    id="financial_institution"
                    value={formData.financial_institution}
                    onChange={(e) => setFormData({ ...formData, financial_institution: e.target.value })}
                    placeholder="e.g., Fidelity, Vanguard, Charles Schwab"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="current_balance">Current Balance</Label>
                  <Input
                    id="current_balance"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.current_balance}
                    onChange={(e) => setFormData({ ...formData, current_balance: e.target.value })}
                    placeholder="0.00"
                    required
                  />
                </div>

                {(formData.account_type.includes('401k') || formData.account_type === 'simple_ira' || formData.account_type === 'sep_ira') && (
                  <div className="space-y-2">
                    <Label htmlFor="employer_name">Employer Name</Label>
                    <Input
                      id="employer_name"
                      value={formData.employer_name}
                      onChange={(e) => setFormData({ ...formData, employer_name: e.target.value })}
                      placeholder="Your employer's name"
                    />
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="date_opened">Date Opened (Optional)</Label>
                  <Input
                    id="date_opened"
                    type="date"
                    value={formData.date_opened}
                    onChange={(e) => setFormData({ ...formData, date_opened: e.target.value })}
                  />
                </div>

                {error && (
                  <Alert>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={handleDialogClose}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving...' : editingAccount ? 'Update Account' : 'Add Account'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Accounts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Your Accounts</CardTitle>
          <CardDescription>
            Overview of all your retirement accounts
          </CardDescription>
        </CardHeader>
        <CardContent>
          {activeAccounts.length === 0 ? (
            <div className="text-center py-8">
              <PiggyBank className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No retirement accounts yet</h3>
              <p className="text-muted-foreground mb-4">
                Start by adding your first retirement account to track your progress.
              </p>
              <Button onClick={() => setIsAddDialogOpen(true)}>Add Your First Account</Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Institution</TableHead>
                  <TableHead>Tax Treatment</TableHead>
                  <TableHead>Balance</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeAccounts.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{account.account_name}</span>
                        {account.employer_name && (
                          <span className="text-sm text-muted-foreground flex items-center gap-1">
                            <Building className="h-3 w-3" />
                            {account.employer_name}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{getAccountTypeLabel(account.account_type)}</TableCell>
                    <TableCell>{account.financial_institution || 'Not specified'}</TableCell>
                    <TableCell>{getTaxTreatmentBadge(account.tax_treatment)}</TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {hideBalances ? '****' : formatCurrency(account.current_balance)}
                        </span>
                        {account.vested_balance && account.vested_balance !== account.current_balance && (
                          <span className="text-sm text-muted-foreground">
                            Vested: {hideBalances ? '****' : formatCurrency(account.vested_balance)}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEdit(account)}>
                            <Edit3 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(account.id)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};