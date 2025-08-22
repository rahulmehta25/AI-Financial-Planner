"use client";

import React, { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RetirementGoals, FormStepProps } from '@/types';
import { retirementGoalsSchema, RetirementGoalsFormData } from '@/lib/validationSchemas';
import { formatCurrency } from '@/lib/utils';
import { Plus, X } from 'lucide-react';

const RETIREMENT_LOCATION_OPTIONS = [
  { value: 'current', label: 'Current Area', description: 'Stay in my current location' },
  { value: 'lower_cost', label: 'Lower Cost Area', description: 'Move to a more affordable area' },
  { value: 'higher_cost', label: 'Higher Cost Area', description: 'Move to a more expensive area' }
];

export default function RetirementGoalsForm({ 
  data, 
  onNext, 
  onPrev 
}: FormStepProps<RetirementGoals>) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    control,
    formState: { errors, isValid },
  } = useForm<RetirementGoalsFormData>({
    resolver: zodResolver(retirementGoalsSchema),
    defaultValues: data,
    mode: 'onChange',
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'majorExpenses',
  });

  const watchedValues = watch();

  const onSubmit = (formData: RetirementGoalsFormData) => {
    onNext(formData);
  };

  const addMajorExpense = () => {
    append({
      name: '',
      amount: 0,
      year: new Date().getFullYear() + 1,
    });
  };

  const getTotalRetirementCost = () => {
    const monthlyIncome = watchedValues.desiredMonthlyIncome || 0;
    const majorExpensesTotal = watchedValues.majorExpenses?.reduce((sum, expense) => sum + (expense.amount || 0), 0) || 0;
    const healthcare = watchedValues.healthcareCosts || 0;
    const legacy = watchedValues.legacyGoal || 0;
    
    return {
      monthlyIncome,
      annualIncome: monthlyIncome * 12,
      majorExpenses: majorExpensesTotal,
      healthcare,
      legacy,
      total: (monthlyIncome * 12) + majorExpensesTotal + healthcare + legacy
    };
  };

  const costs = getTotalRetirementCost();

  return (
    <div id="retirement-goals-form" className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Retirement Goals</CardTitle>
          <p className="text-sm text-muted-foreground">
            Let's define your retirement lifestyle and financial goals to create a comprehensive plan.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="desired-monthly-income-input"
                label="Desired Monthly Income in Retirement"
                type="number"
                {...register('desiredMonthlyIncome', { valueAsNumber: true })}
                error={errors.desiredMonthlyIncome?.message}
                helperText="In today's dollars"
                leftIcon="$"
                required
              />

              <Input
                id="inflation-assumption-input"
                label="Inflation Assumption (%)"
                type="number"
                step="0.1"
                {...register('inflationAssumption', { valueAsNumber: true })}
                error={errors.inflationAssumption?.message}
                helperText="Expected annual inflation rate"
                rightIcon="%"
              />
            </div>

            <div className="space-y-4">
              <Select
                onValueChange={(value) => setValue('retirementLocation', value as RetirementGoals['retirementLocation'])}
                defaultValue={data.retirementLocation}
              >
                <SelectTrigger 
                  id="retirement-location-select"
                  label="Retirement Location" 
                  required
                  error={errors.retirementLocation?.message}
                >
                  <SelectValue placeholder="Where do you plan to retire?" />
                </SelectTrigger>
                <SelectContent>
                  {RETIREMENT_LOCATION_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      <div>
                        <div className="font-medium">{option.label}</div>
                        <div className="text-sm text-muted-foreground">{option.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Major Expenses Section */}
            <div id="major-expenses-section" className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Major Retirement Expenses</h3>
                <Button
                  id="add-major-expense-button"
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addMajorExpense}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Expense
                </Button>
              </div>
              
              {fields.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Add any major one-time expenses you anticipate in retirement (travel, home renovations, etc.)
                </p>
              )}

              {fields.map((field, index) => (
                <Card key={field.id} className="p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium">Expense #{index + 1}</h4>
                    <Button
                      id={`remove-expense-${index}-button`}
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => remove(index)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Input
                      id={`expense-${index}-name-input`}
                      label="Name"
                      {...register(`majorExpenses.${index}.name`)}
                      error={errors.majorExpenses?.[index]?.name?.message}
                      placeholder="e.g., Dream vacation"
                    />
                    <Input
                      id={`expense-${index}-amount-input`}
                      label="Amount"
                      type="number"
                      {...register(`majorExpenses.${index}.amount`, { valueAsNumber: true })}
                      error={errors.majorExpenses?.[index]?.amount?.message}
                      leftIcon="$"
                    />
                    <Input
                      id={`expense-${index}-year-input`}
                      label="Year"
                      type="number"
                      {...register(`majorExpenses.${index}.year`, { valueAsNumber: true })}
                      error={errors.majorExpenses?.[index]?.year?.message}
                      min={new Date().getFullYear()}
                    />
                  </div>
                </Card>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="healthcare-costs-input"
                label="Expected Annual Healthcare Costs"
                type="number"
                {...register('healthcareCosts', { valueAsNumber: true })}
                error={errors.healthcareCosts?.message}
                helperText="Additional healthcare costs beyond Medicare"
                leftIcon="$"
              />

              <Input
                id="legacy-goal-input"
                label="Legacy/Inheritance Goal"
                type="number"
                {...register('legacyGoal', { valueAsNumber: true })}
                error={errors.legacyGoal?.message}
                helperText="Amount you want to leave to heirs"
                leftIcon="$"
              />
            </div>

            {/* Retirement Cost Summary */}
            {costs.total > 0 && (
              <div id="retirement-cost-summary" className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-3">Retirement Cost Summary</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-purple-700 dark:text-purple-200">Annual Income Need:</span>
                    <span className="font-medium">{formatCurrency(costs.annualIncome)}</span>
                  </div>
                  {costs.majorExpenses > 0 && (
                    <div className="flex justify-between">
                      <span className="text-purple-700 dark:text-purple-200">Major Expenses:</span>
                      <span className="font-medium">{formatCurrency(costs.majorExpenses)}</span>
                    </div>
                  )}
                  {costs.healthcare > 0 && (
                    <div className="flex justify-between">
                      <span className="text-purple-700 dark:text-purple-200">Healthcare Costs:</span>
                      <span className="font-medium">{formatCurrency(costs.healthcare)}</span>
                    </div>
                  )}
                  {costs.legacy > 0 && (
                    <div className="flex justify-between">
                      <span className="text-purple-700 dark:text-purple-200">Legacy Goal:</span>
                      <span className="font-medium">{formatCurrency(costs.legacy)}</span>
                    </div>
                  )}
                  <hr className="border-purple-200 dark:border-purple-700" />
                  <div className="flex justify-between font-bold text-purple-900 dark:text-purple-100">
                    <span>Total Retirement Need:</span>
                    <span>{formatCurrency(costs.total)}</span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button
                id="retirement-goals-prev-button"
                type="button"
                variant="outline"
                onClick={onPrev}
              >
                Previous
              </Button>
              <Button
                id="retirement-goals-next-button"
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