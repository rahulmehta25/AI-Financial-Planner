"use client";

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AccountBuckets, FormStepProps } from '@/types';
import { accountBucketsSchema, AccountBucketsFormData } from '@/lib/validationSchemas';
import { formatCurrency } from '@/lib/utils';

const ACCOUNT_DESCRIPTIONS = {
  taxable: "Regular investment accounts with no tax advantages",
  traditional401k: "Employer-sponsored retirement account with pre-tax contributions",
  roth401k: "Employer-sponsored retirement account with after-tax contributions",
  traditionalIRA: "Individual retirement account with pre-tax contributions",
  rothIRA: "Individual retirement account with after-tax contributions",
  hsa: "Health Savings Account with triple tax advantage",
};

export default function AccountBucketsForm({ 
  data, 
  onNext, 
  onPrev 
}: FormStepProps<AccountBuckets>) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<AccountBucketsFormData>({
    resolver: zodResolver(accountBucketsSchema),
    defaultValues: data,
    mode: 'onChange',
  });

  const watchedValues = watch();

  // Calculate totals
  const totalBalance = Object.entries(watchedValues).reduce((sum, [key, account]) => {
    return sum + (account?.balance || 0);
  }, 0);

  const totalMonthlyContributions = Object.entries(watchedValues).reduce((sum, [key, account]) => {
    return sum + (account?.monthlyContribution || 0);
  }, 0);

  const onSubmit = (formData: AccountBucketsFormData) => {
    onNext(formData);
  };

  const AccountSection = ({ 
    name, 
    title, 
    description, 
    showEmployerMatch = false 
  }: { 
    name: keyof AccountBucketsFormData; 
    title: string; 
    description: string;
    showEmployerMatch?: boolean;
  }) => (
    <Card id={`${name}-account-section`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{title}</CardTitle>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            id={`${name}-balance-input`}
            label="Current Balance"
            type="number"
            {...register(`${name}.balance`, { valueAsNumber: true })}
            error={errors[name]?.balance?.message}
            leftIcon="$"
          />
          
          <Input
            id={`${name}-contribution-input`}
            label="Monthly Contribution"
            type="number"
            {...register(`${name}.monthlyContribution`, { valueAsNumber: true })}
            error={errors[name]?.monthlyContribution?.message}
            leftIcon="$"
          />
        </div>
        
        {showEmployerMatch && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <Input
              id={`${name}-employer-match-input`}
              label="Monthly Employer Match"
              type="number"
              {...register(`${name}.employerMatch`, { valueAsNumber: true })}
              error={errors[name]?.employerMatch?.message}
              leftIcon="$"
              helperText="Dollar amount your employer matches monthly"
            />
            
            <Input
              id={`${name}-match-percent-input`}
              label="Employer Match Percentage"
              type="number"
              {...register(`${name}.employerMatchPercent`, { valueAsNumber: true })}
              error={errors[name]?.employerMatchPercent?.message}
              rightIcon="%"
              helperText="Percentage of salary your employer matches"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div id="account-buckets-form" className="max-w-4xl mx-auto">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Account Buckets</CardTitle>
          <p className="text-sm text-muted-foreground">
            Tell us about your various investment and retirement accounts. Different account types have different tax implications.
          </p>
        </CardHeader>
        <CardContent>
          {/* Summary Display */}
          {(totalBalance > 0 || totalMonthlyContributions > 0) && (
            <div id="account-summary" className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">Current Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-green-700 dark:text-green-200">Total Balance:</span>
                  <div className="font-bold text-lg text-green-900 dark:text-green-100">
                    {formatCurrency(totalBalance)}
                  </div>
                </div>
                <div>
                  <span className="text-green-700 dark:text-green-200">Monthly Contributions:</span>
                  <div className="font-bold text-lg text-green-900 dark:text-green-100">
                    {formatCurrency(totalMonthlyContributions)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <AccountSection
          name="taxable"
          title="Taxable Investment Accounts"
          description={ACCOUNT_DESCRIPTIONS.taxable}
        />

        <AccountSection
          name="traditional401k"
          title="Traditional 401(k)"
          description={ACCOUNT_DESCRIPTIONS.traditional401k}
          showEmployerMatch={true}
        />

        <AccountSection
          name="roth401k"
          title="Roth 401(k)"
          description={ACCOUNT_DESCRIPTIONS.roth401k}
        />

        <AccountSection
          name="traditionalIRA"
          title="Traditional IRA"
          description={ACCOUNT_DESCRIPTIONS.traditionalIRA}
        />

        <AccountSection
          name="rothIRA"
          title="Roth IRA"
          description={ACCOUNT_DESCRIPTIONS.rothIRA}
        />

        <AccountSection
          name="hsa"
          title="Health Savings Account (HSA)"
          description={ACCOUNT_DESCRIPTIONS.hsa}
        />

        <div className="flex justify-between pt-4">
          <Button
            id="account-buckets-prev-button"
            type="button"
            variant="outline"
            onClick={onPrev}
          >
            Previous
          </Button>
          <Button
            id="account-buckets-next-button"
            type="submit"
            disabled={!isValid}
          >
            Continue
          </Button>
        </div>
      </form>
    </div>
  );
}