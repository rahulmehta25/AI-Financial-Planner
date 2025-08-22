"use client";

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FinancialSnapshot, FormStepProps } from '@/types';
import { financialSnapshotSchema, FinancialSnapshotFormData } from '@/lib/validationSchemas';
import { formatCurrency } from '@/lib/utils';

export default function FinancialSnapshotForm({ 
  data, 
  onNext, 
  onPrev 
}: FormStepProps<FinancialSnapshot>) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<FinancialSnapshotFormData>({
    resolver: zodResolver(financialSnapshotSchema),
    defaultValues: data,
    mode: 'onChange',
  });

  const watchedValues = watch();
  const monthlyIncome = watchedValues.annualIncome ? watchedValues.annualIncome / 12 : 0;
  const savingsRate = watchedValues.annualIncome && watchedValues.monthlyExpenses
    ? ((monthlyIncome - watchedValues.monthlyExpenses) / monthlyIncome) * 100
    : 0;

  const onSubmit = (formData: FinancialSnapshotFormData) => {
    onNext(formData);
  };

  return (
    <div id="financial-snapshot-form" className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Financial Snapshot</CardTitle>
          <p className="text-sm text-muted-foreground">
            Tell us about your current financial situation. This helps us understand your starting point.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="annual-income-input"
                label="Annual Gross Income"
                type="number"
                {...register('annualIncome', { valueAsNumber: true })}
                error={errors.annualIncome?.message}
                helperText="Your total yearly income before taxes"
                leftIcon="$"
                required
              />
              
              <Input
                id="monthly-expenses-input"
                label="Monthly Expenses"
                type="number"
                {...register('monthlyExpenses', { valueAsNumber: true })}
                error={errors.monthlyExpenses?.message}
                helperText="Your total monthly living expenses"
                leftIcon="$"
                required
              />
            </div>

            {/* Savings Rate Display */}
            {monthlyIncome > 0 && watchedValues.monthlyExpenses > 0 && (
              <div id="savings-rate-display" className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Current Savings Rate:
                  </span>
                  <span className={`text-lg font-bold ${savingsRate >= 20 ? 'text-green-600' : savingsRate >= 10 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {savingsRate.toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-blue-700 dark:text-blue-200 mt-1">
                  Monthly surplus: {formatCurrency(monthlyIncome - watchedValues.monthlyExpenses)}
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="total-savings-input"
                label="Total Savings & Investments"
                type="number"
                {...register('totalSavings', { valueAsNumber: true })}
                error={errors.totalSavings?.message}
                helperText="All savings, checking, and investment accounts"
                leftIcon="$"
              />
              
              <Input
                id="emergency-fund-input"
                label="Emergency Fund"
                type="number"
                {...register('emergencyFund', { valueAsNumber: true })}
                error={errors.emergencyFund?.message}
                helperText="Easily accessible funds for emergencies"
                leftIcon="$"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="total-debt-input"
                label="Total Debt"
                type="number"
                {...register('totalDebt', { valueAsNumber: true })}
                error={errors.totalDebt?.message}
                helperText="Credit cards, loans, mortgage, etc."
                leftIcon="$"
              />
              
              <Input
                id="monthly-debt-payments-input"
                label="Monthly Debt Payments"
                type="number"
                {...register('monthlyDebtPayments', { valueAsNumber: true })}
                error={errors.monthlyDebtPayments?.message}
                helperText="Minimum payments on all debts"
                leftIcon="$"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="social-security-input"
                label="Expected Social Security (Monthly)"
                type="number"
                {...register('expectedSocialSecurity', { valueAsNumber: true })}
                error={errors.expectedSocialSecurity?.message}
                helperText="Estimated monthly Social Security benefit"
                leftIcon="$"
              />
              
              <Input
                id="pension-value-input"
                label="Pension Value"
                type="number"
                {...register('pensionValue', { valueAsNumber: true })}
                error={errors.pensionValue?.message}
                helperText="Current value of any pension plans"
                leftIcon="$"
              />
            </div>

            <div className="flex justify-between pt-4">
              <Button
                id="financial-snapshot-prev-button"
                type="button"
                variant="outline"
                onClick={onPrev}
              >
                Previous
              </Button>
              <Button
                id="financial-snapshot-next-button"
                type="submit"
                disabled={!isValid}
              >
                Continue
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}