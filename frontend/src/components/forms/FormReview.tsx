"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FormData, FormStepProps } from '@/types';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { Edit2, CheckCircle2 } from 'lucide-react';

const MARITAL_STATUS_LABELS = {
  single: 'Single',
  married: 'Married',
  divorced: 'Divorced',
  widowed: 'Widowed',
};

const RISK_TOLERANCE_LABELS = {
  conservative: 'Conservative',
  moderate: 'Moderate',
  aggressive: 'Aggressive',
  very_aggressive: 'Very Aggressive',
};

const RETIREMENT_LOCATION_LABELS = {
  current: 'Current Area',
  lower_cost: 'Lower Cost Area',
  higher_cost: 'Higher Cost Area',
};

interface FormReviewProps extends FormStepProps<FormData> {
  onEdit: (step: string) => void;
}

export default function FormReview({ data, onNext, onPrev, onEdit }: FormReviewProps) {
  const handleSubmit = () => {
    onNext(data);
  };

  const ReviewSection = ({ 
    title, 
    onEditClick, 
    children 
  }: { 
    title: string; 
    onEditClick: () => void; 
    children: React.ReactNode;
  }) => (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">{title}</CardTitle>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onEditClick}
            className="text-blue-600 hover:text-blue-800"
          >
            <Edit2 className="w-4 h-4 mr-1" />
            Edit
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {children}
      </CardContent>
    </Card>
  );

  const DetailRow = ({ label, value }: { label: string; value: string | number }) => (
    <div className="flex justify-between py-1">
      <span className="text-muted-foreground">{label}:</span>
      <span className="font-medium">{value}</span>
    </div>
  );

  return (
    <div id="form-review" className="max-w-4xl mx-auto">
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center">
            <CheckCircle2 className="w-6 h-6 text-green-500 mr-3" />
            <div>
              <CardTitle>Review Your Information</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Please review all the information below. Click "Edit" next to any section to make changes.
              </p>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Personal Information */}
      {data.personalInfo && (
        <ReviewSection 
          title="Personal Information" 
          onEditClick={() => onEdit('personal-info')}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <DetailRow label="Age" value={data.personalInfo.age} />
              <DetailRow label="Retirement Age" value={data.personalInfo.retirementAge} />
              <DetailRow label="Years to Retirement" value={data.personalInfo.retirementAge - data.personalInfo.age} />
            </div>
            <div>
              <DetailRow label="Marital Status" value={MARITAL_STATUS_LABELS[data.personalInfo.maritalStatus]} />
              <DetailRow label="Dependents" value={data.personalInfo.dependents} />
              <DetailRow label="Location" value={`${data.personalInfo.state} ${data.personalInfo.zipCode}`} />
            </div>
          </div>
        </ReviewSection>
      )}

      {/* Financial Snapshot */}
      {data.financialSnapshot && (
        <ReviewSection 
          title="Financial Snapshot" 
          onEditClick={() => onEdit('financial-snapshot')}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <DetailRow label="Annual Income" value={formatCurrency(data.financialSnapshot.annualIncome)} />
              <DetailRow label="Monthly Expenses" value={formatCurrency(data.financialSnapshot.monthlyExpenses)} />
              <DetailRow label="Monthly Surplus" value={formatCurrency((data.financialSnapshot.annualIncome / 12) - data.financialSnapshot.monthlyExpenses)} />
              <DetailRow label="Emergency Fund" value={formatCurrency(data.financialSnapshot.emergencyFund)} />
            </div>
            <div>
              <DetailRow label="Total Savings" value={formatCurrency(data.financialSnapshot.totalSavings)} />
              <DetailRow label="Total Debt" value={formatCurrency(data.financialSnapshot.totalDebt)} />
              <DetailRow label="Monthly Debt Payments" value={formatCurrency(data.financialSnapshot.monthlyDebtPayments)} />
              <DetailRow label="Expected Social Security" value={formatCurrency(data.financialSnapshot.expectedSocialSecurity)} />
            </div>
          </div>
        </ReviewSection>
      )}

      {/* Account Buckets */}
      {data.accountBuckets && (
        <ReviewSection 
          title="Account Buckets" 
          onEditClick={() => onEdit('account-buckets')}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(data.accountBuckets).map(([accountType, account]) => {
              const accountName = accountType.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
              return (
                <div key={accountType} className="border rounded-lg p-3">
                  <h4 className="font-medium mb-2">{accountName}</h4>
                  <DetailRow label="Balance" value={formatCurrency(account.balance)} />
                  <DetailRow label="Monthly Contribution" value={formatCurrency(account.monthlyContribution)} />
                  {'employerMatch' in account && account.employerMatch > 0 && (
                    <DetailRow label="Employer Match" value={formatCurrency(account.employerMatch)} />
                  )}
                </div>
              );
            })}
          </div>
        </ReviewSection>
      )}

      {/* Risk Preference */}
      {data.riskPreference && (
        <ReviewSection 
          title="Risk Preference" 
          onEditClick={() => onEdit('risk-preference')}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <DetailRow label="Risk Tolerance" value={RISK_TOLERANCE_LABELS[data.riskPreference.riskTolerance]} />
              <DetailRow label="Time Horizon" value={`${data.riskPreference.timeHorizon} years`} />
              <DetailRow label="Volatility Comfort" value={`${data.riskPreference.volatilityComfort}/5`} />
            </div>
            <div>
              <DetailRow label="Market Downturn Reaction" value={data.riskPreference.marketDownturnReaction.replace('_', ' ')} />
              <DetailRow label="Investment Experience" value={data.riskPreference.investmentExperience} />
            </div>
          </div>
        </ReviewSection>
      )}

      {/* Retirement Goals */}
      {data.retirementGoals && (
        <ReviewSection 
          title="Retirement Goals" 
          onEditClick={() => onEdit('retirement-goals')}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <DetailRow label="Desired Monthly Income" value={formatCurrency(data.retirementGoals.desiredMonthlyIncome)} />
              <DetailRow label="Inflation Assumption" value={formatPercent(data.retirementGoals.inflationAssumption)} />
              <DetailRow label="Retirement Location" value={RETIREMENT_LOCATION_LABELS[data.retirementGoals.retirementLocation]} />
            </div>
            <div>
              <DetailRow label="Healthcare Costs" value={formatCurrency(data.retirementGoals.healthcareCosts)} />
              <DetailRow label="Legacy Goal" value={formatCurrency(data.retirementGoals.legacyGoal)} />
              <DetailRow label="Major Expenses" value={data.retirementGoals.majorExpenses.length} />
            </div>
          </div>
          
          {data.retirementGoals.majorExpenses.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium mb-2">Major Expenses</h4>
              <div className="space-y-2">
                {data.retirementGoals.majorExpenses.map((expense, index) => (
                  <div key={index} className="flex justify-between items-center p-2 bg-muted rounded">
                    <span>{expense.name}</span>
                    <span className="font-medium">{formatCurrency(expense.amount)} in {expense.year}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </ReviewSection>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between pt-6">
        <Button
          id="form-review-prev-button"
          type="button"
          variant="outline"
          onClick={onPrev}
        >
          Previous
        </Button>
        <Button
          id="form-review-submit-button"
          onClick={handleSubmit}
          size="lg"
        >
          Generate Financial Plan
        </Button>
      </div>
    </div>
  );
}